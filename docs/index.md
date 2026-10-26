---
okf_version: "0.2"
---

# Problem Statement

* [Collaborative transaction privacy](collaborative_txn_privacy.md) - Challenges for privacy in multiparty transaction settings, from PayJoin to CoinJoin.

# Protocol Suite

* [Overview](overview.md) - Collaborative transaction construction, privacy, fault tolerance and coalition formation.
* [Abstract transport interfaces](transport-interfaces.md) - Send, receive and bidirectional channels, the kinds of messaging the protocol needs, and broadcast built from peer to peer channels.
* [🤖 Peer and broadcast channels](channels.md) - Broadcast to a group or to the world, built by gossip over peer to peer channels.
* [Contacts and payment messaging](contacts.md) - What interactive payments need from peer to peer messaging between payer and payee.
* [Market-based coalition formation](coalition_formation.md) - Bilateral negotiation and aggregation of co-spend proposals into a unanimously accepted coalition formation proposal.
* [Transaction construction](transaction-construction.md) - Content and state synchronization, the phases, the optimistic and recovery tracks, and what the validity proofs enforce.
  * [Block DAG](block-dag.md) - The validator blocks both tracks share, with their objects, nonce commitments and equivocation evidence, genesis, causal order and frontiers.
  * [🤖 Optimistic track: blocks and phase states](optimistic-track.md) - Unanimity and phase closure on the optimistic track, phase by phase.
  * [Recovery track](recovery-track.md) - How a stalled phase of the optimistic track turns into a recovery coalition formation proposal. Draft.
* [🤖 Peer set reconciliation](set-reconciliation.md) - Requesting hash preimages, naive reconciliation, unordered sets, and range and rateless reconciliation as optimizations.
* [🤖 Protocol messages](protocol-messages.md) - The messages peers exchange, who sends them, when, and what each requires of its channel.
* [🤖 Validity proofs](validity-proofs.md) - Selected design: proving outputs are covered by inputs through anonymous allocation registration.

# Privacy Optimization Strategy

* [Optimization framework for Bitcoin wallets](optimization_framework.md) - Objective costs, privacy liabilities and payment utility as the basis for automated wallet decisions.
* [🤖 Pure Strategy Evaluation](pure_strategy_evaluation.md) - How the cost of a pure strategy is evaluated: the structure of the cost function, its privacy liability terms, and the privacy metrics they take as input.
  * [🤖 Cost function structure](cost_function_structure.md) - The structure shared by the family of cost functions that evaluate pure strategies: time dependence, linear combination of terms and bracketing.
  * [🤖 Privacy liability terms](cost_function_concrete.md) - The privacy objectives assessed by each liability term and how the terms interact.
    * [Randomized selection](cost_function_randomized_selection.md) - Selection preferences that randomize which coins are co-spent, and a lower bound on the size of the order book they were selected from.
    * [🤖 Sybil resistance](cost_function_sybil_resistance.md) - Observed resource requirements and sampled cost estimates assessed against the user's threat model.
    * [🤖 Subset sum ambiguity](cost_function_subset_sum_ambiguity.md) - Outline of a concrete cost function term for the subset sum ambiguity of input and output values.
    * [🤖 Consolidation penalty](cost_function_consolidation.md) - Outline of a concrete cost function term penalizing consolidation unless the subset sums are very dense and the coins are impervious to intersections.
    * [🤖 Sibling output penalty](cost_function_siblings.md) - Outline of a concrete cost function term penalizing spending sibling outputs together.
  * [🤖 Privacy metrics](privacy_metrics.md) - Measures computed from public data that the privacy liability terms take as input.
    * [🤖 Order book size estimation](sybil_resistance_index.md) - A relatively conservative estimate of a lower bound on the number of candidate coins a transaction's inputs were selected from, and how to find the block hash they were selected with.
    * [🤖 Subset sum density](subset_sum_density.md) - How many subsets of a multiset of effective values sum into a target interval, a quantity the subset sum ambiguity and consolidation terms reuse, how it's estimated, and how co-spend proposals and the aggregator optimize it.
    * [🤖 Counterfactual paths](cost_function_counterfactual_paths.md) - Outline of how to count disjoint counterfactual paths with one max flow, and how to estimate the count.
* [🤖 Mixed strategy](mixed_strategy.md) - How to compose a mixed strategy from the cost of pure strategies: randomization, time dependence, internalization and the decision loop.
* [Tactics](tactics.md) - Generating the decision tree bottom up, with coin selection and change decomposition, and when to re-evaluate it.
  * [Bottom-up construction](bottom_up_construction.md) - Building the decision tree from the leaves: partitions of the intent queue, coin selection, change construction, order book coins, action sequences, and bracketing.
  * [Radix CoinJoin Denominations](Denominations_and_gap_size_distributions.ipynb) - Why small Hamming weight denominations suit CoinJoin outputs, and how closely sums of a few of them approximate arbitrary amounts.

# BIP Drafts

* [PSBT Scrubber](bip-drafts/scrubber.md) - Which PSBT fields can be shared with trusted and untrusted parties such that privacy is preserved.
* [Concurrent PSBT Construction](psbt-concurrent.md) - PSBT fields and rules for combining partial transactions and terminating concurrent construction.
