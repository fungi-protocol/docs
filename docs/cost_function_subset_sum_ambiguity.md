---
type: concept
title: Subset sum ambiguity
status: draft
stale_after: 2026-11-05T00:00:00Z
---

# 🤖 Subset sum ambiguity

<!-- cspell:words sumsets binom quotienting -->

A privacy liability term of the [cost function](optimization_framework.md). It applies the techniques of the [subset sum density](subset_sum_density.md) chapter to the user's own coins, for two measures:

- **Inputs.** How well the sumset of the other users' inputs covers the sumset of the user's inputs.
- **Outputs.** How well the sumset of the other users' inputs covers the sumset of the user's outputs.

Once the transaction has been fully built, both are also checked against the sumset of the other users' outputs. If both are well covered for every combination, the [sub-transaction](collaborative_txn_privacy.md) model is underdetermined.

Given the wallet state and a transaction under consideration, it checks both for a proposed output decomposition, relative to the other users' inputs known so far. The other users' sumsets are bounded in degree, so they stay small, and the user's own are complete. It's cheap enough to evaluate for many decompositions.

## Sub-transaction ambiguity

A sub-transaction mapping, as in the models of Maurer et al. and LaurentMT described in [Collaborative transaction privacy](collaborative_txn_privacy.md), partitions a transaction's inputs and outputs into sub-transactions that each balance. Given one valid mapping, others can be reached by transformations that preserve that invariant. Ordered by generality, they break counting the mappings into a hierarchy of complexity:

- **1:1 exchange.** If an output denomination has multiplicity $m$, the $m!$ permutations of the equal outputs all preserve the mapping. With one copy of the denomination per sub-transaction, quotienting by these permutations is trivial.
- **n:m exchange.** Substitute a set of inputs or outputs for another. With effective values and costs at an estimated feerate, this preserves the invariant in a model that admits non-zero fees.
- **Merge and re-partition.** The most general transformation that's still constructive. Merge some of the mapping's sub-transactions and partition them again, or make exchanges that break the invariant temporarily. It's a walk through the space of partitions and back into the sub-space of sub-transaction mappings.
- **Enumeration.** As in Maurer et al., the space can be enumerated by brute force.

Multiplicity makes 1:1 exchange trivial, but that isn't enough for privacy. This term climbs only as high as n:m exchange, which reduces to subset sum. Subset sum density makes n:m exchange underdetermined as well, without the generality or the computational cost of the last two. The coverage checks below concern n:m exchange of the sums only the wallet knows: its own inputs and outputs. If those are sufficiently underdetermined, they give a lower bound on the number of sub-transaction mappings relevant to the wallet, and on the entropy of Maurer et al.'s link probabilities $p_{II}$, $p_{OO}$ and $p_{IO}$.

## Notation

For a multiset $Z$ of values:

- $\Sigma(Z)$ is the set of its subset sums, over non-empty subsets.
- $\Sigma_{\le d}(Z)$ is the set of sums of at most $d$ of its elements.
- $A \sqsubseteq^{+}_\varepsilon B$: every $s \in A$ has some $t \in B$ with $s \le t \le s + \varepsilon$.
- $A \sqsubseteq^{-}_\varepsilon B$: every $s \in A$ has some $t \in B$ with $s - \varepsilon \le t \le s$.
- A single such $s$ is **covered**.

## Inputs

- $f$: the feerate of the [coalition formation proposal](coalition_formation.md). Effective values are [fixed](subset_sum_density.md#effective-values) at $f$.
- $X$: effective values of the other users' inputs known so far, positive values only.
- $Y$: effective costs of the other users' outputs. They're only known once the transaction has been fully built, though not necessarily signed. By then $O$ is fixed. While decisions are evaluated, $Y$ is empty.
- $I$: the own inputs, as effective values.
- $O$: the user's outputs, as effective costs.
  - In the decision tree, a proposed decomposition.
  - Once the transaction has been fully built, the complete multiset of the user's outputs.
- Parameters:
  - $d$: the degree bound for the other users' sumsets, e.g. 2 or 3 for large transactions;
  - $\varepsilon$: the slop;
  - $\varphi$: the covered fraction at which the liability reaches 0;
  - $\theta$: the number of doublings of $f_c$ over which the liability falls from 1 to 0.

## Definition

1. **Other users' sumsets.** $\Sigma_{\le d}(X)$, and $\Sigma_{\le d}(Y)$ once $Y$ is known. Either can be a bitmap, or count the subsets per sum.
   - Whether coverage should require more than one subset per sum depends on the threat model, the computational resources and the value range.
2. **Own sumsets.** $\Sigma(I)$, and $\Sigma(O)$ once $O$ is proposed.
3. **Coverage.** Effective values are at least effective costs, so each check is one-sided.
   - While decisions are evaluated, check $\Sigma(I) \sqsubseteq^{+}_\varepsilon \Sigma_{\le d}(X)$ and $\Sigma(O) \sqsubseteq^{+}_\varepsilon \Sigma_{\le d}(X)$. The other users' inputs can plausibly combine to the same balance as the user's coins, or slightly more.
   - After the fact, also check $\Sigma(I) \sqsubseteq^{-}_\varepsilon \Sigma_{\le d}(Y)$. Sums of $Y$ are total effective costs, so they're at most the sums of $I$.
   - And $\Sigma(O) \sqsubseteq^{-}_\varepsilon \Sigma_{\le d}(Y)$. A sum of $Y$ is a combination of the other users' outputs that could be interchanged with the user's outputs of that sum, so it's at most their actual sum.
4. **Covered fraction.** For each own coin $c$ in $I$ or $O$, $f_c$ is the fraction of the subsets of its side that contain $c$ and whose sums are covered.
5. **Liability.** $\ell(c) = \text{clamp}(\log_2(\varphi / f_c) / \theta, 0, 1)$.
   - It's 0 once $f_c \ge \varphi$.
   - It falls by $1/\theta$ per doubling of $f_c$.

## Implementation

### Tables

Built once per transaction and shared by all decompositions:

- $K_X$: for each sum up to the range, the smallest number of elements of $X$ that reach it, if at most $d$.
  - Apply $K_X[i] \gets \min(K_X[i], K_X[i - a] + 1)$ per input $a$, from the top down.
  - Counting per sum works the same way, with one layer per subset size.
  - $\Sigma_{\le d}(X)$ has at most $\sum_{h \le d} \binom{|X|}{h}$ elements. Where that's far fewer than the range, enumerate it explicitly, or use a [sparse convolution](subset_sum_density.md#estimates-and-enumerators), and look sums up by binary search.
- $K_Y$: the same over $Y$, once it's known.
- $\Sigma(I)$: enumerated once per transaction. $\Sigma(O)$: enumerated per decomposition. Both are small.
- **Lookups:** a prefix count over the table answers whether the window $[s, s + \varepsilon]$ holds a sum, or $[s - \varepsilon, s]$ against $Y$.
- **Rounding:** the windows tolerate rounding, e.g. to multiples of 128 sats. Round in the direction that counts no implausible substitution.
  - Against $X$, round the values of $X$ down and the own sums up.
  - Against $Y$, round the values of $Y$ up and the own sums down.
  - The window then widens by at most $d + 1$ rounding units.
- **Range:** from 0 to the largest own sum plus $\varepsilon$. Double it and rebuild if needed. Skip inputs that are too large to fit.

### Updates

- Each auxiliary input is one more pass over $K_X$. Once the transaction has been fully built, each of the other users' outputs is one more pass over $K_Y$. The order doesn't matter.
- Deduplicate inputs by outpoint and outputs by output id.
- Removing a value needs counts, or a rebuild.

### Per decomposition

- Look up each sum of $\Sigma(O)$. The results for $\Sigma(I)$ are shared by all decompositions.
- **Satisficing stops the work early:**
  - a coin, once $\ell(c) = 0$;
  - a decomposition, once all of its outputs have.

### Radix denominations

These are inputs with nominal value $c \cdot b^i$:

- $b = 2$, $c = 1$;
- $b = 3$, $c \in \{1, 2\}$;
- $b = 10$, $c \in \{1, 2, 5\}$.

They're grouped by effective value $v$, with multiplicity $m_v$.

- **Multiplicity:** one pass per group, as a sliding window along each residue class mod $v$.
- **Contiguity:** sort the coins and keep a running sum $R$. Accept each next coin while it's $\le R + \varepsilon$, starting from a coin $\le \varepsilon$.
  - Every sum $\le R$ is then covered without the tables.
  - It may use any number of coins, so it only applies when $d$ is at least the number of coins accepted.
  - Keeping $m_v - r$ coins per value gives robustness to $r$ removals per value.

## In the decision tree

- It's a privacy-related term.
- **Worst case:** only the inputs known so far count. $X$ is a lower bound, and auxiliary inputs are learned later. The other users' outputs aren't known until the transaction has been fully built, so only $\Sigma_{\le d}(X)$ is checked.
- **Best case:** $\ell(c) = 0$, which is used for pruning.
- Every participant, including the aggregator in that role, evaluates [co-spend proposals](subset_sum_density.md#co-spend-proposals) with this term, deciding whether to propose a generated one or to accept an incoming one.
  - A generated proposal can carry density challenges, with a reward in the surplus.
  - Perturbing a proposal adds values to the tables, one pass each.
- $\ell(c) \in [0, 1]$.

## After confirmation

This is the analysis that contributes privacy gains, and that uses the budget.

- All inputs and outputs are known, so the checks against $\Sigma_{\le d}(Y)$ apply.
- **Coalition formation proposal known:** evaluate at its $f$, which continues the decision tree's chain. Also evaluate at the final feerate, which is a second scenario.
- **Recovery from seed:** evaluate at the final feerate only.

## Monotonicity

- The decision tree's estimate is the same definition restricted to the lower bound $X$, with $Y$ empty.
- Learning inputs or outputs only adds sums to $\Sigma_{\le d}(X)$ and $\Sigma_{\le d}(Y)$, so covered sums stay covered and $\ell(c)$ can only fall.
- This requires the same $f$, the same realized $O$, and the same parameters.

## Open questions

- Is $\varepsilon$ absolute, or relative to the target? Does it include adjustments?
- After the fact, is a sum covered if either $\Sigma_{\le d}(X)$ or $\Sigma_{\le d}(Y)$ covers it, or are the two fractions separate?
