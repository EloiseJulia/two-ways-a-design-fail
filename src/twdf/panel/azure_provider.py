"""
Azure AI Foundry / Azure OpenAI provider with deterministic caching (Module B).

Implements the SAME ModelProvider protocol as GitHubModelsProvider, making it
a DROP-IN replacement for run_panel. Reuses the same hashlib-based response
cache so runs are deterministic + resumable.

LEVER C (quota-strategy.md): Azure has NO per-model daily cap, enabling
powered single-session axis-1 runs without multi-day batching.

CRITICAL SECURITY: Never log, print, echo, or commit AZURE_OPENAI_KEY.
CRITICAL DETERMINISM: Use hashlib for cache keys, NOT builtin hash().

Supported API styles:
1. "azure_openai": Azure OpenAI Service
   - URL: {endpoint}/openai/deployments/{deployment}/chat/completions?api-version={version}
   - Auth: api-key header
   - Body: NO model field (deployment is in URL)

2. "foundry": Azure AI Foundry models-as-a-service (OpenAI-compatible)
   - URL: {endpoint}/chat/completions (or configurable path)
   - Auth: Bearer token
   - Body: includes model field
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


class AzureFoundryProvider:
    """
    Azure AI Foundry / Azure OpenAI provider with retry logic and deterministic caching.
    
    DROP-IN replacement for GitHubModelsProvider. Shares the SAME hashlib-based
    cache mechanism for cross-provider determinism.
    
    Environment variables (REQUIRED):
    - AZURE_OPENAI_ENDPOINT: Azure endpoint URL (e.g., https://<resource>.openai.azure.com)
    - AZURE_OPENAI_KEY: API key or token (NEVER logged/printed/committed)
    - AZURE_OPENAI_API_VERSION: API version (default: "2024-10-21")
    - AZURE_OPENAI_DEPLOYMENT: (Optional) Deployment name override
    
    API styles:
    1. "azure_openai" (default): Azure OpenAI Service
       POST {endpoint}/openai/deployments/{deployment}/chat/completions?api-version={version}
       Header: api-key
       Body: NO model field
    
    2. "foundry": Azure AI Foundry models-as-a-service
       POST {endpoint}/chat/completions (or custom path via foundry_path)
       Header: Authorization Bearer
       Body: includes model field
    
    Caching: Deterministic hashlib-based cache in data/cache/panel/
    Makes reruns free and ensures cross-process determinism.
    """
    
    def __init__(self, 
                 *,
                 deployment: str,
                 api_style: str = "azure_openai",
                 cache_dir: Optional[Path] = None,
                 call_budget: int = 10000,
                 inter_call_sleep: float = 0.2,
                 max_retries: int = 5,
                 foundry_path: str = "/chat/completions",
                 token_param: str = "max_tokens",
                 omit_temperature: bool = False):
        """
        Initialize Azure provider.
        
        Args:
            deployment: Azure deployment/model name (included in cache key).
            api_style: "azure_openai" or "foundry"
            cache_dir: Directory for response cache (default: data/cache/panel/)
            call_budget: Maximum number of API calls allowed (hard cap)
            inter_call_sleep: Sleep seconds between API calls (rate limit courtesy)
            max_retries: Maximum retry attempts on 429/5xx errors
            foundry_path: Path for foundry style (default: "/chat/completions")
            token_param: Token-limit request field. Default preserves existing
                Azure OpenAI behavior; gpt-5.x configs may set "max_completion_tokens".
            omit_temperature: If true, omit temperature from request payload.
        
        Raises:
            RuntimeError: If required environment variables are missing
        """
        # Deployment/model name (instance-level, overrides class default in cache key)
        self.name = deployment
        
        # Validate api_style
        if api_style not in ["azure_openai", "foundry"]:
            raise ValueError(f"api_style must be 'azure_openai' or 'foundry', got: {api_style}")
        self.api_style = api_style
        
        # Get required environment variables (NEVER log/print them!)
        self.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.key = os.environ.get("AZURE_OPENAI_KEY")
        self.api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")
        
        # Clear error messages for missing env vars
        if not self.endpoint:
            raise RuntimeError(
                "AZURE_OPENAI_ENDPOINT environment variable is not set. "
                "Set it to your Azure endpoint URL (e.g., https://<resource>.openai.azure.com) "
                "before running the experiment."
            )
        if not self.key:
            raise RuntimeError(
                "AZURE_OPENAI_KEY environment variable is not set. "
                "This key/token is required for Azure API access. "
                "Set it before running the experiment. NEVER commit or log this key."
            )
        
        # Optional deployment override from env
        deployment_env = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        if deployment_env:
            self.name = deployment_env
        
        self.foundry_path = foundry_path
        if token_param not in {"max_tokens", "max_completion_tokens"}:
            raise ValueError("token_param must be 'max_tokens' or 'max_completion_tokens'")
        # gpt-5.x Azure deployments may require these non-default knobs; the
        # Manager will confirm/adjust the exact contract during live cred-check.
        self.token_param = token_param
        self.omit_temperature = omit_temperature
        
        # Cache directory (SHARED with GitHubModelsProvider)
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
        
        Cache key includes deployment/model name to prevent cross-provider collisions.
        """
        # Normalize messages to canonical JSON (sorted keys for determinism)
        canonical_payload = {
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
    
    def _build_url(self) -> str:
        """Build API URL based on api_style."""
        # Remove trailing slash from endpoint for consistency
        base = self.endpoint.rstrip('/')
        
        if self.api_style == "azure_openai":
            # Azure OpenAI Service: deployment in URL
            return f"{base}/openai/deployments/{self.name}/chat/completions?api-version={self.api_version}"
        else:  # foundry
            # Azure AI Foundry: configurable path
            return f"{base}{self.foundry_path}"
    
    def _build_headers(self) -> dict:
        """Build request headers based on api_style."""
        headers = {"Content-Type": "application/json"}
        
        if self.api_style == "azure_openai":
            # Azure OpenAI Service: api-key header (NEVER log this!)
            headers["api-key"] = self.key
        else:  # foundry
            # Azure AI Foundry: Bearer token
            headers["Authorization"] = f"Bearer {self.key}"
        
        return headers
    
    def _build_payload(self, 
                      messages: list[dict],
                      temperature: float,
                      max_tokens: int,
                      seed: int) -> dict:
        """Build request payload based on api_style."""
        payload = {
            "messages": messages,
            "seed": seed,
        }
        if not self.omit_temperature:
            payload["temperature"] = temperature
        payload[self.token_param] = max_tokens
        
        # Foundry style includes model in body; azure_openai does NOT
        if self.api_style == "foundry":
            payload["model"] = self.name
        
        return payload
    
    def _call_api(self, 
                  messages: list[dict],
                  temperature: float,
                  max_tokens: int,
                  seed: int) -> str:
        """
        Call Azure API with retry logic.
        
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
        
        url = self._build_url()
        headers = self._build_headers()
        payload = self._build_payload(messages, temperature, max_tokens, seed)
        
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
                
                # Rate limit (429) - retry with backoff
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
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
                
                # Server errors (5xx) - exponential backoff
                if response.status_code in [500, 502, 503, 504]:
                    wait_time = (2 ** attempt) + (attempt * 0.5)
                    print(f"Server error {response.status_code}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{self.max_retries})")
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
        Uses deterministic hashlib-based caching (SHARED with GitHubModelsProvider).
        
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
