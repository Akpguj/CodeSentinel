from __future__ import annotations

from langchain_groq import ChatGroq

from .base import BaseLLMAdapter


class GroqAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str, groq_api_key: str):
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.1,
            api_key=groq_api_key,
        )

    def invoke(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return getattr(response, "content", str(response))

    def get_token_count(self, text: str) -> int:
        return len(text.split())