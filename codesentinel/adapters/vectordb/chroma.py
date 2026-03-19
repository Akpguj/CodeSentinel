from __future__ import annotations

import chromadb
from langchain_chroma import Chroma

from .base import BaseVectorDBAdapter


class ChromaAdapter(BaseVectorDBAdapter):
    def __init__(self, collection_name: str = "sentinel-style-guide"):
        self.collection_name = collection_name
        self.client = chromadb.EphemeralClient()

    def build_retriever(self, texts: list[str], embedding_model, top_k: int):
        store = Chroma.from_texts(
            texts=texts,
            embedding=embedding_model,
            client=self.client,
            collection_name=self.collection_name,
        )
        return store.as_retriever(search_kwargs={"k": top_k})
