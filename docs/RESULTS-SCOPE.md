# Pilot results and release scope

The application CV and `portfolio-v0.1` release refer to the **28 September 2026 four-run pilot**. This collection contains two development worlds with two fresh runs per world, using GPT-5.6 Sol/high at fixed N8 task settings. All four registered outcomes are retained.

| Full run identity | World and repeat | Recorded outcome |
|---|---|---|
| `sol-high-cdr-w2-r1` | World 2, repeat 1 | 22/24 accepted prediction targets |
| `sol-high-cdr-w1-r1` | World 1, repeat 1 | Terminated by protocol (not scored) |
| `sol-high-cdr-w1-r2` | World 1, repeat 2 | Terminated by protocol (not scored) |
| `sol-high-cdr-w2-r2` | World 2, repeat 2 | 24/24 accepted prediction targets |

The two completed runs therefore compare repeated investigations of the same world. The two unscored runs belong to the other world. An absent submission remains unscored; it is not converted into zero or an inferred completed score. The shipped [episode data](../data/episodes.json), [provenance record](../data/PROVENANCE.json) and [offline replay](../replay.py) identify and check this collection.

## The earlier chain-system pilot

The older CV described a different pilot conducted on 23-24 September 2026, also using Sol/high:

| Full run identity | Chain components | Recorded outcome |
|---|---:|---|
| `sol-high-chain-n2-s503-r1` | 2 | 24/24 accepted prediction targets |
| `sol-high-chain-n6-s503-r1` | 6 | 13/24 accepted prediction targets |

Those results describe an earlier chain-system environment. This release was assembled as a self-contained replay of the later four-run collection, whose mechanism and task configuration differ. The earlier runs are outside that collection and remain part of the project's development history. Their scores were not replaced, rescored or pooled with the later pilot. The two sets do not form a before-and-after improvement estimate or one difficulty curve.

The earlier counts above were checked against the original run summaries during this documentation update. Their source identities are retained here as lineage references; those original summaries are not part of the public replay inputs:

- `outputs/research-chain-live-01/episodes/sol-high-chain-n2-s503-r1/summary.json` — SHA-256 `bdb2b0d1b0cd06a98d6964388f92ba64c946027038b6166c5678b6e6e48d01a4`.
- `outputs/research-chain-live-01/episodes/sol-high-chain-n6-s503-r1/summary.json` — SHA-256 `4fa1010a9d564631a02f8d504b88356f1861994405d0208a2caff5d540dc2cdd`.

## What the 1,236 numerical checks mean

The replay independently recomputes **1,188 recorded observation readouts**, including provided initial data, from the recorded input histories. It also recomputes the reference values for **48 prediction targets** across the two submitted runs and applies the recorded acceptance tolerance to reproduce 22/24 and 24/24. This is a count of numerical values checked, with multiple readouts possible within one experiment. File hashes, evidence citations and the original process-rating aggregation are separate checks. [Method and tolerances](REPRODUCING.md).

Documentation clarified on 28 September 2026. The evidence tag and original scientific results are unchanged.
