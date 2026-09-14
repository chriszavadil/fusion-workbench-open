# Central-solenoid fatigue gate — 7 September 2026

The authenticated PR42 PROCESS baseline was numerically converged under its enabled constraints, but it did **not** enable constraint 90 (central-solenoid stress-cycle life). Its raw MFILE reports:

- allowable CS cycles `n_cycle = 5736.9786`;
- declared minimum `n_cycle_min = 20000`;
- blanket DPA cycle count `bktcycles = 12105.7120`;
- CS inner hoop stress `stress_hoop_cs_inner = 437.993 MPa`;
- residual hoop stress `240 MPa`;
- initial vertical crack `0.89 mm`;
- turn-conduit dimensions `8.3037 mm × 8.3037 mm`.

Using the exact PROCESS `CsFatigue.ncycle` equations and these frozen inputs reproduces `5736.9786` cycles. This makes the omission a real systems-closure issue, not a reporting discrepancy.

## Derived design targets from the unchanged PROCESS fatigue model

Holding residual stress, crack size and conduit geometry at the baseline values:

- matching the blanket-DPA life (12,105.7 cycles) requires CS hoop stress **≤333.449 MPa**;
- satisfying the declared 20,000-cycle target requires **≤275.453 MPa**;
- the latter is a **37.1% reduction** from the current 437.993 MPa.

Residual-stress relief alone cannot close the 20,000-cycle requirement in this model: even setting residual hoop stress to zero while leaving the 437.993 MPa cyclic hoop stress unchanged yields only about **13,591 cycles**.

A separate conditional manufacturing sensitivity shows that, at unchanged stress and residual stress, the model reaches 20,000 cycles only when the assumed initial vertical crack is **≤0.3746 mm** (versus the 0.89 mm baseline). This is a model sensitivity, not evidence that such defect control is achievable or certifiable.

## Why this changes the active search

The original plant result should no longer be called engineering-feasible without qualification. The next PROCESS gate explicitly turns on constraint 90 while retaining the 400 MWe flat-top requirement. The baseline already uses iteration variable 16 (`dr_cs`) and iteration variable 122 (`f_a_cs_turn_steel`), both of which influence the CS design, so the optimizer is given a chance to find a fatigue-closed plant rather than merely checking the old design after the fact.

Four prospective cases are frozen before outcomes: blanket-life fatigue closure, 20k-cycle closure, and 20k closure combined with 60%/70% ECRH wall-plug efficiency plus 300 s dwell. Electricity, major radius, fusion power, CS thickness, steel fraction, hoop stress and cycle life are recorded together.

## Claim boundary

This is a source-matched systems-model correction and derived design target. It is not experimental fatigue validation, a qualified magnet design, or a fusion breakthrough. A successful PROCESS case would advance to detailed mechanical/material validation; failure would identify which whole-plant trade must move.
