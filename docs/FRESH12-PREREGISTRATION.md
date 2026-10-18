# Prospective validation on twelve fresh inputs

This study asks whether the task-performance separation between configurations A
and C transfers to twelve newly sampled starting conditions, and where B falls
between those endpoints. It uses GPT-6 Astra with max reasoning. It does not test
a new mechanism family, independent laboratory replication, or the accuracy of a
learned mechanism model.

## Fixed sample and execution

Twelve fresh starting conditions are crossed with A, B and C, giving 36 original
episodes and one attempt per starting-condition/configuration pair. The private
sampling rule and sample were fixed before any validation call. Only exact
duplicate inputs were eligible for rejection. No input is selected or replaced
because of expected difficulty, outcome or cost. The sample is not enlarged after
seeing results.

Starting-condition order and configuration order within each block were
randomized and fixed in advance. Each three-configuration block remains intact.
Three execution chunks contain four different starting conditions each; these
chunks are not repetitions. Participant instructions, permitted tools, task
physics, scoring and budgets are unchanged from the preceding calibration.
Results and analyst diagnoses from that calibration or other episodes are not
supplied to the participant.

Each episode permits up to 32 physical steps, 64 model decisions and four hours
of elapsed time. The task outcome requires completion of all 32 steps and the
announced goal tolerance at each of the final five states. Model decision calls
use fresh contexts containing only the episode's permitted record. Analysis uses
decision, time and token resources but does not advance the physical state.

## Outcomes, retries and missing data

Success and scientific failure are scored outcomes. Infrastructure, protocol and
resource terminations are unscored; they remain visible in the denominator and
are not replaced. Every configuration has twelve planned episodes. Later
physical diagnoses do not change the registered outcome category.

The unchanged recovery policy permits at most two retransmissions for qualifying
transport faults without a completed valid response, using the same input and
state. Correctness never determines a retry. Built-in CLI retries are disabled.
Known usage, unknown-usage reserves and neutral connection checks are reported
separately. No best-of selection is performed. An interruption, identity or
integrity failure prevents automatic resumption. Interim scientific outcomes do
not trigger early stopping.

## Prespecified comparisons

The primary comparison is A greater than C on the twelve matched binary outcomes,
using a one-sided exact paired test with an inclusive tail and significance
threshold 0.05. Only discordant pairs contribute to the exact fair-binomial tail.
The label-exchange interpretation requires the registered randomization and no
cross-episode carryover; random ordering does not make all calls independent.

The A versus B and B versus C comparisons use the same test and are always
reported. A joint claim that both adjacent contrasts are supported requires the
primary and both adjacent tests each to pass the threshold. A favourable single
adjacent comparison is not selected for a separate confirmatory claim. Effect
sizes and paired outcomes are reported even when tests do not pass. No middle
success band or minimum contrast is chosen after observing the validation data.

Missing outcomes are retained in all planned denominators. Both favourable and
unfavourable binary-completion bounds are reported for each paired test. A limited
contrast statement with missing data requires all chunks to close with valid
audits, no holds, and the most unfavourable completion to pass the prespecified
test. Otherwise that comparison remains unassessed because of missing data.
Outcome-completion ranges are not confidence intervals. Integrity failures cannot
be repaired by these bounds. No final comparison is assessed before all 36 planned
assignments have closed.

## Interpretation and access

A supported endpoint comparison establishes a separation for this panel, profile
and task family. It does not by itself establish three distinct difficulty levels.
Even joint adjacent support does not establish universal or stable difficulty
levels across models, budgets, dates or mechanisms. Failure to pass a test is not
evidence of equality. Task success is not a mechanism-learning score; new
prediction-submission and generalization instruments are excluded from this run.

The prior calibration is development evidence and is not pooled with this panel.
An earlier public edition exposed private implementation material, as documented
in [Publication history](PUBLICATION-HISTORY.md). This family is not represented
as never disclosed. The configured participant has no browsing or external tools;
this does not prove absence of prior knowledge or reveal provider training data.

The separate [manifest commitment](FRESH12-COMMITMENT.md) binds the private
protocol, sample, ordering and implementation to fixed bytes before collection.
The private contract, parameters, generator, evaluator and raw model records are
withheld. Public readers can inspect this design and later aggregate reporting;
the commitment does not provide independent physical replay or an independent
audit. The earlier confirmatory decision remains unassessed, and the publication
difficulty gate remains open. Further experiments and result publication require
separate decisions.
