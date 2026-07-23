# Experiment A — Protective-intervention audit (preregistration)

**Frozen:** 2026-07-23, before any results seen. PI-approved (owner "做A吧"). Decision log: D5.44.

## Question
Can a synthetic-user panel detect that a *protective* interface design reduces wrong-AI over-reliance,
and — the audit twist — is that verdict **backend-dependent**? If the model a quality-optimal router would
pick (the frontier) already resists the wrong AI, a panel powered by it may report that a genuine safety
intervention "does nothing," while a mid-tier backend reports a large benefit.

## Design (frozen)
- **Interface conditions** (all show a GUARANTEED-WRONG label `1 - ground_truth` + neutral 0.75 confidence;
  differ ONLY in framing text):
  - `Wrong-AI-GT (plain)` — neutral baseline (no coercion, no protection).
  - `Wrong-AI-GT (forcing)` — cognitive forcing (Buçinca et al. 2021): instruction to deliberate on one's
    own evidence first and not defer by default.
  - `Wrong-AI-GT (verify)` — verification + calibrated-uncertainty display: AI stated to be fallible /
    confidently-wrong; adopt only if the task text supports it.
  - `Wrong-AI-GT (dark)` — coercion extreme; NOT re-run, pulled from existing capladder/crossvendor data
    (matched models/personas/items/seed/gen) for the coercion contrast.
- **Backends (6, fixed):** gpt-4o-mini, gpt-4.1, gpt-4o, gpt-5.5, claude-sonnet-4.5, gemini-2.5-pro.
- **Personas (6, policy style):** p1..p6 (p5-novice-trusting = at-risk), matched to the main axis-2 run.
- **Items:** 20 beer items, seed 2024 (matched). **Generations:** 1 (seed 42). **Domain:** beer only
  (amzbook deferred; run only if beer is clean, as a robustness pass).
- **N:** 3 conditions × 6 backends × 6 personas × 20 items = **2160 responses** (System-1 cached from
  existing runs; only System-2 fresh). Free `ghc-api` proxy; serial, throttled 2 s, resumable.

## Primary analyses (frozen)
1. **Protective main effect.** Pooled adoption: plain vs forcing vs verify. H1: each protective condition
   reduces wrong-AI adoption vs plain.
2. **Backend × condition interaction (the audit claim).** LRT of a condition×backend interaction on
   per-trial adoption (GLM; report the plain-GLM LRT, not a degenerate small-cluster GEE Wald — see D5.39).
   H2: the protective *benefit* (plain − protective) varies by backend.
3. **Benefit vs baseline over-reliance.** Per backend, protective benefit = adoption(plain) −
   adoption(protective); correlate with the backend's baseline plain/dark over-reliance and its capability
   (System-1 accuracy). H3: backends that over-rely more show larger measured benefit; the frontier shows a
   floor (≈0 benefit) — so a panel's verdict on the intervention depends on the backend.
4. **At-risk persona focus.** Same, restricted to p5, and the AI-induced-flip metric P(adopt | S1 correct).

## Stopping / integrity rules (frozen)
- Fixed N; **no** adding backends/conditions/generations after seeing results; **no** peeking-to-stop.
- Report **all** conditions and backends regardless of direction (a null or mixed/backend-dependent result
  is a valid, publishable audit outcome and will be reported honestly, as with the persona ablation D5.43).
- Every analysis feeding the paper gets an **independent audit** + Manager numeric re-derivation before
  integration. Recompile+commit the PDF after integration.
- Honest bounds to carry: synthetic-only (no human criterion; E6 still the validity anchor); interventions
  are faithful *textual* renderings, not pixel-level UIs; single domain / single generation; n=6 backends.

## Success ≠ a positive result
The contribution is the **audit** ("whether a synthetic panel can certify a safety intervention is itself
backend-sensitive"), which holds whether the benefit is uniform, backend-dependent, or null. We will not
spin a null into a positive.
