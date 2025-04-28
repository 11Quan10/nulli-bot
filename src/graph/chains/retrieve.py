def get_document_content(documents):
    return " | ".join([document.page_content for document in documents])


class RetrieveChain:
    def __init__(self, retriever):
        self.retriever = retriever
        self.retrieve_chain = retriever | (lambda documents: get_document_content(documents))
