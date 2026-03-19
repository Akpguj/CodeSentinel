from __future__ import annotations

from importlib import import_module

from .base import BaseLLMAdapter


class OllamaAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str):
        chat_module = import_module("langchain_ollama")
        chat_cls = getattr(chat_module, "ChatOllama")
        self.llm = chat_cls(model=model_name, temperature=0.1)

    def invoke(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return getattr(response, "content", str(response))

    def get_token_count(self, text: str) -> int:
        return len(text.split())
