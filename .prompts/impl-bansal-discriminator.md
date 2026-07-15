# impl-bansal-discriminator — C0 mechanism test (zero API)

You are an implementation subagent in worktree `.worktrees/bansal-discriminator`
(branch `feature/bansal-discriminator`, draft PR #6). Pure real-data analysis — NO
API. You do NOT audit/merge your own work. This is the DECISIVE test of the paper's
co-anchor C0 — methodology rigor is paramount and the audit will be hostile. Report
FACTS; do NOT claim "done/all green"; do NOT tune to force any outcome.

## 0. FIRST: read the source of truth
Read: `SPEC.md` (§2 C0 — currently **HELD** pending THIS test), `PROGRESS.md` (PR#2
Bansal decomposition + PR#5 Lu&Yin boundary result + Known pitfalls + Preregistration),
`docs/research/2026-07-14-overdispersion-decomposition.md` (Bansal method),
`docs/research/2026-07-15-luyin-decomposition-replication.md` (Lu&Yin result + confounds).
Reuse EXISTING code: `src/twdf/metrics/variance_decomposition.py`
(`split_half_reliability` — the SAME primary method, seed=43, n_splits=100, min_tasks=8),
`src/twdf/data/bansal.py` (loader; `task_difficulty` = domain: 1=beer, 2=amzbook, 3=lsat;
domain is BETWEEN-SUBJECTS so each user's tasks are already within ONE domain),
`src/twdf/experiments/e1_decomposition.py` (the Bansal decomposition to extend),
`results/e1_decomposition.json` (the 0.32–0.41 AI-assisted numbers you are dissecting).

## 1. THE QUESTION (PI-directed decision rule — implement faithfully)
Bansal AI-assisted reliance is user×task (stable_user_share ≈ 0.32–0.41). Lu&Yin
AI-assisted is trait-stable (≈ 0.80). The between-dataset comparison is CONFOUNDED. This
slice ISOLATES whether Bansal's low share is driven by CONTROLLABLE regime confounds
(task/difficulty homogeneity, AI-accuracy regime, tasks/user) by re-decomposing Bansal on
subsets MATCHED to Lu&Yin's regime, then applies:
- **If Bansal's user×task PERSISTS under matched homogeneity (share stays low ≈0.3–0.5)**
  → the controllable regime is NOT the driver → the residual gap is likely the
  UNCONTROLLABLE sequential-feedback difference (Bansal is static) → **recommend DEMOTE C0**
  to a single-dataset finding; lean on C1 (panel).
- **If it COLLAPSES to trait-stable (share rises toward ≈0.7–0.8)** → task/difficulty/
  accuracy homogeneity DOES drive the share → **recommend reframe C0 as design-dependent**
  on identified ground.
Report the numbers and the recommendation; the PI/Manager makes the final call.

## 2. Manager-measured Bansal structure (use to design matching; verify yourself)
Per AI condition (task_selection='all'): users ~195–292, tasks/user median ~50 (lsat ~20),
reliance 0.80–0.83, AI-acc 0.80–0.84 — EXCEPT the lsat domain (difficulty=3): AI-acc ≈0.65,
reliance ≈0.71, tasks/user ≈20. **Lu&Yin's regime (AI-acc ≈0.70, reliance ≈0.67) most
closely matches Bansal's LSAT domain.** So lsat is the primary matched subset.

## 3. Matched-subset decompositions (compute `split_half_reliability` on each; same params)
For the AI-assisted conditions (Conf., Conf.+Single, Conf.+Double, Conf.+Adaptive,
Conf.+Adaptive (Expert)) — you may pool the AI conditions and/or report per-condition:
1. **By domain (difficulty homogeneity):** stable_user_share computed WITHIN each single
   domain separately — beer (diff=1), amzbook (diff=2), **lsat (diff=3, the Lu&Yin-matched
   regime)**. Does any single homogeneous domain raise the share toward Lu&Yin's 0.80, or
   does it stay low (~0.35)? lsat is the headline (matched AI-accuracy/reliance).
2. **By AI-accuracy band:** restrict to items whose per-item AI accuracy ≈ Lu&Yin's (~0.70,
   e.g. a band around 0.6–0.75), recompute share. Report the band + n.
3. **Tasks/user match:** to rule out an estimation-length artifact, also compute share
   sub-sampling each user's tasks to ~30 (Lu&Yin's count, min_tasks=8) and confirm Spearman-
   Brown gives a comparable value (SB is length-corrected, so this should be a robustness
   check, not a big mover — report it).
4. **Internal heterogeneity gradient (clean internal test):** compute stable_user_share at
   decreasing task-set heterogeneity (full AI set → single domain → narrow difficulty/
   accuracy band) and report whether share RISES as heterogeneity falls. This is the most
   direct within-Bansal evidence on whether homogeneity drives the share.
Always report per subset: n_users, tasks/user, reliance rate, AI accuracy, stable_user_share
+ 95% CI, alongside Lu&Yin's 0.80 and Bansal-full's 0.32–0.41 for comparison.

## 4. HONESTY + guardrails (§4.5 — this is C0; auditor is hostile)
- Use `split_half_reliability` ONLY (no ANOVA-on-cells). Same seed=43/n_splits=100/min_tasks.
- Do NOT tune subsets to hit a target share; PRE-SPECIFY the subsets (domain, accuracy band)
  in the config and report ALL of them, including inconvenient ones.
- Be explicit that sequential-feedback is an UNCONTROLLABLE confound here (Bansal is static),
  so a persisting low share does NOT prove "regime doesn't matter" in general — it only
  rules out the controllable confounds; state this limitation plainly.
- Determinism (fixed seeds; cross-process subprocess test). `hashlib` only. Honest CIs.
- Do NOT edit SPEC's C0 wording to a causal claim — only report the result + recommendation;
  the PI decides C0's final status.

## 5. Deliverables
- `configs/bansal_discriminator.yaml` (pre-specified subsets), `src/twdf/experiments/
  bansal_discriminator.py` (CLI → `results/bansal_discriminator.json` with full run_manifest
  + every subset's share/CI/structure). Reuse the loader + split_half_reliability.
- `tests/test_bansal_discriminator.py`: subset-selection correctness + determinism
  (cross-process). Do NOT weaken tests. `pytest -q` green.
- `docs/research/2026-07-15-bansal-discriminator.md`: the matched-subset table (share per
  subset vs Lu&Yin 0.80 vs Bansal-full 0.35), the heterogeneity gradient, and a clear
  PERSISTS-vs-COLLAPSES verdict + the resulting C0 recommendation (demote vs design-dependent),
  with the sequential-feedback caveat.
- Update `PROGRESS.md` (Done entry with the real numbers + verdict + recommendation) and
  `INTERFACES.md` §8 AS-BUILT. Commit (trailer `Co-authored-by: Copilot
  <copilot@github.com>`) + push. Do NOT commit scratch.

## 6. Report (FACTS)
The matched-subset stable_user_share table (esp. **lsat** and the accuracy-band subset), the
heterogeneity gradient, whether Bansal's user×task PERSISTS or COLLAPSES under Lu&Yin-matched
homogeneity, and your C0 recommendation (demote vs design-dependent) with honest caveats.
Independent audit + Manager verification follow.
