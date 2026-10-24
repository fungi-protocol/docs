---
type: concept
title: Mixed strategy
status: draft
stale_after: 2026-11-06T00:00:00Z
---

# 🤖 Mixed strategy

This chapter recommends how to compose a mixed strategy out of the cost of pure strategies, as set out in the [Optimization framework](optimization_framework.md) chapter, using the concrete monotone terms of the evaluation in the [Privacy liability terms](cost_function_concrete.md) chapter.

## Randomization

An adversary that knows the wallet's state and pure strategy can predict its next action. A mixed strategy randomizes over pure strategies, but its effect depends on how the observable outcomes differ.

Uniform selection among $k$ distinct leaves has $\log_2(k)$ bits of entropy over leaf identity. However, similarities between their outcomes can reduce the uncertainty over the distinctions relevant to an adversary. Sampling should give less weight to similar alternatives so that the resulting distribution is approximately uniform over materially different choices. How to measure similarity and construct this sampling distribution remains open.

## Time dependence

Every term of the cost of a pure strategy is a piecewise linear function of time, so the cost is too. The cost is a transparent sum of such terms partly so that crossing times can be solved for, and the brackets derived efficiently at predicted future times. Since the predicted times are themselves uncertain, the cost brackets can also be augmented with time brackets, i.e. bounds on those predicted times.

## Internalization

The solver searches for sequences that lead to states with greater valuation. It values the leaves first, then propagates their brackets and the tree level expectation toward the root. The tree level expectation internalizes the optionality of the leaves into their parent: it is the mean of the worst cases of the $k$ least worst leaves below that parent, since the mixed strategy chooses uniformly among them. This ignores that leaves aren't independent, as they may share actions. This reduces a plan involving many contingent future actions to comparisons among the actions available now.

Internalizing the expectations about a node's children into the node gives the node its own piecewise linear curve. Solving it for the time at which the next child is expected to have positive utility determines when to take that branch, unless new information invalidates the decision in the meantime.

## Decision loop

The wallet acts in a decision loop. Internalization is what allows this loop to be run as a greedy search, going one level down the tree per iteration: since each node already accounts for what may follow it, a look ahead of depth 1 is sufficient. Internalizing takes one pass over the tree, and doesn't need to be repeated on every iteration of the loop.

From the current state, the wallet finds the next action, i.e. the child of the root, that will become attractive soonest, waits for it to do so, and takes it. It then prunes that action's siblings, committing to the sub-tree below it. There can be multiple paths to the same outcome, for example through repeated actions or states that converge, so an implementation may share sub-trees and represent the tree as a DAG.
