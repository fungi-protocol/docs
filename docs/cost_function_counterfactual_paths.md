---
type: concept
title: Counterfactual paths
status: draft
stale_after: 2026-11-05T00:00:00Z
---

# 🤖 Counterfactual paths

A counterfactual-connectivity measurement used by the [cost function](optimization_framework.md). It counts how many times the sink's amount could have travelled from a source coin to the sink coins, along disjoint counterfactual paths. This is the [problem definition](collaborative_txn_privacy.md)'s robust connectivity, measured with one max flow.

The paths start at any coin linked to the source within its transactions, and end at any coin linked to the sinks. These links are what make more than one route possible. A source and a sink with nothing linked to them give at most one.

The [Consolidation penalty](cost_function_consolidation.md) chapter uses it to label the wallet's coins, and to estimate when spending them together is safe from intersection attacks.

## Network

The transaction graph, with details that don't matter here, such as scripts, left out. Transactions are vertices and coins are edges, which works because an unspent coin can't carry flow along the DAG. Each max flow is from one source to its sinks, and every edge is labelled with its capacity for that pair.

Edges follow the funds, from the transaction that creates a coin to the one that spends it. The source is the earlier coin, such as an origin of the wallet's coins, and the sinks are later coins, such as the wallet's own. Bitcoin's references point the other way, from each input to the coin it spends. Either direction gives the same result. Reversing every edge and swapping the source with the sinks turns each cut between them into a cut with the same capacity, so the max flow, and with it $k$, is unchanged.

- **Coin edges.** Each coin $c$ is an edge from the transaction that creates it to the transaction that spends it, with capacity $v(c)$.
- **Flow edges.** The model is refined by replacing each transaction with a bipartite graph: an edge from each spent coin to each created coin.
  - Capacity: $P_{I,O}(i, o) \cdot \min(v(i), v(o))$.
  - $P_{I,O}(i, o)$ is the probability that $i$ and $o$ are in the same sub-transaction.
  - Max flow works the same way on the refined graph, so the model with one vertex per transaction is without loss of generality.
- **Link edges.** These carry no flow. They only define the neighbourhoods below.
  - Between the inputs of a transaction, with probability $P_{I,I}$.
  - Between its outputs, with probability $P_{O,O}$.
- **Neighbourhoods.** The super-source of a coin $s$ connects to $s$ and to every coin linked to it on either side, with capacity equal to the link probability times that coin's value. The super-sink of the sink coins $T$ is built the same way.
- **Own edges.** When source and sink are both the wallet's coins, only counterfactual paths should remain. Two kinds of edges are omitted from the graph:
  - flow edges between two of the wallet's coins in the same transaction;
  - coin edges of the wallet's coins on the way from the source to the sink.

## Definition

For a single source coin $s$ and sink coins $T$:

1. **Amount.** $d = \min(v(s), v(T))$, where $v(T)$ is the sum of the sinks' values.
2. **Caps.** Every coin edge and every flow edge is capped at $d$.
   - Uncapped: the coin edges of the source and the sinks, and the super-source and super-sink edges.
   - Coins linked to the source or the sinks are capped like any other, so each carries at most one route.
3. **Flow.** $F$ is the max flow from the super-source to the super-sink.
4. **Routes.** $k(s, T) = \lfloor F / d \rfloor$.

For several sources, $k(S, T) = \min_{s \in S} k(s, T)$.

- A single super-source over all of $S$ would add up the routes of different sources. Two linked coins with one route each would score 2, hiding the intersection.

### Why this counts routes

- **Theorem.** An acyclic flow of value $v$ in which no edge carries more than $v/k$ is a $k$-route flow.[^kishimoto][^aggarwal-orlin][^chekuri-idleman]
  - That is, it's a sum of bundles. Each bundle is $k$ paths that share no edge, carrying equal amounts.
- **Guarantee.** With every capped edge at $d$ and $F \ge k d$, removing any $j \lt k$ capped edges still leaves a flow of at least $(k - j) d$.
  - So no $k - 1$ capped edges cut the source off from the sinks. This is the problem definition's "no small cut".
- **Uncapped edges.** These behave like $k$ parallel copies, so routes may share them.

### Split routes

A route may be spread over several smaller coins, as long as no two routes share a capped edge. For example, two disjoint coins of $d/2$ each count as one route of $d$.

The floor makes $k$ conservative. Three disjoint coins of $d/2$ give $k = 1$, yet any one of them can be removed and $d$ still gets through.

### Max flow alone isn't enough

- Without caps, a single large coin can carry all of $F$, so $F$ can't tell one route from several.
- Scaling the demand to $k d$ doesn't help, for the same reason.

## Scope

For one source and one sink, only the coins that descend from the source's neighbourhood and are ancestors of the sink's neighbourhood matter. These lie between the two confirmations. One pair never needs the full chain.

### Pruning

Any restriction of the transaction graph gives a lower bound on $k$, since removing coins or edges can't raise a max flow. Some examples:

- the last $n$ blocks;
- only CoinJoins meeting some conditions;
- only the flow edges of specific coins in them, such as equal amount outputs.

A lower bound is safe for [labels](cost_function_consolidation.md): a coin is never labelled impervious when it isn't.

Restricting to CoinJoins undercounts, though: payments and PayJoins intertwined with CoinJoins also carry counterfactual routes.

### Cost

- One max flow per source. Sources are independent, so they parallelize.
- A transaction with $n$ inputs and $m$ outputs has $n m$ flow edges.
  - Cache $P_{I,O}$ per transaction. It has a closed form for equal amounts, and needs subset sum enumeration otherwise.
  - Leaving out edges with small $P_{I,O}$ gives a lower bound.
- A new block only adds coins and edges, so it never lowers $k$.

## Approximation

This avoids computing $k$ on the full graph.

The approximation can't be strictly monotone. Bounding the resources spent on decision making is a client implementation decision. As long as a light client doesn't defect, i.e. it behaves as if its evaluation is monotone, it is still incentive compatible.

### Data access

How much of the chain a wallet sees depends on its constraints:

- With limited bandwidth, it samples blocks.
- With limited storage, it fetches every block in a range, but keeps only a subgraph in a compact encoding. See [Pruning](#pruning).
- If it can only fetch transactions adjacent to ones it knows, it uses the [bounds](#bounds).

### Layers

The approximation estimates each layer of the network separately. Each layer depends only on the ones before it.

1. **Topology.** Transactions, their numbers of inputs and outputs, and how long coins stay unspent.
2. **Amounts.** Coin values. Relative to $d$, they set each coin's capacity.
3. **Links.** $P_{I,O}$, $P_{I,I}$ and $P_{O,O}$, computed from the amounts within each transaction. They set the flow edges and the neighbourhoods.
4. **Knowledge.** The wallet's own edges.

### Sampled blocks

- Sample blocks, and estimate each layer's distributions from their transactions, separately.
  - For the topology: the numbers of inputs and outputs per transaction, and the spend rate $p$, the fraction of unspent coins spent per block.
- Base the estimate on randomized selection, as in the [Randomized selection](cost_function_randomized_selection.md) chapter. When coins are selected at random from the candidates, the transaction graph can be treated as a random acyclic network with those degree distributions.[^karrer-newman-acyclic][^karrer-newman-models]
- **Observed paths.** Traversing backwards from a coin in the order book until reaching CoinJoins the wallet already knows, such as descendants of ones it participated in, establishes a flow route. This can be repeated several times, bounded to a block range. Even if only a few paths are found, they estimate the degree sequence of the random acyclic network, together with the [order book size estimation](sybil_resistance_index.md).
  - The paths give the distributions of the numbers of inputs and outputs, from the transactions they pass through.
  - The order book size estimation gives a median estimate $\hat{N}$ of the number of candidates.
- **Number of candidates $N$.**
  - The order book size estimation gives $L$, a relatively conservative estimate of a lower bound on $N$. It scales the Sybil cost.
  - The degree sequence uses $\hat{N}$, a median estimate of $N$.
  - In the pool model below, no coins enter or leave the CoinJoin graph. There, doubling $N$ from 1000 to 2000 lowers $E[k]$ from 1.20 to 0.73 at $n = 4$, $R = 12$.

### Time slices

Every route crosses each block boundary on a coin that's unspent at that boundary.

- A **slice** is the set of coins unspent at a boundary that descend from the source's neighbourhood and are ancestors of the sinks' neighbourhood, excluding the neighbourhoods themselves.
- Each slice is a cut, so $k$ is at most the smallest slice's capacity.
- In the prototype below, $k$ equals the smallest slice in 95% to 100% of runs.

### Analytic estimate

This covers the topology layer only: every coin's capacity is $d$, and every $P_{I,O}$ is 1.

- **Growth.** $D_r$ is the number of unspent coins after block $r$ that descend from the source's neighbourhood.
  - $D_{r+1} = (1 - p) D_r + \frac{p N \bar{o}}{\bar{\imath}} \left(1 - G(1 - D_r / N)\right)$.
  - $\bar{\imath}$ and $\bar{o}$ are the mean numbers of inputs and outputs, and $G$ is the generating function of the number of inputs. The two numbers are assumed independent.
  - Under random selection, a transaction joins the descendants with probability $1 - G(1 - D_r / N)$, the probability that any of its inputs is a descendant.
  - $A_r$, the ancestors of the sinks' neighbourhood, grows the same way backwards from the sink, with inputs and outputs swapped.
- **Slices.** Under random selection, an unspent coin after block $r$ is an ancestor of the sinks with probability $A_r / N$, independently of whether it descends from the source.
- **Ends.** The slices next to the source and the sinks are the narrowest, and nearly independent of each other.
  - $X \sim \text{Binomial}(n_s, A_0 / N)$, where $n_s$ is the number of coins the source's neighbourhood first reaches.
  - $Y \sim \text{Binomial}(n_T, D_{R-1} / N)$, where $n_T$ is the number of coins that first reach the sinks' neighbourhood, and $R$ is the number of blocks between them.
  - $k \approx \min(X, Y)$, so $P(k \ge K) \approx P(X \ge K) \cdot P(Y \ge K)$.
- Using only the single narrowest slice, $\text{Binomial}(D_r, A_r / N)$, overestimates $k$.

The estimate is neither a lower nor an upper bound.

### Monte Carlo

- Generate transaction graphs from the estimated layers, in order: topology, amounts, links, knowledge.
- Compute $k$ on each with the max flow, restricted to the coins between source and sink.
- Estimate $P(k \ge K)$ from the results.
- Unlike the analytic estimate, this covers every layer.

**Prototype, analytic and Monte Carlo.** A pool of $N$ candidate coins of equal value. In each block, a fraction $p = 0.2$ of the pool is selected at random into transactions of $n$ inputs and $n$ outputs. The source's neighbourhood is the inputs of a transaction in the first block, and the sinks' is the outputs of one $R$ blocks later. Each Monte Carlo row is 30 to 40 runs.

| $n$ | $N$ | $R$ | $E[k]$, Monte Carlo | $E[k]$, analytic | $P(k \ge n/2)$, Monte Carlo | $P(k \ge n/2)$, analytic |
|---|---|---|---|---|---|---|
| 4 | 1000 | 8 | 0.23 | 0.11 | 0.03 | 0.00 |
| 4 | 1000 | 12 | 1.20 | 0.97 | 0.30 | 0.23 |
| 4 | 1000 | 20 | 3.08 | 3.20 | 0.97 | 0.99 |
| 8 | 2000 | 6 | 1.43 | 1.04 | 0.03 | 0.00 |
| 8 | 2000 | 8 | 2.83 | 2.90 | 0.30 | 0.30 |
| 8 | 2000 | 12 | 5.33 | 5.58 | 0.93 | 0.97 |

Counting only whether the first coins at each end are spent or created in time predicts $E[k] = 2.8$ at $n = 4$, $R = 8$. The graph between the ends is what limits $k$ there.

### Bounds

- **Upper bound.** For $k^+$, merge every coin $r$ transactions away from the source into the super-sink, and compute $k$. Do the same from the sink backwards, and take the smaller of the two.
  - Keep $d$ as computed from $s$ and $T$. Merged coins raise the sink's value, and recomputing $d$ from it would break the bound.
  - Merging only adds capacity, so each is an upper bound.
  - The cost depends on $r$ and the local degrees, not on the chain.
- **Lower bound.** For $k^-$, take random walks forward from the source's neighbourhood and backward from the sink's. Follow $f$ randomly chosen edges per step, up to the other end's confirmation height. Compute $k$ on their union.
  - The union is a subgraph, so its $k$ is a lower bound.
  - Walks that cross share edges, and the max flow counts a shared edge once. Overlapping paths aren't double counted.

**Randomization.** With randomized selection, as in the [Randomized selection](cost_function_randomized_selection.md) chapter, in the prototype below, this puts the smallest cut next to one of the ends, so $k = k^+$. That isn't guaranteed in general.

- The selection bias bounds the number of candidates from below. It doesn't show that both ends draw from the same candidates: two groups that never transact with each other can each select at random.
- The evidence that the ends are connected is $k^-$ itself, as it approaches $k^+$.

**Prototype, bounds.** A layered model: 7 layers of 256 coins of equal value, joined by 6 rounds of transactions with 8 inputs and 8 outputs, 6 seeds each.

- The source's neighbourhood is the 8 inputs of its transaction, and the sink's is the 8 outputs of its transaction. So 8 is the most $k$ can be.
- **Random selection:** $k = k^+ = 8$ in every seed, so no route was lost in between. With 4 walks branching 2 ways per step, $k^- = 8$ in every seed.
- **Two halves that never transact with each other:** $k = 0$, while $k^+ = 8$.
- **Two halves, 10% of transactions mixed:** $k = 8$ in 5 seeds, and 7 in the other.

## Limitations

- **Sub-transactions.** Flow relaxes sub-transaction mappings: it can split across them in ways no single mapping allows.
- **Unknown link probabilities.** Taking $P_{I,O} = 0$ when it's unknown is conservative.
- **Independent transactions.** Each transaction's probabilities are computed on their own. Intersections across transactions enter only through the minimum over sources and the [consolidation](cost_function_consolidation.md) condition.
- **What the adversary removes.** Routes are counted as disjoint in coins and flow edges, while an adversary deanonymizes users, removing all of a user's coins at once.
- **Timing and hops.** Route length and timing aren't modelled.

## Open questions

- With several sink coins, should each sink get its own share of $d$?
- Should a privileged counterparty's own coins also be omitted, since it knows where they went?
- **Known transactions.** The wallet already has the transactions next to its own coins. Should the estimates use those as they are, such as the actual $n_s$ and $n_T$, and model only the transactions it hasn't fetched?
- **Amounts and links in the analytic estimate.** Can they enter as expected capacities per coin, or only through Monte Carlo?
- How should competing spends of one coin be handled?
- **Entries and exits.** A smaller $N$ also means fewer vertices. Two counts depend on it: coins entering from transactions without randomized inputs, and outputs leaving the CoinJoin graph. Which way this moves $k$, and so whether $L$ or $\hat{N}$ is more conservative here, isn't known.

[^kishimoto]: W. Kishimoto, [*A method for obtaining the maximum multiroute flows in a network*](https://doi.org/10.1002/(SICI)1097-0037(199607)27:4%3C279::AID-NET3%3E3.0.CO;2-D), Networks 27(4), 1996.

[^aggarwal-orlin]: C. C. Aggarwal, J. B. Orlin, [*On multiroute maximum flows in networks*](https://doi.org/10.1002/net.10008), Networks 39(1), 2002.

[^chekuri-idleman]: C. Chekuri, M. Idleman, [*Congestion Minimization for Multipath Routing via Multiroute Flows*](https://doi.org/10.4230/OASIcs.SOSA.2018.3), SOSA 2018, Theorem 1.

[^karrer-newman-acyclic]: B. Karrer, M. E. J. Newman, [*Random acyclic networks*](https://arxiv.org/abs/0902.4013), 2009.

[^karrer-newman-models]: B. Karrer, M. E. J. Newman, [*Random graph models for directed acyclic networks*](https://arxiv.org/abs/0907.4346), 2009.
