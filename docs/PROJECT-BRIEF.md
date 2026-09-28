# Investigating How AI Agents Research Under Uncertainty

**Ongoing independent research project · Research work sample · 28 September 2026**

I initiated this project after noticing a possible gap between an AI model's ability to explain a research method and its ability to choose and carry out useful experiments in an unfamiliar situation. I wanted to examine how agents identify missing information, respond to observations, revise explanations and check their predictions.

I directed the research questions and successive design revisions, working with Codex on technical design, implementation and analysis. Early tasks produced strong results. I challenged whether those tasks actually required the open-ended investigation I wanted to observe. That led to repeated reviews of the information given to the participant, the experiments available to it, and the relationship between the final score and the recorded research process.

The current prototype combines controlled simulated environments, a runner that records experimental actions and observations, quantitative checks of predictions and explicit claims, and an experimental five-dimension process rubric. Records distinguish scientific outcomes, protocol or tool problems, resource stops and insufficient evidence. Numerical checks can be recomputed locally; judgments about the meaning of a public statement remain attributed interpretations. The records are evidence of observable behavior, not access to a model's complete internal reasoning.

A recent preregistered pilot used two development worlds with two fresh runs per world, keeping the model, reasoning setting and task configuration fixed. In one world, the two runs scored 22/24 and 24/24. On the two targets sensitive to a hidden interaction, they scored 0/2 and 2/2. The first run closed its investigation while five available measurements contradicted its stated explanation. The second constructed matched histories that initially produced the same observation but diverged under the same next input. It investigated that difference, revised its explanation and tested new predictions. The final explanation agreed with all 688 measurements available at closure. The other world's two runs terminated by protocol (not scored).

This small case illustrates why I want final accuracy, evidence handling and operational reliability to be inspectable together. It also exposed a limitation of our own scoring: an aggregate dimension could obscure good experimental choices when later interface errors were included. The original scoring rule and alternative scope interpretations are both preserved.

My contribution is the research direction: questioning task validity despite high scores, requiring detailed process evidence, challenging unsupported difficulty claims, and insisting that missing evidence and infrastructure problems remain distinguishable. Codex contributed technical proposals, code, tests, calculations, trace analysis and writing.

The project is developing toward a benchmark. This work sample contributes an inspectable experimental prototype, a reproducible numerical replay and a documented sequence of research decisions. The four-run pilot supports detailed case analysis; calibration and broader validation are the next research stages. [Pilot identities and scope](RESULTS-SCOPE.md).

[Read the case study](CASE-STUDY.md) · [Contributions](CONTRIBUTIONS.md) · [Evidence provenance](REPRODUCING.md)
