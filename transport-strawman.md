# Transport Strawman Ladder

This document describes a sequence of increasingly robust and efficient message dissemination mechanisms for multiparty transaction construction under the Fungi Protocol.

It absorbs the transport-layer concerns of the [upper protocol ladder](./00_overview.md) and its [strawman ladder](https://github.com/fungi-protocol/docs/pull/17). The sneakernet specification remains in the proposed overview structure  but anchors the model here: the limiting case of delivery is one where messages are PSBT fragments merging with a partial order, and delivery may take arbitrarily long. Every rung must degrade gracefully to it conceptually, as a validation oracle: anything that breaks over sneakernet was secretly relying on timing or ordering.

This document explains the main ideas. The detailed technical information, such as framing,encoding and message types are covered in an addendum

**The ladder's contract:** eventual message delivery with set convergence. The protocols need only set consensus (order insensitive), each rung builds on the previous one to improve reliability and efficiency.



## Preliminaries

### Privacy taxonomy

The privacy properties of the underlying transport vary qualitatively. The relevant threat models are:

| Transport | Adversary model | Privacy property |
|---|---|---|
| WebRTC / iroh | honest peers, e2e encryption only | confidentiality, no metadata privacy |
| Tor | local passive adversary | sender anonymity (circuit-based) |
| Nym | global passive adversary | sender/receiver unlinkability (mixnet) |
| OHTTP | relay/gateway non-collusion | sender anonymity (proxy-based) |

Non-collusion underlies Tor, Nym, and OHTTP alike; their robustness varies. Tor depends on path length; Nym depends on network symmetry and Loopix cover traffic. A global passive adversary defeats all but Nym, and can link protocol traffic to the transaction broadcast.

### Target scales

The Desing follows two main rules.

**Transaction construction**:  up to hundreds of peers, many small messages on the happy path, larger validity proofs on the sad path.

**Open broadcast** (order book / coalition formation): potentially many more peers, fewer but larger messages. Co-spend proposals in particular are large.


## P2P channels

### What does this add

A point-to-point message channel: the cellular  building block that every higher rung builds on .

### Substrate

A channel is an async, typed, bidirectional message pipe to only one  peer, moving opaque byte messages one at a time. It provides confidentiality and integrity but deliberately excludes ordering, deduplication, framing, and per-message anonymity as those are handled by other layers.

The channel contract:

- **Best-effort delivery.** NO end-to-end delivery confirmation.
- **Explicit failure semantics.** A message that exceeds the transport's size limit(errors) is the only case where a channel can recover from an error. Any other case means the channel is dead and recovery should be done via a new channel.
- **No liveness detection.** A silently dead path parks  forever. Timeouts and keepalives belong to a higher layer.


**Connection lifecycle.** Oppening  a channel carries a precise identity contract:

- **Dialing is initiator-anonymous.** The transport presents no identity of this peer to the responder.
- **Accepting is anonymous.** the listener learns nothing about who dialed, and implementations must not expose an initiator identity through any side channel.

**Session isolation.** Connectors can be bound to a logical session. Channels from different sessions must use separate transport circuits. This prevents network metadata from being used to link their streams. Channels of the same session may share one. This is how multiparty transaction construction sessions prevent one session's traffic patterns from being linked to another's.

**Representative substrates.** Tor and OHTTP are the two representative substrates, each illustrating a different transport shape:

- **Tor (stream).** A Tor circuit provides a reliable byte stream. Length prefix framing (4 byte big endian payload length, then the payload) adapts it into a datagram channel. Both an external tor daemon (via SOCKS5h) and an in process Arti backend are supported.

- **OHTTP (datagram).** OHTTP provides datagram oriented delivery via an HTTP relay. Each request and response pair is a message exchange. With the same channel interface, the two substrates are interchangeable from the consumer's perspective, the same protocol code runs over either.

With framing, both provide the same logical channel abstraction. d

### Tradeoffs

| Dimension | Tor (stream) | OHTTP (datagram) |
|---|---|---|
| Privacy model | sender-anonymous circuits, local passive adversary | proxy non-collusion |
| Connection | persistent, bidirectional stream | stateless request-response pairs |
| Reliability | reliable (TCP nature, in-order within a circuit) | per-request, no persistent state |
| Latency | circuit setup latency (seconds), then low | per-request relay overhead |
| Mobile friendliness | poor (long-lived circuits, background connectivity) | good (stateless, tolerates intermittent connectivity) |
| Bandwidth overhead | circuit maintenance, cover traffic negligible | per-request relay headers |

Framing costs 4 bytes per message on stream transports. The channel contract deliberately exposes no ordering across channels and no deduplication to kep  the sneakernet degradation requirement.

### Drawbacks

A channel connects exactly two peers. To reach $n$ peers, you need $n$ channels and nothing at this level coordinates among them. There is no group semantics, no relay, no message fan-out, and no discovery of peers. 
### Problems

1. **No group communication.** Every exchange is point-to-point. Sending a message to a group requires the sender to transmit it $n-1$ times independently with no guarantee that all peers see the same set.

2. **No liveness detection.** A silently dead channel parks forever. Callers must impose their own timeouts, and there is no built-in way to distinguish a slow peer from a dead one. This is deliberate but means that any group protocol built on channels must handle channel death explicitly.

3. **No peer discovery.** Addresses are obtained out of band. Nothing at this rung advertises or discovers peers.

4. **No redundancy.** A single channel is a single path. If it dies, the message is lost unless a higher layer retransmits on a new channel.


### Web clients and constrained peers

### What does this  add?

Bridges that let web clients and mobile peers, which cannot run Tor or maintain long-lived connection. They can participate in the channel layer by connecting through intermediaries or alternative transports.

### Substrate

Web clients (including PWAs) face compatibility limits that are hardest on mobile: no raw TCP sockets, no Tor, limited background connectivity, and browser sandboxing limitations. This rung addresses this with several bridging strategies, each with a different trust/privacy level.

**OHTTP as bridge to the overlay networks.** Following the pattern of BIP 77 mailboxes, an OHTTP relay can bridge a web client into the Tor-based overlay. The client posts messages to the relay, which forwards them to the Tor network on the client's behalf. The client's privacy is dependent  on non-collusion between the OHTTP relay and gateway just like in BIP 77 but extended to general-purpose messaging.

**WebRTC peer-to-peer.** WebRTC allows two peers to connect directly. A server is only needed to help them establish the connection using ICE (STUN/TURN). The signaling server learns that two peers are establishing a connection but not the content. However, WebRTC provides no transport metadata privacy from the other peer as peer IPs are mutually known. This is adequate in the honest setting  but unsuitable in the setting where peers are not trusted to follow privacy.

**DC nets for message anonymity within a group.** Even if peers know each other’s IPs, a dining-cryptographer network can still hide message senders. This decouples *message authorship* from *network identity*: every peer sees every message, but cannot tell which peer authored which. 

Key constraints:

- Only for trusted peer groups. Metadata is not checked, if one colluding participant can break anonymity.
- Honest and semi-honest settings only.
- Composed with the delegated bridge below, the delegate is reduced to liveness trust (can censor, not deanonymize; 1-of-k deniability).
- See [Arbitrary Length k-Anonymous Dining-Cryptographers Communication](https://dl.acm.org/doi/pdf/10.1145/3372297.3417261), which leaves group formation to external trust which is the peer's own trust list.


**Delegated broadcast via a trusted peer** (honest/semi-honest settings):

- *The home node as relaying peer.* A peer with a persistent network presence acts as the actual protocol participant, This peer handles sending message to other peers.
- *Trusted peer proxying for its group.* A trusted peer bridges WebRTC→Tor for a group of mobile-only friend (constrained clinet that cant hold connections for long). The proxy relays messages between the WebRTC-accessible group and the Tor-based overlay, bearing the cost of Tor circuit maintenance on behalf of its group.

### Tradeoffs

| Bridge | Privacy cost | Trust requirement | Availability |
|---|---|---|---|
| OHTTP relay | relay/gateway non-collusion | non-colluding pair | good (stateless HTTP) |
| WebRTC p2p | peer IPs mutually known | honest peers | good (browser-native) |
| DC nets | group members know IPs, not authorship | honest/semi-honest group | limited (high overhead) |
| Delegated (home node) | delegate sees all traffic | honest/semi-honest delegate | good if home node available |

Every bridge compromises on  something. The fundamental issue is that  a constrained client cannot independently establish anonymous connectivity (that requires Tor or equivalent), so it must either leak metadata to peers (WebRTC), trust a relay with non-collusion (OHTTP), or trust a delegate with liveness (home node / proxy). zero-trust option for constrained clients currently does not exist.

### Drawbacks

The prior solutions provides  *access* to the channel layer for constrained clients, but does not change its topology. The problems of plain peer to peer networks remains, no group communication, no fan-out, no discovery. A web client connected via OHTTP bridge or delegated proxy still has a point-to-point channel to only one peer. Scaling to group communication is needed.

### Problems

1. **All bridges trade privacy or trust.** There is no bridge option that preserves full transport metadata privacy without trusting some intermediary. Constrained clients face a choice: non-collusion (OHTTP), IP exposure to peers (WebRTC/DC nets), or liveness trust in a delegate.

2. **Delegate availability.** The home node / proxy model works only if the delegate is online and reachable. The delegate is a single point of failure for connectivity. If the delegate goes down, the constrained client cannot participate until it recovers.

3. **DC net overhead.** Dining-cryptographer networks scale poorly: communication is $O(n^2)$ per message in the group, and latency grows with group size. This limits DC nets to small, trusted groups rather  than the hundreds of peers targeted by transaction construction.

4. **Browser constraints are moving targets.** WebRTC, Service Workers, and PWA capabilities change across browser versions and platforms. A bridge strategy that works today may not survive the next mobile OS release's restrictions on background connectivity. The spec must treat browser capabilities as a compatibility surface, not a stable substrate.


## Multicast

Send on every channel, static membership, participating authorization is via a shared-secret handshake.



**Problems:**

- $n^2$ circuits between $n$ peers.
- Partial connectivity: it silently breaks under partial connectivity ,the moment some peer  can't reach each other, “send on every channel” has no channel to send on.
- Dynamic membership:  peers may join or leave.
- Mobile peers: intermittent connectivity, limited bandwidth.


### Coordinator broadcast

Thi is an an alternate solution to the multicast problem, solves its problem  by centralizing, and remains necessary for constrained clients. This is the transport analog of the trusted coordinator in the upper protocol ladder. Good example is a bip 77 mailbox directory.

The coordinator is either a **designated leader** (a participating node taking on asymmetric burden) or a **third-party server**.

A participant-hosted coordinator (public IP, HTTP/OHTTP) places a transaction participant  in charge of light clients' transport privacy, with no authorization mechanism:

- Acceptable in honest/semi-honest settings only.
- In the BFT setting this must be a third-party service.

**Semantics:** a per-topic, grow-only message set with multi-homing (in the server case).

This is what  constrained clients rely on since they can opt out of relaying.

**Group API:** post once, fetch only what's missing. Communication is linear per client.

**DoS mitigation** (server case only; peers are covered by protocol-level protections):

Anonymous rate-limiting credentials:KVAC or ARC (as in bitcoin-pir) — issued per UTXO, in exchange for payment or via proof of work. The goal is bounding data rate from both the service's and the peers' perspectives.

## Problem
- the coordinator is trusted with liveness.
- Single point of censorship and failure, and it can selectively omit which is  indistinguishable from slow delivery until peers reconcile directly.
- An open, no-auth mailbox is a flood target, and a participant-hosted coordinator is unacceptable in BFT


## Gossip (epidemic broadcast)

The standard, proven way to get eventual set convergence over a churny, partially-connected, heterogeneous overlay, tolerant of peers joining and leaving, and it degrades to sneakernet naturally, which is Fungi's exact delivery model.
Gossip supersedes multicast directly  not coordinator broadcast. Only gossip bridges overlays, where peers on different networks can reach each other only through a peer that speaks both.

- Re-send on all channels.** Logical message identity is maintained across transports.
- Scales to the hundreds of peers that multicast can't, and matches the CRDT: a message just propagates whenever any link exists.

### Robust overlays

Churn-tolerant overlays with partial views or random walk peer sampling, with and without the OHTTP service. Three-way interop between different transport substrates.


### Push, pull, and hybrid

- **Push** (rumor mongering): forward new messages eagerly to random peers.
- **Pull** (anti-entropy):  periodically compare state and exchange differences.
- **Hybrid**: combine both; fanout and round parameters govern the latency/redundancy tradeoff.

### Eager + lazy push

Epidemic broadcast trees (Plumtree) over HyParView partial views, as in iroh-gossip:

- Full messages travel over a spanning tree.
- Only message IDs are sent on the remaining (lazy) links.
- The tree self-repairs under churn.

### Discovery

BIP 322 ownership proofs certify listen advertisements (endpoint metadata). The advertisements themselves are gossiped.



**Problems:**

- Redundant bandwidth (mitigated but not eliminated by lazy push).
- Selective omission — a Byzantine peer can forward some messages and suppress others.


## Set reconciliation

**Goal:** all participants converge on the same message set. Order insensitive, supporting multiple epochs and asymmetric capabilities.

### Primitives

**Sketches.** Erlay-style minisketch, compact difference sketches that require a difference estimate and fixed rounds.

**Partition recovery.** Rateless IBLT, CertainSync, multi-server variants, These handle larger differences and recover partitions without needing to know their size in advance
### Which primitive?

Recursive/range-based approaches cost $O(\log n)$ round trips per peer pair which is expensive over anonymous transports where latency is high.

Rateless approaches (rateless IBLT, CertainSync) need no rounds and no difference estimate, at the cost of coding overhead and a shared strong hash.


### Tradeoffs

| Dimension | Approach | Strength | Cost |
|---|---|---|---|
| Latency | Epidemic broadcast | Fast dissemination | Redundant bandwidth |
| Bandwidth | Set reconciliation | Minimal redundancy | Round-trip latency |
| Communication | Erasure coding | Cubic → quadratic | Coding overhead |
| Communication | Network coding | Spectrum between erasure and gossip | Complexity |

The payoff of these tradeoffs must be evaluated at the target scales defined in the preliminaries.

### Multiparty reconciliation

Multiparty set reconciliation is thinly studied:

These cover honest parties / single epoch only ,none cover our setting. Recent primitives are otherwise 2-party (rateless IBLT has a relay extension).

