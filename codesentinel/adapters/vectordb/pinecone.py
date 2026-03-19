from __future__ import annotations

from langchain_pinecone import PineconeVectorStore

from .base import BaseVectorDBAdapter


class PineconeAdapter(BaseVectorDBAdapter):
    def __init__(self, index_name: str):
        self.index_name = index_name

    def build_retriever(self, texts: list[str], embedding_model, top_k: int):
        store = PineconeVectorStore.from_texts(
            texts=texts,
            embedding=embedding_model,
            index_name=self.index_name,
        )
        return store.as_retriever(search_kwargs={"k": top_k})
