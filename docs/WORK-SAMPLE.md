# Work sample: inspect the claim, then run the check

## The question

When an agent's submitted decision record agrees with its proposed action, what has actually been established? Record availability, agreement with an action, sensitivity to the selection rule and task outcomes are different measurements.

## A bounded empirical example

The current follow-up assigns 48 trials across two profiles and three conditions. There are 46 completed responses and two technical losses. In condition B, which requires a record but leaves the proposal to the model, each profile supplies eight valid proposal-matching records. Both supported rules select the same action in all of those records. Thus agreement in this setting does not distinguish the rules or establish a causal account of the proposal.

Two records in condition C change the selected action when the supported rule changes, but keep their existing task label: one P-to-P, one L-to-L. All 15 completed C proposals already match the external selector, so a corrective benefit from overriding a conflicting proposal was not tested. P is conditional continuation feasibility, with the documented premises, rather than full task success.

## Follow the evidence

| Inspect | File | What can be checked |
| --- | --- | --- |
| Assigned and completed denominators | [allocation](../releases/ruu-reader-v2.0.9/artifact/followup/allocation.json), [trials](../releases/ruu-reader-v2.0.9/artifact/followup/trials.json), [accounting](../releases/ruu-reader-v2.0.9/artifact/followup/accounting.json) | Planned conditions, completion and retained technical losses |
| Original minimal finals | [final index](../releases/ruu-reader-v2.0.9/artifact/followup/final-index.json), [schema](../releases/ruu-reader-v2.0.9/artifact/followup/SCHEMA.json) | 46 final-response bindings, including 31 numeric record tables |
| Rules and correspondence | [source checker](../releases/ruu-reader-v2.0.9/artifact/followup/source_check.py) | Recompute row diagnostics and both supported rule choices |
| Family and directional results | [breakdown](../releases/ruu-reader-v2.0.9/artifact/followup/breakdown.json), [recomputation](../releases/ruu-reader-v2.0.9/artifact/followup/breakdown.py) | Descriptive results and generated paper tables |
| Scope and interpretation | [claim map](../releases/ruu-reader-v2.0.9/CLAIM-MAP.json), [paper](../releases/ruu-reader-v2.0.9/paper/manuscript.pdf) | Which source supports which claim, and which inference remains open |

Run the two commands in the [repository README](../README.md). The short command needs no model access and does not rerun the older physical calculations. The full command adds those calculations. Both preserve the original sample; neither is a new trial collection.

## Why this informs the next study

The work supports the ability to construct a bounded measurement, preserve failures, expose source evidence and distinguish supported from unsupported interpretations. It does not establish general diagnostic accuracy, prospective prediction of failures, improved intervention decisions or adoption by another team. Those are questions for the [proposed next benchmark](NEXT-STUDY.md).

The separate [finite-class companion](../releases/ruu-reader-v2.0.9/companion/manuscript.pdf) is optional further reading. Its 5,000 draws are a different study unit and are not 5,000 live agent trials.
