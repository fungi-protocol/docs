---
type: concept
title: Privacy metrics
status: draft
stale_after: 2026-11-09T00:00:00Z
---

# 🤖 Privacy metrics

Measures computed from public data, which the [privacy liability terms](cost_function_concrete.md) take as input. Unlike the terms, they don't depend on the wallet's threat model or preferences.

- [Order book size estimation](sybil_resistance_index.md): how many candidate coins a transaction's inputs were selected from.
- [Subset sum density](subset_sum_density.md): how many subsets of a multiset of values sum into a target interval.
- [Counterfactual paths](cost_function_counterfactual_paths.md): how many times an amount could have travelled from a source coin to sink coins, along disjoint counterfactual paths.
