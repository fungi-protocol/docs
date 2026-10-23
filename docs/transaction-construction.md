---
type: Specification
title: Transaction construction
description: Content and state synchronization, the phases, the optimistic and recovery tracks, and what the validity proofs enforce.
status: draft
stale_after: 2027-04-23T00:00:00Z
---

# Transaction construction

🤖 Transaction construction starts from an accepted coalition formation proposal and ends with a signed transaction. This chapter describes it in the abstract. Its sub-chapters define the [block DAG](block-dag.md) that the tracks share, and describe each track.

## 🤖 Content and state {#content-and-state}

Construction synchronizes two different things:

- **Content**: the transaction-level messages, such as inputs, outputs, fee contributions and their proofs. The [validity proofs](validity-proofs.md) constrain which content is valid.
- **State**: which admitted content is in the agreed state of each phase. State synchronization uses agreement-level messages, the validator blocks. Validity proofs do not cover blocks. Blocks have their own mechanisms, such as the [nonce commitments](block-dag.md#nonce-commitments-and-compact-equivocation-evidence) that expose the key of a validator that equivocates.

Transmitting either between peers is described in [peer set reconciliation](set-reconciliation.md).

## 🤖 Phases {#phases}

🤖 The initial inputs are already fixed by the accepted coalition formation proposal. The *optimistic phases* add content without validity proofs. They concern transaction data, and are not to be confused with the [optimistic track](optimistic-track.md), which concerns agreement. The optimistic phases are the semi-honest construction, including when it is used in the Byzantine setting.

🤖 Every message is [keyed](optimistic-track.md#keyed-and-anonymous-phases): it relates to one input, one output or one fee contribution. Phases differ in whether their keys are listed when the phase opens or arrive anonymously.

| Phase | Keys | Content | Next |
| --- | --- | --- | --- |
| 1. Kickoff | listed: initial inputs | acknowledgement of the proposal | 2 |
| 2. Optimistic auxiliary inputs | anonymous | auxiliary inputs, without proofs | 3 |
| 3. Optimistic outputs and fee contributions | anonymous | outputs and fee contributions, without destination commitments or proofs | balance zero: 8; overflow: 4 |
| 4. Initial-input proofs | listed: initial inputs | commitments to allocations of funds and vbytes | 5 |
| 5. Auxiliary-input proofs | anonymous | proofs authenticated by each auxiliary input's own online key, consuming initial inputs' vbyte allocations | 6 |
| 6. Allocation registration | anonymous | proofs of allocations against the session root | 7 |
| 7. Output proofs | anonymous | proofs of coverage against the registered-leaf root | 8 |
| 8. Signatures | listed: final inputs | input signatures | done |

🤖 Phases 4 to 7 are the proven phases. They run only if the optimistic outputs and fee contributions overflow the available balance. The optimistic outputs are then discarded, and the proven phases use fresh, unguessable output ids. Once phase 5 closes, both input-proof sets determine the session root; the closed registration set determines the registered-leaf root. Output scripts are authorized as specified by the [validity proofs](validity-proofs.md). On the optimistic track, only a balance of zero continues to signatures. Unclaimed balances are possible only on the [recovery track](recovery-track.md), which is a different termination path. How output values are chosen is a matter of strategy, not of this protocol.

Each phase closes on a stable state before the next one starts. The [optimistic track](optimistic-track.md#phase-closure) says why, and gives the acknowledgement rule for each kind of phase. The [overview](overview.md) describes the honest, semi-honest and Byzantine settings these phases run in.

## 🤖 Tracks {#tracks}

Both tracks use the [block DAG](block-dag.md).

- [**Optimistic track**](optimistic-track.md), with threshold $t = n$. It is asynchronous, and phases advance by unanimous acknowledgement. On its own, it is sufficient in the honest and semi-honest settings.
- [**Recovery track**](recovery-track.md), with $t \lt n$. It is optional, and assumes synchrony or partial synchrony. It turns a stalled phase into a recovery coalition formation proposal.

## Validity proofs

🤖 [Validity proofs](validity-proofs.md) are needed only once overspending is detected. They reduce the validity of transaction-level messages to omission faults: a participant can still withhold a message, but cannot get an invalid one accepted. They enforce:

- **No inflation.** Amounts are non-negative, and the outputs sum to at most the value of the inputs. What no output claims is fee.
- 🤖 **Flood protection.** In the proven phases, auxiliary inputs consume initial inputs' vbyte allocations, registrations consume input slots, and each output claims a registered leaf. In the optimistic outputs phase, every output or fee contribution accounts for at least 1 sat, so the available input balance bounds contributions before overflow. An overflow signal can trigger proving, but the phase still closes under its normal agreement rule. These are contribution bounds, not bounds on all network traffic.
- **Session binding.** No statement can be replayed in another session.

🤖 They enforce this without revealing how a participant splits its inputs' value among its outputs and payments. Payment satisfaction is checked by counterparty confirmation before signing, as the [concurrent PSBT specification](psbt-concurrent.md#confirmation-of-successful-payment-prior-to-signing) defines. In the proven phases, a receipt additionally proves that the payment allocation was claimed; it does not replace confirmation.

In the optimistic phase, no proofs are needed if every participant can verify that all of its funds are accounted for in its outputs and fees contributions, and no overspending has occurred, and everyone acknowledges that exact state. Overspending triggers proving so that contentious outputs and fee contributions can be validated. An anonymous, oversized fee contribution permits any participant to abort the optimistic phase and force validity proofs to be required.

Only valid transactions have consequences for the owners of the inputs, because an invalid transaction cannot actually spend any coins, even if fully signed. The sense in which the fragments themselves must be valid according to the proofs is that when combined they would result in a valid transaction if it were fully signed. Taken together with the incentive compatibility assumption, the lack of obstruction removes any reason for honest participants to withhold their signatures: by following the protocol their funds will be sent to the destination they intended, and since this applies to all participants, this removes any valid reason for honest participants to withhold their input signatures.
