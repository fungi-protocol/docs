<!-- 
META:
in a concurrent setting participants may need to send authenticated and confidential messages to one another. In setting where PSBTs are the main unit of communication its best if participants can continue to use PSBTs.

How can we HPKE encrypt custom messages in proprietart fields. Need to specify what version, ciphersuit (?), and include the ciphertext in the value. 

Things to think about:
- HPKE Auth mode
- the spec should leave key bootstraping out of the scope.
- Additional context? Dummy data?
- HPKE doesn't pad. Ciphertext length leaks plaintext length, 
- Aligator switft a.la bip77

-->


# Encrypted PSBT Fragments

## Abstract

This document specifies a method for encoding HPKE-encrypted messages within PSBT proprietary fields. Participants in multi-party transaction construction protocols use this mechanism to exchange authenticated, confidential, arbitrary-length application messages alongside the transaction data they are jointly building, without introducing a communication channel outside PSBT itself.

## Rationale

PSBT fields are visible to every participant who receives the PSBT. Multi-party construction protocols require this for the transaction data itself to be jointly readable but not for all application-layer messages. Coordination messages such as payment acknowledgments are often intended for a single recipient or a subset of the participant set, and must remain confidential from the rest.

Encrypting these messages and carrying them in PSBT proprietary fields lets participants reuse the existing PSBT exchange as the transport, instead of standing up a separate authenticated channel and new data formats. This preserves the property that a single PSBT round-trip carries everything needed to advance the protocol.

<!-- TODO: maybe a blurb about hpke (rfc#...) -->

## Specification

### Using Proprietary Fields

Callers MUST use proprietary field in either the input, output or global map `0xFC`. 

The keydata will include the RFC9180 cipher suite ids (if we support multiple ciphersuites see below). // TODO: this will identify this field has a hpke message.

Valuedata must include `enc` (the encapsulated ephemeral key) and the ciphertext(s).

Encrypted messages are encoded as PSBT proprietary fields (PSBT_*_PROPRIETARY, type 0xFC), scoped to the global, input, or output map depending on which part of the transaction the message pertains to.

A single logical message occupies exactly one proprietary field. A sender addressing multiple recipients encrypts and encodes the message separately for each, producing one field per recipient.

Participants must optimistically attempt to decrypt each field to identify their own.

<!--
How can we prevent the receiver from processing teh exact same message.
i.e deterministically join two encrypted fragments.

-->

### Versioning and Type

<!-- How can the participants in the protocol detect and try to decrypt a message. 
Could add a type byte to keydata. And A version to support schema upgrades.
-->

### HPKE 

#### Specifying cipher suite

<!--

Do we specify cipher suite or allow participants to dictate? I'm leaning towards the latter it helps with future compatability (PQ schemes, etc..)
keep in mind specifiying these things in keydata (or in valuedata) may have dicernable structure? How can we get it close to uniform random

Maybe some piece about future upgrades e.g ML-KEM.
-->

#### Info

<!-- We need to bind the keys used during hpke to specific context.
Without it a cipher text valid in one setting can be valid in another.


Bip# can be used but some application provided string is also needed.-->
#### Key sharing

<!-- mention that pks are meant to be shared out of band. Key establishment is out of scope.  -->

#### Auth mode

<!-- Do we support various auth modes. Base? Auth? PSK? In which case is the auth mode communicated out of band? Not sure how this works -->
<!-- Single shot mode or stateful seq ? -->


### Privacy Considerations

<!-- How much can we actually get away with? And explicitly what are out goals?

the AEAD output IIRC is uniformally random and so can enc with BIP324 (see below) but other things have strucutre such the ciphersuit bits 

-->_

#### Message Padding

<!-- In a privacy preserving setting we may want to prevent other peers from learning any metadata about the contents of our message -->

<!-- In general the data should be look like uniform random bytes -->


#### BIP324 ElligatorSwift

Encode the HPKE encap'd public keys such that other participants the cannot detect a raw curve point.

<!-- I believe this only pertains to certain curves and KEMs -->


## Flow Diagram
<!-- what does the e2e flow look like? Should cover out of band key pk retreieval, encrypting with some auth mode, and what information the decryptor has to decrypt -->

## Reference Implementation and Test vectors

TODO

