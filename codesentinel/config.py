from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class ProviderConfig:
	provider: str
	model: str


@dataclass
class VectorDBConfig:
	provider: str
	index_name: str = "sentinel-style-guide"


@dataclass
class SentinelConfig:
	style_guide: str
	llm: ProviderConfig
	embedding: ProviderConfig
	vector_db: VectorDBConfig
	cost_tracking: bool
	max_files_per_pr: int
	top_k_rules: int
	reviewable_extensions: tuple[str, ...]


DEFAULT_CONFIG: Dict[str, Any] = {
	"style_guide": ".github/style_guide.md",
	"llm": {
		"provider": "gemini",
		"model": "gemini-3.1-flash-lite-preview",
	},
	"embedding": {
		"provider": "openai",
		"model": "text-embedding-3-small",
	},
	"vector_db": {
		"provider": "chroma",
		"index_name": "sentinel-style-guide",
	},
	"cost_tracking": True,
	"max_files_per_pr": 20,
	"top_k_rules": 4,
	"reviewable_extensions": [
		".py",
		".js",
		".ts",
		".jsx",
		".tsx",
		".java",
		".go",
		".rs",
		".cpp",
		".c",
		".yaml",
		".yml",
		".env",
	],
}


def _merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
	merged = dict(base)
	for key, value in override.items():
		if isinstance(value, dict) and isinstance(merged.get(key), dict):
			merged[key] = _merge_dict(merged[key], value)
		else:
			merged[key] = value
	return merged


def _to_sentinel_config(raw: Dict[str, Any]) -> SentinelConfig:
	llm = raw["llm"]
	embedding = raw["embedding"]
	vector_db = raw["vector_db"]

	return SentinelConfig(
		style_guide=str(raw["style_guide"]),
		llm=ProviderConfig(provider=str(llm["provider"]), model=str(llm["model"])),
		embedding=ProviderConfig(provider=str(embedding["provider"]), model=str(embedding["model"])),
		vector_db=VectorDBConfig(
			provider=str(vector_db["provider"]),
			index_name=str(vector_db.get("index_name", "sentinel-style-guide")),
		),
		cost_tracking=bool(raw.get("cost_tracking", True)),
		max_files_per_pr=int(raw.get("max_files_per_pr", 20)),
		top_k_rules=int(raw.get("top_k_rules", 4)),
		reviewable_extensions=tuple(
			raw.get(
				"reviewable_extensions",
				[
					".py",
					".js",
					".ts",
					".jsx",
					".tsx",
					".java",
					".go",
					".rs",
					".cpp",
					".c",
					".yaml",
					".yml",
					".env",
				],
			)
		),
	)


def load_config(repo_root: str | Path | None = None) -> SentinelConfig:
	root = Path(repo_root) if repo_root else Path.cwd()
	cfg_path = root / "sentinel.yml"

	cfg = DEFAULT_CONFIG
	if cfg_path.exists():
		with cfg_path.open("r", encoding="utf-8") as fh:
			parsed = yaml.safe_load(fh) or {}
		if not isinstance(parsed, dict):
			raise ValueError("sentinel.yml must be a YAML object")
		cfg = _merge_dict(DEFAULT_CONFIG, parsed)

	return _to_sentinel_config(cfg)
