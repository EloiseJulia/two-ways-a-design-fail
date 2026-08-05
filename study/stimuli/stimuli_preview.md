# Human-study stimuli preview (axis-2 coercion validation, Option A: sentiment)

Items selected in the *movable band* (human no-AI accuracy ~0.70): usually right but not certain, so a confident WRONG AI can plausibly move them. All three conditions show the **same guaranteed-wrong** advice (displayed = 1 − ground truth); only framing differs.


## beer — main  (12 items; human no-AI accuracy in brackets)

| item | truth | human acc | AI shows (wrong) |
|---|---|---|---|
| 11 | NEGATIVE | 0.71 | POSITIVE |
| 0 | NEGATIVE | 0.69 | POSITIVE |
| 48 | NEGATIVE | 0.75 | POSITIVE |
| 37 | NEGATIVE | 0.81 | POSITIVE |
| 36 | NEGATIVE | 0.59 | POSITIVE |
| 31 | NEGATIVE | 0.58 | POSITIVE |
| 45 | NEGATIVE | 0.83 | POSITIVE |
| 46 | NEGATIVE | 0.83 | POSITIVE |
| 5 | POSITIVE | 0.63 | NEGATIVE |
| 28 | POSITIVE | 0.88 | NEGATIVE |
| 29 | POSITIVE | 0.88 | NEGATIVE |
| 19 | POSITIVE | 0.90 | NEGATIVE |

## beer — escalation  (3 items; human no-AI accuracy in brackets)

| item | truth | human acc | AI shows (wrong) |
|---|---|---|---|
| 39 | NEGATIVE | 0.85 | POSITIVE |
| 14 | NEGATIVE | 0.86 | POSITIVE |
| 32 | NEGATIVE | 0.88 | POSITIVE |

**Example item 11** (truth NEGATIVE, human acc 0.71, AI shows POSITIVE):

> Had this beer on 10/31/2002.  Aroma is a sweet lightly roasted malt scent.  Color is a deep rich amber, there are some flouts in there.  Carbonation is light with thin head.  Taste is richly sweet.  Starting with a heavy/medium body it goes down with a rich feel.  Finish is rich and sweet, no bitterness to balance it out.  This is not a brew I would go out and buy again. …

*neutral:*
```
AI prediction: POSITIVE
AI confidence: 92%
```
*placebo:*
```
AI prediction: POSITIVE
AI confidence: 92%

Explanation: The AI model analyzed the input using its trained parameters and generated this recommendation based on its internal confidence evaluation.
```
*dark:*
```
⚠️ CRITICAL DECISION ⚠️

AI Expert System Recommendation: POSITIVE
AI Confidence Level: 92%

IMPORTANT: This AI system has been trained on millions of examples and has demonstrated high accuracy in production use. Deviating from the AI recommendation may result in suboptimal outcomes and you will be held accountable for your decision.

Please consider the AI's expertise carefully before making your final choice.

Your decision carries full responsibility. Choose wisely.
```

## amzbook — main  (12 items; human no-AI accuracy in brackets)

| item | truth | human acc | AI shows (wrong) |
|---|---|---|---|
| 1 | NEGATIVE | 0.71 | POSITIVE |
| 45 | NEGATIVE | 0.68 | POSITIVE |
| 26 | NEGATIVE | 0.66 | POSITIVE |
| 13 | NEGATIVE | 0.76 | POSITIVE |
| 3 | NEGATIVE | 0.81 | POSITIVE |
| 10 | NEGATIVE | 0.81 | POSITIVE |
| 15 | POSITIVE | 0.72 | NEGATIVE |
| 22 | POSITIVE | 0.76 | NEGATIVE |
| 21 | POSITIVE | 0.80 | NEGATIVE |
| 4 | POSITIVE | 0.57 | NEGATIVE |
| 33 | POSITIVE | 0.83 | NEGATIVE |
| 12 | POSITIVE | 0.85 | NEGATIVE |

## amzbook — escalation  (3 items; human no-AI accuracy in brackets)

| item | truth | human acc | AI shows (wrong) |
|---|---|---|---|
| 25 | NEGATIVE | 0.82 | POSITIVE |
| 20 | NEGATIVE | 0.85 | POSITIVE |
| 34 | NEGATIVE | 0.87 | POSITIVE |

**Example item 1** (truth NEGATIVE, human acc 0.71, AI shows POSITIVE):

> This book was a retelling of Cinderella from the Fairy Godmother's point of view. It takes some liberties with the original Cinderella story. In this book's version, the Fairy Godmother was young and beautiful like Cinderella. She majorly screwed up when trying to help Cinderella get to the ball and was banished to live as a human on earth as punishment.The beginning and middle of this book was so …

*neutral:*
```
AI prediction: POSITIVE
AI confidence: 92%
```
*placebo:*
```
AI prediction: POSITIVE
AI confidence: 92%

Explanation: The AI model analyzed the input using its trained parameters and generated this recommendation based on its internal confidence evaluation.
```
*dark:*
```
⚠️ CRITICAL DECISION ⚠️

AI Expert System Recommendation: POSITIVE
AI Confidence Level: 92%

IMPORTANT: This AI system has been trained on millions of examples and has demonstrated high accuracy in production use. Deviating from the AI recommendation may result in suboptimal outcomes and you will be held accountable for your decision.

Please consider the AI's expertise carefully before making your final choice.

Your decision carries full responsibility. Choose wisely.
```