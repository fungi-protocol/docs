# Fungi protocol overview

Fungi is a suite of protocols for collaborative Bitcoin transactions. Its goal is to support interactive payments and net settlement with counterparties, as well as decentralized, market-based CoinJoins with untrusted parties.

While the protocols themselves support arbitrary transaction structures, obtaining privacy outcomes is a matter of participants acting in their own self-interest and cooperating with others to achieve the desired results. The [problem definition](../collaborative_txn_privacy.md) describes conditions for a transaction graph to preserve privacy on chain. The repository also discusses the definition of a [cost function](./cost_function_abstract.md) for optimizing for this outcome. That said, the protocols for collaborative transactions summarized in this document are agnostic to the details of such a cost function.

Depending on whether peers must be considered adversarial, and the underlying transport mechanisms, different variations of transaction construction are defined. These are the honest, semi-honest (also known as honest-but-curious) and Byzantine settings.

In the honest setting, we assume peers can be trusted to follow the protocol and never leak any information apart from the final transaction (deliberately or otherwise). In the semi-honest setting we no longer trust peers with privacy; privacy-preserving transports are used to hide the attribution of different transaction fragments. Finally, in the Byzantine setting we must tolerate arbitrarily malicious behavior from peers.

Finally, the [coalition formation](../coalition_formation.md) protocol provides a market-based mechanism to allow mutually distrusting strangers to anonymously start transaction construction together. Randomizing peer selection is a requirement for CoinJoin graphs with the desired privacy properties. Net settlement, while beneficial for privacy, does not obscure the community structure that is inherent in real-world economic networks.

## Concurrent PSBTs

[BIP 174](https://bips.dev/174/) defines Partially Signed Bitcoin Transactions (PSBTs), which allow a device with UTXO data to prepare a transaction for signing on a separate signing device. Signatures can be collected in any order, so multiple signing devices can be used, with a well-defined procedure for how to assemble everything into a signed transaction that can be broadcast.

While BIP 174 has been used in several collaborative transaction protocols, as specified it can only represent a fully formed unsigned transaction. [BIP 370](https://bips.dev/370/) extends the format to explicitly allow the input and output lists to be modifiable. The fact that these lists are ordered presents a challenge for concurrent transaction construction.

The first component of the Fungi protocol suite is the proposed [Concurrent PSBT specification](../psbt-concurrent.md). It treats these collections as unordered sets rather than lists, allowing fragments to be combined regardless of arrival order, not just when collecting signatures but also when authoring the transaction. A consistent ordering is established before signing.

In the "sneakernet" setting participants can pass around a single PSBT file, editing it in turn before handing it to the next party, but with concurrent PSBTs they can also concurrently modify different copies and merge them as well. And anything in between. Because divergent copies can be merged into one coherent transaction, the details of communication don't need to be specified; it could be a shared directory on a server, or one or more USB sticks, perhaps files shared over email, or some combination of the above.

## Consistency, safety and liveness

Consistency has to do not just with peers synchronizing their states, but also detecting when they have been successfully synchronized. Two properties of distributed systems related to this are safety and liveness: safety excludes unacceptable outcomes; liveness concerns whether the protocol eventually completes.[^safety-liveness]

Because transactions are subject to the safety guarantees of the Bitcoin protocol, collaborative transaction construction can more or less take it for granted. In all transaction construction variants the consistency requirement is agreeing on the exact unsigned transaction. We assume `SIGHASH_ALL`, which means that a signature by an input only authorizes that exact transaction, with its full list of inputs and outputs. In order to combine the signatures and obtain a fully valid transaction, all of the signatures must be made against the same transaction data.

Because even in the honest setting spending authority is never delegated and signing is unanimous, safety violations (sending money to an unintended destination) are precluded. The unfortunate cost of such unconditional theft resistance is that any input owner can effectively veto a transaction, disrupting the liveness property even if all the other parties agree to proceed with it.

As a result, liveness is inherently brittle. Consistency is a liveness requirement, not a safety requirement, and all of the mechanisms described here are primarily concerned with enhancing liveness without breaking the privacy assurances made to honest participants.

## Interactive transaction construction with honest participants

An honest participant is one that complies with the protocol. Faulty peers may deviate by being unresponsive or by being actively malicious. In the honest setting, not only do we assume that the only kind of fault is being unresponsive, but peers are also expected to keep confidential all of the information pertaining to the protocol's execution.

When we do have some well-defined way to transmit messages from one peer to another, we can start to reason about how synchronization between peers can happen by using interactivity. Communication serves two purposes: peers exchange payment details directly with their counterparties, and send transaction contributions to the group as a whole.

For peer-to-peer channels, any transport that provides authentication, integrity and confidentiality may be used. This allows peers to send messages to each other directly, for initiating as well as carrying out transaction construction.

Group communication can be built out of peer-to-peer channels; this is known as gossip or rumor-spreading. Alternatively, a specialized broadcast channel implementation can be used. So long as each peer eventually receives all messages sent by every other peer, they will converge on the same transaction fragments, and combine them in the same way to obtain a consistent view of the unsigned transaction.

The honest setting accommodates geographically separated multisig wallets, coordination between separately managed funds within an organization, and collaborative batching. Before signing, every participant checks this transaction, ensuring their funds end up in the destinations they intended. Although the model assumes no malicious edits to the transaction, performing these checks is what enforces safety. Doing this ensures that if the assumption does not hold, the system still fails closed, and any faults that aren't explicitly accounted for in the model will only lead to denial of service, not loss of funds. Needless to say, this check applies to the more adversarial settings described below.

## Interactivity under different communication models

Because of this unanimity condition, a peer which is offline will not be able to sign its inputs. If a subset of participants can all agree that some other peers are faulty, they could recover by restarting transaction construction without those peers' inputs, allowing them to produce a valid transaction without those peers.

Deciding when a peer is unresponsive, the only kind of fault that is tolerated in the honest threat model, largely depends on how messages are transmitted. The distributed systems literature typically divides this into three communication models: asynchrony, partial synchrony and synchrony.[^dls] Each demands a different approach to fault tolerance. These models also apply to the more adversarial settings.

### Asynchronous

In the asynchronous communication model, messages may be delayed arbitrarily long, so when an expected message fails to arrive, we cannot assume the sender is faulty. This setting is the simplest in which correct behavior can be defined because it makes the weakest guarantees. If we assume all peers are honest, the only recourse is to keep waiting.

### Synchronous

Intuitively, a peer that has been unresponsive for too long can be considered faulty. By adding timeouts, we can recover liveness by simply giving up coordinating with such peers.

The synchronous communication model is typically in play whenever a protocol relies on specific timeout values, i.e. defining how long is "too long". This model assumes that the participants can agree on what time it is, and that all sent messages will arrive no later than some maximal delay. If a message that is expected to arrive fails to do so before the timeout elapses, the peer which was supposed to send is said to experience a crash fault, rendering it unresponsive for the remainder of the protocol, or an omission fault if it was temporarily unavailable and some of its messages were not delivered..

Note that such delays may be arbitrarily long, provided their bound is well defined, even if the underlying transport requires interactivity on a shorter time scale. For example, we might use TCP/IP with timeouts on the order of tens of seconds to interact with a store-and-forward service that allows peers to send each other messages with timeouts on the order of hours or days. The model assumed by the underlying transport or its parameters need not agree with the model assumed for transaction construction.

### Partial synchrony

Partial synchrony lies in between. Like the synchronous model, it assumes message delivery is timely, but unlike the synchronous model, the bound on the delay either isn't known or may not always apply, so simply waiting for a timeout duration will not suffice to obtain liveness. Typically this requires acknowledgement from some threshold fraction of participants in order for progress to be made.

## Net settlement

A motivating use case for interactive transaction construction, one of several, is more efficient and private on-chain payments. Several parties can batch arbitrarily many payments into one transaction. Each participant's inputs and outputs express only the net difference. Individual payment amounts need not appear on chain.

Net settlement adds safety considerations. Before signing, a participant must know that its funds reach the intended destinations. It can check outputs returning funds to itself directly; for a payment, it needs the payee to confirm that the transaction satisfies their agreement. Within each payment cycle at least one party will receive as much as it sends or more, and can therefore safely initiate confirmation. See the [concurrent PSBT specification](../psbt-concurrent.md#confirmation-of-successful-payment-prior-to-signing) for additional details.

## The semi-honest setting: adding privacy-preserving communication

An authenticated channel may identify the sender of a message, which can be problematic for privacy. Even if the sender isn't authenticated, transport-related metadata such as IP addresses can leak information about the sender. If transaction fragments are exchanged this way, this can indicate links between inputs and outputs that belong to the same user, even when the final transaction leaves those relationships ambiguous.

In the semi-honest setting, participants are still assumed to cooperate, but are no longer trusted with privacy. Instead we assume the adversary can see their observations, regardless of whether this information is leaked accidentally or deliberately shared.[^honest-but-curious] 

Preserving privacy requires anonymous broadcast to the group. Overlay networks such as Tor can be used to anonymously send messages to peers for relaying. The privacy guarantees of the underlying transport form the basis of message unlinkability, and once a message is not linked to its owner it can be relayed even on a non-anonymous channel.

Payment communication has different requirements, which also must be provided by the underlying transport. A sender must authenticate its receiver and obtain confirmation that the proposed transaction satisfies their agreement. However, this authentication can rely on a one-time code or pseudonym. The receiver doesn't need to authenticate the sender in order to be paid securely. Both counterparties know their payment amount, but need not disclose that relationship to the group or identify their transaction inputs and outputs to one another.

The privacy objective is to avoid revealing anything more than what is inherent in the transaction data to the world, and the minimal payment details to counterparties. Anonymous communication is a necessary but insufficient requirement for this; it does not prevent inference from amounts or transaction structure, nor from the wider transaction graph. The on-chain limitations described in the [problem definition](../collaborative_txn_privacy.md) still apply.

This setting is inherently more brittle, because when disruptive messages are shared anonymously not only is it unclear how to recover, in general it isn't possible to tell apart the disruptive messages from the honest ones.

## The Byzantine setting: resilience against malicious behavior

The semi-honest setting assumes that participants claim only what they are entitled to in outputs, and cooperate until the transaction is successfully constructed and signed. While crash faults can be detected depending on the communication model, there are of course many other ways participants can be disruptive, especially if they have malicious goals like preventing the other parties from transacting.[^byzantine-generals]

Participation is voluntary, and no party can be compelled to sign. The protocol therefore operates in a non-cooperative game-theoretic setting: agreements to transact are not binding, and must be self-enforcing through incentives. We therefore define an honest participant as one which intends to complete the protocol and sign, regardless of which permitted actions the other honest participants choose to take. The agreed conditions must preserve that incentive throughout construction; the coalition formation protocol, discussed at the end of this overview, provides a mechanism for negotiating those conditions and aligning incentives for cooperation. For now we will simply assume that the honest users' incentives are already aligned when transaction construction commences.

Under the rules of the semi-honest setting a malicious participant can add outputs exceeding its allocation. Because such outputs would be included as well, in general this may result in an invalid transaction even if it is fully signed. A malicious peer might also equivocate: give conflicting accounts of its actions to different peers. Or it might simply withhold a signature, causing delays. In the Byzantine setting the honest peers must be able to tolerate any such malicious behavior.

### Optimistic transaction construction

The first problem is to establish that transaction fragments are valid without attributing them to specific participants. Validity means that the cost of an output is covered by input funds without double spending. Validity can be proven using zero-knowledge proofs, but this is costly, so we would like to avoid it where possible.

Due to the unanimity condition even in the Byzantine setting, successful termination requires that all participants in a particular transaction construction session comply with the protocol, which includes being responsive. When this happens to be the case, the optimistic approach is to let everything proceed exactly as in the semi-honest setting: Participants anonymously add their fragment, and once everyone acknowledges the same balanced transaction they can simply sign. The Byzantine fault-tolerant variant of Fungi is therefore designed to recover liveness by identifying at least one input controlled by a faulty peer, and then attempting transaction construction again with the faulty inputs excluded. Once all faulty participants have been excluded the honest participants will be able to successfully carry out transaction construction.

### Validity proofs

Assuming the input set has been finalized, outputs and fee contributions reduce the remaining available funds. If their total cost exceeds the total input value the unsigned transaction will not be valid even if signed, and at least one party is attempting to overspend. Any participant can also anonymously force termination of the optimistic path by adding an oversized fee contribution.

Once overspending has been detected, uncertified output and fee contributions are no longer allowed. Instead zero-knowledge proofs establish that outputs are covered by input funds. This includes payments between participants, and must not reveal the details of how each participant allocates its funds.

The purpose of the proofs is to restore the possibility of completion *without* sacrificing privacy, which is why they are zero-knowledge proofs. They mainly prevent the same funds from being claimed more than once. They do not replace each participant's final approval, nor can they compel any participant into providing the remaining proofs or signatures. They ensure that honest, responsive participants can successfully add all of their intended inputs and outputs to the shared state without obstruction.

Invalid transactions cannot spend any coins. Only valid transactions have consequences for the owners of the inputs. The sense in which the fragments themselves must be valid according to the proofs is that when combined they would result in a valid transaction if fully signed. Taken together with the incentive compatibility assumption, the lack of obstruction removes any reason for honest participants to withhold their signatures: by following the protocol the correct destination for all of their funds will be secured. And if we also assume consistency of the shared state, validity proofs ensure there is no way to poison the state so the transaction will be invalid, so maximally disruptive manipulation of the shared state amounts to withholding a signature, the only way the malicious participant can ensure a transaction does not have consequences.

A widely circulated misconception is that validity proofs with zero knowledge somehow provide privacy. This is false. All they can do is enforce validity, and if done correctly, they can enforce this without destroying privacy. They cannot contribute to privacy.

### Consistency, liveness and termination in the presence of Byzantine faults

Valid fragments can do nothing to establish the consistency property nor do they preclude equivocation itself; they can only force it to be detectable when attempted. A malicious peer can send two independently valid but conflicting fragments to different honest peers. In order to detect such equivocations, the honest nodes must observe the conflict, allowing both to be removed and maintaining the invariant that the unsigned transaction must be valid if signed.

To know when they can sign, peers need to communicate not only the fragments themselves, but also which fragments they have seen and whether they agree to proceed at the end of a particular phase. Misbehaving peers might then attempt to prevent progress by disrupting convergence by the honest peers.

In typical definitions of Byzantine fault-tolerant distributed consensus or agreement protocols, once a majority of honest peers has settled on a certain state, any lagging honest peers will only ever accept updates that progress towards that state when they are able to catch up. Unfortunately for our purposes this isn't enough for fault-tolerant transaction construction, since *successful* termination of the protocol requires unanimity.

If a majority of the honest users can agree on a set of inputs and outputs, but one of the honest participants not in this majority still hasn't submitted all of their outputs, then it would rightfully withhold its signatures even if it does come back online. When assuming the asynchronous communication model, this can delay termination indefinitely, and achieving a majority is not sufficient for termination.

The validity proofs added in the previous section make it possible to interpret signatures on the inputs as an honest signal, pun intended: signatures are an honest signal because they aren't costless, but may have consequences such as the mining fees if the other parties also sign, and secondly, signatures signal honest participation in the protocol, because the protocol makes it safe for honest participants to broadcast them regardless of the actions of other users.

What such a majority can provide, therefore, is a mechanism for agreeing on which inputs belong to peers that have failed to complete the protocol. Depending on the communication model, some kind of timeout or recovery condition will be reached, and any inputs for which signatures have not yet been provided can be defined as out of compliance with the protocol. A new transaction construction session can then be attempted, excluding those inputs.

Under synchrony or partial synchrony (specifically the eventual synchrony variant), if a sufficient threshold of peers can all agree it has been too long, then they can initiate such a recovery session. A threshold of peers agreeing implies a majority of honest peers agreeing. Note that agreement by a majority of honest participants requires a supermajority threshold. A quorum is a set of peers meeting the required agreement threshold. Given $n = 3f+1$ where at most $f$ are faulty, a quorum of $2f+1$ peers will have at least $f+1$ honest peers in it agreeing.

So long as the notion of "too long" is well defined (consistent with the communication model) and agreed by a quorum, if there are $f$ inputs owned by misbehaving peers honest parties should be able to successfully complete a run of the protocol after $O(f)$ attemptsby simply excluding those inputs as it becomes apparent that they are unresponsive.

## Synchronization protocol

The abstract synchronization requirements of the previous sections can be realized by a family of related constructions.

### Byzantine eventual consistency

The simplest of these is Byzantine Eventual Consistency by Martin Kleppmann and Heidi Howard.[^bec] In this model, messages, or transaction fragments as in our case, are committed to a [Merklized](https://en.wikipedia.org/wiki/Merkle_tree) causal log. For example, if Alice is adding an output, the output itself would be the payload of her message, and the envelope would contain references to Alice's last message, as well as the messages of other peers, referenced by hash.

In the naive version of their protocol (they describe a more optimized version), whenever a message is received, if the receiving peer does not know what a hash in its references commits to, it will request the preimage from the peer which sent this message, and after a finite number of such recursive queries and round trips it will eventually reach a message it has already seen. Signatures on the messages authenticate their authorship, allowing messages to be relayed via intermediate peers, and for any equivocations to be detectable. If the payloads are subject to validity constraints and merging independently accepting updates preserves these constraints, as Kleppmann and Howard show, this is sufficient for *Byzantine* eventual consistency: loosely speaking, even in the presence of Byzantine nodes, honest peers will eventually converge on the same set of messages.

For privacy-preserving transaction construction, the payload should be a list of transaction fragments delivered anonymously to the peer which constructs the message. In BEC, these messages form an unstructured directed acyclic graph (DAG), with each honest peer's messages forming a linked list which also links into the linked lists of other peers. The depths of these lists are not synchronized or bounded.

Because in our setting they collect several state-related messages submitted by other participants, we'll call these messages blocks, in line with conventions in similar protocols.

### Cordial miners inspired invariants

Cordial Miners[^cordial-miners] is one of a family of so-called block DAG protocols, which also includes DAG-Rider.[^dag-rider] In these protocols, a fixed set of participants, usually called validators, produce blocks that, similarly to BEC, refer to other validators' blocks, and the consensus protocol involves defining a deterministic function that produces a consistent priority order when blocks conflict, that all honest validators will agree on. The cordiality requirement is that for $n = 3f + 1$ validators, every block at height $h$ will have $t = n - f$ parent blocks with height $h - 1$. In addition to setting up the required thresholds for Byzantine fault-tolerant consistency, this also serves as a flood protection mechanism.

By waiting to reconcile the set of fragments with neighboring peers before building a block, peers can adhere to the cordiality while minimizing the number of blocks sent overall, which is more appropriate for the goal of coming to consensus over a finite sequence of sets with minimal end-to-end latency, as opposed to maximizing throughput and minimizing confirmation latency, which is the more typical design goal for DAG consensus algorithms.

Note that these restrictions on the structure still consist of a special case of Kleppmann and Howard's [hash-consed](https://en.wikipedia.org/wiki/Hash_consing) DAG; every block DAG structure is also a valid Byzantine eventual consistency causal log structure. Because of the validity proofs on transaction fragments, and the concurrent PSBT semantics we do not need an ordering but only a set union.

Whether or not eventual consistency will suffice for synchronizing a set union depends on the communication model. When it is not sufficient, the blocks which do arrive and their parent blocks can be used to coordinate failure recovery, identifying responsive peers. In any case we do not need to ensure the stronger notion of safety that cordial miners and other such protocols provide, because of the unanimity requirement, and the consensus machinery is only needed for coordinating failure recovery.

### Fault tolerance as branched execution

Under asynchrony and in the presence of (Byzantine) faults, due to the unanimity requirement the best consistency guarantee that can be made is eventual consistency. No liveness guarantee can be made in the presence of faults for a particular run of the transaction construction protocol because liveness relies on starting a new protocol, and that requires some kind of synchronization between the honest peers.

Recall that when multiple transactions attempt to spend some of the same coins, it is up to miners to determine which one (if any) will be confirmed in a block. Miners are assumed to follow their incentives, maximizing fee revenues. Even if transaction replacement wasn't useful or desirable, there is no mechanism that can enforce that unspent outputs are exclusively bound to one transaction construction session over another without *global* consensus.

As we have seen, the success path always reaches termination, and can only reach it by observing unanimous agreement, and when that is possible progress requires only eventual consistency. Validity proofs reduce Byzantine faults to omission faults, so recovering liveness in the presence of failure requires partial synchrony assumptions at the very least.

Since input exclusivity is neither desirable nor enforceable, we can embrace its absence and reframe liveness in a simpler way by treating all failure recovery as branching off another instance of the protocol with a subset of the participants precisely when that subset of the participants can agree among themselves that a failure condition has been detected. Such agreement inherently requires synchrony or partial synchrony, and so explains why this is needed for fault tolerance. In this case the blocks at some height $h$ with $t < n$ parent blocks will be produced as part of the recovery synchronization protocol on top of which a new transaction construction session will commence. If messages are delivered allowing a block at height $h$ to be produced with $t = n$ messages, the asynchronous base protocol can resume progress resulting in the diverging protocol states at height $h$. This special case has the same structure as all-to-all broadcast.

The reason this framing is simpler is that recovery attempts do not need to terminate the run of the protocol that they are trying to recover. In the case that both branches eventually succeed, Bitcoin itself will adjudicate the conflicting transactions. We can treat failure recovery as a (more) synchronous layer building on a fundamentally asynchronous optimistic base protocol with BEC semantics.

### Centralization spectrum and TEE-based liveness

All participants can submit their transactions to a designated validator, with all other validators' blocks simply acknowledging the designated validator's blocks. 

In principle, it is possible to decouple the validator role from the participant role and setting $n = 1$, where blocks form a linked list. This instantiates a version of the protocol based on a trusted coordinator. Note that "trust" here is meant only with regard to liveness, not to privacy. If a coordinator is trusted with privacy, which is the norm for such services,[^trusted-coordinators] validity proofs and anonymous broadcast are little more than privacy theater. A centralized protocol where the server simply does not keep a permanent record would be strictly better because users would be informed and computational and bandwidth resources would not be pointlessly wasted, degrading reliabiliy (which itself a privacy concern).

Note that this does not actually require $n = 1$ to shift the communication and coordination complexity onto a more powerful node; clients who choose to follow a particular attested state can still submit acknowledgements to it, and simply echo the parent block set commitments of the attested blocks when acknowledging the same height with minimal communication complexity. Therefore there is no need to actually decouple those roles, it is sufficient to just shift the workload to one validator, unless such a validator is not itself a participant in the transaction.

A trusted execution environment (TEE) can shift this trust assumption from the service operator to the hardware vendor and its attestation infrastructure. Attestation provides verifiable evidence that designated validation code executed in the claimed protected environment. Clients can therefore accept its validation of the protocol state without trusting the operator to execute that code faithfully, instead trusting the vendor’s hardware isolation and attestation guarantees. This additional trust assumption can improve liveness and consistency under weaker quorum assumptions, while reducing clients’ validation work. It does not relax the requirement for unanimous transaction signing; private allocations and spending authority remain with the participants.

This has two primary advantages. The first is that bandwidth or compute restricted devices can participate asymmetrically in dissemination, validation, etc. If the trust assumption fails, that is still only a liveness violation, and doesn't compromise on safety or privacy. Presumably such clients are too constrained for scalable Byzantine fault tolerance. On the other hand, if the TEE assumption holds, liveness can tolerate a dishonest majority allowing successful termination after $O(f)$ attempts even if $f = n - 2$ (note that $f = n - 1$ holds trivially, that's just falling back to a unilateral transaction).

In other words, using essentially the same unmodified block DAG structure we can accommodate multiple communication models and trust assumptions, to accommodate a variety of client capabilities.

## Coalition formation

Until now we have assumed an initial set of participants, some of which will be removed in new branches of the protocol as these are spun off in response to failures. We have not discussed how this initial set of participants is formed. The honest and semi-honest settings imply some degree of trust, which means such groups can form out of band.

The Byzantine setting, on the other hand, is designed to facilitate transacting with potentially malicious, ideally randomly selected peers, because as discussed in the [problem definition](collaborative_txn_privacy.md) document, such randomness is required for privacy guarantees to be robust, but this still depends on the initial set of participants being defined. For this purpose we define a coalition formation protocol, and that comes with its own set of challenges, first among which is that it operates in the permissionless setting.

The [coalition formation](./coalition_formation.md) protocol is designed to allow mutually distrusting strangers to bootstrap transaction construction using a market-based mechanism. Coalition formation games, in game theory, typically refer to the cooperative game theory setting, where agreements are binding and can be enforced by some kind of mechanism. While Bitcoin can provide such a construct, analogously to the function of the court system, the current consensus rules require some kind of contract to be anchored in a confirmed transaction, i.e. binding agreements require creating new transactions and waiting for them to confirm.[^coinswap] In order to build transactions without having already built transactions, we must therefore assume the non-cooperative setting. Coalition formation in the non-cooperative setting can only rely on incentives.

When preferences over the coalition structure are in play (the cost function), in so-called hedonic games, it is often very hard (also in an algorithmic sense) to find stable coalition structures, as the preferences of the participants may conflict. In their most general form, such game descriptions are enormous as the preferences are defined over a large combinatorial object but even when many assumptions are made, like constraining the kinds of preferences the participants may have, it is still generally hard to find stable equilibria.[^hedonic] Complicating matters further, sharing the preferences would itself be a privacy leak, so we would prefer to limit that as much as possible, and certainly we cannot assume a mechanism that optimizes outcomes by just being able to read these preferneces.

Fortunately, some of these difficulties of hedonic games can be bypassed with the introduction of a transferable utility, and assigning the coalition itself a payoff, which can be redistributed. In our use case this payoff originates from any blockspace savings from net settlement, and the privacy benefits from collaboration. This surplus is not observable, it is the sum of subjective payoffs depending on individual participants' preferences (which in turn depend on their circumstances, privacy threat model, etc). While this does not guarantee stability, if a stable coalition structure exists, a transferable utility can make the process of finding one much easier by iterated bilateral negotiation. However much these benefits are worth it to participants, if this surplus exists, then it can be voluntarily redistributed as sats among the participants (i.e. via a fee mechanism) aligning incentives for collaborative transaction construction, so that all coalition members stand to gain from participating.

This is exactly the mechanism that the coalition formation protocol attempts to build: co-spend proposals are anonymous and confidential proposals, each of which is a bundle of bilateral agreements between the proposer and the owner of the other UTXOs listed in the proposal. The distinguishing feature of co-spend proposals is that they can be aggregated together, which generalizes a JoinMarket-like fee mechanism: it allows multiple "takers" to pay a single "maker" as a kind of group buy, as well as multiple independent "makers", all in the same transaction. This generality means that the distinction between taker and maker is removed; any participant can play both roles in a single transaction, depending on the co-spend proposals it makes or accepts.

Coalition formation proposals bundle together a collection of co-spend proposals, each of which has been unanimously accepted. Unanimous acceptance of a coalition formation proposal by the owners of all inputs named in all proposals kicks off the permissioned transaction construction with an initial set of inputs, and the terms of the aggregated co-spend proposals in effect. The aggregator role is undertaken by peers which proposing coalition formation proposals.

[^safety-liveness]: B. Alpern and F. B. Schneider, [*Defining Liveness*](https://www.cs.cornell.edu/fbs/publications/85-650.pdf) (1985). Formal definitions of safety and liveness, and their decomposition of system properties.

[^dls]: C. Dwork, N. Lynch and L. Stockmeyer, [*Consensus in the Presence of Partial Synchrony*](https://groups.csail.mit.edu/tds/papers/Lynch/jacm88.pdf) (1988). The introduction contrasts synchronous and asynchronous models and defines the two forms of partial synchrony used here: an unknown timing bound, or a bound that holds only eventually.

[^honest-but-curious]: A. Paverd, A. Martin and I. Brown, [*Modelling and Automatically Analysing Privacy Properties for Honest-but-Curious Adversaries*](https://ajpaverd.org/publications/casper-privacy-report.pdf). Section II-A defines an honest-but-curious participant as following the protocol while attempting to infer all possible information from legitimately received messages; the paper studies undetectability and unlinkability.

[^byzantine-generals]: L. Lamport, R. Shostak and M. Pease, [*The Byzantine Generals Problem*](https://lamport.azurewebsites.net/pubs/byz.pdf) (1982). The foundational treatment of agreement in the presence of arbitrary faults, including conflicting messages sent to different participants.

[^bec]: M. Kleppmann and H. Howard, [*Byzantine Eventual Consistency and the Fundamental Limits of Peer-to-Peer Databases*](https://arxiv.org/abs/2012.00472) (2020). Byzantine causal broadcast and invariant-preserving replication; see §2.2–3 for the requirement that independently valid updates remain valid when merged.

[^cordial-miners]: I. Keidar, O. Naor, O. Poupko and E. Shapiro, [*Cordial Miners: Fast and Efficient Consensus for Every Eventuality*](https://arxiv.org/abs/2205.09174) (2023). Blocklace dissemination, equivocation exclusion and ordering, with asynchronous and eventually synchronous variants.

[^dag-rider]: I. Keidar, E. Kokoris-Kogias, O. Naor and A. Spiegelman, [*All You Need is DAG*](https://arxiv.org/abs/2102.08325) (2021). DAG-Rider separates construction of a communication DAG from local ordering of its proposals.

[^trusted-coordinators]: Y. Kogman, [*Reiterating centralized coinjoin (Wasabi & Samourai) deanonymization attacks*](https://groups.google.com/g/bitcoindev/c/CbfbEGozG7c/m/w2B-RRdUCQAJ)

[^coinswap]: For example [CoinSwap](https://openswap.live/) is such a protocol which relies on atomic swap contracts, designed with privacy in mind.

[^hedonic]: D. Peters and E. Elkind, [*Simple Causes of Complexity in Hedonic Games*](https://arxiv.org/abs/1507.03474) (2015). Shows how modest expressiveness in preferences can make deciding the existence of stable outcomes computationally hard.
