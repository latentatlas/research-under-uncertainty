# Task scoring and resource controls

The October calibration evaluates goal-directed interaction with an unfamiliar synthetic system. The participant sees the task interface, permitted observations and the goal. Hidden transition rules and private configurations are excluded from its input. The configurations are labelled A, B and C in this edition without disclosing their internal parameters.

## Matched comparison

The same four fixed starting conditions are crossed with all three levels. The model is GPT-6 Astra with max reasoning. Within each starting-condition block, the level order is fixed by a randomization prepared before execution. Participant-facing instructions, tools, scoring and budgets are held constant across levels.

Each episode permits up to 32 physical steps, 64 model decisions and four hours of elapsed time. Analysis does not advance the physical state, but it uses decision and elapsed-time resources. Each model decision receives only the permitted record for its episode in an isolated working context. Results from other episodes and analyst diagnostics are not added to that context.

The complete calibration plans two sessions, separated by at least 12 hours after the first session closes, for 24 episodes in total. This edition reports the complete first session only. The configurations were selected during development, so this collection is a development calibration rather than an independent confirmation of the task family.

## Outcome categories

Success requires completion of all 32 physical steps and satisfaction of the announced goal tolerance at each of the final five states. The tolerance in the scoring contract is 0.05, with a fixed numerical allowance for computation. The same criterion applies at every level.

A completed goal violation, departure from the permitted region or participant abandonment is a scientific failure. Infrastructure, protocol and resource terminations are recorded as unscored outcomes. A later analyst diagnosis does not replace an unscored outcome with a retrospective success or failure.

All planned episodes remain visible in the denominator. An incomplete result is never silently removed or replaced with the best of several attempts. The first session has 12 scored outcomes and no unscored outcomes.

## Transport and resource accounting

The recorded system includes the model and a fixed transport-recovery policy. Eligible transport faults may trigger at most two retransmissions of the same input, after waits of 60 and 180 seconds. Partial responses are discarded. The first completed valid response is applied once; its scientific correctness does not determine whether it is retried. Built-in CLI retries are disabled.

Measured usage and reserved allowances for unknown usage are kept in separate ledgers. A dropped response with unknown usage is not treated as free. Neutral connection checks are accounted for separately from participant calls. Episode time limits include the episode's calls and recovery waits.

In the reported session, four technical retransmissions affected two episodes. All planned episode outcomes were obtained. Those episodes remain in the results. The observed success counts describe the model operating with this recovery policy; they do not identify the success distribution of a hypothetical system with no retries.

## Checks and their limits

Before execution, local source checks bind the plan, code, scoring rules and model interface to a fixed manifest. Closure checks reconcile recorded outcomes, usage and internal physical replay. These are local integrity checks, not independent peer review, a public timestamped preregistration or proof that the provider's model weights remain unchanged over time.

Because the protected evaluation code and interaction records are omitted from this edition, readers cannot independently repeat those physical checks from the public files. [Evidence boundaries](EVIDENCE-AND-LIMITS.md) describe the checks this edition does support.
