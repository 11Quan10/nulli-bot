from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


class SearchChain:
    def __init__(self):
        self.search_chain = DuckDuckGoSearchResults(
            api_wrapper=DuckDuckGoSearchAPIWrapper(region="us-en", max_results=10), output_format="list"
        )
