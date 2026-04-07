# CodeCheck

> LLM-powered PR reviewer that checks code against your style guide and posts structured comments — automatically, on every pull request.

```
┌─────────────────────────────────────────────────────────────┐
│  PR opened  →  CodeCheck reads diff  →  reviews against     │
│  your style guide  →  posts comment with violations + fixes │
└─────────────────────────────────────────────────────────────┘
```

---

## What it does

When a pull request is opened or updated, CodeCheck:

1. Fetches the changed files from the PR
2. Loads your `.github/style_guide.md` and indexes it into a local vector DB
3. For each changed file, retrieves the most relevant rules via semantic search
4. Sends the diff + rules to your chosen LLM with a Chain-of-Thought prompt
5. Posts a structured comment on the PR with every violation, its explanation, and a suggested fix

---

## Quick start (3 steps)

### Step 1 — Add the workflow file

Create `.github/workflows/codecheck.yml` in your repo:

```yaml
name: CodeCheck PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run CodeCheck
        uses: Akpguj/CodeCheck@v2.1.0
        with:
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
          # openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          # groq_api_key: ${{ secrets.GROQ_API_KEY }}
          # anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          # hf_token: ${{ secrets.HF_TOKEN }}
        env:
          PR_NUMBER: ${{ github.event.pull_request.number }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_WORKSPACE: ${{ github.workspace }}
          # OPENAI_BASE_URL: "https://openrouter.ai/api/v1"  # uncomment for OpenRouter
```

Only uncomment the key(s) matching your chosen provider. `GITHUB_TOKEN` is provided by GitHub automatically — no setup needed.

### Step 2 — Add your API key as a secret

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

Add the secret for your chosen provider (e.g. `GOOGLE_API_KEY`).

### Step 3 — Create your style guide

Create `.github/style_guide.md` in your repo. This is the document CodeCheck reviews all code against. Example:

```markdown
## Naming Conventions
- Python functions must use snake_case
- Constants must be UPPER_SNAKE_CASE
- Classes must use PascalCase
- No single-letter variable names except loop counters (i, j, k)

## Security Rules
- Never hardcode API keys, tokens, or passwords in source files
- Load secrets via os.environ or dotenv — never as inline strings
- No print() statements that could expose sensitive data in production

## Code Style
- All functions must have a docstring
- Maximum function length: 50 lines
- No commented-out code in final PRs
```

The richer this file, the better the reviews. CodeCheck uses semantic search to find the most relevant rules for each file it reviews.

That's it. Open a PR and CodeCheck will post a review comment automatically.

---

## Configuration (`sentinel.yml`)

Drop `sentinel.yml` in your repo root to customize behaviour. Everything has a default — this file is optional.

```yaml
# Path to your style guide (default shown)
style_guide: ".github/style_guide.md"

# LLM used to review code
llm:
  provider: "gemini"             # gemini | openai | groq | anthropic | huggingface
  model: "gemini-2.5-flash"

# Embedding model used to index the style guide
embedding:
  provider: "openai"             # openai | gemini | huggingface
  model: "text-embedding-3-small"

# Local vector DB (no external service needed)
vector_db:
  provider: "chroma"             # chroma | faiss
  index_name: "sentinel-style-guide"

# Review behaviour
cost_tracking: true              # logs estimated token usage per review
max_files_per_pr: 20             # cap to avoid very large PRs running up costs
top_k_rules: 4                   # how many style guide chunks to retrieve per file

# Which file types get reviewed — customize for your stack
reviewable_extensions:
  - ".py"
  - ".js"
  - ".ts"
  - ".jsx"
  - ".tsx"
  - ".java"
  - ".go"
  - ".rs"
  - ".cpp"
  - ".c"
  - ".yaml"     # catches hardcoded secrets in config files
  - ".yml"
  - ".env"      # catches accidental key commits
```

---

## Choosing a provider

### Provider combinations

| Goal | `llm.provider` + model | `embedding.provider` + model | Secrets needed |
|---|---|---|---|
| Free, easiest setup | `gemini` / `gemini-1.5-flash` | `gemini` / `models/text-embedding-004` | `GOOGLE_API_KEY` only |
| Best review quality | `anthropic` / `claude-haiku-4-5` | `openai` / `text-embedding-3-small` | `ANTHROPIC_API_KEY` + `OPENAI_API_KEY` |
| Open-source via API | `groq` / `llama-3.1-8b-instant` | `huggingface` / `sentence-transformers/all-MiniLM-L6-v2` | `GROQ_API_KEY` + `HF_TOKEN` |
| Any model (OpenRouter) | `openai` + set `OPENAI_BASE_URL` | `openai` / `text-embedding-3-small` | `OPENAI_API_KEY` (OpenRouter key) |

### All supported model strings

**Gemini** (`provider: gemini`)

**OpenAI** (`provider: openai`)

**Groq** (`provider: groq`) — free tier available

**Anthropic** (`provider: anthropic`)

**HuggingFace** (`provider: huggingface`) — uses Serverless Inference API, no local weights

**OpenRouter** (`provider: openai`) — access 100+ models with one API key

### Embedding model strings

**OpenAI** (`provider: openai`)

**Gemini** (`provider: gemini`)

**HuggingFace** (`provider: huggingface`) — Serverless Inference API

---

## Full workflow example

Below is a complete workflow showing all available options with comments:

```yaml
name: CodeCheck PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
  # Optional: also run on draft PRs
  # pull_request:
  #   types: [opened, synchronize, reopened, ready_for_review]

jobs:
  review:
    runs-on: ubuntu-latest

    # Optional: skip draft PRs
    # if: github.event.pull_request.draft == false

    steps:
      - uses: actions/checkout@v4

      - name: Run CodeCheck
        uses: Akpguj/CodeCheck@v2.1.0
        with:
          # Uncomment only the key(s) your chosen provider needs.
          # If both your LLM and embedding use the same provider,
          # you only need that one key.
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
          # openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          # groq_api_key: ${{ secrets.GROQ_API_KEY }}
          # anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          # hf_token: ${{ secrets.HF_TOKEN }}
        env:
          # Required — auto-provided by GitHub, no setup needed
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          GITHUB_WORKSPACE: ${{ github.workspace }}

          # Optional — only needed if using OpenRouter
          # OPENAI_BASE_URL: "https://openrouter.ai/api/v1"
```

---

## How the review comment looks

CodeCheck posts one comment per reviewed file. Each comment follows this structure:

```
## CodeCheck | `src/auth/token.py`
> Overall: 2 violations found in this file.
---

### 2 violation(s) found

#### Issue 1 — Security
Rationale:
API key is hardcoded as a string literal. Per the style guide security rules,
secrets must be loaded from environment variables, never stored in source code.

Current code:
```python
API_KEY = "sk-abc123xyz"
```

Suggested fix:
```python
import os
API_KEY = os.environ.get("API_KEY")
```

#### Issue 2 — Naming Convention
Rationale:
Function name `ProcessUserData` uses PascalCase. Per the style guide,
Python functions must use snake_case.

Current code:
```python
def ProcessUserData(user_id):
```

Suggested fix:
```python
def process_user_data(user_id):
```
```

---

## Troubleshooting

**The action runs but posts no comment**

Check that `GITHUB_TOKEN` has `pull-requests: write` permission. Add this to your job:

```yaml
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
```

**"Style guide not found" error**

Make sure `.github/style_guide.md` exists in your repo and the path in `sentinel.yml` matches exactly. The path is relative to the repo root.

**"Missing environment variable" error**

You have a provider set in `sentinel.yml` but the matching key wasn't passed in the workflow. The error message tells you exactly which key to add. For example, if you set `provider: "groq"`, you must uncomment `groq_api_key` in the workflow `with:` block and add `GROQ_API_KEY` to your repo secrets.

**Review comment says "response could not be parsed"**

This happens occasionally with smaller models (HuggingFace free tier, small Groq models) that don't reliably return structured JSON. Switch to a larger model or a different provider. Gemini 1.5 Flash and GPT-4o-mini are the most reliable for structured output.

**The action is very slow (5+ minutes)**

This is almost always the embedding step when using HuggingFace embeddings on a large style guide. Switch to `openai` or `gemini` embeddings — they are significantly faster for the indexing step.

---

## Running locally (for development)

```bash
# Install dependencies
pip install -r requirements.txt

# Set required environment variables
export GOOGLE_API_KEY="your-key"
export GITHUB_TOKEN="your-personal-access-token"
export GITHUB_REPOSITORY="your-username/your-repo"
export PR_NUMBER="1"
export GITHUB_WORKSPACE="."

# Run
python -m codecheck.pr_reviewer
```

To generate a GitHub Personal Access Token: GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained. Grant `pull-requests: read/write` and `contents: read` on your test repo.

---

## Repository layout

```
CodeCheck/
├── action.yml                  # GitHub Action definition
├── Dockerfile                  # container built by GitHub on every run
├── requirements.txt
├── sentinel.yml                # default config (used for CodeCheck's own repo)
├── .github/
│   └── style_guide.md          # default style guide
├── codecheck/
│   ├── pr_reviewer.py          # main entrypoint and LangGraph workflow
│   ├── config.py               # sentinel.yml loader and defaults
│   ├── router.py               # provider routing (LLM / embedding / vector DB)
│   └── adapters/
│       ├── llm/                # gemini, openai, groq, anthropic, huggingface
│       ├── embedding/          # openai, gemini, huggingface
│       └── vectordb/           # chroma, faiss
└── README.md
```

---

## Tech stack

| Component | Default | Alternatives |
|---|---|---|
| LLM | Gemini 1.5 Flash | OpenAI, Groq, Anthropic, HuggingFace |
| Embeddings | OpenAI text-embedding-3-small | Gemini, HuggingFace |
| Vector DB | ChromaDB (in-memory) | FAISS |
| Orchestration | LangGraph | — |
| GitHub integration | PyGitHub | — |

## Privacy
CodeCheck does not store, log, or retain any code or PR content.
All data flows directly from GitHub to your chosen LLM API and is
not persisted anywhere by this action.
