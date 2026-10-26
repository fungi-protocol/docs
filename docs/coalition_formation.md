---
type: concept
title: Market-based coalition formation
status: draft
stale_after: 2027-01-23T00:00:00Z
---

# Market-based coalition formation

## Problem definition

In several existing market-based decentralized protocols involving collaborative transactions, a single party initiates and typically bears the costs — for example, JoinMarket or liquidity ads.

Transactions meeting the demand of more than one "taker" can be more efficient, depending on their desired outcomes. CoinJoin privacy in particular is a non-rivalrous positive externality obtained by each participant from the other participants, and as such, it's an inherently positive sum.

The following protocol aims to generalize the type of order matching JoinMarket supports, allowing multiple users' intents to be aggregated together.

## Overview of proposed solution

This document describes a permissionless, peer-to-peer protocol for negotiating the initiation of a collaborative transaction construction. This takes place over two primary phases: bilateral negotiation, followed by aggregation. Successful execution of the protocol results in a coalition of UTXO owners unanimously agreeing to build a transaction together.

This isn't a transaction construction protocol, but a precursor to such a protocol. This protocol bootstraps a compatible transaction construction protocol by finding consensus on an initial set of UTXOs whose (honest) owners intend to spend them in a collaborative transaction. Refer to the last section for a brief discussion of such a protocol and how it composes with this one.

### Bilateral negotiation

A proposer, the owner of one or more UTXOs, selects UTXOs belonging to others from an "order book". The proposer initiates peer-to-peer bilateral negotiations with the owners of these coins by sending them a message that includes a *co-spend proposal*. This expresses an intent to cooperate to spend this set of coins together in a single Bitcoin transaction.

Co-spend proposals are publicly verifiable, confidential adjustments to the effective values of the specified coins. These adjustments can represent arbitrary payoff structures. Whether a proposal takes effect (i.e. the adjustment is applied) is contingent on the constraints specified in the proposal being satisfied in a transaction construction session intended on spending the specified UTXOs. For example, a proposal may require that non-SegWit inputs be excluded for TxID stability, or that the feerate be within an acceptable range, among other constraints.

Co-spend proposals rely on cryptography to keep each coin's adjustment hidden, except for that coin's owner and the proposer. The proposer's UTXO is indistinguishable from the other UTXOs. Before a proposal is unanimously accepted, it isn't known which UTXO owners have accepted the proposal.

### Aggregation

Co-spend proposals aren't exclusive. Many proposals can be aggregated together before collaboratively constructing a transaction in which the combination of all the aggregated proposals is in effect. The UTXOs specified in proposals that are aggregated together may overlap but don't need to; the main requirement is for the constraints to be compatible.

Fully accepted proposals can be broadcast and then aggregated with other compatible proposals. Aggregation makes it possible for multiple participants to simultaneously optimize for their desired outcome according to their individual preferences. When they value privacy, or any other kind of positive sum interaction, aggregation generates surplus from which all participants may benefit.

To aggregate, several proposals are bundled together with a *coalition formation proposal* that all parties must agree to. Unanimous acceptance of such a coalition formation proposal signals that everyone is ready to construct a transaction.

Because transactions are only valid if all inputs are signed, multiparty transactions require unanimous agreement. A precondition for denial of service protection in privacy preserving multiparty transaction construction protocols is incentive compatibility for the honest participants. No honest participant should have a reason to withhold their signature.

The primary purpose of this protocol is to construct an [imputation](https://en.wikipedia.org/wiki/Imputation_%28game_theory%29), which is a payoff distribution over the inputs. This aligns incentives for successful transaction construction while maintaining confidentiality of the individual payoffs.

## Background

### Hedonic games and games with transferable utility

Coalition formation games, in game theory, typically refer to the cooperative game theory setting, where agreements are binding and can be enforced by some kind of mechanism. While Bitcoin can provide such a construct, analogously to the function of the court system, the current consensus rules require some kind of contract to be anchored in a confirmed transaction, i.e. binding agreements require creating new transactions and waiting for them to confirm.[^coinswap] In order to build transactions without having already built transactions, we must therefore assume the non-cooperative setting. Coalition formation in the non-cooperative setting can only rely on incentives.

When preferences over the coalition structure are in play (the cost function), in so-called hedonic games, it is often very hard (also in an algorithmic sense) to find stable coalition structures, as the preferences of the participants may conflict. In their most general form, such game descriptions are enormous as the preferences are defined over a large combinatorial object. Even when many assumptions are made, like constraining the kinds of preferences the participants may have, it is still generally hard to find stable equilibria.[^hedonic] Complicating matters further, sharing the preferences would itself be a privacy leak, so we would prefer to limit that as much as possible, and certainly we cannot assume a mechanism that optimizes outcomes by just being able to read these preferences.

Fortunately, some of these difficulties of hedonic games can be bypassed with the introduction of a transferable utility, and assigning the coalition itself a payoff, which can be redistributed. In our use case this payoff originates from any blockspace savings from net settlement, and the privacy benefits from collaboration. This surplus is not observable, it is the sum of subjective payoffs depending on individual participants' preferences (which in turn depend on their circumstances, privacy threat model, etc). While this does not guarantee stability, if a stable coalition structure exists, a transferable utility can make the process of finding one much easier by iterated bilateral negotiation. However much these benefits are worth to participants, if this surplus exists, then it can be voluntarily redistributed as sats among the participants (i.e. via a fee mechanism) aligning incentives for collaborative transaction construction, so that all coalition members stand to gain from participating.

Coalition formation games output a partition over $N$ peers. Finding stable equilibria in such games is generally difficult. Depending on the structures in the preferences of the peers, many special cases described in the hedonic games literature are still hard. In the byzantine setting appropriate for Bitcoin protocols, no such structure can be assumed, which makes finding stable partitions intractable.

Since the participants in the protocol unilaterally control independent UTXOs during the execution of this protocol, we're constrained to the non-cooperative setting, where agreements are non-binding and can't be enforced. Additionally, for privacy, the cost functions should remain hidden so that no mechanism can access the peers' preferences and globally optimize. Note that due to the nature of revealed preferences, the cost function can't be fully hidden.

Fortunately, the introduction of a transferable utility greatly simplifies finding stable coalition structures, even under these assumptions. Bitcoin can approximate such a transferable utility. This makes it possible to simply assign payoffs to the coalitions and allow them to be distributed among the peers through bilateral negotiation. If Alice prefers not to co-spend with Bob, but Carol strongly favors both Alice's and Bob's participation, Carol is able to compensate Alice, so that as long as the coalition generates some surplus, all parties will be able to obtain a positive payoff.

### Transaction construction liveness assumptions

For a coalition of $n \leq N$ peers, $f$ of which are adversarial, liveness for transaction construction can be achieved (with privacy) by the honest subset of peers in $O(f)$ time. Any defection requires transaction construction to start over. Due to random network disruptions, necessarily some rate of (apparent) defection must be tolerated.

Because exclusivity of spending attempts by inputs can't be enforced without global consensus, and because transaction replacement is desirable for fee market efficiency, we assume inputs are allowed to participate in concurrent sessions, which will result in conflicting transactions. Opt-in signalling can be used and obeyed as a courtesy, but this ultimately reduces to the same liveness model as transaction construction, potentially requiring additional attempts to recreate the transaction.

### Cost functions

This protocol is mostly agnostic to the cost function that describes the peers' preferences.

Much like in the problem of coin selection (which this work aims to generalize), the cost function is denominated in sats, and it's the combination of objective terms (i.e. the fee cost) and subjective ones (any positive utility obtained from transacting, which by definition must dominate over the objective costs for a self-interested, not necessarily honest peer to agree to sign the transaction).

Although out of scope for this specific document, privacy-related terms are assumed to quantify things like how much cover other peers' coins provide in Maurer et al's sub-transaction model, or an estimate of the cost to an adversary of an $n-1$ deanonymization attack (for instance, an adversary using older coins incurs a higher cost to do such an attack, as that liquidity must effectively be locked up to become old).

A precondition for liveness is that any such cost function is monotonically decreasing in new information revealed during transaction construction.

Concretely, this means that whenever the action of some peer is revealed (i.e. when an input or output is added), at worst, other peers should be indifferent to this, but they may also obtain positive utility. If this isn't the case, parties may rationally choose to defect. The purpose of the constraints in proposals is to allow the honest subset peers to avoid such non-malicious conflicts a priori. Since monotonicity is required for liveness, a peer that engages in the protocol without adhering to this restriction and refuses to sign is deviating from the protocol, and therefore by definition not a member of the honest subset.

## Simplified example

Note that this example omits many details discussed below.

Alice, Bob, Carol, and Dave are owners of UTXOs $A$, $B$, $C$, and $D$, respectively. Alice wants to CoinJoin with Bob and Carol. She creates a co-spend proposal with UTXOs $\{ A, B, C \}$. In this proposal, she adjusts her UTXO $A$ down by 100 sats, and adjusts $B$ and $C$, perhaps up by 50 sats each, providing an incentive for Bob and Carol to accept. She sends this to Bob and Carol, who accept, after which the proposal is fully accepted and broadcast.

For all Bob knows, either Carol or Alice made the proposal, and the same goes for Carol, not knowing if it was Alice or Bob. Bob only learns that he was offered 50 sats; he doesn't learn how much Carol (or whomever) was offered. All Bob knows is that the 50 sats, which he would receive if a transaction was constructed with this proposal in effect, would be paid for by one of the UTXOs $\{A, C\}$.

Carol also wishes to CoinJoin with Alice and Dave. She creates a co-spend proposal with UTXOs $\{ A, C, D \}$, and adjusts $C$ down by 50 sats, $A$ up by 20, and $D$ up by 30. This too is unanimously accepted and broadcast.

Dave then notices both proposals are compatible, and chooses to aggregate them together. He produces a coalition formation proposal, which depends on these two proposals. The coalition formation proposal chooses a specific feerate, among other things, combining the constraints of both previous proposals. It names $\{ A, B, C, D \}$ as the UTXOs.

Once all parties accept Dave's proposal, consensus has been bootstrapped. Everyone can derive the same total adjustments: $A - 80$, $B + 50$, $C + 0$, $D + 30$. In general, only the owner of each coin knows their final adjustment, but in this example, Carol knows that Dave obtained $+30$ because her proposal is the only one that applies to his coin, and likewise Alice knows Bob obtained $+50$.

All peers can then proceed to transaction construction, where each party is entitled to add up to their adjusted value's worth in outputs. They may add additional inputs and arbitrary outputs, so long as for each peer, the sum of the outputs' effective cost doesn't exceed the sum of the adjusted effective values of that peer's inputs.

## Technical details

### Setup: BIP 322 gossip, online key enrollment

🤖 Ownership proofs and online keys are specified under [peer to world broadcast](channels.md), together with the gossip, flood protection and precedence ordering rules for them and for listen advertisements.

### Negotiation: Listen advertisements and/or gossip of partially accepted proposals

Short-lived listen advertisements may be signed by "makers" using their online keys to indicate that the owner of a UTXO is soliciting proposals pertaining to its spending over the named communication channel.

"Takers" evaluate listening coins and can construct proposals (defined in the next section) over the specified communication channels.

Alternatively, negotiation with listening but unaddressable UTXO owners can be made possible using an opt-in gossip layer. On this layer, it's permitted to broadcast partially accepted proposals. See below for a discussion of flood protection considerations in this setting.

Listen advertisements can specify constraints for proposals being entertained, indicating that proposals outside of the constrained subspace (see coalition formation proposal details below for specifics) are unacceptable at any price.

Finally, listen advertisements also indicate the owner's willingness to serve as a validator node in transaction construction, as either demanding to be a one, opting in at the aggregator's discretion, or declining. The aggregator has an incentive be a validator (and to do so honestly), but is not required to.

### Co-Spend proposals

Co-spend proposals specify a set of outpoints of coins intended to be spent together. Fully accepted proposals take effect contingent on the conditions they specify, such as the range of feerates the offer is valid under, `nLocktime` ranges, or whether or not txid stability is required (i.e. only SegWit inputs). The effect of a proposal is some confidential redistribution of the input funds, e.g. fees negotiated between the transacting parties.

#### Making and ratifying co-spend proposals

A proposal specifying $n$ UTXOs can have $1 \leq m \leq n$ linkable ring signatures by the associated online keys of the named UTXOs.

While $m < n$, a proposal is only partially accepted. Which of the peers have accepted a partial proposal is kept hidden by the ring signatures. This includes keeping the proposer anonymous within this set of signers; technically, the proposer is just the first to accept, and at least one peer needs to accept for anti-Sybil flood protection reasons.

If $m=n$ linkable ring signatures with distinct key images have been collected, then a proposal has been unanimously accepted.

Finally, for a proposal to be fully accepted, the $n$ linkable ring signatures are replaced with a single Schnorr signature made by the MuSig2 aggregate key formed from the set of associated online keys of the UTXOs. This reduces the size, as well as the computational cost of verifying proposals. Because all parties have accepted, no single party can deny having signed. This makes a joint multisignature semantically equivalent to the $n$ individual linkable ring signatures. The deniability of linkable ring signatures only makes a difference during negotiations before all parties have accepted.

Fully accepted proposals can then be broadcast for aggregation. A fully accepted proposal indicates that all owners of the specified UTXOs have some interest in this proposal being in effect.

Individual proposals commit to a specific set of BIP 322 ownership proofs so that the signatures on them are verifiable. Proposals that refer to expired ownership proofs are still considered valid, and more generally, proposals that commit to different ownership proofs are potentially valid as long there is a non-expired ownership proof associated with the UTXO, which is also used for input weight estimations. See the coalition formation proposal section below for details.

Co-spend proposals aren't updatable or revocable once fully accepted, but they do have an expiry (specified in block height, MTP, or UTC time). More than one signature on the same proposal should be considered a flooding attack by all participants, and honest parties should only sign (MuSig2) a proposal once. Again, see below for discussion of flood protection with respect to partially accepted proposals.

However, co-spend proposals are able to explicitly include conflict hints for other proposals, indicating that (at least) the proposer of the conflicting proposal wouldn't accept a coalition formation proposal that depends on the excluded proposals.

#### Effective value adjustments

Proposals verifiably redistribute sats among the UTXOs by adjusting their effective values. Corresponding to each UTXO, a homomorphic value commitment to an adjustment term is included. This adjustment can implement fee payments between peers, and it may be positive or negative for every UTXO.

The sum of all the adjustment value commitments in a proposal is a commitment to the sum of the adjustments. This value, the *surplus* of a proposal, is included in cleartext, and the sum commitment is proven to commit to it in a balance proof. This too may be positive or negative.

When communicating a partial proposal, the proposer shares with each recipient the opening of the commitment associated with their UTXO. This payoff is denominated in sats, and it can be positive or negative.

Each adjustment value commitment is also covered by a range proof certifying that the adjustment is a small positive or negative integer. Small means at least $\lfloor\frac{v}{log_2(v)}\rfloor$, where $v$ is the minimal effective value among all specified UTXOs. This minimum value is computed by taking the highest acceptable feerate in the proposal conditions and multiplying that by the input weights estimated from the ownership proofs.

The sum of the adjustment commitments, when tweaked by the effective value of the UTXO according to the final feerate of the UTXO, must be a commitment to a positive number of sats. This is ensured by accounting for the maximum values in the range proofs, and by ensuring it doesn't overflow the effective value.

Imposing a minimal range width size imposes a limit on how many proposals can be aggregated together, roughly logarithmic in the total value to be spent. Proposals can use wider range proofs than the minimum, which limits their ability to be aggregated and leaks information about the size of the adjustments.

### Proposal aggregation and condition details

A coalition formation proposal is a special kind of co-spend proposal that aggregates together a bundle of non-conflicting, fully accepted co-spend proposals. The coalition formation proposal is made by one of the peers, the aggregator, to *all* other peers implicated in the aggregation. The aggregator must also set specific values for any constrained parameters (e.g. a concrete feerate and not just a range).

#### Making and ratifying coalition formation proposals

Any peer may attempt to construct a coalition formation proposal by aggregating unanimously accepted co-spend proposals together, so long as it controls at least one of the online keys implicated in the aggregation. For rate limiting, the aggregator's key is made explicit, and the hash of this signature is used for flood control when gossipping the partially signed coalition formation proposal, much like the hash of ownership proofs.

Unlike co-spend proposals, coalition formation proposals are accepted with a regular signature by the online key. This makes them tractable for aggregators to make coalition formation proposals that revise the payoff or omit peers who didn't accept. As discussed above, coalition formation proposals aren't mutually exclusive. If a peer rejects a coalition formation proposal due to the inclusion of a specific proposal, it may broadcast a counter final proposal of its own, so there's no mechanism for explicit rejection.

A coalition formation proposal also specifies a concrete transaction construction protocol version, and commits to a specific set of listen advertisements associated with the specified UTXOs, which have either demanded or opted into serving as validators. These peers agree to allow other peers to connect to them and facilitate in gossip. Depending on the liveness requirements of byzantine agreement for the subsequent transaction construction protocol, the aggregator may specify validators at their discretion and named parties may accept or decline.

#### Bootstrapping consensus for transaction construction

Once a coalition formation proposal is fully accepted, a coalition has been formed, complete with a payoff imputation. The online keys are then used to initiate a consensus protocol to construct the full transaction.

Since the coalition formation proposal addresses every UTXO, its ownership proof set commitment is authoritative. This determines the canonical online key set for the coalition, allowing a consensus protocol to be initialized. The aggregator should use [precedence ordering](channels.md) for symmetry breaking to minimize additional gossip and improve the chances of the coalition formation proposal being unanimously accepted, but there's no consensus state for this data at the time the coalition formation proposal is being authored. The purpose of coalition formation proposals is to bootstrap both the consensus protocol and incentive compatibility to make use of it.

#### Coalition formation proposal structure

🤖 The surplus of all included co-spend proposals belongs to the coalition. The aggregator proposes adjustments for each UTXO and an amount to allocate to mining fees. Some or all of the surplus may be allocated to mining fees, which must cover the shared transaction fields at the agreed feerate. These allocations take effect only if the coalition formation proposal is unanimously accepted.

The logical conjunction of co-spend proposals implies the union of their adjusted UTXOs and the intersection of their conditions is in effect. The per-UTXO adjustments are collected for each outpoint. The total adjustment for each UTXO may not overflow its effective value, based on the range proof widths.

Co-spend proposals therefore form a commutative semi-group, unioning the sets of UTXOs and summing the adjustments component wise. It's only a semi-group because proposals can't always be aggregated together. One reason for this is that the conditions might be mutually exclusive. Another is consensus rules (e.g. `OP_CLTV` making conflicting assertions).

Conditions are intersected elementwise. The intersection of mutually exclusive conditions — for example, a time-based vs. a height-based nLocktime — is empty, precluding the combination of such proposals.

The following are all numerical intervals under intersection:

- Transaction consensus fields
  - version
  - individual flag bits (top is {0,1} then {0}, {1}, bottom is {})
  - nIns
  - not included: nOuts, (min cannot be enforced and so can't be included, max is enforced indirectly by vbytes allocation see below)
  - nSequence (constrains all nSequence fields)
  - nLocktime
- Non-consensus parameters
  - feerate
  - max total vbytes per tx (divide by nIns and round down for allocation per input, nIns must be set accordingly to pass standardness or consensus limits)

The following are sets under intersection:

- Allowed input types (catchall "unknown" or "arbitrary" as one of the variants, variants for standard or well known output types)
- Allowed output types

### Flood protection for partially accepted proposals

🤖 Gossip of partially accepted proposals, and its flood protection, is specified under [peer to world broadcast](channels.md).

### Post quantum security and privacy

Apart from the BIP-322 ownership proofs, which are related to spending keys, the signatures used throughout don't require PQ security for privacy (assuming perfectly hiding commitments) or safety, but only for liveness.

However, for privacy, it's important that any proofs of knowledge of openings of the commitments don't compromise the unconditional hiding of commitments, so as to avoid "harvest now, decrypt later" attacks on anonymity (although out of the scope of this document, this is also required for transaction construction).

Secondly, in addition to the secp256k1 online key, a PQ key for end-to-end encrypted communication (e.g. the encrypted openings of commitments included in a proposal) can also be used. HPKE is an obvious choice for secp256k1-based encryption, and hybrid HPKE is specified using ML-KEM, which makes it a relatively simpler change. However, neither of these is verifiable without general purpose ZK, which is often costly for the prover or in proof size. Lattice-based schemes (without a symmetric cipher) seem potentially amenable to such verifiable encryption, but I have yet to look into that. Verifiable encryption is necessary for partial proposal gossip, as otherwise there's no guarantee that the proposal can even be accepted, as some parties may not learn the opening of the value commitments associated with their UTXOs.

Finally, PQ privacy must of course also assume that metadata privacy at the transport layer is also preserved.

### Transaction construction protocol

🤖 The accepted coalition formation proposal specifies the initial inputs, their online keys, the negotiated adjustments and the parameters for [transaction construction](transaction-construction.md). It is the genesis of the construction instance. The initial state can be proven valid with respect to each UTXO's adjustment sum commitments, which enforces that the agreed imputation is in effect. When construction stalls, the [recovery track](recovery-track.md) turns the stall into a new coalition formation proposal among the responsive subset.

🤖 Any participant can act as an aggregator. Assembling a proposal gives that participant no additional privileges during transaction construction.

[^coinswap]: For example [CoinSwap](https://openswap.live/) is such a protocol which relies on atomic swap contracts, designed with privacy in mind.

[^hedonic]: D. Peters and E. Elkind, [*Simple Causes of Complexity in Hedonic Games*](https://arxiv.org/abs/1507.03474) (2015). Shows how modest expressiveness in preferences can make deciding the existence of stable outcomes computationally hard.
