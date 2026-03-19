from __future__ import annotations

from langchain_openai import OpenAIEmbeddings

from .base import BaseEmbeddingAdapter


class OpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    def __init__(self, model_name: str, openai_api_key: str):
        self.embedding = OpenAIEmbeddings(model=model_name, api_key=openai_api_key)

    def get_embedding_model(self):
        return self.embedding
