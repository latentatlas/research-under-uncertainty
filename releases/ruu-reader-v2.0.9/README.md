# Decision-record crossings: TMLR submission candidate v2.0.9

Start with `paper/manuscript.pdf`. The separate `companion/manuscript.pdf` is supporting material reporting a completed finite-class observation-selection study. Its 5,000 paired draws are not additional live LLM trials or crossing observations. This is a locally prepared anonymous review package, not a submitted or accepted paper.

## Revision focus: interpretation, observed transitions and reader commands

This revision makes the empirical record findings primary and the full-scan identity a supporting control. It explains the proposal's origin in our own pilot, the concrete ambiguity a researcher must resolve, and the broader experiment-selection and held-out prediction questions still untested. The main paper adds separate family outcomes, directional paired transitions, two action-changing/label-preserving examples, and a history-level appendix. All are derived from the unchanged original allocation, final responses and bound label census by `artifact/followup/breakdown.py`. The reader also verifies the generated LaTeX tables. This adds no scientific trial, physical grade or live counterfactual.

Behavior-linked explanation evaluation and BoxingGym are compared by target and access. The companion remains optional and byte-identical. Continuous-label premises, older interface confounds, absent C correction opportunities and the limits of correspondence remain explicit. PDF commands use literal verbatim options and are tested after extraction in the local revision record. This package has not been submitted.

## Source tables and complete follow-up identity checks

The main paper now includes the closed 48-assignment follow-up: 46 completed trials, two preserved technical losses, no active/unstarted or protocol-lost assignments. This is distinct from the older 48-trial transfer panel. Astra/max/Fast and Sol/max/Fast remain separate strata, with eight planned A/B/C triplets each. A is optional record/model proposal; B required record/model proposal; C required record/external selector. Each profile's B arm has eight valid proposal-matching records, all invariant in action under the two supported rules. The paired P changes have different signs across profiles. P is conditional continuation feasibility, not measured full task success. Four purposeful historical contexts and repeats do not support a population effect or model ranking.

Run the source-derived follow-up check, without redoing the older numerical computations:

```sh
python3.12 -I -B -S verify_all.py --followup-only
```

This command verifies the exact package tree and reconstructs decisions from 46 exact minimal final responses, including 31 numeric tables with declared rules. It validates record schema, recomputes both rule choices and row diagnostics, checks proposal/execution correspondence, binds action indices to menus and re-reads all 46 labels from the existing census. Common/A/B/C instructions, wire schema and original allocation are included. This was tested from a fresh extraction. It does not regenerate responses, execute participant programs, attest a provider profile or regrade physics. `artifact/followup/SCHEMA.json` distinguishes planned partial triplets from scientific incompleteness and known-usage cache splits from unknown usage. Older scientific inputs and the companion remain unchanged; their prior numerical validation is carried forward by byte equality.

## Reproduce from the distributed inputs

Use CPython 3.12 and its standard library, from a fresh extraction of the bundle:

```sh
python3.12 -I -B -S verify_all.py
```

The full command below adds the older numerical work to the source-derived follow-up reader. It checks the exact manifest, record comparisons, numerical constants, all 80 request hashes, per-trial analysis-error accounting, twelve pilot plans and five selector completions, all 32 menu labels, the full existing 5,000-draw acquisition sample, and the pilot/transfer numerical replay. The complete candidate scans can take several minutes; a final JSON result follows the per-check progress. No account, API, network, external dataset, new randomness or participant-generated program execution is needed. Numerical replay outputs are created in a temporary directory outside the bundle and removed afterward. Preserve the bundle unchanged; compilation and inspection output belong outside it.

Individual checks:

```sh
python3.12 -I -B -S artifact/check.py
python3.12 -I -B -S artifact/numeric_constants.py
python3.12 -I -B -S artifact/protocol/check.py
python3.12 -I -B -S artifact/interface_audit.py
python3.12 -I -B -S artifact/pilot_sensitivity.py
python3.12 -I -B -S artifact/menu_replay.py
python3.12 -I -B -S artifact/acquisition/replay.py
python3.12 -I -B -S legacy-replay/replay.py reproduce --output /tmp/new-decision-record-replay
```

The last command's output directory must not exist and must have an existing parent. Its historical README uses the old `replay/` directory name; use the paths above. The pilot/transfer replay's audit hook is defense in depth for trusted code, not an OS sandbox. The other checkers execute reviewed local computation without claiming adversarial-code isolation.

Expected results: eight eligible mandatory pairs; 32/32 observed cells and 29/32 weak-family cells structurally recoverable; full per-record scan recovers 32/32 and leaves zero additional cells. All 32 menu labels match. Acquisition cells are n11=282, n10=90, n01=1, n00=4627; all 655 issued certificates agree with regenerated targets; difference 0.0178 and interval [0.012284958848050642, 0.022904001234075738]. Pilot replay gives 6 P/2 L, 90 computed component cells and one unresolved; transfer gives 42 P/6 L, one eligible record and zero eligible pairs.

## Raw acquisition evidence and identities

`artifact/acquisition/` contains the structural catalog generator, original sampling algorithm, original catalogs and exclusions, original entropy seed and rejection receipts, ordered draw, frozen plan, commitments, event order and 5,000 original scientific records. The seed is a disclosed synthetic-study reproduction input, not a credential. Hypotheses cover systems with at most three states. Sampled worlds have exactly three minimal reachable states, excluding development classes:

11,500 total behaviors = 4 one-state + 144 two-state + 11,352 three-state; remove the 148 lower-state behaviors and two distinct eligible behaviors among seven prior fixtures to obtain 11,350; remove 1,499 first-development classes and 1,479 additional second-development classes to obtain 8,372. Crossing with 256 input histories yields 2,143,232 sampling units. The original 5,000 draws contain 4,993 distinct pairs and 3,791 distinct classes, with six rejection-mapping events and seven retained duplicate-pair excess draws.

`replay.py` reconstructs and checks that complete ordered chain, including the full first development manifest recovered from indices and catalog tables. It regenerates every eight-step history, performs the unchanged candidate computation and selector independently per arm, regenerates both query responses, fixes predictions before calculating targets, and compares every scientific result field and work counter. It then recomputes aggregate counts and the unchanged primary interval. A separate post hoc accumulator reuses the reconstructed candidate supports and original world responses: fixed q1 yields 219 certificates, fixed q0 283, selected policy 372, and a fair independent random-query policy has expectation 251. This is not an observed randomized run or a new confirmatory sample; historical work counters and primary statistics are unchanged. Source hashes are checked against reconstructed original JSON bytes; JSON layout normalization is documented in `SOURCE-BINDINGS.json`.

The records use transparent JSON columns plus a plain string dictionary to avoid repeated field names/hashes. These are lossless representations, not missing fields: all 5,000 original canonical record bytes reproduce their unchanged commitment hashes. Inspect one original record with:

```sh
python3.12 -I -B -S artifact/acquisition/replay.py --show-record t0001
```

Historical PIDs and timings remain only to verify original committed bytes; they are not regenerated timing or process-attestation claims. Inspection-only `historical-code/*.py.txt` includes the frozen collector, environment, worker, isolation controls and validation sources. The reader command imports only the pure candidate computation/selector and performs a transparent in-process reconstruction; it does not relaunch that historical collector. Local dates, hashes and the recorded commitment-before-truth order are not independently timestamped public preregistration or proof of historical execution. Independent laboratory/cross-platform replication remains unestablished.

## Main-panel requests and labels

`artifact/protocol/` includes both complete condition instructions, shared schema, four packets and all 80 exact request payloads. A renderer reconstructs the full prompts, including each trial's accumulated analysis records, and verifies both prompt and original payload hashes. To inspect a prompt:

```sh
python3.12 -I -B -S artifact/protocol/check.py --show-call 1
```

The historical collection entry point and helper code are inspection-only. One host-specific workspace prefix in the isolated-computation helper is explicitly anonymized; its original and distributed hashes and transformation are recorded. Original model responses/usage receipts are not all redistributed. Profile names are configuration labels, not independent provider-weight attestation. Any participant analysis program text is data and is never executed by these checks.

`artifact/menu_replay.py` binds each public probe to the corresponding original transfer history, menu and numerical evaluator, then regenerates 26 continuous and six route action labels. Continuous P uses a continuation witness; continuous L retains the manuscript's open uniform-library-accuracy and historical-runtime premises. Route labels use a finite integer recurrence. U stays unresolved. Present-host equality does not retrospectively discharge the continuous premises.

## Scope, interpretation and provenance

The older 32-trial panel separates optional record absence (15/16), valid optional correspondence (1/16), and mandatory external execution (16/16 by construction). Those counts do not describe the new follow-up, whose B correspondence is observed without imposed action selection. A worked same-record contrast produces action 7/L under uniform mean and action 12/P under worst case, without a partner record; these are bound menu evaluations, not new live decisions. Unchanged pilot selector sensitivity remains conditional on the analyst's completion.

The companion establishes a positive difference against the frozen fixed q0 policy in the stated finite frame. It does not claim optimality against q1/randomized alternatives, a gain of at least two percentage points, universal coverage, live LLM selection benefit, or cross-contract generalization. Earlier failed development criteria remain reported. Main-paper Appendix H provides the historical study inventory, including the excluded unfinished collection and technical null.

`CLAIM-MAP.json` maps claims to distributed checks. `artifact/PROVENANCE.json` retains historical original-source references and projection rules plus this revision's transformations; original relative paths are provenance, not claims that every internal file is distributed. Duplicate pilot reference bytes now occur once at `legacy-replay/data/references.json`. The older legacy replay and its own manifest are preserved byte-for-byte. `RELATED-WORK-SCOPE.md` states which primary sources were inspected and the limits of comparison.

LaTeX sources and the TMLR style files accompany both PDFs. Tectonic can compile `manuscript.tex` inside each paper directory with an output directory outside the bundle; compilation requires a TeX cache/distribution, while scientific checks require only the standard library. The default bibliography spacing is retained. Both PDFs contain the same AI-assistance disclosure in design, implementation, analysis, literature review, drafting and revision.

Mechanism disclosure is authorized for this current study and reviewed derivative materials only. No future benchmark, unrelated study, personal account information, credential, Git history or provider authentication is included. The manifest rejects missing, changed and unlisted files, including `.DS_Store`; do not relax it to overlook a mismatch. Hash equality establishes internal identity relative to this supplied package, not historical authenticity. The author must review the scientific argument and submission declarations before an external submission; this local package does not certify authorship, novelty, acceptance or external-form eligibility.

## Interface audit and what remains unknown

`artifact/interface_audit.py` emits all 32 common-menu trial rows, checks each request's cumulative analysis prefix and remaining-slot field, and reconciles the final attempt count. The 48 analyses comprise 41 successes and seven errors in seven trials: five dictionary-attribute errors and two unavailable-next errors. Five affected trials are optional and two mandatory. Each consumed one of three analysis slots on an error and two successfully. The sole rule-sensitive mandatory record is affected. In the separate transfer panel, 24 route trials made no analysis attempt; 24 continuous trials made 72 attempts (67 successful, five errors). Completed trials and zero technical missingness do not mean error-free analyses.

The archived COMMON instructions, runtime sources and submitted records remain byte-identical. This revision does not correct historical prompts, execute historical submitted programs, exclude affected trials, or infer that errors had no effect. Their causal effects on decisions and record structure require a separate prospective comparison.

`artifact/pilot_sensitivity.py` recomputes twelve fixed single-candidate plans and all five metrics, then selects each completion and checks native-action compatibility. It links resulting indices to archived grades; it does not regrade those sensitivity actions. Present-host plan recomputation and historical label provenance are distinct. Continuous labels retain the disclosed numerical/runtime conditions; `uniform_library_proof=false` and `historical_runtime_attestation=false` remain open.

The immutable `legacy-replay/README.md` uses its original `replay/` path. Use the top-level commands above in this bundle; do not interpret the archival path as a missing dependency. The legacy tree's own manifest remains unchanged. License details, including the separate LPPL notice in the bibliography style, are in `LICENSES.md`.
