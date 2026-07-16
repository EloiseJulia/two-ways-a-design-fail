# Azure AI Foundry / Azure OpenAI Setup Guide — PI Provisioning Steps

> **Purpose:** Enable powered single-session axis-1 runs without GitHub Models' per-model daily cap.
> This guide details the exact steps the PI must take to provision Azure credentials for the
> confirmatory axis-1 multi-condition panel run.

## 0. Why Azure (Lever C — quota-strategy.md)

- GitHub Models enforces a **per-user, per-model DAILY cap ~500 requests** (429, `x-ratelimit-type: UserByModelByDay`, `Retry-After` ≈ 18–19 h).
- A powered axis-1 run needs **~1,920 calls/model** (8 personas × 40 items × 5 conditions + shared System-1).
- **Azure AI Foundry / Azure OpenAI have NO per-model daily cap** (pay-per-token, high throughput).
- **Cost estimate:** ~1,920 calls × ~700 tok input + ~400 tok output per call = ~1.3 M in + 0.4 M out per model.
  - gpt-4o-class ≈ **$5–15/model**; mini tier ≈ **$1–3/model**.
  - A full 3-model cross-family run ≈ **$15–45 total** (one-time cost for confirmatory run).

## 1. Choose deployment style

The `AzureFoundryProvider` supports two API styles:

### Option A: Azure OpenAI Service (recommended if you have an existing Azure subscription)
- Create an Azure OpenAI Service resource in the Azure portal.
- Deploy one or more models (e.g., `gpt-4o`, `gpt-4o-mini`, `gpt-4.1-mini`).
- **URL pattern:** `https://<resource>.openai.azure.com`
- **Auth:** `api-key` header
- **Body:** NO `model` field (deployment name is in URL)

### Option B: Azure AI Foundry models-as-a-service
- Use Azure AI Foundry's OpenAI-compatible endpoint.
- **URL pattern:** `https://<foundry-endpoint>/chat/completions` (or custom path)
- **Auth:** `Authorization: Bearer <token>`
- **Body:** includes `model` field

Both options work identically from the code's perspective. Choose based on your existing Azure setup.

## 2. Provisioning steps (Azure OpenAI Service)

### 2.1 Create Azure OpenAI resource
1. Log in to the Azure Portal: https://portal.azure.com
2. Create resource → **Azure OpenAI**
3. Select subscription, resource group, region (e.g., `East US`)
4. Choose pricing tier (Standard S0 is typical)
5. **Note the endpoint URL** (format: `https://<resource-name>.openai.azure.com`)

### 2.2 Deploy models
1. In the Azure OpenAI resource, go to **Model deployments** (or **Azure OpenAI Studio**)
2. Deploy the models you need for the confirmatory run. Recommended frozen model set (preregister BEFORE seeing results):
   - **gpt-4o** (or gpt-4o-mini) — OpenAI family
   - **Llama-3.3-70B-Instruct** (if available) OR **Phi-4** — alternative family for cross-family triangulation
   - (Add more families for robustness; record the EXACT frozen list in PROGRESS §Preregistration)
3. **Note the deployment names** (these become the `deployment` parameter in `AzureFoundryProvider`)

### 2.3 Get API key
1. In the Azure OpenAI resource, go to **Keys and Endpoint**
2. Copy **Key 1** (or Key 2)
3. **NEVER commit this key to git or log it.** Store it securely.

### 2.4 Note API version
- As of this guide (2026-07-16), the stable API version is `2024-10-21`.
- Check Azure docs for the latest stable version if this is outdated: https://learn.microsoft.com/en-us/azure/ai-services/openai/api-version-deprecation

## 3. Set environment variables (REQUIRED)

On the machine where you run the experiment, set these environment variables:

```bash
# Linux / macOS / Git Bash
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"
export AZURE_OPENAI_KEY="<your-api-key>"
export AZURE_OPENAI_API_VERSION="2024-10-21"  # or latest stable
export AZURE_OPENAI_DEPLOYMENT="<deployment-name>"  # optional; can pass to constructor

# Windows PowerShell
$env:AZURE_OPENAI_ENDPOINT = "https://<your-resource>.openai.azure.com"
$env:AZURE_OPENAI_KEY = "<your-api-key>"
$env:AZURE_OPENAI_API_VERSION = "2024-10-21"
$env:AZURE_OPENAI_DEPLOYMENT = "<deployment-name>"  # optional
```

**CRITICAL SECURITY:**
- The `AZURE_OPENAI_KEY` is sensitive. NEVER commit it to git, print it, echo it, or log it.
- Do NOT add these to `.env` files that get committed.
- Use a secrets manager or session-only env vars.

## 4. Update experiment config to use Azure provider

Example: modify `configs/e1_powered_axis1.yaml` (or create a new config for the confirmatory run):

```yaml
# Multi-condition axis-1 powered run (confirmatory)
experiment_name: "e1_axis1_confirmatory_azure"
dataset: "bansal"
task_selection: "all"  # Maximum data for powered run
conditions:
  - "Human"
  - "Conf."
  - "Conf.+Adaptive (Expert)"
  - "Conf.+Adaptive"
  - "Conf.+Double"
  - "Conf.+Single"

personas:
  - persona_id: "p1_novice_skeptic"
    domain_skill: 0.2
    ai_literacy: 0.2
    risk_sensitivity: 0.2
    caution: 0.8
    temperature: 0.5
    prior_mix: 0.5
  # ... 7 more personas for diversity (8 total)

# Azure provider config (replaces GitHub Models)
providers:
  - type: "azure"  # NEW: use AzureFoundryProvider
    deployment: "gpt-4o"  # Or read from AZURE_OPENAI_DEPLOYMENT env
    api_style: "azure_openai"  # Or "foundry"
    call_budget: 5000  # Generous for powered run
    inter_call_sleep: 0.2  # Courtesy pacing (Azure has no daily cap, but be polite)

seeds:
  - 42  # Frozen seed for confirmatory run

mode: "static"  # Counterfactual pairing
```

In the experiment code, instantiate the provider:

```python
from twdf.panel.azure_provider import AzureFoundryProvider

provider = AzureFoundryProvider(
    deployment=config['providers'][0]['deployment'],
    api_style=config['providers'][0]['api_style'],
    call_budget=config['providers'][0]['call_budget'],
    inter_call_sleep=config['providers'][0]['inter_call_sleep']
)

# Then pass to run_panel as usual (drop-in replacement)
responses = run_panel(
    personas=personas,
    tasks=tasks,
    ui_pair=conditions,
    providers=[provider],
    seeds=seeds,
    mode="static"
)
```

## 5. Verify setup (offline test)

Before running the powered confirmatory experiment, verify the credentials work:

1. Ensure environment variables are set (step 3)
2. Run the **offline tests** to confirm code structure:
   ```bash
   pytest -m "not live" tests/test_azure_provider.py
   ```
   Expected: **22/22 PASSED** (offline, mocked HTTP)

3. Run ONE **live test** to confirm Azure credentials work (optional, skipped by default):
   ```bash
   pytest -m live tests/test_azure_provider.py::test_real_azure_openai_api
   ```
   Expected: connects to Azure, returns a short response, no errors.
   This makes **ONE real API call** (minimal cost, ~$0.001).

4. Once verified, proceed with the confirmatory run.

## 6. Run the confirmatory axis-1 experiment

```bash
python -m twdf.experiments.e1_axis1_confirmatory --config configs/e1_axis1_confirmatory_azure.yaml
```

- Expected calls: ~1,920/model (8 personas × 40 items × 5 conditions + shared System-1).
- Wall-clock time: ~1–2 hours (depends on Azure throughput + pacing).
- Cost: ~$5–15/model (estimated; track actual usage in Azure portal).
- Results: `results/e1_axis1_confirmatory_azure.json` with run_manifest.

**Cache makes reruns free:** The hashlib-based cache persists across runs. If the run is interrupted,
rerun the same command; cached calls cost $0, only new calls are billed.

## 7. Preregistration reminder (CRITICAL)

**FREEZE the model set + axis-1 design BEFORE seeing results** (PROGRESS §Preregistration):
- Exact models / families (e.g., gpt-4o, Llama-3.3-70B, Phi-4)
- Personas (8 frozen configurations)
- Items (40 hard/ambiguous, selected per `item_selector.py` criteria)
- Conditions (5 Bansal UI arms)
- Seed (e.g., 42)
- Pooling rule (per-model + cross-family agreement)
- Timestamp this freeze in PROGRESS.md BEFORE running the experiment.

Post-hoc model selection = researcher degrees of freedom = fatal to preregistration.

## 8. Monitoring + cost control

- **Azure portal:** Monitor usage / costs in real-time under Cost Management.
- **Provider stats:** `provider.get_stats()` returns `{api_calls, cache_hits, total_requests}`.
  Log this in the run_manifest for transparency.
- **Budget cap:** Set `call_budget` in the provider constructor to a safe upper bound (e.g., 5000).
  The provider will raise an error if exceeded (avoids runaway costs).

## 9. Security checklist

- [ ] `AZURE_OPENAI_KEY` is set as an environment variable (not committed to git)
- [ ] `.gitignore` covers `data/cache/` and `data/raw/` (already present)
- [ ] No key appears in any log file, cache file, or console output
- [ ] Offline tests pass (22/22) before provisioning real credentials
- [ ] (Optional) Live test passes with real credentials
- [ ] Run_manifest includes `api_calls` / `cache_hits` for transparency
- [ ] Preregistration frozen (model set + design) BEFORE seeing results

## 10. Troubleshooting

### Error: "AZURE_OPENAI_ENDPOINT environment variable is not set"
- Solution: Set the env var (step 3). Verify with `echo $AZURE_OPENAI_ENDPOINT` (Linux/Mac) or `$env:AZURE_OPENAI_ENDPOINT` (PowerShell).

### Error: "AZURE_OPENAI_KEY environment variable is not set"
- Solution: Set the env var (step 3). NEVER log or print the key.

### Error: 401 Unauthorized
- Solution: Check that the API key is correct (step 2.3). Regenerate if needed.

### Error: 404 Not Found
- Solution: Check that the endpoint URL is correct (step 2.1) and the deployment name matches (step 2.2).

### Error: 429 Too Many Requests
- Azure should NOT have a per-model daily cap (unlike GitHub Models). If you see 429, check:
  - Burst rate limits (Azure has per-minute limits; the provider retries with backoff).
  - Quota allocation in the Azure portal (Standard S0 tier has generous limits).

### Cache not working / determinism issues
- Verify `data/cache/panel/` directory exists and is writable.
- Check that the cache key includes the deployment name (prevents collisions).
- Run the cross-process determinism test: `pytest tests/test_azure_provider.py::test_cross_process_cache_determinism_subprocess`

---

**Summary for PI:**
1. Provision Azure OpenAI resource + deploy models (step 2)
2. Set 4 env vars: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_API_VERSION`, optionally `AZURE_OPENAI_DEPLOYMENT` (step 3)
3. Verify offline tests pass (step 5)
4. Preregister frozen model set + design (step 7)
5. Run confirmatory experiment (step 6)
6. Cost: ~$15–45 for 3-model powered axis-1 run (one-time)
