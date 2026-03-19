from __future__ import annotations

from importlib import import_module

from .base import BaseVectorDBAdapter


class QdrantAdapter(BaseVectorDBAdapter):
    def __init__(self, collection_name: str = "sentinel-style-guide"):
        self.collection_name = collection_name

    def build_retriever(self, texts: list[str], embedding_model, top_k: int):
        qdrant_module = import_module("langchain_qdrant")
        store_cls = getattr(qdrant_module, "QdrantVectorStore")
        store = store_cls.from_texts(
            texts=texts,
            embedding=embedding_model,
            collection_name=self.collection_name,
            location=":memory:",
        )
        return store.as_retriever(search_kwargs={"k": top_k})
