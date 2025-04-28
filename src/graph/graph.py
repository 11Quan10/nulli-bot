import time
from langsmith import traceable
from langgraph.graph import END, StateGraph, START
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from graph.models import Models
from graph.memory import Memory
from graph.chains.search import SearchChain
from graph.chains.summarize import SummarizeChain
from graph.chains.summarize_iterative import IterativelySummarizeChain
from graph.chains.retrieve import RetrieveChain
from graph.chains.respond import RespondChain
from graph.chains.filter import FilterChain
import base64
from urllib.request import Request, urlopen


class AgentState(TypedDict):
    # The add_messages function defines how an update should be processed
    # Default is to replace. add_messages says "append"
    messages: Annotated[list, add_messages]
    context: str
    current_summary: str
    new_summary: str
    memory: str
    response: str
    start_time: float
    response_time: float


class Graph:
    def __init__(self):
        self.current_summary = ""
        self._build_graph()
        self._save_graph_as_png()

    @traceable
    async def invoke_model(self, context: str):
        results = await self.graph.ainvoke(
            {
                "current_summary": self.current_summary,
                # "context": "Your close friend Ryo Yamada asks: When is your birthday?",
                "context": context,
                "start_time": time.time(),
            }
        )
        print(results)
        return results

    def _build_graph(self):
        models = Models()
        memory = Memory(models.embeddings, models.sparse_embeddings)
        search_chain = SearchChain()
        summarize_chain = SummarizeChain(model_llm=models.model_llm)
        iteratively_summarize_chain = IterativelySummarizeChain(model_llm=models.model_llm)
        retrieve_chain = RetrieveChain(retriever=memory.retriever)
        respond_chain = RespondChain(model_llm=models.model_llm)
        filter_chain = FilterChain(model_guard=models.model_guard)

        async def search(state):
            search_results = await search_chain.search_chain.ainvoke({"context": state["context"]})
            return {"context": search_results, "messages": [AIMessage(content=search_results, id="1")]}

        def is_summary_empty(state) -> Literal["summarize", "iteratively_summarize"]:
            return "summarize" if self.current_summary == "" else "iteratively_summarize"

        async def summarize(state):
            summary = await summarize_chain.summarize_chain.ainvoke({"context": state["context"]})
            self.current_summary = summary
            return {"new_summary": summary, "messages": [AIMessage(content=summary, id="1")]}

        async def iteratively_summarize(state):
            summary = await iteratively_summarize_chain.iteratively_summarize_chain.ainvoke(
                {"current_summary": state["current_summary"], "context": state["context"]}
            )
            self.current_summary = summary
            return {"new_summary": summary, "messages": [AIMessage(content=summary, id="2")]}

        async def retrieve(state):
            memory = await retrieve_chain.retrieve_chain.ainvoke(state["current_summary"] + " " + state["context"])
            return {"memory": memory, "messages": [AIMessage(content=memory, id="6")]}

        async def respond(state):
            response = await respond_chain.respond_chain.ainvoke(
                {"context": state["context"], "new_summary": state["current_summary"], "memory": state["memory"]}
            )
            return {
                "response": response,
                "messages": [AIMessage(content=response, id="3")],
                "response_time": time.time(),
            }

        async def filter_response(state):
            filter_result = await filter_chain.filter_chain.ainvoke(state["response"])
            if filter_result["safe"]:
                return {
                    "messages": [AIMessage(content="response is safe", id="4")],
                }
            else:
                return {"messages": [AIMessage(content=f"response is unsafe: {filter_result['reason']}", id="5")]}

        workflow = StateGraph(AgentState)
        workflow.add_node("summarize", summarize)
        workflow.add_node("iteratively_summarize", iteratively_summarize)
        workflow.add_node("respond", respond)
        workflow.add_node("filter_response", filter_response)
        workflow.add_node("retrieve", retrieve)

        workflow.add_conditional_edges(START, is_summary_empty)
        workflow.add_edge(START, "retrieve")
        workflow.add_edge(["retrieve"], "respond")
        workflow.add_edge("respond", "filter_response")
        workflow.add_edge("filter_response", END)
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
