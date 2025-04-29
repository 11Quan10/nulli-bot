from langchain_core.output_parsers import StrOutputParser


class IterativelySummarizeChain:
    def __init__(self, prompt, model_llm):
        self.iteratively_summarize_chain = prompt | model_llm | StrOutputParser()
