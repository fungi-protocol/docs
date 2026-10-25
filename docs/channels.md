---
type: Specification
title: Peer and broadcast channels
description: Broadcast to a group or to the world, built by gossip over peer to peer channels.
status: draft
stale_after: 2027-04-15T00:00:00Z
---

<!-- cspell:words Alon Babai blocklace Itai Luby mixnet nostr Nym OHTTP pubsub PWA RIBLT unlinkable -->

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
* **Gossip.** Two models apply, both described by Weaver (Unknown Participants, Changing Topologies, and Faulty Devices, PhD dissertation, Georgetown University, 2023, p. 69 and p. 155):
  * In the **random phone call model**, also called the gossip model, each round a peer exchanges a bounded amount of information with one neighbor, picked at random. The graph is often assumed to be connected ([Karp et al. 2000](https://doi.org/10.1109/SFCS.2000.892324), [Boyd et al. 2006](https://doi.org/10.1109/TIT.2006.874516)).
  * In the **LOCAL model**, each round a peer exchanges messages with all of its neighbors, and the topology has bounded degree ([Luby 1985](https://doi.org/10.1145/22145.22146), [Alon, Babai and Itai 1986](https://doi.org/10.1016/0196-6774%2886%2990019-2)).

  Fungi targets both models.

Connection based channels limit a peer to a more or less static local topology, so a connection oriented transport scales well only in the LOCAL model. A transport that is connectionless end to end can send a message to any peer at any time. It matches the random phone call model, or a low capacity clique.

## Candidate transports

The specification relies only on the channel properties above. These candidate transports are not part of it. Gossip over any of them provides group and world broadcast. The table says what each provides directly.

| Transport | Delivery | Broadcast domain | Sender anonymity | Topology |
| --- | --- | --- | --- | --- |
| BIP 77 mailbox | Store and forward | None, peer to peer | Message unlinkable towards the directory, if the OHTTP relay and the directory do not collude. Messages to one mailbox are linkable to each other by its ID. | Random phone call model: connectionless end to end, so a peer can reach any mailbox. The directory is a hub. |
| OHTTP pubsub | Store and forward, by topic | Group (secret topic) and world (well known topic) | As for the BIP 77 mailbox, for each publish and each read. | Independent servers, connected to each other or not, like nostr relays. Peers bridge between them. |
| Nostr with gift wrapping | Store and forward, by subscription | World | Each event is signed by a one-time key, so it does not name its author. The relay connection still identifies the client, and links the events sent on it. | Independent relays, connected to each other or not. Peers bridge between them. |
| Tor | Connection oriented, low latency | None, peer to peer | Connection unlinkable. With connection isolation, one message per connection is message unlinkable. | LOCAL model: connection oriented, so it scales well only with a bounded number of connections per peer. |
| Nym | Message based mixnet | None, peer to peer | Message unlinkable. Mixing delays and cover traffic resist timing correlation. | Random phone call model: connectionless end to end, so a peer can send to any peer at any time. |

* **BIP 77 mailbox.** [BIP 77](https://github.com/bitcoin/bips/blob/master/bip-0077.md) payjoin already uses it, with directories reached through [OHTTP](https://www.rfc-editor.org/rfc/rfc9458) relays. It suits interactive payments and session initiation with a known peer: the receiver is identified by its mailbox, and the sender need not be.
* **OHTTP pubsub.** A specialized service, with topics in place of mailboxes. It would serve group broadcast, and global gossip as well. It runs on a set of independent servers, much like nostr relays. A broadcast domain can span several servers, or be sharded across them, as long as some peers bridge between the servers and keep the network connected. None exists yet.
* **Nostr with gift wrapping.** [Gift wrapping](https://github.com/nostr-protocol/nips/blob/master/59.md) hides the author in the event, not in the connection. Open gossip that is message unlinkable therefore needs one relay connection per message, over an anonymous channel.
* **Tor.**
  * It has by far the most adoption, compared with Nym or OHTTP mailboxes. [Anonymity loves company](https://freehaven.net/doc/wupss04/usability.pdf), so Tor is likely the better privacy choice, even though its guarantees are weaker than Nym's.
  * Its guarantees are stronger than OHTTP's, with three hops instead of two. Neither resists a global passive adversary doing traffic analysis.
  * It is not usable from a web app or progressive web app (PWA).
  * Being connection oriented, it suits neighbor channels, and submission channels that carry one message per connection, using [stream isolation](https://spec.torproject.org/proposals/171-separate-streams.html).
  * A cold start is slow, because building circuits takes many round trips. Once circuits are built, a new connection costs about the circuit's end to end latency, plus the exit node's connection to the server.
  * A phone waking up pays the cold start. This is the main reason to also support OHTTP: a request takes only a few round trips, because the OHTTP relay keeps its connection to the gateway open. Being request and response oriented, OHTTP also keeps a client's requests unlinked at the server, without a separate connection for each.
* **Nym.** [Nym](https://nym.com/docs) sends to any peer without a connection, so it suits the random phone call model. Mixing adds latency.

## Open questions

1. **Own messages in the synchronized set.** If a sender adds its own message to its set before submission, synchronization shows that it held the message first. Should a sender keep its own message out of its set until it arrives through synchronization?
