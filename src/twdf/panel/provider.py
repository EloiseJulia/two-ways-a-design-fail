"""
GitHub Models LLM provider with deterministic caching (Module B).

CRITICAL SECURITY: Never log, print, echo, or commit GH_MODELS_TOKEN.
CRITICAL DETERMINISM: Use hashlib for cache keys, NOT builtin hash().

Caching makes reruns free + byte-identical for determinism tests.
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Protocol, Optional
from dataclasses import dataclass

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


class GitHubModelsProvider:
    """
    GitHub Models provider with retry logic and deterministic caching.
    
    API: https://models.github.ai/inference/chat/completions
    Auth: Bearer token from GH_MODELS_TOKEN environment variable
    
    Caching: Deterministic hashlib-based cache in data/cache/panel/
    Makes reruns free and ensures cross-process determinism.
    """
    
    name = "openai/gpt-4o-mini"
    
    def __init__(self, 
                 *,
                 cache_dir: Optional[Path] = None,
                 call_budget: int = 1000,
                 inter_call_sleep: float = 0.5,
                 max_retries: int = 5):
        """
        Initialize GitHub Models provider.
        
        Args:
            cache_dir: Directory for response cache (default: data/cache/panel/)
            call_budget: Maximum number of API calls allowed (hard cap)
            inter_call_sleep: Sleep seconds between API calls (rate limit courtesy)
            max_retries: Maximum retry attempts on 429/5xx errors
        """
        # Get token from environment (NEVER log/print it!)
        self.token = os.environ.get("GH_MODELS_TOKEN")
        if not self.token:
            raise RuntimeError(
                "GH_MODELS_TOKEN environment variable is not set. "
                "This token is required for GitHub Models API access. "
                "Set it before running the experiment."
            )
        
        # Cache directory
        if cache_dir is None:
            cache_dir = Path("data/cache/panel")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting + budget
        self.call_budget = call_budget
        self.inter_call_sleep = inter_call_sleep
        self.max_retries = max_retries
        
        # Call counters
        self.api_calls = 0
        self.cache_hits = 0
        
    def _compute_cache_key(self, 
                          messages: list[dict],
                          temperature: float,
                          max_tokens: int,
                          seed: int) -> str:
        """
        Compute deterministic cache key using hashlib (NOT builtin hash()).
        
        CRITICAL: builtin hash() is non-deterministic across processes and is BANNED.
        This function uses hashlib.sha256 for cross-process determinism.
        """
        # Normalize messages to canonical JSON (sorted keys for determinism)
        canonical = json.dumps({
            "model": self.name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "seed": seed,
        }, sort_keys=True)
        
        # Hash with hashlib (deterministic)
        hash_obj = hashlib.sha256(canonical.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[str]:
        """Load response from cache if available."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                entry = json.load(f)
            
            # Verify cache entry structure
            if not isinstance(entry, dict) or 'response' not in entry:
                print(f"Warning: Invalid cache entry {cache_key}, ignoring")
                return None
            
            self.cache_hits += 1
            return entry['response']
            
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
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Failed to save cache {cache_key}: {e}")
    
    def _call_api(self, 
                  messages: list[dict],
                  temperature: float,
                  max_tokens: int,
                  seed: int) -> str:
        """
        Call GitHub Models API with retry logic.
        
        Returns:
            Response text from the model
        
        Raises:
            RuntimeError: If API call fails after all retries or budget exceeded
        """
        # Check call budget
        if self.api_calls >= self.call_budget:
            raise RuntimeError(
                f"API call budget exhausted ({self.call_budget} calls). "
                f"Increase call_budget if this is a legitimate large experiment."
            )
        
        url = "https://models.github.ai/inference/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "seed": seed,
        }
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                
                # Success
                if response.status_code == 200:
                    self.api_calls += 1
                    data = response.json()
                    
                    if 'choices' not in data or len(data['choices']) == 0:
                        raise RuntimeError(f"API response missing choices: {data}")
                    
                    content = data['choices'][0]['message']['content']
                    
                    # Rate limit courtesy sleep
                    if self.inter_call_sleep > 0:
                        time.sleep(self.inter_call_sleep)
                    
                    return content
                
                # Rate limit or server error - retry with backoff
                if response.status_code in [429, 500, 502, 503, 504]:
                    wait_time = (2 ** attempt) + (attempt * 0.5)  # Exponential backoff
                    print(f"API error {response.status_code}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    continue
                
                # Other error - fail immediately
                raise RuntimeError(f"API error {response.status_code}: {response.text}")
                
            except requests.RequestException as e:
                last_error = str(e)
                wait_time = (2 ** attempt) + (attempt * 0.5)
                print(f"Request exception: {e}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(wait_time)
        
        # All retries exhausted
        raise RuntimeError(
            f"API call failed after {self.max_retries} retries. Last error: {last_error}"
        )
    
    def generate(self, prompt: str, *, seed: int, max_tokens: int,
                 temperature: float) -> str:
        """
        Generate text from prompt (INTERFACES.md §3 signature).
        
        Internally converts prompt to messages format (system + user).
        Uses deterministic caching for reproducibility.
        
        Args:
            prompt: User prompt text
            seed: Random seed for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Returns:
            Generated text response
        """
        # Convert prompt to messages (simple user message)
        messages = [{"role": "user", "content": prompt}]
        
        return self.generate_messages(
            messages=messages,
            seed=seed,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def generate_messages(self, 
                         messages: list[dict],
                         *,
                         seed: int,
                         max_tokens: int,
                         temperature: float) -> str:
        """
        Generate from messages (system + user).
        
        Helper that allows more control than the simple generate() signature.
        Uses deterministic hashlib-based caching.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            seed: Random seed for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Returns:
            Generated text response
        """
        # Compute cache key (deterministic with hashlib)
        cache_key = self._compute_cache_key(messages, temperature, max_tokens, seed)
        
        # Try cache first
        cached = self._load_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Cache miss - call API
        response = self._call_api(messages, temperature, max_tokens, seed)
        
        # Save to cache
        self._save_to_cache(cache_key, messages, temperature, max_tokens, seed, response)
        
        return response
    
    def get_stats(self) -> dict:
        """Get provider statistics (for run_manifest)."""
        return {
            "api_calls": self.api_calls,
            "cache_hits": self.cache_hits,
            "total_requests": self.api_calls + self.cache_hits,
        }
