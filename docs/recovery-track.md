---
type: Specification
title: Recovery track
description: How a stalled phase of the optimistic track turns into a recovery coalition formation proposal.
status: draft
stale_after: 2026-11-06T00:00:00Z
---

<!-- cspell:words Dwork Lynch Stockmeyer APSA APSA's Baudet Brugeres CRBB Chondros Christos Croman Danezis Deligios Diamantopoulos Dolev Duan Ehud Eurocrypt Falbesoner Garay Guerraoui Haibin Haifeng Idit Ittai josibake Keidar Kelkar Kichidis Klasovita Kuznetsov Languille Mahimna Maneas mathit Maxence Mema Minghang Naor Nikos Oded Ouri Patsonakis permissioned Pieter Poupko Rachid Reiter Roussopoulos Ruomu Sisi Skoumios Somsen Sonnino Stathis Tasos texttt Tonkikh Vassilis Wonseok Wuille Yuval Zarfaoui Zhuolun Zikas antichain counterpropose mathcal mathrm operatorname paxpay precommitted semilattice -->

# Recovery track

## Fault tolerance via branched execution

Somewhat surprisingly, the optimistic track and the recovery track can both proceed more or less independently.

Under asynchrony and in the presence of (Byzantine) faults, due to the unanimity requirement the best consistency guarantee that can be made for the optimistic track is eventual consistency. No liveness guarantee is possible in the presence of faults for a particular run of the transaction construction protocol.

Recall that when multiple transactions attempt to spend some of the same coins, it is up to miners to determine which one (if any) will be confirmed in a block. Miners are assumed to follow their incentives, maximizing fee revenues. Even if transaction replacement wasn't useful or desirable, there is no mechanism that can enforce that unspent outputs are exclusively bound to one transaction construction session over another without *global* consensus.

As we have seen, the success path always reaches termination, and can only reach it by observing unanimous agreement, and when that is possible progress requires only eventual consistency. Validity proofs reduce Byzantine faults to omission faults, so recovering liveness in the presence of failure requires partial synchrony assumptions at the very least.

Since input exclusivity is neither desirable nor enforceable, we can embrace its absence and reframe liveness in a simpler way by treating all failure recovery as branching off another instance of the protocol with a subset of the participants precisely when that subset of the participants can agree among themselves that a failure condition has been detected. Such agreement inherently requires synchrony or partial synchrony, and so explains why this is needed for fault tolerance. In this case the blocks at some height $h$ with $t < n$ parent blocks will be produced as part of the recovery synchronization protocol on top of which a new transaction construction session will commence. If messages are delivered allowing a block at height $h$ to be produced with $t = n$ messages, the asynchronous base protocol can resume progress resulting in the diverging protocol states at height $h$. This special case has the same structure as all-to-all broadcast.

Since recovery is just permissioned coalition formation, any participant may act as an aggregator and make a coalition formation proposal based on its local view; the proposed participants must all accept before it starts. Membership changes can alter anonymity or payment terms, so participants may renegotiate or decline. Recovery also has a privacy cost: excluding an input links it to the outputs that drop out with it, even if its owner was merely unresponsive.

The reason this framing is simpler is that recovery attempts do not need to terminate the run of the protocol that they are trying to recover. In the case that both branches eventually succeed, Bitcoin itself will adjudicate the conflicting transactions. We can treat failure recovery as a (more) synchronous layer building on a fundamentally asynchronous optimistic base protocol with BEC semantics.

## Consistency, liveness and termination in the presence of Byzantine faults

In typical definitions of Byzantine fault-tolerant distributed consensus or agreement protocols, once a majority of honest peers has settled on a certain state, any lagging honest peers will only ever accept updates that progress towards that state when they are able to catch up. Unfortunately for our purposes this isn't enough for fault-tolerant transaction construction, since *successful* termination of the protocol requires unanimity.

If a majority of the honest users can agree on a set of inputs and outputs, but one of the honest participants not in this majority still hasn't submitted all of their outputs, then it would rightfully withhold its signatures even if it does come back online. When assuming the asynchronous communication model, this can delay termination indefinitely, and achieving a majority is not sufficient for termination.

Contributing signatures to a transaction that may become valid when fully signed is both an honest signal and a signal of honesty. In the signalling-theory sense, it is not costless, since the transaction may have consequences such as mining fees if the other parties also sign. Contributing signatures *also* signals honesty in the sense defined above: validity proofs make it safe for honest participants to sign regardless of the actions of other users, so they have no reason to withhold their signatures. A which deviates or defects from transaction construction can veto the transaction but at the cost of withholding a signature on at least one of their inputs.

In lieu of agreement about a transaction, agreement on the available evidence can still support liveness by allowing recovery from a fault. This boils down identifying inputs for which signatures have not yet been received. A missing signature may still eventually arrive, completing the transaction, but to avoid waiting indefinitely, participants can negotiate another transaction construction attempt while continuing to listen for progress in the original one.

Under synchrony or partial synchrony (specifically the eventual synchrony variant), if a sufficient threshold of peers can all agree it has been too long, then they can initiate such a recovery session. A threshold of peers agreeing implies a majority of honest peers agreeing. Note that agreement by a majority of honest participants requires a supermajority threshold. A quorum is a set of peers meeting the required agreement threshold. Given $n = 3f+1$ where at most $f$ are faulty, a quorum of $2f+1$ peers will include at least $f+1$ honest peers, a majority within any such quorum.

So long as the notion of "too long" is well defined (consistent with the communication model) and agreed to by such a quorum, whenever there are up to $f$ inputs owned by faulty peers honest parties should be able to successfully complete a run of the protocol after $O(f)$ attempts by simply excluding those inputs as it becomes apparent that they are disruptive or unresponsive. Even in the worst case this process ensures at least one input can always be excluded.

If there are more than $f$ faults recovery is still possible but coordinating recovery attempts by identifying the subset of inputs eligible to participate in recovery requires additional assumptions.

## Fault tolerance under different communication models

If a subset of participants can all agree that some other peers are faulty, they could recover by restarting transaction construction without those peers' inputs, allowing them to produce a valid transaction without those peers. Deciding when a peer is unresponsive, the only kind of fault that is tolerated in the honest threat model, largely depends on how messages are transmitted. Depending on what can be assumed about message delivery, different guarantees about liveness or fault tolerance can be made.

The distributed systems literature typically divides this into three communication models: asynchrony, synchrony, and partial synchrony.[^dls] Each demands a different approach to fault tolerance. These models also apply in the more adversarial settings.

### Asynchrony

In the asynchronous communication model, messages may be arbitrarily delayed, so when an expected message fails to arrive, we cannot conclude the sender is faulty because when that happens isn't well defined. This setting is the simplest in which correct behavior can be reasoned about, because it makes the weakest guarantees. If we assume all peers are honest, the only recourse is to keep waiting.

### Synchrony

Intuitively, a peer that has been unresponsive for too long can be considered faulty. By adding timeouts, we can recover liveness by simply giving up coordinating with such peers.

The synchronous communication model is typically in play whenever a protocol relies on specific timeout values, i.e. defining how long is "too long". This model assumes that the participants can agree on what time it is, and that all sent messages will arrive no later than some maximal delay. If a message that is expected to arrive fails to do so before the timeout elapses, the peer which was supposed to send is said to experience a crash fault, rendering it unresponsive for the remainder of the protocol, or an omission fault if it was temporarily unavailable and some of its messages were not delivered.

Note that such delays may be arbitrarily long, provided their bound is well defined, even if the underlying transport requires interactivity on a shorter time scale. For example, we might use TCP/IP with timeouts on the order of tens of seconds to interact with a store-and-forward service that allows peers to send each other messages with timeouts on the order of hours or days. The model assumed by the underlying transport or its parameters need not agree with the model assumed for transaction construction.

### Partial synchrony

Partial synchrony lies in between. Like the synchronous model, it assumes message delivery is timely, but unlike the synchronous model, the bound on the delay either isn't known or may not always apply, so simply waiting for a timeout duration will not suffice to obtain liveness. Typically this requires acknowledgement from some threshold fraction of participants in order for progress to be made.

## Privacy

Note that synchronization has consequences for privacy as well, when operating outside of the design parameters. A majority of malicious validators, for example, could disrupt gossip and inclusion of certain messages in order to deanonymize them. In this scenario, the participant which unsuccessfully attempted to anonymously broadcast that message but failed can choose to include it, which would potentially implicate it as the author, or defect from validation in order to avoid acknowledging a state which does not include the message. However, in such a circumstance it would be better to allow outputs to be omitted and to withhold signing with one of the inputs in order to reveal as little as possible.

Other chapters link to these sections:

## Recovery overlay

## Evidence that excludes at once

## Recovery track blocks

## Recovery proposal

## Open questions

## References

[^dls]: C. Dwork, N. Lynch and L. Stockmeyer, [*Consensus in the Presence of Partial Synchrony*](https://groups.csail.mit.edu/tds/papers/Lynch/jacm88.pdf) (1988). The introduction contrasts synchronous and asynchronous models and defines the two forms of partial synchrony used here: an unknown timing bound, or a bound that holds only eventually.
