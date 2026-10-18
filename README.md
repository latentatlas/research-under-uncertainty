# Research Under Uncertainty

How well can an AI agent choose experiments, revise an explanation and act successfully in an unfamiliar system? This project develops tasks and measurements for studying those abilities together, while keeping task completion separate from evidence that a mechanism has been learned.

The current development question is whether matched task levels produce a repeatable change in difficulty under the same information, tools and resource limits. In the first completed session of a two-session calibration, GPT-6 Astra at max reasoning succeeded in 4 of 4 episodes at Level A, 2 of 4 at Level B and 0 of 4 at Level C. These are encouraging development observations from four fixed starting conditions. The full calibration and validation on fresh conditions are separate steps.

Research direction is by [LatentAtlas](https://github.com/latentatlas), with substantial assistance from Codex in implementation, analysis and writing. [Contribution details](docs/CONTRIBUTIONS.md).

## Read the study

- [Research question and design choices](docs/PROJECT-BRIEF.md)
- [Task, scoring and resource controls](docs/METHODS.md)
- [Results and their denominators](docs/RESULTS.md)
- [What can be checked from this edition](docs/EVIDENCE-AND-LIMITS.md)
- [Publication history and confidentiality](docs/PUBLICATION-HISTORY.md)

## Interim calibration results

The same four starting conditions were used at every level. Each condition received one attempt at each level in this session.

| Candidate level | Planned episodes | Success | Scientific failure | Unscored |
| --- | ---: | ---: | ---: | ---: |
| A | 4 | 4 | 0 | 0 |
| B | 4 | 2 | 2 | 0 |
| C | 4 | 0 | 4 | 0 |

The labels identify development configurations; their hidden parameters are withheld. The table describes the first session, closed on 17 October 2026. It is not the final result of the planned 24-episode collection. The second session is outside this snapshot. All 12 outcomes from the first session are included, including failures and episodes with technical retransmissions.

[Structured aggregate counts](data/calibration-summary.json) accompany the table. [Methods](docs/METHODS.md) explain the unchanged task budgets and the distinction between scientific failure and an unscored termination. [Results](docs/RESULTS.md) also preserve the outcome summary of the earlier September pilot, which used a different task and scoring unit.

## Scope of this edition

This edition contains a research account and aggregate results. Evaluation laws, private configurations, simulator code and reconstructive interaction records are not distributed. The public counts can be reconciled across the table and JSON file; regenerating the original trajectories and scores requires the protected research archive. No full replay or independent verification of the underlying outcomes is claimed for this edition.

An earlier distribution included evaluation internals and was withdrawn from public access. This revision changes what is distributed; it cannot undo previous exposure. [Publication history](docs/PUBLICATION-HISTORY.md) explains that limitation and the revised scope of the portfolio entry.

Edition prepared 18 October 2026. [Portfolio revision notes](RELEASE-NOTES.md). [License](LICENSE.txt).
