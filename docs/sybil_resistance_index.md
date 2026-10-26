---
type: concept
title: Order book size estimation
status: draft
stale_after: 2026-11-06T00:00:00Z
---

# 🤖 Order book size estimation

A relatively conservative estimate of a lower bound $L$ on the number of candidate coins a transaction's inputs were selected from, and a [median estimate](#median-estimate) $\hat{N}$ of that number. Both measure the effect of the selection preferences in the [randomized selection](cost_function_randomized_selection.md) chapter. The [Sybil resistance](cost_function_sybil_resistance.md) term uses $L$, and the [Counterfactual paths](cost_function_counterfactual_paths.md) chapter uses $\hat{N}$ for its degree sequence.

## Candidates

**Candidates** are the coins whose owners are active and offering them in the order book. $N$ is how many there are. It isn't directly observable.

- Under the actual block hash $t$, the candidates' hashes are uniform. The selected inputs are a subset. If the selection depends on the hashes, the subset deviates from uniform, which bounds $N$ from below, much like estimating the hash rate from proofs of work.
- Candidates must be fixed before $t$ is known.
- Each candidate is one draw. Spending the same coin twice isn't a second draw.
- To exhibit the deviation, an adversary must control all the candidates, not just the selected coins.

## Hashes

- $x_i = H(t, i)$ for each input outpoint $i$. $H$ is a tagged hash, truncated to 64 bits and read as an integer modulo $Q = 2^{64}$, so the $x_i$ are points on a circle.
- Truncation keeps the guarantees below: the truncated hashes are uniform on the grid of $Q$ points, and the extra grid unit per span covers the rounding.

## Pool size bound

For the $n$ input hashes of a transaction and a confidence parameter $\delta$:

1. **Spans.** Sort the hashes around the circle. An $m$-span runs from a hash to its $m$-th successor. Its width is the distance between them, plus one grid unit.
2. **Sums.** For each $1 \le m \lt n$ and $1 \le r \le n/m$, $T_{m,r}$ is the smallest total width of $r$ spans with disjoint interiors. Spans may share endpoints. Let $\tau_{m,r} = T_{m,r} / Q$.
   - For $m = 1$, this is the sum of the $r$ smallest gaps.
   - Larger $m$ detects groups of nearby hashes.
3. **Tail bound.** For a hypothetical pool of $M$ candidates:
   $$
   q_{m,r}(M) = \min\left(1, \frac{M^{r(m+1)} \, \tau_{m,r}^{rm}}{r! \, (rm)!}\right)
   $$
4. **Score.** With weights that sum to 1 over all $m, r \ge 1$:
   $$
   S(M) = \sum_{m,r} \frac{q_{m,r}(M)^{-1/2} - 1}{m(m+1)r(r+1)}
   $$
5. **Bound.** $L$ is the smallest integer $M \ge n$ with $S(M) \lt 1/\delta$.

### Why it's conservative

$P(L \gt N) \le \delta$ for every selection strategy. This includes choosing the inputs, and how many, after seeing the hashes, in order to maximize $L$.

- **One placement.** In a uniform pool of $M$, the total of $r$ fixed disjoint blocks of $m$ gaps is $\text{Beta}(rm, M - rm)$. Its lower tail is at most $(M \tau)^{rm} / (rm)!$.
- **Every placement.** There are at most $M^r / r!$ ways to place the blocks. A union bound covers taking the minimum after seeing the pool.
- **Subsets.** Each selected $m$-span contains at least $m$ gaps of the full pool. So no subset has smaller totals than the pool itself. The extra grid unit per span covers rounding hashes to integers.
- **Combining.** Each $q$ is a conservative p-value, so $E[q^{-1/2} - 1] \le 1$. By Markov's inequality, $P(S(N) \ge 1/\delta) \le \delta$. The terms may be dependent.

### Properties

- **Monotone.** At a fixed beacon and $\delta$, adding inputs never lowers $L$. So withholding coins from a fixed pool can't raise it.
- **Symmetric.** No position on the circle is special. Rotating or reflecting the hashes doesn't change $L$, so it doesn't matter which hashes count as lucky.
- **All inputs.** Every input's hash enters through the spans.
- **Integer arithmetic.** Each weighted term is rounded down to a multiple of $2^{-64}$, using integer square roots. Rounding only lowers the score, so it keeps both guarantees.
- **Caps.** Leaving out the terms above a fixed $m$ or $r$ keeps both guarantees: their weight goes unused. It costs power.
- **Cost.** $O(n^3)$ arithmetic operations over all $m$, on integers of $O(n (\log Q + \log M))$ bits.
  - A Python reference implementation takes a median of 25 ms for 64 inputs and 92 ms for 100.
  - A Rust implementation takes 0.01–2.5 ms for up to 100 inputs, and 17 ms for 200, on an Apple M4. It decides in floating point, and falls back to the exact integer score near the threshold, so it returns the same $L$ as the reference.

## 🤖 Median estimate {#median-estimate}

$\hat{N}$ inverts the joint sums at their median instead of at $\delta$. For a chosen $m$ and $r$, it is the smallest $M \ge n$ at which the observed $\tau_{m,r}$ is at least the median of the same quantity for a uniform pool of $M$ candidates.

- **Same construction as $L$.** The spans and sums are those of the [pool size bound](#pool-size-bound), with $1/2$ in place of $\delta$. For $m = 1$, the quantity is the sum of the $r$ smallest gaps, whose exact law is known.[^holst]
- **Median-unbiased only for the pool's own spans.** $\hat{N}$ reads $N$ correctly in the median only when the observed spans are spans of the full pool, as when the whole pool is observed.
- **Reads low under weaker selection.** As in [Why it's conservative](#why-its-conservative), no selected set has smaller joint sums than the pool itself, so $\hat{N}$ is lower.
- **Reads high on small pools.** It spends no $\delta$, so nothing bounds how often it exceeds $N$.
- **Not the largest over $m$ and $r$.** Taking the largest $\hat{N}$ over all $m$ and $r$ reads high.
- **No lowest error estimate.** Without a probability law for the selection, no estimator has lowest error. The tails are heavy, so estimators are compared by quantiles rather than by mean squared error.

Measured in the prototype for a related statistic, the median inversion of the $k$-th smallest gap:

- With clustering and $n \ll N$, it reads about $\sqrt{n N}$. At $N = 10^4$ and $n = 200$, the median reading is $0.15 N$.
- At $N \le 2n$, it overshoots $N$ in 28% of runs, and in 22 of 40 runs at $n = N = 200$.

## Finding the block hash

Someone examining a transaction doesn't know which block hash the selection used. They can guess it from the confirmation time, or from the nLockTime, but not exactly. So they evaluate every candidate $t$, at $\delta / W$ each for $W$ candidates, and take the largest $L$.

- **Candidate block hashes.** 1000 or more for every transaction that looks like a CoinJoin, all mined after its inputs confirmed.
- **No false beacon.** Under a block hash the selection didn't use, the input hashes are independent and uniform: a fully observed pool of $n$. So $L \gt n$ with probability at most $\delta / W$ for each such block hash, and at most $\delta$ for all of them.
- **Screen.** Only the $m = 1$ terms, sums of the smallest gaps, are evaluated for every block hash, once, at $M = n$. That is a sort and one score. The full bound is evaluated only when the screen gives $L \gt n$. The screen's threshold is fixed, so both guarantees hold.
- **Cost.** With $W = 1000$ and up to 100 inputs, 2–9 ms per transaction in Rust, mostly hashing (about 75 ns per hash) and the screen (1–4 µs per block hash). Hashes may be cached per outpoint and block hash.

### Simulation

1000 random block hashes per transaction, $\delta = 0.05$, 32 transactions per configuration, using the Python reference.

- **No block hash used.** Inputs drawn uniformly. In all 96 transactions ($n$ = 16, 32, 80), no block hash gave $L \gt n$. At $\delta$ instead of $\delta / 1000$, 25 of them had one, up to $16 n$.
- **One block hash used**, by lowest hashes, XOR pairs or the tightest cluster, with $N$ = 1000 or 100,000. In all 576 transactions, it gave the largest $L$, no other gave $L \gt n$, and $n \lt L \le N$.
- **Cost of the split.** Median $L$ at $\delta / 1000$ is lower than at $\delta$ by about 2.6 times at $n = 16$, 1.7 at $n = 32$ and 1.3 at $n = 80$.

### Caps

Median $L / N$ of the used block hash with $N = 100{,}000$ and $n = 80$, at $\delta / 1000$:

| Cap | Lowest hashes | XOR pairs | Cluster |
|---|---:|---:|---:|
| $m \le 1$ | 0.010 | 0.329 | 0.013 |
| $m \le 8$ | 0.108 | 0.329 | 0.167 |
| $m \le 16$ | 0.156 | 0.329 | 0.238 |
| $m \le 4$, $r \le 8$ | 0.051 | 0.106 | 0.075 |
| none | 0.225 | 0.329 | 0.350 |

- **Don't cap $r$.** Pairs need many $m = 1$ terms.
- **Capping $m$** loses clusters and lowest hashes. The full bound runs on about one block hash per transaction, so it can stay uncapped up to about 100 inputs.
- The screen missed the used block hash in 1 of 32 transactions (lowest hashes, $N = 1000$, $n = 16$).

## Measurements

From the prototype, with $\delta = 0.05$. Nine selection strategies are applied to the same candidate hashes in each trial.

Median $L$ with $N = 1000$, over 32 trials:

| $n$ | XOR pairs | Lowest hashes | Closest pairs | Uniform |
|---:|---:|---:|---:|---:|
| 4 | 57.5 | 11 | 66.5 | 4 |
| 16 | 227.5 | 116.5 | 265 | 16 |
| 32 | 346.5 | 225 | 378.5 | 32 |
| 100 | 400 | 327 | 457.5 | 100 |

- With $N = 100{,}000$ and $n = 80$, median $L / N$ ranges from 0.28 (lowest hashes) to 0.47 (two clusters).
- **Uniform selection** gives $L = n$. A large pool shows nothing unless the selection is biased.
- **Overshoot.** $L \gt N$ in none of the 1,152 selected sets at $N = 100{,}000$, and none of the 2,304 at $N = 1000$.
  - This doesn't prove coverage. The proof does.
  - The guarantee bounds how often $L$ exceeds $N$, not by how much.

### Tighter alternatives

Overestimating $N$ awards credit for Sybil resistance that isn't there. That is worse than underestimating it, so the bound above is preferred over tighter ones.

- **Density profile.** Anchored ranks, Beta spans and Rényi gap ranks, at $\delta/3$ each.
  - Median $L / N$ between 0.66 and 0.78 in the same comparison.
  - $L \gt N$ in 5 of the 1,152 sets, by up to 1.30 times, and in 11 of the 2,304.
  - Its returned bound has only been tested to be monotone, not proved. It also treats fixed positions on the circle specially.
- **Gap curve.** Accumulates the evidence of every ordered gap, with fixed weights $1/r$ and power $9/10$.

## Limitations

- **Candidates, not owners.** $L$ bounds the number of candidate coins, not the number of users. One owner with many coins is many candidates.
- **Values.** The adversary's cost is proportional to $L$ only if the selected coins' values are typical of the candidates.
- **Lower bound only.** $L$ isn't an estimate of $N$. There is no likelihood for the selected set given $N$.
- **Power.** The fixed weights, the union bound and the square root lose power.
  - The minimum totals discard some of where the hashes are.
  - In a fixed example with one dense cluster, adding a second cluster at half the density raised $L$ by about 3%.
  - Splitting $\delta$ over 1000 block hashes costs most at small $n$: about 2.6 times at $n = 16$.
- **Concealment.** A selection strategy can keep $L$ near $n$. Monotonicity only prevents raising $L$ by withholding coins.
- **Review.** The calibration argument hasn't been reviewed outside the prototype.

## Open questions

- Which $m$ and $r$ should $\hat{N}$ use, or how should they be combined?
- How should the median be computed for $m \gt 1$, and for large $M$?
- Can $L$ be updated as inputs are added? A wallet compares many candidate transactions.
- **More power.** Options next to the bound above:
  - Combine the terms by a weighted minimum, rejecting $M$ if any $q_{m,r} \le w_{m,r} \delta$, instead of the square root. This loses less to the split over block hashes.
  - Tighter tails for $m = 1$. In a uniform pool, the gaps are exponential variables divided by their sum.[^renyi] Sums of the smallest gaps then have an exact law,[^holst] but it is impractical for large $n$ and small sums. A Chernoff bound on this form is practical, and gains about 1.3–1.6 times in $L$, only for large $r$. Nothing comparable is known for $m \gt 1$.
  - Anchored ranks for the per-input preference, which are tighter for lowest hashes, at part of $\delta$. They treat the anchor specially, so symmetry is lost.

[^renyi]: A. Rényi, "On the theory of order statistics", *Acta Mathematica Academiae Scientiarum Hungaricae* 4 (1953), 191–231, [doi:10.1007/BF02127580](https://doi.org/10.1007/BF02127580).

[^holst]: L. Holst, "On the lengths of the pieces of a stick broken at random", *Journal of Applied Probability* 17(3) (1980), 623–634, [doi:10.2307/3212956](https://doi.org/10.2307/3212956).
