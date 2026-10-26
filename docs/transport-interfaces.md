---
type: Specification
title: Abstract transport interfaces
description: Send, receive and bidirectional channels, the kinds of messaging the protocol needs, and broadcast built from peer to peer channels.
status: draft
stale_after: 2027-04-22T00:00:00Z
---

<!-- cspell:words unlinkable -->

# Abstract transport interfaces

🤖 These interfaces give the protocol an abstract syntax for messages. Every part of the protocol is described in terms of messages: who sends them, who receives them, and what a message reveals about its sender. How a message travels is up to the transport.

🤖 Delivering messages is the transport's job. Its non-malicious delivery faults and delays constrain the timing model the layers above can assume. Agreeing on what was delivered belongs to those layers. Protocol timeouts need not match transport timeouts; see the [communication models](recovery-track.md#fault-tolerance-under-different-communication-models). Wire encodings are out of scope.

## 🤖 Channels {#channels}

* A **send channel** accepts messages, one per send.
* A **receive channel** yields messages, one at a time.
* A **bidirectional channel** is both. Its two directions may carry different message types.

A channel may offer only one direction, and a participant needs only the direction it uses. A receive channel need not belong to one sender: some transports deliver every message for an address to one receive channel.

The protocol should make progress even if a channel delivers only one message at a time. In the asynchronous and partially synchronous models, the network adversary can already impose this.

## Kinds of messaging

With some well-defined way to transmit messages from one peer to another, we can start to reason about how synchronization between peers can happen by using interactivity. Communication serves two purposes: peers exchange payment details directly with their counterparties, and send transaction contributions to the group as a whole.

In order to realize peer-to-peer channels, any transport that provides authentication, integrity and confidentiality may be used. This allows peers to send messages to each other directly, for initiating as well as carrying out transaction construction.

🤖 The protocol needs three kinds of messaging:

| Kind | Sender |
| --- | --- |
| Peer to peer | Authenticated |
| Peer to group | Anonymous |
| Peer to world | Anonymous |

🤖 Peer to group and peer to world are both broadcast. In line with the literature on reliable broadcast, this specification uses "broadcast" for both. They differ in the broadcast domain:

* a **group** is the participants of one session, such as a transaction construction session. Peer to group is also called multicast.
* the **world** is open to anyone, such as the readers of a public order book.

🤖 Some uses:

| Use | Direction | Sender |
| --- | --- | --- |
| Session initiation with known peers (honest and semi-honest settings) | Bidirectional | Authenticated |
| Interactive payments: notification and confirmation for net settlement | Bidirectional, reliable, to one peer | The receiver is authenticated and can reply. The sender need not be authenticated, and game theory suggests it shouldn't be. |
| Offering co-spend proposals in coalition formation | Bidirectional | Sender anonymous |
| Anonymous broadcast within a session, such as transaction outputs in the semi-honest and Byzantine settings | To the group | Message unlinkable and metadata hiding |

## Unlinkability

An authenticated channel may identify the sender of a message, which would be problematic for this notion of privacy. Even if the sender isn't authenticated, transport-related metadata such as IP addresses can leak information about the sender. If transaction fragments are exchanged this way, this can indicate links between inputs and outputs that belong to the same user, even when the final transaction would leave those relationships ambiguous to an outside observer. This is an undesirable trust assumption.

Preserving privacy requires anonymous broadcast to the group. Overlay networks such as Tor can be used to anonymously send messages to peers for relaying. The privacy guarantees of the underlying transport form the basis of message unlinkability, and once a message is not linked to its owner it can be relayed even on a non-anonymous channel. While this can also be achieved without external dependencies, for example using DC-nets, this approach does not scale to large numbers of participants, and is hard to make fault tolerant in addition to still revealing transport-related metadata.

🤖 Two properties describe what a send channel reveals to the peer that receives its messages:

| Property | Messages linkable to each other | Messages linkable to the sender |
| --- | --- | --- |
| Message unlinkability | No | No |
| Connection unlinkability | Yes | No |

* Leaving out a sender field does not make a channel anonymous. Identity can still leak through the transport, or be part of it, as when a connecting peer authenticates.
* Metadata hiding is always with respect to the initiator: the sender, or the side that connects. The responder is identified by its address.
* A connection unlinkable channel that carries only one message is message unlinkable. The same holds for one set of inherently related messages, such as a transaction input and its signature. Timing metadata can still link messages.

## Broadcast from peer channels

Group communication can be built out of peer-to-peer channels; this is known as gossip or rumor-spreading. Alternatively, a specialized broadcast channel implementation can be used. So long as each peer eventually receives all messages sent by every other peer, they will converge on the same transaction fragments, and combine them in the same way to obtain a consistent view of the unsigned transaction.

🤖 Peer to group and peer to world are built by gossip over peer to peer channels that are sender anonymous and message unlinkable.

🤖 A sender submits its message to a member of the broadcast domain over such a channel. From then on, peers relay it like any other message, over channels that need not be anonymous. The anonymity of a broadcast therefore rests on the channel it was submitted on, not on the channels between gossip neighbors.

🤖 [Peer and broadcast channels](channels.md) describes the gossip.
