from __future__ import annotations

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from .base import BaseEmbeddingAdapter


class GeminiEmbeddingAdapter(BaseEmbeddingAdapter):
    def __init__(self, model_name: str, google_api_key: str):
        self.embedding = GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=google_api_key,
        )

    def get_embedding_model(self):
        return self.embedding