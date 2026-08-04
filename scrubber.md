o<!-- ### meta/TODO

The immediate goal of this document is just to be a minimal list of fields that
are necessary and safe to share.

Ideally this document should comprehensively categorize fields by privacy
implications with respect to different kinds of peers, for all BIP 174 and BIP 370 roles.

---

There should be clear diagrams showing how the different roles interact around
the privacy boundary. For example, Creator role can already add a bunch of
private information in a single-party setting (`createfundedpsbt`), and this is
appropriate. (nested) Multisig may involve multiple privacy boundaries, and the
updater role may interact in complicated ways with this.

--- -->

# BIP: XXX Privacy PSBT

## Abstract

PSBT creation, construction, updating, and signing may all add privacy-sensitive information to PSBTs.

When exchanging (modifiable) PSBTs during construction (BIP 370 or otherwise) or signing with untrusted counterparties, only some fields are necessary to share, and privacy can be harmed significantly if certain fields required for a signing device, for example, are leaked to an untrusted party.

This document specifies what fields can be shared with trusted and untrusted parties such that privacy is preserved.

## Rationale

Historically, PSBTs were exchanged only with trusted peers. For example, one owner, one organization, or mutually trusting cosigners. Interactive protocols now pass PSBTs across trust boundaries (payjoin, coordinator-less coinjoin, external combiners). Some protocols, such as BIP 77, explicitly mention what fields should be removed. However, other interactive transaction-construction BIPs either always assume a trusted environment or tacitly assume that clients will remove sensitive information. Without proper specification clients will diverge.

## Trust scope

Model the trust scope as a single authorization boundary: every PSBT role inside it may observe the full PSBT, including signing material and wallet-internal metadata. You rely on those parties not to relay that data outside the scope. When a PSBT leaves the scope, hand off only the entries the external role needs for its next step. Scrub every privacy-sensitive field listed below at each trust-boundary crossing unless policy explicitly documents an exception.

If a PSBT re-enters the trust scope, it may regain the fields that were stripped.

### Motivating examples

TODO: remove this section and integrate into parts of this doc

BIP 77/78 example: Payjoin requires the sender to strip derivation fields before responding to their counterparty.
The counterparty adds their inputs and outputs, updates with information necessary to sign the PSBT and then strips that information again before responding
to the sender. Either party only learns the information needed to complete the protocol.

Multisig example (2-of-3) with a central coordinator and mutually untrusting independent signers:
PSBT gets created, coins are selected and outputs are created. The change output includes enough information such that each signer can verify the change is created correctly.
The updater creates 3 different PSBTs with signing fields specific to a signer. Signers strip signing fields before distributing back to combiner -- they only include
a partial signature.
Signers do not learn each other's derivation paths. In case a signer is replaced, they will not be able to identify the wallet's future outputs based on on-chain information.

BIP 174 manual coinjoin workflow:
This is an example of interactive transaction construction between three mutually untrusting wallets. Alice creates the PSBT and adds her inputs; at this point the PSBT should only contain public fields. Bob does the same. Carol adds inputs and signs them. This is not explicitly noted, but signing fields may have been present. Carol (and the other signers) must strip signing fields before returning the PSBT.

## Specification

### Scrubber Role

Run the scrubber at the trust boundary on the sending side. It reads the in-scope PSBT, copies only the non-sensitive fields defined below into a fresh outbound PSBT, and drops everything else before handoff. The scrubber must sit inside the wallet trust scope: it needs the full PSBT to scrub correctly, and only the scrubbed copy crosses the trust scope.

## Fields

We categorize PSBT fields from the [BIP 174 type registry](https://github.com/bitcoin/bips/blob/master/bip-0174/type-registry.mediawiki) by privacy sensitivity. Each table lists the registry name, key type, minimum PSBT version, and the BIP that introduces the field.

### Insensitive Fields

These include public fields that the final transaction reveals on-chain.

Some of these fields will always be available on-chain. Others are conditional based on the output type and/or the wallet policy. Those that are optional should not be shared with other signing parties or the combiner. If they are non-optional, they can be shared unconditionally. If a field is non-optional but may not end up on-chain (for example, when witness data exists for multiple spending conditions), the peer before the trust boundary must judge which path is likely to be used and remove witness fields that are unlikely to appear on-chain before handoff. TODO: elaborate on the last sentence.

#### Global

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_GLOBAL_UNSIGNED_TX = 0x00` | 0 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_GLOBAL_TX_VERSION = 0x02` | 2 | [370](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki) |
`PSBT_GLOBAL_FALLBACK_LOCKTIME = 0x03` | 2 | [370](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki) |
`PSBT_GLOBAL_INPUT_COUNT = 0x04` | 2 | [370](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki) |
`PSBT_GLOBAL_OUTPUT_COUNT = 0x05` | 2 | [370](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki) |

#### Input

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_IN_NON_WITNESS_UTXO = 0x00` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_WITNESS_UTXO = 0x01` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_SIGHASH_TYPE = 0x03` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_REDEEM_SCRIPT = 0x04` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_WITNESS_SCRIPT = 0x05` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_FINAL_SCRIPTSIG = 0x07` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_FINAL_SCRIPTWITNESS = 0x08` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_PREVIOUS_TXID = 0x0e` | 2 | [370](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki) |
`PSBT_IN_OUTPUT_INDEX = 0x0f` | 2 | [370](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki) |
`PSBT_IN_SEQUENCE = 0x10` | 2 | [370](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki) |
`PSBT_IN_REQUIRED_TIME_LOCKTIME = 0x11` | 2 | [370](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki) |
`PSBT_IN_REQUIRED_HEIGHT_LOCKTIME = 0x12` | 2 | [370](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki) |
`PSBT_IN_TAP_KEY_SIG = 0x13` | 2 | [371](https://github.com/bitcoin/bips/blob/master/bip-0371.mediawiki) |
`PSBT_IN_TAP_SCRIPT_SIG = 0x14` | 2 | [371](https://github.com/bitcoin/bips/blob/master/bip-0371.mediawiki) |
`PSBT_IN_TAP_LEAF_SCRIPT = 0x15` | 2 | [371](https://github.com/bitcoin/bips/blob/master/bip-0371.mediawiki) |

/// Tapscript signatures must be treated as sensitive if they may not end up on-chain; i.e., the PSBT can be finalized in more than one way.
/// Contrived example: you have both a key-path spend signature and a tapscript signature. Some other party decides which to broadcast. That party learns your tap tree structure.

#### Output

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_OUT_AMOUNT = 0x03` | 2 | [370](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki) |
`PSBT_OUT_SCRIPT = 0x04` | 2 | [370](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki), [375](https://github.com/bitcoin/bips/blob/master/bip-0375.mediawiki) |

#### Internal PSBT Fields

These fields govern internal PSBT logic and can be shared without loss of privacy.

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_GLOBAL_TX_MODIFIABLE = 0x06` | 2 | [370](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki) |
`PSBT_GLOBAL_VERSION = 0xFB` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |

### Sensitive Fields

These include signing fields and metadata a signing party needs to derive keys, identify wallet-controlled outputs, verify wallet policy, or verify protocol-specific rules.

Air-gapped cold signing parties need these fields explicitly because they may not maintain wallet state or derive the required context from another source.

#### Partial Signatures

The primary privacy concern is revealing which keys have signed and any public keys not already present in script fields; combiners require the signature values to merge.

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_IN_PARTIAL_SIG = 0x02` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |

#### Derivation Fields

Untrusted parties that learn an xpub and derivation path can derive previous and future (unhardened) addresses.

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_GLOBAL_XPUB = 0x01` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_BIP32_DERIVATION = 0x06` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_OUT_BIP32_DERIVATION = 0x02` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_TAP_BIP32_DERIVATION = 0x16` | 2 | [371](https://github.com/bitcoin/bips/blob/master/bip-0371.mediawiki) |
`PSBT_OUT_TAP_BIP32_DERIVATION = 0x07` | 2 | [371](https://github.com/bitcoin/bips/blob/master/bip-0371.mediawiki) |
`PSBT_IN_SP_SPEND_BIP32_DERIVATION = 0x1f` | 2 | [376](https://github.com/bitcoin/bips/blob/master/bip-0376.mediawiki) |

#### Proprietary and Unknown Fields

Global, input, and output proprietary and unknown fields are application-defined: their meaning is not specified by the PSBT standards, so a scrubber cannot classify them as safe to retain. **By default, remove them** before any handoff to an untrusted party.

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_GLOBAL_PROPRIETARY = 0xFC` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_PROPRIETARY = 0xFC` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_OUT_PROPRIETARY = 0xFC` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`(any unregistered keytype)` | 0, 2 | — |

#### Pre-images

These fields supply preimages for hash-lock conditions in scripts (HTLCs). TODO: expand rationale.

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_IN_RIPEMD160 = 0x0a` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_SHA256 = 0x0b` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_HASH160 = 0x0c` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_IN_HASH256 = 0x0d` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |

#### Taptree Fields

Taproot hides optional script paths from untrusted parties. Internal key and related fields reveal whether script paths exist.

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_IN_TAP_INTERNAL_KEY = 0x17` | 2 | [371](https://github.com/bitcoin/bips/blob/master/bip-0371.mediawiki) |
`PSBT_IN_TAP_MERKLE_ROOT = 0x18` | 2 | [371](https://github.com/bitcoin/bips/blob/master/bip-0371.mediawiki) |
`PSBT_OUT_TAP_INTERNAL_KEY = 0x05` | 2 | [371](https://github.com/bitcoin/bips/blob/master/bip-0371.mediawiki) |
`PSBT_OUT_TAP_TREE = 0x06` | 2 | [371](https://github.com/bitcoin/bips/blob/master/bip-0371.mediawiki) |

#### Output Redeem Script / Witness Script

This data may eventually appear on-chain; revealing it early leaks the spending condition prematurely.

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_OUT_REDEEM_SCRIPT = 0x00` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |
`PSBT_OUT_WITNESS_SCRIPT = 0x01` | 0, 2 | [174](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) |

#### MuSig Fields

MuSig2 signing parties usually sit in the same trust scope. An untrusted party that learns the other signing parties’ keys can correlate them with the aggregate key and weaken MuSig’s single-key-spend obfuscation.

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_IN_MUSIG2_PARTICIPANT_PUBKEYS = 0x1a` | 2 | [373](https://github.com/bitcoin/bips/blob/master/bip-0373.mediawiki) |
`PSBT_IN_MUSIG2_PUB_NONCE = 0x1b` | 2 | [373](https://github.com/bitcoin/bips/blob/master/bip-0373.mediawiki) |
`PSBT_IN_MUSIG2_PARTIAL_SIG = 0x1c` | 2 | [373](https://github.com/bitcoin/bips/blob/master/bip-0373.mediawiki) |
`PSBT_OUT_MUSIG2_PARTICIPANT_PUBKEYS = 0x08` | 2 | [373](https://github.com/bitcoin/bips/blob/master/bip-0373.mediawiki) |

/// I don't think MuSig2 keys are sensitive in the same way as public keys in `OP_CHECKMULTISIG`. During setup, generating the aggregate key requires knowing the entire key set to commit to it, so signers are necessarily in the same trust scope—but what about the combiner?

In MuSig2 the signing parties are necessarily within the same trust scope. However, if an untrusted party learns the other signing parties’ keys, they can correlate the aggregate key with individual signers in that multisig. Worse, it defeats the point of MuSig2: obfuscating a multisig behind a single key-path spend.

// Partial signatures are listed for the same reason as above.

#### Silent Payment Fields

Silent payment outputs should look like ordinary P2TR key spends. Reveal silent-payment fields only across a trust boundary when the protocol requires it.

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_GLOBAL_SP_ECDH_SHARE = 0x07` | 2 | [375](https://github.com/bitcoin/bips/blob/master/bip-0375.mediawiki) |
`PSBT_GLOBAL_SP_DLEQ = 0x08` | 2 | [375](https://github.com/bitcoin/bips/blob/master/bip-0375.mediawiki) |
`PSBT_IN_SP_ECDH_SHARE = 0x1d` | 2 | [375](https://github.com/bitcoin/bips/blob/master/bip-0375.mediawiki) |
`PSBT_IN_SP_DLEQ = 0x1e` | 2 | [375](https://github.com/bitcoin/bips/blob/master/bip-0375.mediawiki) |
`PSBT_IN_SP_TWEAK = 0x20` | 2 | [376](https://github.com/bitcoin/bips/blob/master/bip-0376.mediawiki) |
`PSBT_OUT_SP_V0_INFO = 0x09` | 2 | [375](https://github.com/bitcoin/bips/blob/master/bip-0375.mediawiki) |
`PSBT_OUT_SP_V0_LABEL = 0x0a` | 2 | [375](https://github.com/bitcoin/bips/blob/master/bip-0375.mediawiki) |

// Tweak the input such that it can spend the output.
// If you reveal your tweak, an untrusting participant can link your input to a silent payment output and verify that the output is a silent payment.

// TODO: are these sensitive? Yes, partly because they label an output as a silent payment when untrusting parties would not otherwise know.
// Created when the input set is not unilateral.
// Created and shared when all inputs are owned by the same owner.
// This necessarily implies a common input owner.
// TODO: maybe these are sensitive because of the common-input-ownership heuristic, but the per-input ones are not?

#### Misc

`<keytype>` | PSBT version | BIP |
--- | --- | --- |
`PSBT_GLOBAL_GENERIC_SIGNED_MESSAGE = 0x09` | 2 | [322](https://github.com/bitcoin/bips/blob/master/bip-0322.mediawiki) |
`PSBT_IN_POR_COMMITMENT = 0x09` | 0, 2 | [127](https://github.com/bitcoin/bips/blob/master/bip-0127.mediawiki) |
`PSBT_OUT_DNSSEC_PROOF = 0x35` | 2 | [353](https://github.com/bitcoin/bips/blob/master/bip-0353.mediawiki) |

`PSBT_GLOBAL_GENERIC_SIGNED_MESSAGE` falls into a similar category as proprietary and unknown fields. Depending on the message contents, sharing with untrusted parties may be appropriate, but by default it should be removed.

`PSBT_IN_POR_COMMITMENT` is meant to be shared only with trusted parties. Signing parties must share their commitment only with trusted parties.

`PSBT_OUT_DNSSEC_PROOF` creates an identity-to-output mapping and should be shared only with trusted parties.

### Modifiable Flag Note

If the inputs- or outputs-modifiable flags are set, the scrubber [can still remove individual fields](https://github.com/bitcoin/bips/pull/1059#discussion_r593537694).

### Updater: multi-signer case

In cases where multiple untrusting signers are participating in the signing process, the updater must build a separate PSBT per signer and attach only that signer's required signing fields on each copy.

### Field transfer sequence

Example: wallet trust scope versus an external combiner. The Creator through Scrubber roles sit in one scope and may handle signing metadata under your internal policy. Scrubber to Combiner is the trust-boundary crossing: the scrubber builds the outbound PSBT copy that keeps only what merge needs (typically the public transaction skeleton plus that signing party’s partial witness material) and drops every other privacy-sensitive field listed below.

```mermaid
sequenceDiagram
    box rgba(230,242,255,0.55) Wallet trust scope
        participant Creator
        participant Constructor
        participant Updater
        participant Signer
        participant Scrubber
    end
    box rgba(255,235,235,0.45) External to wallet trust scope
        participant Combiner
        participant Finalizer
        participant Extractor
    end

    Creator->>Constructor: Empty PSBT
    Constructor->>Updater: Public transaction fields

    Updater->>Signer: Public transaction fields
    Updater->>Signer: Signing fields scoped to this signer

    Signer->>Scrubber: PSBT with signing metadata and partial witness
    Note over Signer,Scrubber: Scrubber stays inside the wallet trust scope and may read the full PSBT.

    Scrubber->>Combiner: Public transaction fields
    Scrubber->>Combiner: Partial witness fields for merge
    Note over Scrubber,Combiner: Trust boundary. Outbound copy omits sensitive fields.

    Combiner->>Finalizer: Public transaction fields
    Combiner->>Finalizer: Combined partial witness fields

    Finalizer->>Extractor: Finalization fields
    Note over Extractor: Extract broadcast-ready transaction
```

Example: **2-of-3** with two co-owner signing parties in the wallet trust scope and a third **recovery signing party** outside it, as in [BIP 89](https://github.com/bitcoin/bips/blob/master/bip-0089.mediawiki) chain-code delegation. Co-owners receive full signing metadata inside the scope. The recovery party acts as **delegator** and must not receive other parties’ derivation paths, public keys, or partial signatures. The updater builds a separate PSBT copy per signing party.

```mermaid
sequenceDiagram
    box rgba(230,242,255,0.55) Wallet trust scope
        participant Creator
        participant Constructor
        participant Updater
        participant SignerA
        participant SignerB
        participant Scrubber
        participant Combiner
    end
    box rgba(255,235,235,0.45) BIP 89 delegator outside scope
        participant SignerC
    end

    Creator->>Constructor: Empty PSBT
    Constructor->>Updater: Public transaction fields

    Updater->>SignerA: PSBT copy, public fields and signing metadata
    Updater->>SignerB: PSBT copy, public fields and signing metadata
    Note over Updater,SignerB: Co-owners stay in scope. One party may act as BIP 89 delegatee.

    Updater->>Scrubber: PSBT copy scoped to SignerC
    Note over Updater,Scrubber: Omit other signing parties' derivations and partial signatures.

    Scrubber->>SignerC: Scrubbed PSBT and CCD tweak bundle
    Note over Scrubber,SignerC: Trust boundary. Delegator sees only per-spend signing context.

    SignerC->>Combiner: Partial witness from SignerC

    SignerA->>Combiner: Partial witness from SignerA
    SignerB->>Combiner: Partial witness from SignerB
    Note over SignerA,Combiner: Combiner is trusted. Co-owners need not scrub for merge.

    Combiner->>Combiner: Merge partial witnesses
```

### Reference Implementation

<https://github.com/arminsabouri/rust-psbt/tree/scrubber-role>

### Test Vectors

A collection of test vectors is [provided](https://github.com/arminsabouri/rust-psbt/blob/scrubber-role/tests/data/psbt-scrub.json). Each test vector contains an input PSBT and an expected PSBT after the scrubber role has run. Both PSBTs are in base64 format.
