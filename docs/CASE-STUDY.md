# When the same score table is not enough to understand the investigation

Research case study, 28 September 2026. This is a retrospective reading of a prospectively registered four-run pilot. The examples were selected after the outcomes to explain observable differences. They are not a new preregistered causal comparison.

The agent worked with an unfamiliar simulated system. It could choose input sequences, obtain measurements, analyze its recorded data and submit predictions for target sequences. The mechanism was not supplied in its starting instructions. The model and reasoning profile, GPT-5.6 Sol/high, were fixed across all four runs. Two N8 development worlds were each tested twice, in a recorded order, with broad resource limits.

All four original outcomes are retained:

| Recorded order | Run | Termination | Accepted targets | Interaction-sensitive targets |
|---|---|---|---|---|
| 1 | w2-r1 | Completed | 22/24 | 0/2 |
| 2 | w1-r1 | Participant protocol error | No score | No score |
| 3 | w1-r2 | Participant protocol error | No score | No score |
| 4 | w2-r2 | Completed | 24/24 | 2/2 |

Full identifiers have the prefix `sol-high-cdr-`. The target groups were frozen before these runs. No run stopped because of resource limits, and no additional run was selected in response to a result. These worlds were already part of development; this is not a held-out family test. [Outcome records](../data/episodes.json).

In w2-r1, the agent corrected the spatial part of its explanation but retained an additive account of the temporal behavior. At closure, five of the 206 measurements available to it disagreed with that account. One example was observation o0075 at its second tick: the stated rule predicted 1.25, while the observed value was 1.37. The final calculation faithfully applied the incomplete rule. Both interaction-sensitive targets were wrong, while the other 22 were correct. This separates the support for an explanation from the faithful execution of its arithmetic.

In w2-r2, the fifth decision selected a particularly useful comparison. Two different first inputs created the same initial readout, after which the agent applied the same continuation:

| Selected input history | First readout | Common next input `(x, u, v)` | Next readout |
|---|---|---|---|
| First input `(0, 1, 0)` | 1.000000 | `(6.8, 0.1, 0.2)` | 0.900000 |
| First input `(0, 0, 1)` | 1.000000 | `(6.8, 0.1, 0.2)` | 0.936000 |

The equal initial readouts did not determine the next response. In its next public record, the agent recognized a dependence on the earlier channel history. It tested controls with zero current input; the difference disappeared. It then varied the current inputs and incorporated a position-dependent interaction between the previous v input and the current u input into its explanation.

At the eighth decision, the revised rule agreed with the 545 measurements then available. Two subsequent experiment groups returned 84 and 59 new measurements that also agreed. At closure, the rule matched all 688 available measurements within the recorded numerical precision. The submitted predictions scored 24/24. The observation count includes six provided measurements; readouts from shared sequences are not 688 independent experimental replications. [Source-bound numerical examples](../data/episodes.json) and [closure-rule replay](../replay.py).

The two unscored runs illustrate another distinction. In w1-r1, the agent closed with 16 contradictory measurements among 169 available. In w1-r2, all 125 available measurements were compatible with its incomplete account: the chosen experiments had not exposed the interaction. The latter cannot fairly be described as ignoring an observed contradiction. Its broad claim about channel symmetry instead raises a question about the scope actually tested.

Both runs later produced invalid submission/stop envelopes. A separately registered local diagnostic found that the stored schema included the submission operation and accepted the already-computed lists through that path. It did not repair the live runs, assign them replacement scientific scores or establish the remote cause of the interface confusion. The successful w2-r2 run also had interface difficulties before eventually submitting. [Delivery diagnostic](../data/DELIVERY-CHECK.json).

The project assistant read all 54 committed decisions across five process dimensions. Of 270 cells, 122 have ordinal ratings; the remaining cells distinguish no opportunity, insufficient evidence and out-of-rubric cases. These are outcome-aware, assistant-authored interpretations supported by public records. Programmatic checks validate their provenance and consistency, not independent human agreement. Scope and wording sensitivities are explicitly recorded. [Complete process reading](DECISION-INDEX.md).

The case demonstrates an observable link between an experimental comparison, subsequent model revision and successful predictions. It does not establish the causal advantage of that strategy, a model ranking, an exponential difficulty curve or a general alignment finding. Its value as a work sample is that a reviewer can inspect the evidence, challenge the interpretation and see why seemingly similar failures were treated differently.
