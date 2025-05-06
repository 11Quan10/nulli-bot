import asyncio
import codecs
import os
import re
import time
from langsmith import traceable
from langgraph.graph import END, StateGraph, START
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from graph.models import Models
from graph.memory import Memory
from graph.system_prompts import SystemPrompts
from graph.chains.search import SearchChain
from graph.chains.iteratively_summarize import IterativelySummarizeChain
from graph.chains.retrieve import RetrieveChain
from graph.chains.respond import RespondChain
from graph.chains.filter import FilterChain
import base64
from urllib.request import Request, urlopen

# load filtered words from encrypted txt
if os.path.exists("../regex_filters/bad_words.txt"):
    with open("../regex_filters/bad_words.txt", "r") as file:
        content = codecs.encode(file.read(), "rot13")
    filtered_words = [word.strip() for word in content.split(",")]
    filter_pattern = re.compile(r"\b(" + "|".join(filtered_words) + r")\b", flags=re.IGNORECASE)
else:
    filter_pattern = re.compile(r"(?!)")


class AgentState(TypedDict):
    # The add_messages function defines how an update should be processed
    # Default is to replace. add_messages says "append"
    messages: Annotated[list, add_messages]
    context: list[HumanMessage]
    current_summary: str
    new_summary: str
    memory: str
    response: str
    response_prefiltered: str
    start_time: float
    response_time: float

    ctx_guild_id: any
    tts_callback: any
    stop_audio_callback: any


class Graph:
    def __init__(self):
        self.current_summary = ""
        self._build_graph()
        self._save_graph_as_png()

    @traceable
    async def invoke_model_with_human_messages(
        self, messages: list[HumanMessage], _ctx_guild_id=None, _tts_callback=None, _stop_audio_callback=None
    ):
        results = await self.graph.ainvoke(
            {
                "current_summary": self.current_summary,
                "context": messages,
                "start_time": time.time(),
                "ctx_guild_id": _ctx_guild_id,
                "tts_callback": _tts_callback,
                "stop_audio_callback": _stop_audio_callback,
            }
        )
        return results

    def _build_graph(self):
        models = Models()
        # memory = Memory(models.embeddings, models.sparse_embeddings)
        system_prompts = SystemPrompts()
        # search_chain = SearchChain()
        # iteratively_summarize_chain = IterativelySummarizeChain(model_llm=models.model_llm)
        # retrieve_chain = RetrieveChain(retriever=memory.retriever)
        respond_chain = RespondChain(model_llm=models.model_llm)
        filter_chain = FilterChain(model_guard=models.model_guard)

        async def search(state):
            # search_results = await search_chain.search_chain.ainvoke({"context": state["context"]})
            # return {"context": search_results, "messages": [AIMessage(content=search_results, id="1")]}
            pass

        async def iteratively_summarize(state):
            # summary = await iteratively_summarize_chain.iteratively_summarize_chain.ainvoke(
            #     {"current_summary": state["current_summary"], "context": state["context"]}
            # )
            # self.current_summary = summary
            # return {"new_summary": summary, "messages": [AIMessage(content=summary, id="2")]}
            pass

        async def retrieve(state):
            # memory = await retrieve_chain.retrieve_chain.ainvoke(state["current_summary"] + " " + state["context"])
            # return {"memory": memory, "messages": [AIMessage(content=memory, id="6")]}
            pass

        async def respond(state):
            response = await respond_chain.respond_chain.ainvoke(
                [
                    SystemMessage(content=system_prompts.respond_system_prompt),
                    *state["context"],
                ]
            )
            response_prefiltered = response
            # filter out action indicators from response
            response = re.sub(r"\*[^*]+\*", "", response).strip()
            response = re.sub(r"\:[^:]+\:", "", response).strip()
            response = re.sub(r"\([^)]*\)", "", response).strip()

            return {
                "response": response,
                "response_prefiltered": response_prefiltered,
                "messages": [AIMessage(content=response, id="Response")],
                "response_time": time.time(),
            }

        async def filter_response_regex(state):
            match = filter_pattern.search(state["response"])
            if match:
                
                return {
                    "messages": [
                        AIMessage(
                            content=f"Response contains filtered words: {match.group()}. Response={state['response']}",
                            id="Filter Regex BAD",
                        )
                    ]
                }
            # play text as audio
            if state["ctx_guild_id"] is not None and state["tts_callback"] is not None:
                asyncio.create_task(state["tts_callback"](state["ctx_guild_id"], state["response"]))
            return {
                "messages": [AIMessage(content=f"Response is safe. Response={state['response']}", id="Filter Regex OK")]
            }

        async def filter_response_llm(state):
            filter_result = await filter_chain.filter_chain.ainvoke(state["response"])
            if filter_result["safe"]:
                return {
                    "messages": [AIMessage(content=f"Response is safe. Response={state['response']}", id="Filter OK")],
                }
            else:
                if state["ctx_guild_id"] is not None and state["stop_audio_callback"] is not None:
                    asyncio.create_task(state["stop_audio_callback"](state["ctx_guild_id"]))

                return {
                    "messages": [
                        AIMessage(
                            content=f"Response is unsafe: {filter_result['reason']}. Resposne={state['response']}",
                            id="Filter BAD",
                        )
                    ]
                }

        workflow = StateGraph(AgentState)
        workflow.add_node("iteratively_summarize", iteratively_summarize)
        workflow.add_node("respond", respond)
        workflow.add_node("filter_response_regex", filter_response_regex)
        workflow.add_node("filter_response_llm", filter_response_llm)
        workflow.add_node("retrieve", retrieve)

        workflow.add_edge(START, "iteratively_summarize")
        workflow.add_edge(START, "retrieve")
        workflow.add_edge(["retrieve"], "respond")
        workflow.add_edge(["respond"], "filter_response_regex")
        workflow.add_edge(["filter_response_regex"], "filter_response_llm")
        workflow.add_edge("filter_response_llm", END)
        self.graph = workflow.compile()

    def _save_graph_as_png(self):
        graph = self.graph.get_graph().draw_mermaid()
        graphbytes = graph.encode("ascii")
        base64_bytes = base64.b64encode(graphbytes)
        base64_string = base64_bytes.decode("ascii")
        url = "https://mermaid.ink/svg/" + base64_string
        req = Request(url, headers={"User-Agent": "IPython/Notebook"})
        with open("./src/graph/graph.svg", "wb") as f:
            f.write(urlopen(req).read())
