# Research Under Uncertainty

**What Decision Records Establish About Model Choices Under Uncertainty — v2.0.18**, submitted to TMLR on 30 October 2026, submission **13906**. [Submission record](https://openreview.net/forum?id=Lu6hxicGcr). The recorded status is submitted; an editorial decision is not claimed.

The study develops three practical evaluation checks: create cases where candidate rules can disagree, separate action agreement from task labels, and measure the added value of a decision record for predicting a later choice. It combines a worked counterexample, a 48-assignment follow-up and a prospective choice-prediction pilot.

## Read and inspect

- [Exact submitted paper](submission/paper/manuscript.pdf).
- [Exact submitted supplementary files](submission/README.md) and [downloadable supplementary ZIP](https://github.com/latentatlas/research-under-uncertainty/releases/download/ruu-tmlr-v2.0.18/RUU-TMLR-v2.0.18-supplement.zip).
- [Claim-to-source map](browse/paper-package/CLAIM-MAP.json), [manuscript source](browse/paper-package/paper/body.tex), and [appendix source](browse/paper-package/paper/appendix.tex).
- [Verification and reproduction guide](docs/REPRODUCIBILITY.md), including expected results and the limits of each command.
- [What changed from the previous Git release](docs/TMLR-ALIGNMENT.md) and [submission file identities](SUBMISSION.json).

`submission/` contains the same 25 files as the submitted ZIP, without edits. Its readable UTF-8 storage restores **1,424 original files**: 949 in `paper-package/` and 475 in `prospective/`. [browse/](browse/README.md) provides 83 byte-identical manuscript and checker files for direct inspection on GitHub. The complete executable reader, data, protocols and source records are restored from `submission/`.

## Run the checks

Requirements: **CPython 3.12 and its standard library**. No account, API key, package installation or network access is needed after download. From this repository's root:

```sh
python3.12 -I -B -S verify_submission.py
python3.12 -I -B -S submission/verify.py
python3.12 -I -B -S submission/archive_tests.py
```

The first checks the submitted file identities, all restored hashes and every browsing copy. The second runs **13 existing-evidence checks**, including the disclosed numerical cases; each must pass. The third runs **15 storage corruption controls**. A nonzero exit means verification failed. Keep any saved outputs outside the exact `submission/` directory.

To retain the full source tree for inspection, use a new destination outside this repository:

```sh
python3.12 -I -B -S submission/verify.py --extract-to ../ruu-evidence
```

The [reproduction guide](docs/REPRODUCIBILITY.md) explains source paths, focused checks, negative controls, and manuscript rebuilding. These commands recompute the distributed evidence and repeat specified numerical calculations on the current host. They add no model responses and do not execute archived participant programs or live collectors.

## Main observations

In the A2 example, the same plan dominates all five criteria, so agreement among the five selectors cannot identify a unique rule. A1 provides a distinguishing case. In the follow-up, 46 of 48 assigned trials completed; all 16 B records match the unforced proposal, with 14 single-row tables. All 15 completed C proposals already agree with the external selector, leaving corrective benefit on conflicting proposals unmeasured.

In the prospective pilot, Astra has 6/8 correct predictions with the record and 7/8 without; Sol has 3/8 and 3/8. Each profile has four purposefully selected histories and two linked targets per history. The original 15-target segment and the separately completed final Sol target remain separately documented. Seven of eight numeric tables contain one row; the treatment includes the accompanying prose. These observations concern choice prediction and retain the manuscript's sampling and protocol limits.

## Versions, provenance and licenses

Use the fixed [ruu-tmlr-v2.0.18 tag](https://github.com/latentatlas/research-under-uncertainty/tree/ruu-tmlr-v2.0.18) for this submission. The previous [v2.0.9 reader](https://github.com/latentatlas/research-under-uncertainty/tree/ruu-reader-v2.0.9) and [portfolio snapshot](https://github.com/latentatlas/research-under-uncertainty/tree/portfolio-v0.1) remain intact in their tags and Git history. GitHub's automatically generated source ZIP is a repository snapshot; the separately named supplement asset is the exact TMLR ZIP.

The [submission binding](SUBMISSION.json) records the PDF and ZIP SHA256 values and the author's byte comparison with downloads from OpenReview. The [public verification record](VERIFICATION.json) reports checks of this distribution. Neither record is a provider-signed receipt or an independent laboratory replication.

Research direction is by Huseyin Buldurgan, with substantial AI assistance in design discussion, implementation, analysis and writing. The submitted manuscript retains its anonymous-review text and disclosure unchanged. [Contribution record](docs/CONTRIBUTIONS.md). Original research code is MIT; original manuscript, research records and documentation retain CC BY 4.0, with the included third-party notices: [submission licenses](submission/LICENSES.md). Historical internal version headings in those notices do not indicate a different submitted PDF.

The older [project brief](docs/PROJECT-BRIEF.md), [results summary](docs/RESULTS.md) and [proposed next study](docs/NEXT-STUDY.md) are dated historical context. The proposed benchmark is separate from the completed studies in this submission. [Publication history](docs/PUBLICATION-HISTORY.md) · [Release notes](RELEASE-NOTES.md).
