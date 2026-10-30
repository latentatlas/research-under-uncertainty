# Direct source inspection

These 83 files are byte-identical copies selected from the exact submitted supplement's 1,424-file expansion. The selection contains the main manuscript sources and license notices, claim map, component READMEs, and all distributed Python files. `SUBMISSION.json` maps every copy to its original path and SHA256. Run `python3.12 -I -B -S verify_submission.py` from the repository root to verify the mapping.

This view is for browsing. Restore the complete data tree before running component checkers; their relative data paths refer to that full tree. The repository README gives the extraction command. Source files that were distributed for inspection, including privileged case preparation and archived numerical implementations, retain that role. Standard verification never executes participant-generated code or a live model collector.

Start with [claim map](paper-package/CLAIM-MAP.json), [main manuscript](paper-package/paper/body.tex), [appendix](paper-package/paper/appendix.tex), [13-check orchestrator](paper-package/verify_all.py), [scalar interpretation checks](paper-package/artifact/interpretation_checks.py), [follow-up source check](paper-package/artifact/followup/source_check.py), and [prospective reader](prospective/verify_prospective.py). Paths inside these unchanged files refer to the extracted component roots.
