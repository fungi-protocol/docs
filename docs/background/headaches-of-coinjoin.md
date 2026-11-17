---
type: Essay
title: "The many headaches of CoinJoin"
description: "Why designing a CoinJoin that overtly optimizes for privacy is harder than the folk anonymity set model suggests."
status: stable
---

# The Many Headaches of CoinJoin

> Originally published as [The Many Headaches of CoinJoin](https://spiralxyz.substack.com/p/the-many-headaches-of-coinjoin) by Yuval Kogman
> ([@not_nothingmuch](https://x.com/not_nothingmuch)) on Spiral,
> 2026-09-03.

CoinJoin has [many faces](faces-of-coinjoin.md), and it also has many headaches. This post will specifically focus on the cluster headache, pun unapologetically intended, that is designing an overtly privacy-optimizing CoinJoin structure.

## Anonymity sets packed with strawmen

The “folk” notion of an equal-amount CoinJoin anonymity set, based on the analogy to mixnets, unfortunately rests on some fairly strong and often tacit assumptions. These assumptions limit the model’s applicability for understanding the capabilities of real-world adversaries.

In this conception of on-chain privacy, a CoinJoin transaction is analogized to a single shuffling stage in a mixnet. In each such transaction, there are *k* equivalent outputs that are presumed to be shuffled. Because they are equivalent, in the absence of auxiliary information not on the blockchain, there is ostensibly nothing to link any one output to any particular cluster associated with the inputs.

A real-world adversary can incorporate later spending patterns, clustering techniques, and auxiliary information. It is not constrained to only examine the CoinJoin, with no memory of other transactions.

If you want to skip the rest of this post, the main takeaway is that these outputs almost inevitably become more distinguishable in a variety of ways. The discussion is not exhaustive. Sometimes these privacy leaks will be enough for an adversary to link post-CoinJoin coins to their pre-CoinJoin ancestors successfully, but it’s hard to say to what degree.

## The adversary doesn’t necessarily have tunnel vision

The most obvious tacit assumption of the folk anonymity set model is that the CoinJoin structure can be considered separately from the rest of the transaction graph.

Real-world adversaries of bitcoin users might be abusive spouses, criminals looking to steal or extort (sometimes aided by government officials), dragnet surveillance by governments, advertising companies, each with their different purposes in mind. A bitcoin user is exposed to harm from such interests if they lose deniability or leak information about their spending habits, net worth, security posture, etc. Depending on how motivated such a real-world adversary is, they may spend more resources attempting to surveil their victims. Still, it’s not reasonable to assume such adversaries can’t access a block explorer.

It is customary to think of the adversary as an algorithm trying to output its best guess about the links. If this algorithm is constrained, and given only a single transaction in isolation, and no memory, although that might be enough to express some of the capabilities of the real-world adversaries, it already fails to capture wallet clustering, which is literally the oldest trick in the book (i.e., in the bitcoin privacy literature).

A related misconception is that for some transactions breaking privacy is computationally intractable, which makes them private. Privacy should not rely on non-standard computational hardness assumptions (and relying on standard ones is just a fancy way of saying “using cryptography”).

## Auxiliary information, metadata privacy

Another tacit assumption is that it is enough to consider just the data on-chain. Unfortunately, external blockchain auxiliary information is clearly useful for deanonymization.

Such information might be confidential compliance records (e.g. AML/KYC data available exchanges, or companies to whom they outsource identity verification) or other personally identifying information (e.g. email or physical addresses leaked in a website breach), temporal fingerprints (e.g. periods of activity indicating a likely time zone, but also things like latency), IP addresses, and implementation specific behavior that might reveal a user’s choice of wallet.

Although this is important to consider, for this post we’ll now assume transport-level privacy works as a black box.

A much stronger assumption we will leave intact is that it is easy to design a safety margin that accounts for any other auxiliary information related to the on-chain structure. The next post in the series will not entirely remove that assumption, but can at least provide a framework for treating it as an engineering problem as opposed to a tribal identity.

We will return to the subject of auxiliary information in the last section of this post.

## Sybil resistance

The *n*-1 or Sybil deanonymization attack gives the adversary information about who the user is *not*. If all users but one are under adversarial control, all of their inputs and outputs can be excluded. This leaves the remaining honest user with effectively no anonymity, but maintains the appearance of an intact anonymity set.

This challenge is inherent in a permissionless system. Such “[Sybil” users](https://en.wikipedia.org/wiki/Sybil_attack), many pseudonymous identities of a single entity, are indistinguishable from honest users. Therefore, Sybil resistance can only come from imposing some cost on participation. Some costs are inherent in bitcoin: transaction fees and time value of money. Additional costs can be imposed through mechanism design, but e.g. in the case of coordination fees, note that those decrease the cost of a Sybil attack by a corrupted coordinator, but that is largely a theoretical concern because thus far every centrally coordinated protocol on bitcoin has required trust in the coordinator at the protocol level.

For bitcoin transactions specifically, the number of honest users may be large without much impact if the honest users’ actions don’t support each other’s privacy. For example, if the values of their coins are too far apart.

For now, we will assume Sybil resistance can be taken for granted, i.e., that some mechanism enforces that such an attack is not costless, as that is the only kind of mitigation possible in the permissionless setting. Note that whatever mechanism is used, it shouldn’t degrade the privacy of the honest users. Where this is relevant to the on-chain structure, it will come up again, but otherwise Sybil resistance will be out of scope for this post.

## Other users must also protect their privacy

Even if we assume other users are not under adversarial control, if they lose their privacy due to carelessness or any other reason, the net effect is essentially the same as if they colluded with the adversary. Unlike a Sybil attack, sometimes it at least might be obvious that one of the other participants has lost privacy entirely.

<div class="chart-src">
<img src="img/headaches-of-coinjoin-1-light.png#gh-light-mode-only" loading="lazy" alt="When the CoinJoin is created, from Alice’s perspective it’s indistinguishable from the best case privacy: each equal output appears equally attributable to any participant.">
<img src="img/headaches-of-coinjoin-1-dark.png#gh-dark-mode-only" loading="lazy" alt="When the CoinJoin is created, from Alice’s perspective it’s indistinguishable from the best case privacy: each equal output appears equally attributable to any participant.">
</div>

When the CoinJoin is created, from Alice’s perspective it’s indistinguishable from the best case privacy: each equal output appears equally attributable to any participant.

A trivial example is reusing a public key used before a CoinJoin in a subsequent transaction, overtly linking a particular input and output. If Alice indexed all known addresses on the blockchain, she would be able to notice this, but that is costly. Needless to say, for the adversary, such costs are negligible and do not present a meaningful barrier. From the attacker’s point of view, it looks more like this at the time the CoinJoin is broadcast:

<div class="chart-src">
<img src="img/headaches-of-coinjoin-2-light.png#gh-light-mode-only" loading="lazy" alt="The adversary can recognize that Bob’s output reuses a public key from before the CoinJoin. Note that this doesn’t require the adversary also to know that Bob’s input is Bob’s in this example. However, that is what is depicted; merely knowing the output belongs to Bob eliminates that output from being owned by Alice from the adversary’s point of view. The remaining candidate set shrinks from four participants to three.">
<img src="img/headaches-of-coinjoin-2-dark.png#gh-dark-mode-only" loading="lazy" alt="The adversary can recognize that Bob’s output reuses a public key from before the CoinJoin. Note that this doesn’t require the adversary also to know that Bob’s input is Bob’s in this example. However, that is what is depicted; merely knowing the output belongs to Bob eliminates that output from being owned by Alice from the adversary’s point of view. The remaining candidate set shrinks from four participants to three.">
</div>

The adversary can recognize that Bob’s output reuses a public key from before the CoinJoin. Note that this doesn’t require the adversary also to know that Bob’s input is Bob’s in this example. However, that is what is depicted; merely knowing the output belongs to Bob eliminates that output from being owned by Alice from the adversary’s point of view. The remaining candidate set shrinks from four participants to three.

A more subtle example is linking through clustering heuristics. Such loss might be as damaging as address reuse, but it would typically be harder to notice, especially if it results from multiple data points rather than one unambiguous privacy error.

<div class="chart-src">
<img src="img/headaches-of-coinjoin-3-light.png#gh-light-mode-only" loading="lazy" alt="In this example, Carol spends her CoinJoin output together with an input of hers that the adversary knows about. The common input ownership heuristic (see the first post in the series) identifies her output, leaving only Alice and Dave indistinguishable.">
<img src="img/headaches-of-coinjoin-3-dark.png#gh-dark-mode-only" loading="lazy" alt="In this example, Carol spends her CoinJoin output together with an input of hers that the adversary knows about. The common input ownership heuristic (see the first post in the series) identifies her output, leaving only Alice and Dave indistinguishable.">
</div>

In this example, Carol spends her CoinJoin output together with an input of hers that the adversary knows about. The common input ownership heuristic (see the [first post](wallet-clustering-basics.md) in the series) identifies her output, leaving only Alice and Dave indistinguishable.

In general, such privacy losses may not even be apparent on-chain, e.g., another user disclosing KYC information to an exchange. This can even happen after the fact, and the damage to the other users’ privacy will be retroactive. Perhaps the most egregious such deanonymization occurred when, as part of litigation, Celsius users’ transaction history was inadequately “anonymized” (see [the post before last](intersection-attacks.md) for a discussion about anonymization failures), further harming not only direct victims of the fraud, but any parties they may have interacted with.

<div class="chart-src">
<img src="img/headaches-of-coinjoin-4-light.png#gh-light-mode-only" loading="lazy" alt="If the adversary has auxiliary information identifying Dave, then Alice’s output is deterministically linkable to her input, undoing all anonymity.">
<img src="img/headaches-of-coinjoin-4-dark.png#gh-dark-mode-only" loading="lazy" alt="If the adversary has auxiliary information identifying Dave, then Alice’s output is deterministically linkable to her input, undoing all anonymity.">
</div>

*If the adversary has auxiliary information identifying Dave, then Alice’s output is deterministically linkable to her input, undoing all anonymity.*

Setting this class of hazards aside, we will assume other users are both competent and vigilant in their pursuit of privacy.

## Change outputs are toxic for privacy

On a fundamental level, predicting payment amounts and future fee amounts has an element of market speculation. Even in cases when these might be reasonably predictable, the likelihood that a CoinJoin denomination would correspond to the required amount without producing change is low.

Suppose Alice has two coins with value *d* from two independent CoinJoin transactions, that *d* is the smallest denomination in common use, and that there were *k* such values in each of the CoinJoins. She then makes two independent payment transactions, each for an amount smaller than *d*. At this point the anonymity sets of the payment transactions are indeed as the naive analysis suggests.

<div class="chart-src">
<img src="img/headaches-of-coinjoin-5-light.png#gh-light-mode-only" loading="lazy" alt="Two CoinJoin output coins spent independently: each payment is ambiguous, and nothing overtly links the payments to the same user on-chain.">
<img src="img/headaches-of-coinjoin-5-dark.png#gh-dark-mode-only" loading="lazy" alt="Two CoinJoin output coins spent independently: each payment is ambiguous, and nothing overtly links the payments to the same user on-chain.">
</div>

*Two CoinJoin output coins spent independently: each payment is ambiguous, and nothing overtly links the payments to the same user on-chain.*

The value of each change output depends on the nature of Alice’s economic activity, as do the fees, so unless these are somehow fully determined well in advance (and denominated in bitcoin), she will need to deal with change outputs whose amounts will vary. This is more or less unavoidable in the UTXO model.

If Alice attempts to recover the value of these coins by spending them separately, each subsequent transaction will be linked to its predecessor. Worse, if the two coins are spent together, that transaction, by being linked to both prior payments, also undoes their privacy.

Next, suppose that the sum of the two change outputs happens to be *d* or more. This would allow Alice to CoinJoin again and recover the value in these change outputs. Unfortunately, with current CoinJoin implementations, this too will undermine privacy.

<div class="chart-src">
<img src="img/headaches-of-coinjoin-6-light.png#gh-light-mode-only" loading="lazy" alt="Even if the change outputs are only spent in CoinJoin transactions, the privacy of payment transactions and that of the user&#x27;s wallet more broadly are likely to become undermined as a result of attempting to improve them.">
<img src="img/headaches-of-coinjoin-6-dark.png#gh-dark-mode-only" loading="lazy" alt="Even if the change outputs are only spent in CoinJoin transactions, the privacy of payment transactions and that of the user&#x27;s wallet more broadly are likely to become undermined as a result of attempting to improve them.">
</div>

*Even if the change outputs are only spent in CoinJoin transactions, the privacy of payment transactions and that of the user's wallet more broadly are likely to become undermined as a result of attempting to improve them.*

Even if the change outputs are only spent into CoinJoin transactions, the payment transactions’ privacy and that of the user’s wallet more broadly is likely to become undermined as a result of attempting to improve it.

Fortunately, as we will see, this is not an inherent problem in CoinJoin transactions in the looser sense of the term, but it is inherent if only mix-style transactions are used.

## Coin selection

The previous section argued that change creation is inevitable. If only a single input is used for each transaction, the value of such a change output will necessarily be smaller than that of the input. If a wallet is subject to this constraint, over time its balance will get increasingly fragmented to the point of uselessness. For this reason, consolidation by spending more than one input per transaction is also inevitable. The more severe the fragmentation, the greater the degree of consolidation.

This inevitability provides some intuition for why CIOH is as effective as it is, but a less intuitive threat is that of intersection attacks. As [previously discussed](intersection-attacks.md), intersection attacks are much more powerful. While CIOH is only concerned with what is implied by a single transaction, assuming the adversary can examine the transaction graph to arbitrary depth and intersect coin histories, common points of origin may be identified much more easily than is often assumed. Especially if the targets for intersection are clusters obtained from auxiliary information, not just those based on local heuristics.

Even under the very generous assumptions we’ve made, we can see that CoinJoin transactions still have some irreducible friction that must be accounted for.

## Auxiliary information (example scenario)

If we now let go of these simplifying assumptions and return to auxiliary information, as we’ve already seen, it can take many forms. With the additional knowledge of what must be considered on-chain, we can now work through an example scenario in a bit more detail, and examine how such information might be used in the real world.

Say Alice is paid monthly from her employer Emily’s cold storage wallet. This takes the form of a large, batch transaction with outputs for various employees. If we assume all employees are paid the same, then outwardly this transaction might resemble a CoinJoin, but at the very least Emily knows which output belongs to which employee, even as the employees only know which output is theirs and 3rd party observers know even less.

Suppose that in subsequent batch payments, Emily’s change output from the previous transaction would sometimes be used to fund the next transaction. This loosely links the wallet clusters of Emily and her employees from the perspective of 3rd party observers. Emily’s coins would be in the history intersection of all of these clusters. The transactions themselves will be fairly identifiable if carried out periodically, especially if most of the output amounts imply a fixed fiat amount.

Suppose Alice CoinJoins every one of her outputs after being paid by Emily. Even though her pay is unlikely to correspond to any particular denomination useful for CoinJoining, since that was already discussed in the previous section for the following example, assume this is not an issue. Note the strength of these assumptions; this is more or less the best-case scenario for using mix-style CoinJoins, and even here there are difficulties. In reality, all of these sources of friction give rise to privacy leaks which will compound (as opposed to merely accumulating, which would still be bad).

Next, Alice would like to make a large purchase. Perhaps now that she’s saved up some coins, she needs a boat to secure her savings. Can she do this privately? If she treats her CoinJoin outputs as “anonymous” and consolidates them into a single payment, the answer is most likely “no”.

For example, Bob the boat salesman will likely learn information about the origin of Alice’s income by intersections, because Emily’s coins are predecessors of all of Alice’s coins. The more coins Alice consolidates, the more these patterns will become apparent and unambiguous from Bob’s perspective.

Similarly, Alice’s coworker Carol can also see that one of her colleagues likely bought something expensive. Carol has slightly more power to deanonymize Alice than Bob, because the structure of Emily’s transactions is clear, and she can further eliminate herself as a target, reducing some of Bob’s uncertainty.

For similar reasons, Emily can also infer that Alice made an expensive purchase. Although Alice CoinJoined the coins she received directly from Emily, the logic of an intersection attack still works with respect to the set of Alice’s coins given that Emily knows the members of this set. This is trivially true if Alice is the only employee using CoinJoin, but even if the other employees are CoinJoining, even if they mostly participate in the same transactions, the power of an intersection attack will likely allow Emily to tell the employees apart and infer that it’s Alice who made the large purchase.

Only if some other employee participated in every CoinJoin transaction that Alice made prior to the purchase will she have plausible deniability from Emily[^1]. Finally, if Emily is herself a boating accident aficionado, happened to transact with Bob, and he in turn was not careful to avoid linking his received coins, Emily will further learn that Alice’s transaction was with Bob.

While this scenario was a bit contrived to illustrate how perspectives and privileged information may vary, in reality similar and more powerful capabilities are available to counterparties and 3rd parties.

## Conclusion

For real-world transaction graphs, subject to the constraints of the UTXO model, the naive anonymity set size estimate based on counting equivalent sibling outputs can be misleading and provide a false sense of privacy, even under fairly generous assumptions. This is even more true when the adversary has access to higher-quality auxiliary information, and when attacking the privacy of multiple users, not just one specific target.

In the next post, we’ll explore some privacy failure modes across a range of structures, from PayJoin to a CoinJoin structure that takes an alternative approach to equal output amounts. For claims about privacy to be credible, any proposed solution must, of course, account for the state of the art (and not so state of the art but so far unaddressed) deanonymization attacks described in the literature, so the next post will try to define necessary, and hopefully sufficient, conditions for on chain transactions to be considered private.

[^1]: If Emily's cold storage setup involves multisig these coins be more fingerprintable too, unless it's done with e.g. MuSig or FROST in a Taproot keyspend path. Even Multiparty ECDSA, while potentially blending into P2{,W}PKH set is unlikely to match the distribution of signature sizes, and so might be distinguishable from her employee's wallet fingerprints.
