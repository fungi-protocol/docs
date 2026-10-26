---
type: Specification
title: Recovery track
description: How a stalled phase of the optimistic track turns into a recovery coalition formation proposal.
status: draft
stale_after: 2026-11-06T00:00:00Z
---

<!-- cspell:words Dwork Lynch Stockmeyer APSA APSA's Baudet Brugeres CRBB Chondros Christos Croman Danezis Deligios Diamantopoulos Dolev Duan Ehud Eurocrypt Falbesoner Garay Guerraoui Haibin Haifeng Idit Ittai josibake Keidar Kelkar Kichidis Klasovita Kuznetsov Languille Mahimna Maneas mathit Maxence Mema Minghang Naor Nikos Oded Ouri Patsonakis permissioned Pieter Poupko Rachid Reiter Roussopoulos Ruomu Sisi Skoumios Somsen Sonnino Stathis Tasos texttt Tonkikh Vassilis Wonseok Wuille Yuval Zarfaoui Zhuolun Zikas antichain counterpropose mathcal mathrm operatorname paxpay precommitted semilattice -->

# Recovery track

🤖 A stalled phase can produce recovery observations in validator blocks, each signed by its validator and committing to what that validator is missing. Any participant can turn those observations into a recovery coalition formation proposal that anyone can check. The intended synchrony properties are exclusion of a faulty party without excluding an honest one, apart from the [counterparty-stall exception](#counterparty-stalls). Claims below that depend on identifying missing first- or second-round acknowledgements remain unresolved under the two-round finalization rule.

🤖 This chapter describes the recovery track ($t \lt n$). The block structure and the per-track nonce commitments are described in the [block DAG](block-dag.md) chapter. The closing of each phase is described in the [optimistic track](optimistic-track.md#phase-closure) chapter ($t = n$). Dissemination and set reconciliation are out of scope here.

🤖 Several names in this chapter and in [phase closure](optimistic-track.md#phase-closure) are placeholders, chosen only so the rules can be stated: *per-input message*, *quorum mode*, *own-view mode*, *deny list*, *late pass*, *coin binding*, *evidence-only proposal*, *boundary split* and *light participant*. A light participant is one that does not see the DAG.

## Fault tolerance via branched execution

Somewhat surprisingly, the optimistic track and the recovery track can both proceed more or less independently.

Under asynchrony and in the presence of (Byzantine) faults, due to the unanimity requirement the best consistency guarantee that can be made for the optimistic track is eventual consistency. No liveness guarantee is possible in the presence of faults for a particular run of the transaction construction protocol.

Recall that when multiple transactions attempt to spend some of the same coins, it is up to miners to determine which one (if any) will be confirmed in a block. Miners are assumed to follow their incentives, maximizing fee revenues. Even if transaction replacement wasn't useful or desirable, there is no mechanism that can enforce that unspent outputs are exclusively bound to one transaction construction session over another without *global* consensus.

As we have seen, the success path always reaches termination, and can only reach it by observing unanimous agreement, and when that is possible progress requires only eventual consistency. Validity proofs reduce Byzantine faults to omission faults, so recovering liveness in the presence of failure requires partial synchrony assumptions at the very least.

Since input exclusivity is neither desirable nor enforceable, we can embrace its absence and reframe liveness in a simpler way by treating all failure recovery as branching off another instance of the protocol with a subset of the participants precisely when that subset of the participants can agree among themselves that a failure condition has been detected. Such agreement inherently requires synchrony or partial synchrony, and so explains why this is needed for fault tolerance. In this case the blocks at some height $h$ with $t < n$ parent blocks will be produced as part of the recovery synchronization protocol on top of which a new transaction construction session will commence. If messages are delivered allowing a block at height $h$ to be produced with $t = n$ messages, the asynchronous base protocol can resume progress resulting in the diverging protocol states at height $h$. This special case has the same structure as all-to-all broadcast.

Since recovery is just permissioned coalition formation, any participant may act as an aggregator and make a coalition formation proposal based on its local view; the proposed participants must all accept before it starts. Membership changes can alter anonymity or payment terms, so participants may renegotiate or decline. Recovery also has a privacy cost: excluding an input links it to the outputs that drop out with it, even if its owner was merely unresponsive.

The reason this framing is simpler is that recovery attempts do not need to terminate the run of the protocol that they are trying to recover. In the case that both branches eventually succeed, Bitcoin itself will adjudicate the conflicting transactions. We can treat failure recovery as a (more) synchronous layer building on a fundamentally asynchronous optimistic base protocol with BEC semantics.

## 🤖 Recovery overlay {#recovery-overlay}

Each optimistic session is monotone and append-only. Its optimistic and recovery tracks are interleaved within the same block DAG, distinguished by the threshold used for progress: $t=n$ for unanimous construction and $t<n$ for recovery. The recovery DAG is the logical overlay formed by the reduced-threshold blocks and their causal references, not a separately synchronized history or a rollback of construction. Publishing a recovery block does not disable subsequent optimistic progress. The overlay provides robust dissemination and synchronization of the observations used by aggregators to propose recovery coalitions. The original session can continue receiving contributions and completing phases while the overlay progresses.

This resembles dual-track consensus, which combines an optimistic path with a more robust alternative; TockOwl+ is an example using concurrent fast and slow tracks with hedging delays.[^dual-track] Here the tracks share the DAG substrate and are differentiated by $t$, rather than requiring a global switch between protocols. Their purposes also differ: the optimistic track completes the existing construction, while recovery supports proposals for successor coalitions. The citation provides a design comparison, not a proof of this composition.

🤖 Unlike those tracks, the optimistic track here requires unanimity, and the tracks may race without violating safety: different sessions may attempt to spend the same inputs, and Bitcoin resolves conflicts between competing transactions.

An aggregator may propose a successor when its recovery view is sufficient under its chosen policy. Let $F$ represent that view's frontier. The recovery coalition formation proposal $g'$ references the blocks in $F$ as parents, thereby committing to their causal history. The proposal is the genesis of a new optimistic session, with its own first and second unanimous acknowledgement rounds at kickoff. Multiple aggregators can propose different successors from different views; there is no requirement to first agree globally on one recovery view.

Let $A(F)$ denote the active set derived from the recovery evidence and policy at $F$. A recovery proposal may use only co-spend proposals involving members of $A(F)$. Restricting eligibility does not rewrite the terms or membership of an existing co-spend proposal. The successor coalition still requires acceptance of its own terms and satisfaction of its kickoff conditions. The precise activity and view-sufficiency predicates remain parameters to be specified.

For recovery blocks, a threshold predicate may authorize progress in permissioned coalition formation without satisfying [unanimous set finalization](optimistic-track.md#state-acknowledgement-and-unanimity) for the original membership. Such progress does not close the original construction phase. Successful negotiation establishes a new instance, whose membership and kickoff conditions are checked against the accepted proposal. Threshold selection and the recovery predicates are independent parameters of the interpretation function.

The parallel recovery overlay uses $t<n$ to coordinate fault-tolerant, permissioned coalition formation; its purpose is to improve the robustness of aggregators' recovery proposals. Wall-clock policies, threshold logical clocks or BEC proposal exchange can support different recovery modes. Anyone can aggregate a proposal from a local view. Other participants can counterpropose; no globally agreed recovery view is required before negotiation.

An accepted proposal fixes a successor's initial inputs and validators as a subset of the parent session's, and fixes its allowed auxiliary inputs. Kickoff requires the proposal's required signatures and anonymity conditions. The successor then runs its own optimistic construction with $t'=n'$. The original and competing recovery instances may remain active concurrently.

Lower thresholds permit smaller groups to pursue recovery, down to two-party collaboration. They do not automatically preserve quorum-intersection or censorship-resistance guarantees of larger groups. Censorship-Resistant Byzantine Broadcast (CRBB) couples agreement on a set with inclusion of timely honest submissions, and studies the latency cost of that guarantee; replacing its timing assumptions with threshold-clock evidence requires a separate argument.[^crbb] The DAG retains proposals, contributions and evidence needed for those arguments without requiring global agreement between distinct successor instances.

## Consistency, liveness and termination in the presence of Byzantine faults

In typical definitions of Byzantine fault-tolerant distributed consensus or agreement protocols, once a majority of honest peers has settled on a certain state, any lagging honest peers will only ever accept updates that progress towards that state when they are able to catch up. Unfortunately for our purposes this isn't enough for fault-tolerant transaction construction, since *successful* termination of the protocol requires unanimity.

If a majority of the honest users can agree on a set of inputs and outputs, but one of the honest participants not in this majority still hasn't submitted all of their outputs, then it would rightfully withhold its signatures even if it does come back online. When assuming the asynchronous communication model, this can delay termination indefinitely, and achieving a majority is not sufficient for termination.

Contributing signatures to a transaction that may become valid when fully signed is both an honest signal and a signal of honesty. In the signalling-theory sense, it is not costless, since the transaction may have consequences such as mining fees if the other parties also sign. Contributing signatures *also* signals honesty in the sense defined above: validity proofs make it safe for honest participants to sign regardless of the actions of other users, so they have no reason to withhold their signatures. A which deviates or defects from transaction construction can veto the transaction but at the cost of withholding a signature on at least one of their inputs.

In lieu of agreement about a transaction, agreement on the available evidence can still support liveness by allowing recovery from a fault. This boils down identifying inputs for which signatures have not yet been received. A missing signature may still eventually arrive, completing the transaction, but to avoid waiting indefinitely, participants can negotiate another transaction construction attempt while continuing to listen for progress in the original one.

Under synchrony or partial synchrony (specifically the eventual synchrony variant), if a sufficient threshold of peers can all agree it has been too long, then they can initiate such a recovery session. A threshold of peers agreeing implies a majority of honest peers agreeing. Note that agreement by a majority of honest participants requires a supermajority threshold. A quorum is a set of peers meeting the required agreement threshold. Given $n = 3f+1$ where at most $f$ are faulty, a quorum of $2f+1$ peers will include at least $f+1$ honest peers, a majority within any such quorum.

So long as the notion of "too long" is well defined (consistent with the communication model) and agreed to by such a quorum, whenever there are up to $f$ inputs owned by faulty peers honest parties should be able to successfully complete a run of the protocol after $O(f)$ attempts by simply excluding those inputs as it becomes apparent that they are disruptive or unresponsive. Even in the worst case this process ensures at least one input can always be excluded.

If there are more than $f$ faults recovery is still possible but coordinating recovery attempts by identifying the subset of inputs eligible to participate in recovery requires additional assumptions.

## Fault tolerance under different communication models

If a subset of participants can all agree that some other peers are faulty, they could recover by restarting transaction construction without those peers' inputs, allowing them to produce a valid transaction without those peers. Deciding when a peer is unresponsive, the only kind of fault that is tolerated in the honest threat model, largely depends on how messages are transmitted. Depending on what can be assumed about message delivery, different guarantees about liveness or fault tolerance can be made.

The distributed systems literature typically divides this into three communication models: asynchrony, synchrony, and partial synchrony.[^dls] Each demands a different approach to fault tolerance. These models also apply in the more adversarial settings.

### Asynchrony

In the asynchronous communication model, messages may be arbitrarily delayed, so when an expected message fails to arrive, we cannot conclude the sender is faulty because when that happens isn't well defined. This setting is the simplest in which correct behavior can be reasoned about, because it makes the weakest guarantees. If we assume all peers are honest, the only recourse is to keep waiting.

### Synchrony

Intuitively, a peer that has been unresponsive for too long can be considered faulty. By adding timeouts, we can recover liveness by simply giving up coordinating with such peers.

The synchronous communication model is typically in play whenever a protocol relies on specific timeout values, i.e. defining how long is "too long". This model assumes that the participants can agree on what time it is, and that all sent messages will arrive no later than some maximal delay. If a message that is expected to arrive fails to do so before the timeout elapses, the peer which was supposed to send is said to experience a crash fault, rendering it unresponsive for the remainder of the protocol, or an omission fault if it was temporarily unavailable and some of its messages were not delivered.

Note that such delays may be arbitrarily long, provided their bound is well defined, even if the underlying transport requires interactivity on a shorter time scale. For example, we might use TCP/IP with timeouts on the order of tens of seconds to interact with a store-and-forward service that allows peers to send each other messages with timeouts on the order of hours or days. The model assumed by the underlying transport or its parameters need not agree with the model assumed for transaction construction.

### Partial synchrony

Partial synchrony lies in between. Like the synchronous model, it assumes message delivery is timely, but unlike the synchronous model, the bound on the delay either isn't known or may not always apply, so simply waiting for a timeout duration will not suffice to obtain liveness. Typically this requires acknowledgement from some threshold fraction of participants in order for progress to be made.

## 🤖 Model {#model}

### Parties

- **Initial inputs** $I$ are listed in the genesis. Each input is represented by the online key enrolled by its ownership proof, as specified in [coalition formation](coalition_formation.md).
- **Auxiliary inputs** $A$ are admitted anonymously in the auxiliary input phase.
- **Validators** $N$, with $n = |N|$. A validator uses the online key of an initial input to sign its blocks with the precommitted nonce. The ownership proof selected by the accepted coalition formation proposal binds that key to the input's outpoint. Exposure of the key disqualifies the validator; exposure alone does not establish whether its owner equivocated, disclosed the key or was compromised.
- **Participants** own inputs. Every initial-input owner participates as a validator through its enrolled online key and supplies the required acknowledgements. Following another node does not remove this role.
- **Aggregator**: whoever submits a recovery proposal. It has no other role.

### Faults

- Byzantine faults, which include crashes and omissions.
- **Quorum mode**: at most $f$ of the $n$ validators are faulty, with $n \ge 3f+1$. Any number of input owners may be faulty.
- **Own-view mode**: any number of validators and owners may be faulty. This is the dishonest majority setting.
- A validator's faults are attributed to its initial input, and that input's faults to its validator.

### Synchrony

Under synchrony there is a known bound $\Delta$: a message an honest party sends at its local time $\tau$ is held by an honest recipient by the recipient's local time $\tau + \Delta$. $\Delta$ covers delivery, fetching missing causal history and clock skew.

Honest validators relay every valid message and block they hold to every validator, and to the participants connected to them. So whatever one honest validator holds, every honest validator holds within $\Delta$ more.

Under partial synchrony the bound holds only after an unknown time, or for an unknown $\Delta$. See [Timing](#timing).

### Transport properties

- Validator-to-validator channels are authenticated.
- Anonymous contributions use a sender-anonymous transport. Each copy goes over its own connection, unless the transport provides unlinkability between messages.
- In quorum mode, an honest participant sends each message to at least $f+1$ validators and receives from at least $f+1$. In own-view mode it sends to and receives from every validator.

## 🤖 Objects {#objects}

🤖 Hashes and identifiers, input lists, per-input messages, [keyed messages](optimistic-track.md#keyed-and-anonymous-phases) and the interpretation of ordinary DAG blocks are defined with [phase closure](optimistic-track.md#phase-closure) in the optimistic track chapter.

### Evidence that excludes at once

| Evidence | Content | Excludes |
| --- | --- | --- |
| exposed key | a validator scalar $x$ with $xG = P$ | that validator |
| per-input equivocation | two conflicting valid input proofs of $i$ | input $i$ |

A key is exposed when a validator signs two different blocks with the same committed nonce: the two responses give $x = (z_1 - z_2)(e_1 - e_2)^{-1}$.[^bip340]

An invalid block is not evidence. It is ignored, and its author is treated as unresponsive, so honest validators may mark it missing. One example is a recovery track block that marks as missing something in its own causal history. The exception is equivocation: if an invalid block reuses a committed nonce, the author's key is still recovered from it as a fraud proof. So the nonce commitment check applies to every signed block, valid or not.

## 🤖 Recovery track {#recovery-track}

### Acknowledgement evidence

🤖 Set finalization uses ordinary blocks in two acknowledgement rounds. In the first round, each peer implicitly acknowledges that it has nothing to add to the candidate set. In the second, every peer acknowledges that the first-round acknowledgements were synchronized: the same set is represented in all those blocks. The union of different first-round states is not a finalized state.

🤖 These rounds describe how blocks are interpreted, not separate block types. The recovery rules must identify which block and state satisfy each round before absence of that acknowledgement can support an exclusion. Two ordinary blocks with different contents are not, by that fact alone, nonce reuse or evidence of equivocation. The nonce-consumption and conflicting-acknowledgement rules needed for that inference remain to be specified.

### Deadlines

The recovery track adds deadlines to the optimistic track. $T_{\mathrm{enter}}(\phi)$ is the local time at which a validator enters phase $\phi$, and the deadline is $T_{\mathrm{dl}}(\phi) = T_{\mathrm{enter}}(\phi) + D_\phi$, with $D_\phi$ one of the [parameters](#parameters).

🤖 A deadline does not close a phase or force an acknowledgement. Anonymous-phase publication still waits for reconciliation quiescence and the minimum waiting period, independently of the validator's own anonymous contributions. Finalization still requires the two acknowledgement rounds over the same set. The deadline supplies the reference time for the proposed recovery schedule below; its compatibility with those publication conditions remains to be established.

### Recovery track blocks

On the optimistic track a phase advances only with blocks from all $n$ validators, $t = n$. In terms of Cordial Miners, this is the most cordial a validator can be, at the cost of liveness: one silent validator stalls the phase.[^cordial] A recovery track block has a reduced threshold, $t \lt n$. A validator sends one when it thinks it has waited too long, subject to the usual cordiality requirement on its parents.

A validator $v$ in phase $\phi$ publishes a recovery track block for $(\mathit{sid}, \phi, r)$ at $T_{\mathrm{rec}}(\phi, r)$ if it has not entered $\phi + 1$. For the signatures phase, "entered $\phi + 1$" means it holds every signature.

$$
T_{\mathrm{rec}}(\phi, 0) = T_{\mathrm{dl}}(\phi) + 4\Delta,\qquad
T_{\mathrm{rec}}(\phi, r) = T_{\mathrm{rec}}(\phi, r-1) + D_R\,\beta^{r-1}.
$$

It stops once it holds a successor of $\mathit{sid}$ whose kickoff has closed, or once $r$ reaches $R_{\max}$. It keeps relaying $\mathit{sid}$'s messages after that, so a late signature can still complete $\mathit{sid}$.

**Parents.** In quorum mode, blocks of $\mathit{sid}$ from at least $q = n - f$ distinct validators. In own-view mode, at least $v$'s own latest block. It should also reference every block of $\mathit{sid}$ that $v$ holds and that is not already below one of its parents. A validator in a minority partition cannot gather $q$ parents, so in quorum mode it publishes nothing.

**Payload.** Every received phase message $v$ holds that is not yet in its causal history, as on the optimistic track. Anonymous submissions become eligible for inclusion once received through synchronization, without distinguishing the validator's own submissions from those of other participants. This relays late messages.

**Contents.** Besides the payload, the block holds $\mathit{sid}$, $\phi$, $r$, any evidence objects, and what $v$ is missing: inputs of $L_\phi$, none for anonymous phases, and validators.

The block commits unambiguously to what $v$ is missing, explicitly or implicitly. Whether it lists the missing items or they follow from its parents and causal history is a wire-level encoding choice, and so is a bitmap versus a list of validator indices. They are left to the [protocol messages](protocol-messages.md). An explicit list is expected to be simpler: in quorum mode $t \gt n/2$, so fewer items are generally missing than present.

A block that marks as missing something in its own causal history contradicts itself. It is [invalid](#evidence-that-excludes-at-once), and its author is treated as unresponsive.

**What is missing.** An honest validator marks a **missing input** $i$ if its view holds no valid message keyed by $i$ in phase $\phi$.

🤖 **Missing-validator marks remain unresolved.** The earlier proposed timing rule used absence of a first-round acknowledgement, or of a second-round acknowledgement after publishing the corresponding local acknowledgement, with a $2\Delta$ relay margin. Applying such a rule requires identifying the relevant ordinary block, round and candidate state. It must also account for reconciliation quiescence, minimum waiting periods and differing first-round states. No bound showing that every honest peer can issue the required acknowledgement within $2\Delta$ has been established for these conditions. The exclusion rules below therefore do not yet establish no framing for missing-validator marks.

### Exclusion

Exclusion is a function of the evidence in the proposal alone, so anyone can recompute it. Its inputs are $E$, a set of recovery track blocks for one $(\mathit{sid}, \phi, r)$ by distinct validators, and $V$, a set of evidence objects.

**Quorum mode** requires $\lvert E \rvert \ge q$:

$$
X_I = \{ i \in L_\phi : \text{at least } f+1 \text{ blocks of } E \text{ mark } i \},\qquad
X_V = \{ w \in N : \text{at least } f+1 \text{ blocks of } E \text{ mark } w \}.
$$

$E$ may hold more than $q$ blocks. The mark threshold remains $f+1$; the intended [no-framing argument](#no-framing) for validator marks still requires the missing-acknowledgement rules.

**Own-view mode** takes $E$ to be one block, by the proposer's validator. $X_I$ and $X_V$ are what that block marks. Honest participants protect themselves with the veto in [acceptance](#acceptance).

**Evidence**, in both modes, adds its signer or author to $X_I$ or $X_V$. It needs no recovery track block, so a proposal may be built from evidence alone, at any time.

**Coin binding** is applied once, at the end: each excluded validator's coin joins $X_I$, and the validator of each coin in $X_I$ joins $X_V$.

**Empty result.** If both sets are empty, no proposal is valid. The instance continues, and the next round's deadline applies. This is a late pass.

### Recovery proposal

A recovery proposal is a coalition formation proposal. It carries evidence, and the successor's genesis is derived from that evidence.

| # | Field | Content |
| --- | --- | --- |
| 1 | version | u8 = 1 |
| 2 | kind | u8 = recovery |
| 3 | parent | $\mathit{sid}$ (32), $\phi$ (u8), $r$ (u16); $r$ = 0xFFFF for an evidence-only proposal |
| 4 | evidence blocks | hashes of the blocks in $E$ |
| 5 | evidence objects | one type-length-value object each |
| 6 | excluded inputs | $X_I$, sorted outpoints |
| 7 | excluded validators | $X_V$, sorted indices into the parent's $N$ |
| 8 | proposer | an outpoint in $I'$ |
| 9 | signature | by the proposer's online key over $H(\texttt{fungi/recovery-proposal}, \text{fields 1–8})$ |

Every recipient derives the successor's genesis:

| Field | Derivation |
| --- | --- |
| deny list | $D' = D \cup X_I$, where $D$ is the parent's deny list (empty for a first instance) |
| initial inputs | $I' = I \setminus D'$ |
| validators | $N' = N \setminus X_V$, in parent order, each with its outpoint |
| co-spend proposals | those of the parent that name no outpoint in $D'$ |
| parameters | as in [Parameters](#parameters) |

The successor id is $\mathit{sid}' = H(\texttt{fungi/session}, \text{derived genesis})$. It depends on $X_I$ and $X_V$, not on $E$, the evidence objects or the proposer. Two proposals with the same result therefore name the same successor.

Excluded inputs' co-spend proposals must be dropped, so new co-spend proposals may be required.

Validators of every descendant instance reject a denied outpoint as an auxiliary input. An excluded auxiliary input is never an initial input, so only the deny list keeps it out.

**Validation.** A proposal is valid if and only if:

1. the parent instance and $(\phi, r)$ are known;
2. each block in $E$ is a validly signed recovery track block for $(\mathit{sid}, \phi, r)$, and the authors are distinct validators of $N$;
3. in quorum mode $\lvert E \rvert \ge q$, and each block of $E$ has parents from $q$ distinct validators; in own-view mode $E$ is one block, by the proposer's validator;
4. each evidence object is valid for $\mathit{sid}$;
5. $X_I$ and $X_V$ equal the output of [exclusion](#exclusion);
6. $X_I \cup X_V$ is not empty;
7. the proposer is in $I'$ and the signature verifies;
8. the successor's parameters pass the participant checks in [Parameters](#parameters).

Checks 2 and 3 are skipped for evidence-only proposals.

**Dissemination and flood bound.** A proposal counts only when it is in the payload of a validator block, and its evidence blocks are in that block's causal history. Honest validators relay blocks, so within $\Delta$ every honest party holds what one honest validator holds. Each proposal is signed by an initial input, which is the input-issued unit it spends. Validators carry at most one proposal per proposer per $(\mathit{sid}, \phi, r)$, and at most one per $\mathit{sid}'$.

### Acceptance

A participant owning $i \in I'$ accepts a proposal $P$ only if:

1. $P$ is valid;
2. 🤖 **veto**, if the participant sees the DAG: no input excluded by marks has a valid per-input message in its view. A validator exclusion must be checked against the first- or second-round acknowledgement it was marked for, interpreted from ordinary DAG blocks; this part of the veto remains unresolved until the acknowledgement-identification rule is specified (required in own-view mode, recommended in quorum mode);
3. its own policy accepts the new terms: anonymity, fees and payments.

A participant may accept competing successors of the same phase, in the same round or in later rounds. Like the parent and its successor, they run concurrently, and Bitcoin decides which one confirms.

**Choosing.** At $T_{\mathrm{rec}}(\phi, r) + C$ by its own clock, with $C = 6\Delta$, it considers the proposals held in validator blocks by then, plus evidence-only proposals for $\mathit{sid}$. An evidence-only proposal competes at the next cutoff. Among those that pass the checks:

- in quorum mode it picks the one with the most exclusions;
- in own-view mode it picks the one with the fewest;
- ties go to the lowest $\mathit{sid}'$.

🤖 Conditional on the intended no-framing property in quorum mode, a larger exclusion set is preferable, and a faulty aggregator can only offer a subset of what an honest one finds unless it adds more faulty parties. In own-view mode a single block decides, and a faulty one can frame. A participant that cannot veto therefore prefers the smaller set.

**Accepting.** It sends $\mathrm{ACCEPT}(i)$ for $\mathit{sid}'$ to every validator in $N'$. This is the successor's first per-input message. Validators enter the successor's kickoff on holding its genesis, and kickoff closes like any other phase. A participant in $I'$ that never accepts stalls that kickoff. [Kickoff](optimistic-track.md#kickoff) has no recovery, so the successor does not exclude that input. Its other participants can accept a competing successor instead.

**The parent keeps running.** Validators keep processing $\mathit{sid}$, and participants keep their obligations in it, including signing if it gets that far. If both instances are signed, Bitcoin decides which one confirms. Either pays every honest participant as intended.

### Timing

- Honest validators enter a phase within $\Delta$ of each other.
- **Submission margin**: an honest initial-input owner sends each phase message by $T_{\mathrm{dl}} - 3\Delta$ by its own clock. Then every honest validator holds it by its own deadline. The three $\Delta$ are delivery to some honest validator, relay to the rest, and entry skew.

🤖 The following is the proposed recovery schedule. Its acknowledgement-completion times are targets, not established bounds for the two-round set-finalization rule:

| Local time | Event |
| --- | --- |
| $T_{\mathrm{enter}}$ | enters $\phi$ |
| $T_{\mathrm{dl}} - 3\Delta$ | proposed last submission by an honest initial-input owner |
| $T_{\mathrm{dl}}$ | proposed deadline; first-round acknowledgement still depends on its publication conditions |
| $T_{\mathrm{dl}} + 2\Delta$ | proposed availability of honest first-round acknowledgements; unresolved |
| $T_{\mathrm{dl}} + 4\Delta$ | proposed availability of honest second-round acknowledgements; scheduled round-0 recovery observation if it has not entered $\phi + 1$ |
| $T_{\mathrm{dl}} + 6\Delta$ | every honest party holds every honest round-0 recovery track block; aggregators build proposals |
| $T_{\mathrm{dl}} + 10\Delta$ | cutoff $C$: participants choose a successor and send ACCEPT |

🤖 Conditional on the recovery blocks being published and relayed at the proposed times, the cutoff calculation is as follows. This does not establish the preceding acknowledgement deadlines. Measured from the earliest honest validator's $T_{\mathrm{rec}}$, call it $t_0$: every honest recovery track block is held by $t_0 + 2\Delta$; an honest aggregator, which entered by $t_0 + 2\Delta$, builds by $t_0 + 4\Delta$; an honest validator holds the proposal and carries it by $t_0 + 5\Delta$; every honest participant holds it by $t_0 + 6\Delta$. Each participant's own $T_{\mathrm{rec}}$ is at least $t_0$, so its cutoff $T_{\mathrm{rec}} + 6\Delta$ is late enough.

**Partial synchrony.** Set $\beta = 2$, so the round spacing doubles each round, and successors inherit $\Delta$ and every duration multiplied by $\beta^{r+1}$. Before stabilization an honest message can miss a deadline, and an honest input can then be excluded in quorum mode. The veto still protects it while some honest participant in $I'$ with a view holds its message. A successor's $\Delta$ exceeding the real delivery bound supplies the timing assumption; it does not resolve acknowledgement identification or prove the missing-validator rule. The cutoff, proposed relay margins and submission margins all grow with it.

### Parameters

All parameters are fixed in the genesis.

| Name | Meaning | Suggested |
| --- | --- | --- |
| mode | quorum or own-view | quorum when $n \ge 4$ |
| $f$ | fault bound in quorum mode | $\lfloor (n-1)/3 \rfloor$ for a first instance |
| $\Delta$ | timing bound | set by the aggregator |
| $D_\phi$ | duration from entry to deadline, per phase | at least $5\Delta$ |
| $D_R$ | spacing between recovery rounds | $4\Delta$ |
| $\beta$ | backoff factor | 1 under synchrony, 2 under partial synchrony |
| $C$ | acceptance cutoff after $T_{\mathrm{rec}}$ | $6\Delta$ |
| $R_{\max}$ | last recovery round per phase | set by the aggregator |

**Successors.** $\Delta$ and each duration are multiplied by $\beta^{r+1}$ for the stalled round $r$. The fault bound is carried, not recomputed: $f' = f - k$, where $k$ counts the validators excluded by proven fault. Those are $f+1$ marks in quorum mode, an exposed key, or coin binding from an input excluded by $f+1$ marks or by equivocation. The successor runs in quorum mode if $n' \ge 3f' + 1$, and in own-view mode otherwise.

For example, with $n = 7$ and $f = 2$, two faulty validators stay and three honest ones leave. Then $n' = 4$ and $f' = 2$, so the successor runs in own-view mode, since $4 \lt 7$. Recomputing $f'$ from $n'$ would give $f' = 1$, and the two faulty validators alone could then exclude anyone.

**Participant checks.** The genesis comes from whoever started the instance, and an aggregator that sets $\Delta$ too small breaks synchrony for everyone. A participant accepts a genesis or a successor only if $\Delta$ is at least its own estimate of the transport bound, every $D_\phi \ge 5\Delta$, $D_R \ge 4\Delta$, and the mode and $f'$ follow the rules above.

## 🤖 Counterparty stalls {#counterparty-stalls}

A faulty payee can stall its honest payer at no cost to itself. For example, it never claims its payment after the payer's input proof. The payer gets no receipt, so it does not sign, and its input is named. Recovery then excludes the payer, not the payee.

Payer and payee trust each other for liveness: the payer chose its payee and takes the risk that it stalls. So either way of handling this is acceptable. This draft specifies option A and describes option B.

### Option A: blame the payer only

This is the rule above, and it matches the failure table in the validity proofs draft (`validity-proofs.md`).

- **Bound**: a faulty payee can get each honest payer that chose it named once. The successors it forces for free are at most the number of honest payers paying faulty payees.
- **Who pays**: the payer loses this attempt. Third parties pay one retry each time, with fresh secrets and a new session, and one more attempt that retry unlinkability must cover.
- **Privacy**: no payment is published. The named input is public, as it is for any failure.

### Option B: blame the pair

- **Gain**: every stall costs the adversary a coin, so [each successor costs a coin](#each-successor-costs-a-coin) holds, except for payees with no input in the instance.
- **The payee must be provably the payee.** A payer that could name any input would get third parties excluded, which is ruled out. So the payer needs a statement the payee signed, for example a signature by the payee's online key over the payment terms. The payer would post it as an evidence object, and exclusion would add the payee's input to the payer's.
- **That statement proves the payment to anyone.** The payer can publish it at any time. Publishing it for blame shows everyone which two inputs a payment links. Both leave the instance, but the link stays attached to those coins.
- **The payer learns the payee's input.** The validity proofs draft requires that the payee not learn the paying input and the payer not learn the funded output. It says nothing about this direction, so option B needs that decided. A stall already weakens the first requirement in both options, as below.
- **A payee with no input in the instance** cannot be blamed. Option B then falls back to option A.
- **Who failed stays unknown.** The statement shows that the pair did not complete, not which one failed. A lying payer can get its honest payee excluded, but the payer is also excluded.

### In both options

A faulty payee learns the paying input when that input is named after its own stall. Payer anonymity with respect to the payee therefore holds only for payees that complete. The retry restarts from the destination commitments with fresh secrets, not in place.

## 🤖 Properties {#properties}

🤖 The intended properties assume synchrony and the submission margins in [Timing](#timing). Missing-validator exclusion and the properties that depend on it remain conditional on the unresolved acknowledgement-identification and timing rules.

### Honest messages arrive in time

An honest participant that respects its margin has its message held by every honest validator by that validator's own deadline.

### No framing

🤖 The intended quorum-mode property is that no valid proposal excludes an honest input or validator, except a payer whose payee stalled it and that payer's validator. The argument is incomplete for missing-validator marks:

1. No honest validator marks an honest input, since its message arrived in time and a received message is never withdrawn.
2. 🤖 The proposed $2\Delta$ rule does not yet establish that an honest validator cannot be marked missing. Finalization requires synchronized first-round acknowledgements of the same set; differing first-round blocks do not by themselves prove equivocation or expose a signing key. The earlier argument based on a unique first-round block therefore does not apply.
3. Faulty validators supply at most $f$ marks, and exclusion needs $f+1$.
4. Honest validators' keys are not exposed, their blocks are valid, and honest parties do not equivocate.
5. Coin binding links an honest coin only to an honest validator. So it excludes an honest validator only together with its coin, which happens only after a counterparty stall.

### Late passes are bounded

🤖 The previous late-pass bound counted one first-round acknowledgement and one second-round acknowledgement per validator per phase, plus a per-input message where applicable. Ordinary DAG blocks do not supply that fixed item count without an acknowledgement-identification rule. The claimed one-late-pass bound per item, and the derived totals of 13 rounds ($52\Delta$) or 17 rounds ($68\Delta$), are therefore unresolved. The current phase sequence also needs to be included when any such count is derived again.

### Successors are bounded

🤖 Conditional on the intended no-framing property, a chain of started successors has length at most the number of faulty inputs plus faulty validators, plus the number of honest payers paying faulty payees. Each valid proposal excludes at least one party, every excluded party is faulty apart from those payers, excluded inputs stay on the deny list, and excluded validators are never added again. If at most $f$ inputs are faulty as well, as [above](#consistency-liveness-and-termination-in-the-presence-of-byzantine-faults), that is the $O(f)$ attempts described there, plus the payer term.

An honest participant that declines a successor's terms does not send ACCEPT, so that successor's kickoff stalls. Kickoff has no recovery, so the input is not excluded there, and the other participants can accept a competing successor.

### Each successor costs a coin

🤖 Conditional on the intended no-framing property, every exclusion by marks or proven fault removes a faulty coin, directly or through coin binding. Under option A the exception is a faulty payee stalling its payer, as above. Retries are then limited by the adversary's coins, plus the number of honest payers paying faulty payees.

### Own-view mode

- A successor that names an honest participant with a view never excludes an honest input by marks: that participant vetoes, and the successor needs every ACCEPT.
- An honest aggregator whose result is empty holds every item and relays it, which is a late pass. A vetoing participant holds the item and relays it too, so the next round has it.
- A light participant cannot veto. If every participant with a view named in a successor is faulty, a framed exclusion can start.

### Boundary splits

A proposal that reaches an honest validator just before the cutoff reaches some participants in time and others too late. In quorum mode it wins only if it excludes more, and under synchrony those extra exclusions are faulty parties. The two groups accept different successors. Each stalls at kickoff while the parent keeps running, and neither excludes the other group, since kickoff has no recovery. Either group can also accept the other's successor.

Without agreement on the set of proposals, this cannot be ruled out. Applying the relay rule of the next section to proposals gives that agreement, at a cost of $2(f+1)\Delta$.

## 🤖 Dishonest majority {#dishonest-majority}

The [block DAG](block-dag.md#cordial-miners-inspired-invariants) leaves this setting unexplored, so this section is exploratory. Open coalition formation resembles Byzantine agreement with unknown participants. Recovery resembles the active-set setting instead: the universe is known, and which members are active is not. Choi et al. define active-parties set agreement for this.[^choi] Its validity conditions map onto recovery:

| Active-parties set agreement | Recovery |
| --- | --- |
| includes every party active from the start that stays honest | intended no framing; validator-mark rule unresolved |
| excludes parties not activated by termination | a missing per-input message supports an input mark; missing-validator marks need a specified acknowledgement rule |
| may include faulty parties | a spared faulty party costs one more round |

Recovery needs less than active-parties set agreement. Different aggregators may build different successors, and unanimous acceptance takes the place of agreement.

Own-view mode is the dishonest majority mode. Per-input messages are signed by their inputs and blocks by their validators, so relaying needs no threshold. 🤖 The intended no-framing argument uses synchrony, signatures and the veto; for validator marks it still depends on identifying the required acknowledgement and its state. What own-view mode lacks is agreement: two honest views can differ at a deadline, and the cost is one more round per vetoed proposal. See [what the literature gives](#what-the-literature-gives).

### Relay signatures

This optional rule adds agreement on exclusions among honest parties, as in Dolev and Strong's authenticated broadcast.[^dolev-strong] For a per-input message $m$ of a phase with deadline $T$ by the party's own clock:

- a party counts $m$ as on time if it holds $m$ by $T + 2k\Delta$ with signatures from $k$ distinct validators other than the submitter;
- an honest validator that first counts $m$ as on time with $k$ signatures adds its own and relays $m$ to every validator;
- with $t$ the assumed number of faulty validators, up to $n - 1$, a party marks $m$ missing only at $T + 2(t+1)\Delta$;
- 🤖 Extending the rule to first- and second-round acknowledgements requires identifying their ordinary DAG blocks and relevant states. Using the same phase deadline for both rounds is not yet justified.

Each hop needs $2\Delta$, not $\Delta$, because honest deadlines differ by up to $\Delta$. If $h_1$ relays at its own $T_1 + 2k\Delta$, then $h_2$, whose $T_2 \ge T_1 - \Delta$, holds the message by $T_2 + 2(k+1)\Delta$, which is on time with $k+1$ signatures. If one honest party counts $m$ as on time, every honest party does, so honest marks agree and an honest aggregator's proposal passes every honest veto. The cost is up to $2(t+1)\Delta$ before marking: $200\Delta$ for $t = n - 1$ at $n = 100$.

### What the literature gives

- **The threshold is tight.** Vigil proves that a node silent toward at most $f$ honest nodes cannot be identified (Theorem 2), so the threshold of $f+1$ marks is tight.[^vigil] Silence toward fewer nodes can only be repaired by relaying. Vigil also shows that accountability is impossible under partial synchrony with an unknown stabilization time (Proposition 2). That is why framing before stabilization remains.
- **A polarizer can replace the relay chain.** A polarizer is a broadcast step after which every honest party holds the message with a proof, or a proof that the sender sent nothing. In the send-transferable-message protocol of Deligios, Klasovita and Liu-Zhang, every honest party ends with the message and a proof, or with a proof that the sender did not send it. This holds for any $t \lt n$, and all honest parties stop within $\min\{f_a+2, d+2\}$ rounds, at most one round apart, with $f_a$ the number of parties actually corrupted, $t$ the corruption bound and $d = 2n/(n-t)$ (Lemma 10).[^deligios] That is what own-view mode needs: a transferable missing mark that never names an honest sender. It builds on the polarizer of Loss and Nielsen.[^loss-nielsen]
- **The agreement lower bound may not apply.** Deterministic broadcast needs $\min\{f_a+2, t+1\}$ rounds.[^deligios] Recovery does not need agreement, and no bound is known for the task without it.
- **A veto alone wastes an attempt.** A held message shows that its sender sent it, not that it arrived in time. So a vetoed proposal excludes no one, and progress then needs an event that can be proven. This is open.

### Which mode to use

| Setting | Mode |
| --- | --- |
| $n \ge 3f+1$ can be assumed | quorum mode, with the veto as a second check |
| no honest supermajority | own-view mode |
| own-view mode, and vetoes cost too many rounds | own-view mode with relay signatures, or a polarizer |

## Privacy

🤖 What the recovery track reveals:

- which inputs and validators were late in which phase; both are already public within the instance;
- nothing about anonymous contributions, since recovery track blocks mark only per-input messages and validator blocks.

🤖 Retries:

- each started successor costs the adversary at least one coin, apart from option A's counterparty exception;
- a late pass starts nothing, so it creates no new attempt;
- a participant accepts at most one successor per stalled phase;
- excluding an input links it to the outputs that drop out, which is inherent, and is why a retry restarts with fresh secrets rather than in place.

🤖 Change scripts. BIP 352 change derivation is tweaked by the input set.[^bip352] Every valid proposal removes at least one coin, through coin binding if it excludes only a validator, so the successor's input set always differs and its change scripts differ too. Without coin binding, a validator-only exclusion would keep the input set and repeat the scripts. Then the tweak would have to include $\mathit{sid}$.

🤖 The following protections are intended; those relying on missing-validator exclusion remain conditional on the unresolved rules above:

- **censoring anonymous contributions**, by sending each one to $f+1$ validators, or to all in own-view mode;
- **lying aggregators**, since anyone recomputes the exclusion from signed evidence, and the veto checks it against the participant's own view;
- **withdrawing presence**, since a received message is never withdrawn and the DAG witnesses duplicates;
- 🤖 **Differing first-round states are not finalized by union.** A second-round acknowledgement must establish that the first-round acknowledgements were synchronized over the same set. How conflicting acknowledgement evidence affects recovery remains unresolved.

🤖 What remains: framing before stabilization under partial synchrony, framing of light participants in own-view mode, boundary splits, honest payers named after a counterparty stall.

Note that synchronization has consequences for privacy as well, when operating outside of the design parameters. A majority of malicious validators, for example, could disrupt gossip and inclusion of certain messages in order to deanonymize them. In this scenario, the participant which unsuccessfully attempted to anonymously broadcast that message but failed can choose to include it, which would potentially implicate it as the author, or defect from validation in order to avoid acknowledging a state which does not include the message. However, in such a circumstance it would be better to allow outputs to be omitted and to withhold signing with one of the inputs in order to reveal as little as possible.

## 🤖 Cost {#cost}

🤖 Set finalization requires two acknowledgement rounds using ordinary DAG blocks. This does not establish a cost of exactly two blocks per validator per phase: ordinary publication may produce additional blocks, and acknowledgement identification is not yet specified. The earlier fixed block-count claim is withdrawn. Timers themselves do not add network messages before firing.

One recovery round:

| Item | Size |
| --- | --- |
| recovery track block parents | at least $q$ hashes of 32 bytes |
| missing inputs, as a bitmap | $\lceil \lvert L_\phi \rvert / 8 \rceil$ bytes; 92 at 729 inputs |
| missing validators, as a bitmap | $\lceil n/8 \rceil$ bytes |
| signature | 64 bytes |

With $n = 100$ and $q = 67$, one block is about 2.3 KB, and one round about 230 KB across all validators. A proposal with five exclusions is about 2.5 KB, mostly the 67 block hashes, since the successor's lists are derived rather than sent. A light participant fetches the $q$ blocks of $E$, about 150 KB, and the blocks they name as parents, so that it can check signatures, parent authors and marks. It needs no deeper causal history. A participant with the history also checks that no block marks as missing something in its own causal history.

Participants send ACCEPT for the successor at about $T_{\mathrm{dl}} + 10\Delta$. The successor's kickoff then closes like any phase.

## 🤖 Worked example {#worked-example}

Quorum mode, with validators A, B, C and D: $n = 4$, $f = 1$, $q = 3$, and exclusion needs 2 marks. D is faulty. A, B, C and D use the online keys of initial inputs $i_1$, $i_2$, $i_3$ and $i_6$. The auxiliary inputs are $i_4$ and $i_5$, and the signature for $i_5$ is withheld. The phase is signatures.

🤖 No validator holds a message from $i_5$. The example illustrates input-omission marks only; it assumes that honest validators make no missing-validator marks while that input message is pending. The general rule for such marks is unresolved. At $T_{\mathrm{rec}}(\text{signatures}, 0)$:

| Block | missing inputs | missing validators |
| --- | --- | --- |
| A | $i_5$ | none |
| B | $i_5$ | none |
| C | $i_5$ | none |
| D | $i_2$ (false) | A |

With $E = \{A, B, C, D\}$, $i_5$ has 3 marks and is excluded, while $i_2$ and A have one each and are not. So $X_I = \{i_5\}$, $X_V = \varnothing$, and no coin binding applies. The successor has $D' = \{i_5\}$, $I' = \{i_1, i_2, i_3, i_6\}$, $N' = \{A, B, C, D\}$ and $f' = 1$.

If D's coin $i_6$ later withholds its signature, the next round excludes $i_6$, and validator D with it. If $i_2$'s signature is in the causal history of D's block, that block contradicts itself. It is invalid and ignored, and D is treated as unresponsive.

## 🤖 Open questions {#open-questions}

- Counterparty stalls: whether to adopt option B, and if so, whether the payer may learn the payee's input.
- Boundary splits: accept them, or pay for agreement on proposals with relay signatures or a polarizer.
- Whether a veto in own-view mode can lead to an exclusion that can be proven, rather than a wasted attempt.
- Whether successors may reuse input proofs from the parent, rather than restarting at kickoff.
- 🤖 How an input that never sends ACCEPT for a successor is excluded, since kickoff has no recovery.
- 🤖 How the new co-spend proposals that replace dropped ones are made.
- 🤖 Identification of first- and second-round acknowledgements in ordinary DAG blocks, including their state references, nonce consumption, conflicting-acknowledgement evidence and the timing needed for missing-validator marks.
- Exact encodings of blocks, signatures and nonce commitments, which are shared with the [optimistic track](optimistic-track.md) and defined in the [block DAG](block-dag.md) chapter.
- Recovery activity and view-sufficiency predicates, including how the active set constrains eligible co-spend proposals.

## 🤖 Appendix: Comparison with agreement building blocks {#appendix-comparison-with-agreement-building-blocks}

The DAG records causal evidence; it does not prescribe one agreement primitive for every phase or recovery mode. The following comparison distinguishes dissemination, agreement and inclusion. Applications to Fungi are candidate compositions, not guarantees inherited merely by representing a protocol's messages as blocks.

The comparison uses the [design objectives](optimistic-track.md#design-objectives) of the optimistic track. A construction optimized for sustained blockchain throughput or rapid block confirmation may introduce unnecessary work and observable intermediate states in a finite phase. The relevant question is how cheaply and quickly it establishes a stable phase boundary, including the cost of disseminating its agreement evidence.

| Building block | Guarantee relevant here | Relationship to this specification |
| --- | --- | --- |
| Byzantine Eventual Consistency | Eventual convergence of valid, mergeable updates under its delivery and application assumptions. | Supports dissemination of contributions and concurrent recovery proposals. Convergence alone does not identify a finite closing boundary. |
| Byzantine reliable broadcast | An honest sender's value is delivered; if one honest peer delivers, all honest peers eventually deliver the same value. | Can establish consistent availability of a block or proposal. It need not terminate for a silent faulty sender, and does not establish completeness of a phase. |
| Interactive consistency | Honest peers decide an identical indexed vector containing every honest participant's submitted value. | A comparison for collecting views. Taking their union does not implement Fungi's two acknowledgement rounds, which finalize only when the first-round blocks represent the same set. |
| Asynchronous common subset | Agreement on a sufficiently large subset of indexed proposals, possibly omitting some honest proposals. | Can establish a common recovery view without a wall-clock deadline. It does not by itself establish full phase inclusion or require the selected proposers to become successor members. |
| Lattice agreement | Decided states are comparable, with validity relating them to proposed states. | Comparable causal views can still differ. A phase requiring one exact common state needs a stronger agreement condition. |
| Censorship-Resistant Byzantine Broadcast | Set agreement with inclusion guarantees for timely honest submissions. | Supplies a reference for phase-specific inclusion. The meaning of timely submission must be established for each recovery mode. |

### Completeness and asynchronous selection

Interactive consistency exposes the collection problem directly. The mostly-asynchronous construction of Diamantopoulos et al. uses a synchrony boundary for collecting inputs, followed by agreement on the result.[^ic] Thus agreement on the vector and knowing which inputs it must contain are separate obligations.

In the standard asynchronous common subset (ACS) formulation, the selected proposer set $Q$ has $|Q|\geq n-f$, including at least $n-2f$ honest proposals. HoneyBadger constructs ACS from reliable broadcast and randomized binary agreement under $n>3f$.[^acs] These are guarantees within a fixed instance; they do not imply global agreement between separate recovery branches.

Overlapping proposals provide a useful inclusion condition. Suppose each proposal $X_i$ is a validated fragment set, and $H_x$ is the set of honest proposers whose submitted sets contain fragment $x$. Since at most $f$ proposals are omitted,

$$
|H_x|>f\ \Longrightarrow\ Q\cap H_x\neq\varnothing
\ \Longrightarrow\ x\in\bigcup_{i\in Q}X_i.
$$

🤖 This counting argument protects a sufficiently replicated fragment even when its original observer's proposal is omitted. It concerns the submitted sets, not information learned after submission. Causal ancestry can witness this inclusion without identifying the anonymous author of the fragment. ACS alone gives no corresponding guarantee for a fragment present in only one honest proposal. This inclusion calculation is not a phase-finalization rule: the union of selected differing views is not the synchronized first-round set required by the second acknowledgement round. A participant continues validator duties independently of inclusion of its own anonymous contributions; its authority to withhold transaction signatures remains separate.

### Membership, resilience and recovery

Active-parties set agreement (APSA) establishes a common set of participant identities without knowing their number in advance. Its validity condition includes every participant active from the start that remains honest until termination, excludes identities not activated by termination, and permits inclusion of faulty participants. The construction uses synchronous rounds, signatures and a certificate-authority setup; it does not identify exactly the honest or currently responsive participants.[^choi] This is relevant to the recovery overlay: the parent session has known membership, but the subset available for a successor is not fixed in advance. An aggregator's view-derived active set need not be globally agreed; APSA supplies a stronger comparison in which eligible honest participants agree on one set. Once a successor coalition proposal is accepted, its construction instance has fixed membership. Agreement on an active set is not a substitute for acceptance of that proposal's terms or for future signing cooperation.

Authenticated synchronous broadcast admits dishonest-majority constructions. Dolev–Strong is the classical example; FlintBB adds an optimistic execution path when actual faults are lower than the configured bound.[^dm] Their timing assumptions cannot be replaced by DAG height alone. Conversely, allowing separate successor instances weakens the global agreement objective without proving any particular broadcast or inclusion guarantee within those instances.

Sample-based reliable broadcast addresses a different dimension: reducing communication and computation with probabilistic guarantees.[^sample-brb] Its uniform sampling and hidden-communication assumptions require examination before exposing its evidence in validator blocks. It is a dissemination alternative, not a replacement for unanimous acceptance.

The specification does not yet select one of these constructions as the recovery agreement mechanism.

## References

[^bip340]: P. Wuille, J. Nick and T. Ruffing, [*BIP 340: Schnorr Signatures for secp256k1*](https://bips.dev/340/). The signature equation behind key exposure.

[^bip352]: josibake, R. Somsen and S. Falbesoner, [*BIP 352: Silent Payments*](https://bips.dev/352/). Output derivation tweaked by the transaction's inputs.

[^choi]: W. Choi, R. Cohen, J. Garay, N. Skoumios and V. Zikas, [*Byzantine Broadcast with Unknown Participants*](https://eprint.iacr.org/2025/2133) (2025). Defines active-parties set agreement.

[^dolev-strong]: D. Dolev and H. R. Strong, [*Authenticated Algorithms for Byzantine Agreement*](https://doi.org/10.1137/0212045), SIAM Journal on Computing (1983).

[^vigil]: J. Cheng, H. Sun, R. Zhou, J. Zhou and Z. Chen, [*Vigil: Accountable Liveness against Selective Silence*](https://arxiv.org/abs/2609.18778) (2026).

[^deligios]: G. Deligios, I. Klasovita and C.-D. Liu-Zhang, [*Asymptotically Optimal Early Termination for Dishonest Majority Broadcast*](https://eprint.iacr.org/2024/1656), Eurocrypt 2025. The lower bound is cited there on p. 2.

[^loss-nielsen]: J. Loss and J. B. Nielsen, [*Early Stopping for Any Number of Corruptions*](https://eprint.iacr.org/2023/1813), Eurocrypt 2024.

[^cordial]: Idit Keidar, Oded Naor, Ouri Poupko and Ehud Shapiro. [Cordial Miners: Fast and Efficient Consensus for Every Eventuality](https://arxiv.org/abs/2205.09174).

[^dual-track]: Minghang Li et al. [TockOwl: Asynchronous Consensus with Fault and Network Adaptability](https://eprint.iacr.org/2025/134) (USENIX Security 2025). TockOwl+ combines fast and slow tracks using hedging delays.

[^crbb]: Ittai Abraham, Yuval Efron and Ling Ren. [The Latency Cost of Censorship Resistance](https://eprint.iacr.org/2025/2136).

[^ic]: Panos Diamantopoulos, Stathis Maneas, Christos Patsonakis, Nikos Chondros and Mema Roussopoulos. [Interactive Consistency in practical, mostly-asynchronous systems](https://arxiv.org/abs/1410.7256).

[^acs]: Andrew Miller, Yu Xia, Kyle Croman, Elaine Shi and Dawn Song. [The Honey Badger of BFT Protocols](https://eprint.iacr.org/2016/199). See also Sisi Duan, Michael K. Reiter and Haibin Zhang, [BEAT: Asynchronous BFT Made Practical, Section 5](https://reitermk.github.io/papers/2018/CCS.pdf), for the ACS properties.

[^dm]: Danny Dolev and H. Raymond Strong. [Authenticated Algorithms for Byzantine Agreement](https://doi.org/10.1137/0212045). Ruomu Hou and Haifeng Yu. [Optimistic Execution in Byzantine Broadcast Protocols That Tolerate Malicious Majority](https://doi.org/10.1016/j.jpdc.2025.105203).

[^sample-brb]: Rachid Guerraoui et al. [Scalable Byzantine Reliable Broadcast](https://arxiv.org/abs/1908.01738).

[^dls]: C. Dwork, N. Lynch and L. Stockmeyer, [*Consensus in the Presence of Partial Synchrony*](https://groups.csail.mit.edu/tds/papers/Lynch/jacm88.pdf) (1988). The introduction contrasts synchronous and asynchronous models and defines the two forms of partial synchrony used here: an unknown timing bound, or a bound that holds only eventually.
