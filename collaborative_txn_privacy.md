# Collaborative Transaction Privacy

This document examines some challenges for privacy in a variety of multiparty transaction settings, from PayJoin to CoinJoin. None of the attacks described are novel, but some of the cited results of the privacy literature originated in a different setting than Bitcoin privacy.

Common misconceptions about how privacy works on chain for such transactions paint a much rosier picture than what the published literature has shown. Unlike in cryptography, where the burden of proof for claims of security is rightfully rather high, various apologists and interested parties often promote the notion that the burden of proof should be reversed, or that addressing these problems is trivial.

This document is not concerned with providing empirical proof of the viability of different attacks, partly because some of the structures whose weaknesses are examined are still hypothetical, but mostly because of the lack of novelty, the cited works are supported by evidence and most are peer reviewed.

This document *is* concerned with defining specific failure modes, and by extension the success criteria for claims about privacy on chain. Vendors of privacy enhancing technologies, as is the norm in other industries, should be expected to address these widely understood attacks, and argue for how privacy is maintained in the face of such adversaries.

## Unilateral transaction privacy

Unilateral transactions are highly susceptible to deanonymization using clustering techniques. After address reuse, the most obvious way to cluster, or link a user's coins is the **common-input-ownership heuristic** (CIOH): a transaction that spends several inputs is evidence that one entity owns all of them, since at the protocol level signing for all of them normally requires all of their keys.[^cioh-wp][^cioh-scroll]

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef cc fill:#da817d,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  a1("input 0.5"):::ac --> tx1["transaction 1"]:::txn
  a2("input 0.3"):::ac --> tx1
  tx1 --> pay1("payment 0.6"):::bc
  tx1 --> chg1("change 0.2"):::ac
  chg1 --> tx2["transaction 2"]:::txn
  a3("input 0.4"):::ac --> tx2
  tx2 --> pay2("payment 0.5"):::cc
  tx2 --> chg2("change 0.1"):::ac
```

*CIOH links the inputs of each transaction, and change identification links the two transactions: all five blue coins merge into a single cluster.*

Practical clustering combines heuristics beyond CIOH to build a **wallet cluster**: a set of addresses and coins inferred to share one owner.[^reid-harrigan][^ron-shamir][^androulaki][^meiklejohn][^nick][^harrigan-fretter][^scroll-history]

## Collaborative transactions

A transaction that spends inputs owned by more than one user falsifies CIOH by construction. Starting with just two parties, the observable structure can have (at least) two forms.[^forms] The on-chain transaction must be compatible with the actual allocation of inputs, outputs, and payments among the participants, but might not reveal that allocation in its entirety.

The first form is a batched transaction, or a CoinJoin: two independent and balanced sub-transactions aggregated into a single transaction.

Here, a **sub-transaction** means some, but not all, of a transaction's inputs and outputs attributed to one participant's action. A more precise, probabilistic notion will be discussed below.

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#5778a4,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#e49444,color:#111,rx:12,ry:12
  classDef payA fill:#da817d,stroke:#5778a4,stroke-width:3px,color:#111,rx:12,ry:12
  classDef payB fill:#9dc5c1,stroke:#e49444,stroke-width:3px,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  ai("Alice's input 0.9"):::ac --> tx["transaction"]:::txn
  bi("Bob's input 0.3"):::bc --> tx
  tx --> pa("payment 0.5"):::payA
  tx --> cb("Bob's change 0.1"):::bc
  tx --> pb("payment 0.2"):::payB
  tx --> ca("Alice's change 0.4"):::ac
  linkStyle 0,2,5 stroke:#5778a4,stroke-width:3px
  linkStyle 1,3,4 stroke:#e49444,stroke-width:3px
```

*A batch: two independent spends aggregated, SharedCoin style. Each sub-transaction balances on its own (0.9 = 0.5 + 0.4 and 0.3 = 0.2 + 0.1).*

In the shown example although CIOH is falsified, the amounts strongly suggest one way of partitioning the transaction, and CIOH still applies within each sub-transaction separately. We will return to this form in later sections.

## Two-party payjoin

The other main form a two party transaction can take is a payjoin,[^p2ep][^bip79][^bip78][^bip77] which consists of a single payment connecting the sender's sub-transaction to the receiver's, the sender's surplus covering the receiver's sub-transaction's funding deficit.

A single payment from Alice to Bob, but Bob also contributes one of his own inputs alongside Alice's:

```mermaid
flowchart LR
  classDef alice fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bob fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  ai("Alice's input 0.9"):::alice
  bi("Bob's input 0.6"):::bob
  tx["transaction"]:::txn
  pay("Bob's output 1.1"):::bob
  chg("Alice's change 0.4"):::alice
  ai --> tx
  bi --> tx
  tx --> pay
  tx --> chg
```

*Here Alice pays Bob 0.5: Bob's 0.6 input grows into a 1.1 output. The payment amount appears nowhere on chain, and the ownership coloring is of course not part of the on-chain data either.*

CIOH, seeing two inputs, wrongly concludes one owner. There is no single unambiguous interpretation: looking at just this transaction in isolation, an analyst cannot be sure which inputs are Alice's, which output is the real payment, or even that a payjoin occurred at all rather than an ordinary two-input spend.

For privacy, a somewhat teleological but more general definition of Payjoin is a collaborative transaction that should be **indistinguishable from an ordinary single-party transaction**. The **unnecessary-input heuristics** flag an input when the remaining inputs could already fund the outputs and fees; such an input may reveal that another participant contributed it.[^uih-adamisz][^uih-ghesmati] If collaborative transactions were sufficiently common, naive application of CIOH would quickly lead to cluster collapse, forcing a more nuanced approach to clustering.

With only two parties, there are only a few interpretations, all the different ways of assigning inputs and outputs to sub-transactions attributed to Alice and Bob separately. The typical uncertainty is therefore on the order of a few bits to an external observer, even when looking only at the transaction in isolation and ignoring its context.[^payjoin-entropy]

The next few sections discuss extensions to two party payjoin, but bear in mind that as they are more difficult to analyze, the same concerns apply even more to the two party case.

Additionally, a two-party payjoin cannot provide privacy from the counterparty. Each participant can eliminate their own inputs and outputs from consideration which entails that everything else is attributable to the only other party. Privacy within a transaction requires three or more parties.

## Many senders, one receiver (NS1R)

A natural generalization is from one sender to many.[^ns1r] Several senders each contribute inputs to a single transaction that pays one common receiver, so it resembles an ordinary batched payout the receiver might have made by consolidating funds:

```mermaid
flowchart LR
  classDef s1c fill:#7993b6,stroke:#000,color:#111
  classDef s2c fill:#e9a969,stroke:#000,color:#111
  classDef s3c fill:#da817d,stroke:#000,color:#111
  classDef rc fill:#9dc5c1,stroke:#000,color:#111
  ls1(["Alice"]):::s1c -- "0.2" --> lr(["Dave"]):::rc
  ls2(["Bob"]):::s2c -- "0.3" --> lr
  ls3(["Carol"]):::s3c -- "0.7" --> lr
```

*The payment graph, which is not observable on chain.*

```mermaid
flowchart LR
  classDef s1c fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef s2c fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef s3c fill:#da817d,stroke:#000,color:#111,rx:12,ry:12
  classDef rc fill:#9dc5c1,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  r1("Dave's input 0.4"):::rc
  s1("Alice's input 0.5"):::s1c
  s2("Bob's input 0.6"):::s2c
  s3("Carol's input 0.9"):::s3c
  tx["transaction"]:::txn
  pay("Dave's output 1.6"):::rc
  c1("Alice's change 0.3"):::s1c
  c2("Bob's change 0.3"):::s2c
  c3("Carol's change 0.2"):::s3c
  r1 --> tx
  s1 --> tx
  s2 --> tx
  s3 --> tx
  tx --> c2
  tx --> pay
  tx --> c3
  tx --> c1
```

*Alice, Bob and Carol pay 0.2, 0.3 and 0.7 respectively; Dave consolidates the payments with a 0.4 input of his own. None of the payment amounts appear on chain.*

This allows more payments to be consolidated into a single receiver output, so it is cheaper than paying separately. There is also now a limited form of counterparty privacy: the receiver, seeing a pile of inputs, cannot always be sure which input belongs to which sender, giving the senders some plausible deniability.

The receiver still learns each sender's change output, because it knows each sender's payment amount and can read off what is left over. The senders gain a little cover against outsiders while handing the receiver a map of their remaining coins.

This structure can't really hide much more than that, as the change outputs will likely still link and as the number of senders grows, to leverage the savings the receiver must consolidate more aggressively which is a detectable fingerprint. Avoiding it means foregoing the fee savings and splitting the received funds into several outputs of a smaller magnitude in order to better match the distribution of the change outputs. Unfortunately, this in turn creates another liability: spending sibling outputs of the same transaction together, in addition to being wasteful, is a very unusual pattern, and should also be avoided if privacy is to be preserved.

## Many senders, many receivers (NSNR)

The two sides can instead be made symmetric. Let $n = 2m$ be the number of participants, half spending and half receiving. The transaction consists of $m$ payments between the $n$ sub-transactions, pairing sub-transactions uniquely.

```mermaid
flowchart LR
  classDef s1c fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef s2c fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef s3c fill:#da817d,stroke:#000,color:#111,rx:12,ry:12
  classDef r1c fill:#9dc5c1,stroke:#000,color:#111,rx:12,ry:12
  classDef r2c fill:#88b279,stroke:#000,color:#111,rx:12,ry:12
  classDef r3c fill:#ecd580,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  s1("Alice's input 0.9"):::s1c --> tx["transaction"]:::txn
  r3("Frank's input 0.15"):::r3c --> tx
  s2("Bob's input 0.4"):::s2c --> tx
  r1("Dave's input 0.3"):::r1c --> tx
  s3("Carol's input 0.45"):::s3c --> tx
  r2("Erin's input 0.35"):::r2c --> tx
  tx --> p2("Erin's output 0.85"):::r2c
  tx --> c3("Carol's change 0.25"):::s3c
  tx --> p1("Dave's output 0.5"):::r1c
  tx --> c1("Alice's change 0.4"):::s1c
  tx --> p3("Frank's output 0.45"):::r3c
  tx --> c2("Bob's change 0.1"):::s2c
```

*A multiparty payjoin transaction with three payments between six participants, with one input and one output per party.*

```mermaid
flowchart LR
  classDef s1c fill:#7993b6,stroke:#000,color:#111
  classDef s2c fill:#e9a969,stroke:#000,color:#111
  classDef s3c fill:#da817d,stroke:#000,color:#111
  classDef r1c fill:#9dc5c1,stroke:#000,color:#111
  classDef r2c fill:#88b279,stroke:#000,color:#111
  classDef r3c fill:#ecd580,stroke:#000,color:#111
  ls1(["Alice"]):::s1c -- "0.5" --> lr2(["Erin"]):::r2c
  ls2(["Bob"]):::s2c -- "0.3" --> lr3(["Frank"]):::r3c
  ls3(["Carol"]):::s3c -- "0.2" --> lr1(["Dave"]):::r1c
```

*The underlying payment graph, which is not observable on chain.*

A different interpretation of the same transaction might swap the candidate ownership of Alice's 0.4 change and Erin's 0.85 output:

```mermaid
flowchart LR
  classDef s1c fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef s2c fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef s3c fill:#da817d,stroke:#000,color:#111,rx:12,ry:12
  classDef r1c fill:#9dc5c1,stroke:#000,color:#111,rx:12,ry:12
  classDef r2c fill:#88b279,stroke:#000,color:#111,rx:12,ry:12
  classDef r3c fill:#ecd580,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  s1("Alice's input 0.9"):::s1c --> tx["transaction"]:::txn
  r3("Frank's input 0.15"):::r3c --> tx
  s2("Bob's input 0.4"):::s2c --> tx
  r1("Dave's input 0.3"):::r1c --> tx
  s3("Carol's input 0.45"):::s3c --> tx
  r2("Erin's input 0.35"):::r2c --> tx
  tx --> c1("Alice's change 0.85"):::s1c
  tx --> c3("Carol's change 0.25"):::s3c
  tx --> p1("Dave's output 0.5"):::r1c
  tx --> p2("Erin's output 0.4"):::r2c
  tx --> p3("Frank's output 0.45"):::r3c
  tx --> c2("Bob's change 0.1"):::s2c
```

*Under this alternative assignment, Alice's 0.9 input leaves 0.85 in change, implying a payment of only 0.05 to Erin.*

Because each participant only participates in exactly one payment, each hidden sub-transaction is related to only *one payment of one amount*. The amounts therefore still carry information. In the example, the alternative 0.05 payment may seem less plausible than the original 0.5 payment if its magnitude is atypical relative to prior on-chain payments and auxiliary context such as exchange rates, timing, fees, and wallet fingerprints. This is essentially the same logic as the unnecessary input heuristics.[^uih-adamisz][^uih-ghesmati] And if the adversary happens to know that Alice's cluster contains a smaller UTXO than the 0.9 one which still suffices for a payment of 0.05, that would be rather strong evidence in favor of the payment amount being 0.5.

## Net-settlement with cycles

Net-settlement is the most general form of multiparty payjoin. Where NSNR fixed $\frac{n}{2}$ payments among $n$ participants, net-settlement allows odd $n$ and up to $\frac{n(n-1)}{2}$ net payments to be aggregated: any participant may pay any other.

Participants settle an arbitrary set of mutual obligations in a single transaction, including cycles (e.g. Alice pays Bob, Bob pays Carol, Carol pays Alice). A participant may both pay and receive payments in the same settlement. The number of participants $n$ is in general not observable from the transaction (though in some cases it can be statistically or directly inferred from its structure).

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef cc fill:#da817d,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  ia("Alice's input 0.6"):::ac --> tx["transaction"]:::txn
  ib("Bob's input 0.2"):::bc --> tx
  ic("Carol's input 0.5"):::cc --> tx
  tx --> oc("Carol's output 0.4"):::cc
  tx --> oa("Alice's output 0.5"):::ac
  tx --> ob("Bob's output 0.4"):::bc
```

*A single settlement transaction. Only the net balances (Alice −0.1, Bob +0.2, Carol −0.1) are reflected on chain; none of the obligation amounts appear anywhere.*

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111
  classDef bc fill:#e9a969,stroke:#000,color:#111
  classDef cc fill:#da817d,stroke:#000,color:#111
  A(["Alice"]):::ac -- "0.5" --> B(["Bob"]):::bc
  B -- "0.3" --> C(["Carol"]):::cc
  C -- "0.4" --> A
```

*Three mutual obligations, including a cycle.*

Once cycles are allowed, a participant's *implied* payment balance is no longer a single, plausible magnitude amount but a signed sum of what they sent and received, which can net to anything, including near zero. This removes the discriminating power that payment amounts had in the previous scenario: once more than one payment per sub-transaction is possible, the net balance of a candidate sub-transaction is much harder to interpret.

Since net-settlement is strictly more general, if it is supported in implementations then *every* multiparty batch could in principle be a net settlement transaction even if that's not actually the case. Conversely, if the only thing actually deployed is the restricted NSNR above, users are forced back into that weaker regime where amounts still leak. The strength of the defense depends on the general form being the norm, not the exception.

Unfortunately, this is not enough for privacy. The resulting graph still has community structure. The adversary does not see only a single transaction; it sees the transaction graph, and some clustering of it (which may be based just on the graph structure, or be based on blockchain external information too). A settlement among counterparties is a slice of an economic network, and economic networks are not featureless: they have recurring relationships, and the behaviors can often follow predictable patterns.

### Sparse datasets

Deanonymization of networks with exactly this kind of structure is a well studied problem. In 2008, Narayanan and Shmatikov showed that real world high dimensional datasets are typically sparse — most records have no close neighbors in the feature space — and this sparseness makes deanonymization feasible with only a little auxiliary information, even when that information is noisy.[^ns-netflix][^ns-retro]

Any observable pattern in a cluster is potentially useful for such an analysis. These divide into *statistical* features (fee-rate habits, activity timing and time zone, value distributions) and *structural* features (the shape a cluster carves through the graph, and its links to other clusters).

**Wallet-software fingerprints** are a special case of the statistical kind: signature grinding, fee-rate selection, script and address types, nSequence and locktime conventions each vary from one wallet to the next. While some wallets randomize these, and specific entities may use more than one piece of software, fingerprint based clustering both more generally[^moser-narayanan][^kappos] and specifically in the context of payjoin[^sabouri] has thus far proven to be extremely powerful.

In principle this can be mitigated by the Sisyphean task of making all wallets behave the same, but this problem is pretty widespread, and while fixing it is a necessary precondition for clustering resistance, it is not sufficient for addressing the concern, since wallet fingerprints are not the only dimensions along which clusters can be compared for similarity.

### Social Graphs

Turning to the structural features, in subsequent work[^ns-social] the same authors showed that the vertices of two social graphs can be matched iteratively, starting from relatively small seed matching which identifies the some of the vertices of one graph with those of the other.

This builds on the sparseness exploited by the previous work. Here a "dimension" can be thought of roughly as whether some target vertex is related to some other specific vertex. In a social graph most nodes will be readily identifiable based on the identities of their neighbors. The actual result in the paper is significantly stronger, requiring only a seed of relatively few matched nodes in order to iteratively propagate the matching along the graphs. Later work by Narayanan et al generalized this further to link prediction on incomplete graphs.[^ns-linkpred]

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111
  classDef bc fill:#e9a969,stroke:#000,color:#111
  classDef cc fill:#da817d,stroke:#000,color:#111
  classDef dc fill:#9dc5c1,stroke:#000,color:#111
  classDef enc fill:#88b279,stroke:#000,color:#111
  classDef acs fill:#7993b6,stroke:#ffe234,stroke-width:4px,color:#111
  classDef bcs fill:#e9a969,stroke:#ffe234,stroke-width:4px,color:#111
  classDef amb fill:#fafafa,stroke:#777,stroke-dasharray:4 3,color:#111
  classDef ambs fill:#fafafa,stroke:#ffe234,stroke-width:4px,color:#111
  subgraph aux["auxiliary graph"]
    A(["Alice"]):::ac --- B(["Bob"]):::bc
    A --- C(["Carol"]):::cc
    B --- C
    B --- D(["Dave"]):::dc
    C --- E(["Erin"]):::enc
    D --- E
  end
  subgraph anon["anonymized graph"]
    v1(["Alice"]):::acs --- v2(["Bob"]):::bcs
    v1 --- v3(["&nbsp;?&nbsp;"]):::amb
    v2 --- v3
    v2 --- v4(["&nbsp;?&nbsp;"]):::amb
    v3 --- v5(["&nbsp;?&nbsp;"]):::amb
    v4 --- v5
    v1 --- v6(["&nbsp;?&nbsp;"]):::amb
  end
  A -.- v1
  B -.- v2
  style aux fill:none,stroke:#777
  style anon fill:none,stroke:#777
  linkStyle 13,14 stroke:#ffe234,stroke-width:3px
```

*The adversary holds two overlapping social graphs — one identified, one anonymized. The yellow correspondence edges mark the seed of confidently matched pairs, identifying their anonymous endpoints.*

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111
  classDef bc fill:#e9a969,stroke:#000,color:#111
  classDef cc fill:#da817d,stroke:#000,color:#111
  classDef dc fill:#9dc5c1,stroke:#000,color:#111
  classDef enc fill:#88b279,stroke:#000,color:#111
  classDef acs fill:#7993b6,stroke:#ffe234,stroke-width:4px,color:#111
  classDef bcs fill:#e9a969,stroke:#ffe234,stroke-width:4px,color:#111
  classDef ccs fill:#da817d,stroke:#ffe234,stroke-width:4px,color:#111
  classDef amb fill:#fafafa,stroke:#777,stroke-dasharray:4 3,color:#111
  classDef ambs fill:#fafafa,stroke:#ffe234,stroke-width:4px,color:#111
  subgraph aux["auxiliary graph"]
    A(["Alice"]):::ac --- B(["Bob"]):::bc
    A --- C(["Carol"]):::cc
    B --- C
    B --- D(["Dave"]):::dc
    C --- E(["Erin"]):::enc
    D --- E
  end
  subgraph anon["anonymized graph"]
    v1(["Alice"]):::acs --- v2(["Bob"]):::bcs
    v1 --- v3(["Carol"]):::ccs
    v2 --- v3
    v2 --- v4(["&nbsp;?&nbsp;"]):::amb
    v3 --- v5(["&nbsp;?&nbsp;"]):::amb
    v4 --- v5
    v1 --- v6(["&nbsp;?&nbsp;"]):::amb
  end
  A -.- v1
  B -.- v2
  C -. "1" .- v3
  style aux fill:none,stroke:#777
  style anon fill:none,stroke:#777
  linkStyle 13,14,15 stroke:#ffe234,stroke-width:3px
```

*The only unidentified vertex adjacent to both seeds must be Carol's, so it is matched first.*

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111
  classDef bc fill:#e9a969,stroke:#000,color:#111
  classDef cc fill:#da817d,stroke:#000,color:#111
  classDef dc fill:#9dc5c1,stroke:#000,color:#111
  classDef enc fill:#88b279,stroke:#000,color:#111
  classDef acs fill:#7993b6,stroke:#ffe234,stroke-width:4px,color:#111
  classDef bcs fill:#e9a969,stroke:#ffe234,stroke-width:4px,color:#111
  classDef ccs fill:#da817d,stroke:#ffe234,stroke-width:4px,color:#111
  classDef dcs fill:#9dc5c1,stroke:#ffe234,stroke-width:4px,color:#111
  classDef encs fill:#88b279,stroke:#ffe234,stroke-width:4px,color:#111
  classDef amb fill:#fafafa,stroke:#777,stroke-dasharray:4 3,color:#111
  classDef ambs fill:#fafafa,stroke:#ffe234,stroke-width:4px,color:#111
  subgraph aux["auxiliary graph"]
    A(["Alice"]):::ac --- B(["Bob"]):::bc
    A --- C(["Carol"]):::cc
    B --- C
    B --- D(["Dave"]):::dc
    C --- E(["Erin"]):::enc
    D --- E
  end
  subgraph anon["anonymized graph"]
    v1(["Alice"]):::acs --- v2(["Bob"]):::bcs
    v1 --- v3(["Carol"]):::ccs
    v2 --- v3
    v2 --- v4(["Dave"]):::dcs
    v3 --- v5(["Erin"]):::encs
    v4 --- v5
    v1 --- v6(["&nbsp;?&nbsp;"]):::amb
  end
  A -.- v1
  B -.- v2
  C -. "1" .- v3
  D -. "2" .- v4
  E -. "3" .- v5
  style aux fill:none,stroke:#777
  style anon fill:none,stroke:#777
  linkStyle 13,14,15,16,17 stroke:#ffe234,stroke-width:3px
```

*Each match extends the frontier: Dave's vertex is the remaining neighbor of Bob's, Erin's the remaining neighbor of Carol's. The graphs need not agree exactly — the vertex with no counterpart in the auxiliary graph simply remains unmatched.*

Suppose the adversary starts with an incomplete clustering of Bitcoin transaction outputs. While the clusters do link together some outputs, because it's incomplete for every user there may be several clusters. So long as the adversary still hasn't collected enough evidence to conclude that several clusters belong to the same user, that user still enjoys pseudonymity.

This adversary doesn't just apply CIOH blindly. When it is first observed, a transaction suspected to be a Payjoin, for example, will have four or more related clusters. Each entity will be represented by at least one input-side cluster and at least one output-side cluster. Naive CIOH would compel merging of all of the input clusters, and change identification may additionally link it to one of the outputs. Subsequent transactions will in turn link to those. The ensuing cluster collapse will of course be avoided by any competent adversary.

Starting with the transaction graph, where coins are vertices, let clusters be represented by undirected edges connecting the linked coins. By edge contraction on these edges, a sort of graph minor[^minor-nitpick] can be obtained from a given clustering, where all of the coins of a particular cluster are fused into just one vertex representing the cluster itself. The residual edges of this now multigraph correspond to transfers of Bitcoin.

Reid and Harrigan's paper[^reid-harrigan], in its discussion of clustering, introduced the notion of a user network, where vertices are users and edges represent the flows of Bitcoin between them. If the clustering is complete, and each user can be identified with just one node on the contracted graph, that is the user network. Otherwise, when the clustering is incomplete, this cluster graph is better thought of as a pseudonym graph rather than a user network. This is a social network per Shmatikov and Narayanan's definition.[^multigraph-nitpick] The statistical feature distributions of clusters reduce to attributes on the vertices, and both those and the structural features can inform the edge attributes.

In order to apply Narayanan and Shmatikov's algorithm more than one social graph is required, but the kinda sorta graph minor that can be obtained by contraction is just one such graph. But we could first partition the cluster-annotated coin graph, for example by leveraging the notion of time baked into the blockchain and splitting it into epochs. Contracting each subgraph separately, each corresponding graph minor would present as a somewhat different view of the pseudonym graph. The more active a particular user, the more likely they are to lose pseudonymity, since more data will leak. Furthermore, the more consistent their economic activity, the more stable their representation will be in the resulting graphs, because more of their relationships will be apparent. Every pair of such graphs is then, given just a few seeds (clusterings across epochs), susceptible to deanonymization using the propagation algorithm introduced by Narayanan and Shmatikov.

Although a proliferation of pseudonyms may limit the effectiveness of this approach for any particular run of the propagation algorithm, high confidence links obtained by this method can feed into other clustering heuristics. Additionally, there are more ways of partitioning the transaction graph than just by epoch. A more optimal partitioning would be, as a very crude analogy, the "opposite" of expander decomposition: instead of identifying a sparse cut that decomposes the graph into several components, each of which is a very well connected expander, the adversary decomposes the cluster graph along a high ambiguity cut, such that each component is relatively sparser, and then matching these components.

Some clustering must already have been produced by another technique for this to work, hence the starting assumption that the clustering is partial. It supplies both the annotations that make contraction possible in the first place, and provides the seed correspondence from which graph matching can propagate.

So, even when net settlements call amount based analysis into question, and the number of parties complicates things further, the nature of social networks and of the transaction graph is that over time a lot of structure will inevitably be revealed. There is an expression, I think it goes something like "show [the adversary] who your friends are, and [the adversary] will [successfully deanonymize you]".

## Equal amount CoinJoin among arbitrary peers

Every construction so far required its participants to be doing business with one another: a payment, a batch of payments, a settlement of mutual obligations.

A CoinJoin does not have this limitation.[^maxwell] The participants of an equal amount CoinJoin transaction spend their inputs, with no payment passing between them, to produce outputs of the same amount and script type.

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef cc fill:#da817d,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  classDef amb fill:#fafafa,stroke:#777,stroke-dasharray:4 3,color:#111,rx:12,ry:12
  a1("Alice's input 0.7"):::ac --> cj["CoinJoin"]:::txn
  b1("Bob's input 0.25"):::bc --> cj
  b2("Bob's input 0.15"):::bc --> cj
  c1("Carol's input 0.55"):::cc --> cj
  cj --> e1("output 0.3"):::amb
  cj --> cb("Bob's change 0.1"):::bc
  cj --> e2("output 0.3"):::amb
  cj --> cc2("Carol's change 0.25"):::cc
  cj --> e3("output 0.3"):::amb
  cj --> ca("Alice's change 0.4"):::ac
```

*The equal outputs are interchangeable, but the change outputs remain linked to the inputs by their amounts, and Bob's two inputs are linked to each other by the consolidation forced by a minimum denomination requirement.*

Because no payments are made, the peers do not need to have any economic relationship to each other. This means they can be chosen randomly from a broader population rather than from one's counterparties. While it may seem that this already confounds social-graph analysis, this type of CoinJoin is readily identifiable. A cautious adversary can decline to apply CIOH within it, leaving additional cluster pseudonyms, while still matching the implied user graphs on either side.[^ns-social] Later payments continue to expose recurring economic relationships and therefore community structure.

What it can do is introduce uncertainty about the origins of a coin, limiting the ability to perform input side clustering for any subsequent transactions as well. This slows the rate at which certainty can be gained about clustering structures, but it is not a comprehensive or robust defense, and over time such structures will generally be revealed.[^danezis][^troncoso]

Unfortunately, linking inputs to one another is practically inherent in the equal-amount approach.[^tx0] Users generally cannot choose incoming payment amounts or outgoing-payment change to match a CoinJoin denomination, so reaching that denomination often requires combining inputs and almost always produces change. This change is also relatively easy to link to the input clusters, as discussed in the next section.

Turning to the equal amount outputs, their order is presumed to be meaningless, so as long as they are unspent they are interchangeable. But this does not last indefinitely. Any spending transactions of these outputs will reveal more information about an output's ownership, through its timing, fingerprints, and other information that can be incorporated into the adversary's clustering model.

Furthermore, even though such a transaction only spends a single output, any change left from the payment will, in general, not be of a specific denomination either. In order to avoid harming the privacy of the payment transaction, this change should not be linkable to the spender's other on chain activity, but even if spent into a CoinJoin, the equal amount approach necessitates consolidating multiple such coins together, which potentially links many "anonymous" transactions to each other, and to subsequent transactions via the change from the CoinJoin.

For example, suppose Alice obtains two seemingly anonymous coins from two independent CoinJoins of the same denomination, and spends each in its own payment:

```mermaid
flowchart LR
  classDef rc fill:#9dc5c1,stroke:#000,color:#111,rx:12,ry:12
  classDef r2c fill:#88b279,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  classDef amb fill:#fafafa,stroke:#777,stroke-dasharray:4 3,color:#111,rx:12,ry:12
  cj1["CoinJoin 1"]:::txn
  cj1 --> m2("output 0.1"):::amb
  cj1 --> m3("output 0.1"):::amb
  cj1 --> m1("output 0.1"):::amb
  cj2["CoinJoin 2"]:::txn
  cj2 --> n1("output 0.1"):::amb
  cj2 --> n2("output 0.1"):::amb
  cj2 --> n3("output 0.1"):::amb
  m1 --> tx1["transaction"]:::txn
  tx1 --> p1("payment 0.03"):::rc
  tx1 --> g1("change 0.07"):::amb
  n1 --> tx2["transaction"]:::txn
  tx2 --> g2("change 0.04"):::amb
  tx2 --> p2("payment 0.06"):::r2c
```

*Two mixed coins spent independently: each payment is ambiguous, and nothing links the payments to the same user.*

Later, wanting to CoinJoin again, she consolidates the two leftover change outputs:

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef rc fill:#9dc5c1,stroke:#000,color:#111,rx:12,ry:12
  classDef r2c fill:#88b279,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  classDef amb fill:#fafafa,stroke:#777,stroke-dasharray:4 3,color:#111,rx:12,ry:12
  classDef acg fill:#7993b6,stroke:#ffe234,stroke-width:5px,color:#111,rx:12,ry:12
  cj1["CoinJoin 1"]:::txn
  cj1 --> m2("output 0.1"):::amb
  cj1 --> m3("output 0.1"):::amb
  cj1 --> m1("Alice's output 0.1"):::acg
  cj2["CoinJoin 2"]:::txn
  cj2 --> n1("Alice's output 0.1"):::acg
  cj2 --> n2("output 0.1"):::amb
  cj2 --> n3("output 0.1"):::amb
  m1 --> tx1["transaction"]:::txn
  tx1 --> p1("payment 0.03"):::rc
  tx1 --> g1("Alice's change 0.07"):::acg
  n1 --> tx2["transaction"]:::txn
  tx2 --> g2("Alice's change 0.04"):::acg
  tx2 --> p2("payment 0.06"):::r2c
  g1 --> cj3["CoinJoin 3"]:::txn
  g2 --> cj3
  b1("Bob's input 0.13"):::bc --> cj3
  cj3 --> q1("output 0.1"):::amb
  cj3 --> q2("output 0.1"):::amb
  cj3 --> q3("Alice's change 0.01"):::acg
  cj3 --> q4("Bob's change 0.03"):::bc
  linkStyle 6,8,9,10,12,13,17 stroke:#ffe234,stroke-width:4px
```

*The consolidating CoinJoin links the two change outputs, which links the two payments, and retroactively identifies Alice's outputs in both of the original CoinJoins.*

In other words, attempting to CoinJoin in order to recover the change and make it usable for private payments not only fails to achieve that goal, but also undoes the privacy of the previous transactions.

## Arbitrary amount CoinJoin

So strict adherence to the equal amount approach leaks information about linkage after the fact. Naive batching, which we glossed over, does too, even without considering the wider context of the graph.[^sudoku]

The Boltzmann link probability matrix[^boltzmann] and Maurer et al's sub-transaction model[^maurer] are two similar models. They employ a combinatorial approach: count all the ways that the transaction could be partitioned, grouping together subsets of the inputs and outputs into sub-transactions, which are assumed to be the actions of a single party in a multiparty transaction.

What exactly makes a partition a valid sub-transaction mapping is whether or not the sub-transaction is deemed plausible. In Maurer et al, the values of the inputs and the outputs must exactly cancel out, which is not sufficiently general for real world analyses. Boltzmann casts a wider net, by allowing these to vary somewhat, accounting for fees (including JoinMarket maker fees).

In these models, even if the number of coins and therefore partitions is large, if the probabilities over the partitions are far from uniform this amounts to relatively little privacy. This is typically quantified in terms of entropy.[^diaz][^serjantov-danezis][^syverson][^scroll-intersection]

When a sub-transaction mapping is underdetermined, i.e. there is more than one way to link inputs to outputs in separate sub-transactions, then there is ambiguity as to how to link the coins of those mutually exclusive interpretations. This can be achieved overtly by choosing output values to generate many possibilities.[^radix]

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  b1("Bob's input 2"):::bc --> cj["Bad CoinJoin"]:::txn
  a1("Alice's input 0.3"):::ac --> cj
  b2("Bob's input 5"):::bc --> cj
  a2("Alice's input 0.1"):::ac --> cj
  cj --> o1("Alice's output 0.4"):::ac
  cj --> o2("Bob's output 7"):::bc
```

*Carelessly chosen values are no better than a naive batch: the only sub-transaction mapping consistent with the amounts is 0.1 + 0.3 = 0.4 and 2 + 5 = 7, so a subset sum analysis fully partitions the transaction.*

```mermaid
flowchart LR
  classDef txn fill:#444,stroke:#000,color:#fff
  classDef amb fill:#fafafa,stroke:#777,stroke-dasharray:4 3,color:#111,rx:12,ry:12
  b1("input 0.1"):::amb --> cj["CoinJoin"]:::txn
  a2("input 0.4"):::amb --> cj
  b2("input 0.2"):::amb --> cj
  b3("input 0.5"):::amb --> cj
  a1("input 0.3"):::amb --> cj
  cj --> o1("output 0.7"):::amb
  cj --> o2("output 0.8"):::amb
```

*With values chosen to be underdetermined, three distinct mappings balance: the 0.7 output can be funded by 0.3 + 0.4, by 0.2 + 0.5, or by 0.1 + 0.2 + 0.4, with the remaining inputs funding the 0.8 output. Across these readings — and the single-owner one — no input is linked to either output.*

Alternatively, the assumption of the model itself can be invalidated. This is exactly the line of reasoning from the discussion leading up to net-settlement transactions. There is no technical reason why net-settlements between economically related users should not also be possible within such a protocol that also lets strangers be parties to the same transaction. And indeed economically related users who settle in this way can also better conceal their business relationships when they do that in the context of a broader transaction.

Unfortunately, something that is omitted by both models but which should hopefully be apparent based on the above, is that the adversary can incorporate information from the surrounding context of the graph to its sub-transaction analysis, not just the input and output values. So while net-settlement can improve the resistance to analysis, as can the overt structural ambiguity of transactions with carefully chosen output values, they are no panacea.

## Taking provenance into account

Enumerating the possible points of origin of the funds of a particular coin is fairly intuitive based on the graph structure.[^kelen-seres] The entropy of the probability distribution of this candidate set can grow fairly quickly by CoinJoining, especially if an effort is made to diversify peer selection.

However, it can also decay rather quickly. Suppose the adversary successfully deanonymizes some auxiliary user, this can have two very different outcomes:

- The coins of that user are eliminated as linking candidates when attempting to deanonymize the target user. This is an additive decay of privacy.
- In addition, the eliminated coins form the boundary between regions of the transaction graph, fracturing it. This is a multiplicative decay of privacy, the adversary can make progress at an exponential rate when this is the case.

Merely quantifying the entropy at a point in time does not account for how it may decay over time. And even if it did, it's impossible to account for any private information the adversary may have.

For example, a chain analysis vendor with access to KYC information may have sufficiently granular data to be operating in the exponential decay regime for graphs which seemingly imply high entropy.

## Robust connectivity

If the CoinJoin graph is *robustly connected*[^flow], then no small cut separates any output from the mass of its candidate origin coins. Stated differently, every output is connected to its candidate origins by multiple disjoint paths.

This safety margin delays the brittle cliff-edge of exponential decay, extending the duration of the additive decay regime, by requiring the adversary to deanonymize a much larger proportion of users before divide and conquer tactics start coming into play.

But when two post-CoinJoin outputs are linked, on chain or otherwise, this makes **intersection attacks**[^goldfeder][^scroll-intersection] possible. In such attacks, we take the candidate origins of these now linked coins, and check for any overlaps.

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111
  classDef bc fill:#e9a969,stroke:#000,color:#111
  classDef cc fill:#da817d,stroke:#000,color:#111
  classDef dc fill:#9dc5c1,stroke:#000,color:#111
  classDef enc fill:#88b279,stroke:#000,color:#111
  classDef txn fill:#444,stroke:#000,color:#fff
  classDef amb1 fill:#fdf6ec,stroke:#777,stroke-dasharray:4 3,color:#111,rx:12,ry:12
  classDef amb2 fill:#edf5f5,stroke:#777,stroke-dasharray:4 3,color:#111,rx:12,ry:12
  B(["Bob's cluster"]):::bc --> cj1
  C(["Carol's cluster"]):::cc --> cj1
  A(["Alice's cluster"]):::ac --> cj1["CoinJoin 1"]:::txn
  A --> cj2["CoinJoin 2"]:::txn
  D(["Dave's cluster"]):::dc --> cj2
  E(["Erin's cluster"]):::enc --> cj2
  cj1 --> x1("Alice, Bob or Carol?"):::amb1
  cj1 --> x2("Alice, Bob or Carol?"):::amb1
  cj1 --> x3("Alice, Bob or Carol?"):::amb1
  cj2 --> y1("Alice, Dave or Erin?"):::amb2
  cj2 --> y2("Alice, Dave or Erin?"):::amb2
  cj2 --> y3("Alice, Dave or Erin?"):::amb2
```

*The adversary's view while the CoinJoin outputs remain unspent: six outputs in two equivalence classes, each output ambiguous among its CoinJoin's participants.*

```mermaid
flowchart LR
  classDef txn fill:#444,stroke:#000,color:#fff
  classDef amb fill:#fafafa,stroke:#777,stroke-dasharray:4 3,color:#111,rx:12,ry:12
  classDef aci fill:#7993b6,stroke:#e9a969,stroke-width:8px,color:#000,font-weight:bold
  classDef bc1 fill:#e9a969,stroke:#ffe234,stroke-width:2px,color:#111
  classDef cc1 fill:#da817d,stroke:#ffe234,stroke-width:2px,color:#111
  classDef aco1 fill:#7993b6,stroke:#ffe234,stroke-width:3px,color:#111,rx:12,ry:12
  classDef dc2 fill:#9dc5c1,stroke:#ff7a76,stroke-width:2px,color:#111
  classDef enc2 fill:#88b279,stroke:#ff7a76,stroke-width:2px,color:#111
  classDef aco2 fill:#7993b6,stroke:#ff7a76,stroke-width:3px,color:#111,rx:12,ry:12
  B(["Bob's cluster"]):::bc1 --> cj1
  C(["Carol's cluster"]):::cc1 --> cj1
  A(["Alice's cluster"]):::aci --> cj1["CoinJoin 1"]:::txn
  A --> cj2["CoinJoin 2"]:::txn
  D(["Dave's cluster"]):::dc2 --> cj2
  E(["Erin's cluster"]):::enc2 --> cj2
  cj1 --> xo1("Bob or Carol?"):::amb
  cj1 --> x("Alice's output"):::aco1
  cj1 --> xo2("Bob or Carol?"):::amb
  cj2 --> y("Alice's output"):::aco2
  x --> sp["transaction"]:::txn
  y --> sp
  cj2 --> yo1("Dave or Erin?"):::amb
  cj2 --> yo2("Dave or Erin?"):::amb
  linkStyle 0,1 stroke:#ffe234,stroke-width:2px
  linkStyle 2,7,10 stroke:#ffe234,stroke-width:5px
  linkStyle 4,5 stroke:#ff7a76,stroke-width:2px
  linkStyle 3,9,11 stroke:#ff7a76,stroke-width:5px
```

*Alice's spend links one output from each class. Tracing each input back — from spent output, through its creating CoinJoin, and to the pre-CoinJoin input clusters — gives the two antecessor sets, highlighted in yellow and red. These overlap only at Alice's cluster, highlighted as the one node belonging to both: the intersection identifies her, and by elimination also narrows the remaining outputs' candidate sets: CoinJoin 1's to Bob or Carol, CoinJoin 2's to Dave or Erin.*

A successful intersection makes progress at a rate that is exponential in the number of observations available to the adversary. If the set is of size $n$, then $O(\log n)$ observations — each intersection cutting the candidate set down by a constant factor — may suffice to pinpoint a single element, whereas striking candidates off of the list one at a time in a naive process of elimination may require $O(n)$ observations.

This holds unless the size of the symmetric difference between antecessor sets is bounded by a constant, i.e. the antecessor sets of linked coins are very similar, because the size of the intersection is similar to the size of the intersected sets. This attack is powerful because in most cases that isn't the case, and the size of the intersection will usually be significantly smaller.

It's also important to bear in mind that the candidate origins are not coins, but rather clusters, so the objects being intersected needn't be connected on the transaction graph for the adversary to notice an overlap. This is particularly concerning because the clusters being intersected are the pre-CoinJoin ones, where presumably privacy is inherently weak. It's also worth emphasizing that the change outputs of equal amount CoinJoins are part of these clusters as well.

Next, consider an adversary who is also a counterparty. For example, an ATM in some remote location that sells coins to a user in exchange for cash, and later receives funds from descendants of those coins. Such a counterparty knows, from its own records, exactly which coins it paid out and can observe when descendants of those coins are sold back to it. Connectivity to a crowd of strangers over the internet does little against this, because none of those strangers are likely to have transacted with the ATM, and the CoinJoin does not sever the link from a coin to its past. By the same logic of intersection attacks, privacy loss arising from consolidation of more than one input doesn't just add up, it compounds. This is known as the **Eve-Alice-Eve** threat model.

## Own-origin robustness

The privileged counterparty knows one endpoint because it *is* the origin, so the property is stated relative to that origin. It demands that a coin have many plausible, counterfactual paths back to the user's own antecedent coins.

Suppose Alice withdraws from that ATM, and that is her only means of obtaining Bitcoin. She then CoinJoins with Bob. If one of those coins is then returned to the ATM, its operator can conclude that it is likely Alice.

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef ec fill:#b996b2,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  classDef amb fill:#fafafa,stroke:#777,stroke-dasharray:4 3,color:#111,rx:12,ry:12
  atm(("ATM")):::ec -. "withdrawal" .-> a0("Alice's coin"):::ac
  a0 --> cj["CoinJoin<br/>Alice + Bob"]:::txn
  b0("Bob's coin"):::bc --> cj
  cj --> x1("Alice or Bob?"):::amb
  cj --> x2("Alice or Bob?"):::amb
  x1 --> deposit["deposit"]:::txn
  deposit --> atmd("ATM's output"):::ec
```

*Taken in isolation the deposited coin is ambiguous: it could be Alice's or Bob's.*

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef ec fill:#b996b2,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  classDef acg fill:#7993b6,stroke:#ffe234,stroke-width:5px,color:#111,rx:12,ry:12
  atm(("ATM")):::ec -. "withdrawal" .-> a0("Alice's coin"):::acg
  a0 --> cj["CoinJoin<br/>Alice + Bob"]:::txn
  b0("Bob's coin"):::bc --> cj
  cj --> x1("Alice's output"):::acg
  cj --> x2("Bob's output"):::bc
  x1 --> deposit["deposit"]:::txn
  deposit --> atmd("ATM's output"):::ec
  linkStyle 0,1,3,5,6 stroke:#ffe234,stroke-width:4px
```

*But in this minimal example the ambiguity is thin. The ATM can conclude with reasonable certainty that the deposit is Alice's, because it is much more likely to get repeated business from her than it is for her to randomly interact with Bob just before Bob happens to use the ATM.*

Consolidation makes the ATM's job easier still. Suppose Alice withdraws two coins, mixes each once with a different peer, and then spends the two mixed outputs together:

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef cc fill:#da817d,stroke:#000,color:#111,rx:12,ry:12
  classDef ec fill:#b996b2,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  classDef acg fill:#7993b6,stroke:#ffe234,stroke-width:5px,color:#111,rx:12,ry:12
  atm(("ATM")):::ec -. "withdrawal" .-> a0("Alice's coin"):::acg
  atm -. "withdrawal" .-> a0b("Alice's other coin"):::acg
  b0("Bob's coin"):::bc --> cj1
  a0 --> cj1["CoinJoin 1<br/>Alice + Bob"]:::txn
  cj1 --> o2("Bob's output"):::bc
  cj1 --> o1("Alice's output"):::acg
  a0b --> cj2["CoinJoin 2<br/>Alice + Carol"]:::txn
  c0("Carol's coin"):::cc --> cj2
  cj2 --> o3("Alice's output"):::acg
  cj2 --> o4("Carol's output"):::cc
  o1 --> deposit["deposit"]:::txn
  o3 --> deposit
  deposit --> atmd("ATM's output"):::ec
  linkStyle 0,1,3,5,6,8,10,11,12 stroke:#ffe234,stroke-width:4px
```

*Each CoinJoin output on its own is ambiguous, but only Alice is consistent with both inputs of the consolidation, so the deposit identifies her. Additional inputs amplify the ATM's observing power exponentially.*

Suppose instead that Bob CoinJoins with another user, Carol, and then Carol CoinJoins with Alice.

If *Carol* were to use the ATM at that point, her coin has inherited Alice's provenance, which may cause the ATM to incorrectly conclude that it is Alice which is using it. By symmetry, if it was Alice who did that, she gets some degree of plausible deniability.

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef cc fill:#da817d,stroke:#000,color:#111,rx:12,ry:12
  classDef ec fill:#b996b2,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  atm(("ATM")):::ec -. "withdrawal" .-> a0("Alice's coin"):::ac
  a0 --> cj1["CoinJoin 1<br/>Alice + Bob"]:::txn
  b0("Bob's coin"):::bc --> cj1
  cj1 --> a1("Alice's output"):::ac
  cj1 --> b1("Bob's output"):::bc
  b1 --> cj2["CoinJoin<br/>Bob + Carol"]:::txn
  c0("Carol's coin"):::cc --> cj2
  cj2 --> c1("Carol's output"):::cc
  cj2 --> b2("Bob's output"):::bc
  a1 --> cj3["CoinJoin 3<br/>Carol + Alice"]:::txn
  c1 --> cj3
  cj3 --> o1("Alice's output"):::ac
  cj3 --> o2("Carol's output"):::cc
  o2 --> deposit["deposit"]:::txn
  deposit --> atmd("ATM's output"):::ec
```

*In this scenario it *is* actually Carol who deposits, and the funds were never in Alice's possession, but its history is interwoven with Alice's through the CoinJoins, which by the same logic would cause the adversary to mistakenly conclude that it is Alice.*

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef cc fill:#da817d,stroke:#000,color:#111,rx:12,ry:12
  classDef ec fill:#b996b2,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  classDef amb fill:#fafafa,stroke:#777,stroke-dasharray:4 3,color:#111,rx:12,ry:12
  atm(("ATM")):::ec -. "withdrawal" .-> a0("Alice's coin"):::ac
  a0 --> cj1["CoinJoin 1<br/>Alice + Bob"]:::txn
  b0("Bob's coin"):::bc --> cj1
  cj1 --> a1("Alice or Bob?"):::amb
  cj1 --> b1("Alice or Bob?"):::amb
  b1 --> cj2["CoinJoin<br/>Bob + Carol"]:::txn
  c0("Carol's coin"):::cc --> cj2
  cj2 --> c1("Alice, Bob or Carol?"):::amb
  cj2 --> b2("Alice, Bob or Carol?"):::amb
  a1 --> cj3["CoinJoin 3<br/>Carol or Bob + Alice"]:::txn
  c1 --> cj3
  cj3 --> o1("Alice, Bob or Carol?"):::amb
  cj3 --> o2("Alice, Bob or Carol?"):::amb
  o2 --> deposit["deposit"]:::txn
  deposit --> atmd("ATM's output"):::ec
```

*The same transactions from the ATM's point of view: after CoinJoin 3 the two outputs are equivalent — whichever one is deposited has plausible paths back to the dispensed coin, directly through CoinJoin 3 or via Bob through CoinJoins 1 and 2 — so the ATM cannot tell Alice returning from either Bob or Carol.*

Repeated CoinJoins can spread Alice's coins' provenance fingerprint to other users' coins while spreading their features to hers. This allows her to build up to a quantifiable anonymity set.

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef cc fill:#da817d,stroke:#000,color:#111,rx:12,ry:12
  classDef dc fill:#9dc5c1,stroke:#000,color:#111,rx:12,ry:12
  classDef enc fill:#88b279,stroke:#000,color:#111,rx:12,ry:12
  classDef fc fill:#ecd580,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  classDef txni fill:#444,stroke:#5778a4,stroke-width:6px,color:#fff
  classDef ai fill:#7993b6,stroke:#5778a4,stroke-width:6px,color:#111,rx:12,ry:12
  classDef bi fill:#e9a969,stroke:#5778a4,stroke-width:6px,color:#111,rx:12,ry:12
  classDef ci fill:#da817d,stroke:#5778a4,stroke-width:6px,color:#111,rx:12,ry:12
  classDef di fill:#9dc5c1,stroke:#5778a4,stroke-width:6px,color:#111,rx:12,ry:12
  a0("Alice's coin"):::ac --> cj1["CoinJoin<br/>Alice + Bob"]:::txni
  b0("Bob's coin"):::bc --> cj1
  cj1 --> a1("Alice's output"):::ai
  cj1 --> b1("Bob's output"):::bi
  b1 --> cj2["CoinJoin<br/>Bob + Carol"]:::txni
  c0("Carol's coin"):::cc --> cj2
  cj2 --> b2("Bob's output"):::bi
  cj2 --> c1("Carol's output"):::ci
  d0("Dave's coin"):::dc --> cjx1["CoinJoin<br/>Dave + Erin"]:::txn
  e0("Erin's coin"):::enc --> cjx1
  cjx1 --> d1("Dave's output"):::dc
  cjx1 --> e1("Erin's output"):::enc
  c1 --> cj3["CoinJoin<br/>Carol + Dave"]:::txni
  d1 --> cj3
  cj3 --> c2("Carol's output"):::ci
  cj3 --> d2("Dave's output"):::di
  e1 --> cjx2["CoinJoin<br/>Erin + Frank"]:::txn
  f0("Frank's coin"):::fc --> cjx2
  cjx2 --> e2("Erin's output"):::enc
  cjx2 --> f1("Frank's output"):::fc
  linkStyle 0,2,3,4,6,7,12,14,15 stroke:#5778a4,stroke-width:3px
```

*Coins are colored by their true owner; a thick blue border marks the coins descending from Alice's. Dave's coin picks up the fingerprint when mixing with Carol, for example.*

As this set grows, Alice's chances of CoinJoining her actual funds with such a coin increase with time. If Alice participates in enough CoinJoins so that eventually inputs to the next CoinJoin are already descendants of her prior coin and many such counterfactual paths exist, that can provide privacy even against an adversarial counterparty, which by finding its own coins in the intersection is able to cluster much more reliably than a 3rd party observer relying on heuristics.

```mermaid
flowchart LR
  classDef ac fill:#7993b6,stroke:#000,color:#111,rx:12,ry:12
  classDef bc fill:#e9a969,stroke:#000,color:#111,rx:12,ry:12
  classDef cc fill:#da817d,stroke:#000,color:#111,rx:12,ry:12
  classDef dc fill:#9dc5c1,stroke:#000,color:#111,rx:12,ry:12
  classDef enc fill:#88b279,stroke:#000,color:#111,rx:12,ry:12
  classDef fc fill:#ecd580,stroke:#000,color:#111,rx:12,ry:12
  classDef gc fill:#b9a0d8,stroke:#000,color:#111,rx:12,ry:12
  classDef txn fill:#444,stroke:#000,color:#fff
  classDef txni fill:#444,stroke:#5778a4,stroke-width:6px,color:#fff
  classDef ai fill:#7993b6,stroke:#5778a4,stroke-width:6px,color:#111,rx:12,ry:12
  classDef bi fill:#e9a969,stroke:#5778a4,stroke-width:6px,color:#111,rx:12,ry:12
  classDef ci fill:#da817d,stroke:#5778a4,stroke-width:6px,color:#111,rx:12,ry:12
  classDef di fill:#9dc5c1,stroke:#5778a4,stroke-width:6px,color:#111,rx:12,ry:12
  classDef ei fill:#88b279,stroke:#5778a4,stroke-width:6px,color:#111,rx:12,ry:12
  classDef fi fill:#ecd580,stroke:#5778a4,stroke-width:6px,color:#111,rx:12,ry:12
  classDef gi fill:#b9a0d8,stroke:#5778a4,stroke-width:6px,color:#111,rx:12,ry:12

  a0("Alice"):::ac --> cj1[" "]:::txni
  b0("Bob"):::bc --> cj1
  cj1 --> a1("Alice"):::ai
  cj1 --> b1("Bob"):::bi
  a1 --> cj6[" "]:::txni

  b1 --> cj2[" "]:::txni
  c0("Carol"):::cc --> cj2
  cj2 --> c1("Carol"):::ci
  cj2 --> b2("Bob"):::bi
  d0("Dave"):::dc --> cjx1[" "]:::txn
  e0("Erin"):::enc --> cjx1
  cjx1 --> d1("Dave"):::dc
  cjx1 --> e1("Erin"):::enc
  c1 --> cj3[" "]:::txni
  d1 --> cj3
  cj3 --> d2("Dave"):::di
  cj3 --> c2("Carol"):::ci
  e1 --> cjx2[" "]:::txn
  f0("Frank"):::fc --> cjx2
  cjx2 --> e2("Erin"):::enc
  cjx2 --> f1("Frank"):::fc

  b2 --> cj4[" "]:::txni
  e2 --> cj4
  cj4 --> b3("Bob"):::bi
  cj4 --> e3("Erin"):::ei

  d2 --> cj5[" "]:::txni
  f1 --> cj5
  cj5 --> d3("Dave"):::di
  cj5 --> f2("Frank"):::fi

  b3 --> cj6
  d3 --> cj6
  g0("Grace"):::gc --> cj6
  cj6 --> a2("Alice"):::ai
  cj6 --> b4("Bob"):::bi
  cj6 --> d4("Dave"):::di
  cj6 --> g1("Grace"):::gi

  linkStyle 0,2,3,4,5,7,8,13,15,16,21,23,24,25,27,28,29,30,32,33,34,35 stroke:#5778a4,stroke-width:4px
```

*Continuing the preceding graph, Bob and Dave spend marked outputs along separate branches. As more marked outputs circulate, more branches can spread Alice's deep feature. In Alice's next four-input CoinJoin, Bob's and Dave's inputs also descend from her original coin; only Grace's does not.*

Let's call provenance specific structural features deep features. When spending more than one coin, if the coins have similarly distributed deep features then they will have similar antecessor sets.

In order to quantify an anonymity set size, Alice can count the inputs belonging to other users that already share her coins' deep features,[^proximity], i.e. inputs that counterfactually trace back to her origin coins. Many such counterfactual paths imply that intersected candidate sets shrink only at a linear rate, because Alice's coins would also be in the intersections arising from post CoinJoin linking of coins that have nothing to do with her.

This is the most conservative notion of on chain privacy described in this document. CoinJoin transactions that have the structural properties discussed, where peers are chosen so as to satisfy these robustness properties, are required in order to frustrate a real world deanonymization adversary, because without them the information required to deanonymize is often revealed in the transaction graph itself, which already is very harmful for privacy, fungibility and censorship resistance, but perhaps catastrophically it is augmented by many other privacy loss vectors, such as blockchain indexing services for light clients, KYC information, leaks from data breaches, transport level information like IP addresses, etc.

Note however that this still requires that the other ATM users also CoinJoin; otherwise Alice's history will still be unique. Even if she tries to obscure this using "normal looking" transactions, the ATM could still distinguish Alice based on the fact that these transactions descend from the CoinJoin subgraph, simply because those of the other users do not. Determining whether she is the only such user is something that can be judged based on evidence like temporal patterns (correlations or periodic activity). Such patterns are more easily discernible when there are clearly delineated CoinJoin-using and non-CoinJoin-using populations in the transaction graph as a whole.

## Censorship resistance vs. privacy tradeoffs and complementarity

The constructions discussed here form a spectrum: unilateral transactions, two-party payjoins, many senders and receivers, net-settlement, and market-based coinjoin among strangers, constructed with increasing degrees of connectivity robustness.

One end offers censorship resistance and generally weak privacy; the other offers stronger privacy guarantees at the cost of an overt fingerprint.

Note that this does not refer to on-chain censorship resistance specifically, we must take for granted that at least some miners will include CoinJoin transactions for any of this to work. The relevant risk is censorship by businesses: an exchange or custodian that refuses, freezes, or discounts coins by their history, and in particular if their history uses privacy enhanced transactions.[^scam-exchanges]

This is not zero sum. The two ends then reinforce each other. The censorship resistant end gains fungibility and can better resist clustering from being interwoven with the well-connected structure. The robust anonymity end gains censorship resistance by not being an insular sub-economy that rarely touches ordinary transactions.

Multiparty transactions that don't overtly optimize for an underdetermined sub-transaction mapping can still provide ambiguity, with their susceptibility to censorship based on public information largely reduced to their proximity to the overtly privacy enhancing ones.

If this structural feature spectrum is realized on chain, the distribution of deep features labeling a user's output has a better chance of matching the deep feature distributions of more superficially similar but unrelated coins. Superficially similar coins are those with which it shares statistical features (like value distribution or wallet software fingerprints) or more general structural features (e.g. size of the containing transaction).

Recall that sparseness is a requirement for Narayanan and Shmatikov's results. In today's transaction graph, cluster features, both statistical and more importantly structural, are very likely to be unique because there doesn't exist any wallet software that deliberately blends the structural features. Wallet fingerprints and other statistical features of clusters might be not be sparse on their own. But if the social network structure is recoverable from the transaction graph, that will be enough for the adversary to deanonymize most of the graph. Auxiliary information like KYC data might be the basis of such a seed, but just high degree nodes on the social graph, such as well known mining pools, exchanges and payment processors may suffice.

Sufficiently ambiguous collaborative transactions would produce coins that share the *sum* of their inputs' deep feature vectors, blending together their fingerprints. This undermines sparseness by construction. The more widely these sums spread, the less sparse the feature vectors of all coins become. For the transaction graph structure to actually be connected in this way requires deliberate effort, but there is no fundamental barrier to this occurring.

This seems to suggest that some of today's often misleading, but widely held beliefs or intuitions about on chain privacy and fungibility would be more accurate if such mixing of deep features were pervasive, and the boundary between such transactions and "normal" transactions was obscured by a network of covert transactions, none of them completely disconnected from the CoinJoin graph.

In other words, in a world where some users CoinJoin, and take care to construct transaction graphs with sufficiently many disjoint counterfactual paths as discussed above, and where some users engage in net settlement transactions, or 2 party PayJoins, and crucially where these subgraphs are all intertwined then the combinatorial explosion of graph based features, which today can reveal a lot of information to the adversary, will be rendered mostly inert. By construction, this would no longer satisfy the conditions for Narayanan and Shmatikov's algorithms.

Until such time, be skeptical of claims that PayJoin or even CoinJoin provide privacy against a competent adversary. Especially if it is well funded and is widely known to have access to a trove of high quality auxiliary information. And even if this does become a reality, please remember that it wouldn't address the auxiliary information concern, nor thwart any as-of-yet undiscovered analyses that perhaps exploit some subtler leaks.

[^cioh-wp]: The common-input-ownership observation appears in passing in the Bitcoin whitepaper: S. Nakamoto, [*Bitcoin: A Peer-to-Peer Electronic Cash System*](https://bitcoin.org/bitcoin.pdf)

[^cioh-scroll]: For an informal introduction to wallet clustering, see [The Scroll #2, Wallet Clustering Basics](https://spiralbtc.substack.com/p/the-scroll-2-wallet-clustering-basics)

[^forms]: The two-party case is not exhaustive; the space of collaborative transaction forms is larger, in particular lightning is probably the most widespread type of two-party transaction. See [The Scroll #5, The Many Faces of CoinJoins](https://spiralbtc.substack.com/p/the-scroll-5-the-many-faces-of-coinjoins)

[^payjoin-entropy]: Roughly 1.58 bits is the best possible case for a two-input, two-output transaction, which is a rather typical shape. Counterintuitively while additional inputs seem to suggest linear growth in entropy because of the combinatorics, that can input consolidation may result in linear reduction entropy due to consolidation as a function of the in-degree of the consolidation sub-transaction. See the discussion about intersection attacks below.

[^reid-harrigan]: F. Reid and M. Harrigan, [*An Analysis of Anonymity in the Bitcoin System*](https://arxiv.org/abs/1107.4524)

[^ron-shamir]: D. Ron and A. Shamir, [*Quantitative Analysis of the Full Bitcoin Transaction Graph*](https://eprint.iacr.org/2012/584)

[^androulaki]: E. Androulaki, G. Karame, M. Roeschlin, T. Scherer, S. Capkun, [*Evaluating User Privacy in Bitcoin*](https://eprint.iacr.org/2012/596)

[^meiklejohn]: S. Meiklejohn, M. Pomarole, G. Jordan, K. Levchenko, D. McCoy, G. M. Voelker, S. Savage, [*A Fistful of Bitcoins: Characterizing Payments Among Men with No Names*](https://cseweb.ucsd.edu/~smeiklejohn/files/imc13.pdf)

[^nick]: J. Nick, [*Data-Driven De-Anonymization in Bitcoin*](https://jonasnick.github.io/papers/thesis.pdf)

[^harrigan-fretter]: M. Harrigan and C. Fretter, [*The Unreasonable Effectiveness of Address Clustering*](https://arxiv.org/abs/1605.06369)

[^moser-narayanan]: M. Möser and A. Narayanan, [*Resurrecting Address Clustering in Bitcoin*](https://arxiv.org/abs/2107.05749)
[^kappos]: G. Kappos, H. Yousaf, R. Stütz, S. Rollet, B. Haslhofer, S. Meiklejohn, [*How to Peel a Million: Validating and Expanding Bitcoin Clusters*](https://arxiv.org/abs/2205.13882)

[^scroll-history]: For a narrative history of clustering techniques, see [The Scroll #3, A Brief History of Wallet Clustering](https://spiralbtc.substack.com/p/the-scroll-3-a-brief-history-of-wallet)

[^p2ep]: [Pay-to-EndPoint (P2EP)](https://blockstream.com/2018/08/08/en-improving-privacy-using-pay-to-endpoint/)
[^bip79]: R. Havar, [BIP 79: *Bustapay :: a practical coinjoin protocol*](https://github.com/bitcoin/bips/blob/master/bip-0079.mediawiki)
[^bip78]: N. Dorier, [BIP 78: *A Simple Payjoin Proposal*](https://github.com/bitcoin/bips/blob/master/bip-0078.mediawiki)
[^bip77]: D. Gould and Y. Kogman, [BIP 77: *Async Payjoin*](https://github.com/bitcoin/bips/blob/master/bip-0077.md)

[^uih-adamisz]: AdamISZ, [payjoin / unnecessary-input-heuristic writeup](https://gist.github.com/AdamISZ/4551b947789d3216bacfcb7af25e029e)

[^uih-ghesmati]: S. Ghesmati, A. Kern, A. Judmayer, N. Stifter, and E. Weippl, [*Unnecessary Input Heuristics & PayJoin Transactions*](https://eprint.iacr.org/2022/589)

[^boltzmann]: LaurentMT, [*Boltzmann*](https://gist.github.com/LaurentMT/d361bca6dc52868573a2), specifically the link-probability matrix.

[^ns1r]: rust-payjoin, [PR #923 (removal of the experimental NS1R implementation, with status discussion)](https://github.com/payjoin/rust-payjoin/pull/923)

[^maxwell]: G. Maxwell, [*CoinJoin: Bitcoin privacy for the real world*](https://bitcointalk.org/index.php?topic=279249)

[^maurer]: F. K. Maurer, T. Neudecker, M. Florian, [*Anonymous CoinJoin Transactions with Arbitrary Values*](https://www.researchgate.net/publication/318128387_Anonymous_CoinJoin_Transactions_with_Arbitrary_Values)

[^ns-netflix]: A. Narayanan and V. Shmatikov, [*Robust De-anonymization of Large Sparse Datasets*](https://arxiv.org/abs/cs/0610105) (S&P 2008; the linked arXiv version is titled *How To Break Anonymity of the Netflix Prize Dataset*)

[^ns-retro]: A. Narayanan and V. Shmatikov, [*Robust De-anonymization of Large Sparse Datasets: a Decade Later*](https://www.cs.princeton.edu/~arvindn/publications/de-anonymization-retrospective.pdf)

[^ns-social]: A. Narayanan and V. Shmatikov, [*De-anonymizing Social Networks*](https://arxiv.org/abs/0903.3276)

[^minor-nitpick]: This is not really a graph minor since there are directed edges. In fact it's not really a graph because it's got both directed and undirected edges.

[^multigraph-nitpick]: Strictly speaking their model involves a directed graph, not a multigraph, but edges are labeled with arbitrary attributes so the information about the various payments can be collected into a rich set of attributes on a single edge representing the relationship between two clusters.

[^ns-linkpred]: A. Narayanan, E. Shi, B. I. P. Rubinstein, [*Link Prediction by De-anonymization*](https://arxiv.org/abs/1102.4374)

[^sabouri]: A. Sabouri, [*How Wallet Fingerprints Damage Payjoin Privacy*](https://payjoin.org/blog/2026/03/25/wallet-fingerprints-payjoin-privacy/)

[^goldfeder]: S. Goldfeder, H. Kalodner, D. Reisman, A. Narayanan, [*When the Cookie Meets the Blockchain*](https://arxiv.org/abs/1708.04748)

[^danezis]: G. Danezis, [*Statistical Disclosure Attacks*](https://www.freehaven.net/anonbib/cache/statistical-disclosure.pdf)

[^troncoso]: C. Troncoso, B. Gierlichs, B. Preneel, I. Verbauwhede, [*Perfect Matching Disclosure Attacks*](https://www.freehaven.net/anonbib/cache/troncoso-pet2008.pdf)

[^scroll-intersection]: For an accessible treatment of entropy and intersection attacks on coinjoin anonymity sets, see [The Scroll #4, Intersection Attacks](https://spiralbtc.substack.com/p/the-scroll-4-intersection-attacks)

[^kelen-seres]: D. M. Kelen and I. A. Seres, [*Towards Measuring the Traceability of Cryptocurrencies*](https://arxiv.org/abs/2211.04259)

[^flow]: Note that being connected doesn't just mean a path can be traced along the graph, but that the flow of funds along that path appears plausible.

[^diaz]: C. Diaz, S. Seys, J. Claessens, B. Preneel, [*Towards Measuring Anonymity*](https://www.freehaven.net/anonbib/cache/Diaz02.pdf)

[^serjantov-danezis]: A. Serjantov and G. Danezis, [*Towards an Information Theoretic Metric for Anonymity*](https://bib.mixnetworks.org/pdf/serjantov2002towards.pdf)

[^tx0]: This gets worse if coins of a specific denomination are prepared before the CoinJoin, because that setup transaction is highly fingerprintable as a unilateral transaction.

[^sudoku]: K. Atlas, [*CoinJoin Sudoku*](https://www.coinjoinsudoku.com/)

[^radix]: https://colab.research.google.com/drive/1We_FvfX_Ob9BapFW3X_By9vTtxUrt3pm

[^syverson]: P. Syverson, [*Why I'm not an entropist*](https://www.freehaven.net/anonbib/cache/entropist.pdf)

[^scam-exchanges]: Unsurprisingly, the most aggressive compliance posturing has historically often come from businesses that later collapsed, namely FTX, whose executives were convicted of fraud, and BlockFi, which settled SEC charges that included materially false statements before going under in FTX's wake.

[^proximity]: Not exactly the same, since both temporal patterns and the number of hops make a difference. This can be addressed by ensuring the length of the actual path taken is consistent with the distribution of lengths of the counterfactual paths.
