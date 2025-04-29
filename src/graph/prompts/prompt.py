from graph.prompts._respond_prompt import respond_prompt
from graph.prompts._iteratively_summarize_prompt import iteratively_summarize_prompt


class Prompts:
    def __init__(self):
        self.respond_prompt = respond_prompt
        self.iteratively_summarize_prompt = iteratively_summarize_prompt
