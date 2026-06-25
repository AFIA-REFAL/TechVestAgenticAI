# Load OPENROUTER_API_KEY from .env into os.environ
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import time
from openai import OpenAI

# Fix Windows console encoding so Unicode characters print correctly
sys.stdout.reconfigure(encoding="utf-8")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODELS = [
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-20b:free",
    "openai/gpt-oss-120b:free",
    "mistralai/mistral-nemo:free",
]

# Input and output price in USD per 1 million tokens
PRICES = {
    "google/gemma-4-31b-it:free":                  (0.0, 0.0),
    "openai/gpt-oss-20b:free":                     (0.0, 0.0),
    "openai/gpt-oss-120b:free":                    (0.0, 0.0),
    "mistralai/mistral-nemo:free":                 (0.0, 0.0),
}

QUESTION = "What is the most important skill for a software engineer in 2025?"

REQUEST_TIMEOUT = 60  # seconds before a stalled model call is abandoned
PREVIEW_LEN = 120     # characters of answer shown in the summary table


def ask(question, model):
    # Retry up to 3 times; wait 32s on rate-limit (429), 3s on other errors
    for attempt in range(1, 4):
        try:
            start = time.perf_counter()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": question}],
                timeout=REQUEST_TIMEOUT,
            )
            latency = time.perf_counter() - start

            answer = response.choices[0].message.content
            in_tok = response.usage.prompt_tokens if response.usage else 0
            out_tok = response.usage.completion_tokens if response.usage else 0
            in_price, out_price = PRICES.get(model, (0.0, 0.0))
            cost = (in_tok * in_price + out_tok * out_price) / 1_000_000

            return answer, latency, (in_tok, out_tok), cost

        except Exception as e:
            err = str(e)
            if "429" in err and attempt < 3:
                print(f"  [{model}] Rate-limited, waiting 32s before retry {attempt+1}/3...")
                time.sleep(32)
            elif attempt < 3:
                print(f"  [{model}] Attempt {attempt} failed, retrying in 3s...")
                time.sleep(3)
            else:
                return f"ERROR: {e}", 0.0, (0, 0), 0.0


def print_table(results):
    col_model   = 38
    col_preview = 52
    col_latency =  9
    col_cost    = 12

    divider = (
        "+" + "-" * col_model +
        "+" + "-" * col_preview +
        "+" + "-" * col_latency +
        "+" + "-" * col_cost + "+"
    )
    header = (
        f"| {'Model':<{col_model-2}} "
        f"| {'Preview':<{col_preview-2}} "
        f"| {'Latency':>{col_latency-2}} "
        f"| {'Cost (USD)':>{col_cost-2}} |"
    )

    print(divider)
    print(header)
    print(divider)

    for model, answer, latency, cost in results:
        clean = answer.replace("#", "").replace("*", "").replace("\n", " ").strip()
        preview = clean[:PREVIEW_LEN - 3] + "..." if len(clean) > PREVIEW_LEN else clean

        words, lines, line = preview.split(), [], ""
        for word in words:
            if len(line) + len(word) + 1 <= col_preview - 2:
                line = (line + " " + word).strip()
            else:
                lines.append(line)
                line = word
        lines.append(line)

        lat_str  = f"{latency:.2f}s"
        cost_str = f"${cost:.6f}"

        print(f"| {model:<{col_model-2}} | {lines[0]:<{col_preview-2}} | {lat_str:>{col_latency-2}} | {cost_str:>{col_cost-2}} |")
        for extra in lines[1:]:
            print(f"| {'':<{col_model-2}} | {extra:<{col_preview-2}} | {' ':>{col_latency-2}} | {' ':>{col_cost-2}} |")

    print(divider)


if __name__ == "__main__":
    print(f"\nQuestion: {QUESTION}\n")
    print("Querying models...\n")

    results = []
    for model in MODELS:
        answer, latency, (in_tok, out_tok), cost = ask(QUESTION, model)
        results.append((model, answer, latency, cost))

    print_table(results)


