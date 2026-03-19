from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseEmbeddingAdapter(ABC):
    @abstractmethod
    def get_embedding_model(self) -> Any:
        raise NotImplementedError
