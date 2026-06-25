# Spec — Multi-Model Comparison Tool

## Goal
Ask one question to multiple LLMs via OpenRouter and display each answer
with its latency, token usage, and cost — both in the terminal and in a
Streamlit web UI — so models can be compared side by side.

## Input
- A single question (string).
- CLI (`main.py`): hardcoded `QUESTION` constant.
- Web UI (`app.py`): free-text prompt entered by the user.

## Models (active — OpenRouter free tier)
| Model ID | Label | Provider |
|---|---|---|
| google/gemma-4-31b-it:free | Gemma 4 31B | Google |
| openai/gpt-oss-20b:free | GPT-OSS 20B | OpenAI OSS |
| openai/gpt-oss-120b:free | GPT-OSS 120B | OpenAI OSS |

> **Note:** Original spec models (deepseek/deepseek-r1:free, qwen/qwen3-32b:free,
> google/gemma-3-27b-it:free) were removed from OpenRouter's free tier and replaced
> with the above equivalents.

## Architecture
```
.env                  ← OPENROUTER_API_KEY (never committed)
main.py               ← core logic: ask(), MODELS, PRICES
app.py                ← Streamlit web UI (imports from main.py)
requirements.txt      ← openai, python-dotenv, streamlit
```

## Core function
```python
def ask(question, model) -> (answer, latency, (in_tok, out_tok), cost)
```
- Times the API call with `time.perf_counter()`
- Reads token usage from `response.usage`
- Computes `cost = (in_tok * in_price + out_tok * out_price) / 1_000_000`
- Retries up to 3 times: 32s wait on 429, 3s on other errors
- 60-second request timeout per call

## PRICES dict
Maps each model ID to `(input_price, output_price)` in USD per 1M tokens.
All current models are on the free tier → `(0.0, 0.0)`.
Update values here when switching to paid models.

## CLI output (`main.py`)
Columnar table printed to terminal:
```
+--------------------------------------+...+----------+--------------+
| Model                                |...| Latency  |  Cost (USD)  |
+--------------------------------------+...+----------+--------------+
| google/gemma-4-31b-it:free           |...| 24.98s   |  $0.000000   |
```

## Web UI (`app.py`)
- Hero section with gradient title
- Prompt textarea inside a styled card
- Model checkboxes (all pre-selected) below the textarea
- "Compare Models" button
- Skeleton loader per column while models are queried
- Result cards with: model name, provider, latency tile, token tile, cost tile, answer text
- Latency color-coded: green < 20s · amber < 40s · red ≥ 40s
- Error state per card — one failure does not stop the others

## Error handling
- Each model call wrapped in try/except in both CLI and UI
- On failure: CLI logs the error and continues; UI shows a red error card
- No API key ever appears in code

## Done when
- Running `python main.py` prints results for all active models
- Running `python -m streamlit run app.py` opens the web UI
- One failing model does not stop the others
- All API keys loaded from `.env` only
