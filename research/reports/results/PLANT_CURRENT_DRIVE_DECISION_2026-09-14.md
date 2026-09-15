# Whole-plant decision: test multifunction heating before another blanket benchmark

## Decision and significance
A specific allocation change produced a materially higher net-electric operating point in the full installed PROCESS model. At the same 8.379532870755202 m major radius, the controlled pair gives 401.659 versus 501.659 MW net during the burn, and 214.683 versus 274.011 MW after integrating the recorded pulse/dwell schedule and multiplying by assumed 80% availability. The conditional average difference is 59.328 MW, or 27.635%.

**This is a design lead, not achieved power or an accepted reactor improvement.** The condition that must now be tested is whether the proposed heating deposition can drive the credited additional current while preserving plasma heating, current-profile stability and control. The alternative leaves only 30 MW in the model's dedicated heating-only allocation. That allocation has not been validated as sufficient. A favorable scalar input does not prove a physical actuator can do both jobs.

The research priority is therefore a candidate-specific integrated current-drive/deposition/control assessment. Repeating generic neutron benchmarks or assuming a better wall-plug efficiency would not answer this question. Existing benchmark work is retained; none of its unresolved validation gates is silently closed.

## Existing work reused and credited
Pulsed versus steady-state current-drive trade-offs, recirculating-power penalties and integrated plasma scenario modeling are already established research topics. Kembleton, Morris, Siccinio, Maviglia and the PROCESS team discuss them in *EU-DEMO design space exploration and design drivers* [1]. EU-DEMO heating-system literature describes multiple heating/control functions rather than a freely removable power allowance [2]. Sugiyama, Aiba, Asakura, Hayashi and Sakamoto use integrated modeling to assess JA-DEMO pulsed scenarios and current-profile requirements [3].

We used the maintained UKAEA PROCESS systems framework, pinned at `c0ae5b28649f2b20fb7efc7904628b6defe4151c`, its native objective 17, current-drive and bootstrap equations, and the project's previously disclosed adaptive-fatigue/pulse-duty adapters. The inherited generic large-tokamak input credits James Morris, UKAEA. We did not build a new reactor solver or claim a new physical current-drive mechanism. Publisher/author-repository abstracts and accessible descriptions were reviewed; no reproduction of the papers' integrated plasma models is claimed.

## The controlled comparison
The existing reference assigns 200 MW of injected electron-cyclotron power as 125 MW credited to current drive plus 75 MW extra heating-only. Both portions heat the plasma. They consume 400 MW of electricity at the assumed 50% wall-plug efficiency.

The alternative assigns 170 MW to current drive plus 30 MW heating-only, retaining the same 200 MW total injection ceiling and the same normalized current-drive efficiency, bootstrap model, confinement limit and wall-plug efficiency. The two final input files differ only in their final heating-only allocation line. Both start from the same exact reference seed.

The major radius is fixed, the other 19 shared variables are optimized, and all 27 original pulsed constraints remain enabled, including the two-hour burn requirement and dynamically evaluated 30-year central-solenoid duty requirement. Both use native objective `i_figure_merit=-17`, maximizing flat-top net electricity. Conditional cycle-average electricity is calculated independently afterward; it is not the optimized objective.

| Quantity | 75 MW heating-only control | 30 MW heating-only alternative |
|---|---:|---:|
| Major radius (m) | 8.379533 | 8.379533 |
| Total injected heating (MW) | 200.000 | 200.000 |
| Heating electrical demand (MW) | 400.000 | 400.000 |
| Power credited with driving current (MW) | 125.000 | 170.000 |
| Field on plasma axis (T) | 5.011595 | 5.280938 |
| Plasma current (MA) | 19.767832 | 20.830235 |
| Fusion power (MW) | 2156.935797 | 2413.360935 |
| Gross electricity (MW) | 1212.635754 | 1347.227464 |
| Internal electrical demand (MW) | 810.976690 | 845.568187 |
| Coolant-pumping electricity (MW) | 281.335177 | 314.804374 |
| Net electricity during burn (MW) | 401.659064 | 501.659277 |
| Conditional average electricity (MW) | 214.683128 | 274.011273 |

**This is not a reduction in total internal demand.** Gross output rises about 134.592 MW while internal demand rises about 34.591 MW; their difference yields the approximately 100 MW higher net output. Increased fusion power supplies the modeled additional energy. The alternative increases field, current and heat-removal requirements. Fixed major radius is not identical full geometry, identical magnets or installed hardware. No cost or construction advantage has been established.

## Why the earlier attempts matter
Six full-model solves were completed, each bounded to 240 seconds and one thread. Two steady-state attempts, at 200 and 350 MW injection ceilings, returned `ifail=5` and no numerically feasible result. Their raw output fields are not feasible electricity predictions. Nonconvergence does not establish physical impossibility or a global design-space exclusion.

A fixed-profile current-balance screen requires about 336.181 MW injected power for continuous sustainment of the archived r838 point, or 390.238 MW for r900, retaining their original extra heating. These are necessary same-profile estimates, not optimized plants.

The next two solves retained pulsed operation but minimized radius. Removing all extra heating gave a converged 8.000 m optimistic bound with 216.758 MW conditional average. Retaining 30 MW gave 8.066453 m and 214.529 MW. Neither result is a validated control design. More importantly, the radius objective and 400 MW output floor made their near-constant output unsuitable for testing an electricity benefit. That objective mismatch was identified before admitting the final controlled, fixed-radius power comparison.

Run admissions and amendments were recorded before their respective executions. The initial three-run budget was expanded explicitly to four for the retained-allocation test and to six to correct the objective mismatch. There was no post-measurement fitting, changed optimizer tolerance or unrecorded parameter sweep. The two failed steady attempts used a rounded xenon initial guess; the final controlled pair uses the exact reference xenon fraction and otherwise identical initial guesses. Solver-native retries in unsuccessful optimizations are preserved in the local logs.

## Verification and unresolved physics
Independent integration of both recorded power profiles reproduces their pulse energies within 1e-6 kWh. Gross-minus-internal equals net within 1e-7 MW. The driven-current/power relation and current-fraction closure were checked. All three equalities and 24 inequalities satisfy the existing 1e-7 numerical acceptance tolerance; the largest equality residual is approximately 5.2e-12 and the smallest control-case inequality residual is approximately -4.5e-9. Exact-input reconstruction reproduces both executed input hashes. The two local optimizations are not proven global optima.

The modeled central-solenoid lifetime is essentially on its required mathematical boundary: approximately 76,462 cycles for the control and 76,298 for the alternative. This is not validated material life or a new reliability margin. Plant-level reporting residuals of approximately -0.556 and -0.466 MW remain visible. The electrical account closes; that does not certify every thermodynamic/plasma convention or physical subsystem.

Both configurations still assume the same 1.2 internal confinement cap, 0.30 normalized drive efficiency, 50% heating wall-plug efficiency, 40% turbine conversion and 80% availability. The conditional average includes modeled scheduled startup/dwell demand through the recorded profile; additional unscheduled-outage electricity is not modeled. It is not measured annual output.

The 30 MW case is an explicit allocation sensitivity, not a validated control requirement. The cited EU-DEMO description separately identifies 30 MW for NTM control, 30 MW for burn control and 70 MW for thermal-instability control in its own preconcept. Those separate roles cannot be covered merely by borrowing one 30 MW number. The current experiment quantifies the payoff worth investigating, not the adequacy of that allowance.

Current-profile stability, launch/deposition geometry, power needed for particular modes and transients, and the availability of simultaneous heating/current-drive roles need higher-fidelity assessment. Higher fusion output also requires same-design neutron heating, breeding, cooling, fuel processing and structure checks. Old header or tritium results cannot be attached to these altered designs. No empirical benchmark discrepancy was converted into a reactor correction factor.

## Next test and reopening rule
Test a specific EC launch/deposition configuration against the final candidate's density, temperature and current requirements. Require the credited current-drive contribution together with adequate control power and an acceptable evolving current profile, using established integrated tools rather than another unconstrained scalar efficiency sweep. If this cannot be met, reject or reduce the allocation lead. If it can, propagate the higher nuclear/thermal loads into one consistent engineering geometry.

Do not repeat the present scalar allocation comparison merely to increase solver-run counts. Reopen it only for a substantiated deposition/control limit, changed validated input, a genuine numerical defect or a declared optimization-robustness question. This study changes the next engineering question, not the accepted reactor configuration.

## Reproduction, display and artifact scope
`research/source/experiments/plant_current_drive_2026_09_14/prepare_inputs.py` reconstructs the exact final pair from `research/approved_inputs/r838.IN.DAT`, verifies both hashes and refuses an existing output directory. Use the same pinned PROCESS and the disclosed runtime adapters for a full reproduction; normal library/version/platform differences should be investigated rather than hidden. The accompanying instructions distinguish arithmetic replay from a new solver execution.

`docs/plant-decision/data.json` contains the exact displayed selected metrics, schedules, hashes and six-attempt summary. It is a reviewed projection, not all raw solver fields. Full six-case inputs, outputs, failed logs, admissions and exact used driver versions are retained locally. Private execution paths and logs are not bundled in the web data. The new standalone browser view uses the actual power ledger and recorded schedules; it does not create spatial physics or run a scientific solver. The existing accepted models and released Unreal binary are unchanged. A fresh end-to-end browser check was not completed: the local browser's navigation was administrator-blocked; it was not bypassed. Numerical, exact-input and source checks are separate from that outstanding UI verification.

## Sources
[1] R. Kembleton, J. Morris, M. Siccinio, F. Maviglia and PROCESS team, *EU-DEMO design space exploration and design drivers*, Fusion Engineering and Design 178 (2022) 113080. https://doi.org/10.1016/j.fusengdes.2022.113080

[2] *Status and future development of Heating and Current Drive for the EU DEMO*, Fusion Engineering and Design 180 (2022) 113159. Publisher and contributing-author repository records. https://doi.org/10.1016/j.fusengdes.2022.113159

[3] S. Sugiyama, N. Aiba, N. Asakura, N. Hayashi and Y. Sakamoto, *Development of pulsed plasma operation scenario and required conditions in JA DEMO*, Nuclear Fusion 64 (2024) 076014. https://doi.org/10.1088/1741-4326/ad49b6

[4] UKAEA PROCESS, exact executed source revision: https://github.com/ukaea/PROCESS/tree/c0ae5b28649f2b20fb7efc7904628b6defe4151c . In particular `process/core/solver/objectives.py`, `process/models/physics/current_drive.py` and the disclosed project pulse-duty/fatigue adapters. No endorsement by the original investigators is implied.
