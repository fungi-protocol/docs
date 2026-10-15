---
type: Specification
title: Peer and broadcast channels
description: Broadcast to a group or to the world, built by gossip over peer to peer channels.
status: draft
stale_after: 2027-04-15T00:00:00Z
---

<!-- cspell:words blocklace RIBLT unlinkable -->

# 🤖 Peer and broadcast channels

Peer to group and peer to world messages are broadcast. Both are built by gossip over peer to peer channels, using the send and receive channels of the [abstract transport interfaces](transport-interfaces.md). A broadcast channel is itself a send channel and a receive channel, so protocol code that broadcasts sees only those two.

* **Send** submits a message to the broadcast domain. The sender does not choose which peers the gossip reaches.
* **Receive** yields messages from the broadcast domain. It need not authenticate or distinguish anonymous senders.

## Broadcast domains

Gossip always happens within a namespace or topic, which names the broadcast domain.

* A **group** namespace is ephemeral. It is derived from a shared secret with a tagged hash, as for a transaction construction session. A secret namespace restricts discovery, but it does not hide authorship, and it does not stop members from sharing it.
* A **world** namespace is well known, such as a public order book.

If the namespace includes a block hash, message IDs can be short.

A session's initiation message binds its namespace to the construction context, including the initial PSBT state and parameters. See [session initiation issue #61](https://github.com/fungi-protocol/fungi/issues/61).

Gossip by itself does not provide reliable broadcast, agreement, a total order, or evidence that every participant has received a message. Those need protocol rules on top. For transaction construction, the [block DAG](block-dag.md) provides them.

## Peer channels

A broadcast channel uses two kinds of peer to peer channel:

* **Neighbor channels** connect a peer to each of its gossip neighbors. They are bidirectional, and may be authenticated. A neighbor's authentication identifies the neighbor, not the author of a message it relays.
* **Submission channels** carry the peer's own messages into the broadcast domain. They are sender anonymous and message unlinkable.

## Gossip messages

These travel over neighbor channels. The minimal set suffices for the honest setting:

* **announce** a message by its hash;
* **pull** a message by its hash;
* **push** a message that a neighbor pulled.

The semi-honest and Byzantine settings add **unsolicited push**, used for anonymous broadcast. A peer that receives a new unsolicited message pushes it to one randomly selected neighbor, and announces it to its other neighbors. This is a candidate policy, not an established anonymity guarantee.

## Anonymous submission

1. The sender pushes its message, unsolicited, to a member of the broadcast domain over a submission channel.
2. That member handles it as any new unsolicited message. From then on it is an ordinary message in the synchronized set. A message that is not linked to its author can be relayed even on a channel that is not anonymous.
3. The sender watches synchronization for its own message. It keeps submitting anonymously until it is satisfied that the message has been disseminated.

The broadcast's anonymity therefore rests on the submission channels, not on the neighbor channels. Removing an author field later cannot undo what the submission channel revealed. If a message is first announced by an identified peer, and then pulled from it, that peer is revealed as the first to hold it, even if later gossip hides the route.

## Synchronization

Convergence is the point of a transaction construction session. Each peer therefore synchronizes the set of all session messages with each of its neighbors. Order does not matter: the result is the union of the sets. This includes the blocklace, the session's block DAG. A peer's broadcast receive channel yields each message when it first enters the peer's set.

Every message carries a state commitment: the Merkle roots of the sender's sets, with height and set sizes. Fetching an ever-growing set of sets is a resource exhaustion risk. Blocks are necessary for progress, and cordiality rate limits them.

Honest peers should converge on the messages to include before producing blocks. A peer should be eager to gossip, but not too eager to produce blocks.

The goal is that all participants, even those with asymmetric capabilities such as limited bandwidth, arrive at the same set of messages. This repeats over multiple epochs.

## Dissemination methods

**Epidemic gossip** is the minimal approach: announce new messages to neighbors, which pull the ones they lack. It works over simplex peer channels. It avoids write contention and multiple readers per destination, and the potential censorship these allow. It will likely win on latency. But announcements are sent for every message to every neighbor, and a peer may hear of the same message many times.

**Set reconciliation** is a later improvement of blocklace dissemination efficiency. Two neighbors compare their sets and learn which messages each is missing. It throttles or suppresses announcements. Communication then grows with the difference between the sets, not with their size. It will likely win on communication complexity. Range based reconciliation and rateless invertible Bloom lookup tables (RIBLT) are candidates. Multiparty set reconciliation has not been studied as far as we know; recent work covers two parties. A peer can still reconcile with each neighbor in turn. See [peer set reconciliation](set-reconciliation.md).

**Network coding**, such as algebraic gossip on top of the same structure, offers a whole spectrum of further possibilities, with some additional complications.

The same building blocks may not suit both peer to world broadcast (coalition formation) and peer to group broadcast (transaction construction). Message counts and sizes also vary: small messages on the happy path, larger ones for validity proofs.

## Topology

* **Hub and spoke.** Some peers are better connected, and many others connect to them.
* **Clique.** Every peer is connected to every other peer, with no distinction between them. A transport that can send to any peer at any time, without a connection, behaves like this.
* **Gossip.** In the random telephone model, any peer may be reachable, and each round a peer shares new information with one neighbor. In the local model, each peer is connected to only part of the network. Fungi mainly targets the local model, with a limited number of connections per peer.

Connection based channels limit a peer to a more or less static local topology. A transport that can send a message to any peer at any time behaves more like a low capacity clique, or the random telephone model.

## Open questions

1. **Own messages in the synchronized set.** If a sender adds its own message to its set before submission, synchronization shows that it held the message first. Should a sender keep its own message out of its set until it arrives through synchronization?
