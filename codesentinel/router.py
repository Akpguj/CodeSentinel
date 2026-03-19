from __future__ import annotations

import os

from codesentinel.adapters.embedding.base import BaseEmbeddingAdapter
from codesentinel.adapters.llm.base import BaseLLMAdapter
from codesentinel.adapters.vectordb.base import BaseVectorDBAdapter
from codesentinel.config import SentinelConfig


def _require_env(name: str) -> str:
	value = os.environ.get(name)
	if not value:
		provider_hint = {
			"GOOGLE_API_KEY": "gemini",
			"OPENAI_API_KEY": "openai",
			"GROQ_API_KEY": "groq",
			"ANTHROPIC_API_KEY": "anthropic",
			"HF_TOKEN": "huggingface",
		}
		hint = provider_hint.get(name, "selected provider")
		raise ValueError(
			f"\n\nCodeSentinel Error: Missing environment variable '{name}'\n"
			f"You have provider: '{hint}' set in sentinel.yml but the key was not passed.\n"
			"Fix: In your workflow file, uncomment this line under 'with:':\n"
			f"  {name.lower()}: ${{{{ secrets.{name} }}}}\n"
			"Then add the secret in: Settings -> Secrets -> Actions -> New repository secret\n"
		)
	return value


def get_llm_adapter(config: SentinelConfig) -> BaseLLMAdapter:
	provider = config.llm.provider.lower()
	model = config.llm.model

	if provider == "huggingface":
		from codesentinel.adapters.llm.huggingface import HuggingFaceAdapter

		return HuggingFaceAdapter(model_name=model, hf_token=_require_env("HF_TOKEN"))

	if provider == "anthropic":
		from codesentinel.adapters.llm.anthropic import AnthropicAdapter

		return AnthropicAdapter(model_name=model, anthropic_api_key=_require_env("ANTHROPIC_API_KEY"))

	if provider == "gemini":
		from codesentinel.adapters.llm.gemini import GeminiAdapter

		return GeminiAdapter(model_name=model, google_api_key=_require_env("GOOGLE_API_KEY"))

	if provider == "openai":
		from codesentinel.adapters.llm.openai import OpenAIAdapter

		return OpenAIAdapter(model_name=model, openai_api_key=_require_env("OPENAI_API_KEY"))

	if provider == "groq":
		from codesentinel.adapters.llm.groq import GroqAdapter

		return GroqAdapter(model_name=model, groq_api_key=_require_env("GROQ_API_KEY"))

	raise ValueError(
		f"Unknown llm.provider: '{provider}'\n"
		"Supported: gemini | openai | groq | anthropic | huggingface"
	)


def get_embedding_adapter(config: SentinelConfig) -> BaseEmbeddingAdapter:
	provider = config.embedding.provider.lower()
	model = config.embedding.model

	if provider == "huggingface":
		from codesentinel.adapters.embedding.huggingface import HuggingFaceEmbeddingAdapter

		return HuggingFaceEmbeddingAdapter(model_name=model, hf_token=_require_env("HF_TOKEN"))

	if provider == "gemini":
		from codesentinel.adapters.embedding.gemini import GeminiEmbeddingAdapter

		return GeminiEmbeddingAdapter(model_name=model, google_api_key=_require_env("GOOGLE_API_KEY"))

	if provider == "openai":
		from codesentinel.adapters.embedding.openai import OpenAIEmbeddingAdapter

		return OpenAIEmbeddingAdapter(model_name=model, openai_api_key=_require_env("OPENAI_API_KEY"))

	raise ValueError(
		f"Unknown embedding.provider: '{provider}'\n"
		"Supported: openai | gemini | huggingface"
	)


def get_vectordb_adapter(config: SentinelConfig) -> BaseVectorDBAdapter:
	provider = config.vector_db.provider.lower()
	index_name = config.vector_db.index_name

	if provider == "chroma":
		from codesentinel.adapters.vectordb.chroma import ChromaAdapter

		return ChromaAdapter(collection_name=index_name)

	if provider == "faiss":
		from codesentinel.adapters.vectordb.faiss import FaissAdapter

		return FaissAdapter()

	raise ValueError(
		f"Unknown vector_db.provider: '{provider}'\n"
		"Supported: chroma | faiss"
	)
