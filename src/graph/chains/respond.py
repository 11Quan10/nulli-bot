# Prompt
from langchain_core.output_parsers import StrOutputParser

class RespondChain:
    def __init__(self, prompt, model_llm):
        self.respond_chain = prompt | model_llm | StrOutputParser()
