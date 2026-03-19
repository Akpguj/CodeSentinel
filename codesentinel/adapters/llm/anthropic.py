from __future__ import annotations

from langchain_anthropic import ChatAnthropic

from .base import BaseLLMAdapter


class AnthropicAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str, anthropic_api_key: str):
        self.llm = ChatAnthropic(
            model=model_name,
            temperature=0.1,
            api_key=anthropic_api_key,
            max_tokens=1024,
        )

    def invoke(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return getattr(response, "content", str(response))

    def get_token_count(self, text: str) -> int:
        return len(text.split())