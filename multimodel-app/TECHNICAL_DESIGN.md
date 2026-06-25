# Technical Design Document
# LLM Arena — Multi-Model Comparison Tool

**Version:** 1.0  
**Date:** 2026-06-20  
**Author:** TechVest Global  
**Status:** Active

---

## 1. Overview

LLM Arena is a Python-based tool that sends a single user prompt to multiple large language models (LLMs) simultaneously via the OpenRouter API and returns each model's answer alongside its latency, token usage, and cost. It exposes two interfaces: a terminal CLI and a Streamlit web UI.

---

## 2. Goals and Non-Goals

### Goals
- Query multiple LLMs in a single run from one prompt
- Measure and display latency, token counts, and cost per model
- Provide a polished web UI for non-technical users
- Keep all models on the free tier (zero cost to operate)
- Isolate failures — one model erroring must not block others

### Non-Goals
- Streaming responses (full response is awaited before display)
- User authentication or session management
- Persistent storage of comparison history
- Fine-tuning or training models

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        User                             │
│          Browser (Web UI)  │  Terminal (CLI)            │
└────────────────┬───────────┴────────────────────────────┘
                 │
     ┌───────────▼───────────┐
     │        app.py         │   Streamlit Web UI
     │  (imports from main)  │
     └───────────┬───────────┘
                 │  calls ask()
     ┌───────────▼───────────┐
     │        main.py        │   Core Logic Layer
     │  ask() / MODELS /     │
     │  PRICES / print_table │
     └───────────┬───────────┘
                 │  HTTPS / OpenAI-compatible API
     ┌───────────▼───────────┐
     │    OpenRouter API     │   https://openrouter.ai/api/v1
     │  (model routing hub)  │
     └───────────┬───────────┘
                 │
     ┌───────────▼───────────────────────────────────────┐
     │              LLM Providers                        │
     │  Google (Gemma)  │  OpenAI OSS  │  Mistral       │
     └───────────────────────────────────────────────────┘
```

---

## 4. File Structure

```
multimodel-app/
├── main.py            # Core logic: ask(), MODELS, PRICES, CLI entry point
├── app.py             # Streamlit web UI
├── requirements.txt   # Python dependencies
├── .env               # API key — never committed to git
├── .gitignore         # Excludes .env and __pycache__
├── spec.md            # Product specification
├── README.md          # Setup and usage guide
└── TECHNICAL_DESIGN.md  # This document
```

---

## 5. Core Module — main.py

### 5.1 Configuration

| Constant | Type | Purpose |
|---|---|---|
| `MODELS` | `list[str]` | Ordered list of OpenRouter model IDs to query |
| `PRICES` | `dict[str, tuple]` | Maps each model to `(input_price, output_price)` in USD per 1M tokens |
| `QUESTION` | `str` | Hardcoded prompt used by the CLI runner |
| `REQUEST_TIMEOUT` | `int` | Per-call timeout in seconds (default: 60) |
| `PREVIEW_LEN` | `int` | Max characters shown in the CLI table preview (default: 120) |

### 5.2 Active Models

| Model ID | Label | Provider | Size |
|---|---|---|---|
| `google/gemma-4-31b-it:free` | Gemma 4 31B | Google | 31B |
| `openai/gpt-oss-20b:free` | GPT-OSS 20B | OpenAI OSS | 20B |
| `openai/gpt-oss-120b:free` | GPT-OSS 120B | OpenAI OSS | 120B |
| `mistralai/mistral-nemo:free` | Mistral Nemo | Mistral | 12B |

### 5.3 `ask()` Function

```python
def ask(question: str, model: str) -> tuple[str, float, tuple[int, int], float]
```

**Returns:** `(answer, latency_seconds, (input_tokens, output_tokens), cost_usd)`

**Execution flow:**

```
ask(question, model)
  │
  ├── for attempt in 1..3:
  │     ├── record start = time.perf_counter()
  │     ├── client.chat.completions.create(model, messages, timeout=60)
  │     ├── latency = perf_counter() - start
  │     ├── extract answer, in_tok, out_tok from response
  │     ├── cost = (in_tok * in_price + out_tok * out_price) / 1_000_000
  │     └── return (answer, latency, (in_tok, out_tok), cost)
  │
  └── on exception:
        ├── "429" in error → sleep 32s, retry
        ├── other error   → sleep 3s, retry
        └── attempt 3 exhausted → return ("ERROR: ...", 0.0, (0,0), 0.0)
```

**Key design decisions:**
- `time.perf_counter()` used (not `time.time()`) for high-resolution latency that is not affected by system clock changes
- `response.usage` guarded with `if response.usage else 0` — some providers omit usage data
- Retry sleep of 32s on 429 matches the `retry_after_seconds` value returned by rate-limited providers
- The `if __name__ == "__main__"` guard allows `app.py` to import `ask()` without triggering CLI execution

### 5.4 `print_table()` Function

Renders a fixed-width columnar table to stdout. Long answers are word-wrapped across multiple rows. Unicode output requires `sys.stdout.reconfigure(encoding="utf-8")` on Windows.

---

## 6. Web UI Module — app.py

### 6.1 Responsibilities

- Defines `ALL_MODELS`, `MODEL_LABELS`, `MODEL_PROVIDER`, `MODEL_ICON` independently (not imported from main) to avoid Streamlit's module import cache bug causing stale model lists
- Imports only `ask` and `PRICES` from `main.py`
- Renders the full UI using `st.markdown()` with inline HTML/CSS

### 6.2 UI Layout

```
┌─────────────────────────────────────────────┐
│              HERO SECTION                   │
│   "One Prompt. Every Model."                │
│   Gradient title + animated badge           │
├─────────────────────────────────────────────┤
│              PROMPT CARD                    │
│   [ Textarea — user question         ]      │
│                                             │
│   ● Select Models                           │
│   [☑ Gemma 4 31B] [☑ GPT-OSS 20B] ...     │
│                                             │
│   [ ⚡ Compare Models ]                    │
├─────────────────────────────────────────────┤
│              RESULTS ROW                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Skeleton │ │ Skeleton │ │ Skeleton │   │  ← while loading
│  └──────────┘ └──────────┘ └──────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Result   │ │ Result   │ │ Result   │   │  ← after response
│  │ Latency  │ │ Latency  │ │ Latency  │   │
│  │ Tokens   │ │ Tokens   │ │ Tokens   │   │
│  │ Cost     │ │ Cost     │ │ Cost     │   │
│  │ Answer   │ │ Answer   │ │ Answer   │   │
│  └──────────┘ └──────────┘ └──────────┘   │
└─────────────────────────────────────────────┘
```

### 6.3 Skeleton Loader Pattern

Each column gets a `st.empty()` placeholder before any API call begins. The placeholder is filled with a shimmer skeleton card immediately. When a model's `ask()` call returns, its placeholder is replaced with the result card. This allows per-model progressive rendering — faster models appear before slower ones finish.

```python
slots = []
for col in cols:
    with col:
        ph = st.empty()
        ph.markdown(skeleton, unsafe_allow_html=True)
        slots.append(ph)

for i, model in enumerate(selected_models):
    answer, latency, ... = ask(question, model)
    slots[i].markdown(result_card, unsafe_allow_html=True)
```

### 6.4 Latency Color Coding

| Condition | Color | Meaning |
|---|---|---|
| `latency < 20s` | Green `#34d399` | Fast |
| `20s ≤ latency < 40s` | Amber `#fbbf24` | Moderate |
| `latency ≥ 40s` | Red `#f87171` | Slow |

### 6.5 Error Handling in UI

Each model call is wrapped in its own `try/except`. On failure, the skeleton is replaced with a red error card showing the exception message (truncated to 300 chars). Other models continue loading unaffected.

---

## 7. API Integration

### 7.1 OpenRouter

OpenRouter is an LLM routing hub that exposes a single OpenAI-compatible API endpoint. It routes requests to the appropriate model provider based on the model ID.

- **Base URL:** `https://openrouter.ai/api/v1`
- **Auth:** Bearer token via `OPENROUTER_API_KEY`
- **Client:** `openai.OpenAI` with custom `base_url`
- **Endpoint used:** `POST /chat/completions`

### 7.2 Authentication

```python
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
```

The API key is loaded exclusively from `.env` via `python-dotenv`. It never appears in source code and is excluded from version control via `.gitignore`.

### 7.3 Request Format

```python
client.chat.completions.create(
    model="google/gemma-4-31b-it:free",
    messages=[{"role": "user", "content": question}],
    timeout=60,
)
```

### 7.4 Response Fields Used

| Field | Usage |
|---|---|
| `response.choices[0].message.content` | Model's answer text |
| `response.usage.prompt_tokens` | Input token count |
| `response.usage.completion_tokens` | Output token count |

---

## 8. Error Handling Strategy

| Scenario | Behavior |
|---|---|
| HTTP 429 (rate limit) | Wait 32s, retry up to 3 times |
| Network error / timeout | Wait 3s, retry up to 3 times |
| 3 retries exhausted | Return `"ERROR: ..."` string, latency=0, cost=0 |
| Missing `response.usage` | Default token counts to 0 |
| Invalid/empty prompt (UI) | Show inline warning, halt execution with `st.stop()` |
| No models selected (UI) | Show inline warning, halt execution with `st.stop()` |

---

## 9. Security

| Concern | Mitigation |
|---|---|
| API key exposure | Loaded from `.env` only; `.gitignore` excludes `.env` |
| XSS in result cards | Answer text HTML-escaped before injection into card HTML |
| Dependency vulnerabilities | Minimal dependencies (`openai`, `python-dotenv`, `streamlit`) |

HTML escaping in `app.py`:
```python
safe = answer.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
```

---

## 10. Dependencies

| Package | Version | Purpose |
|---|---|---|
| `openai` | latest | OpenAI-compatible client for OpenRouter |
| `python-dotenv` | latest | Load `OPENROUTER_API_KEY` from `.env` |
| `streamlit` | latest | Web UI framework |

**Python requirement:** 3.9+  
**Platform:** Cross-platform (Windows, macOS, Linux); Windows requires `sys.stdout.reconfigure(encoding="utf-8")` for Unicode terminal output.

---

## 11. Known Limitations

| Limitation | Detail |
|---|---|
| Rate limits | Free-tier models are rate-limited by upstream providers (Venice, Google AI Studio). Persistent 429s indicate daily quota exhaustion. |
| Sequential model calls | Models are queried one after another, not in parallel. Total wait time = sum of all model latencies. |
| No streaming | Full response is awaited before rendering. Long responses feel slow. |
| Streamlit import cache | `ALL_MODELS` must be hardcoded in `app.py` — importing `MODELS` from `main.py` causes Streamlit to cache the old list after code changes. |
| Windows encoding | `sys.stdout.reconfigure(encoding="utf-8")` required or Unicode characters in model responses crash the CLI. |

---

## 12. Future Improvements

| Improvement | Description |
|---|---|
| Parallel model calls | Use `asyncio` or `concurrent.futures.ThreadPoolExecutor` to query all models simultaneously, reducing total wait time to `max(latencies)` instead of `sum(latencies)` |
| Streaming responses | Use the `stream=True` parameter to display tokens as they arrive |
| Prompt history | Store past comparisons in SQLite or a JSON file |
| Model discovery | Dynamically fetch available free models from `/api/v1/models` at startup |
| Export results | Add a "Download as CSV/PDF" button in the web UI |
| Paid model support | Update `PRICES` with real per-token costs and display accurate USD estimates |
