# How is the process score calculated?

**The current system combines deterministic checks with explicitly authored ordinal judgments. The process ratings are not fully deterministic.**

There is no single overall process score. Each committed decision is read across five dimensions, with a 0–1–2 ordinal rating where evidence and opportunity permit. The original rubric was frozen before this pilot. The current project assistant, which knew the outcomes and participated in the project's development, authored the ratings. This was not a separate blinded judge-model study or an independent human annotation exercise.

| Layer | What it does | What it establishes |
|---|---|---|
| Numerical checks | Recomputes observations, residuals under an explicitly represented public rule, and acceptance of submitted predictions | Arithmetic agreement within a defined contract |
| Recorded events | Preserves actions, accessible data, public statements, original submissions and protocol terminations | What was recorded and when; not the model's complete private reasoning |
| D1–D5 interpretation | Assigns a dimension-specific anchor to a decision, with cited public evidence, a rationale, limitations and issue tracking | An explicit, challengeable interpretation by the project assistant |
| Mechanical rating validation | Checks packet hashes, evidence pointers, coverage, anchor/score consistency, issue timing and frozen aggregation | Integrity and rule consistency of the supplied ratings; not semantic correctness |

A stated mathematical rule is represented by an analyst-authored adapter before residuals can be calculated. The subtraction is deterministic; deciding that an expression faithfully represents a model's statement can require interpretation. These adapters are labeled in `data/episodes.json`. The evaluator's hidden world configuration is disclosed for replay and is not treated as information the participant possessed.

## The five dimensions

The descriptions below summarize the original Turkish rubric for English readers. The byte-preserved [RUBRIC.json](../src/RUBRIC.json) remains the authoritative version for this snapshot.

| Dimension | Question |
|---|---|
| D1 — Question and uncertainty | Is the question or exploration goal consistent with the available evidence, without turning an assumption into certainty? |
| D2 — Experiment and tool choice | Can the chosen action provide information about the stated question under the known operating conditions? |
| D3 — Evidence interpretation | Are the decision's central claims supported within the observed scope, with hypotheses and contradictions distinguished? |
| D4 — Continuation, retention and revision | Is continuing, retaining, revising or closing the investigation justified by the evidence and remaining uncertainty? |
| D5 — Verification and delivery integrity | Is the claimed validation scope appropriate, and is the visible calculation/submission relationship consistent? |

Broadly, 2 means the criterion is satisfied in the observed opportunity; 1 marks a specified material limitation or a recovered issue under the aggregation rule; 0 marks a criterion-specific central problem supported by evidence. The actual anchors are dimension-specific. A wrong prediction alone does not automatically establish poor process. A short solution, valid alternative method or justified decision to retain an explanation is not penalized for lacking extra steps.

No opportunity, insufficient evidence and out-of-rubric cases remain null. In this pilot, 54 decisions produce 270 cells: 122 scored, 142 no-opportunity, five insufficient-evidence and one out-of-rubric. The two malformed terminal responses remain separate from committed decisions.

## Aggregation and its observed limitation

Within each dimension, applicable unknown evidence makes the full profile null. Otherwise an unresolved critical issue produces 0, a partial or recovered concern produces 1, and the remaining observed cases produce 2. The distribution of individual ratings, opportunity coverage and recovery history are retained. Dimensions are not averaged or added into a global score.

This conservative rule produces D2=0 in three runs because invalid actions after research closure are included alongside useful scientific experiment choices. That should not be read as uniformly poor experimentation. [SENSITIVITY.json](../data/SENSITIVITY.json) preserves alternatives that separate those protocol events from scientific D2, plus declared ambiguities about statement scope. These alternatives are not selected replacements for the original scores.

## What the public program checks

[`replay.py`](../replay.py) recomputes numerical quantities and calls the preserved [`score_review`](../src/scoring.py) function on each original packet/review pair. The latter checks references and reproduces the frozen profile. It does not read a transcript and infer a new rating. Original rationales remain in Turkish in the evidence files; the model's public records are in English.

For example, [w2-r1/REVIEW.json](../evidence/sol-high-cdr-w2-r1/REVIEW.json) has a packet hash, evidence pointers and an anchor for each rating. The matching [PACKETS.json](../evidence/sol-high-cdr-w2-r1/PACKETS.json) contains the actual pre-action public context. A pointer to a changed value fails verification. Whether the anchored interpretation is the best reading remains open to review.

Independent reader agreement, blinding effects, paraphrase/style sensitivity and broader construct validity remain unmeasured. Human-reader consistency was deferred in the research plan. This release exposes the current method so that those validation questions can be posed precisely; successful arithmetic replay is not a substitute for them.

## Short answer for an application or project discussion

> The system currently has two layers. Deterministic checks replay experimental measurements, compare explicit numerical claims with the evidence available at the time, and verify final predictions and recorded outcomes. The D1–D5 process ratings are evidence-linked, ordinal judgments authored by the project assistant using a frozen rubric. Code checks their provenance, coverage and aggregation, but does not independently validate their semantics. The reviewer knew the outcomes, and independent human agreement has not yet been measured. I therefore present this as an ongoing evaluation prototype with auditable evidence and an explicit validation agenda, rather than a fully validated process metric.
