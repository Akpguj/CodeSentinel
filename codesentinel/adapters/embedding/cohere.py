from __future__ import annotations

from importlib import import_module

from .base import BaseEmbeddingAdapter


class CohereEmbeddingAdapter(BaseEmbeddingAdapter):
    def __init__(self, model_name: str, cohere_api_key: str):
        cohere_module = import_module("langchain_cohere")
        embedding_cls = getattr(cohere_module, "CohereEmbeddings")
        self.embedding = embedding_cls(model=model_name, cohere_api_key=cohere_api_key)

    def get_embedding_model(self):
        return self.embedding
