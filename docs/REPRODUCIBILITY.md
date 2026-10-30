# Reproduce the submitted evidence

This guide refers to TMLR submission 13906, v2.0.18, and the fixed `ruu-tmlr-v2.0.18` tag. The submission contains 25 physical files, restoring 949 main-component and 475 prospective-component files. CPython 3.12's standard library is sufficient for evidence verification. No provider, account, network or third-party Python package is used.

## Obtain the fixed version

```sh
git clone --branch ruu-tmlr-v2.0.18 https://github.com/latentatlas/research-under-uncertainty.git
cd research-under-uncertainty
python3.12 -I -B -S verify_submission.py
```

Expected: `passed: true`, `submitted_files: 25`, `expanded_files: 1424`, `browsing_copies: 83`. This command checks identities and restores content in memory; it does not run scientific readers.

Alternatively download the exact [supplement asset](https://github.com/latentatlas/research-under-uncertainty/releases/download/ruu-tmlr-v2.0.18/RUU-TMLR-v2.0.18-supplement.zip) into a directory outside the repository. Its SHA256 is `6fce1da5fa90a97e621d26dd6c053499855ad79e3c59bf1fe7a1cf512a9a6134`; it is 18,459,131 bytes. If saved one directory above the repository:

```sh
python3.12 -I -B -S verify_submission.py --zip ../RUU-TMLR-v2.0.18-supplement.zip
```

Expected: the same checks, plus `submitted_zip_checked: true`. The submitted PDF is 204,150 bytes with SHA256 `8043ec80b38a4aab1749a98027998066f37bbf3fa4e8270f92ac912f24c7e0e6`. File identities are also in [SUBMISSION.json](../SUBMISSION.json).

## Full and focused checks

From the repository root:

```sh
python3.12 -I -B -S submission/verify.py
python3.12 -I -B -S submission/archive_tests.py
python3.12 -I -B -S submission/verify.py --archive-only
```

The full reader reports `passed: true`, 13 `evidence_checks` all true, `evaluated_targets: 16`, `expanded_files: 1424`, and `temporary_evidence_removed: true`. It can take several minutes. The archive corruption suite reports 15 successful rejection/control checks. `--archive-only` checks all stored and restored hashes without running any evidence program. Details of public-run results are in [VERIFICATION.json](../VERIFICATION.json).

To inspect all original files and run individual checks, extract once to a new path outside the repository:

```sh
python3.12 -I -B -S submission/verify.py --extract-to ../ruu-evidence
cd ../ruu-evidence/paper-package
python3.12 -I -B -S verify_all.py --prospective-dir ../prospective
```

Extraction reports `extracted_files: 1424` and runs no evidence programs. Existing destinations are refused. Both sibling components are required for the complete main-paper verification; the main component alone is insufficient.

The [restored component guide](../browse/paper-package/README.md) lists focused commands. From the extracted `paper-package/`:

```sh
python3.12 -I -B -S verify_all.py --followup-only
python3.12 -I -B -S artifact/interpretation_checks.py --prospective-dir ../prospective
python3.12 -I -B -S artifact/pilot_sensitivity_tests.py
python3.12 -I -B -S artifact/followup/interaction_tests.py
```

From the sibling extracted `prospective/`:

```sh
python3.12 -I -B -S verify_prospective.py
python3.12 -I -B -S negative_controls.py
```

Never save logs, generated PDFs, caches or other outputs inside an exact-manifest component. Save them elsewhere. A nonzero exit or any `passed: false` means the relevant verification failed; do not substitute a different evidence revision to obtain a pass.

## Match an observation to its source

All paths below are relative to the complete extracted tree. The [claim map](../browse/paper-package/CLAIM-MAP.json) supplies the more detailed file bindings.

| Observation | Starting point | What the reader recomputes |
| --- | --- | --- |
| A2 agreement and A1 contrast | `paper-package/artifact/pilot_sensitivity.py`, `artifact/interpretation_checks.py` | Plan metrics, selector choices, conditional labels, and 15 A2 dominance comparisons |
| Follow-up denominators and records | `paper-package/artifact/followup/` | 48 assignments, 46 completed responses, row structure, rule/proposal/label correspondence |
| Visible follow-up interactions | `paper-package/artifact/followup/interaction_check.py` | 120 prompts, 118 terminal responses, 177 visible messages, 72 analysis pairs and source bindings |
| Prospective prediction | `prospective/verify_prospective.py`, `INDEX.json`, `REFERENCE.json` | 103 requests in two segments; source/prediction/target order, 16 targets, 32 predictions, 12 references and usage accounting |
| Paired correctness and reporting tables | `paper-package/artifact/interpretation_checks.py` | Astra 5/1/2/0 and Sol 2/1/1/4 paired cells, family/history breakdowns and protocol/row diagnostics |
| Original prospective case preparation | `paper-package/artifact/prospective-design/` | Inspect original construction source and generation record; standard verification does not execute them |

## Rebuild the manuscript

The submitted PDF is the reference file. The exact TeX sources, bibliography and style files are included under extracted `paper-package/paper/` and mirrored for browsing. To rebuild, copy that paper directory to a separate working directory, then use a LaTeX installation with `pdflatex` and `bibtex`:

```sh
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
bibtex manuscript
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
```

The verification record states whether a fresh typeset build was tested. PDF byte identity is required for the distributed submitted PDF, not for a new typeset build: TeX versions and PDF metadata can change regenerated bytes. The evidence checks do not require LaTeX.

## What rerunning establishes

The package supports exact file checking, recalculation of reported outcomes, and present-host replay of the specified disclosed numerical cases. It retains technical losses, the original interrupted prospective request and its unknown-usage reserve, and the separately completed final target block. Continuous P/L labels retain their stated numerical and historical-runtime premises.

The reader does not collect fresh model responses, recreate historical provider weights or hidden reasoning, execute participant programs, or establish independent laboratory replication. The prospective component reuses the collector's parser and scalar calculation; the paired-table check reads terminal decisions separately. Four purposeful histories per profile and two linked targets per history remain the sample structure. The optional companion PDF concerns a separate completed study; its full standalone archive and fresh live collections are outside this submitted package.
