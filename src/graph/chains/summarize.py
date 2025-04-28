from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

summarize_prompt = ChatPromptTemplate(
    [
        (
            "system",
            "You are Bocchi from Bocchi the Rock. You are nervous, awkward, and introverted. Summarize the following conversation and keep track of who did and said what.",
        ),
        ("human", "Here is the conversation to summarize. {context}"),
    ]
)


class SummarizeChain:
    def __init__(self, model_llm):
        self.summarize_chain = summarize_prompt | model_llm | StrOutputParser()
