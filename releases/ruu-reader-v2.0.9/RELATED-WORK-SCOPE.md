# Reading scope and contribution boundary

The main paper asks how much information decision-record crossings add beyond simpler checks with the same access. The result is a scoped case study, not a new general diagnosis algorithm. The companion compares two fixed observation policies in one finite covering class; it does not introduce active learning or establish live LLM benefit. Neither component reports a head-to-head performance comparison with the sources below.

This targeted review was conducted on 27 October 2026. Reading depth is explicit; a primary abstract is not represented as a full-paper examination. This is not an exhaustive novelty proof.

| Primary source and reading scope | Consequence for the claim |
|---|---|
| [CAR v1](https://arxiv.org/html/2606.08275v1), methods and evaluation | Intervening on an agent step and rerunning its policy differs from recomputing an external decision record. Counterfactual execution is not claimed as new. |
| [AgentRx v2](https://arxiv.org/html/2602.02475v2), methods and limitations | Constraint-derived evidence already supports trace diagnosis. Our question is the additional information of a specific record/rule calculation. |
| [AGENTSCOPE v1](https://arxiv.org/html/2609.02371v1), abstract and behavioral abstraction | Structured behavioral evidence is established prior work. No superiority over this method was tested. |
| [BLADE v1](https://arxiv.org/html/2610.18780v1), methods and section 4.3 ablation | Evidence-level comparisons and selective versus full inspection are close prior themes. The distinction here is the exact structural accounting of a fixed crossing contract. |
| [Jacovi and Goldberg (2020)](https://aclanthology.org/2020.acl-main.386/), primary abstract and bibliographic record | External agreement must be separated from faithfulness to the underlying computation. No detailed full-text audit is claimed for this source. |
| [Geiger et al. (2021)](https://proceedings.neurips.cc/paper/2021/hash/4f5c422f4d49a5a807eda27434231040-Abstract.html), primary abstract and intervention framing | Interventions on neural representations and substitutions in an external numerical table are different evidence. |
| [Cohn, Atlas and Ladner (1994), author source page](https://www.cs.cmu.edu/~cohn/papers.html), author abstract | Choosing informative observations is established. The companion contributes a realized policy comparison with explicit computational costs in its specified frame. |
| [LLM-IDEA v1](https://arxiv.org/html/2610.11253v1), identifiability/acquisition method and limits | Identifiability depends on the class and observation contract. The companion retains this dependency and does not claim a universal guarantee. |

[One Reflex, Two Answers](https://www.mdpi.com/2504-4990/8/9/275) was an additional potentially related lead. Primary full-text and PDF access failed during the review. It is not treated as a verified comparison or a read source. This unresolved lead is another reason to avoid universal priority claims.

The main empirical lessons concern applicability, same-rule and row degeneracies, and sensitivity to researcher completion. Full recovery by a per-record rule scan is a consequence of the common-menu contract. The companion's positive paired difference remains conditional on its finite class, query contract, saved-target audit and sampling frame. Broad reliability, internal faithfulness, cross-contract transfer, economic utility and independent replication remain outside the demonstrated claims.


The companion now adds a bounded connection to active automata learning and query selection. Angluin (1987), *Learning Regular Sets from Queries and Counterexamples*, was inspected in the primary paper (abstract and teacher/oracle setup): membership/equivalence queries and whole-language identification differ from the present one-step, target-specific transducer certificate. Seung, Opper and Sompolinsky (1992), *Query by Committee*, was checked through the Princeton bibliographic record and abstract, not a full-text replication: disagreement-based selection provides context, not a theorem or learning-rate comparison. Sources: https://homepages.math.uic.edu/~lreyzin/papers/angluin87.pdf and https://collaborate.princeton.edu/en/publications/query-by-committee/. These additions do not establish exhaustive novelty or comparative performance.


## Focused update — 29 October 2026

Three primary sources clarify the connection to the broader research program. Madsen, Chandar and Reddy (2024), https://aclanthology.org/2024.findings-acl.19/, was checked at abstract/metadata depth: behavior-linked self-consistency is a different target from exact external record recomputation. Mayne et al., https://arxiv.org/html/2602.02639v2, was inspected at abstract and Sections 1–2.2 depth: a predictor's gain from access to an explanation concerns the reference model's behavior on related inputs. BoxingGym, https://arxiv.org/html/2501.01540v2, was inspected at abstract and evaluation/framing depth (Sections 3.2–3.3): experiment information gain and predictive use of explanations differ from the current record-level case study. No source was independently reproduced here, and this update is not an exhaustive literature review.

The main manuscript uses these distinctions to state three untested next questions: assumption–experiment-choice linkage, uncertainty reduction against a valid fixed plan with the same resources, and explanation predictions on withheld cases. No superiority or priority claim over these sources is made.
