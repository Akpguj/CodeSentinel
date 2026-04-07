from __future__ import annotations

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from .base import BaseLLMAdapter

import os


class HuggingFaceAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str, hf_token: str):
        # Ensure model_name and hf_token are provided
        if not model_name:
            raise ValueError("model_name must be provided for HuggingFaceAdapter")
        if not hf_token:
            # Fallback to check environment if hf_token is not passed
            hf_token = hf_token or os.getenv("HUGGINGFACEHUB_API_TOKEN")
            if not hf_token:
                raise ValueError("hf_token must be provided or HUGGINGFACEHUB_API_TOKEN set in environment")

        endpoint = HuggingFaceEndpoint(
            repo_id=model_name,
            huggingfacehub_api_token=hf_token,
            temperature=0.1,
            max_new_tokens=1024,
            task="text-generation",
            timeout=300,
        )
        self.llm = ChatHuggingFace(llm=endpoint)

    def invoke(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return getattr(response, "content", str(response))

    def get_token_count(self, text: str) -> int:
        return len(text.split())
