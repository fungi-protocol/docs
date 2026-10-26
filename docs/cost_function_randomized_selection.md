---
type: concept
title: Randomized selection
status: draft
stale_after: 2026-11-06T00:00:00Z
---

# Randomized selection

<!-- cspell:words msats rivalrous -->

Two terms of the [cost function](optimization_framework.md): weak preferences that randomize the choice of which UTXOs to co-spend with, using the blockchain as a randomness beacon. The [Sybil resistance](cost_function_sybil_resistance.md) term values coins by how well that randomization can be observed in their history.

Together they:

- make Sybil attacks more costly;
- promote a robustly connected transaction graph, with similarities to [interconnection networks](https://en.wikipedia.org/wiki/Multistage_interconnection_networks);
- establish a Schelling point among takers with regards to which makers to interact with;
- reduce temporal fingerprinting of makers' UTXOs' availability;
- provide useful information to light clients with limited access to the blockchain.

They compose with arbitrary other terms. The setting is non-cooperative, so they are a component of a strategy, not a mechanism. If widely adopted by those paying for CoinJoin blockspace, privacy related payoffs are more strongly positive sum.

Makers announce UTXOs in an order book, and takers propose to spend them in CoinJoin transactions, as in [coalition formation](coalition_formation.md). The roles are used loosely: a single participant may perform both.

## Inputs

- $t$: a block hash, e.g. 144 blocks from the best known chain tip.
- $I$: the outpoints being considered for spending in a possible transaction, with $n = |I|$.
- $x_i = H(t, i)$ for each $i \in I$, where $H$ is a tagged hash. Hash outputs are interpreted as rational numbers in $[0, 1]$.
- $f_1, f_2$: monotone scaling functions, e.g. log or sqrt, possibly with a bias.

## Per input term

$$
f_1\left( \sum_{i \in I} x_i \right)
$$

- How "lucky" a maker's coin is at a point in time, with many leading 1's in the hash output being considered lucky. This is a total ordering over inputs.
- A weak preference: more than 0 but less than 1 sat, so it only breaks ties.
- It lets takers converge on the same makers' coins, especially when the number of active takers is small enough that a grand coalition can construct a single transaction. All else being equal, takers concentrate on the same subset of makers, reducing their shared costs.

## Pairwise term

$$
f_2\left( \sum_{i,j \in I} x_i \oplus x_j \right)
$$

- An affinity between inputs, using the XOR metric. Valuing it promotes randomized assortativity between inputs.
- A weak preference, like the per input term. It scales quadratically in the number of inputs, which $f_2$ must account for.
- **Tipping point.** Due to the CoinJoin liveness model, success probability is roughly exponential in the number of inputs. This limits how far the total order of the per input term can be optimized. Where these interactivity costs dominate, this term dominates over the first, avoiding more rivalrous competition for lucky coins to all be spent in the same transaction.
- **Partitions.** When the candidate UTXO set is larger than the feasible transaction size, this term promotes partitioning of the candidate UTXO set, with each part being a reasonable estimator for its size.
- **Why XOR.** For uniform $x_i$, $x_i \oplus x_j$ is also uniform. Preferring small values also biases the $x_i$ themselves: a pair whose XOR has $b$ leading zero bits shares its $b$ most significant bits, so both lie in a random subinterval of size $2^{-b}$. This simplifies the density estimation. The Hamming distance or the arithmetic difference would change the distribution, and the scaling functions can simulate such effects.

## 🤖 Order book size estimation {#cardinality}

The [Order book size estimation](sybil_resistance_index.md) chapter gives a lower bound $L$ on the number of candidate coins $N$ the inputs were selected from, using the joint sums of the input hashes, with $P(L \gt N) \le \delta$ for every selection strategy. It also gives the proofs, the scan over block hashes, and measurements.

## 🤖 In the decision tree {#in-the-decision-tree}

- **Per input and pairwise terms** change during coalition formation, as candidates appear.

## After confirmation

This is the analysis that contributes privacy gains, and that uses the budget.

- All inputs are known, but $t$ isn't. It can be guessed from the confirmation time, or the nLockTime.
- 🤖 $L$ is the maximum over the candidate block hashes mined after the inputs confirmed, each at $\delta / W$ for $W$ candidates. See [Finding the block hash](sybil_resistance_index.md#finding-the-block-hash).
- 🤖 The [Sybil resistance](cost_function_sybil_resistance.md) term of the transaction's outputs is then fixed.

## 🤖 Open questions {#open-questions}

- What should $\delta$ be?
- Can light clients estimate $L$ for transactions they only sample?

