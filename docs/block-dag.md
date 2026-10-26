---
type: Specification
title: Block DAG
description: The validator blocks both tracks share, with their objects, nonce commitments and equivocation evidence, genesis, causal order and frontiers.
status: draft
stale_after: 2027-04-23T00:00:00Z
---

<!-- cspell:words Alpos antichain Cachin consed Ehud Heidi Kleppmann Kogias Kokoris Malkhi Nayak Spiegelman Tackmann Zanolini Idit Keidar mathcal mathrm Naor Oded operatorname Ouri permissioned Pieter Poupko Wuille -->

# Block DAG

🤖 Both tracks use the block DAG defined here.

## Synchronizing protocol state

The abstract state sharing requirements of [transaction construction](transaction-construction.md) can be realized by a family of related constructions.

🤖 These constructions form a ladder of increasingly narrow special cases. Each step restricts the one before it, so every structure further down is still an instance of those above it:

1. **Byzantine eventual consistency**: a hash-linked causal log of authenticated messages.
2. **A block DAG with cordiality**: a fixed set of validators, each block referring to $t$ blocks of the previous height.
3. **A threshold per track**: $t = n$ on the optimistic track, $t \lt n$ on the recovery track.
4. **One validator collecting**: the others acknowledge its blocks. This splits the workload within the same model, on either track.
5. **TEE attestations**: an optional extension to all blocks, which certain clients can choose to trust, even when they act as validators.

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

🤖 Peers need not make identical trust assumptions: one may accept a vendor's attestations while another validates independently. This is related to asymmetric distributed trust, which models each participant's assumptions about which combinations of peers may fail.[^asymmetric-trust] Flexible BFT provides a complementary precedent for interpreting a shared protocol transcript under different fault and timing assumptions.[^flexible-bft] These are relevant frameworks rather than proofs of this TEE construction; its guarantees depend on the chosen acceptance rules and trust assumptions.

In other words, using essentially the same unmodified block DAG structure we can accommodate multiple communication models and trust assumptions, to accommodate a variety of client capabilities and circumstances.

## 🤖 Objects {#objects}

A construction instance identifies a fixed validator set and its permitted inputs. A phase identifies the interpretation and admission rules for contributions within that instance. Recovery proposals can establish successor instances with different membership.

A **contribution** is an application message, such as a transaction fragment, proof, acknowledgement or coalition proposal. Anonymous submission prevents a validator's inclusion of a contribution from identifying its author.

A **block** is a product type

$$
b=(M_b, B_b, s_b, R_b^{\mathrm{opt}}, R_b^{\mathrm{rec}}, \kappa_b, \phi_b, E_b),
$$

with the following components:

| Component | Meaning |
| --- | --- |
| $M_b$ | Set of included messages; may be empty for an acknowledgement block. |
| $B_b$ | Set of parent blocks. |
| $s_b$ | Optional self-parent block, from the same validator. |
| $R_b^{\mathrm{opt}}$ | Nonce point committed for signing the validator's next optimistic block. |
| $R_b^{\mathrm{rec}}$ | Nonce point committed for signing the validator's next recovery block. |
| $\kappa_b$ | Block type: optimistic ($t=n$) or pessimistic recovery ($t<n$). |
| $\phi_b$ | Phase within that type's protocol. |
| $E_b$ | Optional extensions encoded as type-length-value (TLV) fields. |

Type and phase may be implicit in the protocol context rather than separately encoded. The optional self-parent is a distinct component from the parent set. Causal ancestry follows both the parent-set references and the self-parent, when present. The block is authenticated by its validator; the signature encoding remains to be specified. Every validator block commits separate nonce points for its next optimistic and recovery signatures.

Optimistic blocks coordinate transaction construction. Recovery blocks coordinate fault-tolerant, permissioned coalition formation so that a new transaction construction instance can start. The recovery type describes the fault model being accommodated, not evidence that a particular participant is faulty.

## 🤖 Optional block extensions {#optional-block-extensions}

Blocks carry optional protocol extensions as type-length-value (TLV) fields. A reader can skip an unknown field using its length. Ignoring an extension leaves the core block interpretation unchanged; an extension cannot silently redefine parent references, messages, thresholds or phase-transition rules. Extensions can supply additional evidence that a peer elects to use under its own validation policy.

One extension carries a trusted execution environment (TEE) attestation. It binds the claimed validation result to the relevant block contents, parent-set commitment, instance and phase, and identifies the executed validation code. A peer may rely on that evidence under its hardware-vendor and attestation trust assumptions, while another peer ignores it and validates independently. The attested statement must exclude the attestation bytes themselves to avoid a circular commitment. TLV identifiers, canonical encoding and the precise attested statement remain to be specified.

## 🤖 Optional attested validation and acknowledgement relay {#optional-attested-validation-and-acknowledgement-relay}

🤖 As in the [centralization spectrum](#centralization-spectrum-and-optional-tee-based-liveness), a validator can leave message collection to other validators. Its own blocks then have empty message sets, $M_b=\varnothing$, and serve as acknowledgements of the blocks they reference.

Peers can follow a trusted node's validation, or use attestations from a validator with a TEE. In either case, each retains its validator key and produces its own acknowledgement blocks. Configuring the peers to follow one trusted node provides the single-server arrangement without introducing a separate protocol.

The attested validator supplies the parent set needed for a peer to issue its acknowledgement of the preceding block. After checking the attestation and its context, the peer can use those parent commitments in its own acknowledgement block, retaining its self-parent and nonce commitments. Thus constrained peers need not reconstruct the parent set by independently processing every relayed contribution and acknowledgement.

The exchange is interleaved:

1. A TEE-backed validator publishes an attested block containing the parent-set evidence needed to acknowledge the preceding block.
2. Other validators issue their individual acknowledgement blocks using that evidence; their message sets can be empty.
3. The next TEE-backed block references the preceding TEE-backed block and the other validators' acknowledgements, relaying them and supplying the evidence for the next acknowledgements.

The validator relays acknowledgements rather than signing on behalf of their authors. Support still counts the distinct validators whose acknowledgements are represented. Peers can independently validate the same DAG, and multiple validators may provide attestations; the profile does not create a privileged protocol leader.

The attestation can certify validation and satisfaction of the applicable agreement predicate. It does not authorize a change to that predicate: unanimous phases still require all required acknowledgements, and transaction signing still requires the input owners. Private allocation information and spending keys are not supplied to the TEE. Peers retain local checks needed to bind their own contributions, proofs and signatures to the intended instance and privacy context. The optional trust assumption reduces validation work and can support stronger liveness under the selected recovery policy.

## Nonce commitments and compact equivocation evidence

Valid fragments can do nothing to establish the consistency property nor do they preclude equivocation itself; they can only force it to be detectable when attempted. A malicious peer can send two independently valid but conflicting fragments to different honest peers. In order to detect such equivocations, the honest nodes must observe the conflict, allowing both to be removed and maintaining the invariant that the unsigned transaction must be valid if signed.

To know when they can sign, peers need to communicate not only the fragments themselves, but also which fragments they have seen and whether they agree to proceed at the end of a particular phase. Misbehaving peers might then attempt to prevent progress by disrupting convergence by the honest peers.

🤖 Let $P_i=x_iG$ be validator $i$'s public signing key in a group of prime order $q$. Each block commits two independently generated nonce points, $R_b^{\mathrm{opt}}$ and $R_b^{\mathrm{rec}}$. A successor signature must use the point committed for its track in the preceding signing block. The two commitments allow an optimistic successor and a recovery successor without treating that permitted branching as equivocation. Each individual commitment may authorize only one distinct signed block.

🤖 For a Schnorr signature with committed nonce $R=rG$, response $z$ and challenge $e$, verification checks

$$
zG=R+eP_i,\qquad z=r+ex_i\pmod q.
$$

🤖 The challenge binds the public key, nonce point and complete signed block context, including the instance, track and predecessor commitment.[^schnorr] If the validator signs two distinct blocks using the same committed nonce, yielding distinct challenges $e_1\neq e_2$, their responses reveal

$$
x_i=(z_1-z_2)(e_1-e_2)^{-1}\pmod q.
$$

🤖 Anyone who obtains both signatures can extract this scalar. Other peers need only receive $x_i$ and check $x_iG=P_i$; they do not need to obtain the equivocated blocks. The validator private key therefore serves as compact, independently verifiable equivocation evidence. Repeating an identical signature is not equivocation, and using the two distinct track commitments as intended does not expose the key.

🤖 Strictly, the scalar proves that the validator key is exposed: deliberate disclosure or compromise produces the same evidence. The protocol treats this as sufficient to disqualify the key without requiring attribution to a particular pair of conflicting blocks. Once exposed, signatures under that key cannot establish who produced subsequent messages. Validator keys must be separate from Bitcoin spending keys and other secrets whose exposure would violate theft resistance or privacy.

🤖 The validator key is the online key endorsed by the coin owner's BIP-322 proof during coalition formation. The revealed scalar, together with that endorsement or a reference to it, forms a coin-associated fraud proof. A recipient checks both $x_iG=P_i$ and the endorsement binding $P_i$ to the coin. The recipient need not obtain the conflicting blocks or participate in the construction instance where the key was exposed.

🤖 This fraud proof can be gossiped through the permissionless coalition-formation order book using the same peer reconciliation mechanism as advertisements and proposals. Peers that validate it can ban the endorsed coin from subsequent coalition formation. Replacing the online key does not remove evidence against that coin. This is a protocol admission decision, not a restriction on spending the coin under Bitcoin consensus. The endorsement scope determines which coin or coins the evidence applies to.

🤖 The encoding must unambiguously identify the predecessor nonce commitment consumed by each signature, including the first signature on each track and transitions to successor instances. Nonce normalization and challenge construction must preserve the extraction equation. These details remain part of the signature profile.

## 🤖 Genesis {#genesis}

The coalition formation proposal serves as the instance's genesis, denoted by $g$. In the honest and semi-honest settings, an equivalent initiation message serves the same role. It establishes the construction context, including the initial inputs and validator membership $N$, with $n=|N|$. Every initial-input owner participates as a validator through its enrolled online key. Genesis is the common root within this instance; its representation need not be identical to an ordinary validator block.

## 🤖 Optimistic and recovery tracks {#optimistic-and-recovery-tracks}

Genesis and the two acknowledgement layers of [kickoff](optimistic-track.md#kickoff) have instance-local heights 0, 1 and 2. From height 3 onward, progress has two branches: the optimistic or unanimous branch with $t=n$, and a pessimistic recovery branch with $t<n$ and improved liveness under its chosen recovery assumptions. This does not require producing two blocks for every step. Until a reduced-threshold block is published, the recovery overlay contains no blocks; publication of such blocks activates it. The recovery track is described in the [recovery track](recovery-track.md) chapter.

🤖 This differs from typical DAG consensus, including protocols that switch between modes or tracks. There, every mode or track must agree on a single log. Here, the optimistic track requires unanimity, and the two tracks may race: different sessions may attempt to spend the same inputs. That can't be prevented in a permissionless setting, and it is useful for replace-by-fee (RBF). Racing is not a safety violation, because Bitcoin itself resolves conflicts between competing transactions.

Recovery can establish a successor coalition through a new coalition formation proposal. That proposal serves as the successor instance's genesis and references blocks in the preceding instance's recovery DAG as parents. The new construction context therefore retains the causal history of the recovery evidence.

## 🤖 Causal order and block properties {#causal-order-and-block-properties}

Write $a\preceq b$ when $a=b$ or $a$ is reachable from $b$ through parent-set or self-parent references. Define

$$
D(b)=\{a:a\preceq b\},\qquad
C(b)=\bigcup_{a\in D(b)}M_a.
$$

$D(b)$ is the block's inclusive causal history. For independent validation, a block is causally delivered only after its required contents and ancestors have been obtained and validated. Receiving a root or block hash is not causal delivery. The [optional attested-validation profile](#optional-attested-validation-and-acknowledgement-relay) permits peers to accept certified validation of that history without independently retrieving and checking all of it; this does not assert that they locally possess the history. The following properties are derived from authenticated block data and its causal history:

| Property | Definition |
| --- | --- |
| Author $\operatorname{author}(b)$ | Validator authenticating the block. |
| Instance-local height $h(b)$ | Zero for this instance's genesis; otherwise one plus the maximum height of its parent-set and self-parent references within the instance. Cross-instance recovery ancestry remains part of causal history. |
| Context | Construction instance, block type $\kappa_b$ and phase $\phi_b$, whether explicit or inferred. |
| Observed messages $C(b)$ | Union of included messages throughout $D(b)$. |
| Phase state $V_\phi(b)$ | Application interpretation of the messages for phase $\phi$ and the construction instance in $D(b)$. Ancestors from predecessor instances provide recovery evidence, not new contributions to this instance. |
| Support | Distinct validators whose qualifying acknowledgements occur in $D(b)$, for a specified state and predicate. |

Height measures causal depth; it is not elapsed time or by itself a threshold logical clock. Support counts validators, not blocks. Producing additional blocks cannot multiply a validator's weight.

The analogue of Cordial Miners' $\tau$ is a deterministic interpretation function

$$
\mathcal I(b)=\mathcal I(D(b)),
$$

which derives the phase state, supporting evidence and permitted transitions. Cordial Miners uses $\tau$ to extract a total order while excluding equivocations.[^cordial] Here the interpretation is set-valued: compatible admitted contributions are joined without assigning them a total order. The phase rules determine how invalid or conflicting evidence affects admission. Observation of a message and acceptance into application state remain distinct.

For the compatible admitted contributions of a phase, extending causal history preserves inclusion. Block authentication identifies the validator, not the authors of anonymous payloads. Incompatible self-parent histories by the same validator within the same branch provide equivocation evidence. Explicitly separate recovery branches are different contexts, not automatically equivocations. Evidence is retained rather than resolved by choosing whichever block arrived first.

## 🤖 Frontiers {#frontiers}

A finite causally closed block set $D$ has frontier

$$
F(D)=\max_{\preceq}D.
$$

The frontier is the antichain of its maximal blocks. It represents the entire causal cut because

$$
D=\bigcup_{b\in F(D)}D(b).
$$

For a frontier $F$, write $D(F)=\bigcup_{b\in F}D(b)$ and $C(F)=\bigcup_{b\in F}C(b)$. Frontier extension is ordered by $F\sqsubseteq G$ iff $D(F)\subseteq D(G)$. The join of two compatible causal views is represented by $F(D(F)\cup D(G))$.

A frontier is not a selection of one block per validator. It can omit a validator whose blocks are ancestors of another frontier block, or contain several incomparable blocks by an equivocating validator. A local current frontier represents all causally delivered blocks in its scope. A historical frontier represents a specific earlier cut and must be identified as such.

Different frontiers may contain exactly the same phase contributions. Phase agreement therefore compares interpreted phase states, not equality of block hashes or frontier sets. Acknowledgement-only blocks can advance the frontier without changing the transaction state.

## References

[^schnorr]: Pieter Wuille, Jonas Nick and Tim Ruffing. [BIP 340: Schnorr Signatures for secp256k1](https://bips.dev/340/). Reference for the Schnorr verification equation and key-prefixed challenges; the predecessor nonce commitments and equivocation-evidence policy are part of this protocol.

[^cordial]: Idit Keidar, Oded Naor, Ouri Poupko and Ehud Shapiro. [Cordial Miners: Fast and Efficient Consensus for Every Eventuality](https://arxiv.org/abs/2205.09174).

[^bec]: M. Kleppmann and H. Howard, [*Byzantine Eventual Consistency and the Fundamental Limits of Peer-to-Peer Databases*](https://arxiv.org/abs/2012.00472) (2020). Byzantine causal broadcast and invariant-preserving replication; see §2.2–3 for the requirement that independently valid updates remain valid when merged.

[^dag-rider]: I. Keidar, E. Kokoris-Kogias, O. Naor and A. Spiegelman, [*All You Need is DAG*](https://arxiv.org/abs/2102.08325) (2021). DAG-Rider separates construction of a communication DAG from local ordering of its proposals.

[^trusted-coordinators]: Y. Kogman, [*Reiterating centralized coinjoin (Wasabi & Samourai) deanonymization attacks*](https://groups.google.com/g/bitcoindev/c/CbfbEGozG7c/m/w2B-RRdUCQAJ)

[^asymmetric-trust]: O. Alpos, C. Cachin, B. Tackmann and L. Zanolini, [*Asymmetric Distributed Trust*](https://arxiv.org/abs/1906.09314) (2024). Subjective fault assumptions and asymmetric Byzantine quorum systems.

[^flexible-bft]: D. Malkhi, K. Nayak and L. Ren, [*Flexible Byzantine Fault Tolerance*](https://arxiv.org/abs/1904.10067) (2019). Different clients interpret one protocol transcript using different fault and timing assumptions.


