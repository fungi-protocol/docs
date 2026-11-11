---
type: Specification
title: Block DAG
description: The validator blocks both tracks share, with their objects, nonce commitments and equivocation evidence, genesis, causal order and frontiers.
status: draft
stale_after: 2027-04-23T00:00:00Z
---

<!-- cspell:words Alpos antichain Cachin consed Ehud Heidi Kleppmann Kogias Kokoris Malkhi Nayak Spiegelman Tackmann Zanolini Idit Keidar mathcal mathrm Naor Oded operatorname Ouri permissioned Pieter Poupko Wuille Kogman Merklized Samourai unlinkable -->

# Block DAG

## Synchronizing protocol state

The abstract state sharing requirements of [transaction construction](transaction-construction.md) can be realized by a family of related constructions.

### Byzantine eventual consistency

The general starting point is Byzantine Eventual Consistency (BEC) by Martin Kleppmann and Heidi Howard.[^bec] In this model, messages, or transaction fragments as in our case, are committed to a [Merklized](https://en.wikipedia.org/wiki/Merkle_tree) causal log. For example, if Alice is adding an output, the output itself would be the payload of her message, and the envelope would contain references to Alice's last message, as well as the messages of other peers, referenced by hash.

In the naive version of their protocol (they describe a more optimized version), whenever a message is received, if the receiving peer does not know what a hash in its references commits to, it will request the preimage from the peer which sent this message, and after a finite number of such recursive queries and round trips it will eventually reach a message it has already seen. Signatures on the messages authenticate their authorship, allowing messages to be relayed via intermediate peers, and for any equivocations to be detectable. If the payloads are subject to validity constraints and merging independently accepted updates preserves these constraints, as Kleppmann and Howard show, this is sufficient for *Byzantine* eventual consistency: loosely speaking, even in the presence of Byzantine nodes, honest peers will eventually converge on the same set of messages.

For privacy-preserving transaction construction, the payload should be a list of transaction fragments delivered anonymously to the peer which constructs the message. In the general BEC construction, these messages form a directed acyclic graph (DAG), with each honest peer's messages forming a linked list which also links into the linked lists of other peers. BEC itself does not require the depths of these lists to be synchronized or bounded; the block DAG specializations below impose additional structure.

Because in our setting they collect several state-related messages submitted by other participants, we'll call these messages blocks, in line with conventions in similar protocols.

### Cordial miners inspired invariants

Cordial miners[^cordial] is one of a family of so-called block DAG consensus protocols.[^dag-rider] In these protocols, a fixed set of participants, usually called validators, produce blocks that, similarly to BEC, refer to other validators' blocks, and the consensus protocol involves defining a deterministic function that produces a consistent priority order when blocks conflict, that all honest validators will agree on. The cordiality requirement is that for $n = 3f + 1$ validators, every block at height $h$ will have $t = n - f$ parent blocks with height $h - 1$. In addition to setting up the required thresholds for Byzantine fault-tolerant consistency, this also serves as a flood protection mechanism.

By waiting to reconcile the set of fragments with neighboring peers before building a block, peers can adhere to the cordiality while minimizing the number of blocks sent overall, which is more appropriate for the goal of coming to consensus over a finite sequence of sets with minimal end-to-end latency, as opposed to maximizing throughput and minimizing confirmation latency, which is the more typical design goal for DAG consensus algorithms.

Note that these restrictions on the structure still consist of a special case of Kleppmann and Howard's [hash-consed](https://en.wikipedia.org/wiki/Hash_consing) DAG; every block DAG structure is also a valid Byzantine eventual consistency causal log structure. Because of the validity proofs on transaction fragments, and the concurrent PSBT semantics we do not need an ordering but only a set union.

In the optimistic track, borrowing the cordial structure and setting $t = n$ to fulfill the unanimity requirement means that under asynchrony eventual consistency is the best guarantee we could make. Under synchrony or partial synchrony, the more standard $t = 2f + 1$ lets responsive peers coordinate the recovery track. Note that in principle $t$ could be lowered further, for partition tolerance or recovery in the presence of a dishonest majority, but this is a substantial qualitative difference in guarantees and so it has not yet been explored.

### Centralization spectrum and optional TEE-based liveness

All participants can submit their transaction fragments to a designated validator, with all other validators' blocks simply acknowledging the designated validator's blocks. These acknowledgements can have empty payloads, concentrating collection and validation work on one peer.

In principle, it is possible to decouple the validator role from the participant role, with one validator serving many transaction participants. That validator's blocks form a linked list. This instantiates a version of the protocol based on a trusted coordinator. Note that "trust" here is meant only with regard to liveness, not to privacy. If a coordinator is trusted with privacy, which is the norm for such services,[^trusted-coordinators] validity proofs and anonymous broadcast are little more than privacy theater. A centralized protocol where the server simply does not keep a permanent record would be strictly better because users would be informed and computational and bandwidth resources would not be pointlessly wasted, degrading reliability (which is itself a privacy concern).

Note that centralizing the bulk of this communication and coordination work on one node does not require decoupling the validator and participant roles, nor does it confer any special privileges to this de-facto leader; on the DAG model participants which only acknowledge the blocks of a single peer, can make those acknowledgement in the form of blocks that echo the content bearing blocks with minimal communication complexity. No protocol modifications so long as this validator is still a participant in the transaction, and only the introduction of a validator that is not a participant would require these roles to be decoupled.

Going further, a trusted execution environment (TEE) can shift trust assumptions from a participant to the hardware vendor on which the participant is running the protocol. Such a participant can produce attestations about exactly what code is being executed in the TEE enclave, which the other participants can verify. Clients could therefore accept its validation of the protocol state without trusting the operator to execute that code faithfully, instead trusting the vendor’s hardware isolation and attestation guarantees.

The reason such an additional trust assumption may be desired in some circumstances is that it improves liveness and consistency under weaker quorum assumptions, while reducing clients’ validation work further. This does not relax the requirement for unanimous transaction signing, nor is the TEE trusted with protecting privacy; private allocations and spending authority remain with the participants and their messages must remain unlinkable. This provides an alternative path to liveness when clients are too constrained for scalable Byzantine fault tolerance, or when the conditions for Byzantine fault tolerance don't hold (for example a dishonest majority of validators).

In other words, using essentially the same unmodified block DAG structure we can accommodate multiple communication models and trust assumptions, to accommodate a variety of client capabilities and circumstances.

## Nonce commitments and compact equivocation evidence

Valid fragments can do nothing to establish the consistency property nor do they preclude equivocation itself; they can only force it to be detectable when attempted. A malicious peer can send two independently valid but conflicting fragments to different honest peers. In order to detect such equivocations, the honest nodes must observe the conflict, allowing both to be removed and maintaining the invariant that the unsigned transaction must be valid if signed.

To know when they can sign, peers need to communicate not only the fragments themselves, but also which fragments they have seen and whether they agree to proceed at the end of a particular phase. Misbehaving peers might then attempt to prevent progress by disrupting convergence by the honest peers.

$$
zG=R+eP_i,\qquad z=r+ex_i\pmod q.
$$

$$
x_i=(z_1-z_2)(e_1-e_2)^{-1}\pmod q.
$$

Other chapters link to these sections:

## Optional attested validation and acknowledgement relay

## Optimistic and recovery tracks

## References

[^cordial]: Idit Keidar, Oded Naor, Ouri Poupko and Ehud Shapiro. [Cordial Miners: Fast and Efficient Consensus for Every Eventuality](https://arxiv.org/abs/2205.09174).

[^bec]: M. Kleppmann and H. Howard, [*Byzantine Eventual Consistency and the Fundamental Limits of Peer-to-Peer Databases*](https://arxiv.org/abs/2012.00472) (2020). Byzantine causal broadcast and invariant-preserving replication; see §2.2–3 for the requirement that independently valid updates remain valid when merged.

[^dag-rider]: I. Keidar, E. Kokoris-Kogias, O. Naor and A. Spiegelman, [*All You Need is DAG*](https://arxiv.org/abs/2102.08325) (2021). DAG-Rider separates construction of a communication DAG from local ordering of its proposals.

[^trusted-coordinators]: Y. Kogman, [*Reiterating centralized coinjoin (Wasabi & Samourai) deanonymization attacks*](https://groups.google.com/g/bitcoindev/c/CbfbEGozG7c/m/w2B-RRdUCQAJ)
