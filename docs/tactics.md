---
type: concept
title: Tactics
status: draft
stale_after: 2026-11-06T00:00:00Z
---

# Tactics

🤖 A procedure for constructing the decision tree that the [cost function](optimization_framework.md) evaluates, using the terms in the [Privacy liability terms](cost_function_concrete.md) chapter. The input is the current wallet state. The output is a tree whose edges are actions and whose nodes are successor wallet states.

## 🤖 Inputs and output {#inputs-and-output}

The wallet state contains the spendable UTXO set, inflight transactions, current protocol observations and beliefs, policy parameters, and an ordered queue $Q=(q_1,\ldots,q_n)$ of pending actions. An entry may be a PSBT fragment, a lone `TxOut` for an intended payment, or an arbitrary transaction fragment. This procedure calls every such entry an *intent* without assuming that it already defines a complete transaction.

The edges of the tree are the actions listed in the [Optimization framework](optimization_framework.md) chapter, together with constructing, signing, broadcasting, or replacing a unilateral transaction, and deferring or skipping an intent.

Each path must be executable from the current wallet state. Each leaf denotes the resulting wallet state after a mutually exclusive plan, including its remaining queue and unilateral fallbacks.

🤖 The [Bottom-up construction](bottom_up_construction.md) chapter builds the tree from the leaves toward the root: it partitions the queue of intents, selects coins, constructs change, extends outcomes with order book coins, expands leaves into action sequences, and brackets and backs up their values.

## Re-evaluation

Each path down the tree is a plan, i.e. a pure strategy. Since announcements and co-spend proposals are actions like any other, they are planned as well. New alternatives can be added to the tree, or a whole new tree can be computed from any state and combined with the current one as further alternatives.

Because the tree is potentially large and costly to generate and evaluate, most of it is generated up front. It is then updated as co-spend proposals, coalition formation proposals, and the auxiliary inputs of committed transactions are learned.

🤖 The decision loop is specified in the [Mixed strategy](mixed_strategy.md) chapter. The tree is extended or rebuilt within the available compute budget, and re-evaluated with current brackets and action-duration estimates, whenever the pending-action queue changes or other new information arrives.

🤖 Relevant events include new co-spend proposals, changes to randomization terms during coalition formation, fee or time updates, and observing additional inputs before committing to particular output choices. Event-driven re-evaluation allows the wallet to exploit new information without requiring exhaustive precomputation of the partition lattice.
