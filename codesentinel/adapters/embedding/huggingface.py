from __future__ import annotations

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from .base import BaseEmbeddingAdapter


class HuggingFaceEmbeddingAdapter(BaseEmbeddingAdapter):
    def __init__(self, model_name: str, hf_token: str):
        self.embedding = HuggingFaceEndpointEmbeddings(
            model=model_name,
            huggingfacehub_api_token=hf_token,
        )

    def get_embedding_model(self):
        return self.embedding
