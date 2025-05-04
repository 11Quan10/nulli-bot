from langchain_core.output_parsers import StrOutputParser


class IterativelySummarizeChain:
    def __init__(self, model_llm):
        self.iteratively_summarize_chain = model_llm | StrOutputParser()
