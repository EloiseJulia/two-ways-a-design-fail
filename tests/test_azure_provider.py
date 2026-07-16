"""
Tests for Azure AI Foundry / Azure OpenAI provider (Module B).

CRITICAL: ALL tests are OFFLINE with mocked HTTP - NO real network calls.
Tests marked @pytest.mark.live are skipped by default.

Test coverage:
1. Environment variable validation (missing vars raise clear errors)
2. azure_openai style: URL format, headers, body structure, response parsing
3. foundry style: URL format, headers, body with model field, response parsing
4. Cache determinism: hashlib-based cache reuse + cross-process determinism
5. Security: key never appears in logs/repr/cache files
6. Protocol compliance: drop-in replacement for GitHubModelsProvider
7. Retry logic: 429/5xx handling with backoff
"""

import os
import json
import pytest
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

from twdf.panel.azure_provider import AzureFoundryProvider, ModelProvider
from twdf.panel.stub import Persona, AgentResponse
from twdf.data.bansal_tasks import TaskStimulus


# ===== FIXTURE: Mock environment =====

@pytest.fixture
def mock_azure_env(monkeypatch):
    """Set up mock Azure environment variables."""
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_KEY", "test-key-12345")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "")  # Empty = use constructor arg


@pytest.fixture
def clear_azure_env(monkeypatch):
    """Clear Azure environment variables."""
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)


# ===== TEST 1: Environment variable validation =====

def test_missing_endpoint_raises_clear_error(clear_azure_env, monkeypatch):
    """Test that missing AZURE_OPENAI_ENDPOINT raises a clear error."""
    monkeypatch.setenv("AZURE_OPENAI_KEY", "test-key")
    
    with pytest.raises(RuntimeError, match="AZURE_OPENAI_ENDPOINT.*not set"):
        AzureFoundryProvider(deployment="test-deployment")


def test_missing_key_raises_clear_error(clear_azure_env, monkeypatch):
    """Test that missing AZURE_OPENAI_KEY raises a clear error."""
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
    
    with pytest.raises(RuntimeError, match="AZURE_OPENAI_KEY.*not set"):
        AzureFoundryProvider(deployment="test-deployment")


def test_api_version_defaults_to_stable(mock_azure_env, monkeypatch):
    """Test that AZURE_OPENAI_API_VERSION defaults to a stable value."""
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="test-deployment",
            cache_dir=Path(tmpdir)
        )
        assert provider.api_version == "2024-10-21"


# ===== TEST 2: azure_openai style =====

def test_azure_openai_style_url_format(mock_azure_env):
    """Test that azure_openai style builds correct URL with deployment in path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="gpt-4o-mini",
            api_style="azure_openai",
            cache_dir=Path(tmpdir)
        )
        
        url = provider._build_url()
        assert url == "https://test.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-10-21"


def test_azure_openai_style_headers(mock_azure_env):
    """Test that azure_openai style uses api-key header (not Bearer)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="test-deployment",
            api_style="azure_openai",
            cache_dir=Path(tmpdir)
        )
        
        headers = provider._build_headers()
        assert "api-key" in headers
        assert headers["api-key"] == "test-key-12345"
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"


def test_azure_openai_style_body_no_model_field(mock_azure_env):
    """Test that azure_openai style does NOT include model in body."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="test-deployment",
            api_style="azure_openai",
            cache_dir=Path(tmpdir)
        )
        
        messages = [{"role": "user", "content": "test"}]
        payload = provider._build_payload(messages, 0.5, 100, 42)
        
        # CRITICAL: azure_openai does NOT include model in body (deployment is in URL)
        assert "model" not in payload
        assert payload["messages"] == messages
        assert payload["temperature"] == 0.5
        assert payload["max_tokens"] == 100
        assert payload["seed"] == 42


@patch('requests.post')
def test_azure_openai_style_api_call(mock_post, mock_azure_env):
    """Test that azure_openai style makes correct API call and parses response."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "Test response from Azure OpenAI"}}
        ]
    }
    mock_post.return_value = mock_response
    
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="gpt-4o",
            api_style="azure_openai",
            cache_dir=Path(tmpdir),
            inter_call_sleep=0  # Disable sleep for tests
        )
        
        messages = [{"role": "user", "content": "Hello"}]
        response = provider.generate_messages(
            messages=messages,
            seed=42,
            max_tokens=100,
            temperature=0.7
        )
        
        # Verify response
        assert response == "Test response from Azure OpenAI"
        
        # Verify call was made with correct parameters
        assert mock_post.call_count == 1
        call_args = mock_post.call_args
        
        # Check URL (positional arg or keyword arg)
        url = call_args[0][0] if call_args[0] else call_args.kwargs['url']
        assert "openai/deployments/gpt-4o/chat/completions" in url
        
        # Check headers (api-key)
        headers = call_args.kwargs['headers']
        assert "api-key" in headers
        
        # Check body (NO model field)
        payload = call_args.kwargs['json']
        assert "model" not in payload
        assert payload["messages"] == messages


# ===== TEST 3: foundry style =====

def test_foundry_style_url_format(mock_azure_env):
    """Test that foundry style builds correct URL with configurable path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="gpt-4o",
            api_style="foundry",
            cache_dir=Path(tmpdir)
        )
        
        url = provider._build_url()
        assert url == "https://test.openai.azure.com/chat/completions"


def test_foundry_style_custom_path(mock_azure_env):
    """Test that foundry style supports custom path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="test-deployment",
            api_style="foundry",
            foundry_path="/openai/v1/chat/completions",
            cache_dir=Path(tmpdir)
        )
        
        url = provider._build_url()
        assert url == "https://test.openai.azure.com/openai/v1/chat/completions"


def test_foundry_style_headers(mock_azure_env):
    """Test that foundry style uses Bearer token header (not api-key)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="test-deployment",
            api_style="foundry",
            cache_dir=Path(tmpdir)
        )
        
        headers = provider._build_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-key-12345"
        assert "api-key" not in headers
        assert headers["Content-Type"] == "application/json"


def test_foundry_style_body_includes_model_field(mock_azure_env):
    """Test that foundry style includes model in body."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="gpt-4o-mini",
            api_style="foundry",
            cache_dir=Path(tmpdir)
        )
        
        messages = [{"role": "user", "content": "test"}]
        payload = provider._build_payload(messages, 0.5, 100, 42)
        
        # CRITICAL: foundry DOES include model in body
        assert payload["model"] == "gpt-4o-mini"
        assert payload["messages"] == messages
        assert payload["temperature"] == 0.5
        assert payload["max_tokens"] == 100
        assert payload["seed"] == 42


@patch('requests.post')
def test_foundry_style_api_call(mock_post, mock_azure_env):
    """Test that foundry style makes correct API call and parses response."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "Test response from Foundry"}}
        ]
    }
    mock_post.return_value = mock_response
    
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="gpt-4o",
            api_style="foundry",
            cache_dir=Path(tmpdir),
            inter_call_sleep=0
        )
        
        messages = [{"role": "user", "content": "Hello"}]
        response = provider.generate_messages(
            messages=messages,
            seed=42,
            max_tokens=100,
            temperature=0.7
        )
        
        # Verify response
        assert response == "Test response from Foundry"
        
        # Verify call was made with correct parameters
        assert mock_post.call_count == 1
        call_args = mock_post.call_args
        
        # Check URL (positional arg or keyword arg)
        url = call_args[0][0] if call_args[0] else call_args.kwargs['url']
        assert url == "https://test.openai.azure.com/chat/completions"
        
        # Check headers (Bearer)
        headers = call_args.kwargs['headers']
        assert headers["Authorization"] == "Bearer test-key-12345"
        
        # Check body (model field present)
        payload = call_args.kwargs['json']
        assert payload["model"] == "gpt-4o"
        assert payload["messages"] == messages


# ===== TEST 4: Cache determinism =====

@patch('requests.post')
def test_cache_hit_skips_api_call(mock_post, mock_azure_env):
    """Test that second identical call uses cache and does NOT call API."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Cached response"}}]
    }
    mock_post.return_value = mock_response
    
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="test-model",
            cache_dir=Path(tmpdir),
            inter_call_sleep=0
        )
        
        messages = [{"role": "user", "content": "Test prompt"}]
        
        # First call - should hit API
        response1 = provider.generate_messages(
            messages=messages,
            seed=42,
            max_tokens=100,
            temperature=0.5
        )
        
        assert mock_post.call_count == 1
        assert provider.api_calls == 1
        assert provider.cache_hits == 0
        
        # Second call - should use cache
        response2 = provider.generate_messages(
            messages=messages,
            seed=42,
            max_tokens=100,
            temperature=0.5
        )
        
        # CRITICAL: API not called again
        assert mock_post.call_count == 1
        assert provider.api_calls == 1
        assert provider.cache_hits == 1
        
        # Responses are identical
        assert response1 == response2 == "Cached response"


@patch('requests.post')
def test_cache_key_includes_deployment(mock_post, mock_azure_env):
    """Test that cache keys include deployment name to prevent collisions."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Response"}}]
    }
    mock_post.return_value = mock_response
    
    with tempfile.TemporaryDirectory() as tmpdir:
        provider1 = AzureFoundryProvider(
            deployment="model-a",
            cache_dir=Path(tmpdir),
            inter_call_sleep=0
        )
        
        provider2 = AzureFoundryProvider(
            deployment="model-b",
            cache_dir=Path(tmpdir),
            inter_call_sleep=0
        )
        
        messages = [{"role": "user", "content": "Same prompt"}]
        
        # Both providers call with same prompt/seed
        provider1.generate_messages(messages=messages, seed=42, max_tokens=100, temperature=0.5)
        provider2.generate_messages(messages=messages, seed=42, max_tokens=100, temperature=0.5)
        
        # CRITICAL: Different deployments = different cache keys = 2 API calls
        assert mock_post.call_count == 2
        assert provider1.api_calls == 1
        assert provider2.api_calls == 1


def test_cross_process_cache_determinism_subprocess(mock_azure_env, tmp_path):
    """
    Test that cached responses are byte-identical across SEPARATE PROCESSES.
    
    CRITICAL: Single-process tests don't catch hash-seed nondeterminism.
    This test spawns subprocesses to verify true determinism.
    """
    # Create test script that will run in subprocess
    test_script = tmp_path / "test_azure_cache.py"
    cache_dir = tmp_path / "cache"
    output_file = tmp_path / "output.json"
    
    script_content = f'''
import sys
sys.path.insert(0, r"{Path(__file__).parent.parent.parent}")

import os
from pathlib import Path
from unittest.mock import Mock, patch
from twdf.panel.azure_provider import AzureFoundryProvider

# Set mock environment
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com"
os.environ["AZURE_OPENAI_KEY"] = "test-key-12345"
os.environ["AZURE_OPENAI_API_VERSION"] = "2024-10-21"

# Mock requests.post to avoid real network calls
with patch('requests.post') as mock_post:
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {{
        "choices": [{{"message": {{"content": "Subprocess response"}}}}]
    }}
    mock_post.return_value = mock_response
    
    provider = AzureFoundryProvider(
        deployment="test-model",
        cache_dir=Path(r"{cache_dir}"),
        inter_call_sleep=0
    )
    
    messages = [{{"role": "user", "content": "Determinism test"}}]
    response = provider.generate_messages(
        messages=messages,
        seed=42,
        max_tokens=100,
        temperature=0.5
    )
    
    import json
    with open(r"{output_file}", 'w') as f:
        json.dump({{"response": response, "stats": provider.get_stats()}}, f)
'''
    
    test_script.write_text(script_content)
    
    # Run first process
    result1 = subprocess.run(
        [sys.executable, str(test_script)],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    
    if result1.returncode != 0:
        pytest.fail(f"First subprocess failed:\nstdout: {result1.stdout}\nstderr: {result1.stderr}")
    
    with open(output_file, 'r') as f:
        output1 = json.load(f)
    
    # Run second process (should hit cache)
    result2 = subprocess.run(
        [sys.executable, str(test_script)],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    
    if result2.returncode != 0:
        pytest.fail(f"Second subprocess failed:\nstdout: {result2.stdout}\nstderr: {result2.stderr}")
    
    with open(output_file, 'r') as f:
        output2 = json.load(f)
    
    # Verify second run used cache
    assert output2['stats']['cache_hits'] > 0, "Second run should have hit cache!"
    
    # Verify byte-identical responses
    assert output1['response'] == output2['response'], "Cache responses differ across processes!"


# ===== TEST 5: Security - key never appears in logs/repr/cache =====

@patch('requests.post')
def test_key_not_in_cache_files(mock_post, mock_azure_env):
    """Test that API key never appears in cache files."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Response"}}]
    }
    mock_post.return_value = mock_response
    
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="test-model",
            cache_dir=Path(tmpdir),
            inter_call_sleep=0
        )
        
        messages = [{"role": "user", "content": "Test"}]
        provider.generate_messages(messages=messages, seed=42, max_tokens=100, temperature=0.5)
        
        # Read all cache files
        cache_dir = Path(tmpdir)
        for cache_file in cache_dir.glob("*.json"):
            with open(cache_file, 'r') as f:
                content = f.read()
            
            # CRITICAL: Key must NOT appear in cache
            assert "test-key-12345" not in content, f"API key found in cache file: {cache_file}"


def test_key_not_in_repr(mock_azure_env):
    """Test that API key does not appear in repr/str."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="test-model",
            cache_dir=Path(tmpdir)
        )
        
        repr_str = repr(provider)
        str_str = str(provider)
        
        # Key should not appear in string representations
        # (Note: Python doesn't auto-generate __repr__ that includes all attributes,
        # so this is a sanity check - main security is never logging the key)
        assert "test-key-12345" not in repr_str
        assert "test-key-12345" not in str_str


# ===== TEST 6: Protocol compliance / interchangeability =====

def test_implements_model_provider_protocol(mock_azure_env):
    """Test that AzureFoundryProvider implements ModelProvider protocol."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="test-model",
            cache_dir=Path(tmpdir)
        )
        
        # Has required attributes
        assert hasattr(provider, 'name')
        assert hasattr(provider, 'generate')
        assert hasattr(provider, 'generate_messages')
        assert hasattr(provider, 'get_stats')
        
        # Name is set correctly
        assert provider.name == "test-model"


@patch('requests.post')
def test_interchangeable_with_github_provider_in_run_panel(mock_post, mock_azure_env):
    """
    Test that AzureFoundryProvider can be used as drop-in replacement in run_panel.
    
    This is a smoke test - full run_panel integration is tested elsewhere.
    """
    from twdf.panel.real_panel import run_panel
    
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"decision": 1, "confidence": 0.8, "reasoning": "test"}'}}]
    }
    mock_post.return_value = mock_response
    
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="gpt-4o",
            cache_dir=Path(tmpdir),
            inter_call_sleep=0
        )
        
        personas = [
            Persona(
                persona_id="p1",
                domain_skill=0.5,
                ai_literacy=0.5,
                risk_sensitivity=0.5,
                caution=0.5,
                temperature=0.5,
                prior_mix=0.5
            )
        ]
        
        tasks = [
            TaskStimulus(
                task_id="t1",
                domain="beer",
                text="Test task",
                ground_truth=1,
                ai_pred=1,
                ai_conf=0.9,
                expert_explanation="Test explanation",
                system="test",
                testid="t1"
            )
        ]
        
        ui_pair = ("Conf.", "Conf.+Adaptive (Expert)")
        
        # Run panel with Azure provider
        responses = run_panel(
            personas=personas,
            tasks=tasks,
            ui_pair=ui_pair,
            providers=[provider],
            seeds=[42],
            mode="static"
        )
        
        # Verify responses are well-formed
        assert len(responses) == 2  # 1 persona × 1 task × 2 conditions
        for resp in responses:
            assert isinstance(resp, AgentResponse)
            assert resp.model == "gpt-4o"
            assert resp.system1_decision in ['0', '1']
            assert resp.final_decision in ['0', '1']


# ===== TEST 7: Retry logic =====

@patch('requests.post')
def test_retry_on_429(mock_post, mock_azure_env):
    """Test that provider retries on 429 rate limit."""
    # First call fails with 429, second succeeds
    mock_fail = Mock()
    mock_fail.status_code = 429
    mock_fail.text = "Rate limited"
    mock_fail.headers = {"Retry-After": "2"}
    
    mock_success = Mock()
    mock_success.status_code = 200
    mock_success.json.return_value = {
        "choices": [{"message": {"content": "Success after retry"}}]
    }
    
    mock_post.side_effect = [mock_fail, mock_success]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="test-model",
            cache_dir=Path(tmpdir),
            inter_call_sleep=0
        )
        
        messages = [{"role": "user", "content": "Test"}]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            response = provider.generate_messages(
                messages=messages,
                seed=42,
                max_tokens=100,
                temperature=0.5
            )
        
        # Verify retry happened
        assert mock_post.call_count == 2
        assert response == "Success after retry"


@patch('requests.post')
def test_retry_on_5xx(mock_post, mock_azure_env):
    """Test that provider retries on 5xx server errors."""
    # First call fails with 503, second succeeds
    mock_fail = Mock()
    mock_fail.status_code = 503
    mock_fail.text = "Service unavailable"
    
    mock_success = Mock()
    mock_success.status_code = 200
    mock_success.json.return_value = {
        "choices": [{"message": {"content": "Success after retry"}}]
    }
    
    mock_post.side_effect = [mock_fail, mock_success]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment="test-model",
            cache_dir=Path(tmpdir),
            inter_call_sleep=0
        )
        
        messages = [{"role": "user", "content": "Test"}]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            response = provider.generate_messages(
                messages=messages,
                seed=42,
                max_tokens=100,
                temperature=0.5
            )
        
        # Verify retry happened
        assert mock_post.call_count == 2
        assert response == "Success after retry"


# ===== TEST 8: grep for banned builtin hash() =====

def test_no_builtin_hash_in_provider():
    """
    Test that builtin hash() is NOT used in azure_provider.py.
    
    CRITICAL: builtin hash() is non-deterministic across processes and is BANNED.
    Only hashlib.sha256 is allowed.
    
    This test looks for actual code patterns like:
    - variable = hash(...)
    - return hash(...)
    - hash(...) as a standalone expression
    
    NOT patterns like "hash_obj" or "hashlib.hash" or mentions in comments/docstrings.
    """
    provider_file = Path(__file__).parent.parent / "src" / "twdf" / "panel" / "azure_provider.py"
    
    with open(provider_file, 'r') as f:
        lines = f.readlines()
    
    import re
    
    violations = []
    
    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
        
        # Skip comment lines
        if stripped.startswith('#'):
            continue
        
        # Skip docstring content (anything inside """ or ''')
        # Simple heuristic: if line contains quotes but no code-like patterns, skip
        if ('"""' in stripped or "'''" in stripped) and not any(p in stripped for p in ['=', 'return', '(', ')']):
            continue
        
        # Skip lines that are clearly docstring content (start with text, no code patterns)
        if re.match(r'^[A-Z].*[.:]$', stripped) and '=' not in stripped and 'def ' not in stripped:
            continue
        
        # NOW check for banned hash( in actual code
        # Look for patterns like: = hash(, return hash(, func(hash(
        # But NOT: hash_obj, hashlib, .hash(, or hash() in text context
        if re.search(r'(?<![._\w])hash\s*\([^"]', line):  # Not followed by quote (docstring context)
            # Additional check: line should have code-like structure
            if any(p in line for p in ['=', 'return', 'def ', 'if ', 'for ', 'while ']):
                violations.append((line_no, line.strip()))
    
    assert len(violations) == 0, \
        f"Found banned builtin hash() calls in azure_provider.py:\n" + \
        "\n".join(f"  Line {ln}: {code}" for ln, code in violations)


# ===== LIVE TESTS (skipped by default) =====

@pytest.mark.live
def test_real_azure_openai_api():
    """
    Real Azure OpenAI API test (marked 'live', skipped by default).
    
    Run with: pytest -m live tests/test_azure_provider.py
    
    Requires:
    - AZURE_OPENAI_ENDPOINT
    - AZURE_OPENAI_KEY
    - AZURE_OPENAI_API_VERSION
    """
    if "AZURE_OPENAI_ENDPOINT" not in os.environ or "AZURE_OPENAI_KEY" not in os.environ:
        pytest.skip("Azure environment variables not set - skipping live API test")
    
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment=deployment,
            api_style="azure_openai",
            cache_dir=Path(tmpdir),
            call_budget=5
        )
        
        response = provider.generate(
            prompt="Say 'Hello from Azure OpenAI'",
            seed=42,
            max_tokens=50,
            temperature=0.0
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        print(f"\nLive Azure OpenAI response: {response}")


@pytest.mark.live
def test_real_foundry_api():
    """
    Real Azure AI Foundry API test (marked 'live', skipped by default).
    
    Run with: pytest -m live tests/test_azure_provider.py
    
    Requires:
    - AZURE_OPENAI_ENDPOINT (Foundry endpoint)
    - AZURE_OPENAI_KEY
    """
    if "AZURE_OPENAI_ENDPOINT" not in os.environ or "AZURE_OPENAI_KEY" not in os.environ:
        pytest.skip("Azure environment variables not set - skipping live API test")
    
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = AzureFoundryProvider(
            deployment=deployment,
            api_style="foundry",
            cache_dir=Path(tmpdir),
            call_budget=5
        )
        
        response = provider.generate(
            prompt="Say 'Hello from Foundry'",
            seed=42,
            max_tokens=50,
            temperature=0.0
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        print(f"\nLive Foundry response: {response}")
