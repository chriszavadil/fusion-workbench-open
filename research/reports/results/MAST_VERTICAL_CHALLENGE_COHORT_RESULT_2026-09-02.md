# Public MAST vertical-control challenge cohort — result

**Classification:** `challenge_cohort_ready`

- Metadata keyword matches: **325**
- Matches with the exact required PF/current/axis interface: **317**
- Frozen cohort: **50** shots (20 train, 10 validation, 20 test)

## Semantic review without post-result exclusion

| Review tier | Count | Role |
|---|---:|---|
| Tier A: explicit VDE/control loss/instability | 29 | Failure-oriented challenge cases |
| Tier B: broader vertical behavior mention | 19 | Ambiguous behavior / expert review |
| Negative-control mention | 2 | Comments explicitly saying no VDE |

All 50 selected shots remain in the frozen record. The review tiers annotate comment semantics; they do not remove inconvenient cases or change train/validation/test membership.

## Untouched Tier-A test shots

25660, 26192, 26276, 26280, 26282, 26817, 26884, 27762, 28207, 30120

These ten test shots are never used for model fitting or threshold selection. Signal-read failures will be preserved rather than replaced after outcomes are observed.

## Data-quality caveat

A post-shot comment is not a machine-verified VDE label. Timing, cause, direction, and whether the event is an actual VDE must be checked against signals and, where possible, expert-reviewed metadata.

## Next gate

Read exact signal windows for all Tier-A test shots and preserve failures; do not train on the test cohort.

## Claim boundary

Historical MAST metadata selection only—not MAST-U validation, controller effectiveness, a machine operating limit, reactor safety, net energy, or sustainable fusion.
