# Frozen whole-plant tool baselines

The Fusion Solution Set will connect validated plasma/control results to existing whole-plant tools rather than create another monolithic reactor code.

## PROCESS

- Official project: UKAEA PROCESS
- Frozen tag: `v3.4.2`
- Expected commit prefix: `c0ae5b2`
- Intended role: self-consistent plant constraints, systems optimization, power balance and engineering trade studies

## FUSE

- Official project: Project Torrey Pines `FUSE.jl`
- Frozen tag: `v1.1.6`
- Expected commit prefix: `475115c`
- Intended role: integrated plasma, engineering, control, balance-of-plant, costing and uncertainty studies

## Required order

1. Reproduce each unmodified upstream package and its tests/examples.
2. Preserve source identity and numerical environment.
3. Define a small, versioned interface contract for validated inputs from other workstreams.
4. Run a published/reference case before introducing Fusion Solution Set inputs.
5. Compare overlapping quantities between PROCESS and FUSE rather than assuming either is ground truth.
6. Propagate uncertainty and provenance; never pass a surrogate control result downstream as machine evidence.

## First plant decision

The first intended coupling question is:

> Is additional PF voltage, current, slew and diagnostic/control capability justified by the resulting reduction in vertical-loss frequency, downtime, component damage and lost electricity?

This requires a validated machine-level control result and an explicit event-frequency/repair model. Until then, the plant workflows are reproduction infrastructure only.

## Claim boundary

A successful software reproduction is not a validated pilot-plant design, an economic forecast, a licensing case or evidence of sustainable fusion.