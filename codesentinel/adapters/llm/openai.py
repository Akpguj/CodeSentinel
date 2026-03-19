from __future__ import annotations

from langchain_openai import ChatOpenAI

from .base import BaseLLMAdapter


class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str, openai_api_key: str):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1, api_key=openai_api_key)

    def invoke(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return getattr(response, "content", str(response))

    def get_token_count(self, text: str) -> int:
        return len(text.split())
