
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()


def call_llm(model: str, prompt: str) -> str:

    api_key = os.getenv("UNBOUND_API_KEY")
    api_url = os.getenv("UNBOUND_API_URL")

    if not api_key:
        raise ValueError("UNBOUND_API_KEY environment variable is not set")
    if not api_url:
        raise ValueError("UNBOUND_API_URL environment variable is not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Connection": "close"  # Prevents stale connection reuse
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }

    MAX_RETRIES = 3

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=60
            )

            response.raise_for_status()

            data = response.json()

            return data["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            print(f"LLM call failed (attempt {attempt + 1}): {e}")
            time.sleep(2)

    raise RuntimeError("LLM call failed after retries")
