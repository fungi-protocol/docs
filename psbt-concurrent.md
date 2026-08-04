# Concurrent PSBT Construction

## Abstract

New fields and rules for combining PSBTs in a distributed setting. This provides an alternative to the BIP 370 constructor role that is less sensitive to order of operations and therefore more amenable to concurrency, which reduces the coordination required for collaborative transaction construction.

## Motivation

BIP 174 defines *Combiner* functionality. Its purpose is to integrate information add by either the *Updater* or *Signer* roles to divergent copies of a PSBT. According to the specification the combiner is intended for for PSBTs whose underlying unsigned transactions are identical, i.e. it is restricted to the *Updater* and *Signer* roles.

BIP 370 introduced a *Constructor* role, which allows signalling that the inputs or outputs of a PSBT are modifiable. Arbitrary mutation of the inputs and outputs is then allowed, but this assumes such state updates are done sequentially. The combiner role is mostly unchanged in BIP 370, and is restricted to only allow combining fields of PSBTs which spend and create the same outputs, and in the same order. This facilitates aggregating signatures from multiple parties in any order, but has limited usefulness during the construction of the PSBT.

In a distributed system it is easier to deliver messages without guaranteeing the order of delivery is consistent across nodes. Agreement on the set of outputs to spend and a set of outputs to create is sufficient for constructing a transaction, it isn't necessary to agree on the order in which they were added. This document defines an order insensitive merging procedure which generalizes the *Combiner* role to non-identical modifiable PSBTs which may still overlap in some of their data. To terminate concurrent transaction construction, a consistent ordering procedure is also defined for producing a a consistent PSBT which can subsequently be manipulated using the normal BIP 174 roles.

## Specification

TODO diagram for the combined state machine, indicate when downconversion (to v2 or v0) can happen

    creator -> constructor<modifiable, unordered> -> constructor<modifiable> (bip 370) -> updater -> signer -> combiner -> finalizer -> extractor

TODO discuss scrubbing after signer and before combiner

The new field types for distributed PSBT construction are as follows:

### New global types

| Name | `keytype` | `keydata` | `keydata` Description | `valuedata` | `valuedata` Description |
| --- | --- | --- | --- | --- | --- |
| Transaction Unordered Flag | `PSBT_GLOBAL_TX_UNORDERED = TBD` | None | No key data | `<8-bit uint>` | If present, must be set to a value `0x03` to indicate inputs and outputs are unordered. |
| Sort Seed | `PSBT_GLOBAL_SORT_SEED = TBD` | None | No key data | `<bytes globalseed>` | Random seed used to derive deterministic sort keys when explicit per-map sort keys are absent. |
| Deterministic Sort Flag | `PSBT_GLOBAL_SORT_DETERMINISTIC = TBD` | None | No key data | `<8-bit uint>` | A value of `0x01` indicates sort keys must be deterministically derived and explicit `PSBT_IN_SORT_KEY` / `PSBT_OUT_SORT_KEY` fields are disallowed. A value of `0x00` indicates sort keys are required and `PSBT_GLOBAL_SORT_SEED` is disallowed. |
| Removed Input | `PSBT_GLOBAL_REMOVED_INPUT = TBD` | `<bytes input unique id>` | `PSBT_IN_UNIQUE_ID`  of an input removed from the logical input set. | None | No value data. |
| Removed Output | `PSBT_GLOBAL_REMOVED_OUTPUT = TBD` | `<bytes output unique id>` | `PSBT_OUT_UNIQUE_ID` removed from the logical output set. | None | No value data. |

### New per-input types

| Name | `keytype` | `keydata` | `keydata` Description | `valuedata` | `valuedata` Description |
| --- | --- | --- | --- | --- | --- |
| Input Sort Key | `PSBT_IN_SORT_KEY = TBD` | None | No key data | `<bytes sort key>` | Arbitrary lexicographically comparable value used to order inputs. |
| Input Unique ID | `PSBT_IN_UNIQUE_ID = TBD` | None | No key data | `<bytes unique id>` | Optional unique suffix for outpoint identity, used for input removal extensions. |

### New per-output types

| Name | `keytype` | `keydata` | `keydata` Description | `valuedata` | `valuedata` Description |
| --- | --- | --- | --- | --- | --- |
| Output Unique ID | `PSBT_OUT_UNIQUE_ID = TBD` | None | No key data | `<bytes unique id>` | Universally unique identifier for output map identity under unordered output semantics. |
| Output Sort Key | `PSBT_OUT_SORT_KEY = TBD` | None | No key data | `<bytes sort key>` | Arbitrary lexicographically comparable value used to order outputs when transitioning from unordered to ordered mode. |

### PSBT identity and transaction effects

The BIP 174 *Combiner* role specifies how to merge diverging copies of the same PSBT. PSBTs are considered "the same", by identifying them based on the unsigned transaction. Two PSBTs with the same unsigned transaction but potentially different key value pairs are considered two versions of the same PSBT.

BIP 370 introduces the notion of a [unique ID](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki#user-content-Unique_Identification) which is computed as a hash that commits to UTXOs being spent and the new outputs being created, thereby ensuring PSBTs with the same ID have the same structure, but abstracting away some details of the transaction, thereby introducing a notion of equivalence that is a bit more general.

The effects of a transaction on the distribution of money are determined by its effects the UTXO set: which outputs does it spend and create. However, with regards to money changing hands, we would like to treat equivalent outputs as interchangeable by disregarding the specific outpoints by which specific coins are identified.

Both notions of identity ensure that PSBTs with the same ID have the same effects, but it is not true that PSBTs with the same effects will have the same ID, since depends on the specific order of the inputs and outputs, among other things. By abstracting over these details we obtain a more general notion of PSBT identity than in BIP 370. The details of how to compute this ID are [provided below](#unique-identifiers).

### Combiner role and transaction effects

The BIP 174 *Combiner* role requires that the PSBTs have the same identity. In order to relax this constraint and allow the *Combiner* role to be used in conjunction with (a more general notion of) the *Constructor* role, the *Combiner* role has to be made more conservative in other regards.

BIP 174 specifies that fields with duplicate keys and more than one distinct value may be combined by [picking one of the values arbitrarily](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki#handling-duplicated-keys). This is safe within the scope of BIP 174 because any inconsistency will only affect the validity of a transaction. In other words, when choosing one value over another for a duplicate field, although signing may fail to produce a valid signature, no money will be lost because if the IDs are the same, the the effects are identical.

This notion of safety can be extend beyond just combining signing related data, so that effects of a transaction formed by combining PSBTs do not depend in any way on the order in which the PSBTs were combined, nor even on combination being done sequentially. Note that this does not require that the effects of the constituent PSBT be identical, only that all of them are combined at some point. More formally, in order to be safe, combining should be monotone in the transaction effects.

Unfortunately choosing between conflicting values arbitrarily does not preserve this notion of safety when merging PSBTs where the inputs or outputs of one PSBT don't correspond to the inputs or outputs which occupy the same positions in the second PSBT. For example, if the first inputs of two PSBTs spend different coins, and one PSBT takes precedence, the input in the other transaction will be omitted. If the `PSBT_IN_PREVIOUS_TXID` field of one PSBT overrides the other but this precedence is reversed for `PSBT_IN_OUTPUT_INDEX`, the one remaining input will be corrupted.

#### `joinpsbts` vs. the Combiner role

Bitcoin Core additionally implements a `joinpsbts` RPC command which does allow merging PSBTs with different identities, so long as their spent output sets are disjoint.

`joinpsbts` is not idempotent with respect to inputs (writing it as $+$, idempotence would mean that $A + A = A$). Attempting to join a PSBT more than once fails closed: if $B$ contains an input, and $A + B$ is defined, then $(A + B) + B$ will fail, because a transaction cannot spend the same coin twice.

`joinpsbts` is also not idempotent with respect to the outputs, but unfortunately also does not fail closed, potentially leading to overspending: if $B$ contains just an output, then $B + B$ will contain two copies of that output.

Although not strictly associative or commutative, due to use of shuffling, in regards to transaction effects it does hold that $(A + B) + C = A + (B + C)$ and that $A + B = B + A$.

#### Strict Combiner

In order for combination being deterministic, idempotent and commutative and associative in regards to transaction effects, when either bits 0 or 1 of `PSBT_GLOBAL_TX_MODIFIABLE` are set, indicating the transaction is modifiable, instead of choosing arbitrarily the strict *Combiner* MUST fail whenever duplicate fields have conflicting (unequal) values.

Exceptions to this are detailed in the next sections, preserving idempotence, commutativity and associativity.

This establishes a more conservative foundation for ensuring that the effects of a transaction formed by combining a set of PSBTs will always be the same regardless how these PSBTs were combined to obtain a complete transaction.

### Unordered input and output sets

Since transaction effects are invariant under permutations of the inputs or outputs, treating the inputs and outputs as unordered sets as opposed to order lists allows safe combining to be defined for PSBTs that are not identical.

To represent this we define a global field `PSBT_GLOBAL_TX_UNORDERED`, indicating whether the order of inputs and outputs should be ignored. The value is an unsigned 8 bit integer and if present must be set to `0x03`, indicating the transaction in unordered.

Rationale: Since there is no known use case that requires input or output to be marked unordered or ordered separately from each other, that is omitted from the spec. The value `0x03` simplifies forward compatibility with any specification that might amend this by allowing either bit to be set independently, so long as it overlaps with this specification when both are set.

If set, the `Has SIGHASH_SINGLE` flag of `PSBT_GLOBAL_TX_MODIFIABLE` must not be set. `SIGHASH_SINGLE` inputs [MUST not be used](#divergence-and-sighash-flags) in unordered transactions.

Unordered PSBTs MUST be shuffled prior to reserialization. This is easily accomplished by storing them in randomized hashmaps, keyed by their unique identifiers as defined below. If all inputs and outputs have [sort keys](#ordering-inputs-and-outputs), the key based ordering may be used instead of shuffling.

[fn:Join is implicitly defined on equivalence class of all permutations of inputs/outputs, but the PSBT contents is a random representative.

Rationale: Not shuffling presents a privacy hazard, leaking information about the sequence of actions leading to a transaction's construction. When a transaction is unordered, shuffling by definition doesn't change its meaning, but ensures the incidental order can't accidentally be relied upon.

#### Combining PSBTs with different identities

When `PSBT_GLOBAL_TX_UNORDERED` is set, the input or output maps are no longer distinguished by their index, but instead by a unique identifier defined for each input or output.

Inputs or outputs with identical unique IDs (those which are present in both PSBTs) are merged by combining their key-value pairs with the stricter, idempotent combination defined above.

These sets of combined inputs and outputs are then unioned with any inputs or outputs from that have distinct unique identifiers (i.e. are only present in one of the PSBTs, and therefore aren't combined with a counterparts). Distinct identifiers are only allowed if the corresponding `PSBT_GLOBAL_TX_MODIFIABLE` flag is set, because such combinations represent additions of inputs or outputs. If this is not the case but a distinct input or output is present, then combining must fail.

#### Unique identifiers for inputs

Inputs are identified by their outpoint, i.e. the tuple of their `PSBT_IN_PREVIOUS_TXID` and `PSBT_IN_OUTPUT_INDEX`, both of which must be set.

#### Unique identifiers for outputs

Outputs are identified by a new `PSBT_OUT_UNIQUE_ID` field, which must be universally unique (e.g. 16 bytes of randomness).

This ensures that repeated addition of the same output is idempotent, but that if two different distributed constructors both attempt to add an identical output (same `PSBT_OUT_VALUE` and `PSBT_OUT_SCRIPT`), that will still result in two copies of the output as intended. This is important because a transaction with only a single copy will appear correct but end up losing the value of all missing copies to mining fees.

Outputs with an identical `PSBT_OUT_SCRIPT` can be merged, and their values summed together after `PSBT_GLOBAL_TX_UNORDERED` is cleared and an order is determined, using BIP 370 construction rules. See the next section on ordering.

### Ordering inputs and ouputs

- TODO: unique ID can be derived by sorting even if sort key is empty, but txn finalization must not be unless all sort keys are provided explicitly (regardless of DETERMINISTIC)
- add section for unique ID derivation a la BIP 370

Clearing the `PSBT_GLOBAL_TX_UNORDERED` field indicates the order of the inputs and outputs. Due to the shuffling requirement, the given order will in general not be consistent across replicas if this is done without determining an order, resulting in diverging unsigned transactions.

For consistent ordering we define `PSBT_IN_SORT_KEY` and `PSBT_OUT_SORT_KEY` fields for inputs and outputs respectively, that may include up to 32 bytes of arbitrary data, used as a sort key for lexicographical sorting.

If the global field `PSBT_GLOBAL_SORT_DETERMINISTIC` is set (unsigned 8 bit integer) to `0x01`, then sort keys MUST NOT be set, and `PSBT_GLOBAL_SORT_SEED` MUST be set and contain at least 128 bits of randomness.

If `PSBT_GLOBAL_SORT_DETERMINISTIC` is set to `0x00`, explicit sort keys are required to be set and used prior to clearing the `PSBT_GLOBAL_TX_UNORDERED` field and fixing the transaction order.

If any `PSBT_IN_SORT_KEY` and `PSBT_OUT_SORT_KEY` are omitted, the global `PSBT_GLOBAL_SORT_SEED` field is set, and `PSBT_GLOBAL_SORT_DETERMINISTIC` is either omitted or set to `0x01`, the sort keys are derived deterministically. A missing `PSBT_IN_SORT_KEY` is derived as `H(PSBT_GLOBAL_SORT_SEED || PSBT_IN_PREVIOUS_TXID || PSBT_IN_OUTPUT_INDEX)` and `PSBT_OUT_SORT_KEY` as `H(PSBT_GLOBAL_SORT_SEED || PSBT_OUT_UNIQUE_ID)`, where `H_s` is a BIP 341 style tagged hash, with the tag preimage being `BIP ???? deterministic ordering` (TODO pick a real domain separator).

If any sort key is missing, ordering can only proceed after `PSBT_GLOBAL_SORT_SEED` is set.

A *Creator* creating an unordered transaction SHOULD set `PSBT_GLOBAL_SORT_DETERMINISTIC` to enure consistent ordering rules are enforced.

For sufficiently large transactions the ordering itself (and therefore the per input signatures) is a cryptographically binding commitment to the `PSBT_GLOBAL_SORT_SEED` value. This is because the entropy of the ordering of $n$ elements is $log_2(n!)$. For reference, $\log_2(35!) > 128$, $\log_2(25!) > 80$, and $\log_2(15!) > 40$.

This can provides additional integrity to a collaborative transaction construction protocol, since [`SIGHASH_ALL`](#divergence-and-sighash-flags) signatures must agree on the ordering.

In applications where this is desirable, the *Creator* should only set `PSBT_GLOBAL_SORT_DETERMINISTIC` to `0x01`, and leave `PSBT_GLOBAL_SORT_SEED` unset. Each replica will locally provide a value for `PSBT_GLOBAL_SORT_SEED` just in time, as a commitment to protocol transcript (e.g. the root hash of a Merkle set of protocol messages).

If that is not the case, the *Creator* should initialize `PSBT_GLOBAL_SORT_SEED` with sufficient randomness thereby ensure some order can always be determined, or set `PSBT_GLOBAL_SORT_DETERMINISTIC` to `0x00` to indicate explicit sort keys are required..

TODO global sort seed || hash of fee contributions or expect application to commit to that in transcript if appropriate?

TODO: Rationale for allowing explicit sort key: lightning interactive-tx `serial_id` field. should always use odd parity form, encoded in network order so that lexicographical sorting works the same as the interactive-tx sorting rule.

### Unique identification of unordered PSBTs

In order to derive unique IDs as in BIP 370 for unordered transactions, the `PSBT_GLOBAL_SORT_SEED` and `PSBT_IN_SORT_KEY` and `PSBT_OUT_SORT_KEY` fields are cleared, and then the ordering procedure of the previous section is used without the restriction of a non-empty `PSBT_GLOBAL_SORT_SEED` (sorting with an empty seed).

TODO: domain separation from PSBT v2, it doesn't make sense to treat an ordered BIP 370 PSBT as the same PSBT even if it agrees on its content when it doesn't agree that the order is meaningless. how to do this? hashing output unique IDs of outputs is insufficient for domain separation of input only partially constructed PSBTs, but maybe that's OK.

### Divergence and SIGHASH flags

Signers MUST sign only using `SIGHASH_ALL`.

If `SIGHASH_ANYONECANPAY` or `SIGHASH_NONE` is used by a signer, the signature is valid for an (ill defined) equivalence class of transactions, with non-equivalent transaction effects.

At minimum any such signature could lead to txid malleability, and so is not composable with any protocol that requires pre-signed descendant transactions.

Furthermore, members of this equivalence class of transactions may differ substantially in their effects, potentially leading to loss of funds, not only due to byzantine faults but even omission faults. To ensure undesired transactions are not inadvertantly authorized, the full output list should always be comitted to using `SIGHASH_ALL`.

Rationale: No known use cases for such flags in true multiparty transactions (i.e. three or more parties). If necessary, a carve out can be specified in a separate document (e.g. for kickstarter-style crowdfunding with `SIGHASH_ANYONECANPAY|SIGHASH_ALL` signing).

### Confirmation of successful payment prior to signing

Parties which neither send nor receive payments within a transaction can safely sign so long as all of their intended outputs are covered by the input signature. This may require signing more than once if some messages are delayed, but TODO see also termination via explicit fee contributions.

If there is any net transfer between the parties, it is insufficient for a sender (any party that makes an outgoing payment to another party within the transaction regardless of their net send/receive balance) to rely only on the signature comitting to the outputs they added, because some of their funds will be used by other parties and their actions need to have been registered as well.

Before signing, every sender must wait until it has positive confirmation of the PSBT's unique ID (which commits to the full output set) from every one of its receivers, and that in every case the confirmed ID matches the one they derive locally.

Every recevier whose net balance is non-negative (they may be a sender too but they receive at least as much as they send) can confirm the unique PSBT ID to their respective senders output set contains all of their added outputs.

Every receiver whose balance is net negative (they send more than they receive) must wait for confirmation from all receivers for whom it is a sender before it confirms the unique ID to the senders for whom it is a receiver.

If there is a cyclic payment graph, for example Alice pays Bob, Bob pays Carol, and Carol pays Alice, net positive receivers can safely initiate confirmations, breaking the circular dependency, because senders will sign will only occur after all receivers have confirmed and if all net positive receivers have confirmed then all funds are accounted for. At least one such node must exist in every cyclic payment structure, since the sum of the payments along a cycle will be 0.

If there is any mismatch in the confirmations, either the receiver or the sender has not yet received the full message set. If a receiver learns of an additional input or output after previously confirming, they must confirm the new unique ID which incorporates this additional data. If a sender learns of an additional input or output, they can derive a new unique ID, and stop waiting if this matches all of their receivers' confirmations.

Such a confirmation mechanism does not require an agreement or consensus mechanism, only eventual consistency. If messages are guaranteed to be delivered eventually then every receiver will eventually confirm a consistent least upper bound.

TODO sender/receiver examples, including an example with a receiver that contributes no inputs, only outputs

TODO net-sender, net-receiver, explain in terms of breaking cyclic graph to a tree with net-receivers at the leaves, propagate confirmation up the chain.

### Input or output removal (optional)

As in BIP 174, the combination of several PSBTs must contain all the key-value pairs from each of the input PSBTs.

If support for removal of inputs and outputs is needed, two global fields `PSBT_GLOBAL_REMOVED_INPUT` and `PSBT_GLOBAL_REMOVED_OUTPUT` can be used to represent a [two phase set](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type#2P-Set_(Two-Phase_Set)) by specifying the inputs or outputs to be removed in the keydata. Inputs or outputs whose unique IDs are specified must be pruned from the input or output.

Because inputs are identified by outpoint, an input spending the same coin as an input whose outpoint is in the set of removed inputs can't normally be added. Therefore we introduce an optional `PSBT_IN_UNIQUE_ID` field, whose value (if provided) is appended to the outpoint.

Support for removal is entirely optional. Implementations may explicitly fail when combining with a PSBT that sets either `PSBT_GLOBAL_REMOVED_INPUT` or `PSBT_GLOBAL_REMOVED_OUTPUT`, but completely ignoring these fields is fail safe.

Assuming [`SIGHASH_ALL` is used](#divergence-and-sighash-flags), it's sufficient to simply rely on the signature hashing. If an output was removed, a peer which does not implement removal it will diverge from those that do, and therefore produce a signature that will not be valid for the transaction supporting peers will produce and subsequently sign, and vice versa, ensuring that neither transaction is valid.

This optionality extends the `PSBT_IN_UNIQUE_ID` field, a removal and re-insertion with incompatible data will either cause combination to fail due to a mismatch or succeed by ignoring the removal and treating the insertion as idempotent, but otherwise diverge.

While this would allow limited interoperability among clients, that is not reccomended, and is described as an argument for the safety of omitting any removal related functionality. Implementations which omit removal functionality SHOULD fail or at least warn if combining a PSBT that signals removal.

TODO: while combine is monotone of data / PSBT fields including removals, it is no longer monotone in transaction effects. This does not present a safety issue if [only `SIGHASH_ALL` is used](#divergence-and-sighash-flags).

Rationale for optionality: not implementing is safe, couldn't find usage of `tx_remove_{input,output}`, non-monotonic state makes termination / limits trickier.

TODO for interactive-tx, set `PSBT_IN_UNIQUE_ID` to odd parity `serial_id`. this makes it possible to support `tx_remove_{input,output}` operations.

### PSBT CRDT (optional)

In some circumstances a conflict free replicated data type (CRDT) can be defined as a subtype of (unordered) PSBTs. In a CRDT, in addition to being idempotent, commutative and associative, combination is additionally [guaranteed to succeed](https://en.wikipedia.org/wiki/Semilattice).

Success here means producing a useful output, which ideally would guarantee a transaction that would be valid if fully signed, which also conforms to standardness policy. This can only be guaranteed under assumptions that must be realized by some additional protocol, beyond the scope of this document.

#### Mutually exclusive inputs

Two `OP_CLTV` encumbered coins, one with a height based and one with a time based `nLocktime` constraint will impose mutually exclusive validity requirements on their spending transactions, and therefore cannot be spent together in the same transaction.

In order to ensure the least upper bound of any two inputs under consideration not only can be defined, but will correspond to a valid transaction, the *Creator* role can restrict the domain of spendable inputs before inputs are added.

TODO `PSBT_GLOBAL_{REQUIRED,MAXIMUM}_{HEIGHT,TIME}_LOCKTIME` height and time separately or just integer range? separately is consistent with other PSBT specs. a single nlocktime interval field with two unsigned integers, required and max-required would make many invalid states unrepresentable, but is more fiddly and unfamiliar.

#### Size Limits

advisory fields: `MAX_WEIGHT_PER_PARTICIPANT`, `MAX_TRANSACTION_WEIGHT` (default 400000?) - determines max number of participants while also signalling size limit is enforced

if every participant effectively restricts the domain by respecting the limit the least upper bound is guaranteed not to exceed the limit making the join valid.

assumes the number of partcipants can be restricted via some external mechanism.

#### Termination

knowing when to proceed to signing

- global fee contribution
  - `PSBT_GLOBAL_EXPLICIT_FEE_CONTRIBUTION`
  - keydata = 16 byte uuid
  - value = u64 amount of funds explicitly contributed as fees
  - needs `PSBT_IN_NON_WITNESS_UTXO` or `PSBT_IN_WITNESS_UTXO` for nominal value
  - effective values/costs would a specific feerate and input size estimation,
    instead all such fee contributions should also be added (but can be
    computed deterministically in case this is known)

inputs before outputs?
only rely on payment ACKs

## Rationale

## Backwards Compatibility

## Reference Implementation

---

# TODO

- new PSBT version?
  - con: new PSBT version
    pro: deserializing unordered txns in psbtv2 will error instead of
    potentially leaking unshuffled input/output order

- Move inline rationales to their own section

- BIP 174 describes how to aggregate signatures via combiner. example includes a manual coinjoin flow, joining of PSBTs not defined in the spec. technically this involves two different PSBTs. discuss what happens when not sequential, as well as conceptual issues.

---

- discuss liveness. safety WRT transaction effects is nice but we also want to
  minimize irrecoverable failures. discuss both generally and in CRDT section.
