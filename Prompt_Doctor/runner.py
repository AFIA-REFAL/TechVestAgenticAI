"""
prompt_doctor/runner.py

Executes the student's candidate system prompt against the sample task
data, using the same LLM backend (OpenRouter) as the examiner, and
returns the raw text output (or an "[ERROR] ..." string on failure,
which app.py checks for via llm_out.startswith("[ERROR]")).
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"


def run(student_prompt: str, task_data: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return "[ERROR] Missing API key. Set OPENROUTER_API_KEY in your .env file."

    if not student_prompt or not student_prompt.strip():
        return "[ERROR] Student prompt is empty."

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": student_prompt},
            {"role": "user", "content": task_data},
        ],
        "temperature": 0.3,
        "max_tokens": 800,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://localhost:3000"),
        "X-Title": "Prompt Doctor Runner",
    }

    try:
        res = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=30)

        if res.status_code != 200:
            return f"[ERROR] API Error (Status {res.status_code}): {res.text}"

        data = res.json()

        if isinstance(data, dict) and "error" in data:
            err = data["error"]
            if isinstance(err, dict):
                msg = err.get("message", "Unknown error")
            else:
                msg = str(err)
            return f"[ERROR] {msg}"

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return "[ERROR] Unexpected API response shape (no message content found)."

        if not isinstance(content, str):
            content = str(content)

        return content.strip()

    except requests.exceptions.Timeout:
        return "[ERROR] Request to the LLM provider timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"[ERROR] Network error: {str(e)}"
    except Exception as e:
        return f"[ERROR] {str(e)}"