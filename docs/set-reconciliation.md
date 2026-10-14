---
type: Specification
title: Peer set reconciliation
description: Requesting hash preimages, naive reconciliation, unordered sets, and range and rateless reconciliation as optimizations of the same mechanism.
status: draft
stale_after: 2027-04-15T00:00:00Z
---

<!-- cspell:words Alizadeh Aljoscha Amsden ECMH getdata Gilad iblt Kleppmann mathbin Minisketch multiset pinsketch RBSR RIBLT Sourav Yossi Zhuolun -->

# 🤖 Peer set reconciliation

## Push gossip

[Epidemic gossip](channels.md#dissemination-methods) disseminates data by pushing it: a peer that learns of a new message passes it on to its neighbors, and they pass it on in turn. Every peer eventually receives every message. Until then, a peer waits for messages to be pushed to it.

🤖 Small messages are pushed eagerly to neighbors. A block is pushed as just its header, expecting the receiver to already know its Merkle tree.

## Requesting hash preimages

A block refers to its parents and to the messages it includes by hash, and a set of messages is committed to by a Merkle root. A peer can therefore hold a root without knowing the leaves it commits to. Such a peer wants to pull the missing leaves, not wait for someone to push them.

## Naive reconciliation

Pulling works because honest peers follow two rules:

* An honest peer never sends a message containing hashes for which it has not validated the preimages.
* An honest peer responds to a pull for a hash with its preimage.

This is analogous to `getdata` in Bitcoin's peer to peer protocol. A peer that receives a hash can pull its preimage from the sender. It repeats this for the hashes in the obtained message, until it reaches messages it already has. This is enough for the naive reconciliation of Byzantine Eventual Consistency (BEC).[^bec] In the block DAG, the hashes are a block's parents and included messages. The number of round trips can be up to the length of the longest path of missing messages. Kleppmann and Howard reduce it using Bloom filters; that optimization is not needed.

Reconciliation uses [peer to peer channels](transport-interfaces.md), independently of whether delivery uses a live connection or store-and-forward messages. Exchanges identify their root and scope so delayed replies remain interpretable after a newer advertisement or transport rebuild. A reconciliation stream is a sequence of messages, not a requirement for a connection-based byte stream. Neighbor identity and acknowledged knowledge belong to peer management; they need not expire with the transport connection.

## Sparse Merkle sets

Sets are represented by sparse Merkle trees keyed by the cryptographic hash of each referenced object. The key is its set identity; repeated insertion is idempotent. The tree commits to an unordered set, independently of arrival order or the peer that supplied an element.

Empty subtrees have a canonical representation. A singleton subtree is represented by its leaf rather than a chain of otherwise empty internal nodes, following the compression described for Libra's sparse Merkle trees.[^libra] Leaf, internal-node and empty-node encodings must be unambiguous and domain separated. The exact encoding and hash function are pending choices.

Every message sent to a neighbor carries the relevant set root. An advertised root adds that set to the reconciliation allow-list for that neighbor. Reconciliation requests are scoped to such an advertised set, or to a subtree established during its reconciliation. Advertising a root authorizes reconciliation; it does not establish that the contents are valid or available.

Immutable sets coexist with changing inventory sets. For example, a block DAG can advertise its current frontier, unincorporated contributions or all known blocks; the frontier can change while its causal closure grows monotonically. An inventory advertisement identifies the kind of set as well as its current root; the retention policy for superseded inventory roots remains to be specified.

An exchange identifies an immutable root. Later advertisements can introduce newer roots without changing the meaning of an exchange already in flight. Obtained messages are shared across exchanges and neighbors through the local content-addressed inventory.

## Unordered sets

The same mechanism can exchange the Merkle roots of messages that are not yet ordered in blocks. Such sets have no consistency guarantees: two peers' sets can differ, and nothing says they should converge at any particular point.

* In the peer to group context, this is analogous to a mempool: contributions to a transaction construction session that no block includes yet.
* In the peer to world context, this is the order book of coalition formation: listen advertisements, co-spend proposals, and their ownership proofs.

Peer to world does not rely on BEC or on blocks. Peers just exchange Merkle trees with adjacent peers. The coalition formation protocol decides which objects are valid, which are kept, and which are eligible for negotiation.

The [DAG's equivocation mechanism](block-dag.md#nonce-commitments-and-compact-equivocation-evidence) exposes a validator's BIP-322-endorsed online private key. Gossiping this scalar and its endorsement evidence lets other peers verify the fraud proof and ban the associated coin from coalition formation without obtaining the equivocated blocks. Reconciliation disseminates the evidence; the consuming protocol validates it and applies the admission policy.

## Quiescence before block authoring

🤖 Set reconciliation is an input to block publication: a validator waits for its neighbors' sets to converge before authoring its next block, whichever reconciliation algorithm is used. The rule and its purpose, avoiding needless block DAG waves, are described under [block publication and quiescence](optimistic-track.md#block-publication-and-quiescence) in the optimistic track.

## Optimizations

Range-based set reconciliation (RBSR), and RBSR combined with rateless invertible Bloom lookup tables (RIBLT), come naturally from the same mechanism. Instead of exchanging a root and pulling every leaf, two peers compare subtrees, and pull only where their sets differ. We call the combination **hybrid recursive/rateless set reconciliation**: RBSR recursively controls the scope of the exchange; optional `rateless<iblt>` and `rateless<pinsketch>` streams can use available bandwidth while range replies are in flight. These algorithms target different device and network tradeoffs; an optimal switching policy has not yet been established.

### Mutual and asymmetric knowledge

Each peer has a local inventory and neighbor-specific evidence about the neighbor's inventory. A root identifies a set without establishing that the receiver possesses its elements. The receiver may know only the commitment, some leaves, or the complete set. Missing identifiers and missing message preimages are distinct: learning a leaf hash can identify a subsequent content request.

Mutual knowledge here means an operationally established shared subset, not epistemic common knowledge. A jointly identified baseline can be omitted from both sides of a reconciliation exchange. Asymmetric knowledge also helps: a peer can request particular missing objects or avoid resending acknowledged objects without first establishing identical inventories. Mere absence from an advertisement need not establish that the neighbor lacks an object.

### Range reconciliation and streaming

The first optimization direction is range-based set reconciliation in the style of Meyer and Scherer.[^rbsr] It is not needed for the base functionality. A sparse-tree prefix identifies a key range. Equal subtree commitments require no further exchange; unequal ranges are subdivided or resolved by transmitting leaves.

A subtree advertisement includes its key prefix as well as its root. The receiver can compare it directly with the corresponding position in its local tree, without first requesting every intervening level. The sender may skip levels and stream intermediate subtrees of comparable population, reducing sequential round trips. Population estimates used for scheduling are not substitutes for checking the committed set.

Each channel independently randomizes the order of streamed subtrees, for example using an ephemeral channel secret. If several neighbors possess the same set, their different schedules tend to expose different missing ranges first. Recovered objects immediately update the common inventory and can satisfy work pending on other channels. This reduces duplicate transfers in expectation; it does not guarantee disjoint work.

Restricting comparisons to sparse-tree prefixes is a specialization of the range approach. It does not automatically inherit bounds for arbitrary equal-population range partitions; the cost of representing such partitions by multiple prefixes requires evaluation.

The range protocol remains usable without a homomorphic fingerprint. Rateless reconciliation, described below, has additional requirements.

### Shared-knowledge baselines

Acknowledged set commitments provide evidence of data already shared with a neighbor. Application-level references can compactly supply further evidence; a block DAG is one such application. Let $S$ and $T$ be the two sets being reconciled and let $K$ be a mutually identified subset of their intersection. Then

$$
(S\setminus K)\mathbin{\triangle}(T\setminus K)=S\mathbin{\triangle}T.
$$

Removing $K$ reduces the number of elements to encode without changing the difference to recover. This is useful even when the residual elements are widely scattered across the key space.

In either setting, acknowledged inventory roots and object receipts can establish shared knowledge. In the DAG setting, additional neighbor-specific information is available:

* A neighbor's validated blocks identify payloads and causal ancestors that the local node has also obtained.
* Blocks from that neighbor which build upon local blocks acknowledge the corresponding causal closure.
* The local transmission log identifies objects already sent to that neighbor. Until receipt is established, this is speculative knowledge rather than an acknowledged common baseline.

Baseline references must determine the same $K$ at both endpoints. A local belief about a neighbor's inventory is insufficient. A baseline can be named by agreed DAG frontiers; its use is restricted to elements common to the sets in the current exchange. Knowing an object does not imply that it belongs to every advertised block payload. For cumulative causal inventories, a shared ancestral frontier supplies this subset directly.

The original root remains the target commitment. Residual reconciliation need not create a separate authenticated tree for each neighbor. PinSketch subtraction, for example, can remove a common baseline algebraically, whereas range traversal can skip established shared subtrees or account for known leaves.

A Byzantine neighbor may acknowledge data it does not possess. Such an acknowledgement does not permit either endpoint to accept unchecked contents. Missing data can still be requested, and the exchange can fall back to a smaller baseline or none. Baseline agreement and fallback messages remain to be encoded.

### Hybrid recursive/rateless set reconciliation

The second optimization direction combines range reconciliation with rateless streams.

An advertised root may be followed immediately by a rateless reconciliation stream for that set. This uses the time before a range-based reply arrives. The `rateless<iblt>` candidate uses an elliptic-curve multiset hash (ECMH) for its homomorphic cell checks, together with a channel-specific sampling schedule.[^riblt] The ECMH and adversarial-set adaptations are distinct from the published RIBLT construction and require their own analysis.[^ephemeral-ecmh]

A range reply narrowing the work to subsets is an **unconditional stop signal** for the parent stream. Stopping does not depend on whether its decoder has completed. Further optional streams are scoped to the unresolved subsets. The exchange identifies the root, prefix and stream parameters so that delayed parent cells cannot be mistaken for child cells.

Streams with different sampling parameters have separate decoder state. Recovered objects can be shared across decoders; differently parameterized cells cannot be pooled as one sketch. Previously received cells may be retained locally, but stopping a stream ends further transmission for that scope.

The relevant robustness target includes honest peers reconciling sets whose elements were chosen adversarially by third parties. Channel-specific schedule randomness and ECMH checks address different concerns: deliberate concentration in the sampling schedule and false cell recovery, respectively. Neither compels a malicious neighbor to send data. Parameter selection and bounds on decoding work remain open.

### Sparse differences and `rateless<pinsketch>`

A small difference spread throughout a large set can require many tree comparisons. PinSketch is a candidate for resolving such ranges directly. A capacity-$c$ sketch of $b$-bit nonzero field elements occupies $bc$ bits and can recover a symmetric difference of at most $c$ elements. Sketches combine by XOR.[^minisketch]

Capacity depends on the difference size, while construction work also depends on the population being encoded. Straightforward construction over $N$ elements costs $O(Nc)$ field operations. Conventional decoding has quadratic scaling in the supported difference size. A shared-knowledge baseline reduces $N$ without reducing the required capacity for the same difference.

Two extensions are under evaluation:

| Variant | Operation | Tradeoff |
| --- | --- | --- |
| Additional syndromes | Extend the PinSketch for the same range without retransmitting earlier syndromes. | Increasing capacity increases computation; reuse of failed decoding work requires implementation support. |
| Small PinSketch cells | Use small-capacity sketches with a rateless sampling sequence, allowing a cell to recover several residual elements. | Bounds local decoding work, but changes the peeling algorithm and requires new performance and robustness analysis. |

In either case, a narrowing range reply stops transmission for the parent scope. Computational budgets can trigger subdivision rather than further sketch expansion. Small fixed-capacity sketches cached at selected tree nodes can reduce repeated encoding work, at a storage and update cost. Channel-dependent sampling limits reuse of cached sampled sketches.

Decoding beyond capacity can return a false candidate rather than an explicit failure. Sketch results are provisional until checked against the committed data. A sampled-cell construction must account for false recovery before propagating it through peeling; checking only the final root detects failure but does not bound wasted decoding work. Mapping message hashes into smaller field elements also requires collision handling. These details remain part of the sketch profile, not changes to the DAG semantics.

### Relation to asynchronous data dissemination

Asynchronous Data Dissemination (ADD) distributes a common message $M$ from at least $f+1$ honest holders to all honest nodes, with communication $O(n|M|+n^2)$ under $f<n/3$.[^add] It provides a benchmark for distributing transfer work and bounding redundant communication under adversarial requests. Its starting condition differs from reconciliation between peers with overlapping inventories. An ADD-style transfer is a possible alternative for large immutable batches, subject to its holder and fault assumptions; it does not exploit sparse set differences directly.

## Resource bounds and validation

Outstanding neighbor exchanges, speculative decoder work and retained unresolved roots require explicit bounds. An advertised root scopes requests but does not establish that its set is small or admissible. Duplicate data does not earn repeated processing rights. Retrieved contents are checked against commitments; application validity is checked by the consuming protocol.

## Open specification choices

Remaining choices include canonical tree encodings; advertisement scopes and retention; baseline references and fallback; range scheduling; rateless parameters and ECMH checks; field-element mapping and sketch validation; and computational and bandwidth budgets. Measurements should vary set population, symmetric difference, latency, device capability and number of neighbors independently.

The reconciliation mechanism reports completion for a specified scope. Whether that completion permits publishing a block or advancing a phase belongs to the consuming protocol.

## References

[^libra]: Zachary Amsden et al. [The Libra Blockchain](https://sonnino.com/papers/libra.pdf), sparse Merkle tree discussion.

[^bec]: Martin Kleppmann and Heidi Howard. [Byzantine Eventual Consistency and the Fundamental Limits of Peer-to-Peer Databases](https://arxiv.org/abs/2012.00472), §5.

[^rbsr]: Aljoscha Meyer and Konstantin Scherer. [Range-Based Set Reconciliation Without Homomorphic Hashing](https://aljoscha-meyer.de/assets/landing/rbsr_nonhomomorphic.pdf).

[^riblt]: Lei Yang, Yossi Gilad and Mohammad Alizadeh. [Practical Rateless Set Reconciliation](https://arxiv.org/abs/2402.02668).

[^ephemeral-ecmh]: [Ephemeral ECMH](https://nothingmuch.github.io/ephemeral-ecmh/), on whether small elliptic curves can serve as the checksum in rateless set reconciliation, against adversarially chosen items, with a public beacon instead of a shared secret.

[^minisketch]: [Minisketch: an optimized library for BCH-based set reconciliation](https://github.com/bitcoin-core/minisketch), including its mathematical explanation and incremental-decoding discussion.

[^add]: Sourav Das, Zhuolun Xiang and Ling Ren. [Asynchronous Data Dissemination and its Applications](https://eprint.iacr.org/2021/777).
