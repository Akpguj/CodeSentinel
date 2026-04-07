from __future__ import annotations

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from .base import BaseEmbeddingAdapter

import os


class HuggingFaceEmbeddingAdapter(BaseEmbeddingAdapter):
    def __init__(self, model_name: str, hf_token: str):
        if not hf_token:
            hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

        self.embedding = HuggingFaceEndpointEmbeddings(
            repo_id=model_name,
            huggingfacehub_api_token=hf_token,
            timeout=300,
        )

    def get_embedding_model(self):
        return self.embedding
