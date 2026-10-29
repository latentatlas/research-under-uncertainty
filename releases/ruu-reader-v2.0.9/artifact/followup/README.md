# Closed three-condition follow-up: source-derived reader

This separate 48-assignment pilot has 46 completed trials and two preserved technical losses. Astra/max/Fast and Sol/max/Fast are separate strata. Four historical contexts and their repeats are purposeful, not a population sample.

From the package root run `python3.12 -I -B -S verify_all.py --followup-only`. No model account, network, participant program, physics replay or new observation is used. `--scalar-only` remains a compatibility alias for the same strengthened checks.

## Available inputs and derivation

`finals/` contains all 46 exact minimal final wire JSON responses. Thirty-one contain `candidate_losses` numeric tables and their declared `rule`; the other fifteen are action-only A finals. The decimal lexemes are preserved byte-for-byte. There is no completed final for the two technical positions 13/14. `final-index.json` maps each file to its original trial, response hash and inner-final hash. `allocation.json` is the original allocation. `protocol/` contains byte-identical common and A/B/C instructions and the common transport schema; these were identical across all three execution segments. Analysis programs, analysis outputs and intermediate prompts are not distributed here.

`source_check.py` independently implements the declared numeric contract using exact decimal rationals. It derives schema/identity/range validity, the declared-rule action, both supported rule actions, single-row/duplicate/distinct-row diagnostics, and proposal/execution correspondence from the supplied final inputs. Ties choose the first menu index and repeated rows retain multiplicity. Derived decisions and commit hashes must equal the preserved projection; precomputed `record_valid` or `rule_actions` fields are reconciliation targets, not calculation inputs. All 46 completed action indices are bound to their existing menu in `artifact/data/crossing.json`, and all 46 labels are re-read at those indices. No labels changed; this checks the stored census link, not its physics anew.

`check.py` then recounts model/arm statuses, correspondence, triplets and paired differences. `reference.json` is an aggregate reconciliation target, not independent evidence. `tests.py` checks malformed inputs, exact-number/tie/multiplicity behavior, changed source-derived claims and broken identity/label links; run it with `python3.12 -I -B -S artifact/followup/tests.py`.

## Field populations

`partial_triplets` is retained from the archive and aliases `planned_partial_triplets`: it counts original planned blocks missing an A/B/C assignment. Its value 0 is unrelated to scientific completion. Astra has 7 fully completed, 1 scientifically incomplete and 1 technical-loss-containing triplet; Sol has 8, 0 and 0 respectively. Two technical losses in the same block count as one affected triplet.

`cache_split_unknown_requests` covers **only requests with known token usage**. Its denominator `cache_split_assessed_requests` is 58 for Astra and 60 for Sol. The two unknown-usage Astra requests appear separately in `usage_unknown_requests_excluded_from_cache_split`. The zero cache-split-unknown count does not mean zero cached input or no unknown usage. Both unknown requests retain their complete input/output and credit-equivalent reserves. Cached input is a subset of input and reasoning output a subset of output. See `SCHEMA.json` for machine-readable definitions; receipt totals remain archived arithmetic, not independently attested billing.

## Interpretation limits

A permits an optional record and executes the proposal; B requires a valid record and executes the proposal; C executes the required record's declared selector. B correspondence is observed, C execution agreement imposed. All 15 completed C proposals already match, so no correction benefit for a conflicting proposal is measured. C minus B is the total disclosed-regime contrast, not a fixed-record mechanical effect. Empty record denominators are undefined. The records are uncalibrated forecasts, not verified hypotheses or internal reasoning.

P is conditional continuation feasibility, not full task success. Existing bound menu labels retain their numerical/runtime premises. This is not a new live crossing, physics experiment, independent laboratory replication, provider identity attestation or permanent 429 resolution. Historical source hashes bind the cited bytes but do not independently authenticate execution.
