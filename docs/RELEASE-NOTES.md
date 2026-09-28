# Research work sample — portfolio-v0.1

A research work sample from an ongoing project on how AI agents investigate unfamiliar systems.

This work sample connects an agent's experimental choices, observed evidence and explanation revisions to final prediction accuracy, while keeping protocol outcomes visible. It demonstrates an inspectable pilot and reproducible evidence checks; the four-run study does not establish a general model ranking or a calibrated difficulty curve.

This release includes:

- An English project overview, case study, explicit contribution statement and evaluation-method explanation.
- All four outcomes from the 28 September pilot: 22/24, two runs terminated by protocol (not scored), and 24/24.
- All 54 public decision packets and 270 source-linked experimental process-rating cells.
- A standard-library offline replay covering 1,236 numerical values: it independently recomputes 1,188 recorded observation readouts from their input histories and the reference values for 48 submitted prediction targets, reproducing the original acceptance decisions. File hashes, evidence citations and frozen rating aggregation are checked separately.
- Four failure checks for changed measurements, fabricated scores for unsubmitted runs, broken citations and missing evidence.

The local detached-directory check passed on Python 3.12.14. GitHub Actions passed on Python 3.10 and 3.12 for commit `f07f4bc22ec4b350337825c750d7f58d1742f85a`.

**Which pilot is included?** This release contains the complete four-run block on two development worlds, each run twice with GPT-5.6 Sol/high at fixed N8 settings. Both completed submissions came from world 2; both protocol terminations came from world 1. The earlier **24/24 at two components and 13/24 at six components** belong to the separate chain-system pilot of 23-24 September. That earlier task uses a different environment and is outside this release's four-run collection; its results remain part of the research history. These are different pilot scopes, not a before-and-after performance comparison. [Run identities and scope](https://github.com/latentatlas/research-under-uncertainty/blob/main/docs/RESULTS-SCOPE.md).

The five-dimension process ratings are attributed, outcome-aware assistant interpretations. The replay verifies their evidence references and aggregation; the numerical findings can be recomputed directly. This release provides an offline analysis of recorded runs.

Research direction: LatentAtlas. Substantial Codex assistance in technical design, implementation, analysis and writing.

Documentation clarification: 28 September 2026. The `portfolio-v0.1` evidence tag, recorded outcomes and rating files are unchanged.
