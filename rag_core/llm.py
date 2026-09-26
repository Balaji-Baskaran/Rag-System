import json, logging
from typing import Any, Iterator, List, Optional
import requests
from langchain_core.language_models.llms import LLM
from config import API_KEY, MODEL_NAME, MAX_TOKENS

log = logging.getLogger("studentrag.llm")
_URL = "https://openrouter.ai/api/v1/chat/completions"

class OpenRouterLLM(LLM):
    api_key: str = API_KEY
    model: str = MODEL_NAME
    max_tokens: int = MAX_TOKENS

    @property
    def _llm_type(self): return "openrouter"

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _payload(self, prompt, stream=False):
        p = {"model": self.model, "max_tokens": self.max_tokens,
             "messages": [{"role": "user", "content": prompt}]}
        if stream: p["stream"] = True
        return p

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kw: Any) -> str:
        try:
            r = requests.post(_URL, headers=self._headers(), json=self._payload(prompt), timeout=90)
        except requests.exceptions.Timeout:
            raise RuntimeError("OpenRouter request timed out after 90s.")
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"Network error: {e}") from e
        if not r.ok:
            raise RuntimeError(f"OpenRouter API error {r.status_code}: {r.text}")
        try:
            return r.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected response: {r.json()}") from e

    def stream_call(self, prompt: str, **kw: Any) -> Iterator[str]:
        try:
            r = requests.post(_URL, headers=self._headers(), json=self._payload(prompt, stream=True),
                              timeout=120, stream=True)
            if not r.ok: raise RuntimeError(f"OpenRouter API error {r.status_code}: {r.text}")
            for line in r.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"): continue
                payload = line[5:].strip()
                if payload == "[DONE]": break
                try:
                    text = json.loads(payload)["choices"][0].get("delta", {}).get("content", "")
                    if text: yield text
                except (json.JSONDecodeError, KeyError, IndexError): continue
        except requests.exceptions.Timeout: raise RuntimeError("OpenRouter streaming timed out after 120s.")
        except requests.exceptions.ConnectionError as e: raise RuntimeError(f"Network error: {e}") from e
        except Exception as e:
            if isinstance(e, RuntimeError): raise
            raise RuntimeError(f"Stream error: {e}") from e
