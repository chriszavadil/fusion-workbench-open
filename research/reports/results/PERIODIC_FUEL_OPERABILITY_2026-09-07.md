# Fusion continuation: indefinitely repeated fuel-operation test

## Goal and present status

The objective is reliable net electricity from fusion fuel, not energy from nothing. The whole plant must export more usable electricity than it consumes across startup, generating phases, dwell and outages, while respecting fuel, equipment-life and other engineering constraints. The 400 MW average target used in this branch is a study target, not the definition of fusion success.

This continuation executed a stricter fuel-operability gate on the existing four-state ledger. It does NOT solve fusion, establish experimental self-sufficiency, validate an integrated reactor, or establish novel generic inventory mathematics. The earlier pump-heat and fatigue corrections remain in force; the superseded 406.5 MW / 20,000-cycle candidate is not reinstated.

## Completed work

- Reproduced the previous 73 new-module tests against the original authenticated power archive.
- Implemented the unique limiting periodic orbit and complete reserve-minimum test; evaluated 36 critical-TBR scenarios and six equal-annual-burn outage comparisons.
- Evaluated 12 inverse operating-parameter requirements in a separately declared adaptive follow-on.
- Final suite: **127 passed in 1.75 seconds, zero failures and zero skips**, including 54 tests added in this continuation. This is the assembled audit suite, not every test in the GitHub repository.
- The 36+6 scenario run took 7.3264 seconds locally. Inputs were saved and hashed before evaluation. Exact transitions, a separate matrix-exponential fixed point and an adaptive ODE replay cross-check the arithmetic.

No full PROCESS optimization, OpenMC transport, new hosted job, cloud resource or physical experiment ran here. Existing local numerical tools were sufficient for this calculation.

## What changed scientifically

Previously, a supplied startup stock could support a 60-day run even when the plant was slowly losing fuel. The new gate asks whether the infinitely repeated schedule has an available-fuel inventory that remains above a stated reserve at EVERY time, without further imported tritium. It includes radioactive decay and residence-time holdup. A failed limiting periodic orbit cannot be rescued indefinitely by a finite one-time stock under unchanged model assumptions.

This is an important distinction in the test, not a claim that the mathematical method is new. The proof and its restrictions are in `docs/PERIODIC_FUEL_OPERABILITY_PROOF_2026-09-07.md`.

### Explicit average-pass / reserve-fail witness

Declared case: 2% effective core burn fraction, tritium-puff/core-input ratio 10, 80% fast recycling, 0.01% unrecoverable loss per exhaust pass, 99% blanket delivery, and a 0.5 kg mathematical reserve.

| Quantity | Result |
|---|---:|
| Necessary average-balance TBR, including decay and reserve | 1.0693121775 |
| Minimum TBR respecting the full periodic reserve | 1.0695079561 |
| Deliberately chosen TBR between these boundaries | 1.0694100668 |
| Limiting minimum available inventory at that test point | **0.334474 kg** |
| Required reserve in this scenario | **0.500000 kg** |

The average condition passes, but the pulse trough misses the reserve by approximately 0.165526 kg. This is not a claim that a real machine ran out of fuel; it is a reproducible counterexample to accepting an average-only test.

## Requirements that can guide the next physical investigation

With a fixed assumed TBR of 1.15, 0.5 kg reserve and 80% fast recycling, the inverse model provides alternatives. Each row changes only the stated variable while retaining the other assumptions:

| Test of the high-throughput scenario | Conditional boundary |
|---|---:|
| At 2% effective core burn and puff/core tritium ratio 10, maximum unrecovered loss per exhaust pass | **0.0245106%** |
| At 0.05% loss and puff/core tritium ratio 10, minimum effective core burn fraction | **4.02277%** |
| At 2% effective core burn and 0.05% loss, maximum puff/core tritium ratio | **4.46887** |

The original high-throughput case (ratio 10, burn 2%, loss 0.05%) requires TBR **1.2913934**, above the assumed 1.15. Reducing the assumed loss to 0.01% lowers the threshold to **1.0695080**. Even routing all exhaust through fast recycling does not rescue the high-loss case at TBR 1.15. Faster recovery changes holdup and decay; it does not replace permanently lost fuel.

These are NOT measured recovery capabilities, actual operating limits, or validated plasma-design changes. The gas ratio is tritium throughput specifically, not total D+T gas throughput. Changing isotope mixtures or particle flows can affect core performance and divertor operation; this ledger does not model those effects.

## Outage timing matters separately from annual burn

Two schedules were compared with exactly the same annual burned mass and 2,837 pulses: one clusters the unused time into an annual outage, while the other distributes it between pulses. Processing continues throughout both schedules. For the ratio-10, 0.01%-loss scenario, required TBR is approximately **1.0705229 clustered** versus **1.0698812 distributed**.

At EACH schedule's own critical TBR and the same 0.5 kg reserve, maximum available inventory is approximately 6.744 kg versus 2.072 kg. Because these maxima use slightly different breeding ratios, they are not a strict fixed-TBR storage-only comparison. Neither schedule is asserted to be physically achievable maintenance planning. The result demonstrates why annual availability alone does not specify the inventory requirement.

## Numerical evidence

The largest independent matrix-versus-closed-form initial-state difference was below 1.9e-9 kg in the three saved checks. The test suite also checks complete orbit closure, conservation-related transitions, limiting behavior, invalid inputs, a continuous-burn limiting case, interior extrema, sufficient empty-reservoir startup stock, and both sides of every inverse boundary. These checks establish implementation consistency, not experimental validation.

## Assumptions still requiring data

Common assumptions: fast residence 360 s; slow residence 14,400 s; blanket residence 172,800 s; half-life 12.32 years; blanket delivery 99%; rectangular burn at the original archived DT power; pre-burn 701.3463 s; burn 7403.5870 s; post-burn 791.3463 s including 600 s dwell. The source power ZIP and its internal evidence manifest are verified before use.

No maximum store size, exported tritium, fleet-growth requirement, random failures, shutdown of processing, isotopic-separation dynamics, spatial transport/trapping, ramp consumption, or coupled plasma-power calculation is included. Reserve values 0, 0.5 and 2 kg are diagnostic choices only, not safety guidance. Large unexported surplus inventories must not be interpreted as necessary operational stocks.

## External research and the next evidence gate

Primary literature already treats fuel-cycle integration and direct recycling. Meschini and Moscheni's June 2026 preprint examines gas fueling, isotope mixtures, recycling and plasma performance together. Its data-availability statement identifies Zenodo 10.5281/zenodo.20399975. That dataset was identified, but its files were NOT fetched or used to calibrate this calculation.

The March 2026 multi-fidelity tritium-workflow paper supplies open PathSim/PathView models and a public code/data repository. The repository tree was actually read through the connected GitHub tool (tree SHA 31aedef8aa12205c7ba71fc1b9d80b2ac443e065); source graphs, results, and a license file are present. No complete framework reproduction is claimed. Its liquid-breeder/bubble-column cases are NOT interchangeable with this project's HCPB ceramic blanket. Reuse the framework and relevant validation methods, not incompatible blanket performance numbers.

Next high-value task: obtain usable, provenance-preserved fuel-stream data and HCPB release/recovery measurements; fit bounds without using evaluation cases; replace scalar residence assumptions where transport models are needed; then combine the fuel test with the SAME physical geometry's neutron heating, TBR, pumping and magnet-lifecycle solve. A newly favorable abstract component value is not integrated closure.

## Compute and continuity

The local Python/SciPy environment works. In this turn PROCESS and OpenMC were not installed, and DNS resolution failed for GitHub/raw GitHub/PyPI. These local failures are distinct from earlier hosted runner-allocation failures; their underlying account/billing cause is unverified. No unchanged heavy jobs were resubmitted. Integration discovery did not provide a verified Azure execution connection. No account settings or spending limits were changed.

No further user approval was needed for this local research. Larger source-matched execution needs a functioning compute route, and ultimately physical validation needs relevant data or collaboration. No unattended/off-turn research team has been established.

## Reproduction

```sh
python -m pip install -r requirements-periodic-audit.txt
python scripts/audit_periodic_fuel.py --archive inputs/process-power-cycle-33906304781.zip --output results
python scripts/audit_fuel_operating_limits.py --archive inputs/process-power-cycle-33906304781.zip --output results
FUSION_POWER_ARCHIVE=inputs/process-power-cycle-33906304781.zip OPENBLAS_NUM_THREADS=1 python -m pytest -q tests/test_coupled_candidate.py tests/test_fuel_campaign.py tests/test_periodic_fuel.py tests/test_fuel_operating_limits.py
```

Input archive SHA256: `5aae03f0d4dc4e7eff11b46488f6c3bddc290d29a759cd38712ea79a0b9b627b`.
Prior research commit: `18c2d9f4daf9753d14739e5ca02cd14d51e648dd`.
Full numerical results and hashes are preserved in the downloadable checkpoint; the repository stores reproducible source, frozen inputs, compact results, tests, proof and report. Result JSON contains measured runtime, so a rerun can change its file hash without changing scientific quantities.

Primary sources checked 7 September 2026:
- IAEA fusion explanation: https://www.iaea.org/newscenter/news/what-is-nuclear-fusion (used for basic mechanism, not dated deployment forecasts).
- Abdou et al., fuel-cycle self-sufficiency requirements: https://doi.org/10.1088/1741-4326/abbf35
- Meschini and Moscheni, plasma-fuel-cycle interface: https://arxiv.org/html/2606.28043v1
- Multi-fidelity fuel-cycle workflow: https://arxiv.org/html/2603.25751v1
- Read public source tree: https://github.com/rossmacdonald98/PathView_Paper
