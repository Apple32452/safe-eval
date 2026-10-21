# Closest-work boundary for Stage 17

This is a focused primary-source comparison, not an exhaustive survey.

| Work | Closest capability | Difference from Stage 17 |
| --- | --- | --- |
| Kossen et al., [Active Testing, ICML 2021](https://proceedings.mlr.press/v139/kossen21a.html) | Actively selects test labels and debiases performance estimation. | Estimates model loss; does not address simultaneous fixed-benchmark pair certificates with one system-item score reused across many pairs. |
| Mohankumar and Khapra, [Active Evaluation, ACL 2022](https://aclanthology.org/2022.acl-long.600/) | Uses dueling-bandit pair selection to identify the top NLG system and adds metric-guided pair comparisons. | Its feedback is a direct comparison for one chosen system pair; Stage 17 charges scalar system-item scores and exploits reuse across the entire pair graph. |
| Kossen et al., [Active Surrogate Estimators, NeurIPS 2022](https://proceedings.neurips.cc/paper_files/paper/2022/hash/9b9cfd5428153ccfbd4ba34b7e007305-Abstract-Conference.html) | Learns a surrogate and interpolates unobserved losses for label-efficient evaluation. | Stage 17 makes design-based finite-population conclusions without imputing unobserved human scores. |
| Ashury-Tahan et al., [DiffUse, ACL 2024](https://aclanthology.org/2024.acl-long.456/) | Selects pair-specific examples by clustering output-difference embeddings and includes iterative stopping. | Each selection is built for one model pair and its reported hypergeometric stopping rule is not the shared-label simultaneous certificate here. |
| Li et al., [Active Evaluation Acquisition, ICML 2025](https://proceedings.mlr.press/v267/li25bp.html) | Learns example-selection policies that predict held-out benchmark outcomes. | Optimizes performance estimation from example dependencies; it does not give the fixed-population family guarantee or shared system-item cost model studied here. |
| Purificato et al., [Active Testing in NLP, 2026](https://arxiv.org/abs/2603.21840) | Benchmarks NLP active-testing strategies and adds adaptive stopping. | Its target is metric estimation from selected examples rather than simultaneous pairwise certification with reusable labels. |

Accordingly, the candidate contribution is the combination of a reusable
system-item annotation cost model, arbitrary shared-label scheduling wrapped
around complete randomized pair paths, and certificate-driven frontier
allocation. Applying active testing, dueling bandits, or clustering to MT is
already established and cannot be claimed as new.
