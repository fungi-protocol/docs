---
okf_version: "0.2"
---

# Background

* [Wallet clustering basics](background/wallet-clustering-basics.md) - How chain analysis links coins to a common owner, starting from address reuse and the common input ownership heuristic.
* [A brief history of wallet clustering](background/history-of-wallet-clustering.md) - A survey of the academic literature on wallet clustering, from early observational studies to wallet fingerprinting.
* [Intersection attacks on CoinJoin anonymity](background/intersection-attacks.md) - Measuring anonymity with entropy, and how intersections of clusters over time erode CoinJoin anonymity sets.
* [The many faces of CoinJoins](background/faces-of-coinjoin.md) - What "CoinJoin" refers to: equal amount CoinJoins, multiparty batching, PayJoin and Lightning.
* [The many headaches of CoinJoin](background/headaches-of-coinjoin.md) - Why designing a CoinJoin that overtly optimizes for privacy is harder than the folk anonymity set model suggests.

# BIP Drafts

* [PSBT Scrubber](bip-drafts/scrubber.md) - Which PSBT fields can be shared with trusted and untrusted parties such that privacy is preserved.

# In Review

* [Collaborative transaction privacy](collaborative_txn_privacy.md) - Under review in #7.
* [Cost function framework for Bitcoin wallets](cost_function_abstract.md) - Under review in #15.
* [Concurrent PSBT Construction](psbt-concurrent.md) - Under review in #16.
* [Market-based coalition formation for collaborative transaction construction](coalition_formation.md) - Under review in #18.
