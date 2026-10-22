---
type: Specification
title: Protocol messages
description: The messages peers exchange, who sends them, when, and what each requires of its channel.
status: draft
stale_after: 2027-04-22T00:00:00Z
---

<!-- cspell:words blocklace ECMH fastcrypto multiset prevout RIBLT unlinkable -->

# 🤖 Protocol messages

## Scope and status

This chapter lists the messages peers exchange in the Fungi protocol suite. For each message it says who sends it, to whom, in which setting, what it carries, and what the channel carrying it must provide.

It is a draft. Wire encodings, field sizes and signature profiles are not specified yet. Sizes below are orders of magnitude. Each section ends with its open questions.

The messages fall into these groups:

| Group | Purpose | Settings |
| --- | --- | --- |
| [Peer introduction](#peer-introduction) | Learn and label peers out of band | honest, semi-honest |
| [Gossip](#gossip) | Disseminate objects within a namespace | all |
| [Sets](#sets) | Commit to, list and reconcile sets of objects | all |
| [Public gossip](#public-gossip) | Order book for coalition formation | Byzantine |
| [Negotiation](#negotiation) | Bilateral co-spend and coalition proposals | Byzantine |
| [Session initialization](#session-initialization) | Start a construction session | all |
| [Transaction construction](#transaction-construction) | Build the transaction | all |
| [Interactive payments](#interactive-payments) | Grant funds and confirm payments | honest, semi-honest |
| [Blocks](#blocks) | Synchronize state and signal phase changes | semi-honest, Byzantine |

## Channel requirements

Channels are described by their properties, not by a transport. Choosing a transport that has these properties belongs to another layer.

| Property | Values | Interface |
| --- | --- | --- |
| Direction | send, receive, or both | `SendChannel`, `RecvChannel`, `Bidirectional` |
| Delivery mode | one peer, or broadcast | `PeerChannel`, `BroadcastChannel` |
| Unlinkability | per channel, or per message | `UnlinkableMessageChannel` |
| Delivery guarantees | reliable or unreliable | |
| Timing | asynchronous or synchronous | |
| Metadata hiding | hides metadata, or not | |

Delivery guarantees, timing and metadata hiding are tags: properties declared about a channel.

Metadata hiding is always with respect to the initiator: the sender, or the side that connects on a stream. The responder is always identified, by its peer ID or its address.

An unlinkable channel used for one message at a time yields unlinkable messages, with caveats. For example, an implementation that reuses circuits can leak timing metadata.

Every message type states explicitly which channels are appropriate for it. Two are specified so far:

| Messages | Direction | Delivery mode | Unlinkability | Delivery | Metadata hiding | Authentication |
| --- | --- | --- | --- | --- | --- | --- |
| [Transaction construction](#transaction-construction), semi-honest and Byzantine | send | broadcast | per message | reliable | required | — |
| [Interactive payments](#interactive-payments) | send and receive | peer | either | reliable | — | the payer authenticates the payee; the payee may or may not authenticate the payer |

Open questions:

- What do gossip, set and public gossip messages require of their channels?
- What do transaction construction messages require in the honest setting?

## Peer introduction

Honest and semi-honest settings only.

A user adds a peer ID out of band, with one of four trust levels:

| Trust level | Meaning |
| --- | --- |
| self | the user's own devices |
| trusted | trusted with privacy and liveness, e.g. in the same organization |
| semi-trusted | trusted with liveness |
| untrusted | the peer ID is stored and labeled, but not used |

Open questions:

- Should there be an introducer role, for self, trusted and semi-trusted peers, that may add peers at or below its own trust level?

## Gossip

Gossip always happens within a namespace, also called a topic.

Some namespaces are ephemeral. Their name is derived from a shared secret using a tagged hash. Some are well known, such as the version 1 public order book. Co-spend proposals are namespaced by a Bitcoin block hash. If an object's ID is derived from a namespace that includes a block hash, the ID can be short.

### Minimal gossip

These three messages suffice in the honest setting:

| Message | Contents | Notes |
| --- | --- | --- |
| announce | object hash | throttled, or suppressed by [set reconciliation](#set-reconciliation) |
| pull | object hash | requests an announced object |
| push | object | solicited: answers a pull |

🤖 Small messages are pushed eagerly to neighbors. A block is pushed as just its header, expecting the receiver to already know its Merkle tree.

🤖 After an anonymous submission enters the broadcast domain, peers disseminate it by gossip or set reconciliation. Anonymous submission does not replace dissemination.

### Unsolicited push

The semi-honest and Byzantine settings add one message:

| Message | Contents | Notes |
| --- | --- | --- |
| push (unsolicited) | object | used for anonymous broadcast |

A peer receiving a new object by unsolicited push forwards it by push to one randomly selected peer, and announces it to its other peers.

Open questions:

- How to scope ephemeral namespaces: by shard, by time, or by number of messages.

## Sets

Every message carries a state commitment. It includes the Merkle roots of the sender's mutable sets, its height and its set sizes.

### Immutable sets

An immutable set is referenced by its Merkle root. Sets are sparse Merkle trees, in the style of Libra's. A block commits to two immutable sets: its parents and its messages.

### Mutable sets

A mutable set is tracked as a sequence of Merkle roots. A peer has these:

| Set | Monotone |
| --- | --- |
| roots: the highest blocks, and the messages in no block | its closure is; the set itself is not |
| all blocks known to the peer | yes |
| blocks known to the peer at a given height | yes |
| all messages in blocks known to the peer | yes |

Fetching an ever-growing collection of sets is a resource exhaustion risk. Blocks are needed for progress, and are rate limited by cordiality. A dishonest majority can still flood.

### Set listing

| Message | Contents | Reply |
| --- | --- | --- |
| pull | Merkle root | its preimage |
| list | Merkle root | all of its leaves |

Leaves here are hashes, not preimages. Listing all leaves lets the receiver recompute the root.

### Set reconciliation

Two methods are candidates:

- **Range based.** List to a given depth, with clamping.
- **RIBLT.** A stream of rateless coded symbols for a set.

For mutable sets, randomize the hash and restart the stream on each new item. Reply to a range based request with the children, then stream RIBLT data.

The RIBLT cells need a multiset hash. Elliptic curve multiset hash (ECMH) candidates are:

- GLS254;
- a GLS254 analogue with m = 61 or m = 67, where complete formulae should hold;
- the curve25519 ECMH in fastcrypto;
- secp256k1.

Open questions:

- Can only the latest root of each mutable set be queried?
- Should listing to a given depth return the intermediate nodes?
- Should a range based reply jump ahead, up to some listing size, instead of returning only the children? How does range based reconciliation apply to mutable sets?
- Is range based reconciliation only for immutable sets, or throttled for mutable ones?
- Should immutable sets use a hybrid, interspersing RIBLT with range based reconciliation?
- Can reconciliation data be carried in padding and in announce messages?

## Public gossip

Public gossip uses a well known namespace. These objects form the order book for [coalition formation](coalition_formation.md).

| Object | Contents | Flood protection |
| --- | --- | --- |
| ownership proof | BIP 322 proof for a UTXO, committing to its online key, a validity interval and a block hash | proof hash below a threshold; replaces higher hashes for the same UTXO |
| UTXO directory entry | ownership proof, prevout or previous transaction, listen advertisements | — |
| listen advertisement | channel to reach the owner, constraints on proposals, willingness to be a validator, signed by the online key | signature hash, as for ownership proofs |
| co-spend proposal, unanimously accepted | see [negotiation](#negotiation) | one MuSig2 signature per proposal |
| co-spend proposal, partially accepted | opt-in only | time dependent key images |
| coalition proposal | see [negotiation](#negotiation) | signature hash of the aggregator's key |

Willingness to be a validator is one of: demands it, opts in at the aggregator's discretion, or declines.

## Negotiation

Byzantine setting. These messages go over the channel named in the recipient's listen advertisement, or are gossiped as partial proposals where peers opt in.

| Message | From | To | Contents |
| --- | --- | --- | --- |
| co-spend proposal | proposer | each named UTXO owner | outpoints, conditions, ownership proof commitments, one adjustment commitment per UTXO with range proofs, surplus and balance proof, expiry, optional conflict hints, the opening of the recipient's adjustment |
| acceptance | each owner | involved peers | a linkable ring signature by its online key |
| MuSig2 nonces and partial signatures | each owner | involved peers | turn a unanimously accepted proposal into a fully accepted one |
| coalition proposal | aggregator | every implicated owner | fully accepted co-spend proposals, concrete parameters, adjustment vector, protocol version, committed listen advertisements naming the validators |
| coalition acceptance | each owner | involved peers | a signature by its online key |

In the semi-honest setting the ring signatures can be skipped. Owners then negotiate MuSig2 directly.

## Session initialization

| Setting | How a session starts |
| --- | --- |
| honest, semi-honest | a peer invites others to a random gossip topic |
| Byzantine | the gossip topic is the hash of the coalition formation proposal, including secret data encrypted to all participants |

## Transaction construction

These messages are gossiped to the session's topic. Transaction contributions project into unordered PSBT state and combine according to [concurrent PSBT construction](psbt-concurrent.md). In the Byzantine setting, the wire format consists of specified protocol messages, rather than arbitrary PSBTs. Honest and semi-honest construction can tolerate PSBT extensions; extensions in the Byzantine setting must be specified as protocol extensions.

In the semi-honest and Byzantine settings they need a send channel with unlinkable messages, reliable delivery and broadcast addressing. Outputs in particular must always be message-unlinkable and hide metadata.

| Message | Contents | Size | Settings |
| --- | --- | --- | --- |
| initialize | session parameters | — | all |
| add input | input with prevout data | hundreds of bytes | all |
| add output | output with its unique ID | hundreds of bytes | all |
| add fee contribution | explicit fee contribution | tens of bytes | all |
| issue from initial input | validity proof | several KiB | Byzantine |
| issue from auxiliary input | validity proof | several KiB | Byzantine |
| redeem | validity proof | several KiB | Byzantine |
| sign | signatures for one input | tens of bytes, more in the Byzantine setting | all |

### Initialize

Sets up the session parameters. The sort seed is the transcript hash: the Merkle set commitment of the accepted construction messages at the agreed state before signing, including the applicable proofs. Later input signatures and acknowledgement-only blocks do not change this seed. Concurrent PSBT construction allows this by setting `PSBT_GLOBAL_SORT_DETERMINISTIC` and leaving `PSBT_GLOBAL_SORT_SEED` unset, so each replica supplies the seed when it orders the transaction.

### Add input

An input map with its prevout data. In the Byzantine setting, initial inputs are named by the coalition formation proposal, so only auxiliary inputs carry prevout data. The message also carries:

- an ownership proof committing to an online key;
- a signature by that online key on the message, committing to the session ID or gossip topic.

### Add output

An output contribution, which projects into a PSBT output map. Its unique ID becomes `PSBT_OUT_UNIQUE_ID`, so adding it twice is idempotent, while two equal outputs added separately stay distinct.

🤖 In the optimistic phases, each admitted output has an amount of at least 1 sat, as required by the [construction rules](transaction-construction.md#validity-proofs).

### Add fee contribution

A 16 byte unique ID and an amount, which project into a `PSBT_GLOBAL_EXPLICIT_FEE_CONTRIBUTION` entry. Fee contributions let peers account for fees exactly.

🤖 In the optimistic phases, each admitted fee contribution accounts for at least 1 sat. The overflow signal has the separate meaning described [below](#phase-change-signals).

### Issue and redeem

Byzantine setting only. These messages carry validity proofs. Issuance is from initial inputs or from auxiliary inputs. Their contents depend on the validity proof construction, which is specified separately.

### Sign

The signer first converts the PSBT to an ordered one, then signs with `SIGHASH_ALL`. A signature is tens of bytes. In the Byzantine setting the message can be larger, bounded by the size of the input's ownership proof.

Signers differ in how they can be used:

| Signer | Behavior |
| --- | --- |
| hot key | signs automatically, any number of times |
| manual | the user approves each signature |
| limited | e.g. a hardware security module, or a virtual one |

## Interactive payments

Messages to a designated peer, the counterparty of a payment:

| Message | From | To | Meaning |
| --- | --- | --- | --- |
| grant | payer | payee | grants n sats of the payer's funds to the payee |
| confirm | payee | payer | confirms the committed state the payer's signature depends on |

The [concurrent PSBT specification](psbt-concurrent.md#confirmation-of-successful-payment-prior-to-signing) defines what is confirmed and in what order, including how cycles are broken by net receivers. It is concerned with state only. These messages carry that state between the counterparties.

These messages need send and receive channels with reliable delivery and peer addressing. They may be linkable or unlinkable. The payer must authenticate the payee. Whether the payee authenticates the payer depends on the payment; game theory suggests it shouldn't.

Interactive payments belong to the honest or semi-honest threat model, not the Byzantine one. They can still take place within a broader Byzantine session.

## Blocks

Blocks provide consistency and synchronization, in the style of a blocklace. They are used in the semi-honest and Byzantine settings.

A block contains:

- the Merkle set commitment of its parent blocks;
- the Merkle set commitment of the gossiped transaction construction messages it includes;
- its parent block by the same node;
- the nonce point R its successor will be signed with.

A block is signed with the nonce point committed in its own-node parent.

| Setting | Signing key |
| --- | --- |
| Byzantine | the UTXO's online key |
| semi-honest | an ephemeral key, for simplicity, though the model doesn't need it |

### Phase change signals

Blocks also signal phase changes:

| Signal | Effect |
| --- | --- |
| inputs fixed | clears the inputs modifiable flag |
| overflow | acts as a single fee contribution with ID "" and amount `MAX_MONEY`, the top of the lattice |
| outputs fixed | clears the outputs modifiable flag and sorts the transaction |
| initial input issuance | issuance from initial inputs |
| auxiliary input issuance | issuance from auxiliary inputs |
| outputs proven | all outputs are proven, and invalid outputs pruned |

Open questions:

- In the semi-honest setting, can additional validators just join? If not, how is initialization synchronized?
