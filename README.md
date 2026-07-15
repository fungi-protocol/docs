# The following is an WIP outline for a intro / README

## Who is the audience for this repo?
<!-- meta: privacy researches who care about why and how, the non-technical user who cares about why and developers who care about how -->
<!-- meta: technical: researchers and developers who care aobut why, how and what -->
<!-- meta: non-technical: plebs who care about mostly why -->

## Abstract / Opening

The following are documents to describe a family collaborative Bitcoin transaction construction protocols with the ultimate goal of decentralized and market based privacy preserving transactions.

This family of protocols starts with a protocol that assumes all participants can be trusted with privacy and not to distrupt the protocol. During the execution this protocol participants may learn privacy damaging information and are trusted to keep it a secret -- ideally by forgetting. When we assume peers behave in this way, this is called the *honest* setting. In this protocol and the rest of the family, trust never means giving up control over one's funds by virtue of unanimous consent. 

The next protocol no longer assumes peers have to be trusted to keep a secret, instead privacy preserving transports and a careful approach towards transaction structure ensure that they don't need to be. This is called the *semi-honest* or *honest-but-curious* setting.

In order to avoid inherent privacy issues with (community graph) we require a market based solution -- coalition formation.

Interacting with strangers on an open permissionless market invites distruption or attempts are survaillance this requires byzantine fault tolerance so honest peers can still suceeced despite the unanimity requirment.

## Motivation

<!-- summarizde the problem and refer to the defintion. Sketch of a solution concept?  -->
<!-- Privacy decays exponentially. The graph is much more richer than we think it is  -->
<!-- Mixing histories -->

The proposed solution is one where collaborative optimization of this tx construction naturally emerges from an extension of the coin selection problem

-----
If you want more info what the problems are refer to: X.


## Structure of repo
<img width="1862" height="891" alt="image" src="https://github.com/user-attachments/assets/e8bb556c-178b-42be-8fa8-dc5019e5993b" />
<!-- TODO: mermaid diagramify this -->
