# Cost function framework for Bitcoin wallets

This document describes how score the outcomes of transacting on Bitcoin, in particular privacy outcomes. This is the basis for automating various decisions delegated by the user to the wallet.

## Coin selection with objective costs

The coin selection problem in Bitcoin is that of deciding which of the unspent transaction outputs available to a wallet should be used when constructing a new transaction. Coin selection is constrained by the desired outcomes of constructing a transaction. The simplest example of such outcome is when the user is intending to make an on-chain payment: a transaction which includes an output whose value is the payment amount, and whose `scriptPubKey` is determined by the receiver. The most basic constraint then is that the payment output is included, giving control over those funds to the receiver.

Because confirmation is needed for payment finality, the feerate of a transaction is also constrained. For a transaction to be valid, the value of the new outputs must be covered by the value of the spent outputs, and the fees paid by a transaction consist of the difference between these sums. The feerate is a transaction's fees divided by its size. For timely confirmation the feerate must provide a strong enough incentive for miners to include the given transaction in their block templates, as compared to alternative transactions they might wish to include instead.

With respect to some given feerate, the *effective value* of an unspent transaction output is its nominal value, minus the cost of the blockspace consumed by the input which spends it. Similarly, the *effective cost* of an output accounts not just for its nominal value, but also the cost of the block space required to create it.

Sometimes it's possible to closely approximate the effective cost of a payment output as the sum of the effective values of a subset of the spendable coins. However, typically the smallest sum of effective values that is larger than the sum of the effective costs will be significantly larger. A *change* output with an effective cost equal to the excess balance is then created instead of overpaying in fees.

Framed as an optimization problem, coin selection aims to minimize transaction costs while still achieving the desired outcomes (e.g. making payments). Since the decision space scales exponentially in the number of available UTXOs, a brute force search will in general be intractable requiring an approach such as [branch and bound]( https://bitcoin.stackexchange.com/questions/119919/how-does-the-branch-and-bound-coin-selection-algorithm-work).

## Internalizing expectation of future costs

The immediate costs of some action may not represent its long term consequences. Internalizing expectations of the future into the cost of an action makes optimization simpler, since decisions can be evaluated one step at a time.

Abstractly, one might considering all actions that may follow any particular state, recursively. An expected cost can be derived by first assigning a cost to each terminal state, then weighting it according to a probability distribution. Adding these costs to the cost of the actions which immediately precede the terminal states internalizes future expected costs, and this can be propagated way back up to the immediately available actions.

Unfortunately, enumerating every contingency like this, even if the depth is restricted, is not only intractable, but often hard to define. Assigning probabilities can also be tricky. Due to these challenges, in practice simplified models are instead used to internalize such future costs into the cost of the immediately available actions. Although this might not account for everything, that may eventually happen, that isn't really a goal worth pursuing so long as relative comparisons between alternatives are made possible.

### Future cost of spending (Bitcoin Core's waste metric)

At the time an output is created, the size of the input that will eventually spend it already known (or an expected size in the case of P2TR outputs). This size is independent of whatever else happens in that transaction. Reliably predicting a feerate, on the other hand, is not possible, as that is a market prediction problem.

While specific future feerates are inherently unpredictable, if at some point in time it's clear that a low feerate is sufficient for timely confirmation, then it is possible to reliably predict that at any point in the future feerate is likely to be higher. When this is the case it makes sense to spend a larger set of potentially smaller outputs, consolidating their values, because although the total blockspace required to spend a set of outputs is fixed regardless of when each output is spent, the cost can be minimized if more of this blockspace is consumed at lower feerates.

Optimizing these costs is the underlying motivation for the [*waste metric*](https://bitcoin.stackexchange.com/questions/113622/what-does-waste-metric-mean-in-the-context-of-coin-selection) used in Bitcoin Core's coin selection. This term in the cost function which governs coin selection internalizes an expected cost of spending a coin to the evaluation of the cost of its output. When the target feerate is lower than this predicted future feerate, this makes the evaluation of spending an input right now lower than this predicted future cost.

A simplified version of the waste metric (omitting some terms) is to consider some expected future feerate as effectively the zero point, by subtracting it from the target feerate at the time of coin selection. When the target feerate is lower, this will be negative, which makes *larger* transactions seem cheaper than smaller ones. The rationale for rewarding larger transactions is that the total blockspace that will eventually be consumed spending all of coins available in a wallet is essentially fixed, but what matters is simply *when* is that blockspace consumed, and at what feerate. During times of low demand for blockspace (and therefore low target feerates), coin selection will therefore tend to consolidate a fragmented wallet. When demand rises again, if coin selection must be done at the higher target feerate, since there would be fewer, higher value coins available on average, the expected transaction size at these higher target feerates will be lower, which in turn will result in a lower overall spending on fees.

### Cost of CPFP transactions

Child-pays-for-parent (CPFP) transactions spend one or more outputs of transactions that have not yet been confirmed, and at a higher feerate than of the unconfirmed transactions' average feerate. This gives miners an incentive to include the parent(s), as the more lucrative child transaction can only be confirmed after the parent(s).

From the point of view of a wallet, spending unconfirmed outputs is therefore more costly in expectation, because to do so at a higher feerate requires paying for the parent transaction(s) blockspace as well.

Arguably this is already accounted for by the waste metric future feerate parameter, but a qualitative distinction is being made here because there is more uncertainty in predicting the payments a wallet is expected to make at any point in the indefinite future, as opposed only what is due before some inflight transaction is expected to confirm.

### Utility of payments

For the purposes of this document a *payment* will mean a net transfer of funds between two parties. Transactions are a way of realizing payments, but a single transaction can perform multiple payments or even net settlement for multiparty transactions.

An *intent* is a concrete representation of the goal of create some output (or input, in which case the goal is the destruction of some unspent output) before some deadline. The deadline can refer to the transmission of a signed transaction to the recipient out of band, broadcasting the transaction, or its confirmation in a block. For simplicity, and without loss of generality, output creation intents will be assumed to correspond to payments but that isn't necessarily the case (for example funding a lightning channel). We will assume intents are made known to the wallet some time in advance of the deadline.

The change in the balance of a wallet resulting a transaction is its *objective cost*. This can be negative, for example for the case of receiving a payment. In contrast, the utility obtained from a transaction confirming may include subjective terms as well. Subjective costs inherently depend on beliefs or preferences, and are the basis for any surplus created from transactions as any redistribution of on chain funds is necessarily zero sum.

Reliably confirming transactions at the lowest possible feerate before the deadline of any payments it realizes is not feasible, because predicting future feerates is a market prediction problem. Attempting to confirm as close to the deadline as possible can incur additional costs due to the variability of fees, or risk missing the deadline. If payment deadlines are missed, the utility obtained from making the payments may be diminished. Some risk of missing the deadline or overpaying fees is always inherent.

This perspective suggests that the same action performed at different times is in fact not the same action, but two different ones, which will have different costs. However, to keep things simple we will not consider actions-at-a-point-in-time separately, but rather each action's cost evaluation will output not just a single numerical value, but a function of time, and different actions can be compared across all of time.

## Payment batching

Confirming transactions at the earliest possible time (well in advance of the deadline) is sub-optimal as it precludes any possibilities of batching payments. However, before confirmation it is possible to replace transactions by double spending at least one of its output in a transaction which is more attractive to miners (which also diminishes from the importance of introducing any CPFP liability). This is known as replace-by-fee (RBF), and multiple policies for allowing this, some defunct, have existed over the years.

A reasonable strategy that utilizes RBF for batching is to simply broadcast a transaction which underpay fees as soon as a payment becomes known, and then replace the transaction with progressively higher feerate transactions, growing the batch of payments with each such replacement. This conserves blockspace, the blockspace increase of another payment is primarily just the cost of an additional output. If some subsequent transaction is much more urgent than inflight ones, then it of course can also be realized in a separate, higher feerate transaction, in order to avoid paying for the entire batch at the higher feerate.

This batching strategy can reduce costs, minimizing the opportunity costs of the eager but naive strategy (successfully confirming before the deadline precludes RBF based batching) or the risk of missing deadlines in the lazier one. Unfortunately this RBF-eager strategy also leaks a lot more information about the payments made and the wallet making them than simply posting the full batch as late as possible (for example as discussed in [this paper](https://arxiv.org/pdf/2303.01012)). A lazy strategy will make the same batching possible without such leaks, at the cost of forgoing any low fee opportunities that may be available well in advance of the earliest deadline.

## Privacy Liabilities

Whether or not one should broadcast eagerly and then bump fees, or wait in order to limit how much information is revealed by fee bumping depends on the harms from the loss of privacy outweigh the expected savings from broadcasting earlier.

Unilaterally spending more than one output reveals to the adversary, based on the *common input ownership* or *multi-input* heuristic, that they are likely to be owned by the same entity. More broadly, all transactions necessarily reveal which coins they spend, the total amount involve, the values of the inputs and outputs, script types used, and a number of *wallet fingerprints* such as the value of `nLocktime` or details of signature encoding. This information is useful for wallet clustering ([1](https://spiralbtc.substack.com/p/the-scroll-2-wallet-clustering-basics), [2](https://spiralbtc.substack.com/p/the-scroll-3-a-brief-history-of-wallet), [3](https://spiralbtc.substack.com/p/the-scroll-4-intersection-attacks)), a cornerstone of Bitcoin chain analysis and deanonymization.

The adversary is anyone who might be attempting to deanonymize the user. This can be a third party or a counterparty. In some cases information linking several coins may already be known to the adversary. For example, suppose a customer makes one payment to a merchant in an on-chain transaction, creating a change output, and then eventually spends that change output to make another payment to the same merchant. If these payments are already linkable, for example because they are both associated with the same email address, then no further information is revealed to the merchant by spending a coin that it already knows belongs to that customer.

On the other hand it may be the case that two payments are made by the same customer to the same merchant, but no information with which the merchant could link these payments is available. In such cases the appropriate behavior might be to deliberately avoid any coins linked to the previous payment when making the later one.

The worst case for this kind of leakage, in terms of how much information is revealed in a single transaction, is when the entire wallet's balance is spent in a single transaction. This is problematic not just because it links all coins together but also because it reveals the wallet's total balance, potentially aiding in additional analysis (such as correlating this amount to past transactions that aren't unambiguously linked to it).

Let's momentarily ignore both the severity of the harm of such privacy leaks (assume it's just some fixed penalty), as well as the risk, i.e. the probability that liquidating the entire wallet is necessary (for example when under duress, in response to a security incident, or when needing to make an urgent payment for an amount close to the available balance). What then determines the cost is how much information is leaked. Considering this potential contingency after every wallet state, and then internalizing the cost into the cost of the transaction which results in that state implicitly encodes the implicit goal of privacy enhancing transactions, which is to leave the wallet in a state where the harm of any such liquidation is reduced, because the information leaks are minimized.

### Censorship risk

On-chain privacy techniques in Bitcoin come in two flavors: overt, or covert. Overt techniques add ambiguity in a way that is apparent, and therefore can be identified as privacy enhanced transactions (e.g. CoinJoin). Contrast this with covert techniques (e.g. CoinSwap), which aren't easily identifiable.

Both overt and covert techniques carry censorship risk. For overt techniques this is inherent, as the use of the technique is self-evident, and exchanges that may regard this as a compliance risk (which incidentally is more often the case for fraudulent exchanges) are more likely to reject or even confiscate deposits that are linkable to such techniques. For covert techniques, although the technique itself doesn't flag a deposit, it may result in counterfactual linking of the deposit funds to coins that are deemed tainted.

## Parameterizing the cost function according to user preferences

The design space of a cost function for a privacy has three main axes: improving privacy, minimizing delays, and economizing on cost, all of which trade off against each other. When considering each transaction independently although there are 3 dimensions for optimization, there are only two degrees of freedom. Meaningfully improving privacy on Bitcoin requires interaction with others, which can inherently introduce delays, or it can require improving the ambiguity of the transaction structure with the goal of frustrating analysis, and this often requires utilizing more blockspace. The sooner this is needed, the higher the fees incurred.

### Privacy sensitivity

To quantify privacy, wallet software must include some kind of privacy metric. Metrics makes it possible to measure progress, and to define stopping conditions for any privacy optimizations (which aren't costless). For example, an estimate of an anonymity set size of a coin might be one such metric. Developer provided default thresholds can allow non-expert users to choose a threshold appropriate for their threat model, on a per intent basis (distinguishing between sensitive payments and those that only require opportunistic privacy).

The metrics discussed here will attempt to ascertain how well the payments of the user blend in with those of others. Due to the limitations of Bitcoin's consensus layer (cleartext amounts, overt spend graph), multiparty transactions are necessary in order to meaningfully resist clustering. Multiparty transactions are those which involve the actions of more than one user. Although are other aspects to Bitcoin privacy, this framework is primarily concerned with on chain notions, which can be defined in terms of wallet clustering.

#### Sybil resistance

Complicating matters, since Bitcoin is permissionless it's not directly observable whether a transaction involves $n$ parties with non-trivial $n$ ($n > 2$) or not. Since only coins have identity, and there is no notion of accounts or users in the protocol, all an honest user knows definitively is which coins are under its own control vs. those that aren't. It's not possible, in general, to determine whether or not the coins that an honest does not control are all controlled by a single entity or multiple separate ones.

A *sybil* attack on a network or distributed system involves a single entity controlling many apparent identities, the closest analog of which are coins. As a component of a deanonymization attack, a sybil attack can be used to isolate the honest parties. If all actions than those of the victim are visible to the adversary, a scenario known as an $n-1$ deanonymization attack, then adversary is able to observe the victim's actions with full transparency. Unfortunately the only recourse for this kind of attack is to impose or at least account for the cost of such an attack.

When any privacy metrics are interpreted, the implied cost to the adversary of doing an $n-1$ deanonymization attack, i.e. the cost of controlling the inputs to the metrics (note: not inputs as in spent coins, but in the sense of all information that is fed into an analysis being under adversarial control), should be factored into the weight of the interpretation of the metric.

We might turning cluster analysis on its head, and as the defender attempting to detect such attacks heuristically. However, evading this only adds some overhead for the adversary, and this overhead may be very low in the case of covert techniques.

Ideally whatever the cost is, it should exceed the value to the adversary obtained by deanonymization, deterring such attacks through incentives. However, in reality the economics for targetted vs. dragnet surveillance will vary, and costs, even liquidity costs, may be far from equilibrium, so it is very hard to say what level of cost will suffice. The value of surveillance for say advertising may be more or less limited by the victim's disposable income, whereas for targets like political dissidents, significant resources might be allocated by the attacker. Ultimately this is very subjective and depends on the threat model.

What is possible to say is that this cost can be quantified concretely by accounting for the fees incurred by others in the construction of transactions which seem attractive and are used to support the analysis of some metric. With a discount rate, the age of a spent coin can be used to estimate a liquidity cost for the adversary, as in [fidelity bonds](https://gist.github.com/chris-belcher/87ebbcbb639686057a389acb9ab3e25b#cost-of-sybil-attacks).

### Payment urgency

As described in abstract terms above, a per intent deadline or confirmation target similar to the standard user experience for determining feerates can be used to control the time sensitivity of specific actions. Although imagining the cost function outputs a function of time has mathematical appeal, in practice to simplify things we can model these as piecewise linear scaling of cost function terms which are computed independently of time.

The privacy sensitivity of a transaction determines whether the preferred behavior is to execute a payment even if privacy is sacrificed as the deadline approaches, or whether it's better to miss the deadline or even forego the transaction entirely if the payment cannot be made privately. This can be modeled as divergence towards negative or positive infinity after the deadline elapses.

### Global privacy budget

Finally, a global (i.e. per wallet, not per intent or transaction) budget specified as a percentage of all externally received funds is used to normalize all metrics so that the costs of actions with different privacy outcomes are directly comparable.

This global budget limits overall spending for the purposes of privacy. This implies a lower bound for the expected harm from privacy leaks, since in specifying it the user is indicating that they wish to spend up to this amount preventing that harm. This accounts for any downsides as well, such as the censorship risk or additional resources consumed.

When coins lack any sufficient privacy (e.g. when known to a counterparty), their value should be discounted by the budget, effectively devaluing non-private wallet states. As progress is made towards satisfying the thresholds on privacy metrics, some coins will be closer to their face value, an increase in subjective value. This simplifies the cost function so it only outputs a satoshi amount, allowing subjective and objective costs to be reduced to a single number, and therefore comparisons can be made between the wallet states predicted to result from taking one action vs. another.

For example, suppose Alice set her budget to 1%. She receives a coin with value $x$. Her total budget $b_0$ is $0.01x$. The subjective balance of the wallet is $x - b_0 = 0.99x$. The wallet then automatically does a CoinJoin transaction and its subjective cost $y$ is subtracted from the budget, $b_1 = b_0 - y$. This is also deducted from the subjective balance, but due to an improvement in the privacy metrics the subjective balance increases overall (or the transaction wouldn't have been made). The coin with nominal value $x$ and subjective value $x - b_0$ has been destroyed, and replaced with a coin whose nominal value is $x - y$ and whose subjective value is at least $x - b_1$ and at most $x - y$.

## Use in multiparty protocols

In the context of a multiparty transaction construction, a fixed overhead of 10.5-12.5 vB per transaction incurs a cost can be shared with others. Since this is substantially smaller than a typical input, the savings are arguably negligible. If a cross input signature aggregation soft fork is enabled then instead of a fixed overhead, a per input overhead can additionally be shared among participants, providing a much stronger incentive than the fast diminishing fixed overhead's savings. Such savings are limited, ultimately by consensus block size limits, and practically by policy, which limits transactions to 100KvB (though this limit can be overcome by use of multisig and pre-signed transaction trees).

Subjective benefits, in particular those related to privacy metrics, can be more strongly positive sum. Since terms derived from privacy metrics are often concerned with data controlled by the other parties, this can be strongly positive sum as the actions of each user individually may benefit every other user, not just themselves, a quadratic number of opportunities to create a surplus.

Unless parties wish to censor each other, they should at the very least indifferent to the the actions of the other users. This is important for liveness, since secure transactions generally require unanimous consent which presents an inherent challenge for liveness. Therefore it makes sense to have prior agreement to avoid any actions which may result in negative utility.

For instance, suppose Alice stands to benefit from funding a lightning channel. In order to do this they need to add the appropriate output, no different than a regular output, but on its own this is insufficient to be as valuable as a unilaterally controlled input: lightning channels require backout transactions signed by the other party to the channel, and secure presigned transactions require stable transaction IDs (no malleability). For this reason if some other party to the transaction chooses to add a non SegWit input, this suddenly devalues Alice's proposed output, and she has a rational reason to avoid signing the resulting transaction.

For this reason we required that any such requirements are specified upfront and all parties agree to them prior to transaction construction. This must cover technical restrictions, such as spending outputs encumbered using `OP_CLTV` with constraining `nLocktime` field to non-overlapping intervals (i.e. one height based vs. one time based output), but also constraints on things like the feerate, nominal effective values of inputs, their script types (and/or spend types for P2TR outputs), nominal values, etc. This agreement must also distribute the net allocation of virtual bytes or weight units in the transaction to the parties involved, ensuring that the total size does not overflow.

With such a setup, it is reasonable to define honest parties' as being indifferent to others arbitrary actions. For this to be incentive compatible we must also demand that the cost function which governs the decisions made during the protocol execution are indeed monotonically decreasing in new information. The input domain of the cost function is defined over partial transactions, and so lower bounds on the information contained within the transactions, such as a subset of the inputs or the outputs (unordered), can be evaluated as well. Monotonicity ensures that the subjective costs can only decrease as additional transaction data is revealed from the other parties, allowing decisions to be made with access to partial information.

Note that this does allow the evaluation to change. For example, if one party's choice of inputs is already committed, and they then learn of the inputs of the other parties, this may change their evaluation of which set of outputs to add in the next stage of the protocol. Monotonicity ensures that this evaluation can only improve in the critical section of the protocol.
