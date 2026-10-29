# Research Under Uncertainty

How can we evaluate the evidence behind an AI research agent's next decision? This project studies experimental decisions, the records supplied to justify them, and the limits of what those records establish.

This release provides the current **decision-record study, v2.0.9**, with source tables and offline checking code. It is a research artifact; journal submission, acceptance and independent laboratory replication are not claimed. The proposed broader benchmark remains future work.

[Download the complete public package](https://github.com/latentatlas/research-under-uncertainty/releases/tag/ruu-reader-v2.0.9). The scientific reader is under `releases/ruu-reader-v2.0.9/`; the other files provide the overview and historical context.

## Start here

1. [Three-minute work sample: question, findings and limits](docs/WORK-SAMPLE.md).
2. [Current study and exact verification instructions](releases/ruu-reader-v2.0.9/README.md).
3. [Main paper](releases/ruu-reader-v2.0.9/paper/manuscript.pdf).
4. [Claim-to-source map](releases/ruu-reader-v2.0.9/CLAIM-MAP.json).
5. [Proposed next study, clearly separated from completed work](docs/NEXT-STUDY.md).

## Check the distributed evidence

With CPython 3.12 and its standard library, from the repository root:

```sh
cd releases/ruu-reader-v2.0.9
python3.12 -I -B -S verify_all.py --followup-only
python3.12 -I -B -S verify_all.py
```

The first command validates the exact tree, reconstructs the follow-up record checks and regenerates its descriptive tables. The second also repeats the older numerical work and the separate finite-class observation-selection calculation. It can take several minutes. Neither command needs an API key, account, paid inference or network access. Keep logs and generated files outside the exact reader directory.

These commands recalculate results from distributed inputs. They do not collect new model responses, reproduce a provider's historical model weights, execute participant-generated programs or establish independent experimental replication. Not every original model response or usage receipt is redistributed. The reader README states the remaining numerical and provenance limits.

## What the current study shows

The follow-up has 48 assigned trials: 46 completed and two technical losses retained in the accounting. In the required-record/model-proposal condition, each of two profiles has eight valid records matching the proposal. Both supported selection rules choose the same action in all sixteen records. Correspondence alone therefore does not establish that the record caused the proposal or faithfully describes internal reasoning.

All 15 completed external-selector proposals already agree with the selector. There is no observed opportunity in that condition to demonstrate the benefit of overriding a conflicting proposal. These are four purposeful historical contexts with repeats, not a population sample or a general model ranking. The main label concerns conditional continuation feasibility, not full task success.

## Earlier public snapshots

The [18 October summary](docs/PROJECT-BRIEF.md), [methods](docs/METHODS.md), [results](docs/RESULTS.md), [evidence boundaries](docs/EVIDENCE-AND-LIMITS.md) and [fresh-input preregistration](docs/FRESH12-PREREGISTRATION.md) remain historical documents. They describe different study stages and are not silently updated by the current reader release. In particular, the full September process-pilot evidence is not redistributed by this package. Do not sum different panels as interchangeable independent episodes.

Research direction is by Huseyin Buldurgan, with substantial AI assistance in design discussion, implementation, analysis and writing. [Existing contribution record](docs/CONTRIBUTIONS.md). The current paper contains its own AI-assistance disclosure.

[Publication scope and previous exposure](docs/PUBLICATION-HISTORY.md) · [Revision notes](RELEASE-NOTES.md) · [Repository license](LICENSE.txt) · [Reader-specific licenses](releases/ruu-reader-v2.0.9/LICENSES.md). The reader's included third-party license notices remain applicable.
