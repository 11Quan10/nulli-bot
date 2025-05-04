# Prompt
from langchain_core.output_parsers import StrOutputParser

class RespondChain:
    def __init__(self, model_llm):
        self.respond_chain = model_llm | StrOutputParser()
