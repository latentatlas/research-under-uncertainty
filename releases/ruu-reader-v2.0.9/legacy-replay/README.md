# Fixed local replay — v1.3

The original `w04replay` implementation and numeric inputs preserve the eight pilot grades and 91 planned component cells. The separate `transferreplay` module adds the 48 archived two-family action grades and exact frozen adapter eligibility. It never calls a model, executes recorded participant programs, refits candidates or adds experiments.

From the parent artifact directory with CPython 3.12 and its standard library:

```sh
python3.12 -I -B -S replay/replay.py verify
python3.12 -I -B -S replay/replay.py reproduce --output /tmp/fixed-history-review-output
```

The output directory must be new, outside the replay tree, with an existing parent. Expected `passed=true`; original six preserved/two lost and 90 computed/one unresolved component cells; prospective 42 preserved/six lost, 22/24 matching pairs, one supported trial and zero supported pairs. `TRANSFER-GRADES.json`, `TRANSFER-ADAPTER.json` and `TRANSFER-SUMMARY.json` keep the new study separate. Reference data are used only to compare results after computation. The five original scientific output files remain byte-identical to the prior replay on the preparation host.

`PROVENANCE.json` covers the original replay; `../transfer/SOURCE-BINDINGS.json` covers the new source/export transformations. Original frozen grader/adapter text is available in `../transfer/protocol/source/` for inspection. New numerical functions preserve their arithmetic; only relative imports and portable data paths replace operational lookup. The unused operational report function is omitted from the adapter module. The new entry point checks the exact archived adapter outcome, including unsupported pairs; it is not a generic future-study adapter service.

The audit hook rejects network access, child processes, writes to inputs and reads outside the replay/output/standard-library roots. It is not a malicious-code sandbox. The interpreter is trusted. Scientific replay has no external dependencies or data downloads. Windows support, cross-platform equality and independent laboratory replication are not claimed. Timing and memory observations are local computation metrics, not participant model cost.
