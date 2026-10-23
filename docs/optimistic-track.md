---
type: Specification
title: "Optimistic track: blocks and phase states"
description: Unanimity and phase closure on the optimistic track, phase by phase.
status: draft
stale_after: 2027-04-15T00:00:00Z
---

<!-- cspell:words antichain APSA APSA's Chondros Christos counterpropose CRBB Croman DAPS Diamantopoulos Dolev Duan Ehud Garay Guerraoui Haibin Haifeng Idit Ittai Keidar Kichidis Kleppmann Maneas mathcal mathit mathrm Mema Minghang Naor Nikos Oded operatorname Ouri Patsonakis Pieter Poupko Rachid Reiter Roussopoulos Ruomu semilattice Sisi Skoumios Stathis Tasos texttt Tonkikh Vassilis vout Wonseok Wuille Yuval Zhuolun Zikas -->

# 🤖 Optimistic track: blocks and phase states

## Scope and status

This specification describes how Fungi transaction construction obtains consistency on the optimistic track, with threshold $t=n$. The [recovery track](recovery-track.md), with $t<n$, is described separately. It uses the [block DAG](block-dag.md). Transmitting that history between peers is described in the [peer set reconciliation](set-reconciliation.md) chapter.

This is a draft technical specification. The data model and reconciliation rules below describe the intended construction. Exact encodings, cryptographic parameters, quiescence scheduling and phase-specific agreement predicates remain to be specified.

The construction retains the causal delivery and validation semantics of Byzantine Eventual Consistency (BEC).[^bec] Discovering missing data only needs BEC's [naive reconciliation](set-reconciliation.md#naive-reconciliation); more efficient algorithms are future optimizations. It does not introduce a total order on transaction fragments. Compatible fragments combine by set union; arbitrary PSBT updates are not assumed to form a join semilattice. The transaction protocol determines admission, compatibility and the interpretation of its state.

### Settings {#settings}

The optimistic track applies in the honest, semi-honest and Byzantine settings, with minor variations:

- **Byzantine.** The genesis is the accepted [coalition formation](coalition_formation.md) proposal. It lists the initial inputs, and their owners are the validators. If the outputs overflow the balance, the proven phases follow.
- **Honest and semi-honest.** In the closed variant described under [contacts](contacts.md), the session initiator sets the validator keys and sends everyone the list. The initial input set is empty, every input is auxiliary, and the proven phases don't run.

Rules below that name initial inputs, validity proofs or the proven phases apply only in the Byzantine setting.

## Design objectives

Progress is measured in completed transaction-construction phases. Unlike a blockchain processing a continuing transaction stream, this protocol coordinates a finite set of contributions toward a stable phase boundary. Its principal performance objectives are end-to-end phase latency, lightweight validation and low communication cost. Faster block production has no independent value.

For a given phase latency and agreement guarantee, fewer blocks are preferable. They reduce authentication, validation, storage and dissemination overhead, and expose fewer intermediate causal views from which an observer could infer propagation order or network topology. Block count is therefore both a resource metric and a privacy consideration, although it is not itself a measure of privacy leakage. Batching must be evaluated against the delay it adds to completing the phase.

The relevant latency measurements are time to reconciliation quiescence, time to a stable common phase state, and time until the evidence permits the next phase. The optimistic target is to reach stability in approximately two communication round trips once the phase's contributions and local prerequisites are available. This is a design target, not an established bound: the precise exchanges, starting condition and completion predicate remain to be derived from the phase rules. DAG depth alone does not count round trips, and communication rounds have no fixed wall-clock duration under asynchrony.

Evaluation therefore measures blocks and bytes per completed phase, per-peer validation work, and the communication needed to establish and disseminate closing evidence.

<a id="phase-agreement"></a>

## Phase closure

The optimistic track is defined for the asynchronous communication model. Every phase closes by two rounds of unanimous acknowledgement of the same contribution set. Cooperative participants advance as soon as they hold the evidence; a silent participant can stall progress. The [recovery track](recovery-track.md) handles missing per-input messages and stalled validator participation.

Finalizing each phase's contribution set keeps it stable for the next. This matters most for the input set, which must be stable before outputs:

- **Validity proofs and their privacy.** Proving an output before a late input arrives would need a more complicated proof statement and would harm privacy, so it is not supported.
- **The balance condition.** With only some of the inputs and some of the outputs, the two could sum to the same amount, and the balance would reach zero too early.
- **Choosing output values.** Most importantly, output values are chosen on the basis of the input set, including the auxiliary inputs. This is a privacy requirement.

### State acknowledgement and unanimity

Set finalization uses two rounds of acknowledgements carried implicitly by ordinary DAG blocks at two consecutive heights. In the first round, each validator acknowledges its phase state with nothing further to add. In the second, each validator acknowledges that all validators' first-round acknowledgements refer to the same set. These are roles of blocks in the construction phase, not separate block types or payload messages.

Let $N$ be the fixed validator set and $\phi$ the index of a construction phase. Write $b_{i,h}$ for the block of validator $i\in N$ at [height](block-dag.md) $h$, and $V_\phi(b)$ for the set of phase $\phi$ contributions that block $b$ represents. Phase $\phi$ closes on a set $S$ when, at two successive heights $h$ and $h+1$, every validator's block represents $S$:

$$
\forall i\in N:\quad V_\phi(b_{i,h})=S \quad\text{and}\quad V_\phi(b_{i,h+1})=S.
$$

The blocks at height $h$ are the first-round acknowledgements. With $t=n$, every block at height $h+1$ refers to the blocks of all validators at height $h$, so a second-round acknowledgement has causal evidence of the first round, and still represents $S$ itself. A participant finalizes $S$ once it has the blocks of every validator at height $h+1$.

Receiving one block from every validator is therefore insufficient if those blocks represent different sets. Taking their union does not establish that the first-round acknowledgements were synchronized. Reconciliation must continue until the common-set condition is met. When a validator may give its first-round acknowledgement depends on whether the phase's [keys](#keyed-and-anonymous-phases) are known when it opens.

### Phase transitions

A validator enters phase $\phi$ once it has the second-round acknowledgements from all of $N$ finalizing the same set for $\phi-1$. Kickoff is entered on holding the genesis.

A participant advances when the relevant evidence becomes available; others catch up through causal delivery. Local phase changes need not be simultaneous.

The exact successor phase is a deterministic function of the completed state and the transaction protocol's rules. A message added to an already closed phase is necessarily an equivocation, so it is a Byzantine fault and is detected.

No phase transition can infer readiness solely from local quiescence. The finite agreement is on $S$ and its readiness conditions. Reconciliation completion, quiescence and phase completion are distinct events.

### Keyed messages {#keyed-and-anonymous-phases}

Every transaction-level message is linked to one input, one output or one fee contribution. When an input or output is first added, its message carries a public key: for an input, the online key enrolled by its ownership proof; for an output, a fresh ephemeral key. Later messages for that input or output are authenticated by this key, so only its owner can post them. Outputs need this because in the Byzantine setting there are several proving phases, and with silent payments the owner would also have to post the unblinded final script. In the optimistic phases, fee contributions are explicit and keyed for idempotence. In the proven phases, explicit fee contributions are no longer required, because nobody can claim more than they can prove. Whatever no output claims is fee. A key has more than one message when proofs are required in the Byzantine setting. Two valid input proofs from one input with different allocation commitments are evidence against that input, as described under [per-input messages](#per-input-messages).

Ideally every kind of equivocation would expose the online key, as conflicting validator blocks expose the validator key through [nonce commitments](block-dag.md#nonce-commitments-and-compact-equivocation-evidence). For anonymously published messages, this could use double-authentication-preventing (DAPS) ring signatures, which could also rate-limit messages per key. This remains to be specified.

An initial input publishes its messages through its validator. The messages of each auxiliary input or output are broadcast anonymously, separately from those of every other input and output. Messages of the same input or output are linked by its key anyway; for example, an output proof is linked to its output. What matters is that the input or output stays anonymous with respect to the others. With a connection-based transport, the messages of one input or output can reuse a connection, but no connection carries those of two.

Once submitted, anonymous messages are relayed by other peers. A peer doesn't change its behavior when it receives its own messages back; in particular, it doesn't stop its anonymous broadcasts. In general a message keeps being broadcast until the phase ends, with these relaxations:

- **Honest.** The requirement doesn't apply.
- **Semi-honest.** Only passive attacks are assumed, so broadcast can stop once enough neighbors are believed to have seen the message.
- **Byzantine.** Broadcast can stop once enough optimistic-track or recovery-track blocks include the message.

Blocks are the only messages not associated with a specific input or output. In the Byzantine setting, a block is associated with the initial input of its validator. In the semi-honest setting, it is associated only with a validator key, which is not linked to any input or output.

Phases differ only in when a validator gives its first-round acknowledgement:

- **Keys known when the phase opens**: kickoff, initial-input proofs and signatures. A validator acknowledges once its view holds a valid message for every key.
- **Keys known only from their messages**: auxiliary inputs, outputs and fee contributions, proven auxiliary inputs, allocation registrations and proven outputs. These messages arrive by anonymous broadcast. A validator acknowledges under the [anonymous-phase publication rule](#anonymous-phase-publication).

### Hashes and identifiers

- $H(\mathit{tag}, m) = \mathrm{SHA256}(\mathrm{SHA256}(\mathit{tag}) \Vert \mathrm{SHA256}(\mathit{tag}) \Vert m)$, the tagged hash of BIP 340.[^schnorr] Tags begin with `fungi/`.
- Instance id: $\mathit{sid} = H(\texttt{fungi/session}, \mathit{genesis})$.
- Outpoint: $\mathit{op}$ = txid (32 bytes, internal byte order) followed by vout (u32, little-endian).
- Validator: its index in $N$, in genesis order.

### Input lists

In the Byzantine setting, the initial inputs $I$ are listed in the genesis. Every initial-input owner participates as a validator, validating and acknowledging the construction state. The aggregator owns an initial input and is therefore a validator too. Each input acts through the online key enrolled by its ownership proof. Its spending keys are used only for the ownership proof and the final signature. Auxiliary inputs are submitted anonymously, first without proofs and, only after overflow, with the required proofs.

Optimistic auxiliary inputs, optimistic outputs and fee contributions, auxiliary-input proofs, allocation registrations and output proofs are submitted anonymously. Input proofs and final signatures identify the input by outpoint. The [optimistic phases](transaction-construction.md#phases), which add content without validity proofs, concern transaction data; they are distinct from the optimistic track this chapter describes, which concerns agreement.

### Per-input messages

A per-input message is signed by, or bound to, one input. These are the only messages that can blame an input. The initial inputs $I$ and the auxiliary inputs $A$ are each sorted by outpoint bytes, ascending. On the optimistic track no input is removed, so the inputs of the final unsigned transaction are $I \cup A$.

| Phase | Keys | Message | Valid if |
| --- | --- | --- | --- |
| kickoff | $I$ | $\mathrm{ACCEPT}(i)$ | signature by the online key of $i$ over $H(\texttt{fungi/accept}, \mathit{sid})$ |
| initial-input proofs, only after overflow | $I$ | input proof of $i$ | verifies under the validity proofs and is authenticated by the online key of $i$, bound to $\mathit{sid}$ and $\mathit{op}_i$ |
| signatures | $I \cup A$ | signature of $i$ | a valid witness for $i$ over the final unsigned transaction |

An invalid message counts as absent.

Validators take the union of the per-input messages they receive, each identified by its input's outpoint. An input commits to one input proof. If it posts two valid input proofs for the same $\mathit{sid}$ with different allocation commitments, the DAG reveals both. Their online-key authentication binds them to that input, so, as in Cordial Miners,[^cordial] the pair is evidence of malfeasance by that specific input. As the [block DAG](block-dag.md#nonce-commitments-and-compact-equivocation-evidence) requires, both are removed from the phase state. [Recovery](recovery-track.md#evidence-that-excludes-at-once) additionally excludes the input. Two different valid signatures over the same transaction, or two valid ACCEPT messages, are not equivocation; either one serves.

### Blocks and acknowledgements

Validators publish blocks in the shared block-DAG format. A block's payload holds received messages not yet in its causal history. Anonymous submissions become eligible for inclusion once received through synchronization, without distinguishing the validator's own submissions from those of other participants. A block with no new messages can acknowledge the state established by its causal history.

The acknowledgement rounds use optimistic-track blocks. Recovery-track blocks use the separate recovery nonce commitment, as described in the [block format](block-dag.md#nonce-commitments-and-compact-equivocation-evidence). The permitted branching between tracks is not equivocation. Equivocation evidence follows the predecessor and nonce-commitment rules of the block DAG.

<a id="optional-attested-validation-and-acknowledgement-relay"></a>

A validator can leave message collection to other validators, or follow a trusted or TEE-attested validator, while still producing its own acknowledgement blocks. The block DAG describes this under [optional attested validation and acknowledgement relay](block-dag.md#optional-attested-validation-and-acknowledgement-relay).

## Phases

Each phase below admits its content, then closes by the rules above. The phases run in the order given in [transaction construction](transaction-construction.md#phases).

### Kickoff

Kickoff is the validators' acknowledgement of the genesis. In the Byzantine setting, the genesis is the coalition formation proposal, and kickoff is keyed by its initial inputs, each acknowledging with an $\mathrm{ACCEPT}$ message. In the semi-honest setting, the genesis comes from the session initiator, and its contents are not yet specified. Its two acknowledgement rounds are the first two layers of the [block DAG](block-dag.md#optimistic-and-recovery-tracks). Once a peer holds second-round acknowledgements from all $n$ validators, kickoff is complete for it, and it can begin anonymously disseminating auxiliary inputs.

A missing acknowledgement can stall kickoff. The [recovery overlay](recovery-track.md#recovery-overlay) begins after the genesis acknowledgement layers; this rule does not itself provide a recovery mechanism for incomplete kickoff.

### Anonymous-phase publication

In each anonymous phase, a validator waits for reconciliation quiescence and at least the phase's minimum waiting period before its first-round acknowledgement. Inclusion of its own anonymous contributions is not a condition for either acknowledgement round. The same rule applies to auxiliary inputs, outputs and fee contributions, allocation registrations, and proven outputs. The waiting periods and reconciliation scope remain to be specified. Quiescence permits publication under this rule; phase closure still requires both rounds of unanimous acknowledgements described above.

Conditioning an identified validator's block on receipt or inclusion of its own anonymous registration or output would let adversarial peers test the association by selectively withholding that contribution. A participant therefore continues validating and acknowledging the construction even if every other validator omits its contributions. If the resulting transaction does not satisfy its output or payment requirements, it refuses transaction signing instead. A missing signature identifies an input, but does not by itself identify the omitted anonymous contribution or establish why the participant refused to sign.

### Auxiliary inputs

Auxiliary inputs are admitted anonymously. Omitted auxiliary inputs are not part of this transaction.

### Outputs

Outputs and fee contributions are admitted anonymously without validity proofs. This phase is the same in every setting. The initial inputs are already known, and the optimistic auxiliary-input set has been agreed. No mandatory destination-commitment phase precedes these contributions.

Every optimistic output or fee contribution accounts for at least 1 sat. The balance in a validator's view is the total of $I \cup A$ minus the outputs and fee contributions in that view. A participant may post the overflow signal, equivalent to a fee contribution of `MAX_MONEY`, to make that balance negative. This starts the need for proving; it does not bypass the anonymous-phase waiting rule or the phase-closing acknowledgements.

The balance of the finalized set determines the next phase:

- **Balanced.** At a balance of zero, the phase continues to signatures. This is the only outcome that terminates on the optimistic track. Agreement on this balance does not establish that every participant's outputs are present or that its payment requirements are satisfied; participants check those conditions before signing.
- **Overspent.** If the balance is negative, at least one output or fee contribution is not covered. In the Byzantine setting, the phase continues with the proven phases, as the [validity proofs](validity-proofs.md) require, and anyone can force this. For example, a faulty party posts an output for exactly the remaining amount before an honest output arrives; the honest output then makes the balance negative.
- **Underspent.** A positive balance does not terminate the optimistic track. Unclaimed balances are possible only on the [recovery track](recovery-track.md), which is a different termination path.

<a id="destination-commitments"></a>
<a id="proven-auxiliary-inputs-and-proven-outputs"></a>

### Initial-input proofs

The proven phases run only in the Byzantine setting, after overflow in the optimistic outputs phase. Optimistic outputs are discarded. Participants choose fresh, unguessable output ids for the proven phases. This phase is keyed by the initial inputs: each posts its proof, identified by outpoint and authenticated by its online key. The proof commits to its allocations of funds and vbytes. The finalized initial-input-proof set supplies the allocations used for auxiliary admission.

### Proven auxiliary inputs

Auxiliary inputs are submitted anonymously with their proofs. Each proof message is authenticated by that input's own online key, enrolled by its BIP-322 ownership proof, and bound to the session. Each admission consumes a vbyte allocation committed by an initial input. Only once the proven auxiliary-input set is finalized is the session root derived from the accepted initial and auxiliary input allocations. The [validity proofs](validity-proofs.md#phases-and-data-dependencies) describe the dependency; the current PoC does not implement the vbyte-allocation admission relation.

### Allocation registration and proven outputs

Output proving has two anonymous phases. First, allocation registrations are submitted against the final session root. Their finalized set determines the registered-leaf root. Then outputs are submitted with proofs against that root. The proofs enforce coverage. As in the outputs phase, only a balance of zero terminates the optimistic track. Script authorization follows the validity proofs.

### Signatures

Signatures are keyed by the inputs, $I \cup A$. Once every validator holds every signature, the transaction is complete.

## Payment confirmation commitments

A payment confirmation states that a particular construction state satisfies the payment agreement: the payee confirms delivery of the funds to their ultimate destination, including any onward payments. Counterparties exchange confirmations after output finalization and before input signing. The payer checks that the output set committed to by its input signature is consistent with that confirmation. This check does not require the payer to learn which output belongs to the payee. The [concurrent PSBT specification](psbt-concurrent.md#confirmation-of-successful-payment-prior-to-signing) defines the dependencies between counterparties' confirmations.

The confirmed construction state is bound by the protocol transcript's Merkle-set commitment. That transcript includes the transaction contributions and required proofs, and its commitment is used as the deterministic sort seed for constructing the unsigned transaction. The payer checks that the payee's confirmation names the same transcript commitment that it uses to construct the output set it signs. Acknowledgement-only blocks can change a DAG frontier without changing this construction state.

In the Byzantine setting, the wire objects are specified protocol messages. Their accepted state projects into the PSBT data used to construct and sign the transaction. Honest and semi-honest construction can use PSBT extensions; the Byzantine construction requires specified protocol extensions rather than accepting arbitrary PSBT extensions as protocol messages.

## Block publication and quiescence

Quiescence minimizes the number of block DAG waves per phase. Convergence on a phase's contributions happens by gossip; the block DAG exists to verify that convergence did occur. Waiting for convergence among its neighbors before authoring a block therefore avoids needless waves. This applies even when the cordial parent threshold is already met, as with $t=n$. Fewer blocks are also more compressible on the wire. [Peer set reconciliation](set-reconciliation.md) is an input to this rule, whichever reconciliation algorithm is used.

Reconciliation between neighbors precedes the release of a new cordial block. The objective is to publish a consolidated view rather than a sequence of intermediate views that exposes the order in which contributions reached the validator. This reduces observable correlations between the block contents and the network's propagation topology.

For a fixed reconciliation scope, local quiescence means that its advertised sets have been reconciled and there is no outstanding reconciliation work for that scope. It is a local condition: it neither proves that no further message exists nor closes admission to a phase. A newly advertised root can create more work.

A publication rule must specify which neighbors and advertised roots belong to the scope, how concurrent advertisements affect it, and how stalled neighbors are handled. Those choices are not yet fixed. Waiting for all future advertisements is not a finite condition; waiting for every neighbor can indefinitely delay publication. Any cutoff or recovery policy must be evaluated together with the intended privacy and liveness properties.

Cordial parent-inclusion rules additionally limit block production according to progress by other validators.[^cordial] Quiescence batches the available contributions before a permitted block is released; it does not replace the parent threshold. On a hub-and-spoke topology, a well-connected validator can assemble most payloads while others acknowledge them. This is workload concentration, without requiring a privileged leader.

The privacy objective is to avoid additional attribution beyond the transaction, authorized counterparty knowledge and the transport's guarantees. Channel-randomized transfer schedules reduce redundant traffic; quiescent publication reduces intermediate public views. Neither alone establishes a topology-hiding theorem. The remaining leakage includes publication timing, neighbor failures and the selected quiescence policy.

## Dissemination interface

Blocks and their messages are disseminated by [peer set reconciliation](set-reconciliation.md). Its [naive reconciliation](set-reconciliation.md#naive-reconciliation), which requests the preimages of unknown hashes until it reaches known blocks, is sufficient for causal delivery; the other algorithms there are optimizations. Reconciliation supplies contents and completion status. It does not decide block validity, unanimity or phase transitions. Beluga's block synchronizer is a reference for this boundary and for evaluating recovery traffic.[^beluga]

## Resource bounds and validation

Bounds on neighbor exchanges, speculative decoder work and unresolved roots are given in [peer set reconciliation](set-reconciliation.md#resource-bounds-and-validation). The transaction protocol bounds admitted contributions; the DAG rules must additionally bound block production and recovery proposals. Invalid contributions do not enter validated application state, and reconciliation cannot force a withholding participant to sign.

## Open specification choices

The remaining choices are:

* Canonical block encodings and the interface to peer-layer committed sets.
* Quiescence scope and publication scheduling, including handling of continuing traffic and stalled neighbors.
* Exact interpretation of the two acknowledgement rounds in the block DAG, admission boundaries, and their interaction with late contributions and recovery.
* Bounds on block production and branch proliferation.
* Equivocation evidence that exposes the online key for every kind of keyed message, for example using DAPS ring signatures, and its use for rate limiting.

The DAG interpretation and phase rules are independent of the peer layer's choice of reconciliation algorithm.

## References

[^bec]: Martin Kleppmann and Heidi Howard. [Byzantine Eventual Consistency and the Fundamental Limits of Peer-to-Peer Databases](https://arxiv.org/abs/2012.00472).

[^schnorr]: Pieter Wuille, Jonas Nick and Tim Ruffing. [BIP 340: Schnorr Signatures for secp256k1](https://bips.dev/340/). Reference for the Schnorr verification equation and key-prefixed challenges; the predecessor nonce commitments and equivocation-evidence policy are part of this protocol.

[^cordial]: Idit Keidar, Oded Naor, Ouri Poupko and Ehud Shapiro. [Cordial Miners: Fast and Efficient Consensus for Every Eventuality](https://arxiv.org/abs/2205.09174).

[^beluga]: Tasos Kichidis et al. [Beluga: Block Synchronization for BFT Consensus Protocols](https://arxiv.org/abs/2511.15517).
