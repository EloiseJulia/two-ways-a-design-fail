You are a FIX subagent for draft PR #2 (branch feature/e1-multicond) of the HCI
METHODS project "two-ways-a-design-fail". The pre-merge audit PASSED methodology
but found ONE BLOCKER: a cross-process nondeterminism bug. Fix exactly this; do
NOT change anything else. NEVER merge.

## WHERE
Worktree: C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\e1-multicond
Confirm `pwd` + branch (feature/e1-multicond) first. Work ONLY here. Commit trailer
EVERY commit: `Co-authored-by: Copilot <copilot@github.com>`. Push to draft PR #2;
NEVER merge.

## THE BUG (single site — verified the ONLY builtin hash() in src/)
`src/twdf/experiments/e1_multicond.py:117`:
  rng = np.random.RandomState(seeds.get('bootstrap', 42) + hash(ui_cond) % 10000)
Python's builtin `hash()` is randomized per process (PYTHONHASHSEED), so
e1_multicond bootstrap CIs differ across runs. This is the same bug class fixed
earlier in stub.py. Fix by using a STABLE hash, consistent with how the rest of
the repo already does it (check stub.py for the existing hashlib pattern and reuse
it — do NOT introduce a second different style). E.g.:
  import hashlib
  def _stable_seed_offset(s: str) -> int:
      return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)
  ... np.random.RandomState(seeds.get('bootstrap', 42) + _stable_seed_offset(ui_cond) % 10000)
Prefer reusing an existing helper if stub.py already defines one.

## VERIFY (must all hold)
1. `grep`/search confirms NO remaining builtin `hash(` in src/ (only hashlib).
2. Run `python -m twdf.experiments.e1_multicond --config configs/e1_multicond.yaml`
   TWICE in SEPARATE processes; confirm the bootstrap CIs (and all numbers) are
   byte-identical across runs. Quote both runs' correlation + a bootstrap CI to
   prove it.
3. Full `pytest` still passes.
4. e1_vslice, e1_decomposition, e1_robustness still run.
5. `git status` clean (no scratch; data/raw not committed). If any results file
   legitimately changed because the seed offset changed, commit the regenerated
   results so committed config reproduces committed results; otherwise leave
   results untouched.

## DELIVERY
Commit the one-line-class fix (+ any regenerated results) and PUSH to
feature/e1-multicond (draft, never merge). Return to Manager: the exact change,
the two-run byte-identical proof, and pytest summary.
