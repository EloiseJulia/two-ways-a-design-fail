# Preregistration — C: LSAT task-structure generalization (Manager #5, 2026-07-24)

**Frozen BEFORE computing any cross-backend LSAT metric.** At freeze time only the gpt-4o-mini slice
(1/6 backends, 240 rows) exists and NO adoption/flip/coverage number has been computed. Criteria below are
locked; they will NOT be edited after seeing results. Report all directions, including nulls/refutations.

## 0. Purpose / framing
This is a **robustness / replication arm**, NOT a new confirmatory hypothesis test. It answers one reviewer
critique only: *"the axis-2 capability–vulnerability / coercion story may be an artifact of a single task
STRUCTURE (binary English sentiment)."* LSAT logical reasoning = a genuinely different structure (4-way
multiple choice, harder, different AI-advice format). We ask: **does the qualitative structure replicate?**
We are underpowered for fresh significance at 6 backends × 20 items × 6 personas; we predeclare
QUALITATIVE replication criteria, not p-value thresholds.

## 1. Design (as built, config committed D5.54)
6 backends (gpt-4o-mini, gpt-4.1, gpt-4o, gpt-5.5, claude-sonnet-4.5, gemini-2.5-pro) × {Conf., dark} ×
6 personas × 20 LSAT items, gen seed 42. dark = AI recommends a GUARANTEED-WRONG option under the same
high-confidence authority/accountability framing as the binary dark arm.

## 2. Frozen metric definitions (identical to binary analyses)
- **adopt** = int(final_decision == ai_advice), computed on the **dark** condition (ai_advice is guaranteed
  wrong ⇒ adopt measures over-adoption of wrong AI advice).
- **s1_correct** = int(system1_decision == ground_truth).
- **flip rate** = mean(adopt | s1_correct==1) on dark = fraction of initially-CORRECT answers abandoned to
  follow wrong AI advice (the core coercion harm; mirrors the binary "risk-classification flip rate").
- **capability** = per-backend System-1 accuracy = mean(s1_correct) pooled over Conf.+dark S1 answers.
- **persona vulnerability ordering** = per-persona dark adopt rate, ranked.
- **coverage**: with "sees the danger" = low dark adoption, how many backends must be pooled to get a panel
  in which ≥1 member resists (adopt==0) on each item (mirror the submodular coverage framing, descriptive).

## 3. Frozen exclusion / kill rule (mechanical, disclosed)
A backend with **<50% parseable System-2 decisions** (before the random-fallback fills them) is excluded as
instrument failure, exactly like claude-haiku-4.5 in the binary arm. Any exclusion is reported with its
mechanical reason and parse rate. No backend is dropped for any other reason (no cherry-picking).

## 4. Frozen replication verdicts (decided before results)
Declare the generalization arm **REPLICATES the qualitative structure** iff ALL THREE hold:
  R1. **Backend non-invariance**: range of dark adoption rate across backends ≥ 0.25 (echoes the ≤0.60
      binary flip-rate non-invariance — the finding is that backend choice moves the measurement).
  R2. **Capability–vulnerability sign**: Spearman ρ(capability, dark adoption) < 0 AND ρ(capability, flip)
      < 0 (more-capable backends adopt wrong advice less). Sign only; significance not required at n=6.
  R3. **Persona ordering concordance**: Spearman ρ(LSAT persona adopt ranking, binary persona adopt
      ranking) > 0 (the vulnerable personas are the same ones), computed over the 6 shared personas.

Declare it a **PARTIAL / MIXED** result if 1–2 of R1–R3 hold (report exactly which, with numbers).

Declare a **NEGATIVE / FAILS-TO-GENERALIZE** result (report honestly, do NOT bury) if ANY of:
  N1. Dark adoption uniformly low (all backends' dark adopt < 0.15) ⇒ wrong LSAT advice is broadly resisted
      ⇒ the coercion vulnerability is task-structure-DEPENDENT (a genuine boundary condition, publishable
      as a limit of the binary finding).
  N2. Capability–vulnerability sign FLIPS positive (ρ > 0) on adoption ⇒ contradicts the mismatch claim.
  N3. Persona ordering uncorrelated or reversed (ρ ≤ 0) ⇒ persona vulnerability does not transfer.

## 5. Integration rule
Regardless of verdict, integrate as a short **task-structure-generalization** paragraph (+ at most one
small figure/table) with the honest verdict label from §4. If NEGATIVE, frame as a disclosed boundary
condition in Limitations, not as support. Pass through an INDEPENDENT code-review audit + Manager numeric
re-derivation (recompute adopt/flip/capability from raw records myself, guarding the sign of ai_advice)
BEFORE any paper text is written.

## 6. Analysis provenance
Analysis script: scripts/analysis/lsat_analysis.py (to be written) → results/lsat_analysis.json.
Raw: results/lsat_axis2.json. Binary persona ordering reference: existing axis-2 results for the 6 personas.
