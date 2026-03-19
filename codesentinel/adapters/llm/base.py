from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLMAdapter(ABC):
    @abstractmethod
    def invoke(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_token_count(self, text: str) -> int:
        raise NotImplementedError
