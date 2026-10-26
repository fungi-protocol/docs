---
type: concept
title: Privacy liability terms
status: draft
stale_after: 2026-11-06T00:00:00Z
---

# 🤖 Privacy liability terms

Privacy liabilities represent subjective losses of utility associated with outcomes that do not meet the user's privacy objectives. Each term evaluates a specified measure or proxy; evidence that the defined problem has been removed discharges the corresponding liability. The cost function combines these liabilities with objective costs and the utility of completing payments to guide the wallet's automated decisions.

The liabilities collectively reduce a new privacy-problematic coin's subjective value by the budget fraction of its nominal value. The [Optimization framework](optimization_framework.md#global-privacy-budget) explains this valuation, and [Cost function structure](cost_function_structure.md#linear-combination) defines the accounting. The measures and their thresholds express objectives chosen for the user's threat model. Meeting them does not establish that the resulting outcome satisfies that threat model in every respect. This chapter describes the purpose and interactions of the terms; their definitions and justifications appear in the linked chapters. The measures computed from public data that the terms take as input are described in the [Privacy metrics](privacy_metrics.md) chapter.

## Randomized selection

An adversary who controls many of the coins a user co-spends with learns the user's coins by elimination. Randomizing which coins are co-spent makes that costly.

- **Per input and pairwise preferences.** They randomize which coins are co-spent, with block hashes as a public randomness beacon. They only break ties, so they don't compete with the other terms.
- **Cardinality.** Everyone uses the same randomness, so the bias it leaves in a transaction's inputs can be observed afterwards, and bounds the size of the order book the inputs were selected from.

Randomization also promotes a robustly connected transaction graph, which the [counterfactual paths](cost_function_counterfactual_paths.md) term measures. See the [Randomized selection](cost_function_randomized_selection.md) chapter for the terms, and the [Order book size estimation](sybil_resistance_index.md) chapter for the lower bound on the number of candidates.

## 🤖 Sybil resistance

The Sybil resistance term evaluates the cost of an adversary supplying the coins in a coin's history and the candidates from which they were selected. Observed resource requirements and estimates derived from selection bias are assessed against the user's threat model. The liability is zero when the attack cost is judged prohibitive under that model; otherwise, it represents a subjective loss scaled by the user's privacy budget. See the [Sybil resistance](cost_function_sybil_resistance.md) chapter.

## Subset sum ambiguity

Amounts are the most direct way to link a transaction's inputs to its outputs, and the inputs to each other. This term measures how well the other users' coins explain the user's amounts.

- The more combinations of the user's outputs the subset sums of the other users' inputs cover, the more readings of the transaction remain, and the lower the liability.
- It measures the same for the user's own inputs.
- Once the transaction has been fully built, both are also checked against the subset sums of the other users' outputs.

See the [Subset sum ambiguity](cost_function_subset_sum_ambiguity.md) chapter. The [Subset sum density](subset_sum_density.md) chapter covers the density it relies on, and how co-spend proposals and the aggregator raise it.

## Counterfactual paths

[Intersection attacks](collaborative_txn_privacy.md) compare the histories of coins across transactions, and what those histories have in common reveals the link. This term counts the disjoint routes a coin's amount could have taken from its origins.

- Its main use is a label for each of the wallet's own coins, indicating how closely it meets the objective for counterfactual routes.
- The consolidation penalty uses these labels, together with subset-sum density, to evaluate spending coins together.

See the [Counterfactual paths](cost_function_counterfactual_paths.md) chapter.

## Consolidation

The consolidation penalty accounts for the additional exposure to intersection attacks introduced by spending multiple wallet-owned inputs together. Its liability is deliberately unbounded: consolidation may leave the wallet worse off than its baseline, and the corresponding subjective loss may exceed the remaining privacy budget. An automated action is taken only when the cost-function evaluation predicts an improvement. Fees, batching, and reduced fragmentation may make more aggressive consolidation attractive in the best case, while the available evidence must support the decision.

The penalty is attenuated jointly by subset-sum density and counterfactual routes, with the contribution of each depending on the other. Dense subset sums alone are insufficient, because comparing the ancestry of pairs of inputs narrows down an intersection efficiently. The route analysis considers each input against the combined set of coins through which the inputs' funds first entered the wallet. These pairwise flow measurements would contribute to a graded measure of absorption, whose aggregation and use in the liability remain to be specified. The consolidation chapter defines these quantities and their thresholds. The same penalty contributes to the evaluation of a wallet state by considering a hypothetical transaction spending all of its coins together, so that the wallet can arrange its state to minimize privacy damage if an emergency requires the user to spend those funds at short notice.

See the [Consolidation penalty](cost_function_consolidation.md) chapter.

## Siblings

Spending outputs of the same transaction together is wasteful, and a strong sign of common ownership. Amounts can explain the values, but not two users spending outputs of one transaction together, so neither subset sums nor counterfactual routes relieve it. It's penalized heavily.

See the [Sibling output penalty](cost_function_siblings.md) chapter.

## UTXO pool diversity

A wallet also values the diversity of its own UTXO pool:

1. some radix denominations;
2. some coins with high Hamming weight;
3. a good size distribution, possibly adapted to the wallet's payment distribution.

How to represent this mathematically is an open question.

## Other ad hoc terms

Other ad hoc terms, such as fingerprint avoidance, are yet to be specified.

## In the decision tree

Each liability either only falls as other users' coins are learned, or is fixed once the inputs are chosen or a coin confirms. That's what lets [bottom-up construction](bottom_up_construction.md#6-bracket-and-back-up-values) bracket every leaf between a best case and a worst case, cache what's fixed per coin, and [re-evaluate](tactics.md#re-evaluation) only when something changes. Once the transaction is fully constructed, the same cost function evaluates the complete state and determines the liabilities and privacy-budget accounting. Each term's chapter says how it behaves in the decision tree.
