# Fungi

This repository contains documents that describe a family collaborative Bitcoin transaction construction protocols. The protocols form a progression towards decentralized and market based privacy preserving transactions.

> [!NOTE]
> **Work in progress**: most chapters are still under review. See the [open pull requests](https://github.com/fungi-protocol/docs/pulls) for material being drafted.

## Fungi protocol suite

### Honest setting

The *honest* setting assumes all participants can be trusted in two ways:

- not to disrupt the execution of the protocol
- with privacy, which means not revealing to the adversary, ideally forgetting, any information that may be revealed by participants in the course of the protocol's execution

In this as well as subsequent protocol, trust never means  giving up control over one's funds. Input signatures in transactions enforce this safety by letting each party ensure its , requiring unanimous consent by all parties.

### Semi-honest setting

In the *semi-honest* setting, also known as *honest-but-curious*, we no longer assume peers have to be trusted to keep a secret. Instead this relies on privacy preserving transports for the communication, that allow a peer to broadcast its messages anonymously to the other participants. Because Bitcoin transactions are transparent, privacy further demands a more careful approach to transaction construction, or the actions of a peer may be revealing even if not directly attributable.

The semi-honest setting can provide some degree of confidentiality, especially against 3rd party observers, through the construction of net settlement transactions. But not anonymity. Transactions between peers that are somehow related have inherent privacy issues because such relationships constitute a social network, exhibiting community structure.

### Byzantine fault tolerant setting

Overcoming the community analysis concern requires a Sybil resistant, permissionless protocol where peers with no meaningful economic relationship can find each other. This involves an additional *coalition formation* protocol that sets up transaction construction using a market based mechanism.

While it is beneficial for privacy, interacting with strangers in a permissionless protocol invites distruption or attempts are survaillance. For honest peers to be able reliably transact, especially with the unanimity requirement, demands a byzantine fault tolerance from the transaction construction protocol.

In the course of a BFT interaction with untrusted peers, a participant may still use the other variants of the protocol to coordinate activity with the subset of peers they do know or trust, for instance by performing net-settlement within a larger BFT CoinJoin.

## Motivation

Wallet clustering is the broad term for a variety of techniques that can be used to deanonymize on chain activity. Clustering involves linking particular coins to one another, attributing their ownership to the same entity. Over the course of Bitcoin's existence many papers have been published on this subject, also about related privacy issues issues, such as Lightning network, or the transport layer.

This body of work has, time and again, shown that misconceptions about privacy invariably err on the side of optimism. Moreover, depending on individual users' threat models, their adversary may have access to comprehensive auxiliary information. Such auxiliary information doesn't even need to be about the target user, information about other users may be useful for deanonymization of the target user. In cryptography, rotating long lived keys or favoring ephemeral ones can limit the scope of a compromise, but an individual's identity is who they are.

The fungi protocol suite is designed to make arbitrary transactions possible between mutually consenting but distrusting peers. This means safety, liveness, and unlinkability of protocol messages. Within such a protocol peers are free to pursue whatever outcomes they desire.

Privacy does not simply emerge naturally from collaborative transactions. Peers must actively optimize for that. Optimization involves the use of a cost function, an extension or generalization of the kind used for coin selection. This repository makes specific reccomendations with which the protocols are designed to be compatible. The recommended privacy related terms address Sybil resistance, the transaction structure (for example how output values are chosen in relation to others' input values) and the graph structure.
