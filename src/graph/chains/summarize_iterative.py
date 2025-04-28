from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

refine_template = """
Produce a final summary.

Existing conversation summary up to this point:
{current_summary}

New context:
------------
{context}
------------

Given the new context, refine the original summary.
"""
refine_prompt = ChatPromptTemplate(
    [
        (
            "system",
            "You are Bocchi from Bocchi the Rock. You are nervous, awkward, and introverted. Summarize the following conversation and keep track of who did and said what.",
        ),
        ("human", refine_template),
    ]
)


class IterativelySummarizeChain:
    def __init__(self, model_llm):
        self.iteratively_summarize_chain = refine_prompt | model_llm | StrOutputParser()
