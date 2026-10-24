<!-- TODO convert all citations to footnotes -->
# Protocol Design

This document introduces the Fungi protocol suite through a series of strawman constructions. Each one solves a different problem introduced by the previous one. This builds up to comprehensively address the broader problem of transacting privately on Bitcoin.

## Informal Problem Definition

Transacting privately means that the funding or spending of a specific transaction output must be plausibly attributable to a sufficiently large number of [wallet clusters](https://spiralbtc.substack.com/p/the-scroll-2-wallet-clustering-basics) under reasonable assumptions. For a more comprehensive and nuanced discussion of the problems these protocols aim to solve, see [./collaborative_txn_privacy.md] which, similarly to this one, builds up from PayJoin.

Constructing transactions that provide privacy this way inherently requires the participation of multiple parties, or there is no crowd for individuals to blend in. The purpose of these protocols is to allow the honest parties to agree on the inputs they intend to spend and the outputs they intend to create, with no arbitrary restrictions and without linking any one input or output to any other. This requires that all outputs are paid for by the inputs being spent, any uncovered output is by definition malicious.

Beyond that this protocol suite does not perscribe ay specific strategy for optimizing privacy. Although specific recommendations to improve privacy are provided in this repository, following those recommendations is a matter of incentives and client policy, not protocol rules.

# BIP 77 PayJoin

BIP 77 is 3 half-round, turn based protocol between two cooperating parties, a sender and a receiver, which provides both a limited form of privacy improvement and blockspace saving potential.

## Protocol Overview

The receiver initiates the protocol by sharing a payment URI that indicates BIP 77 is supported. It is assumed that the receiver has a communication channel to the sender that provides confidentiality and integrity.

Next, the sender replies with a fully signed transaction, sent directly to the receiver (instead of broadcasting).

The receiver then modifies this transaction to add its own inputs, and do as it desires with the payment output, and signs its inputs. The sender's original signatures are not valid on this modified transaction, so this partially signed transaction is then sent back.

Finally, after filling in the missing signatures the sender can broadcast the payjoin transaction, completing the protocol.

Apart from the initial URI, all protocol messages are end to end encrypted, and delivered on ephemeral mailboxes hosted on a public server, accessed using OHTTP in order to hide the peers' IP addresses. This relies on the OHTTP relays not colluding with each other or the server in order to link the metadata of the parties to the protocol to each other in the interaction. This provides no protection against a [global passive adversary](https://sites.cs.ucsb.edu/~ravenben/classes/595n-s07/papers/anon-diaz.pdf) performing traffic analysis. Such an adversary would also likely be able to link both parties traffic to a specific Bitcoin transaction being broadcast.

## Protocol guarantees

For the protocol to succeed both parties must cooperate successfully. Such peers are called honest. No faults can be tolerated in the success path, because each peer is a single point of failure. Faulty peers are peers that deviate from the protocol. Being a faulty node does not necessarily imply malice.

Byzantine behavior, which consists of arbitrary deviations from the protocol, can still tolerated in the sense that its harms are limited.

To start, Bitcoin consensus can ensure that transactions only proceed with unanimous consent. This means both parties funds are safe, neither party can misappropriate funds that are under the control of the other party at the start of the protocol. This does not guarantee the receiver will be paid, the same caveats as regular on chain Bitcoin payments apply.

The fully signed transaction provided by the sender lets the receiver opt out of the protocol and still get paid. This is important for automated receivers, which need to defend against UTXO probing, where a malicious sender would initiate payments but not follow through, in order to costlessly enumerate the UTXOs of the receiver.

By cooperating, both parties can benefit from improved privacy and the receiver can also reduce their on chain footprint. In this two party setting these incentives are sufficient.

## On Chain privacy

To a 3rd party observer such a transaction should look like a typical unilateral payment transaction. If it unconditionally applies the common input ownership heuristic, such an observer would incorrectly conclude that the inputs of the sender and the receiver belong to the same cluster. For such transactions there will be at least 3 interpretations, in the two input two output case, one interpretation is where everything belongs to one cluster, and two interpretations with two clusters involving one input and one output, as there are two matchings.

Even in the best case the privacy guarantees of this structure are fairly weak, so while it is strictly better than not using such a protocol these guarantees are both weak and brittle.

## Problem: when $n = 2$, $(n-1) = 1$

Since each party knows what inputs and outputs it controls, everything else can be attributed to the counterparty. This implies that both parties trust the other with clustering data for the involved coins.

Increasing the number of parties can provide better privacy, thereby reducing the need for counterparty trust. If Alice pays Bob in a larger multiparty transaction in a way that Bob doesn't know which inputs Alice used to do this, and whether or not one of the outputs is her change output, then he no longer has privileged information about Alice's wallet cluster.

# Multi sender, single receiver payjoin

At the cost of one more round trip, where the senders submit signatures for their inputs, BIP 77 can be [modified](https://github.com/payjoin/rust-payjoin/pull/923) to support multiplexing of several senders' payments to one shared receiver.

In this variation the receiver still initiates by sending URIs to multiple receivers in expectation of a payment. The receiver coordinates the entire transaction, similarly to the taker role in JoinMarket. As such it is trusted by the senders to behave honestly.

## Problem: only improves receiver privacy

In this modification the receiver can benefit from improved privacy, no senders should be able to distinguish the receiver's inputs from the other senders' inputs, but this does not extend to sender privacy as the receiver still knows which inputs and outputs are linked to which sender.

# Net-settlement via multiparty transaction construction in the honest threat model

If instead of the receiver multiplexing several sessions of sender-receiver payjoin around a shared receiver the protocol was fully symmetric, then no party would be uniquely privileged or disadvantaged.

Assuming each peer can broadcast messages to all other peers, a simple protocol with 3 main phases can be defined:

- First each party broadcasts its TxIns.
- Then TxOuts are broadcast and collected, finalizing the transaction.
- Finally each TxIn may be signed by its owner, and the signatures are broadcast

The first peer to obtain a full set of signatures can broadcast the transaction on the Bitcoin peer to peer network.

Concretely such a broadcast channel can be instantiated in a number of ways, such as [iroh gossip broadcast](https://docs.iroh.computer/connecting/gossip), or ephemeral [encrypted group chats](https://github.com/nostr-protocol/nips/blob/master/EE.md). There are many viable alternatives. In the honest threat model we assume all parties are trusted, not just to avoid disrupt or abuse the protocol, but also with maintaining privacy, and not retaining any information about links between inputs or outputs of the resulting transaction.

# Multiparty transaction construction in semi-honest threat model

In the semi-honest threat model, also kown as honest-but-curious, peers can be trusted to follow the protocol rules, but must not be trusted with privacy. For this model to even apply, necessarily at least 3 parties are required.

If the broadcast mechanism used to build the transaction supports anonymity, then linking individual inputs or outputs to each other should not be feasible. Concretely this can take many forms. For now, just imagine peer to peer protocol where peers are fully connected to each other. An anonymous handshake using a shared secret known to all parties can be used for authentication of new connections. This makes it possible to post a message anonymously: a peer can connect to one of the others over Tor, for example, submit a message and disconnect. The receiving peer would then broadcast the message to all peers, and nothing should directly link this message to any other message sent by its author.

## Problem: Invalid or unfair transactions may be created

In distributed state machine replication and related protocols, there are two desirable properties:

- *safety* - the replicated state this means that in addition to the state being consistent across replicas, it is also valid, which in our case means excluding maliciously added outputs from the transaction.
- *liveness* - malicious parties can't prevent honest ones from making progress indefinitely, which in our case reduces to honest parties being able to eventually add their inputs and outputs to a transaction.

Although privacy is improved by anonymously broadcasting the pieces of the transaction, just accepting `TxOut`s broadcast this way sacrifices both safety and liveness. The semi-honest model is too trusting. If one of the parties claims more than their fair share in `TxOut` value, this may result in an invalid transaction, theft of the intended mining fees of the other parties, or some of the honestly proposed outputs not be included.

Since outputs are posted anonymously, even if such an attack is detected (e.g. due the total output cost exceeding the input funds), there is no mechanism yet that can exclude the malicious peer or even the maliciously added `TxOut`.

# Multiparty transaction construction with message validity

Unfair TxOut additions can be prevented by requiring every TxOut broadcast to include a zero knowledge proof that this TxOut's effective cost (its value plus the cost of its blockspace) is covered by funds originating from one or more the inputs, without linking the output to the origin of the funds.

Although this can be accomplished generically using multiparty computation or zkSNARK compilers can be used, the communication complexity or prover complexity will be higher than what a more specialized approach can achieve. More efficient sigma protocols are sufficient for instantiating a mechanism like e-cash or privacy preserving blockchain are possible.

A relatively straightforward approach is to use homomorphic value commitments to represent satoshi values, similarly to WabiSabi. Each input's effective value can be distributed into such commitments. To utilize the value in a commitment, a proof with a nullifier is created. The nullifier protects against equivocation, allowing each commitment to only be consumed once. The balance proof allows the value to be aggregated with potentially those of other commitments, and redistributed into a new set of commitments. Range proofs and a balance proof protect the integrity of any newly minted commitments. A balance proof with a negative delta $v$ can be used to consume committed funds in order to create a txout with effective cost $v$.

In order to ensure the transaction does not exceed any size limits, a fixed allocation per initial input can be distributed using homomorphic value commitments, similarly to the satoshi amounts. Any any protocol messages can then be required to "spend" these in order to consume block space.

In order to break the links between inputs and outputs, the exact commitment used from the set must remain hidden. Ring signatures, or 1-of-n proofs (for example [Triptych](https://eprint.iacr.org/2020/018) or [curve forests](https://eprint.iacr.org/2024/1647.pdf)) prove such statements with respect to an explicit list of commitments. This proving knowledge of the opening one (or more) of the commitments, as well as proving that various relations hold with respect to the committed value, namely a balance proof, valid nullifier, etc.

As an alternative to ring signatures, publicly verifiable anonymous credentials could be used to implicitly prove that the commitment id one of a set of commitments seen by all or some threshold number of the parties, with essentially the same proofs as in the ring signature approach for the other relations.

Two equivocated transaction outputs, different outputs covered by the same funds, will both carry valid proofs, and so can be broadcast to different peers, initially causing different peers to include different outputs. However, since the proofs ensure that the nullifiers reveals such equivocation, one (so long as it's chosen deterministically) or both can be retroactively ignored by those peers. If both are struck from the transcripts of honest peers, they would be absent in the unsigned transaction. Since its output(s) will not be included, if the equivocating party signs with its inputs then its funds would potentially be burnt as mining fees. This compels it not to sign, which in turn allows the inputs of byzantine peers peers to be removed by the honest parties.

In addition to detecting equivocations, [DAPS](https://eprint.iacr.org/2017/1203) may be employed to directly reveal (at least one of) the offending party's private keys on equivocations (those used for signing protocol messages, not the spending keys). Such a private key an efficient proof of equivocation, that peers can share in order to expel byzantine nodes.

By restricting output additions transaction construction can be guaranteed to be agreeable to all honest peers. This is because each party retains full control over the precise allocation of their input funds, and by definition honest peers succeed in disseminating their outputs to other honest peers, ensuring they have no reason not to sign.

With message validity, and due to the requirement for unanimous signing, the safety property becomes trivial to satisfy. Honest peers will sign transactions with outputs derived only from provably correct, and non-equivocated protocol messages. This leaves only transaction inputs as potentially malicious payloads. Any deviation from this protocol is therefore no more disruptive than omission faults. Due to the unanimity requirement the most disruptive omission fault is failing to produce a signature at the end, since that preclude any early termination by the honest peers. As the last message, signature omission is equivalent to a crash fault.

Note that the output validity proofs can be optimistically skipped or deferred. If any remaining sats, which a peer intends to go towards mining fees, are explicitly (but anonymously) announced, then as the remaining balance (either sats or vbytes) hits 0, each peer can account for its funds in full, and acknowledge that they accept this transaction. If all parties acknowledge, agreement has been reached and signing can commence, with no need for any proofs. It's only if this balance becomes negative that all transaction outputs must be proven valid, ensuring any malicious attempts to over-spend can be removed and progress towards a valid transaction can be made by the honest peers.

## Problem: byzantine peers may disrupt convergence towards an unsigned transaction by honest peers

Somewhat confusingly, in this section even though peers were not trusted to be honest with regards to message contents, they were still assumed to be honest with regards to the dissemination of those messages. Message validity merely ensures that if consensus can be reached, the agreed transaction will be fair. As yet, nothing ensures consistency (as defined by the agreement property of distributed consensus) in the presence of faulty peers.

Dealing with omission failures in principle is conceptually simple: exclude the non-responsive parties' inputs and retry agreeing on the outputs, with the validity proofs being valid with respect to the reduced input set. However, without a byzantine fault tolerant broadcast mechanism, malicious peers may be able to cause the honest peers' view of the unsigned transaction or the signatures to diverge. In other words, a byzantine peer may cause an honest peer's valid messages to be omitted, which amounts to denial of service for that honest peer.

# Multiparty transaction construction using trusted coordinator

A trusted server may be used to coordinate transaction construction. Because of the unanimity requirement, the coordinator need not be trusted with custody of funds at any point. If properly implemented[^tagging], a coordinator need not be trusted to maintain privacy. The coordinator is trusted with liveness in the protocol, and therefore can censor or disrupt at will, and with plausible deniability.

## Problem: "trusted" coordinator is not trustworthy

This section justifies the design decision to avoid a centralized coordinator primarily on non-technical grounds and may be skipped with no consequence to understanding.

Centralized CoinJoin coordination may work in the sense that a significant volume of transactions has been constructed that way. However, so far, every single centrally coordinated CoinJoin protocol has been broken in one way or another:

- Sharedcoin
  - privacy: fully trusted coordinator
  - privacy: on chain privacy broken by sub-transaction model[^sudoku][^boltzmann][^maurer]
- Wasabi zerolink (RSA)
  - privacy: tagging
  - DoS: blind signature stockpiling (static key)
- Wasabi zerolink (blind Schnorr)
  - privacy: tagging (key consistency)
  - DoS: nonce reuse in first version, wagner attack attack in second version
  - (Also DoS due to server misconfigurations)
- Whirlpool zerolink (Samourai, Ashigaru)
  - privacy: xpubs 
  - privacy: tagging by mixid[^tagging]
  - privacy: tagging by blind signing key[^tagging]
    - "fixed" in ashigaru fork of the protocol, but signatures are still not validated by client
  - DoS: no domain separation on ownership proofs, no prevention of stockpiling with ashigaru modifications for static RSA key[^ashigaru-bullshit]
- Wasabi 2 WabiSabi
  - privacy: tagging[^tagging]
  - privacy: additional concerns in passive and covert adversary model due to improper use of Tor, and bad protocol design (HTTP, JSON)

[^tagging]: https://groups.google.com/g/bitcoindev/c/CbfbEGozG7c/m/hDx-EOJvCAAJ
[^sudoku]: K. Atlas, [*CoinJoin Sudoku*](https://www.coinjoinsudoku.com/)
[^boltzmann]: LaurentMT, [*Boltzmann*](https://gist.github.com/LaurentMT/d361bca6dc52868573a2), specifically the link-probability matrix.
[^maurer]: F. K. Maurer, T. Neudecker, M. Florian, [*Anonymous CoinJoin Transactions with Arbitrary Values*](https://www.researchgate.net/publication/318128387_Anonymous_CoinJoin_Transactions_with_Arbitrary_Values)
[^sudoku]: K. Atlas, [*CoinJoin Sudoku*](https://www.coinjoinsudoku.com/)
[^ashigaru-bullshit]: https://gist.github.com/84adam/3f38280ca2d0ca8362235f0afea2d153?permalink_comment_id=5680496#gistcomment-5680496

Every one of these implementations requires trusting the coordinator with privacy to a significant extent, if not completely, despite claims to the contrary by vendors and proponents. Furthermore, denial of service protection was not actually realized by most of these, despite that being the primary purpose of the coordinator. In all cases the cryptographic aspects of the protocol amounted to little more than theater due to either broken protocol design, or inconsistencies between protocol design and client implementations.

It would be strictly more reliable and efficient, and more or less as privacy preserving, to simply trust the coordinator to not keep logs, i.e. the sharedcoin protocol with a less conspicuous on chain structure.

Making things worse, none of these implementations accounts for privacy loss due to intersection attacks[^scroll-intersection], despite this privacy concern having been described[^goldfeder] well before the existence of current centralized offerings. This is in addition to a number of other on chain deficiencies, such as careless coin selection in both regular transactions and for CoinJoin transactions.

[^scroll-intersection]: For an accessible treatment of entropy and intersection attacks on coinjoin anonymity sets, see [The Scroll #4, Intersection Attacks](https://spiralbtc.substack.com/p/the-scroll-4-intersection-attacks)
[^goldfeder]: S. Goldfeder, H. Kalodner, D. Reisman, A. Narayanan, [*When the Cookie Meets the Blockchain*](https://arxiv.org/abs/1708.04748)

Malicious coordinators have been observed in the wild [exploiting weaknesses](https://github.com/orgs/WalletWasabi/discussions/13249) in the WabiSabi protocol and client implementation. Even if the still remaining flaws were addressed, it is inherently hard to protect against censorship by coordinators. An accountability mechanism for decentralized reputation might be a potential approach to address that, but would introduce significant complexity.

Even if the tagging issues in whirlpool were addressed, the claim that coordinator fees are "anti sybil" are misleading, the exceptionally high coordination fee rate allows a malicious coordinator to subsidize the liquidity costs and mining fees required to perform $(n-1)$ deanonymization attacks with the revenue stream from coordination fees. Ironically claim is technically accurate because the coordinator must be trusted with privacy as well, so it can deanonymize costlessly, but note that this is purely a deterrent against sybil attacks by other input owners, something that is unnecessary in the UTXO model (mining fees provide sufficient unforgeable costliness) and which does not provide the colloquial notion of "sybil attack" in the context of CoinJoins, i.e. a costless deanonymization attack.

Fees paid by consenting users, and understood to be in the service of privacy, have unfortunately not gone towards fixing these flaws. Instead, among other things, were awarded to DoS attackers (through successful extortion) as well as funded misleading marketing efforts, which arguably includes a years long twitter feud that has alienated users and fostered a cult like mentality with regards to Bitcoin privacy technology among the remaining proponents.

The evidence for centralized CoinJoins being flawed and predatory is overwhelming, despite not being inherent it appears inevitable. It is not just harmful to directly exploited users, but to privacy and fungibility as a whole. Weak privacy is antithetical to censorship resistance, the chilling effects of surveillance lead to self-censrship, and it is antithetical to self sovereign custody due to the lack of informed consent and perhaps more importantly because such misinformation exposes users to unnecessary risk with real safety concerns, as indicated by the alarming rise of $5 wrench attacks.

This market failure is unacceptable. We therefore require a decentralized protocol in the spirit of JoinMarket, permissionless and market based, free to the extent possible of any perverse incentives or rent seeking opportunities. JoinMarket technically uses centralized coordination, since the taker coordinates any particular transaction, but since this isn't a third party, and the taker is both benefitting from and paying for the transaction, incentives are aligned. That said, we aim to improve on JoinMarket too, in terms of privacy, scalability and costs.

# Multiparty transaction construction using BFT CRDTs

So long as there is a deterministic procedure for ordering the inputs and outputs, the order in which they are received is immaterial, given the same set of constituents, peers will converge on the same transaction. In other words, transaction construction can be fully described in terms of a [G-set conflict free replicated data type (CRDT)](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type#G-Set_(Grow-only_Set)).

Work by Martin Kleppmann and Heidi Howard introduced [byzantine fault tolerant (BFT) eventual consistency](https://arxiv.org/pdf/2012.00472) and [BFT CRDTs](https://martin.kleppmann.com/papers/bft-crdt-papoc22.pdf) in the asynchronous communication model (where messages can be delayed by an arbitrary amount, discussed in the next section in more detail). This result implies that so long as the honest parties are able to disseminate information, they can make progress and eventually convergence even in the presence of an byzantine peers. This work provides the strong eventual consistency property, which loosely means that eventually the honest peers' states will converge. Since the state is defined as a CRDT, it is guaranteed states which have diverged can always be merged.

Unlike equivocation of Bitcoin transactions (i.e. double spends), which are prevented by miner determined precedence, equivocations in transaction construction can simply invalidate both conflicting messages. Since this is symmetric, equivocations also do not break the CRDT semantics. Such removal can be modeled either as a [two phase set](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type#2P-Set_(Two-Phase_Set)). See section 2.4 of the second paper, by Kleppmann.

Each peer processes the these state updates in an arbitrary order, executing protocol outputs this sequence of updates for processing. The state is obtained by applying these outputs in that order, and because of the CRDT properties, if all updates are eventually delivered to all peers, their states will eventually be identical. This says nothing about their instantaneous states.

Concretely, in Kleppmann and Howard's approach a cryptographic hash is used to construct a distributed causal log of messages (sometimes known as a "blocklace"), and this is used to facilitate efficient set reconciliation even in the presence of byzantine faults. We will return to set reconcilation in later sections.

This establishes a baseline of what can be achieved. As different approaches for improving liveness are discussed in the following sections bear in mind that any of those protocols that the strong eventual consistency is sufficient for the success path. This holds even in the presence of a dishonest majority and in the asynchronous communication model, one of the most severe setting in which honest parties might hope to cooperate.

The catch is that "eventually" says nothing about how long this can takes. Success depends on the ability of the honest peer to actually communicate with each other. For example if one of the peers is taken offline indefinitely, so long as it can eventually comes back online, that is merely a transient delay and doesn't fit the definition of either a crash fault or omission fault, which technically require that either this peer is permanently offline or that some of its messages are permanently lost. Message validity does make possible somewhat stronger guarantees than the model in the paper (and similarly to the improvements of [later work](https://arxiv.org/pdf/2402.08068
)) since for transaction construction can enforce either or both of a rate limit and a total message limit, preventing malicious peers from flooding with messages to delay convergence. The terminal states (coatoms of the lattice) are those where the remaining balance is 0 or all inputs have indicated they are ready to sign, which may or may not require validity proofs.

## Problem: BFT CRDTs only ensure strong eventual consistency

While strong eventual consistency is a useful property, there isn't much that can be said about the intermediate states prior to convergence other than that they converge, and more importantly there isn't anything that can be said about timeliness of convergence, because message delivery may suffer unbounded delays.

For a economic transactions that require privacy, the costs incurred by unbounded delays may be prohibitive. In the worst case unbounded delays impose a choice is between completing a transaction without privacy or waiting indefinitely.

A robust protocol should ideally provide stronger liveness or termination guarantees, so that the honest parties will be able to make progress towards producing a valid transaction which contains all of the outputs they intend to add, and that they are able to succeed in doing so in a timely manner. This extends to network partitions, if communication between two disjoint subsets of the honest breaks down then either subset should be able to fall back on agreement only within the subset, even if strong eventual consistency implies that eventually communications will resume.

# Multiparty transaction construction using leader based BFT consensus

## State machine replication

State machine replication (SMR) has a much stronger notion of consistency than eventual consistency. In this model all peers (typically called replicas) are required to apply updates in exactly the same order. This fully determines all intermediate states. Depending on protocol specifics some of the peers may lag behind the others. Of course this implies eventual consistency as well.

State machine replication is often defined in terms of iterated consensus. In consensus protocols, honest peers will output the same value, and for SMR to coordinate the next update. Whereas under eventual consistency they can apply valid updates immediately after they are received, waiting for consensus requires additional coordination among the peers, so that each honest peer can rule out the possibility of disagreement.

As we have seen, multiparty transaction construction does not depend on the updates being totally ordered for convergence. This implies that SMR is overkill for this application. That said, for now we will set this observation aside, and just note a problem related to the consensus problem, [generalized lattice agreement](https://dl.acm.org/doi/pdf/10.1145/2332432.2332458) ([BFT variant](https://arxiv.org/pdf/1910.05768)), which has been used to define a variant of SMR that relies on the commutativity of updates, much like eventual consistency. This model has stronger consistency guarantees than eventual consistency offers, but weaker ones than consensus. Unlike consensus, lattice agreement can still be deterministically solved in the asynchronous communication model, where we will now turn out focus.

## Communication models

When communications are disrupted, relying on consensus this can impede progress substantially compared to protocols that make weaker guarantees. Different kinds of disruptions are characterized using qualitatively different communication models.

In the synchronous communication model, messages from honest peers will be delivered in a timely manner. This can be made concrete by relying on timeouts, treating unresponsive peers as faulty. This setting tolerates a dishonest majority (c.f. Dolev-Strong byzantine broadcast). While simple and practical in the centralized setting, if the coordinator is replaced with a leader based protocol and leaders may be faulty, relying on timeouts and synchronized clocks is problematic, especially in heterogeneous networks. For this protocols designed for the [partial synchrony](https://groups.csail.mit.edu/tds/papers/Lynch/jacm88.pdf) model are typically preferred for decentralized systems.

Under partial synchrony and in the asynchronous model, a protocol can proceed at rate limited by the underlying network and honest parties' ability to communicate, for example by utilizing a threshold clock. However, any kind of liveness or even termination assurance relies on the number of faulty peers being bounded. Depending on the communication model and on what properties are desired from consensus, this bound may be as tight as 0 as in the famous [FLP impossibility result](https://dl.acm.org/doi/pdf/10.1145/3149.214121).

## Leader based BFT consensus

Various byzantine fault tolerant consensus protocols have been described in both the asynchronous and partial synchrony models. Many practical protocols rely on leader based consensus, ensuring liveness for $n \geq 3f+1$ participants so long as no more than $f$ of them are faulty. Some notable examples include [honey badger](https://eprint.iacr.org/2016/199.pdf) and the [hot stuff](https://arxiv.org/abs/1803.05069) family of protocols.

In leader based protocols, one of the peers is designated as the leader at any point in the protocol. If the leader becomes faulty, a new leader is chosen by the protocol ensuring that eventually one of the honest peers can become the leader, and progress can be made.

## Why not both?

In the transaction construction setting, the requirement for unanimity makes safety trivial, even a single honest peer retains veto power. This does not depend on consistency, but is enforced directly through the signature mechanism itself (barring oddities such as `SIGHASH_SINGLE` or `SIGHASH_ANYONECANPAY`).

It follows that bolstering the consistency guarantees is best understood as a way of improving liveness over the strong eventual consistency baseline. If a complete set of signatures for the same unsigned transaction has been collected by at least one peer and broadcast on the Bitcoin peer to peer network, the protocol has concluded successfully. But if it hasn't, while waiting potentially indefinitely, the active peers may attempt to terminate the protocol earlier via a recovery path.

BFT consensus makes such a recovery path well defined, signing can commence even if only $(n-f)$ peers are responsive and have posted their outputs successfully. Although this won't produce a valid transaction, since at least $f$ inputs almost certainly will not be signed, the honest parties will be able to retry transaction construction with those inputs removed.

In the success path, on top of strong eventual consistency, consensus over the fully signed transaction provides confirmation to all of the honest peers that any one of them will be able to broadcast it on the Bitcoin network.

## Problem: Asymmetric communication burden for leader scales poorly

The practical limit on a single transaction size in Bitcoin is either the standardness limit, 100KvB, or the 1MvB block size limit. This is sufficient for hundreds of inputs and outputs, and by extension hundreds of participants in a single transaction.

A multiparty transaction construction protocol focused on privacy should support scaling hundreds of users per transactions. The bigger the crowd, the better the privacy. With a small number of users privacy is very brittle, and the privacy benefits of adding inputs quickly compound. However, eventually the returns start diminishing. When a transaction is sufficiently ambiguous, and large enough so as to be well connected to other such transactions, the marginal contribution of yet another input may be negligible.

Transaction size limits are not a hard constraint on the scale of multiparty transactions more generally. By utilizing multisig covenant emulation and carefully managing back out paths and transaction dependencies, arbitrarily large transaction graphs can be constructed, which are semantically equivalent to a single transaction that would be too large to be valid. Such constructions are widely believed to have important implications for scaling: virtual UTXO based constructions are a special case of multiparty transaction construction where it is desirable for $n$ to be significantly larger than hundreds. While several such protocols already exist, so far they have relied on centralized coordination and provide no privacy guarantees.

The ultimate constraint on scale is reliability, which due to the unanimity requirement diminishes at an exponential rate. Let $p$ be the probability that any one peer experiences no faults during a run of the protocol, the probability of none of them experiencing a fault is $p^n$. Suppose $p$ is 99.9%, with $n=100$ only a 90% probability that no peer will experience a fault remains, and it's less than 37% for $n = 1000$.

The unanimity requirement demands that no such fault occurs in order to successfully complete a run of the protocol. This is because any fault implies needing to prune the input set, which requires agreement over the output set to be established from scratch (because any proofs would only be valid with respect to the input set before it was pruned).

For overly large values of $n$, success might be achievable but rare enough that it rarely succeeds in practice. Significantly below that there is sweet spot of scale, which maximizes $n$ while maintaining an acceptable failure rate. The precise value of $n$ strongly depends on network reliability, the rate of byzantine behavior, and many other factors, but as stated above it should be at least on the order of hundreds.

While even poorly implemented centrally coordinated coinjoins have demonstrated that $n$ on the order of hundreds is achievable, in the decentralized setting this is more costly for peers who can't rely on communicating with just one trusted coordinator. If one of the peers is selected as a leader, the additional communication overhead. Coordinating such a transaction also requires sharing information about the previous outputs, the message validity proofs, etc, and the leader must broadcast all of this information to all parties, which for large transaction any be too taxing on the chosen leader, necessitating failover and incurring significant communication overhead.

Since traditional leader based consensus imposes asymmetric resource utilization, placing more of burden on the leader, another useful probability to think about is that of the leader being able to communicate successfully during one run of the underlying consensus protocol. Naively the probability of consensus succeeding under this leader is $q^n$, if the probability of error was independent, but network congestion is likely to cause correlated transmission failures for a leader that lacking sufficient resources in reality things will fare worse. Although such leader faults do not break the unanimity requirement, they delay progress of the overall protocol and consume more resources from all peers, which in turn negatively $p$.

For the scales needed to make a positive impact on privacy, leader based consensus is far from optimal.

# Multiparty transaction construction using leaderless BFT consensus

<!-- TODO setchain consensus & redbelly weak coordinator -->

Symmetric consensus algorithms place an equal burden on all peers (typically referred to as validators).

The [DAG rider](https://arxiv.org/pdf/2102.08325) family of algorithms is of particular interest due to its conceptual simplicity. A causal log is used, much like in Kleppmann and Howard's approach, as if maintaining threshold clock based CRDT for leader election, which determines the consensus state. 

- [Recent work](https://arxiv.org/pdf/2506.13998)

- can exploit CRDT structure, c.f. lattice agreement above
- problem: costly communication, not friendly to mobile clients

# Improving broadcast efficiency

Recall the complete graph topology implied by our broadcast channel abstraction.

In practice, not all peers will be publicly reachable, or have sufficient bandwidth. Metadata privacy and reliable communications are harder on mobile clients, requiring [creative workarounds](https://primal.net/e/nevent1qqs2470jrlr4e6ek9yxmhnkl420mt80qu3snr4fsv3tpn545cgj49eg9x35m5).

- best effort broadcast
  - erasure coding
- gossip/epidemic broadcast - most efficient, least resillient
  - robust overlay networks to avoid fully connected topology
  - efficient set reconciliation
  
- stronger guarantees build on top of this:  
  - reliable broadcast
  - atomic broadcast
  - consistent broadcast
  - BBCA?

In order to decrease the communication burden, broadcast protocols have that rely on erasure coding have been described in the literature. This allows the communication complexity to be reduced from cubic overall (in the number of peers) to quadratic (linear per peer).

- gossip, set reconciliation, set union consensus
  - byzantine set union consensus (set reconciliation + gradecast) https://grothoff.org/christian/consensus2016.pdf
  - minisketch
  - rateless set reconcilation, rateless IBLT and certainsync
    - compare with bloom filter approach of Kleppmann 22

# public infrastructure for assisting constrained clients

- allow some clients to opt out of being validators?
- payjoin directory service as semi-trusted party
    - efficient set reconcilation with linear communication per mobile client?
    - rate limiting credentials per UTXO for rate limiting writes to directory broadcast channels
- problem: bft consensus requires n >= 3f+1. dishonest majority or even just more than f malicious parties can disrupt liveness, denying service to honest parties
  
# Multiparty transaction construction under dishonest majority?

- byzantine broadcast under dishonest majority?
- asymmetric trust? https://arxiv.org/pdf/2505.17891

- does such a protocol exist or is strong eventual consistency the assurance that can be obtained?
  - sync vs. async tradeoff
  - ACS? "interactive consistency"?

- problem: privacy still brittle if only co-spending with payjoin counterparties, wallet clustering based on fingerprints

# generalized coinjoin via open protocol enrollment followed by bft multiparty txn construction

- TODO strawman order book model

- more diverse counterparties can improve privacy
- full generality says nothing about privacy guarantees
  - a cost function is needed to make good decisions within the protocol
- recommended structure:
  - [theoretical basis](https://github.com/nothingmuch/tx-graph-anonymity-sets/)
  - radix coinjoin, with [recommended values](https://colab.research.google.com/drive/1We_FvfX_Ob9BapFW3X_By9vTtxUrt3pm)
  - some similarties to wasabi 2, important differences:
    - allow high hamming weight outputs for payments (for use in payjoin, or for more blockspace efficient decomposition)
    - TODO describe:
      - brute force search for fail closed, randomizable strategy
      - efficient subset sum density estimation both for precompution or during critical phase

- problem: not sybil resistant, attacker can flood the order book and do (n-1) attack on honest clients

# generalized coinjoin with randomization mechanism

[verifiable randomization mechanism](https://gist.github.com/nothingmuch/f5b9a559958c6116606d9da0d4d884f2) provides sybil resistance and improved graph properties, as well as useful symmetry breaking properties for the protocol in both the low volume (up to one tx per block) and high volume (more than one tx per block) regimes

problem: incentive alignment for bootstrapping protocol unclear/intractable

# coalition formation protocol

- how does it relate to active participants in unknown participants setting

[coalition formation](https://github.com/payjoin/multiparty-protocol-docs/pull/1) reduces generally hard coalition formation to simpler incremental bilateral negotiations

aligns incentives for txn construction

---


## Background: wallet clustering & 2-party PayJoin

PayJoin was created as a response to the wallet clustering concern. Bitcoin transaction transaction outputs can be clustered together, labeling a group of TXOs as belonging to the same wallet. Clustering allows any blockchain external information linked to one coin in a cluster, such as personally identifying information from KYC requirements, to be associated with any other coin in the cluster.

Clustering is a problem for Bitcoin. For businesses this can reveal information to competitors. For individuals, especially with self-custody, it is about personal safety and freedom from surveillance. And for the system as a whole it degrades fungibility and censorship resistance.

Clustering techniques have advanced significantly over the years and continue to improve. The oldest of these is the common input ownership heuristic, also known as the multi-input heuristic, which assumes that coins that were spent as inputs to the same transaction are owned by the same entity. CoinJoin transactions are created in order to contradict this assumption, but this heuristic can be refined to filter obviously multiparty transactions.

Existing PayJoin protocols (BIPs 79-77) allow two parties to collaboratively construct a transaction. Such transactions are not as easily distinguished from "regular" payment transactions (where the CIOH is be accurate), but since they are multi- party transactions they cast doubt on the heuristic applied to similar transactions.

Since PayJoin is a two party protocol, the counterparty is necessarily trusted with regards to privacy. Each party knows which inputs and outputs belong to it, and after eliminating those only the counterparty's inputs and outputs remain.

## Motivation

### Privacy

A PayJoin transaction with 3 or more parties reduces the counterparty trust with regards to privacy. Suppose Alice is paying Bob, Bob is paying Carol, and Carol is paying Alice. Alice doesn't need to know which of the inputs to such a transaction belong to Bob and which Carol. By the same logic, Bob wouldn't know which input belongs to Carol, nor if Carol is paying Alice, possibly utilizing the funds from his payment to do so.

With regards to 3rd party observers, with improved clustering techniques the privacy of PayJoin transactions degrades. For example, by utilizing wallet fingerprint based techniques to cluster coins, a PayJoin transaction that would otherwise lead two clusters to be incorrectly collapsed into one could be filtered out if the clusters appear too distinct based on their associated fingerprints. This flags PayJoin transactions, with context clues singling them out from the background of "regular" on-chain payment transactions. Furthermore, if the outputs of such a transaction can be linked to the inputs then the payment amount can be inferred. With additional parties involved, the task of linking inputs a PayJoin transaction to each other, or the outputs to the clusters of the inputs, both become more difficult.

### Blockspace savings

Multiparty PayJoin provides the potential for more additional blockspace savings over PayJoin. If $n$ parties all transact with each other on chain that would require $O(n^2)$ block space, but they can instead coordinate and create a single net-settlement transaction with size $O(n)$ with the same outcome.

RBF cut-through. custer mempool.

If cross input signature aggregation is enabled on Bitcoin, full aggregation would require more or less the same interaction as multiparty transactions, and incentivizes collaboration because it requires only $O(\frac{1}{n})$ witness data per participant.

Similarly with any kind of UTXO sharing, such as payment channels or offchain vUTXOs, on chain payments can still be supported as a kind of splicing or cooperative exit operation again through interactivity.

---

The receiver initiates the protocol, providing the sender with a payjoin enabled payment URI (BIPs 21, 321). The sender replies with a fully signed payment transaction, delivered over a peer to peer communication channel instead of by broadcasting to the network. The receiver at that point can opt-in to replacing the transaction, with their inputs as well, and replies to the sender with all of the signatures for the receiver's  adding their inputs and signing, and replying to the sender 

replies with a fallback transaction. This is a unilateral, fully signedThis transaction as would be created by a sender without payjoin support.

- clustering is the problem
- multi user transactions are the solution
  - coinjoin w/ robust theory of anonymity sets is maxxing version of that
  - payjoin not it:
    - requires couinterparty trust
    - anonymity set size is small
    - ...

# CoinJoin constraints

with `SIGHASH_ALL` (and without `SIGHASH_ANYONECANPAY`, which is a malleability issue, or other hypothetical sighash flags), all parties must sign the same transaction and then combine their signatures, or the transaction can't be broadcast on the bitcoin network

this means that all parties must come to agreement about what transaction to sign

if the total txout amount exceeds the total txin amount, the transaction will not be valid. therefore addition of txouts must be restricted

if only the total txout amount is restricted, some users may include txouts exceeding the inputs they are spending, while other users would not be able to get theirs in, so restriction of txout addition must be fair and accountable, ensuring that txin funds cover txout funds per user

for privacy (aspect of safety), txouts must not be linkable by other parties in the transaction, even in the semi-honest setting (fine in the honest setting), so txout restriction can't rely on knowing which inputs are related to the input

if all of this is satisfied, i.e. the honest parties are able to come to agreement about an unsigned transaction without compromising their privacy, then no honest user should have a reason not to sign the resulting transaction.

for liveness txouts must only be included if covered by txin funds, this ensures the unsigned txn could be valid if it were signed, and that every 


---

permissionless network -> new gossip network where peers can start communicating TODO rephrase

how do we get there? the best we have is UTXOs but we can't assume 1 utxo = 1 peer, an adversary can make many small UTXOs, so we can't assume anything about n >= 3f + 1

- circular dependency between these elements needs to be broken by bootstrapping
- ability to verify UTXOs and BIP 322 ownership proofs
- ownership proofs certify listen advertisements, which include metadata
  privacy preserving authenticated endpoint, suitable for establishing
  pairwise channels: i2p destination, tor hidden service, directory mailbox, etc...
- peer to peer channels allow construction of an overlay network
- specifically we are interested in robust overlay networks, resistant to
  dishonest majority and tolerating high churn, for example random walk
  based peer sampling
- anti-entropy or set reconcilation over peer channels makes efficient gossip
  possible, allowing all parties to share the set of ownership proofs and
  listen advertisements
