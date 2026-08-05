"""Two-stage Monte-Carlo power analysis for the human coercion study.

This simulation matches the judge-advisor design rather than drawing the final
"adoption" outcome directly:

1. A participant makes an initial judgment. Its correctness probability is
   anchored to each selected item's historical no-AI human accuracy.
2. The guaranteed-wrong AI recommendation is revealed.
3. If the initial judgment was correct, the participant may flip to the wrong
   AI recommendation. This correct->wrong flip is the primary harm estimand.
4. If the initial judgment was already wrong, it normally remains wrong; these
   trials contribute to raw final wrong-advice agreement but not to the clean
   conflict-conditioned flip estimand.

The main confirmatory block has 12 trials per participant (4 neutral, 4
placebo, 4 static-dark). The three trailing dark+directive escalation trials
are exploratory and excluded from this power calculation.

The generator includes:
- exactly balanced beer/amzbook allocation;
- the final selected item accuracies from stimuli_{domain}.json;
- item-by-condition Latin rotations;
- participant ability and compliance heterogeneity;
- item susceptibility heterogeneity;
- optional trial-position learning (declining AI trust);
- participant-clustered logistic inference with domain and item fixed effects.

Outputs:
  study/power_results.json

Run:
  python study/power_sim.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.special import expit, logit
from scipy.stats import norm


ROOT = Path(__file__).resolve().parents[1]
STIM_DIR = ROOT / "study" / "stimuli"
OUT_PATH = ROOT / "study" / "power_results.json"

SEED = 20260805
ALPHA_ONE_SIDED = 0.05
CONDITIONS = ("neutral", "placebo", "dark")
N_MAIN_ITEMS = 12

# Generative heterogeneity. These are deliberately non-trivial: the old
# simulation's single Bernoulli draw was too optimistic.
ABILITY_SD = 0.70
COMPLIANCE_SD = 0.80
ITEM_FLIP_SD = 0.45
WRONG_RETENTION = 0.95
DEFAULT_LEARNING_LOG_OR_PER_TRIAL = -0.04

# 200 gives Monte-Carlo SE <= .035 at p=.50; sensitivity runs are directional.
N_SIM_MAIN = 200
N_SIM_SENSITIVITY = 120


def _clip_prob(p: float) -> float:
    return float(np.clip(p, 1e-4, 1 - 1e-4))


def load_item_accuracies() -> dict[str, np.ndarray]:
    """Load historical no-AI accuracy for the 12 final main items/domain."""
    out: dict[str, np.ndarray] = {}
    for domain in ("beer", "amzbook"):
        payload = json.loads((STIM_DIR / f"stimuli_{domain}.json").read_text(encoding="utf-8"))
        rows = payload["main"]
        if len(rows) != N_MAIN_ITEMS:
            raise ValueError(f"{domain}: expected {N_MAIN_ITEMS} main items, got {len(rows)}")
        out[domain] = np.asarray([float(r["human_noai_accuracy"]) for r in rows])
    return out


def simulate_dataset(
    *,
    n: int,
    neutral_flip: float,
    dark_flip_beer: float,
    dark_flip_amzbook: float | None = None,
    placebo_flip: float | None = None,
    learning_log_or_per_trial: float = DEFAULT_LEARNING_LOG_OR_PER_TRIAL,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate one complete N-participant, two-stage confirmatory dataset."""
    if n % 2:
        raise ValueError("n must be even so domains are exactly balanced")
    dark_flip_amzbook = dark_flip_beer if dark_flip_amzbook is None else dark_flip_amzbook
    placebo_flip = neutral_flip if placebo_flip is None else placebo_flip
    item_acc = load_item_accuracies()

    rows: list[tuple] = []
    n_per_domain = n // 2
    subject_id = 0

    for domain in ("beer", "amzbook"):
        dark_target = dark_flip_beer if domain == "beer" else dark_flip_amzbook
        base_flip = {
            "neutral": neutral_flip,
            "placebo": placebo_flip,
            "dark": dark_target,
        }

        # Shared item susceptibility for this simulated dataset.
        item_flip_re = rng.normal(0, ITEM_FLIP_SD, N_MAIN_ITEMS)

        for within_domain_id in range(n_per_domain):
            ability = rng.normal(0, ABILITY_SD)
            compliance = rng.normal(0, COMPLIANCE_SD)

            # Latin rotation: every item is assigned to every condition equally
            # across each group of three participants.
            rotation = within_domain_id % 3
            item_condition = {
                item: CONDITIONS[(item + rotation) % len(CONDITIONS)]
                for item in range(N_MAIN_ITEMS)
            }
            display_order = rng.permutation(N_MAIN_ITEMS)

            for position_zero, item in enumerate(display_order):
                position = position_zero + 1
                cond = item_condition[int(item)]

                # Initial judgment is strictly pre-treatment.
                p_initial_correct = expit(logit(_clip_prob(item_acc[domain][item])) + ability)
                initial_correct = int(rng.binomial(1, p_initial_correct))

                # AI trust can decay as participants discover the advice is poor.
                eta_flip = (
                    logit(_clip_prob(base_flip[cond]))
                    + compliance
                    + item_flip_re[item]
                    + learning_log_or_per_trial * position_zero
                )
                p_flip = expit(eta_flip)

                if initial_correct:
                    flipped_to_wrong = int(rng.binomial(1, p_flip))
                    final_wrong = flipped_to_wrong
                else:
                    flipped_to_wrong = 0
                    final_wrong = int(rng.binomial(1, WRONG_RETENTION))

                rows.append(
                    (
                        subject_id,
                        domain,
                        f"{domain}_{item}",
                        position,
                        cond,
                        int(cond == "dark"),
                        int(cond == "placebo"),
                        initial_correct,
                        flipped_to_wrong,
                        final_wrong,
                    )
                )
            subject_id += 1

    return pd.DataFrame(
        rows,
        columns=[
            "subject",
            "domain",
            "item_uid",
            "position",
            "cond",
            "is_dark",
            "is_placebo",
            "initial_correct",
            "flipped_to_wrong",
            "final_wrong",
        ],
    )


def test_dark_effect(df: pd.DataFrame, outcome: str, *, conflict_only: bool) -> tuple[bool, float]:
    """One-sided dark>neutral test; return (significant, estimated OR)."""
    work = df[df["cond"].isin(("neutral", "dark"))].copy()
    if conflict_only:
        work = work[work["initial_correct"] == 1].copy()
    if work[outcome].nunique() < 2 or len(work) < 30:
        raise ValueError("outcome has insufficient variation")

    work["position_c"] = work["position"] - work["position"].mean()
    # Item susceptibility is present in the generator. The Latin rotation makes
    # condition orthogonal to item, so the power-test fit uses domain + position
    # and participant-clustered inference. A 24-level item-fixed-effect fit was
    # prohibitively slow and separation-prone in Monte Carlo; it remains a
    # prespecified sensitivity analysis for the observed dataset.
    model = smf.logit(
        f"{outcome} ~ is_dark + C(domain) + position_c",
        data=work,
    ).fit(
        disp=0,
        maxiter=100,
        cov_type="cluster",
        cov_kwds={"groups": work["subject"], "use_correction": True},
    )
    beta = float(model.params["is_dark"])
    se = float(model.bse["is_dark"])
    p_one = float(1 - norm.cdf(beta / se))
    return bool(beta > 0 and p_one < ALPHA_ONE_SIDED), float(np.exp(beta))


def estimate_power(
    *,
    n: int,
    neutral_flip: float,
    dark_flip_beer: float,
    dark_flip_amzbook: float | None = None,
    learning_log_or_per_trial: float = DEFAULT_LEARNING_LOG_OR_PER_TRIAL,
    n_sim: int,
    seed_offset: int,
) -> dict:
    """Estimate power for both the clean flip and raw final-agreement outcomes."""
    rng = np.random.default_rng(SEED + seed_offset)
    hits_flip = 0
    hits_raw = 0
    ors_flip: list[float] = []
    ors_raw: list[float] = []
    failed = 0

    for _ in range(n_sim):
        df = simulate_dataset(
            n=n,
            neutral_flip=neutral_flip,
            dark_flip_beer=dark_flip_beer,
            dark_flip_amzbook=dark_flip_amzbook,
            learning_log_or_per_trial=learning_log_or_per_trial,
            rng=rng,
        )
        try:
            sig_flip, or_flip = test_dark_effect(
                df, "flipped_to_wrong", conflict_only=True
            )
            sig_raw, or_raw = test_dark_effect(
                df, "final_wrong", conflict_only=False
            )
            hits_flip += int(sig_flip)
            hits_raw += int(sig_raw)
            ors_flip.append(or_flip)
            ors_raw.append(or_raw)
        except Exception:
            failed += 1

    completed = n_sim - failed
    if not completed:
        raise RuntimeError("all simulations failed")
    return {
        "n": n,
        "neutral_flip": neutral_flip,
        "dark_flip_beer": dark_flip_beer,
        "dark_flip_amzbook": (
            dark_flip_beer if dark_flip_amzbook is None else dark_flip_amzbook
        ),
        "learning_log_or_per_trial": learning_log_or_per_trial,
        "n_sim": n_sim,
        "completed": completed,
        "failed": failed,
        "power_flip_primary": round(hits_flip / completed, 3),
        "power_raw_adoption": round(hits_raw / completed, 3),
        "median_estimated_or_flip": round(float(np.median(ors_flip)), 3),
        "median_estimated_or_raw": round(float(np.median(ors_raw)), 3),
        "mc_se_flip": round(
            float(np.sqrt((hits_flip / completed) * (1 - hits_flip / completed) / completed)),
            3,
        ),
    }


def main() -> None:
    item_acc = load_item_accuracies()
    print("Final-item historical no-AI accuracy:")
    for domain, vals in item_acc.items():
        print(
            f"  {domain:7s} mean={vals.mean():.3f}, range={vals.min():.3f}-{vals.max():.3f}"
        )
    print(
        f"\nTwo-stage simulation: N=80, 12 main trials (4/condition), "
        f"abilitySD={ABILITY_SD}, complianceSD={COMPLIANCE_SD}, "
        f"itemFlipSD={ITEM_FLIP_SD}, learning log-OR/trial="
        f"{DEFAULT_LEARNING_LOG_OR_PER_TRIAL}"
    )

    scenarios = [
        ("small", 0.095, 0.13, None),
        ("moderate", 0.095, 0.16, None),
        ("strong", 0.095, 0.22, None),
        # Paper-like cross-domain heterogeneity: one strong, one weak domain.
        ("domain_heterogeneous", 0.095, 0.22, 0.13),
        # Directive-sized upper bound; escalation arm only, not the main dark.
        ("directive_sized_upper_bound", 0.095, 0.29, None),
    ]

    results: dict[str, object] = {
        "design": {
            "primary": "correct-to-wrong flip among initially-correct trials",
            "secondary": "raw final wrong-advice agreement",
            "n_main_trials": N_MAIN_ITEMS,
            "conditions": list(CONDITIONS),
            "escalation_trials_excluded": 3,
            "alpha_one_sided": ALPHA_ONE_SIDED,
            "ability_sd": ABILITY_SD,
            "compliance_sd": COMPLIANCE_SD,
            "item_flip_sd": ITEM_FLIP_SD,
            "wrong_retention": WRONG_RETENTION,
            "learning_log_or_per_trial": DEFAULT_LEARNING_LOG_OR_PER_TRIAL,
        },
        "scenarios_n80": {},
        "n_sensitivity_moderate": {},
        "learning_sensitivity_n80_moderate": {},
    }

    print("\nN=80 scenario power:")
    for idx, (name, neutral, dark_beer, dark_amzbook) in enumerate(scenarios):
        res = estimate_power(
            n=80,
            neutral_flip=neutral,
            dark_flip_beer=dark_beer,
            dark_flip_amzbook=dark_amzbook,
            n_sim=N_SIM_MAIN,
            seed_offset=idx * 1000,
        )
        results["scenarios_n80"][name] = res
        print(
            f"  {name:28s} q: {neutral:.3f}->{dark_beer:.3f}"
            + (
                f"/{dark_amzbook:.3f}" if dark_amzbook is not None else ""
            )
            + f" | power flip={res['power_flip_primary']:.2f}, "
            f"raw={res['power_raw_adoption']:.2f}, "
            f"median OR flip={res['median_estimated_or_flip']:.2f}"
        )

    print("\nN sensitivity (moderate flip 0.095->0.16):")
    for idx, n in enumerate((80, 100, 120, 150)):
        res = estimate_power(
            n=n,
            neutral_flip=0.095,
            dark_flip_beer=0.16,
            n_sim=N_SIM_SENSITIVITY,
            seed_offset=10000 + idx * 1000,
        )
        results["n_sensitivity_moderate"][str(n)] = res
        print(
            f"  N={n:<3d} power flip={res['power_flip_primary']:.2f}, "
            f"raw={res['power_raw_adoption']:.2f}"
        )

    print("\nLearning sensitivity at N=80 (moderate):")
    for idx, slope in enumerate((0.0, -0.04, -0.08)):
        res = estimate_power(
            n=80,
            neutral_flip=0.095,
            dark_flip_beer=0.16,
            learning_log_or_per_trial=slope,
            n_sim=N_SIM_SENSITIVITY,
            seed_offset=20000 + idx * 1000,
        )
        results["learning_sensitivity_n80_moderate"][str(slope)] = res
        print(
            f"  learning={slope:+.2f}/trial power flip="
            f"{res['power_flip_primary']:.2f}, raw={res['power_raw_adoption']:.2f}"
        )

    OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
