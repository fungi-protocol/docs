---
type: Overview
title: Fungi protocol overview
description: Collaborative transaction construction, privacy, fault tolerance and coalition formation.
status: draft
stale_after: 2026-10-31T00:00:00Z
---

# Fungi protocol overview

Fungi is a suite of protocols for collaborative Bitcoin transactions. Its goal is to support interactive payments and net settlement with counterparties, as well as decentralized, market-based CoinJoins with untrusted parties.

While the protocols themselves support arbitrary transaction structures, obtaining privacy outcomes is a matter of participants acting in their own self-interest and cooperating with others to achieve the desired results. The [problem definition](./collaborative_txn_privacy.md) describes conditions for a transaction graph to preserve privacy on chain. These conditions are specified in terms of properties of the graph, both the transactions that form it and its overall structure. The repository also discusses the definition of a [cost function](./optimization_framework.md) for optimizing for this outcome. That said, the protocols for collaborative transactions summarized in this document are agnostic to the details of such a cost function.

Depending on whether peers must be considered adversarial, and the underlying transport mechanisms, different variations of transaction construction are defined. These are the honest, semi-honest (also known as honest-but-curious) and Byzantine settings.

In the honest setting, we assume peers can be trusted to follow the protocol and never leak any information apart from the final transaction (deliberately or otherwise). In the semi-honest setting we no longer trust peers with privacy; privacy-preserving transports are used to hide the attribution of different transaction fragments. In the Byzantine setting fault tolerance means tolerating arbitrary and potentially malicious behavior from peers, to the extent possible.

These protocols are designed to allow interactive payments with net settlement. While net settlement on its own is beneficial for privacy in some ways, it does not adequately obscure the community structure that is inherent in real-world economic networks. Randomizing peer selection is one of the requirements for building CoinJoin graphs with the desired privacy enhancing properties.

In order to randomize peer selection, the last component needed is the [coalition formation](./coalition_formation.md) protocol. It provides a market-based mechanism to allow mutually distrusting strangers to anonymously start an instance of the Byzantine fault tolerant (BFT) transaction construction protocol.

## PSBT concurrency

[BIP 174](https://bips.dev/174/) defines Partially Signed Bitcoin Transactions (PSBTs), which allow a device with UTXO data to prepare a transaction for signing on a separate signing device. Signatures can be collected in any order, so multiple signing devices can be used, with a well-defined procedure for how to assemble everything into a signed transaction that can be broadcast.

While BIP 174 has been used in several collaborative transaction protocols, as specified it can only represent a fully formed unsigned transaction. [BIP 370](https://bips.dev/370/) extends the format to explicitly allow the input and output lists to be modifiable. The fact that these lists are ordered presents a challenge for concurrent transaction construction.

The first component of the Fungi protocol suite is the proposed [Concurrent PSBT specification](./psbt-concurrent.md). It treats these collections as unordered sets rather than lists, allowing fragments to be combined regardless of arrival order, not just when collecting signatures but also when authoring the transaction. A consistent ordering is established before signing.

In the "sneakernet" setting participants can pass around a single PSBT file, editing it in turn before handing it to the next party, but with concurrent PSBTs they can also concurrently modify different copies and merge them as well. And anything in between. Because divergent copies can be merged into one coherent transaction, the details of communication don't need to be specified; it could be a shared directory on a server, or one or more USB sticks, perhaps files shared over email, or some combination of the above.

## Consistency, safety and liveness

Consistency has to do not just with peers synchronizing their states, but also detecting when they have been successfully synchronized. Two properties of distributed systems related to this are safety and liveness: safety excludes unacceptable outcomes; liveness concerns whether the protocol eventually completes.[^safety-liveness]

Because transactions are subject to the safety guarantees of the Bitcoin protocol, collaborative transaction construction can more or less take it for granted. In all transaction construction variants the consistency requirement is agreeing on the exact unsigned transaction. We assume `SIGHASH_ALL`, which means that a signature by an input only authorizes that exact transaction, with its full list of inputs and outputs. In order to combine the signatures and obtain a fully valid transaction, all of the signatures must be made against the same transaction data.

Because even in the honest setting spending authority is never delegated and signing is unanimous, safety violations (sending money to an unintended destination) are precluded. The unfortunate cost of such unconditional theft resistance is that any input owner can effectively veto a transaction, disrupting the liveness property even if all the other parties agree to proceed with it.

As a result, liveness is inherently brittle. Consistency is a liveness requirement, not a safety requirement, and all of the mechanisms described here are primarily concerned with enhancing liveness without breaking the privacy assurances made to honest participants.

## Interactive transaction construction in the honest setting

All of the protocols described here, starting with this one, assume interactivity. The PSBT concurrency spec describes how to merge states without specifying how peers communicate, whereas the protocols prescribe specific messages to be exchanged between peers. Some of these messages correspond to unordered PSBT fragments, and can merged according the concurrent PSBT specification.

An *honest* participant is one that complies with the protocol. Faulty peers may deviate from the protocol, by being unresponsive or potentially with arbitrary, possibly malicious behavior. In the honest setting we assume that the only kind of fault is being unresponsive. Not only that, peers are additionally expected to keep confidential all of the information pertaining to the protocol's execution.

🤖 Peers exchange payment details with their counterparties, and send transaction contributions to the group as a whole. The [abstract transport interfaces](transport-interfaces.md) describe this communication as messages on send and receive channels, independently of the transport: authenticated peer to peer channels, and broadcast to the group built from them by [gossip](channels.md).

The honest setting accommodates geographically separated co-signers within a multisig wallet, coordination between separately managed funds within an organization, collaborative batching, and interactive payments. Before signing, every participant checks this transaction, ensuring their funds end up in the destinations they intended. Although the model assumes no malicious edits to the transaction, performing these checks is what enforces safety. Doing this ensures that if the assumption does not hold, the system still fails closed, and any faults that aren't explicitly accounted for in the model will only lead to denial of service, not loss of funds. Needless to say, this check also applies to the more adversarial settings described below.

## Net settlement

One of the motivating use cases for interactive transaction construction is more efficient and private on-chain payments. Several parties can batch arbitrarily many payments into one transaction. Each participant's inputs and outputs express only the net difference. Individual payment amounts need not appear on chain.

Net settlement adds both safety and liveness considerations. Before signing, a participant must know that its funds reach the intended destinations. It can check outputs returning funds to itself directly; for a payment, it needs the payee to confirm that the transaction satisfies their agreement. This can add sequential dependencies between peers. Within each payment cycle at least one party will receive as much as it sends or more, and can therefore safely initiate a cascade of confirmations. See the [concurrent PSBT specification](./psbt-concurrent.md#confirmation-of-successful-payment-prior-to-signing) for additional details.

## Fault tolerance

Because of the unanimity condition, a peer which is offline and not able to sign its inputs essentially vetoes the transaction even if not intentionally. Transaction construction therefore naturally has two tracks: the *optimistic track*, which requires unanimity, and the *recovery track*, which facilitates restarting transaction construction with a subset of participants. Recovery is a permissioned instance of the coalition formation protocol described in more detail in the last section of this overview.

🤖 Liveness is therefore inherently brittle and sensitive to delays. Deciding when a peer is unresponsive depends on what can be assumed about message delivery. The [recovery track](recovery-track.md#fault-tolerance-under-different-communication-models) describes the asynchronous, synchronous and partially synchronous communication models, and what each allows.

## Transaction construction in the semi-honest setting

In the semi-honest setting, participants are still assumed to cooperate, but are no longer trusted with privacy. Instead we assume the adversary can see their observations, regardless of whether this information is leaked accidentally or deliberately shared.[^honest-but-curious] 

🤖 Preserving privacy therefore requires anonymous broadcast to the group, while payment messages need only authenticate the receiver. The [abstract transport interfaces](transport-interfaces.md#unlinkability) and [contacts](contacts.md) chapters describe these requirements.

The privacy objective is to avoid revealing anything more than what is inherent in the transaction data to the world, and the minimal payment details to counterparties. Anonymous communication is a necessary but insufficient requirement for this; it does not prevent inference from amounts or transaction structure, nor from the wider transaction graph. The on-chain limitations described in the [problem definition](./collaborative_txn_privacy.md) still apply.

This setting is inherently more brittle, because when disruptive messages are shared anonymously not only is it unclear how to recover, in general it isn't possible to tell apart the disruptive messages from the honest ones without some additional mechanism.

## Byzantine fault tolerant transaction construction

The semi-honest setting assumes that participants claim only what they are entitled to in outputs, and cooperate until the transaction is successfully constructed and signed. While crash faults can be detected depending on the communication model, there are of course many other ways participants can be disruptive, especially if they have malicious goals like preventing the other parties from transacting.[^byzantine-generals] A Byzantine fault tolerant (BFT) protocol is one that is resilient to such disruption.

Participation is voluntary, and no party can be compelled to sign. The protocol therefore operates in the non-cooperative game-theoretic setting: any agreement to transact or sign cannot be binding, and must be self-enforcing through incentives in order to have any bearing. We therefore additionally define an honest participant as one which intends to complete the protocol and sign, regardless of which permitted actions the other honest participants choose to take. The agreed conditions must preserve that incentive throughout construction; the coalition formation protocol, discussed at the end of this overview, provides a mechanism for negotiating those conditions and aligning incentives for cooperation. For now we will simply assume that the honest users' incentives are already aligned when transaction construction commences.

Under the rules of the semi-honest setting a malicious participant might attempt to overspend, causing the combined transaction to be invalid even if signatures are given for all inputs. A malicious peer might also equivocate: give conflicting accounts of its actions to different peers. Or it might simply withhold a signature, causing delays. In the Byzantine setting the honest peers must be resilient to such disruption. This means ensuring flood protection and fairness.

### Optimistic transaction construction

The first problem is to establish that transaction fragments are valid without attributing them to specific participants. Validity means that the cost of an output is covered by input funds without double spending. Validity can be proven using zero-knowledge proofs, but this is costly, so we would like to avoid it where possible.

Due to the unanimity condition even in the Byzantine setting, successful termination requires that all participants in a particular transaction construction session comply with the protocol, which includes being responsive. When this happens to be the case, the optimistic approach is to let everything proceed exactly as in the semi-honest setting: Participants anonymously add their fragment, and once everyone acknowledges the same balanced transaction they can simply sign. The Byzantine fault-tolerant variant of Fungi is therefore designed to recover liveness by identifying at least one input controlled by a faulty peer, and then attempting transaction construction again with the faulty inputs excluded. Once all faulty participants have been excluded the honest participants will be able to successfully carry out transaction construction.

### Validity proofs

The purpose of validity proofs is to restore the possibility of completion by preventing the same funds from being claimed more than once. The proofs establish that outputs and fee contributions are covered by input funds, including any funds that originate from payments between participants. They must accomplish this *without* sacrificing privacy, which is why they must be zero-knowledge proofs. They do not replace each participant's final approval, nor can they compel any participant into providing the remaining proofs or signatures. They ensure that honest, responsive participants can successfully add all of their intended inputs and outputs to the shared state without obstruction.

A widely circulated misconception is that validity proofs in such protocols, due to the use of zero knowledge somehow themselves are a source of privacy. This is false. All they can do is enforce validity, and if done correctly, they can enforce this without requiring privacy to be destroyed.

🤖 [Transaction construction](transaction-construction.md#validity-proofs) describes when proving is required in the optimistic phase, and why the proofs remove any reason for honest participants to withhold their signatures.

### Consistency, liveness and termination in the presence of Byzantine faults

🤖 Byzantine faults take different forms, and each is handled differently. An invalid transaction output, one that overspends, is excluded by validity proofs, which reduce it to an omission fault. An equivocated block, two conflicting blocks signed by one validator, exposes that validator's key, which serves as [compact evidence](block-dag.md#nonce-commitments-and-compact-equivocation-evidence) against its coin. Together, these leave delay as the effective attack on liveness: withholding messages, and above all withholding a signature at the end, which is maximally disruptive.

🤖 Since successful termination requires unanimity, a majority agreeing is not enough. Instead, peers agree on the available evidence, such as which inputs' signatures are missing, and recover by excluding those inputs in another attempt. The [recovery track](recovery-track.md#consistency-liveness-and-termination-in-the-presence-of-byzantine-faults) describes this reasoning, and [branched execution](recovery-track.md#fault-tolerance-via-branched-execution) how recovery attempts proceed alongside the original one.

## Synchronizing protocol state

🤖 Peers synchronize protocol state using a [block DAG](block-dag.md#synchronizing-protocol-state). It is a special case of Byzantine eventual consistency, narrowed in steps: validator blocks with cordial parent requirements, a threshold for each track, one validator taking on the collection work, and optional TEE attestations. The same structure therefore accommodates several communication models and trust assumptions, to suit a variety of client capabilities and circumstances.

🤖 Two things distinguish this from typical DAG consensus, including protocols that switch between modes or tracks. First, the optimistic track requires unanimity, not a quorum. Second, the optimistic and recovery tracks may race, and different sessions may attempt to spend the same inputs. This can't be prevented in a permissionless setting, and it is useful for replace-by-fee (RBF). Racing is not a safety violation, because Bitcoin itself resolves conflicts between competing transactions. In consensus protocols, by contrast, every mode or track must agree on a single log.

## Coalition formation

Until now we have assumed an initial set of participants, some of which will be removed in new branches of the protocol as these are spun off in response to failures. We have not discussed how this initial set of participants is formed. The honest and semi-honest settings imply some degree of trust, which means such groups can form out of band.

The Byzantine setting, on the other hand, is designed to facilitate transacting with potentially malicious, ideally randomly selected peers, because as discussed in the [problem definition](collaborative_txn_privacy.md) document, such randomness is required for privacy guarantees to be robust, but this still depends on the initial set of participants being defined. For this purpose we define a coalition formation protocol, and that comes with its own set of challenges, first among which is that it operates in the permissionless setting.

The [coalition formation](./coalition_formation.md) protocol is designed to allow mutually distrusting strangers to bootstrap transaction construction using a market-based mechanism.

🤖 Agreements between strangers can't be binding without a confirmed transaction, so it operates in the non-cooperative setting, and aligns incentives by redistributing the surplus from collaboration as sats. The [background](coalition_formation.md#hedonic-games-and-games-with-transferable-utility) explains why.

This is exactly the mechanism that the coalition formation protocol attempts to build: co-spend proposals are anonymous and confidential proposals, each of which is a bundle of bilateral agreements between the proposer and the owners of the other UTXOs listed in the proposal. The distinguishing feature of co-spend proposals is that they can be aggregated together, which generalizes a JoinMarket-like fee mechanism: it allows multiple "takers" to pay a single "maker" as a kind of group buy, as well as multiple independent "makers", all in the same transaction. This generality means that the distinction between taker and maker is removed; any participant can play both roles in a single transaction, depending on the co-spend proposals it makes or accepts.

Coalition formation proposals bundle together a collection of co-spend proposals, each of which has been unanimously accepted. Unanimous acceptance of a coalition formation proposal by the owners of all inputs named in all proposals kicks off the permissioned transaction construction with an initial set of inputs, and the terms of the aggregated co-spend proposals in effect. The aggregator role is undertaken by peers proposing coalition formation proposals.

[^safety-liveness]: B. Alpern and F. B. Schneider, [*Defining Liveness*](https://www.cs.cornell.edu/fbs/publications/85-650.pdf) (1985). Formal definitions of safety and liveness, and their decomposition of system properties.

[^honest-but-curious]: A. Paverd, A. Martin and I. Brown, [*Modelling and Automatically Analysing Privacy Properties for Honest-but-Curious Adversaries*](https://ajpaverd.org/publications/casper-privacy-report.pdf). Section II-A defines an honest-but-curious participant as following the protocol while attempting to infer all possible information from legitimately received messages; the paper studies undetectability and unlinkability.

[^byzantine-generals]: L. Lamport, R. Shostak and M. Pease, [*The Byzantine Generals Problem*](https://lamport.azurewebsites.net/pubs/byz.pdf) (1982). The foundational treatment of agreement in the presence of arbitrary faults, including conflicting messages sent to different participants.
