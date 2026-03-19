from __future__ import annotations

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from .base import BaseLLMAdapter


class HuggingFaceAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str, hf_token: str):
        endpoint = HuggingFaceEndpoint(
            repo_id=model_name,
            huggingfacehub_api_token=hf_token,
            temperature=0.1,
            max_new_tokens=1024,
            task="text-generation",
        )
        self.llm = ChatHuggingFace(llm=endpoint)

    def invoke(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return getattr(response, "content", str(response))

    def get_token_count(self, text: str) -> int:
        return len(text.split())
