# LLM Arena — Multi-Model Comparison Tool

Compare answers, latency, and cost across multiple LLMs simultaneously — via a terminal CLI or a Streamlit web UI.

---

## Features

- **Side-by-side comparison** of 3 free LLMs in one run
- **Latency** measured per call (color-coded: green / amber / red)
- **Token usage** (input + output) read from the API response
- **Cost estimation** via a `PRICES` dict (USD per 1M tokens)
- **Retry logic** — auto-retries on 429 rate limits and network errors
- **60-second timeout** per model so a stalled call never blocks forever
- **Skeleton loaders** in the web UI while models respond
- **Error isolation** — one failing model shows an error card; the others continue

---

## Models (free tier via OpenRouter)

| Model | Label | Provider |
|---|---|---|
| `google/gemma-4-31b-it:free` | Gemma 4 31B | Google |
| `openai/gpt-oss-20b:free` | GPT-OSS 20B | OpenAI OSS |
| `openai/gpt-oss-120b:free` | GPT-OSS 120B | OpenAI OSS |

---

## Setup

**1. Clone and enter the project**
```bash
git clone <your-repo-url>
cd multimodel-app
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your OpenRouter API key**

Create a `.env` file in the `multimodel-app/` folder:
```
OPENROUTER_API_KEY=sk-or-v1-...
```
Get a free key at [openrouter.ai](https://openrouter.ai).

---

## Usage

### Terminal (CLI)
```bash
python main.py
```
Prints a columnar comparison table for all models.

### Web UI
```bash
python -m streamlit run app.py
```
Opens at [http://localhost:8501](http://localhost:8501).

Type a question, select models, click **Compare Models**.

---

## Project Structure

```
multimodel-app/
├── main.py          # Core logic: ask(), MODELS, PRICES, CLI runner
├── app.py           # Streamlit web UI
├── requirements.txt # Dependencies
├── .env             # API key (not committed)
└── spec.md          # Project specification
```

---

## Adding or swapping models

Edit `MODELS` and `PRICES` in `main.py` — `app.py` imports them automatically.

```python
MODELS = [
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-20b:free",
    "openai/gpt-oss-120b:free",
]

PRICES = {
    "google/gemma-4-31b-it:free": (0.0, 0.0),   # (input, output) per 1M tokens
    "openai/gpt-oss-20b:free":    (0.0, 0.0),
    "openai/gpt-oss-120b:free":   (0.0, 0.0),
}
```

For paid models, fill in the real prices from [openrouter.ai/models](https://openrouter.ai/models).

---

## Requirements

- Python 3.9+
- `openai` — OpenRouter uses the OpenAI-compatible API
- `python-dotenv` — loads the API key from `.env`
- `streamlit` — web UI
