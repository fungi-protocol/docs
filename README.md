# Fungi

Fungi is a protocol for collaborative transactions designed to make using Bitcoin more private. Participants can also pay each other interactively in these transactions, which helps not just privacy but also blockspace efficiency.

A software development kit (SDK) is [in development](https://github.com/fungi-protocol/fungi). This repository contains the specifications and the analysis behind them.

> [!NOTE]
> **Work in progress**: most chapters are drafts under review. See the [open pull requests](https://github.com/fungi-protocol/docs/pulls) for material being drafted.

## Background

Censorship resistance and fungibility are among Bitcoin's foundational properties. Without privacy, both can be undermined largely outside the protocol's rules, whether by targeting specific individuals or through chilling effects.

Bitcoin transactions are public data, and they are connected in a graph structure. Chain analysis is the application of heuristics to this graph to infer which coins share an owner. While no heuristic is perfect, their effectiveness has been shown in numerous studies. Several heuristics can be combined for a more accurate analysis. Analysis might also draw on auxiliary information not recorded on the blockchain, such as which coins an exchange sent to which customer.

CoinJoin transactions seek to undermine some of the heuristics used to cluster coins across the transaction graph. They combine several users' inputs and outputs in one transaction in order to obscure ownership links within it. Several CoinJoin implementations exist with different approaches to their transaction structure.

## Problem statement

Unfortunately, CoinJoin privacy is often stated in terms of the number of indistinguishable outputs in a transaction. This tacitly ignores the fact that those coins will go on to be spent. The information revealed by the spending transactions, which are themselves related to other transactions, can dramatically affect privacy, in some cases making the CoinJoin inputs linkable to the outputs.

Recurring relationships give rise to patterns too. Transacting with the same employers, shops and friends leaves a structure in the transaction graph, even if techniques like PayJoin might hide the individual amounts and confound some of the clustering heuristics. Obscuring this structure necessitates transacting with unrelated users, chosen at random, so users who don't know or trust each other need a way to find each other and agree on a transaction. Random selection must additionally be Sybil resistant, so that the cost of an $n-1$ deanonymization attack, where the adversary controls all of the other (apparent) participants, is a sufficient deterrent.

In general, deanonymizing a single user always makes it easier to deanonymize the other users. But sometimes the adversary might progress not just by process of elimination, but more like divide and conquer. This happens when deanonymizing that one user splits the problem of deanonymizing the rest into several smaller problems, as opposed to merely making it incrementally smaller.

The [problem definition](docs/collaborative_txn_privacy.md) chapter discusses these on-chain privacy leaks in depth, and describes a particular transaction graph structure that resists deanonymization more robustly.

## How Fungi works

A user first tells their wallet which payments they intend to make, and the wallet keeps these in a queue. Intents can vary in their time, privacy or cost sensitivity. Making a payment quickly, cheaply and privately is a balancing act, and improving one usually means compromising on another. The wallet's job is to construct transactions that make the queued payments, balancing these goals in line with the user's preferences.

The wallet schedules and batches payments, negotiating with other participants to find terms that suit the user's priorities. The more flexible a payment's timing, the more cost-effective it can be, because there is more time for compatible proposals to be combined, so that its cost can be shared with more participants. The protocol and the strategy are designed together, and the SDK implements both.

Avoiding links between coins is central to the strategy. The input and output amounts can imply such links if there aren't enough possibilities for how to group inputs and outputs so their totals match. But as mentioned above, a partition of a transaction's coins can also be evaluated based on the surrounding context in the transaction graph, not just the amounts associated with that transaction. So the strategy must consider not just whether the transaction's internal structure is sufficiently ambiguous, but also how a transaction sits in the wider transaction graph.

In Fungi, a *co-spend proposal* sets out the terms for spending a set of coins together. Proposals are made automatically according to the privacy optimization strategy. The transaction-wide terms of a co-spend proposal are public, constraining things like the range of acceptable feerates or whether or not non-SegWit inputs can be used. Proposals can also include fees, which are kept confidential. A proposal involving three or more parties additionally hides which of them made the proposal. Once accepted by all parties, co-spend proposals are publicly broadcast.

Any participant can collect fully accepted co-spend proposals from multiple parties, and then make a *coalition formation proposal* which aggregates them together, so long as the terms are compatible. If everyone accepts the coalition formation proposal, then a coalition has been formed, and the parties can proceed with collaborative transaction construction. Privacy is brittle in small transactions. A critical mass of participants is therefore necessary for privacy to be robust and cost-effective, and coalition formation is designed to facilitate such a critical mass forming.

During collaborative transaction construction, participants add their intended inputs and outputs anonymously. This preserves the unlinkability of inputs and outputs so long as it isn't undermined in some other way (for example by reusing an output address). Interactive payments additionally provide privacy against the payment counterparty. In addition to hiding the payment amount from third parties, the sender and receiver do not learn about each other's coins. Since many interactive payments can be settled in one collaborative transaction, this creates the opportunity for blockspace savings.

In order to ensure funds are secure throughout, every participant retains control at all times and therefore signs their own inputs. Unfortunately, this means that as the number of participants grows, reliability will necessarily degrade. Even if the probability of any one participant causing a fault is low, that compounds when considering the probability that none of them will. Transaction construction is designed to be fault-tolerant, so that even when a valid transaction has not successfully been produced, participants have a basis to refine the coalition structure. Fault tolerance includes malicious disruption.

## Compared to JoinMarket

Fungi could be described as a spiritual successor to JoinMarket (as implemented by [JoinMarket](https://github.com/JoinMarket-Org/joinmarket-clientserver) and [JoinMarket-NG](https://github.com/joinmarket-ng/joinmarket-ng)). Like JoinMarket, it is peer-to-peer and market-based, with no centralized coordinator, but differs substantially in how it approaches the order book mechanism as well as transaction construction.

JoinMarket distinguishes two roles: in each transaction, a user in the role of the taker selects several makers from the order book. Makers advertise their willingness to participate in CoinJoin transactions. Generally, the taker will pay the on-chain fees as well as any maker fees. The taker learns which coins belong to the makers it pays, so makers get no privacy from the taker. And because there is a single taker, a transaction can only include as many participants as one taker is willing to pay for.

Fungi makes no distinction between the taker and maker roles. Instead, a participant can both send and accept proposals, and proposals involving multiple users can be aggregated, allowing a single transaction to be negotiated more as a group buy of blockspace. As the number of participants grows, the privacy benefits compound for everyone, which means each individual user needs to pay for proportionately less blockspace in order to meet their individual privacy requirements. Finally, the proposed transaction structure aims to address several deanonymization attacks that were not yet understood at the time JoinMarket's design was put in place.
