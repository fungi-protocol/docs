---
type: concept
title: Sybil resistance
status: draft
stale_after: 2026-11-06T00:00:00Z
---

# 🤖 Sybil resistance

<!-- cspell:words coindays Karrer superconcentrator superconcentrators bhatt Bhatt -->

The Sybil resistance liability depends on the cost of an adversary supplying the coins in the history of the coin under consideration, and the candidates from which they were selected. The assessment assumes that all candidate UTXOs in the relevant order books, and the transactions that created them, were controlled by one adversary. Observed resource requirements and estimates of unobserved costs are evaluated against the user's threat model.

## Provenance term

For a coin under consideration, a fidelity bond like analysis of the transaction that created it, its funding transaction:

1. **Order book size.** Estimate the size of the order book at the time of the funding transaction, from its input set. This is the lower bound $L$ on the number of candidate UTXOs $N$ from the [Order book size estimation](sybil_resistance_index.md) chapter.
2. **Cost.** Account for the liquidity, holding times and fees visible in the observed graph. Use $L$ and the sampled paths to estimate additional costs, subject to assumptions about the unobserved candidates. A discount rate expresses the time value of capital held over those intervals. This opportunity cost can be combined with fees.
3. **Ancestors.** Repeat for earlier transactions, subject to data availability and computational limits.

Selection bias is a property of past selection events. Those events confer Sybil resistance relevant to the assessment of later coins; the bias itself is not inherited.

- **Why it's a cost.** For a single adversary to construct a transaction exhibiting such a bias, it must control the entire set of candidate UTXOs, not just the coins that end up being selected. Then takers would have to select the outputs of this transaction.
- **Bounds and estimates.** $L$ is a lower confidence bound on candidate count. Converting it into an estimate of unobserved costs requires assumptions about candidate values and holding times. This estimate is distinct from resource bounds established directly by the observed graph.
- **Only with the preferences.** The term can only be optimized in the presence of a market preference like the per input and pairwise terms, or no bias would be detectable.
- **Costless for honest users.** Assuming takers and makers weakly prefer the bias, it's costless, at least on average. With market demand for it, makers can be profitable. This promotes a wider CoinJoin graph, with less temporal assortativity.
- **Waiting.** The longer a UTXO is unspent, the more chances it has of being lucky.
- **Intersection attacks.** Randomization promotes a high number of paths between coins, even for bounded degree graphs, as in superconcentrator graphs.[^bhatt] It doesn't guarantee them: it draws from the non-random set of available candidate UTXOs at a point in time. The estimate can also be used for degree sequence estimation in the Karrer–Newman model of the [Counterfactual paths](cost_function_counterfactual_paths.md) chapter.

See also Belcher's analysis of fidelity bonds.[^belcher]

## 🤖 Observed resource requirements {#cost}

The observed transaction graph provides lower bounds on the resources required under the hypothesis that they were controlled by one adversary:

- **Liquidity.** Coins known to have been unspent concurrently require at least their combined value in liquidity. This bound depends on their total value, regardless of how that value is divided among coins.
- **Capital held over time.** While coins remain unspent, their value cannot also be spent in concurrent CoinJoins. Spending them ends their holding intervals. Maintaining this capital also incurs an opportunity cost due to the time value of money, which is the principal connection to the fidelity bond analysis. Coin values multiplied by their holding durations give capital-time quantities, expressed in coindays; a discount rate is used to evaluate the associated opportunity cost.
- **Fees.** The observed transactions record the fees paid to create and spend those coins. Treating these as costs to the adversary assumes that it controls only a limited share of mining hash rate.

A fetched subgraph can already establish these bounds. It is not necessary to reconstruct the entire ancestry.

## 🤖 Estimation from sampled paths {#whole-graph}

The randomized subgraph is the portion of the transaction graph corresponding to biased input selections. In the bipartite representation with transaction and coin vertices, prune the coin vertices that do not appear to have been randomly selected and take the induced subgraph on the remaining vertices. The randomization is verifiable because the selection uses a cryptographic public randomness beacon.

A path is found by traversing backwards from a UTXO in the order book until reaching CoinJoins already known to the wallet, such as descendants of CoinJoins it participated in. This establishes a flow route. The traversal is repeated several times, bounded to a particular block range.

The observed paths are tallied as in [observed resource requirements](#cost): at a given discount rate, the total cost of their coindays and their transaction fees. This is the base Sybil resistance.

Even if only a small number of paths are found, the [order book size estimate](sybil_resistance_index.md) extends the tally to a cost for the randomized subgraph concurrent with the observed paths: a total cost to the adversary, assuming the observed paths are representative. The representativeness is supported by observable selection bias in the inputs of the traversed transactions.

The estimate is restricted to this randomized subgraph. Only quantities estimated from the subset of inputs exhibiting the selection bias are scaled; other inputs encountered in the fetched history are excluded from that extrapolation. The order book size estimate supplies $L$, a lower confidence bound on candidate count, to estimate the width of the randomized subgraph.

From the observed paths, estimate the candidate-value and holding-time distributions and their means as functions of time, retaining the number of observations supporting each estimate. Scale the estimated means by $L$ to estimate the corresponding aggregate quantities for the randomized subgraph concurrent with the observed paths. Resource estimates derived this way depend on the representativeness assumption, unlike bounds established directly from the observed graph.

Concurrent transactions with similar selection bias provide additional observations of the same candidate population. Combining comparable path samples refines the estimated distributions and their means; it does not add separate population sizes. With two comparable paths, the quantity scaled by $L$ is their mean, rather than their sum. The same applies to more paths: the number of observations supports the estimate and is not an additional width multiplier.

## 🤖 Subjective liability

The observed lower bound and estimated cost are assessed against the user's threat model. There is no universal threshold for sufficient adversarial cost. The cost judged prohibitive depends on the severity of the user's real-world threat model; more severe threats require a higher threshold.

The liability is zero when the attack cost is judged prohibitive under that model. Otherwise, it represents a subjective loss scaled by the user's privacy budget. This valuation guides the combined decision framework; it does not establish that the chosen privacy measures cover every threat to the user.

## 🤖 In the decision tree {#in-the-decision-tree}

The term of a coin under consideration is fixed once its funding transaction confirms, so it's computed once per coin and cached. The transaction's own outputs get theirs after confirmation, as the [randomized selection](cost_function_randomized_selection.md#after-confirmation) chapter describes.

[^belcher]: C. Belcher, [*Financial mathematics of JoinMarket fidelity bonds*](https://gist.github.com/chris-belcher/87ebbcbb639686057a389acb9ab3e25b#cost-of-sybil-attacks).

[^bhatt]: S. N. Bhatt, [*On Concentration and Connection Networks*](https://hdl.handle.net/1721.1/149007), MIT, 1981.
