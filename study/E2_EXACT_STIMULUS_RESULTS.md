# E2 exact-stimulus synthetic rerun — results for the planned human study

Purpose: establish the synthetic reference distribution on the **same final 12 main items** and the same
guaranteed-wrong, 92%-confidence neutral/placebo/static-dark framings that human participants will see.

## Provenance

- `gpt-4o-mini`, `gpt-4.1`, `gpt-4o`, `gpt-5.5`: newly rerun on all three exact framings.
- Original `claude-sonnet-4.5` and `gemini-2.5-pro`: the proxy no longer serves these model IDs. Their
  exact 12-item **static-dark** rows are extracted from the completed n50 runs; static dark is identical
  (same item, guaranteed-wrong label, 92%, same coercive text). No new neutral/placebo values are claimed.
- 6 personas × 12 items = 72 trials/model/condition.
- Machine-readable summary: `results/e2_human_match_summary.json`.

## Four-backend exact three-condition ladder

### Beer

| backend | adoption N / P / D | flip-from-correct N / P / D |
|---|---|---|
| gpt-4o-mini | .319 / .292 / .375 | .210 / .177 / .274 |
| gpt-4.1 | .417 / .417 / .528 | .236 / .236 / .382 |
| gpt-4o | .306 / .306 / .361 | .167 / .167 / .233 |
| gpt-5.5 | .292 / .208 / .264 | .227 / .136 / .197 |
| **mean across four** | **.333 / .306 / .382** | **.210 / .179 / .272** |

### Amzbook

| backend | adoption N / P / D | flip-from-correct N / P / D |
|---|---|---|
| gpt-4o-mini | .347 / .361 / .458 | .242 / .258 / .371 |
| gpt-4.1 | .556 / .542 / .694 | .289 / .267 / .511 |
| gpt-4o | .347 / .347 / .472 | .161 / .161 / .321 |
| gpt-5.5 | .278 / .236 / .222 | .235 / .191 / .176 |
| **mean across four** | **.382 / .372 / .462** | **.232 / .219 / .345** |

N = neutral, P = placebo, D = static dark.

## Six-backend exact-item static-dark reference

| backend | beer adoption | beer flip | amzbook adoption | amzbook flip |
|---|---:|---:|---:|---:|
| gpt-4o-mini | .375 | .274 | .458 | .371 |
| gpt-4.1 | .528 | .382 | .694 | .511 |
| gpt-4o | .361 | .233 | .472 | .321 |
| **gpt-5.5** | **.264** | **.197** | **.222** | **.176** |
| claude-sonnet-4.5 | .528 | .414 | .431 | .369 |
| gemini-2.5-pro | .500 | .333 | .458 | .350 |

The frontier gpt-5.5 is the lowest static-dark backend on both adoption and correct-to-wrong flip in both
domains. It is also the only ladder backend whose exact-subset dark flip does not exceed neutral
(.197 < .227 beer; .176 < .235 amzbook). This preserves the capability–vulnerability mismatch on the
final human-study items without relying on the broader n50 averages.

## Implication for N=80

Using the exact four-backend mean flip rates as the generative reference:

- neutral ≈ .221 (mean of .210 beer / .232 amzbook);
- dark = .272 beer / .345 amzbook;
- realistic two-stage N=80 simulation (with learning and heterogeneity):
  **power = .635**, median estimated flip OR = **1.505**.

Therefore the human study remains a strong-effect test / moderate-effect bound. Its result should not be
described as a high-powered equivalence or absence test.

## How to use after human data arrive

1. Plot human neutral/placebo/dark flip and raw-adoption estimates with participant+item bootstrap CIs.
2. Overlay the six static-dark backend points above; visibly distinguish newly rerun three-condition
   ladder values from extracted old-vendor dark-only values.
3. Report human/backend correspondence descriptively. Do not crown a “most human-faithful” backend.
4. Analyze the trailing 3 dark+directive trials separately; never mix them into the static-dark reference.
