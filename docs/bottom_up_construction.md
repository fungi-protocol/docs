---
type: concept
title: Bottom-up construction
status: draft
stale_after: 2026-11-06T00:00:00Z
---

# Bottom-up construction

The tree is built bottom up, starting with complete outcomes and working back towards the immediate actions that would lead to them:

1. Partition the queue of intents heuristically. Each partition is an outcome: a set of batches to execute.
2. For each outcome, select coins batch by batch, possibly shuffling. Coin selection may optimize or be fully randomized, and interactive incoming payments can be treated as pseudo-inputs. This ensures that the outcome has a positive surplus and can be executed.
3. Decompose each surplus into radix denominations, enumerating the possibilities by brute force.
4. Extend outcomes by selecting coins from the order book.

This generates many independent outcomes, each complete and balanced, each made up of disjoint batches. Typically there will be one greedy batch, or one small batch for a unilateral fallback if an intent becomes urgent.

🤖 Construct the tree from the leaves toward the root. First enumerate candidate outcomes: complete allocations of queued intents to transaction batches or unilateral fallbacks, together with concrete inputs, outputs, change structures, and protocol contingencies. Then derive action sequences that realize those outcomes from the current wallet state. While working upward, merge reverse paths whenever they share the same predecessor action. Equivalently, factor common prefixes of the root-to-leaf action sequences so that shared, less-committal actions appear closer to the root.

## 🤖 1. Seed partitions of the pending-action queue {#1-seed-partitions-of-the-pending-action-queue}

A partition $\pi$ of $Q$ groups intents that the wallet plans to realize together. Each part is one batch; distinct parts are separate transactions or sessions. The partition-refinement order captures every way the same intents may be realized together or separately. Its bottom element is the discrete partition of singleton batches, and its top element is the indiscrete partition containing the entire queue in one batch.

Time-dependent payoff curves constrain this lattice. If an intent is elapsing and its expected multiparty delay would make it irrational, move it to an executable unilateral fallback or skip it. The residue remains eligible for batching. This avoids the false dichotomy between doing the whole queue unilaterally and putting the whole queue into one multiparty transaction: one leaf may contain several multiparty batches, several unilateral actions, and deferred intents.

Seed candidate partitions as follows:

1. Always add the bottom and top elements after applying feasibility and time filters.
2. If $n$ is small enough, add the whole partition-refinement lattice. The number of partitions is the Bell number $B_n$, so exhaustive enumeration is reserved for small queues.
3. Otherwise, seed at least one maximal path from bottom to top. Starting at the bottom, repeatedly merge the pair of parts with the greatest priority according to objective cost reduction, coin-selection feasibility, and time constraints. Never backtrack along this path. Its $n$ partitions provide $O(n)$ partition seeds and a linear-space baseline for this stage. Later coin-selection and change alternatives may expand each seed into several outcomes and leaves.
4. Prefer several paths when resources allow. Vary priority order or retain several near-best merges at selected levels so the seed is a tree rather than only a list.
5. Spend remaining precomputation budget on additional partitions. Simulated annealing, randomized merge and split moves, beam search, or another combinatorial search may sample the omitted lattice. During a live protocol session, repeat this search with newly revealed information and score the sampled partitions directly.

## 🤖 2. Allocate coin selections within each partition {#2-allocate-coin-selections-within-each-partition}

For every seeded partition, allocate inputs jointly across all of its batches. A simple implementation processes the batches successively with an ordinary coin-selection algorithm while removing each selected UTXO from the set available to later batches. The order is part of the candidate. No UTXO may appear in two batches of the same partition.

Repeat allocation with different batch orders, coin-selection randomization, or near-optimal solutions so that each batch can have several candidate coin selections. Reject an allocation unless every batch is balanced: its selected input value must exceed the effective cost of its intended outputs and other mandatory transaction fields.

Positive balance establishes feasibility, not rationality. Before expanding an allocation, reject any batch whose excess implies an unreasonable feerate or whose objective cost can never be offset by its payoff curve. Also reject any choice that the internalized privacy model marks as prohibited, encoded as an infinite privacy liability: by construction such a choice is never rational, regardless of nominal fee savings. Finite privacy harms remain priced terms in the wallet-state valuation and may trade off against other costs.

## 🤖 3. Recover surplus with change construction {#3-recover-surplus-with-change-construction}

Coin selection generally leaves a positive balance that would otherwise be overpaid in fees. Change construction recovers that value and therefore minimizes the batch's objective cost.

In the Radix CoinJoin setting, expand each batch into a decision tree of Radix CoinJoin decompositions. Keep at least $k$ acceptable decompositions selected uniformly at random when at least $k$ exist. A partial decomposition may also be retained when later information is needed to finish it.

In a net-settlement setting, the residual balance may require only an ordinary self-spend output. That produces a degenerate decision tree with one choice and no decomposition decision.

## 4. Extend outcomes with order book coins

Order book coins that would increase the number of counterfactual paths into the wallet's new outputs are especially valuable (see [Counterfactual paths](cost_function_counterfactual_paths.md)). However, a co-spend proposal made from the wallet's input that the paths are added to, naming such a coin, links the two, unless such proposals are already common. An outcome may still prefer such a selection, but the cost function should penalize co-spend proposals that leak the link in this way.

🤖 Such a coin adds paths as a co-input when it descends from the origins of the wallet's own inputs.

## 5. Expand leaves into action sequences

🤖 For each surviving outcome, construct one or more sequences of atomic actions that lead from the current wallet state to that leaf. A multiparty batch may require initiating a session, sending co-spend proposals, adding inputs, observing other participants' inputs, and adding outputs. A fallback batch may instead require constructing and broadcasting a unilateral transaction. Attach the estimated duration and information revealed by each edge.

🤖 When several leaves share an action, factor that action into a common ancestor. Choose the factoring and edge order to preserve options: given each leaf's bracket, put the least committal and least revealing common actions nearest the root. For example, if one or two coins appear in almost every partition, using them in co-spend proposals can leave more of the generated forest addressable than revealing outputs or committing rarer inputs first.

The coins these outcomes share then guide the structure of the tree, as does each coin's luck, both now and at the next block, since the randomness beacon can be a block hash at some depth below the tip rather than the tip itself. Actions are scheduled least committal first, so the actions shared by the most outcomes end up nearest the root.

Within a batch, inputs are added before outputs, and signatures come last. Inputs named in co-spend proposals are scheduled early, in particular those compatible with the most favorable outcomes. *Auxiliary* inputs, which aren't named in any co-spend proposal, are added using the weight unit credits of these initial inputs. Whether to include them can be decided after observing the other users' initial inputs, i.e. the full list of UTXOs in the coalition formation proposal.

The expected durations of steps can be annotated along each path. This takes the time dependence of the leaves into account, so that actions are scheduled early enough.

🤖 Time-dependent payoff curves participate in this construction. An action sequence is admissible only if its cumulative estimated duration leaves every dependent branch rational at the time it would be taken. A branch may end in a unilateral fallback when coalition formation outlives an intent's multiparty window.

## 🤖 6. Bracket and back up values {#6-bracket-and-back-up-values}

Evaluate every leaf under currently available information. A leaf is a pure strategy. The [Optimization framework](optimization_framework.md) chapter scores it as a family of piecewise linear time-dependent curves, one per term, each flagged as privacy-related or not, evaluated at a point and summed. Objective costs, including blockspace, fees, and change, are normally concrete. A leaf's wallet state can itself be valued by imagining a unilateral transaction spending all of its coins right after, and taking that transaction's consolidation penalty and objective costs, as in the [Consolidation penalty](cost_function_consolidation.md) chapter.

Terms that depend on other participants' future input or output choices are bracketed:

- **Worst case:** no other party contributes value, apart from co-spend adjustments in effect.
- **Best case:** every privacy liability is 0. It's used for pruning.

Back the leaf values up through each action, shifting successor payoff curves by the action's estimated duration, and adding the immediate action cost at each edge. These backups internalize future consequences, so the action at the root isn't myopic. Each parent is valued by its tree level expectation, as in the [Optimization framework](optimization_framework.md) chapter.

Once the wallet commits an action, prune its incompatible siblings. Every action discards parts of the forest, so early actions that preserve many acceptable descendants are preferred.
