---
okf_version: "0.2"
---

* [Collaborative transaction privacy](collaborative_txn_privacy.md) - Under review in #7.

# Protocol Suite

* [Overview](overview.md) - Collaborative transaction construction, privacy, fault tolerance and coalition formation.
* [Abstract transport interfaces](transport-interfaces.md) - Send, receive and bidirectional channels, the kinds of messaging the protocol needs, and broadcast built from peer to peer channels.
* [🤖 Peer and broadcast channels](channels.md) - Broadcast to a group or to the world, built by gossip over peer to peer channels.
* [Contacts and payment messaging](contacts.md) - What interactive payments need from peer to peer messaging between payer and payee.
* [Market-based coalition formation](coalition_formation.md) - Under review in #18.
* [Transaction construction](transaction-construction.md) - Content and state synchronization, the phases, the optimistic and recovery tracks, and what the validity proofs enforce.
  * [Block DAG](block-dag.md) - The validator blocks both tracks share, with their objects, nonce commitments and equivocation evidence, genesis, causal order and frontiers.
  * [🤖 Optimistic track: blocks and phase states](optimistic-track.md) - Unanimity and phase closure on the optimistic track, phase by phase.
  * [Recovery track](recovery-track.md) - How a stalled phase of the optimistic track turns into a recovery coalition formation proposal. Draft.
* [🤖 Peer set reconciliation](set-reconciliation.md) - Requesting hash preimages, naive reconciliation, unordered sets, and range and rateless reconciliation as optimizations.
* [🤖 Protocol messages](protocol-messages.md) - The messages peers exchange, who sends them, when, and what each requires of its channel.
* [🤖 Validity proofs](validity-proofs.md) - Selected design: proving outputs are covered by inputs through anonymous allocation registration.

# Privacy Optimization Strategy

* [Optimization framework for Bitcoin wallets](optimization_framework.md) - Under review in #15.
* [🤖 Pure Strategy Evaluation](pure_strategy_evaluation.md) - How the cost of a pure strategy is evaluated: the structure of the cost function, and its privacy liability terms.
  * [🤖 Cost function structure](cost_function_structure.md) - The structure shared by the family of cost functions that evaluate pure strategies: time dependence, linear combination of terms and bracketing.
  * [🤖 Privacy liability terms](cost_function_concrete.md) - What each privacy liability term of the cost function is for: the risk it prices, what it encourages, and how it relates to the others.
    * [Randomized selection and Sybil resistance](cost_function_randomized_selection.md) - Selection preferences that randomize which coins are co-spent, a Sybil resistance index measuring their effect, and a provenance term valuing coins by it.
    * [🤖 Sybil resistance index](sybil_resistance_index.md) - A conservative lower bound on the number of candidate coins a transaction's inputs were selected from, and how to find the block hash they were selected with.
    * [🤖 Others' inputs subset sum density](subset_sum_density.md) - Outline of subset sum density, how it's estimated, and how co-spend proposals and the aggregator optimize it.
    * [🤖 Own inputs or outputs subset sum ambiguity](cost_function_subset_sum_ambiguity.md) - Outline of a concrete cost function term for the subset sum ambiguity of output values.
    * [🤖 Max flow based counterfactual path estimation](cost_function_counterfactual_paths.md) - Outline of a cost function term that estimates disjoint counterfactual paths with one max flow, and labels coins impervious to intersections.
    * [🤖 Consolidation penalty](cost_function_consolidation.md) - Outline of a concrete cost function term penalizing consolidation unless the subset sums are very dense and the coins are impervious to intersections.
    * [🤖 Sibling output penalty](cost_function_siblings.md) - Outline of a concrete cost function term penalizing spending sibling outputs together.
* [Tactics](tactics.md) - Generating the decision tree bottom up, with coin selection and change decomposition, and when to re-evaluate it.
  * [Bottom-up construction](bottom_up_construction.md) - Building the decision tree from the leaves: partitions of the intent queue, coin selection, change construction, order book coins, action sequences, and bracketing.
* [🤖 Mixed strategy](mixed_strategy.md) - How to compose a mixed strategy from the cost of pure strategies: randomization, time dependence, internalization and the decision loop.

# BIP Drafts

* [PSBT Scrubber](bip-drafts/scrubber.md) - Which PSBT fields can be shared with trusted and untrusted parties such that privacy is preserved.
* [Concurrent PSBT Construction](psbt-concurrent.md) - Under review in #16.
