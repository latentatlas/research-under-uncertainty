# Recorded results and study scope

Two development studies are summarized below. They use different tasks and scoring units, so their numbers are not pooled or treated as a model comparison.

## October matched calibration

The first of two planned sessions closed on 17 October 2026. GPT-6 Astra at max reasoning completed one attempt at each of three candidate levels for each of four fixed starting conditions.

| Candidate level | Planned | Success | Scientific failure | Unscored | Observed success fraction |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 4 | 4 | 0 | 0 | 4/4 |
| B | 4 | 2 | 2 | 0 | 2/4 |
| C | 4 | 0 | 4 | 0 | 0/4 |
| Session total | 12 | 6 | 6 | 0 | 6/12 |

These 12 episodes reuse four starting conditions. They are not 12 independent draws from a population of worlds. The observed ordering motivates further checking; it does not establish that the middle level is reliably intermediate. The second session and testing on fresh conditions are needed to assess that interpretation. No inferential model-ranking claim or population confidence interval is supplied for these four fixed conditions.

The [aggregate JSON](../data/calibration-summary.json) contains only the per-level planned counts and outcome categories for this first session. Pending results from the rest of the 24-episode collection are not encoded as failures or omitted from a claimed final collection result.

## September prediction pilot

The earlier pilot, recorded on 28 September 2026, used GPT-5.6 Sol at high reasoning. Two development worlds were each attempted twice. The outcome below is the number of accepted submitted prediction targets, not the goal-completion measure used in October.

| Recorded attempt | Submission outcome | Accepted prediction targets |
| --- | --- | ---: |
| 1 | Scored submission | 22/24 |
| 2 | Submission protocol termination | Unscored |
| 3 | Submission protocol termination | Unscored |
| 4 | Scored submission | 24/24 |

All four planned attempts are represented. The two unscored submissions remain unscored; their absence is not evidence of correct predictions. The target totals of 22 and 24 are not counts of independently solved worlds. The raw inputs, target values and participant solutions are withheld from this edition.

## Interpretation

Task completion and accepted predictions provide evidence about performance on their stated tests. Neither is by itself a demonstration of complete mechanism knowledge. Process annotations also require care: a participant's explicit statements are observable outputs, not a complete record of its internal reasoning. This edition publishes no retrospective mechanism-learning scores.

The practical next step is to assess the completed repeated calibration before deciding whether to open a fresh-condition validation. Additional model and reasoning comparisons should use the same task and accounting rules once candidate levels have been checked. Those future studies are not reported as completed here.
