---
type: Specification
title: Contacts and payment messaging
description: What interactive payments need from peer to peer messaging between payer and payee.
status: draft
stale_after: 2027-04-15T00:00:00Z
---

# Contacts and payment messaging

🤖 Interactive payments need the payer and the payee to message each other. This chapter states what the protocol requires of that messaging. How an application manages contacts, identities and devices, and how it obtains a suitable channel, is up to the application. The protocol only uses the channel it is given, so it need not implement an identity system.

## Requirements

1. 🤖 **Reach the counterparty's device.** A peer can send authenticated [peer to peer messages](transport-interfaces.md#kinds-of-messaging) to a device acting for its counterparty.
2. 🤖 **Invite it into a collaborative transaction.** A payment is made by inviting the counterparty into a transaction construction session. The invitation binds the session's identity, its initial state and its broadcast namespace. An accepted invitation therefore cannot silently substitute a different session. Receiving an invitation is distinct from accepting the transaction's terms.
3. 🤖 **Message it during the critical section.** After output finalization and before input signing, the counterparties exchange payment confirmations. The messaging must remain available for this.

🤖 The payment relationship can be honest or semi-honest, even when the construction session uses the Byzantine fault tolerant protocol. The confirmations below are how the counterparties check that the shared session satisfies their payment.

Payment communication has different requirements, which also must be provided by the underlying transport. A sender must authenticate its receiver and obtain confirmation that the proposed transaction satisfies their agreement. However, this authentication can rely on a one-time code or pseudonym. The receiver doesn't need to authenticate the sender in order to be paid securely. Both counterparties know their payment amount, but need not disclose that relationship to the group or identify their transaction inputs and outputs to one another.

## 🤖 Confirmation during construction {#confirmation-during-construction}

Before signing its inputs, the payer needs the payee to confirm that the output set it will sign is consistent with the payee's claim that the funds reach their ultimate destination. The confirmation is with respect to the construction state, including payments settled through other participants. It is distinct from confirmation of a transaction on the Bitcoin chain.

The [concurrent PSBT specification](psbt-concurrent.md#confirmation-of-successful-payment-prior-to-signing) defines who confirms to whom, in what order, and how cycles in the payment graph are broken. The confirmed construction state is bound to the protocol transcript's Merkle-set commitment, which is used as the deterministic sort seed. The transcript includes the applicable proofs as well as transaction contributions, so this commitment also binds those proofs.

Counterparties exchange these confirmations after output finalization and before input signing, with respect to that finalized state. An earlier agreement on a payment or maker is not a substitute for this check. Each participant also checks the applicable proof obligations, while the construction protocol supplies its validity and phase-agreement rules.
