# Reproducing this work sample

Use Python 3.10 or later. The programs use only the standard library. No dependency installation, API credentials, provider CLI or network access is needed to run the checks after obtaining the repository.

```bash
python3 -B replay.py
python3 -B replay.py --json
python3 -B -m unittest discover -s tests -v
```

Expected original outcomes, in order: **22/24, unscored, unscored, 24/24**. Interaction-sensitive targets for the two submitted runs: **0/2 and 2/2**. The output reports **1,236 numeric values**, **54 committed decisions** and **270 process cells**. Of the numeric values, 1,188 are observation readouts including the provided initial data, and 48 are submitted prediction targets. Repeated readouts within a sequence are not independent experimental replications.

## What is recomputed

For a sequence of inputs `(x, u, v)`, the compact evaluator uses an exact rational finite sum with half-retention weights. The local spatial response is a clipped ramp around the recorded center. The interaction is position-dependent and uses either the previous u with current v, or previous v with current u. The evaluator configuration is included explicitly as privileged replay information.

This is a separate arithmetic implementation from the original lab's state update. It checks observations to half of one unit in the last recorded decimal place, and uses the recorded 0.01 acceptance tolerance for targets. Only actual submitted predictions are graded. It also applies the four analyst-authored closure-rule adapters to the exact observation prefixes available at those decisions, yielding 5/206, 16/169, 0/125 and 0/688 contradictions.

The preserved ordinal scorer rechecks all evidence citations, anchor/score consistency and original profile aggregation. It consumes the existing interpretations; it does not generate new semantic judgments. [Evaluation method](EVALUATION.md).

## Inspecting a process example

```bash
python3 -B replay.py --episode w2-r2 --decision 5
python3 -B replay.py --episode w2-r2 --decision 6
```

These commands show the committed action and public record, the next recorded event and the next public record where available. They show observable public data, not private chain-of-thought. The full pre-action packets and unchanged rating files for all four runs are in [evidence](../evidence/).

## Source identity and transformations

[PROVENANCE.json](../data/PROVENANCE.json) records source paths relative to the original project, original file hashes, exported paths and the transformation used. Packet, review, profile, rubric, scoring and selected supplementary files are byte-preserved. `data/episodes.json` is a structured selection of scientific fields from lab records, original summaries and the declared claim adapters.

[MANIFEST.json](../data/MANIFEST.json) binds the shipped evidence bytes. Those hashes let a reviewer detect a change to this release's inputs. Hashes of unshipped source files document the author's lineage record; they do not independently prove the authenticity of an unavailable original. Raw carrier events, account configuration and the full working directory are not included.

The failure checks demonstrate rejection of changed numerical evidence even without a file-hash check, relabeling an absent submission as zero, a broken rating citation, and a missing evidence file. A failure is reported explicitly with a nonzero exit status.

## Scope of reproduction

This package reproduces arithmetic and specified structural checks of a recorded pilot. It does not rerun the live models, promise identical future trajectories, reproduce the entire research workspace or establish independent semantic validity. Another person's successful run of this program would be a useful portability result; it would not by itself validate the research construct or the process rubric.
