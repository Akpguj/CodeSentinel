from __future__ import annotations

from langchain_community.vectorstores import FAISS

from .base import BaseVectorDBAdapter


class FaissAdapter(BaseVectorDBAdapter):
    def build_retriever(self, texts: list[str], embedding_model, top_k: int):
        store = FAISS.from_texts(texts=texts, embedding=embedding_model)
        return store.as_retriever(search_kwargs={"k": top_k})
