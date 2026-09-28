# Investigating How AI Agents Research Under Uncertainty

An ongoing evaluation project connecting **experimental choices, observed evidence, explicit claims and final predictions**. Research direction by [LatentAtlas](https://github.com/latentatlas), with substantial Codex assistance in design, implementation, analysis and writing.

The motivating question is how an agent turns knowledge into useful investigation when the mechanism and the next experiment are not given. Early high scores led us to question task design and measurement, and to make the recorded research process inspectable alongside the outcome.

This release is a **research work sample and offline evidence replay** connecting experimental choices, observed evidence and explanation revisions to final prediction accuracy. It contains all four planned outcomes, 54 public decision packets, the experimental process rubric, source-linked ratings and a small Python verifier. A reviewer can follow the recorded investigation and recompute its numerical findings.

## Start here

- [Project overview](docs/PROJECT-BRIEF.md): the question, research decisions and current scope.
- [Case study](docs/CASE-STUDY.md): matched histories, an explanation revision and two different kinds of incomplete investigation.
- [How process scoring actually works](docs/EVALUATION.md): deterministic checks, authored judgments and the boundary between them.
- [Contributions and AI assistance](docs/CONTRIBUTIONS.md).
- [Reproduction and evidence provenance](docs/REPRODUCING.md).
- [Which pilot these results describe](docs/RESULTS-SCOPE.md): the current four-run collection and the earlier chain-system pilot.

## A concrete result

In the **28 September 2026 pilot**, two development worlds were each run twice with GPT-5.6 Sol/high and fixed N8 task settings. Every registered outcome is shown:

| Run | Original outcome | Accepted targets | Interaction-sensitive targets | Measurements contradicting the stated rule at closure |
|---|---|---|---|---|
| w2-r1 | Completed | 22/24 | 0/2 | 5 of 206 |
| w1-r1 | Submission protocol error | Unscored | Unscored | 16 of 169 |
| w1-r2 | Submission protocol error | Unscored | Unscored | 0 of 125 |
| w2-r2 | Completed | 24/24 | 2/2 | 0 of 688 |

The earlier 24/24 (two components) and 13/24 (six components) results belong to a separate chain-system pilot of 23-24 September, outside this four-run collection. [Pilot scopes and full run identities](docs/RESULTS-SCOPE.md).

The zero in w1-r2 means no contradiction was exposed by its measurements; the chosen experiments did not distinguish the missing interaction. It does not establish a complete explanation.

In w2-r2, the agent designed two histories with the same first readout, **1.000000**. Under the same next input their readouts became **0.900000** and **0.936000**. It investigated the difference, revised its rule to include a temporal interaction, and checked new measurements. The final predictions scored 24/24. The [case study](docs/CASE-STUDY.md) relates the actual evidence to the subsequent decisions, including earlier overstatements and later interface problems.

## Run the offline checks

Python 3.10+; standard library only. No API key, network connection or model call is required.

```bash
git clone https://github.com/latentatlas/research-under-uncertainty.git
cd research-under-uncertainty
python3 -B replay.py
python3 -B -m unittest discover -s tests -v
```

The replay covers **1,236 numerical values**: it independently recomputes **1,188 recorded observation readouts** from their input histories and the reference values for **48 submitted prediction targets**, reproducing the original acceptance decisions. Separate checks verify file hashes, evidence citations and the frozen aggregation of **270 process-rating cells**. The two absent submissions remain unscored. Process ratings remain attributed interpretations; their numerical aggregation and evidence references are reproducible.

Inspect the matched-history decision and the next public record:

```bash
python3 -B replay.py --episode w2-r2 --decision 5
```

The full JSON report is available with `python3 -B replay.py --json`.

## What this release establishes

The work sample demonstrates how to connect experiment selection, evidence handling and explanation revision to final predictions, with checks that run outside the original working environment. The scope is a descriptive comparison of four recorded runs; it does not establish a general model ranking or calibrated difficulty curve. [Evaluation methods](docs/EVALUATION.md) and [study scope and next experiments](docs/LIMITATIONS.md) give the detailed treatment of process judgments and future validation.

Snapshot: **28 September 2026** · Release: **portfolio-v0.1** · [MIT license](LICENSE)
