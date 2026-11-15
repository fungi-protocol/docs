---
type: Essay
title: "Wallet clustering basics"
description: "How chain analysis links coins to a common owner, starting from address reuse and the common input ownership heuristic."
status: stable
---

# Wallet Clustering Basics

> Originally published as [The Scroll #2: Wallet Clustering Basics](https://spiralxyz.substack.com/p/the-scroll-2-wallet-clustering-basics) by Yuval Kogman
> ([@not_nothingmuch](https://x.com/not_nothingmuch)) on Spiral,
> 2025-03-12.

The Bitcoin transaction graph has various observable patterns. Some of these patterns have been studied and used to link coins from the same wallet, both in theory and practice.

Every transaction consists of a list of inputs (where the sats are taken from) and outputs (where the input sats are distributed). **Inputs** refer to the outputs of previous transactions, such as connecting transactions. **Outputs** lock some amount of Bitcoin with certain spending conditions (i.e., the "address," public key, or output script). Linking coins means identifying the entity that controls the keys to a collection of transaction outputs, spent or unspent.

Section 10 of the Bitcoin Whitepaper, "Privacy,” briefly discusses linking:

> A new key pair should be used for each transaction to keep them from being linked to a common owner.

When the same public key controls more than one coin, these coins are trivially linked since only one entity is supposed to know the private key.

However, address reuse is not the only concern. The paper continues:

> Some linking is still unavoidable with multi-input transactions, which necessarily reveal that their inputs were owned by the same owner.

This is often referred to as the "common input ownership heuristic," **CIOH**, or the "multi-input heuristic." It's only a heuristic because, unlike the implication in the quote above, counter-examples exist. Although it isn't always true, it often is.

Over the years, more sophisticated methods for clustering have been developed, for example, telling apart change outputs from payments or using larger structures in the transaction graph than just individual transactions. Some of these have been described in academic work, while others remain proprietary. Improved methods can link to more coins or avoid so-called "cluster collapse," where coins belonging to different users are incorrectly connected. Commercial offerings often benefit from additional sources of information, such as KYC data; they don’t necessarily depend on just the privacy leaks that occur in the Bitcoin protocol, but clustering is still the central theme.

This motivates an adversarial framing of privacy, where a deanonymization attack attempts to assign coins to clusters. From this perspective, defending privacy means making it more difficult for the adversary to succeed in correctly assigning coins to clusters. The most notable examples involve collaborative transaction construction, whether it is overtly difficult to guess, as in CoinJoin, or covertly as in PayJoin, or perhaps most prominently just a part of how the software works as with Lightning node transactions, in all cases the simplistic assumption breaks down necessitating a more nuanced analysis.

The adversarial framing also makes it explicit that different adversaries have different capabilities, with the appropriate adversarial model depending on the user’s threat model: Are you more worried about surveillance by an oppressive government or snooping by your transaction’s counterparties?

Future posts will go into more detail on these subjects.
