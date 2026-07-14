# Two-Ways-A-Design-Fail: vslice-v0

Thin vertical slice (v0) implementation for the two-axis AI interaction triage system.

## What this is

A proof-of-concept implementation that runs the full analysis chain end-to-end:
- Real human reliance data (Bansal et al. CHI'21)
- Canonical per-trial schema
- Rigorous beta-binomial over-dispersion metric (axis 1)
- Synthetic panel stub (placeholder for real LLM panel)
- Correlation between panel disagreement and human over-dispersion
- Mean-predictor baseline comparison

**Status:** Draft PR #1 (feature/vslice-v0 branch). NOT production-ready.

## Installation

```bash
pip install -e .
pip install -e ".[dev]"  # for tests
```

## Running the experiment

```bash
python -m twdf.experiments.e1_vslice --config configs/vslice_v0.yaml
```

Results saved to `results/e1_vslice_v0.json`.

## Running tests

```bash
pytest tests/
```

Critical tests:
- `test_pure_binomial_returns_near_zero_rho`: Verifies over-dispersion metric doesn't confuse sampling noise with heterogeneity
- `test_high_low_split_returns_positive_rho`: Verifies metric detects true between-user variance
- `test_overdispersed_beats_mean_predictor`: Verifies genuine over-dispersion beats baseline

## Architecture

```
src/twdf/
  data/
    bansal.py          # Bansal CHI'21 loader + canonical schema mapping
  metrics/
    overdispersion.py  # Beta-binomial over-dispersion (axis 1 core)
  panel/
    stub.py            # Synthetic panel stub (NOT real LLM)
  experiments/
    e1_vslice.py       # E1 v0 runner
```

## Key limitations (v0 scope)

1. **Synthetic panel stub**: Not real LLM responses, just a deterministic generator. Real panel (Module B) is separate work.
2. **No threshold freezing**: τ_disp/τ_level thresholds are NOT set in v0. PI freezes these later.
3. **Minimal data**: Only ~10 tasks, 2 UI conditions for speed.
4. **No LOIO/prospective**: E3/E6 experiments are future work.

## Methodology audit points

The implementation enforces these methodological guardrails (SPEC §8):
- ✅ Over-dispersion separated from binomial noise (beta-binomial model, not raw variance)
- ✅ Mean-predictor baseline genuine (rho=0 by construction)
- ✅ Difficulty controlled via within-task diff (not pooled correlation)
- ✅ Deterministic under fixed seed
- ✅ No hallucinated numbers (results from actual re-run)

## References

- Bansal et al. (2021). "Does the Whole Exceed its Parts? The Effect of AI Explanations on Complementary Team Performance." CHI'21.
- SPEC.md: Full scientific protocol
- INTERFACES.md: Data schema and function contracts
