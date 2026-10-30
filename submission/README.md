# Anonymous supplementary material: v2.0.18

Read `paper/manuscript.pdf`. This single archive includes all main-paper and prospective-choice evidence, the manuscript sources, and the optional companion PDF. The main paper separates action correspondence, selector discrimination and later-choice prediction. The prospective joint outcomes are Astra 5/1/2/0 and Sol 2/1/1/4 (both correct / record only / no record only / neither).

For submission, the two files are the main PDF and this complete supplementary ZIP. The restored `paper-package/` is an internal component, not a separate complete supplement.

Version 2.0.18 adds a post hoc descriptive family breakdown: continuous / route accuracy with versus without the record is Astra 2/4 vs 3/4 and 4/4 vs 4/4; Sol 3/4 vs 2/4 and 0/4 vs 1/4. The original per-profile aggregate remains primary. Each family/profile has two purposeful histories and four linked targets, so these counts are not family-level causal estimates. The paper also gives all eight history/profile rows and the fixed source-to-target branch construction. The source reader checks all three added tables. Original preparation code and its generation record are supplied in `paper-package/artifact/prospective-design/` for inspection; the reader does not run the history generator. Privileged preparation is distinct from model behavior and from an informative-record positive control.

## Verify the evidence

Python 3.12 and the standard library are sufficient. From this directory:

```sh
python3.12 -I -B -S verify.py
```

Expected: `passed: true`, thirteen evidence checks all true, sixteen evaluated targets, and `temporary_evidence_removed: true`. No account, network connection or paid request is required. The command validates all stored and restored hashes, restores two components in a temporary directory, runs the source checks and existing numerical replays, then removes that temporary directory. It never executes archived participant programs or collector code.

For permanent direct access to every source file and manuscript source, choose a new output directory outside this archive:

```sh
python3.12 -I -B -S verify.py --extract-to ../ruu-evidence
```

This writes `../ruu-evidence/paper-package/` and `../ruu-evidence/prospective/`. Existing destinations are rejected. Read the restored main component's README for per-study checks, expected counts, numerical tolerances, source paths and licenses. The extraction command validates and restores evidence without executing its readers. Use `--archive-only` for a no-write storage-integrity check. All stored text is directly readable in `data/lines-*.json`; `data/files-*.json` maps original paths to line indices and exact SHA-256 hashes. PDF files are directly readable. Repeated text is stored once; all expanded files, including the original prospective manifest, are preserved byte-for-byte.

## Corruption controls

```sh
python3.12 -I -B -S archive_tests.py
```

This tests the storage representation and rejects corrupted hashes, unsafe paths, invalid references and conflicting destinations on temporary copies. The restored components additionally supply thirteen pilot-sensitivity and sixteen prospective corrupted-evidence controls, plus the follow-up interaction tests.

## Interpretation

Source recalculation and present-host numerical replay establish reproducibility of the supplied evidence, with the paper's stated conditional label premises. They do not attest historical provider execution or constitute independent laboratory replication. Four purposeful histories per profile, two dependent targets per history, different source/target output protocols and one generation per role delimit the prediction result. Numeric single-row tables and semantic information in their prose are different measurements. The original interrupted segment and its separately completed final block remain visible, including unknown usage. No new scientific data are collected by verification.

The companion study has a separate standalone dataset and is optional; none of the main-paper checks requires it. License notices are retained. This is an anonymous local submission artifact.
