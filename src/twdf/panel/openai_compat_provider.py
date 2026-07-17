"""
OpenAI-compatible proxy provider with deterministic caching (Module B).

Implements the same ModelProvider protocol as GitHubModelsProvider and
AzureFoundryProvider for local OpenAI-compatible proxies such as ghc-api.

CRITICAL SECURITY: Never log, print, echo, or commit COPILOT_PROXY_KEY.
CRITICAL DETERMINISM: Use hashlib for cache keys, NOT builtin hash().
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

import requests


class ModelProvider(Protocol):
    """Model provider interface (INTERFACES.md §3)."""
    name: str

    def generate(self, prompt: str, *, seed: int, max_tokens: int,
                 temperature: float) -> str:
        """Generate text from prompt with specified parameters."""
        ...


@dataclass
class CacheEntry:
    """Cache entry for LLM response."""
    model: str
    messages: list[dict]
    temperature: float
    max_tokens: int
    seed: int
    response: str
    timestamp: str


class OpenAICompatibleProvider:
    """
    OpenAI-compatible chat/completions provider with retry logic and caching.

    Environment variables:
    - COPILOT_PROXY_ENDPOINT: Base URL (default: http://127.0.0.1:8787/v1)
    - COPILOT_PROXY_KEY: Optional bearer token. Omitted when absent.
    """

    def __init__(self,
                 *,
                 model_name: str,
                 base_url: Optional[str] = None,
                 cache_dir: Optional[Path] = None,
                 call_budget: int = 10000,
                 inter_call_sleep: float = 0.2,
                 max_retries: int = 5,
                 token_param: str = "max_tokens",
                 omit_temperature: bool = False,
                 min_completion_tokens: int = 0):
        """Initialize the OpenAI-compatible provider."""
        self.name = model_name
        self.base_url = (base_url or os.environ.get("COPILOT_PROXY_ENDPOINT") or "http://127.0.0.1:8787/v1").rstrip('/')
        self.key = os.environ.get("COPILOT_PROXY_KEY")

        if token_param not in {"max_tokens", "max_completion_tokens"}:
            raise ValueError("token_param must be 'max_tokens' or 'max_completion_tokens'")
        self.token_param = token_param
        self.omit_temperature = omit_temperature
        self.min_completion_tokens = int(min_completion_tokens)
        if self.min_completion_tokens < 0:
            raise ValueError("min_completion_tokens must be >= 0")

        if cache_dir is None:
            cache_dir = Path("data/cache/panel")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.call_budget = call_budget
        self.inter_call_sleep = inter_call_sleep
        self.max_retries = max_retries
        self.api_calls = 0
        self.cache_hits = 0

    def _compute_cache_key(self,
                          messages: list[dict],
                          temperature: float,
                          max_tokens: int,
                          seed: int) -> str:
        """Compute deterministic cache key using hashlib (NOT builtin hash())."""
        canonical_payload = {
            "provider": "openai_compat",
            "model": self.name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "seed": seed,
        }
        if self.token_param != "max_tokens":
            canonical_payload["token_param"] = self.token_param
        if self.omit_temperature:
            canonical_payload["omit_temperature"] = True
        canonical = json.dumps(canonical_payload, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _load_from_cache(self, cache_key: str) -> Optional[str]:
        """Load response from cache if available."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                entry = json.load(f)
            if not isinstance(entry, dict) or "response" not in entry:
                print(f"Warning: Invalid cache entry {cache_key}, ignoring")
                return None
            self.cache_hits += 1
            return entry["response"]
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load cache {cache_key}: {e}")
            return None

    def _save_to_cache(self,
                      cache_key: str,
                      messages: list[dict],
                      temperature: float,
                      max_tokens: int,
                      seed: int,
                      response: str):
        """Save response to cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        entry = {
            "model": self.name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "seed": seed,
            "response": response,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Failed to save cache {cache_key}: {e}")

    def _build_url(self) -> str:
        """Build chat/completions URL from the base URL."""
        return f"{self.base_url}/chat/completions"

    def _build_headers(self) -> dict:
        """Build request headers; auth is omitted unless COPILOT_PROXY_KEY is set."""
        headers = {"Content-Type": "application/json"}
        if self.key:
            headers["Authorization"] = f"Bearer {self.key}"
        return headers

    def _build_payload(self,
                      messages: list[dict],
                      temperature: float,
                      max_tokens: int,
                      seed: int) -> dict:
        """Build OpenAI-compatible request payload."""
        payload = {
            "model": self.name,
            "messages": messages,
            "seed": seed,
        }
        if not self.omit_temperature:
            payload["temperature"] = temperature
        effective_max_tokens = max_tokens
        if self.token_param == "max_completion_tokens":
            effective_max_tokens = max(max_tokens, self.min_completion_tokens)
        # Cache keys intentionally use the original max_tokens arg so matched
        # experiments remain comparable while reasoning models receive enough budget.
        payload[self.token_param] = effective_max_tokens
        return payload

    def _call_api(self,
                  messages: list[dict],
                  temperature: float,
                  max_tokens: int,
                  seed: int) -> str:
        """Call the proxy API with retry logic."""
        if self.api_calls >= self.call_budget:
            raise RuntimeError(
                f"API call budget exhausted ({self.call_budget} calls). "
                f"Increase call_budget if this is a legitimate large experiment."
            )

        url = self._build_url()
        headers = self._build_headers()
        payload = self._build_payload(messages, temperature, max_tokens, seed)
        last_error = None
        last_finish_reason = None

        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    self.api_calls += 1
                    data = response.json()
                    if "choices" not in data or len(data["choices"]) == 0:
                        raise RuntimeError(f"API response missing choices: {data}")
                    choice = data["choices"][0]
                    last_finish_reason = choice.get("finish_reason")
                    content = choice.get("message", {}).get("content")
                    if isinstance(content, list):
                        content = "".join(
                            part.get("text", "") if isinstance(part, dict) else str(part)
                            for part in content
                        )
                    if content is not None and str(content).strip():
                        if self.inter_call_sleep > 0:
                            time.sleep(self.inter_call_sleep)
                        return str(content)
                    last_error = (
                        f"Empty content from model {self.name} "
                        f"(finish_reason={last_finish_reason})"
                    )
                    if attempt >= self.max_retries - 1:
                        raise RuntimeError(
                            f"Empty content from model {self.name} after {self.max_retries} "
                            f"attempts (finish_reason={last_finish_reason})"
                        )
                    wait_time = (2 ** attempt) + (attempt * 0.5)
                    print(f"{last_error}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait_time = max(float(retry_after), 2.0)
                    else:
                        wait_time = (2 ** attempt) + (attempt * 0.5)
                    if attempt >= self.max_retries - 1:
                        raise RuntimeError(f"Rate limit (429) exceeded after {self.max_retries} retries")
                    print(f"Rate limit (429), cooling down {wait_time:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    last_error = f"HTTP 429: {response.text}"
                    continue

                if response.status_code in [500, 502, 503, 504]:
                    wait_time = (2 ** attempt) + (attempt * 0.5)
                    print(f"Server error {response.status_code}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    continue

                raise RuntimeError(f"API error {response.status_code}: {response.text}")

            except requests.RequestException as e:
                last_error = str(e)
                wait_time = (2 ** attempt) + (attempt * 0.5)
                print(f"Request exception: {e}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(wait_time)

        raise RuntimeError(
            f"API call failed after {self.max_retries} retries for model {self.name}. "
            f"Last error: {last_error}"
        )

    def generate(self, prompt: str, *, seed: int, max_tokens: int,
                 temperature: float) -> str:
        """Generate text from a single user prompt."""
        messages = [{"role": "user", "content": prompt}]
        return self.generate_messages(
            messages=messages,
            seed=seed,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def generate_messages(self,
                         messages: list[dict],
                         *,
                         seed: int,
                         max_tokens: int,
                         temperature: float) -> str:
        """Generate from messages with deterministic caching."""
        cache_key = self._compute_cache_key(messages, temperature, max_tokens, seed)
        cached = self._load_from_cache(cache_key)
        if cached is not None:
            return cached
        response = self._call_api(messages, temperature, max_tokens, seed)
        self._save_to_cache(cache_key, messages, temperature, max_tokens, seed, response)
        return response

    def get_stats(self) -> dict:
        """Get provider statistics (for run_manifest)."""
        return {
            "api_calls": self.api_calls,
            "cache_hits": self.cache_hits,
            "total_requests": self.api_calls + self.cache_hits,
        }
