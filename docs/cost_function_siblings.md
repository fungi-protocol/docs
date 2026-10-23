---
type: concept
title: Sibling output penalty
status: draft
stale_after: 2026-11-06T00:00:00Z
---

# 🤖 Sibling output penalty

A privacy liability term of the [cost function](optimization_framework.md). Spending outputs of the same transaction together is wasteful, and more indicative of common ownership than spending unrelated coins together. It's penalized heavily.

## Definition

- $I$: the own inputs of the transaction under consideration.
- For each earlier transaction $T$, $j_T$ is the number of its outputs in $I$.
- **Liability.** $\ell_s = \sigma \sum_T \max(0, j_T - 1)$, with $\sigma$ large.
- Neither the labels from the [Consolidation penalty](cost_function_consolidation.md) chapter nor [subset sum density](subset_sum_density.md) reduce it. Amounts can explain the values, but not two users spending outputs of one transaction together.

## In the decision tree

- It's a privacy-related term.
- **Worst case:** $\ell_s$ as defined. It depends only on the own inputs.
- **Best case:** $\ell_s = 0$, which is used for pruning.
- $\ell_s \ge 0$ is unbounded, so it can exceed the remaining budget. The action is then taken only if other terms, e.g. a payment deadline, outweigh it.
- It applies to every own output of the transaction. The discount scales with value, not with the number of outputs.

## After confirmation

- $\ell_s$ is fixed once the inputs are chosen.
- Once the action is taken, the resulting coins' liability is capped at 1.

## Open questions

- Should $\ell_s$ extend to coins with a common ancestor further back?
