# Writing-Lead Handoff — 2026-07-29 (session retiring)

Role: **WRITING LEAD / 语言与叙事负责人** (HCI/AI, target CHI). Owner **@EloiseJulia**, Chinese chat,
English paper. Final say on framing/claim-strength/structure is the owner's; language-level smoothing can
proceed but must be diffable. Rebuild + commit `main.pdf` after every `main.tex` edit; log non-trivial
decisions in `docs/DECISIONS.md`; `$env:GH_TOKEN=$null` before any `gh`.

## Paper state (as of this handoff)
- **Title (owner-approved):** *Don't Crash-Test with Your Safest Driver* / subtitle *A Backend-Sensitivity
  Audit of Synthetic-User Interface-Content Risk Measurement*.
- **Format:** `\documentclass[manuscript,review,anonymous]{acmart}` (CHI 2026), pinned acmart v2.19 in-repo.
- **Length:** **26pp**, builds clean (0 undefined ref/cite). PDF metadata anonymous (no `/Author`).
- **Figure 1:** owner's hand-drawn 4-panel overview, inserted as an acmart **teaserfigure** (MUST be BEFORE
  `\maketitle` or the label drops from .aux), `\label{fig:overview}`, file `figures/fig1_overview.pdf`
  (clean copy of `docs/paper/FIG2 two ways.pdf`). All 4 panels data-verified against 20-item results.
- **STRUCTURE = SINGLE-AXIS (B2, owner-approved).** Main paper audits ONLY the coercion / wrong-advice axis
  (axis 2). The over-dispersion axis (axis 1) — human anchor, synthetic-persona-disagreement + Fig3
  (`fig:collapse`), and the panel<->human correspondence null (`sec:corr`) — was relocated to
  **Appendix `app:overdispersion`** ("Supplement: The Over-Dispersion Axis"). All 4 contributions preserved;
  contribution #4 reworded to "two-axis construct: coercion validated, over-dispersion candidate diagnostic."

## What this session did (D5.62 → D5.86, all committed; see DECISIONS.md)
Two simulated-CHI-reviewer rounds + a 3-model panel review, all integrated:
- **Reviewer #1 (5 pts):** #4 CHI framing + 6-step **protocol box** (`fig:protocol`, top of Discussion);
  #5 threshold reframe (flip = "decision instability conditional on a chosen threshold" + threshold-free
  companions range 0.15-0.66 & Fleiss' k); #6 **result-tier tags** ([Primary/Mechanism/Boundary]) on every
  Results subsection; #3 = B2 single-axis; #2 = dispositional ablation (below).
- **#2 dispositional ablation (RAN, owner-approved integration):** new `prompt_style="dispositional"` in
  `src/twdf/panel/real_panel.py` (states experience + AI-use + **low self-confidence** as facts, NO trust
  policy). Result (`results/dispositional_ablation.json`): deferential disposition out-adopts independent on
  ALL 4 backends (gap +0.08..+0.83); the lever is **low self-confidence**, not the novice label. Integrated
  into the manipulation-check subsection as a stronger anti-circularity control. Config
  `configs/dispositional_ablation.yaml`, script `scripts/analysis/dispositional_probe.py`.
- **Seshadri "Lost in Simulation" = ACL 2026 long paper** (NOT concurrent; verified aclanthology
  2026.acl-long.2192). Fixed bib + Related Work + added a hardened Intro distinction.
- **3-model panel review (A=Opus Reviewer, B=GPT-5.6-Sol Reject, C=Opus Area Chair).** Full outputs saved to
  `session-state/.../files/reviews/` (review_A_opus.md, review_B_gpt56sol.md, review_C_areachair.md).
  **Verdict: C = Weak Reject, liftable to Borderline/Weak Accept via rebuttal; the decisive lever is HUMAN
  DATA (an E6 pilot).** AC independently caught a real bug (fixed): beer tau-sweep said 0.35-0.65 but beer
  max adoption is 0.60 -> corrected to 0.35-0.60. Also softened the abstract "level not slope" overclaim
  (rested on an underpowered null interaction chi2(5)=1.70 p=0.89) to "backend-dependence we cannot detect."
- **Honesty pass:** "vulnerability coverage" -> "synthetic-vulnerability coverage" in load-bearing spots;
  "validated" scoped to "against a matched neutral baseline, not human behaviour"; "users who matter most"
  -> "failure cells that matter most"; Conclusion aligned to single-axis.
- **Citation-accuracy fixes (from owner's ref-check reports):** removed `wang2025mixture` (Mixture-of-Agents
  = aggregation, not routing) from all 4 router citations; recast `rastogi2022deciding` (bias/complementarity,
  not "offline team-performance estimation"); dropped `hamalainen2023` from the caricature bundle;
  `park2024generative` "~85% accuracy" -> "82-86% of participants' own two-week test-retest consistency".
  Two commercial-platform bib entries (`syntheticusers`, `uxia_synthetic`) metadata-corrected.

## Authoritative numbers (20-item; DO NOT change without rerun)
Dark wrong-advice adoption, 6 backends x 2 datasets (beer / amzbook):
gpt-4o-mini 0.50/0.475 · gpt-4.1 0.60/0.658 · gpt-4o 0.433/0.475 · gpt-5.5 0.30/0.15 ·
claude-sonnet-4.5 0.492/0.442 · gemini-2.5-pro 0.525/0.492.
Flip: beer 3clear/3flag rate 0.60; amzbook 5clear/1flag rate 0.33. Coverage (dark adopt>=0.5, of 6):
single frontier gpt-5.5 = 1/6 beer, 0/6 amzbook; weak pair (gpt-4.1+gpt-4o-mini) = 4/6, 5/6 = **same as
full 6-backend panel** (coverage saturates — this is the point). gpt-5.5 System-1 acc 0.93, p5 adoption 0.50.

## IN-FLIGHT: A1 = 50-item confirmatory rerun (owner said keep running)
Goal: raise the load-bearing coercion evidence from 20 items / 8 matched-wrong clusters to **50 items** (the
Bansal ceiling; can't go higher without a new dataset). 4 configs, cache-resumable, serial proxy only:
- `configs/axis2_powered_capladder_n50.yaml`  (beer) — **DONE** (`results/axis2_powered_capladder_n50.json`)
- `configs/axis2_powered_crossvendor_n50.yaml` (beer) — **DONE** (`results/axis2_powered_crossvendor_n50.json`)
- `configs/axis2_powered_capladder_amzbook_n50.yaml` — **DONE** (`results/axis2_powered_capladder_amzbook_n50.json`)
- `configs/axis2_powered_crossvendor_amzbook_n50.yaml` — **NOT DONE / BLOCKED.** Fails because
  **claude-sonnet-4.5 persistently returns empty `choices`** on amzbook right now (12 retries exhausted) — a
  transient MODEL-AVAILABILITY issue, not a code bug (gpt-5.5 + gemini-2.5-pro parts are cached). A detached
  rerun was left running at retirement; if it's still failing, **just re-run this one config when
  claude-sonnet-4.5 recovers** — cache resumes everything else, so it finishes fast.
Runner: `python -m twdf.experiments.axis2_powered --config configs/<name>.yaml`
(PYTHONPATH=src). Provider hardened this session: empty-`choices` responses now retry, and the retry backoff
is **capped at 90s** (max_retries 12–15 with the old uncapped `2**attempt` gave absurd 500–2000s waits).

## NEXT ACTIONS (once A1's 4 configs are all done)
1. **Refresh all 20-item axis-2 numbers to 50-item** across abstract, Fig 1 caption, sec:modeldep,
   sec:coercion (the OR now on ~20 matched-wrong clusters not 8 — check if amzbook OR 1.17 firms up),
   sec:instability, sec:capvuln. Re-derive `displayed_ai_advice = 1 - ground_truth` yourself (sign-trap).
2. **Panel #1 — flip-rate rigor (on 50-item):** report **bootstrap flip *probability*** (not just point
   flip rate) + count only pairs whose Wilson CIs are disjoint and straddle tau as "significant" flips;
   foreground the threshold-free evidence (range, Fleiss' k) and demote tau. (AC + reviewer both flagged the
   point flip-rate as fragile at 120 trials/cell; 50 items ~2.5x helps.)
3. **Capability-vulnerability mechanical decomposition:** quantify and remove the "a correct backend cannot
   adopt a wrong AI" component (use AI-induced flip P(adopt|System-1 correct)); report whether the inversion
   holds beyond amzbook. Bootstrap CIs on the (degenerate 6-group) variance shares.
4. Then re-run the 3-model panel (or a rubber-duck) to confirm the fragility criticisms are answered.

## OWNER DECISIONS OUTSTANDING
- **D1 (E6 human pilot) — deferred by owner ("过几天做").** This is the AC's single decisive lever to move
  Weak Reject -> Weak Accept. Prereg + prototype are READY: `docs/plans/2026-07-28-e6-stripped-prereg.md`,
  `e6-prototype/index.html`, power analysis `scripts/analysis/e6_power.py` (N~=60). Do NOT use E6 to paper
  over current gaps; it is the final external-validity stage. Owner's strategy note: `comment2.md`.
- **D2 = target venue CHI** (owner confirmed; AC judged below-CHI-bar as-submitted, ~20-25%, stronger after
  the human study — but owner wants CHI).

## ENV GOTCHAS (unchanged, still bite)
- Proxy `ghc-api` http://127.0.0.1:8787/v1: **serial only** (429 under concurrency); never run 2 arms at once.
  If down: `ghc-api -p 8787 -a 127.0.0.1 --no-enable-auth`.
- Reasoning models (gpt-5.x, gemini-*-pro) need `token_param=max_completion_tokens` + `min_completion_tokens>=4096`;
  others `max_tokens=600`. **claude-haiku-4.5 is unusable** (0 parseable decisions).
- `PYTHONPATH=(Resolve-Path .\src).Path` before any twdf python.
- pdflatex at `C:\Users\v-elzhang\AppData\Local\Programs\MiKTeX\miktex\bin\x64\`; sequence
  pdflatex -> bibtex -> pdflatex -> pdflatex. PDF->PNG self-check via `pdftocairo.exe` (same dir).
- **teaserfigure MUST precede `\maketitle`** (acmart). `\graphicspath{{../../figures/}}`.

## DO NOT
Freeze thresholds/N after seeing results; trust a subagent verdict without your own numeric re-derivation;
pool axis-1 across incomparable backends; run 2 proxy arms in parallel; fabricate BibTeX (verify every cite);
mass-replace "interface"->"interface framing" (over-sanitizes; scope is already disclosed); forget to
rebuild+commit main.pdf; forget `$env:GH_TOKEN=$null`.
