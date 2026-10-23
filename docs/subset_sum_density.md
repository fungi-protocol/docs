---
type: concept
title: Subset sum density
status: draft
stale_after: 2026-11-06T00:00:00Z
---

# 🤖 Subset sum density

<!-- cspell:words Sasamoto Toyoizumi Nishimori Salas Bringmann Nakos sumsets -->

How many subsets of a multiset of effective values sum into a target interval. It's a quantity that cost function terms reuse, not a term on its own:

- The [subset sum ambiguity](cost_function_subset_sum_ambiguity.md) term checks how well the sumsets of the other users' inputs, and after the fact their outputs, cover the sumsets of the user's inputs and outputs.
- The [consolidation penalty](cost_function_consolidation.md) uses the same coverage for the user's inputs.

Dense subset sums give many readings of which inputs funded which outputs. Where the subset sums of different users' coins on the same side overlap, they also give readings of which coins belong to which user. This chapter covers how the index is estimated, and how co-spend proposals and the aggregator optimize it.

## Effective values

Effective values are computed at the [coalition formation proposal](coalition_formation.md)'s feerate $f$, with no adjustments. They form the multiset whose subset sums are counted.

- This isn't a perfect model, but it's one of the plausible scenarios the adversary must consider.
- For all the adversary knows, the feerate was the coalition formation's and every adjustment was 0. So any reading found under it is one the adversary can't rule out.

## Estimates and enumerators

- **Saddle point estimate.** [Sasamoto, Toyoizumi and Nishimori](https://arxiv.org/abs/cond-mat/0106125) estimate the number of subsets summing to a target.
  - Their grand partition function, $\prod_j (1 + e^{\mu - \beta a_j})$, counts subsets by size as well as by sum.
  - It's a product over inputs, so adding or removing coins changes only their factors. Re-solving $\beta$ and $\mu$ costs $O(n)$ per Newton step.
  - It's only valid where the number of solutions is large.
- **Distinct sums.** [Salas](https://arxiv.org/abs/2507.15511) enumerates the $U$ distinct subset sums in $O(U n^2)$ time, or $O(U n)$ expected, independent of the range. It keeps one witness subset per sum, but gives no counts.
- **Sparse convolution.** Bringmann, Fischer and Nakos convolve nonnegative vectors in time near-linear in the number of nonzero entries of the output, [with a Monte Carlo algorithm](https://arxiv.org/abs/2105.05984), and [deterministically or Las Vegas](https://arxiv.org/abs/2107.07625).
  - Convolving the count vectors of groups of coins gives the explicit sumset with its counts, not only which sums are reachable.
  - Where the distinct sums are far fewer than the range, this is cheaper than a table over the whole range.
- **Bitmaps and counts.** Bellman's algorithm over a bounded range, as implemented by the [subset sum ambiguity](cost_function_subset_sum_ambiguity.md) term.

## Co-spend proposals

- **Challenges.** A co-spend proposal can require density with challenges, and attach a reward for them in the surplus. Aggregators aren't guaranteed a payout.
  - $\rho$, the interval width and a subset size cap $q_{\max}$ are difficulty parameters. Co-spend proposals challenge whatever they like.
  - A simple client can send a single-UTXO proposal with a high density requirement and a large surplus, delegating the search over the order book to the aggregator.
- **Perturbation** ([fungi-protocol/docs#75](https://github.com/fungi-protocol/docs/issues/75)). Given the convolution implied by a co-spend proposal, add desired values, e.g. standard denominations, and check whether the set becomes dense enough.
  - Simulated annealing makes the same moves, adding or removing a coin. It can generate co-spend proposals for the decision tree, and optimize coin selection.
  - Unlike branch and bound, it needs no bounds on the cost function.

## Aggregator

The aggregator searches over combinations of co-spend proposals, for ones whose inputs solve each other's challenges easily.

- **Terms.** A combination's terms must intersect. The aggregator determines the feerate and the other concrete parameters from the intersection, and the feerate fixes the effective values.
- **Score.** The interval is only known once the coalition formation proposal is hashed. So a challenge is easy if density is high across its whole range of interval positions, by the saddle point estimate.
  - It respects $q_{\max}$, since it counts by size.
  - It doesn't check disjointness. The prover does.
- **Moves.** Add or remove a co-spend proposal, as in simulated annealing.
  - Seed with proposals that offer large surpluses.
  - Prefer additions that raise the score in the most challenge ranges per unit of weight. Proposals whose challenge ranges overlap reinforce each other.
  - Each addition brings its own challenges, which must be easy too.
  - Accept a combination once every challenge is easy. Among those, prefer larger rewards within the weight limit.
- **Grinding.** Rehashing for an easier interval is acceptable. Finding better coins to aggregate with is easier.
- **Prover.** Once the combination is fixed and hashed, solve each challenge interval $I = [c, c + w]$ for $\rho$ disjoint subsets of the inputs. If it fails, perturb the combination and rehash.
  1. **Bounds.** Give up if $\rho > \lfloor \sum a / c \rfloor$, or if $\rho > \lfloor n / q_{\min} \rfloor$, where $q_{\min}$ is the number of largest values needed to reach $c$.
  2. **Singletons** by binary search. **Pairs** by two pointers, then a maximum matching.
  3. **Larger subsets.** Run Bellman's algorithm over the unused coins, storing per cell the smallest subset size up to $q_{\max}$ and the last item. Extract a smallest subset, remove it, and repeat.
     - Round values down to multiples of $\Delta$, and target $[c, c + w - q_{\max} \Delta]$, so exact sums stay in $I$.
  4. **Repair.** If stuck below $\rho$, move or swap coins between subsets and the unused pool. Stop at $\rho$.
- **Encoding.** One label per input in $\{0, \dots, \rho\}$, with 0 for unused. The subsets are disjoint by construction, and verification is $O(n)$.
