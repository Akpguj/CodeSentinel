from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseVectorDBAdapter(ABC):
    @abstractmethod
    def build_retriever(self, texts: list[str], embedding_model: Any, top_k: int):
        raise NotImplementedError
