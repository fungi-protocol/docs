---
type: concept
title: Privacy liability terms
status: draft
stale_after: 2026-11-06T00:00:00Z
---

# Privacy liability terms

🤖 The concrete terms of the [cost function](optimization_framework.md). Each term is specified in its own chapter. This one summarizes them.

## Terms

🤖 Objective costs, such as fees and blockspace, are concrete. The terms below are privacy liabilities and preferences.

### 🤖 Randomization {#randomization}

Two weak preferences, defined only on outpoints. $t$ is a block hash, used as a public randomness beacon, and $x_i = H(t, i)$ for each input outpoint $i$. Each preference is worth less than 1 sat, so it only breaks ties.

- **Individual:** $x_i$, preferring "lucky" hashes. This is a total order on coins.
- **Pairwise:** $x_i \oplus x_j$, preferring pairs with a small XOR metric.

Both are summed over the transaction's inputs, through a monotone scaling function. They bias co-spending through market choices. See the [Randomized selection and Sybil resistance](cost_function_randomized_selection.md) chapter.

### 🤖 Sybil resistance {#sybil-resistance}

The provenance term estimates the size of the order book at the time of a coin's funding transaction, from that transaction's input set. So it can be seen as a multiplier for the liquidity (coindays) and the transaction cost (fees) of the observed transaction. A discount rate reduces them to one cost. It can be repeated for ancestors, subject to data availability and computational limits.

That's why it's conservative: the cost to the adversary can be reported as a minimum cost and a predicted maximum. The estimate can also be used for degree sequence estimation in the Karrer–Newman model of the [Max flow based counterfactual path estimation](cost_function_counterfactual_paths.md) chapter.

The Sybil resistance index $L$ is a lower bound on the number $N$ of candidates, computed from joint sums of spans:

1. Sort the input hashes $x_i$ on a circle of $2^{64}$ points.
2. $T_{m,r}$ is the smallest total width of $r$ spans with disjoint interiors, each from a hash to its $m$-th successor, plus one grid unit per span. Let $\tau_{m,r} = T_{m,r} / 2^{64}$.
3. For a hypothetical pool of $M$ candidates:
   $$
   q_{m,r}(M) = \min\left(1, \frac{M^{r(m+1)} \, \tau_{m,r}^{rm}}{r! \, (rm)!}\right)
   $$
4. The score is:
   $$
   S(M) = \sum_{m,r} \frac{q_{m,r}(M)^{-1/2} - 1}{m(m+1)r(r+1)}
   $$
5. $L$ is the smallest $M$, at least the number of inputs, with $S(M) \lt 1/\delta$.

Someone examining the transaction doesn't know $t$. So they take the largest $L$ over the $W$ candidate block hashes, each at $\delta / W$.

Joint sums are used because the estimate:

- **is symmetric:** rotating or reflecting the hashes doesn't change $L$;
- **uses all input values:** every input's hash enters through the spans;
- **can be bounded computationally:** caps on $m$ and $r$ keep the guarantees, and sums of single gaps screen each block hash;
- **is simple to understand how it's monotone:** adding an input splits a gap, so the sums only shrink and $L$ only grows;
- **has a controllable error:** $P(L \gt N) \le \delta$ for every selection strategy.

See the [Randomized selection and Sybil resistance](cost_function_randomized_selection.md) chapter for the terms, and the [Sybil resistance index](sybil_resistance_index.md) chapter for the proofs and measurements.

### 🤖 Subset sum ambiguity {#subset-sum-ambiguity}

A liability $0 \le \ell(o) \le 1$ for each output $o$ of a proposed decomposition.

- It scores how well subset sums of the other users' inputs' effective values cover the complete sumset of the decomposition from above, within a slop $\varepsilon$.
- The denser these subset sums, the more explanations, and the lower $\ell(o)$.
- Counting stops once there are enough explanations, and $\ell(o)$ only falls as inputs and outputs are learned.

See the [Own inputs or outputs subset sum ambiguity](cost_function_subset_sum_ambiguity.md) chapter, and the [Others' inputs subset sum density](subset_sum_density.md) chapter for how density is estimated and optimized.

### 🤖 Max flow based counterfactual path estimation {#max-flow-based-counterfactual-path-estimation}

Disjoint flows: the number of counterfactual routes $\lfloor F / d \rfloor$ from a source coin to a set of sink coins.

- $F$ is a max flow over the transaction graph, with every edge capped at the amount $d$.
- Each own coin gets a label $0 \le \iota(c) \le 1$ from the routes from its own origins. At $\iota(c) = 1$ it's impervious to intersection attacks.
- For coins spent together, the routes matrix, with the routes from each origin to each input, shows what an intersection can reveal.

See the [Max flow based counterfactual path estimation](cost_function_counterfactual_paths.md) chapter.

### Consolidation

🤖 Spending own coins together links them, and loss from intersection attacks compounds with each one.

- 🤖 $\ell_c = (b^{\nu_0} - 1) \cdot (1 - p q)$, where $\nu_0$ is the number of inputs less one, and:
  - $q = 1 - \nu / \nu_0$ measures the routes, where $\nu$ sums $1 - \iota$ over the inputs, less the largest one;
  - $p$ measures the density of their subset sums.
- Normally the penalty can be larger than the budget, to avoid actions vulnerable to intersection attacks.
- 🤖 Routes and density each relieve it only in proportion to the other.
- With subset sums dense enough that the inputs can't easily be clustered, and with counterfactual routes, consolidation is tolerated freely.
- 🤖 $\ell_c = 0$ once the density reaches its threshold and every input but one is impervious. Density alone isn't enough, because comparing the ancestor sets of pairs of inputs narrows down an intersection attack efficiently, even in a large transaction.
- So the cost function compels a strategy. First CoinJoin with low fan-in while the subset sums on the inputs are dense. Once the counterfactual routes are built and the funds are well absorbed into the CoinJoin graph, consolidate their descendants, subject to the counterfactual superconcentrator condition: $K$ routes over the other users' edges only, from the earliest ancestor coins to the inputs under consideration.

🤖 See the [Consolidation penalty](cost_function_consolidation.md) chapter.

### 🤖 Sibling avoidance {#sibling-avoidance}

Spending outputs of the same transaction together is penalized heavily.

- $\ell_s = \sigma \sum_T \max(0, j_T - 1)$, where $j_T$ is the number of inputs created by transaction $T$, and $\sigma$ is large.
- Neither $\iota$ nor density reduces it.

See the [Sibling output penalty](cost_function_siblings.md) chapter.

### 🤖 UTXO pool diversity {#utxo-pool-diversity}

A wallet also values the diversity of its own UTXO pool:

1. some radix denominations;
2. some coins with high Hamming weight;
3. a good size distribution, possibly adapted to the wallet's payment distribution.

How to represent this mathematically is an open question.

### 🤖 Other ad hoc terms {#other-ad-hoc-terms}

Other ad hoc terms, such as fingerprint avoidance, are yet to be specified.

### 🤖 In the decision tree {#in-the-decision-tree}

- **Subset sum ambiguity** can only fall as other users' inputs and outputs are learned. This gives the best and worst cases in [step 6 of *Bottom-up construction*](bottom_up_construction.md#6-bracket-and-back-up-values).
- **Labels** $\iota$, and the routes matrix entries for confirmed inputs, are fixed once a coin confirms, so they're cached per coin. Nothing other users add changes them.
- **Siblings and consolidation** are fixed when the inputs are chosen, except that $\ell_c$ can only fall as density rises.
- **Best cases** of the privacy liabilities are 0, used for pruning.
- **Randomization** changes during coalition formation, as candidates appear. The provenance term is fixed once a coin's funding transaction confirms. Both are events that trigger [re-evaluation](tactics.md#re-evaluation).
