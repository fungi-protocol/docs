---
type: concept
title: Consolidation penalty
status: draft
stale_after: 2026-11-06T00:00:00Z
---

# 🤖 Consolidation penalty

A privacy liability term of the [cost function](optimization_framework.md). Spending several own coins together adds exposure to [intersection attacks](collaborative_txn_privacy.md), which the term models as compounding with each additional coin. [Subset-sum density](subset_sum_density.md) and counterfactual routes jointly attenuate the penalty: the contribution of each depends on the other. The penalty is fully discharged when both meet their thresholds.

- **Why unbounded.** Consolidation may leave the wallet worse off than its baseline, so the liability can exceed 1 and its associated reduction in subjective value can exceed the remaining privacy budget. Other terms may still outweigh this cost; the penalty does not categorically prohibit consolidation.
- Density alone isn't enough. Comparing the ancestor sets of pairs of inputs narrows down an intersection efficiently, even in a large transaction.

Consolidation exposes the inputs' histories to comparison, so the route analysis considers their combined ancestry. Its measurements describe counterfactual connectivity between each input and the coins through which any of the consolidated funds first entered the wallet. Combining these measurements into a scalar would quantify how thoroughly the inputs' histories have become connected through other users' transactions. This measure of absorption would inform the consolidation liability alongside subset-sum density. The aggregation rule remains to be specified.

The routes factor uses the route counts $k$ of the [Counterfactual paths](cost_function_counterfactual_paths.md) to [label](#labels) the wallet's coins, and the [combined ancestry](#combined-ancestry) of the inputs.

## Definition

The following parameterization uses per-coin route labels. Incorporating a joint measure of absorption into this parameterization remains an open question.

- $I$: the own inputs of the transaction under consideration, each with a label $\iota(a) \in [0, 1]$, the degree to which $a$ meets the counterfactual-route objective.
  - The labels are defined in [Labels](#labels).
- **Links.** $\nu_0 = |I| - 1$.
- **Linked count.** $\nu = \sum_{a \in I} (1 - \iota(a)) - \max_{a \in I} (1 - \iota(a))$.
  - A single coin gives $\nu = 0$, and so does one coin below the route threshold spent with coins that meet it.
- **Routes.** $q = 1 - \nu / \nu_0$, and $q = 1$ for a single coin.
- **Density.** $\eta = \min_{a \in I} f_a$.
  - $f_a$ is the covered fraction of the [subset sum ambiguity](cost_function_subset_sum_ambiguity.md#definition) term for own input $a$.
  - While decisions are evaluated, it checks $\Sigma(I)$ against $\Sigma_{\le d}(X)$, the other users' inputs known so far. After the fact, it also checks it against $\Sigma_{\le d}(Y)$, the other users' outputs.
  - $p = 1 - \text{clamp}(\log_2(\varphi_c / \eta) / \theta_c, 0, 1)$, with $\varphi_c$ well above that term's $\varphi$.
    - $\theta_c$: the number of doublings of $\eta$ over which $p$ rises from 0 to 1.
- **Liability.** $\ell_c = (b^{\nu_0} - 1) \cdot (1 - p q)$, with $b > 1$ the factor per intersection.
  - **Thresholds.** $p = 1$ once $\eta \ge \varphi_c$. $q = 1$ once every input but one has $\iota = 1$, i.e. $K$ routes.
  - For more than one own input, it's 0 only when both meet their thresholds.
  - The relief from each is proportional to the other: $\partial \ell_c / \partial p \propto -q$. With $q = 0$, density relieves nothing, and with $p = 0$, routes relieve nothing.

## Labels

For each own coin $c$:

- **Origins.** $O(c)$ is the set of coins by which the wallet received the funds $c$ descends from.
- **Routes.** $k_c = \min_{o \in O(c)} k(o, \{c\})$, with the wallet's own edges omitted.
- **Label.** $\iota(c) \in [0, 1]$ rises with $k_c$ and reaches 1 at $K$, the chosen route threshold. For example, $\iota(c) = \min(1, k_c / K)$.
- **Use.** At $\iota(c) = 1$, $c$ adds nothing to the linked count $\nu$.

Everything $k_c$ depends on exists once $c$ confirms: the coins between its origins and $c$, the other coins in their transactions, and their link probabilities. So $k_c$ is fixed from then on, and labels are cached per coin.

### From bounds

With the [bounds](cost_function_counterfactual_paths.md) $k^-$ and $k^+$:

- $\iota$ uses $k^-$, so it's never overstated.
- If $k^- \ge K$, $c$ is impervious.
- If $k^+ \lt K$, it isn't, and more sampling won't change that.
- Otherwise, take more walks, or compute $k$ exactly on a pruned graph.

## Combined ancestry

Spending own coins $I$ together links them. An intersection attack then intersects their candidate origins.

- **Union.** $U = \bigcup_{i \in I} O(i)$: every coin by which the wallet received funds that any of them descends from.
- **Routes matrix.** $M_{i,u} = k(u, \{i\})$, for each $i \in I$ and $u \in U$.
  - It's a bipartite graph from $U$ to $I$, with each edge labelled by its routes, written as a matrix.
  - Each entry is one max flow. Entries already computed for a coin's own origins carry over: $k_c$ is the minimum of row $c$ over $O(c)$.
- **Reading it.** Row $i$ shows which origins $i$ has many counterfactual routes from. When every row is high in almost every column, each input's candidate origins cover almost all of $U$. The sets the adversary can intersect then have a small symmetric difference, so intersecting them reveals little.
  - "Almost every" is read off $M$, not fixed in advance. For example, the columns where one row is at least $K$ and another isn't are what an intersection of those two inputs can reveal.
- **Aggregation.** A [candidate absorption index](#candidate-absorption-index) aggregates shortfalls in pairwise connectivity. Its parameters and its mapping to the consolidation liability remain to be determined.
- **Counterfactual superconcentrator.** The graph of other users' edges only.
  - Sources: the earliest ancestor coins, $U$.
  - Sinks: the inputs under consideration for consolidation, $I$.
  - The aim is $K$ counterfactual routes across it, making it a superconcentrator: for every $j$, any $j$ sources and any $j$ sinks are joined by $j$ disjoint paths.

### Candidate absorption index

One candidate aggregates the shortfall of each input–origin pair from a connectivity objective. For this purpose, use the unrounded flow ratio $r_{i,u} = F_{i,u}/d_{i,u}$, retaining fractional values rather than the integer route count $k$. Let $K > 0$ be the objective and $s_{i,u} = \min(r_{i,u}/K, 1)$ the degree to which a pair meets it. Saturation prevents additional flow for an already sufficient pair from providing further compensation for weak connectivity elsewhere.

For nonnegative weights $w_{i,u}$ summing to 1 over the input–origin pairs, define

$$
A = 1 - \left(\sum_{i \in I,\,u \in U} w_{i,u}(1-s_{i,u})^\alpha\right)^{1/\alpha},
\qquad \alpha > 1.
$$

At $\alpha = 2$, this is one minus the root-mean-square shortfall. Larger $\alpha$ gives weak pairs more influence; as $\alpha$ tends to infinity, $A$ approaches the weakest score with positive weight. Finite $\alpha$ permits strong coverage to compensate for incomplete coverage, while each improvement below saturation increases the index for a pair with positive weight. If a fraction $f$ of the weight has score 0 and the rest has score 1, then $A = 1-f^{1/\alpha}$.

The weights must represent the exposure being evaluated, rather than the number of sampled paths. Their choice remains open, including how to prevent splitting funds or repeating observations from manufacturing credit. The index is a connectivity measure, not an attack-cost estimate. Incorporating Sybil resistance along the supporting paths remains to be specified: an adversary may create apparent alternatives through prior CoinJoins, and the expenditure supporting several pairs cannot be counted as a separate expenditure for each pair.

A possible extension first computes a coverage score for each input across origins, and for each origin across inputs, using a power mean with exponent $0 < \beta < 1$. It then takes a power mean of those profiles' shortfalls, with exponent $\alpha > 1$, and subtracts it from 1. This distinguishes missing connections concentrated around one input or origin from missing connections spread across them, which the single mean does not. It adds a parameter and requires weights at both levels. Neither formulation by itself establishes that a high score makes a targeted intersection attack prohibitively expensive.

## In the decision tree

- It's a privacy-related term.
- **Fixed per coin.** Once a coin confirms, no later block adds to its ancestry. So $\iota$, and the entries of $M$ for confirmed inputs, are computed once and reused in every leaf. Over time, they're constant.
- **A leaf's inputs.** A leaf fixes the own inputs $I$, and with them $U$ and the rows of $M$. Nothing other users add to the transaction changes them, so the best and worst cases of the labels and $M$ are equal.
- **Outputs.** The transaction's own outputs get labels only after it confirms.
- **Order book coins.** The own inputs' coin edges are omitted, so routes from their origins into the transaction's own outputs enter only through other users' inputs.
  - An order book coin that descends from those origins adds routes, so selecting it is valuable.
  - A co-spend proposal from an own input that names such a coin links the two, unless such proposals are already common. An outcome may still prefer the selection, but the cost function should penalize proposals that leak the link this way.
- **Bounds.** Leaves use $\iota$ from $k^-$, the lower [bound](cost_function_counterfactual_paths.md). Tightening $k^-$, with more walks or an exact $k$ on a pruned graph, can run between iterations of the decision loop in the [Mixed strategy](mixed_strategy.md) chapter. It can only raise $\iota$.
- **Worst case:** $\eta$ checks only the other users' inputs known so far. Their outputs aren't known until the transaction has been fully built.
- **Best case:** $\ell_c = 0$, which is used for pruning.
- $\ell_c \ge 0$ is unbounded, so its associated reduction in subjective value can exceed the remaining budget. An automated action requires a predicted improvement under the full cost-function evaluation. Consolidation-heavy branches are pruned when that evaluation cannot justify them; evidence that improves the lower bound can reduce the penalty and change the decision.
- More aggressive consolidation can nevertheless have a better best-case evaluation because of feerates, batching opportunities, or reduced fragmentation. That best case alone does not justify execution under the current lower bound.
- It applies to every own output of the transaction. The reduction in subjective value scales with their total value, independently of the number of outputs.

## After construction

- Once the transaction is fully constructed, $\eta$ is computed from the complete sets and the same cost function is evaluated with that information. This determines the liabilities and the accounting for privacy-budget expenditure, as described in [Cost function structure](cost_function_structure.md#linear-combination). An explicit manual override resets liability accounting to the baseline.

## Evaluating the wallet state

- The term can evaluate a wallet state too. Imagine that an emergency forces the user to spend all of its coins rapidly in one unilateral transaction, and take that transaction's consolidation penalty. This favors arranging the wallet state to minimize the privacy damage if such a liquidation becomes necessary.
- That transaction's cost includes its objective costs, e.g. the fees for each coin, so this also prices a wallet split over many coins.
- It depends on the [open question](#open-questions) about transactions with only the wallet's own coins. Until that's settled, $p = 0$ there, and every state with more than one coin gets the full penalty.

## Monotonicity

- $\ell_c$ can only fall as $\eta$ rises, or as the labels rise.

## Open questions

- How should the absorption index determine the route factor? The [candidate shortfall mean and its grouped extension](#candidate-absorption-index) describe possible aggregation rules; their weights, parameters and resistance to manipulation remain to be evaluated.

- Should siblings also count towards $\nu$?
- A transaction with only the wallet's own coins has no other users' coins, so $p = 0$ and the penalty can't be discharged. Which density applies there? For example, the [covered fraction](cost_function_subset_sum_ambiguity.md#definition) $f_o$ of the outputs that became the inputs, in the transactions that created them.
- How should $p$ and $q$ be scaled?
- What link probabilities apply to the transaction under construction? They must hold in every completion.
- Which term penalizes a co-spend proposal that leaks a link to an order book coin that adds routes, and how is "already common" measured?
- How is the routes factor computed: from each input's $\iota$, as the [definition](#definition) does now, or from the counterfactual superconcentrator condition?
- How is the counterfactual superconcentrator condition checked? It ranges over sets of sources and sinks of equal size, while $M$ holds only single pairs.
- Should $\iota$ ramp up to $K$, or switch from 0 to 1 at $K$? What should $K$ be?
- May $\iota$ use an estimate ($k^+$, the analytic estimate or Monte Carlo) when the randomization evidence is strong, or only $k^-$?
- What label does an own input get before it confirms, such as change from a transaction still in flight?
