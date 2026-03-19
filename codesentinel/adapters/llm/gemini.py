from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI

from .base import BaseLLMAdapter


class GeminiAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str, google_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.1,
            google_api_key=google_api_key,
        )

    def invoke(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return getattr(response, "content", str(response))

    def get_token_count(self, text: str) -> int:
        return len(text.split())
