# Contributions and AI assistance

The project was initiated and directed by **LatentAtlas**, who set the research question and repeatedly challenged whether the tasks and evaluation matched it. The focus on unfamiliar systems, detailed process reading, fair treatment of alternative methods, source-linked claims and separation of scientific and operational outcomes came from that research direction.

Codex provided substantial assistance with literature review, technical design proposals, implementation, tests, experiment execution, calculations, analysis and writing. The process ratings in this snapshot were authored by the project assistant with knowledge of the outcomes. They are not independent human annotations. The model serving as an experimental participant is distinct from the assistant developing and analyzing the work.

The project's contribution statement concerns the decisions made and the resulting artifacts. It does not imply that every program was independently written by the applicant or that an AI-assisted codebase demonstrates unaided engineering proficiency.

## Research decisions illustrated by the work

- Questioning task validity despite high final scores led to renewed attention to starting information and the experiments a participant actually had to choose.
- Requiring detailed process evidence led to the preservation of pre-action contexts, public statements, observations and subsequent decisions.
- Challenging missing difficulty patterns kept calibrated and exponential difficulty as open questions.
- Requiring interpretable scores led to separate target groups, unscored protocol terminations and explicit aggregation sensitivities.

The original numerical outputs are preserved. Later diagnostics do not turn unsubmitted runs into successful submissions. The short work sample illustrates both an agent revising an explanation and limitations in the evaluation system itself.

## Technical material in this repository

The ordinal scorer and rubric are preserved from the project. The offline finite-sum replay and failure checks were written with Codex during packaging. Public scientific packets and ratings are copied from the recorded pilot; a separate allowlisted extraction supplies observations, target submissions, closure-claim adapters and original outcomes. See [provenance and reproduction](REPRODUCING.md).

Related research that informed the wider project includes [DiscoveryWorld](https://arxiv.org/abs/2406.06769), [BoxingGym](https://arxiv.org/abs/2501.01540) and [RE-Bench](https://arxiv.org/abs/2411.15114). These are references for context, not endorsements, integrations or a claim of priority over those projects. This repository distributes the project's compact replay and synthetic pilot records; it does not bundle their codebases.
