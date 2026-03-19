from __future__ import annotations

import logging
import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import List, Optional, TypedDict

from github import Auth, Github
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from codesentinel.config import SentinelConfig, load_config
from codesentinel.router import get_embedding_adapter, get_llm_adapter, get_vectordb_adapter


class Issue(BaseModel):
	line_reference: str = Field(description="The exact problematic line or snippet from the diff")
	violation_type: str = Field(description="Category: Naming Convention | Security | Code Style | Other")
	explanation: str = Field(description="Why this violates the style rule, referencing the rule text")
	suggestion: str = Field(description="The corrected/refactored version of the line or block")


class ReviewOutput(BaseModel):
	summary: str = Field(description="One sentence overall assessment of the PR changes")
	passed: bool = Field(description="True if zero violations found, False otherwise")
	issues: List[Issue] = Field(description="All violations found. Must be empty when passed=true")


class ReviewState(TypedDict):
	pr_number: int
	repo_name: str
	github_token: str
	pr_files: List[dict]
	current_file_idx: int
	style_rules: str
	review_result: Optional[dict]
	comment_body: str
	comments_posted: int


def build_retriever(config: SentinelConfig):
	style_path = Path(config.style_guide)
	if not style_path.exists():
		raise FileNotFoundError(f"Style guide not found: {style_path}")

	style_text = style_path.read_text(encoding="utf-8")
	splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
	chunks = splitter.split_text(style_text)

	embedding_adapter = get_embedding_adapter(config)
	vectordb_adapter = get_vectordb_adapter(config)

	return vectordb_adapter.build_retriever(
		texts=chunks,
		embedding_model=embedding_adapter.get_embedding_model(),
		top_k=config.top_k_rules,
	)


def build_llm_runtime(config: SentinelConfig):
	llm = get_llm_adapter(config)
	parser = JsonOutputParser(pydantic_object=ReviewOutput)
	prompt = PromptTemplate(
		input_variables=["filename", "code_diff", "style_rules"],
		partial_variables={"format_instructions": parser.get_format_instructions()},
		template="""
You are CodeSentinel, a senior code reviewer AI. Review added lines in a PR diff against style rules.

File: {filename}

Rules:
{style_rules}

Diff:
{code_diff}

Check for naming, security, and style issues. For each violation include exact line, explanation, and fix.
If no violations exist, return passed=true and issues=[].

Return valid JSON only.
{format_instructions}
""",
	)
	return llm, prompt, parser


def fetch_pr_files(state: ReviewState, config: SentinelConfig) -> dict:
	logging.info("Node: fetch_pr_files")
	auth = Auth.Token(state["github_token"])
	gh = Github(auth=auth)
	repo = gh.get_repo(state["repo_name"])
	pr = repo.get_pull(state["pr_number"])

	files = [
		{"filename": f.filename, "patch": f.patch, "status": f.status}
		for f in pr.get_files()
		if f.filename.endswith(config.reviewable_extensions) and f.patch
	]

	max_files = max(1, config.max_files_per_pr)
	files = files[:max_files]
	return {"pr_files": files, "current_file_idx": 0, "comments_posted": 0}


def retrieve_rules(state: ReviewState, retriever) -> dict:
	logging.info("Node: retrieve_rules")
	idx = state["current_file_idx"]
	patch = state["pr_files"][idx]["patch"]
	docs = retriever.invoke(patch)
	rules = "\n\n---\n\n".join(doc.page_content for doc in docs) if docs else "No specific rules found."
	return {"style_rules": rules}


def _llm_output_to_text(raw) -> str:
	# Some providers return content blocks (list[dict]) instead of a plain string.
	content = getattr(raw, "content", raw)
	if isinstance(content, str):
		return content

	if isinstance(content, dict):
		text_value = content.get("text")
		if isinstance(text_value, str):
			return text_value
		return str(content)

	if isinstance(content, Iterable) and not isinstance(content, (str, bytes)):
		parts: list[str] = []
		for item in content:
			if isinstance(item, str):
				parts.append(item)
				continue
			if isinstance(item, dict):
				text_value = item.get("text")
				if isinstance(text_value, str):
					parts.append(text_value)
				continue
			parts.append(str(item))
		return "\n".join(part for part in parts if part).strip()

	return str(content)


def review_code(state: ReviewState, llm, prompt, parser) -> dict:
	logging.info("Node: review_code")
	idx = state["current_file_idx"]
	file_info = state["pr_files"][idx]
	rendered_prompt = prompt.format(
		filename=file_info["filename"],
		code_diff=file_info["patch"],
		style_rules=state["style_rules"],
	)
	raw = llm.invoke(rendered_prompt)
	parsed = parser.parse(_llm_output_to_text(raw))
	return {"review_result": parsed}


def format_comment(state: ReviewState) -> dict:
	logging.info("Node: format_comment")
	idx = state["current_file_idx"]
	filename = state["pr_files"][idx]["filename"]
	review = state["review_result"] or {}

	ext_map = {
		".py": "python",
		".js": "javascript",
		".ts": "typescript",
		".jsx": "jsx",
		".tsx": "tsx",
		".java": "java",
		".go": "go",
		".rs": "rust",
		".cpp": "cpp",
		".c": "c",
		".yaml": "yaml",
		".yml": "yaml",
	}
	lang = ext_map.get(Path(filename).suffix, "")

	issues = review.get("issues", [])
	passed = review.get("passed", True)
	summary = review.get("summary", "")

	lines = [f"## CodeSentinel | `{filename}`", f"> {summary}", "---"]
	if passed or not issues:
		lines.append("### No issues found. Great job!")
	else:
		lines.append(f"### {len(issues)} Violation(s) Found")
		for i, issue in enumerate(issues, 1):
			violation = issue.get("violation_type", "Style Issue")
			lines.extend(
				[
					"<details open>",
					f"<summary><b>Issue #{i}: {violation}</b></summary>",
					"",
					"| Property | Details |",
					"| :--- | :--- |",
					f"| Type | {violation} |",
					f"| Context | `{filename}` |",
					"",
					"#### Rationale",
					issue.get("explanation", ""),
					"",
					"#### Current Code",
					f"```{lang}",
					issue.get("line_reference", ""),
					"```",
					"",
					"#### Suggested Fix",
					f"```{lang}",
					issue.get("suggestion", ""),
					"```",
					"</details>",
					"",
				]
			)

	return {"comment_body": "\n".join(lines)}


def post_comment(state: ReviewState) -> dict:
	logging.info("Node: post_comment")
	auth = Auth.Token(state["github_token"])
	gh = Github(auth=auth)
	repo = gh.get_repo(state["repo_name"])
	pr = repo.get_pull(state["pr_number"])
	pr.create_issue_comment(state["comment_body"])

	return {
		"comments_posted": state["comments_posted"] + 1,
		"current_file_idx": state["current_file_idx"] + 1,
	}


def no_files_to_review(state: ReviewState) -> dict:
	logging.info("Node: no_files_to_review")
	return {}


def route_after_fetch(state: ReviewState) -> str:
	return "no_files_to_review" if not state["pr_files"] else "retrieve_rules"


def route_after_post(state: ReviewState) -> str:
	if state["current_file_idx"] < len(state["pr_files"]):
		return "retrieve_rules"
	return END


def build_graph(config: SentinelConfig, retriever, llm, prompt, parser):
	graph = StateGraph(ReviewState)

	def _fetch(state):
		return fetch_pr_files(state, config)

	def _retrieve(state):
		return retrieve_rules(state, retriever)

	def _review(state):
		return review_code(state, llm, prompt, parser)

	graph.add_node("fetch_pr_files", _fetch)
	graph.add_node("retrieve_rules", _retrieve)
	graph.add_node("review_code", _review)
	graph.add_node("format_comment", format_comment)
	graph.add_node("post_comment", post_comment)
	graph.add_node("no_files_to_review", no_files_to_review)

	graph.set_entry_point("fetch_pr_files")
	graph.add_conditional_edges(
		"fetch_pr_files",
		route_after_fetch,
		{"retrieve_rules": "retrieve_rules", "no_files_to_review": "no_files_to_review"},
	)
	graph.add_edge("retrieve_rules", "review_code")
	graph.add_edge("review_code", "format_comment")
	graph.add_edge("format_comment", "post_comment")
	graph.add_conditional_edges("post_comment", route_after_post, {"retrieve_rules": "retrieve_rules", END: END})
	graph.add_edge("no_files_to_review", END)

	return graph.compile()


def main() -> None:
	logging.basicConfig(level=logging.INFO, format="%(message)s")

	# Docker-based GitHub Actions expose action inputs as INPUT_<NAME>.
	env_aliases = {
		"HF_TOKEN": "INPUT_HF_TOKEN",
		"GOOGLE_API_KEY": "INPUT_GOOGLE_API_KEY",
		"OPENAI_API_KEY": "INPUT_OPENAI_API_KEY",
		"GROQ_API_KEY": "INPUT_GROQ_API_KEY",
		"ANTHROPIC_API_KEY": "INPUT_ANTHROPIC_API_KEY",
	}
	for target, source in env_aliases.items():
		if not os.environ.get(target) and os.environ.get(source):
			os.environ[target] = os.environ[source]

	config = load_config()

	github_token = os.environ.get("GITHUB_TOKEN")
	repo_name = os.environ.get("GITHUB_REPOSITORY")
	pr_number = os.environ.get("PR_NUMBER")

	if not all([github_token, repo_name, pr_number]):
		logging.error("Missing env vars: GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER")
		sys.exit(1)

	retriever = build_retriever(config)
	llm, prompt, parser = build_llm_runtime(config)
	app = build_graph(config, retriever, llm, prompt, parser)

	final_state = app.invoke(
		{
			"pr_number": int(pr_number),
			"repo_name": repo_name,
			"github_token": github_token,
			"pr_files": [],
			"current_file_idx": 0,
			"style_rules": "",
			"review_result": None,
			"comment_body": "",
			"comments_posted": 0,
		}
	)
	logging.info("CodeSentinel done. Posted %s review comment(s).", final_state.get("comments_posted", 0))


if __name__ == "__main__":
	main()
