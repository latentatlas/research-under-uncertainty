# Git and TMLR alignment — 30 October 2026

The public `main` branch was still at v2.0.9 (`1a93e769aebab92e56d108d50433e9d4478d7823`) when TMLR submission 13906 contained v2.0.18. This release aligns the current repository with the submitted material.

| Area | Previous public reader | This release |
| --- | --- | --- |
| Paper | v2.0.9 | Exact submitted v2.0.18 PDF and sources |
| Prospective pilot | Absent | Full 16-target panel, original and completion segments, controls and unresolved-use accounting |
| Follow-up evidence access | Original minimal final-response package | Expanded visible interaction evidence and source bindings |
| Interpretation | Earlier presentation | A2 dominance mechanism, paired prediction outcomes, numeric-table/prose distinction, protocol difference, and family/history breakdowns |
| Storage and entry point | 299-file reader, `verify_all.py` | Exact 25-file supplement, restoring 1,424 files; `submission/verify.py` runs 13 checks |
| Direct browsing | Earlier source files | 83 exact submitted manuscript/checker copies, checked against their restored originals |
| Submission identity | No submitted-paper binding | OpenReview record, submitted PDF/ZIP hashes, per-file and expanded-component bindings |
| Separate acquisition companion | Included standalone acquisition evidence | Submitted optional PDF remains; prior full companion evidence stays in the preserved v2.0.9 tag |

Comparing the old 299-file reader with the restored 949-file main component gives 232 unchanged files, 15 changed files, 702 added files and 52 files absent from the new main component. The 52 are the separate acquisition-companion evidence subtree, not missing main-paper observations. The additional prospective component has 475 files. Physical file counts across the compressed and expanded representations are different units.

The exact submitted tree is under `submission/`. Browsing copies and repository guides are supplemental navigation; they do not modify the submitted evidence. Older license and prospective-component version headings are preserved because those files are original component notices, not a claim that the main paper is an older revision.

The prior [v2.0.9 tag](https://github.com/latentatlas/research-under-uncertainty/tree/ruu-reader-v2.0.9) and release asset remain available. The old reader directory is retired from current `main`, while its complete contents and commit history remain accessible at that fixed tag. No previous scientific file is rewritten in place.

This update changes distribution and access. It adds no model trial, independent replication, broader generalization or editorial acceptance. [Verification guide](REPRODUCIBILITY.md) · [Machine-readable submission binding](../SUBMISSION.json).
