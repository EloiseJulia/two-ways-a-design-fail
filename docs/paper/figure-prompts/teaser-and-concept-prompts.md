# Conceptual / teaser figure prompts (generated via the CCF-Figure skill)

> Purpose: the paper's 8 existing figures are all **data plots** (kept, untouched). What a CHI submission
> most benefits from — and what an image model does well — is a **conceptual teaser / graphical abstract**
> and a couple of concept diagrams. Below are three ready-to-paste prompts, assembled per the
> `CCF-Figure` skill (paper type **B — Mechanism/Analysis** + **D — Empirical**; flat 2D vector,
> top-venue style, English labels, one clear storyline each, anti-decoration constraints).
>
> **How to use:** paste one prompt into an image model that handles in-figure text well
> (GPT Image / "Nano-Banana" / Ideogram are best for labels; Midjourney is prettier but garbles text).
> Generate, then iterate on the ONE element you want changed.
>
> **Honest caveat (read before camera-ready):** AI image models frequently **garble small text labels**.
> These outputs are excellent for a *concept teaser* and for deciding the visual story, but for the final
> camera-ready a text-perfect **editable vector** (TikZ/Figma/Illustrator) is safer. I can build a TikZ
> version of whichever of these you like — just say which.

---

## FIGURE 1 — Graphical Abstract / Teaser
### "The same interface, a different verdict"  (the single highest-value figure)

```
Role: You are an expert scientific illustrator for top HCI/AI venues (CHI, NeurIPS). Produce a
publication-quality GRAPHICAL ABSTRACT / teaser figure: 2D flat vector, pure white background (#FFFFFF),
clean thin lines, functional color only, generous whitespace, ONE clear visual storyline. English labels
only, max two font sizes, all text horizontal and legible. This is a Mechanism/Analysis (measurement-audit)
HCI paper, NOT a generic "input-model-output" pipeline.

THE ONE THING THIS FIGURE MUST SAY: a synthetic LLM "user panel" that screens an interface for risk gives a
verdict that FLIPS between "safe" and "dangerous" depending only on which backend LLM powers it — and the
strongest model is the blindest to the most at-risk user.

Layout (left -> right storyline):
1) LEFT: a single "interface under test" — a small UI card labeled "AI-advice interface" showing an AI
   verdict, a confidence score, a highlighted "explanation", and a coercive banner. Label it "the SAME
   interface". This is the fixed input.
2) CENTER: an arrow into a box labeled "Synthetic LLM user panel (personas x backends)". Inside, show a
   small grid: rows = 6 persona icons (one highlighted, labeled "trusting novice"), columns = several
   different backend LLM chips (e.g., "backend A ... frontier"). Emphasize with a subtle accent that the
   panel itself is "the measurement instrument".
3) RIGHT: the same interface fans out to 3-4 identical risk gauges, one per backend, each a dial with a
   dashed "flag" threshold. Some dials land in GREEN ("safe" / below threshold), others in RED
   ("dangerous" / above threshold). Add a bold callout: "same interface -> verdict flips" and a small tag
   "flip rate up to 0.60". Green = safe, red = dangerous are the ONLY two accent colors used prominently.
4) BOTTOM STRIP (a thin summary band, low-saturation background): a tiny inset showing an inverse relation —
   an up-arrow "model capability" next to a down-arrow "sees the at-risk user", with a one-line label
   "the strongest model is the blindest screener". Keep it small; the flip is the visual focus.

Symbols: interface = UI card; panel = rectangle containing a persona x backend grid; risk reading = dial/
gauge with a dashed threshold; safe/dangerous = green/red fill. Connection lines must not cross text.

Prohibited: 3D perspective, drop shadows, glow, gradient backgrounds, neon colors, texture fills,
commercial-poster look, fake formulas, garbled or tiny unreadable text, more than 3 color groups.
```

---

## FIGURE 2 — Method / Measurement-Pipeline Overview
### "The backend is part of the instrument"

```
Role: Expert scientific illustrator for CHI/NeurIPS. Produce a publication-quality METHOD OVERVIEW figure:
2D flat vector, white background, clean lines, functional color (max 3 groups), one clear left-to-right
storyline, English labels only, max two font sizes, horizontal text. This is a measurement-audit method,
not a model architecture.

THE ONE THING THIS FIGURE MUST SAY: how a synthetic panel turns an interface into a risk decision, and why
the honest output is a DISTRIBUTION across backends with ABSTENTION on disagreement — not a single number.

Layout (layered horizontal pipeline, 5 stages):
1) "Interface content" (a card: AI prediction + confidence + explanation + coercive/protective framing),
   encoded as text. Label: "content & framing, not pixels".
2) "Panel = personas x backends": a grid, rows = 6 personas (novice/expert x trusting/skeptical + 2
   moderates; highlight the trusting-novice), columns = backend LLMs (a within-provider ladder + independent
   vendors). Put a subtle accent border around this whole box labeled "the measurement instrument".
3) "Two-stage decision per agent": a small two-step motif — "System-1 (no AI)" then "System-2 (with AI +
   framing)", with a bracket "reliance = change from System-1". 
4) "Two risk axes": two compact meters — Axis 2 "wrong-advice adoption under coercion" (load-bearing,
   accent color) and Axis 1 "reliance over-dispersion" (secondary, gray). A diamond decision node:
   "adoption >= threshold -> flag for human study?".
5) OUTPUT (accent, the contribution): instead of one number, a small distribution/box-plot over backends
   with a rule: "report a DISTRIBUTION; ABSTAIN & route to a human study when backends disagree".

Make stage 2 (the panel/instrument) and stage 5 (distribution + abstain) the two visually dominant blocks;
gray-down the rest. Arrows labeled with what flows (text-encoded interface; per-agent decisions; per-backend
readings). Lines must not cross labels.

Prohibited: 3D, shadows, glow, gradients, neon, textures, poster style, fake formulas, unreadable text,
more than 3 color groups.
```

---

## FIGURE 3 — The Capability–Vulnerability Inversion
### "Don't crash-test with your safest driver"

```
Role: Expert scientific illustrator for CHI/NeurIPS. Produce a publication-quality CONCEPT/CONTRAST figure:
2D flat vector, white background, clean lines, at most 3 functional colors, one clear storyline, English
labels only, max two font sizes, horizontal text. Restrained and academic — the memorable idea comes from
clarity, not decoration.

THE ONE THING THIS FIGURE MUST SAY: as a backend LLM gets MORE capable, it becomes LESS able to reproduce
the most at-risk user's over-reliance — so the strongest model is the worst probe for interface danger.

Layout (a horizontal axis + a contrast):
- A horizontal axis "backend capability (weak -> frontier)".
- Two diverging trend lines over that axis: one rising line "task competence" (up), one falling line
  "reproduces the at-risk user / vulnerability coverage" (down). Mark their divergence as the key finding
  with a subtle accent; annotate "capability up, vulnerability coverage down".
- LEFT end ("weaker backends"): a small panel of 6 persona icons, most flagged RED ("sees the danger",
  covers ~4-5 of 6).
- RIGHT end ("frontier backend"): the same 6 personas but almost all GREEN/gray ("blind to it", covers ~1
  of 6) — visually the frontier "sees almost nothing".
- One restrained metaphor annotation (small, optional, abstract icon of a car + a calm driver):
  "like crash-testing with your safest driver". Keep this tiny and flat; do NOT let it dominate.
- A one-line bottom banner: "select a panel for vulnerability coverage — the inverse of capability routing".

Green = at-risk user is surfaced, red/gray = missed, plus one accent color for the divergence. Nothing else.

Prohibited: 3D, shadows, glow, gradients, neon, textures, poster/marketing style, fake numbers, garbled or
tiny text, cartoonish characters, more than 3 color groups.
```

---

## Paper facts to keep the figures logically accurate (paste alongside if the model asks for context)
- Title: *Two Ways a Design Fails: When Does a Synthetic LLM Panel See the Danger?*
- It AUDITS whether a synthetic LLM user-panel's interface-risk reading is stable; it does NOT claim to
  predict real humans (a human study is planned).
- Panel = 6 personas x up to 11 backend LLMs. Two axes: Axis 2 = wrong-advice adoption under coercion
  (load-bearing); Axis 1 = reliance over-dispersion (exploratory).
- Key results to honor: wrong-advice adoption swings 0.15–0.66 across backends; risk-classification flip
  rate up to 0.60; the strongest backend (frontier) reproduces the trusting-novice failure least (adoption
  ~0.50 vs ~1.0 for weaker models); a single frontier backend covers ~1/6 at-risk personas vs 4–5/6 for a
  weak pair. Recommendation: report a distribution over backends and abstain when they disagree.
- Voice/metaphor already used in the paper: "the backend is part of the measurement instrument";
  "you would not crash-test with your safest driver"; "the most trustworthy panel knows when to abstain".
