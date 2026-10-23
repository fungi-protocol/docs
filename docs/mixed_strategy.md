---
type: concept
title: Mixed strategy
status: draft
stale_after: 2026-11-06T00:00:00Z
---

# 🤖 Mixed strategy

This chapter recommends how to compose a mixed strategy out of the cost of pure strategies, as set out in the [Optimization framework](optimization_framework.md) chapter, using the concrete monotone terms of the evaluation in the *Concrete cost function* chapter.

## Randomization

The wallet doesn't simply follow the best pure strategy. If it did, an adversary able to predict the wallet's state could also predict its choices. Instead it plays a *mixed strategy*: it chooses uniformly at random among the $k$ best pure strategies that are sufficiently dissimilar, where $k$ is a parameter. This adds noise to the wallet's revealed preferences. The decision tree models the pure strategies explicitly, and the wallet randomizes over them. How to measure dissimilarity is still open. An alternative is to sample non-uniformly from a larger set, with lower probability for similar choices.

## Time dependence

Every term of the cost of a pure strategy is a piecewise linear function of time, so the cost is too. The cost is a transparent sum of such terms partly so that crossing times can be solved for, and the brackets derived efficiently at predicted future times. Since the predicted times are themselves uncertain, the cost brackets can also be augmented with time brackets, i.e. bounds on those predicted times.

## Internalization

The solver searches for sequences that lead to states with greater valuation. It values the leaves first, then propagates their brackets and the tree level expectation toward the root. The tree level expectation internalizes the optionality of the leaves into their parent: it is the mean of the worst cases of the $k$ least worst leaves below that parent, since the mixed strategy chooses uniformly among them. This ignores that leaves aren't independent, as they may share actions. This reduces a plan involving many contingent future actions to comparisons among the actions available now.

Internalizing the expectations about a node's children into the node gives the node its own piecewise linear curve. Solving it for the time at which the next child is expected to have positive utility determines when to take that branch, unless new information invalidates the decision in the meantime.

## Greedy loop

This makes a simple greedy loop sufficient. From the current state, the wallet finds the next action, i.e. the child of the root, that will become attractive soonest, waits for it to do so, and takes it. It then prunes that action's siblings, committing to the sub-tree below it. There can be multiple paths to the same outcome, for example through repeated actions or states that converge, so an implementation may share sub-trees and represent the tree as a DAG.
