---
type: Specification
title: Peer and broadcast channels
description: Broadcast to a group or to the world, built by gossip over peer to peer channels.
status: draft
stale_after: 2027-04-15T00:00:00Z
---

<!-- cspell:words Alon Babai blocklace Itai Luby minrelayfee mixnet nostr Nym OHTTP pubsub PWA RIBLT unlinkable wtxid -->

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

## Peer to world broadcast

### Setup: BIP 322 gossip, online key enrollment

Every spendable coin could potentially be spent in a multiparty transaction (although not all coins can be co-spent). To facilitate this, we require a gossip mechanism for BIP-322 ownership proofs, with a replacement and expiration mechanism for flood protection, committing to a public key referred to as the *online key* for the coin.

The purpose of this online key is to authenticate the owner of the UTXO without requiring them to access the spending keys for communication. Anonymous authentication requires the use of ring signatures (and are therefore less likely to be supported by a HWW than BIP-322 proofs), and also simplify the mapping to just a single public key per UTXO, regardless of the complexity the `scriptPubKey` might have (complex multisig or ambiguity from multiple spend paths).

Ownership proofs are also used to estimate input weights. For P2TR outputs, this indicates the spend path intended to be used in any collaborative transactions. Note, however, that this isn't enforceable.

Each proof's endorsement of the online key has a validity interval specified in terms of Bitcoin block height or MTP (valid-after and valid-until). When multiple proofs by the same UTXO are nominally in effect, the one with the latest expiry time takes precedence. Ownership proofs commit to a block hash whose height or MTP is within some set interval of the valid-after field.

#### Flood protection

Online keys may need to be rotated. A rate limiting mechanism is needed for ownership proofs, and more generally for other protocol messages.

Ownership proofs are tied to UTXOs that provides some degree of Sybil protection, since creating UTXOs incurs a cost. However, this is insufficient for flood protection, since there is no restriction on how many ownership proofs can be created.

Note that Sybil resistance for flood protection is a separate concern from Sybil resistance in the context of CoinJoin $n-1$ deanonymization attacks on CoinJoins. The latter is assumed to be encoded of the cost function, and therefore out of scope for this protocol.

To be accepted (and propagated through gossip) by a peer, any newly made proof associated with a coin must have a hash value (e.g. wtxid of the BIP 322 `to_sign` virtual transaction) numerically smaller than all the other proofs already associated with that output which are known to the peer.

Because ownership proofs may be valid at disjoint time intervals, a peer should store up to $k$ proofs (in total, not per validity time interval) in its gossip set for each candidate UTXO, so long as the hashes of *all* of these are numerically smaller than $c_1 + 2^{(c_2 d k)}$, where $d$ is the total duration of all proofs, and $c_i$ are dynamically set policy values (similar to `minrelayfee`, based on local resource limits).

#### Precedence ordering

In addition to rudimentary flood protection for the ownership proof gossip, this defines a clear precedence order. This is so that with respect to a specific block tip, even without global consensus on the set of all ownership proofs, it's possible to efficiently arrive at the unambiguous mapping from a particular set of UTXOs to the same set of online keys by sharing with peers any relevant proofs they might be missing.

If the online keys are generated by hash chain (similar to LN revocation keys), revealing the key can revoke a previous ownership proof, forcing a linear sequence of key updates, and providing a mechanism for efficient revocation. However, it's unclear at the time of writing whether revocation is required at all, and the proof of work approach to flood protection seems sufficient.

Similarly, rate limiting could be done by restricting the rate of broadcast on the basis of the committed block hash, but on its own, this wouldn't establish a precedence order, and in the absence of consensus on the set of ownership proofs, it may result in ambiguities about which online key to use.

### Listen advertisements

Peers should only gossip [listen advertisements](coalition_formation.md) for currently active or soon-to-be-active online keys. The hash of the signature is used as a flood protection mechanism, similar to ownership proofs.

### Flood protection for partially accepted proposals

Partially accepted proposals can be communicated directly only between involved peers or gossipped to third parties. Gossip of partial proposals enables a single proposer to make many nuisance offers involving different sets of keys. Normally linkable ring signatures will protect their identity, which means that other nodes can only use a statistical approach to detect the culprit and may mistakenly penalize the UTXOs the attacker names, without their owners contributing to this flooding attack. "Normally" means the key image generator point is just be a hash to curve of the proposal data itself, allowing a practically unlimited number of ring signatures per UTXO (exponential in the size of the candidate UTXO set).

To limit this behavior, the linkable ring signature key image base point can be time dependent (e.g. making use of a sufficiently buried block's hash as a randomness beacon) and include a truncated hash of the proposal when choosing the generator (by hashing to the curve). Truncating to 10 bits, for example, would allow up to 1,024 unrelated proposals to be accepted or made by a single UTXO equivocation per timestep, allowing flooding to be prevented. Note, however, that honest users may be restricted from accepting some honest proposals due to the birthday bound, but honest proposers with knowledge of other proposals can grind the proposal data to avoid collisions, and we of course assume attackers can do this without restriction).

Additionally, it's possible to make use of a verifiable encryption scheme for the openings of the commitments, allowing verification of the proposal during gossip, but this doesn't prevent the broadcast of nuisance proposals that wouldn't be accepted despite being formally valid.

In contrast, in a semi-honest setting, and if acceptors don't mind revealing whether they accept to the proposer, the linkable ring signatures can be shortcut entirely and MuSig2 negotiated directly, with the proposer collecting the nonces and partial signatures of all named parties. MuSig2 signing should still be initiated concurrently, even when linkable ring signatures are used to minimize the number of round trips.

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

🤖 Anonymous submission introduces a message into the broadcast domain. Once received, the message is disseminated by gossip or set reconciliation. The submission mechanism and the subsequent dissemination serve different purposes.

## Anonymous submission

1. The sender pushes its message, unsolicited, to a member of the broadcast domain over a submission channel.
2. That member handles it as any new unsolicited message. From then on it is an ordinary message in the synchronized set. A message that is not linked to its author can be relayed even on a channel that is not anonymous.
3. The sender keeps its own message out of its synchronized set until it receives the message through synchronization. It then processes and relays the message by the same rules as any other received message, without using its knowledge of authorship. Until it is satisfied that the message has been disseminated, it continues submitting anonymously.

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
