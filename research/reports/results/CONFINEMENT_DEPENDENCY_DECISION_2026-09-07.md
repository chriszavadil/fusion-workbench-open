# Full-systems confinement dependence: continued through two failed starts

## Decision
The conceptual systems family need not retain its original internal confinement multiplier1.20. A new full-PROCESS point at approximately9m major radius converges at internal hfact1.02963, and a second solve with the native radius objective converges under a1.03 cap. The original27constraints and20design variables remain; no thermal efficiency, heating efficiency, pump or lifetime requirement was relaxed. This is a candidate-specific numerical trade, not new plasma physics, an experimentally validated confinement prediction, or a fusion breakthrough.

Keep the8.38m candidate and its later component studies as a separate reference. The9m comparator has a different geometry. Its pressure/heating/material/fuel results must not borrow the smaller point's header allocation or proposed31-34MW circuit budget. No neutron breeding or experimental fuel-recovery closure follows from these runs.

## Research before the runs
Official PROCESS documentation and pinned source describe hfact as a multiplier on a chosen empirical confinement scaling. The active option34 isIPB98(y,2), with i_rad_loss1(core radiation subtracted in the internal loss-power convention). That internal multiplier must NOT be relabeled directly as every experiment's global H98 value. Confinement power and stored-energy definitions must first be reconciled. The published STEP-0D work(arXiv2305.07285v2) already couples equilibrium,pedestal and transport models and tests against a confinement database; this experiment does not reproduce or replace it.

The targeted question was whether the original lifetime/power systems family can satisfy its constraints with less internal enhancement, not whether increasing size can generically help confinement(that is established). The original three-run admission named twoH1.0 attempts separated by at most oneH1.1 continuation bridge. It excluded arbitrary scan points and any relaxation of engineering bounds.

## Completed full-framework sequence
| Case | Solver disposition | hfact | Major radius m | Conditional average net MW |
|---|---|---:|---:|---:|
| Prior original point |Previously converged|1.20000|8.37953|213.69132|
| H1.0 direct start |ifail5; not accepted|1.00000|Not an accepted point|None|
| H1.1 continuation bridge |ifail1|1.10000|8.72623|212.53175|
| H1.0 from bridge |ifail5; not accepted|1.00000|Not an accepted point|None|
| Direct internal-H objective |ifail1|1.029628|9.00000|211.54742|
| Native radius-objective check with1.03cap |ifail1|1.03000|8.99846|211.55310|

All successful points retain approximately400MW net at flat top. Average values integrate the modeled pulse and multiply by assumed80%availability, not measured uptime or complete shutdown electrical accounting. Other retained assumptions:50%EC wall-plug efficiency,40%thermal-to-electric conversion,1800s dwell,7200s minimum burn, original pumping/heating model and8-9m radius bounds.

The twoH1.0 cases violated equality constraints at their final states and were not promoted just because their raw power fields looked close to400MW. A local optimizer returning ifail5 does not prove that allH1.0 physical designs, or even all mathematical solutions of this bounded family, are impossible.

## Direct requirement search instead of another arbitrary sweep
After the inconclusive starts, a separate adaptive-follow-on admission allowed one direct minimization and one native-objective validation. Pinned PROCESS does not offer an H-factor objective in its default catalog. A small runtime adapter returned data.physics.hfact to the existing optimizer; all model/constraint evaluations remained native except the already-declared fatigue/mission integration from the original baseline. No new general optimizer was built.

The direct solve returned hfact1.0296279195464582 at R8.999999999973625m. Its output objective value equals hfact, confirming the adapter executed. The native banner still calls slot1 major radius; the manifest and this report supersede that banner for the custom-objective case. The independently executed native-radius follow-on has norm_objf=0.2R as expected and converges at R8.998463065871626m, hfact1.0299999999825042. These checks support a feasible numerical comparator, not a certified global minimum or exact threshold separating feasible and impossible reactors.

The inverse admission intended to start at the feasibleH1.1 point. The shared driver copied its labeled design values but then initialized hfact to its1.2 upper cap. This initialization deviation is preserved in VALIDATION.json and the raw input, not concealed. It changes the initial guess, not the admitted bounds/constraints. No claim is made that the first inverse evaluation itself was feasible.

## New point and retained physical caveats
The native1.03 follow-on predicts B_axis5.047196T, CS current density9.039066MA/m2, CS radial width0.978929m, CS steel fraction0.905572, conduit16.2383mm and hoop stress191.939MPa. Calculated life76214.009671cycles meets the schedule requirement76214.009565. A separateRK45 integration gives76214.009661cycles. This is an active-boundary fatigue result with no new validated material-uncertainty margin.

Fusion power2174.786MW, primary heat3054.156MW, gross electricity1221.663MW and heating electricityabout400MW are outputs of the same existing empirical systems model. The scheduled pulse energy is729973.8449kWh over9937.5745s. These are neither produced energy nor a physically qualified plant forecast. Several enabled constraints are active, including injected power, burn duration, current/stress margins and the imposed size/confinement trade.

Radiation accounting remains unchanged. The final printed plasma diagnostic is-296.155671MW and the plant diagnostic-0.837499MW. Earlier work associated these with radiation/ohmic reporting conventions, but no new independent energy-boundary certification or diagnostic patch is claimed. Availability, impurity control, empirical confinement scaling, density/current limits, initial crack and fatigue law remain assumptions. No evolving equilibrium/stability/transport calculation, same-geometryTBR, neutron heat map, actual material lifetime or full economics has been validated.

## Verification
Seventeen focused tests passed. The output audit reads actual eq_con and ineq_con keys; the original driver's unused normres export was empty, not zero. Three accepted cases have maximum absolute normalized equality residual below1.7e-11 and worst negative inequality residual above-6.2e-9. Failed cases retain equality residuals0.1451/0.07339 and no accepted power average. All constraint and variable identifiers were preserved.

Pulse-energy and gross-plus-load profiles were independently integrated; gross thermal conversion identity was checked. The largest adaptive/RK45 life difference among accepted cases is1.59e-5cycle. Native objective restoration, labeled seed extraction, invalid objective values and preservation of warnings are tested. The full repository test suite was not run, and numerical precision is not physical uncertainty.

All five solves completed under600second individual guards; no new cloud resources, software install, OS change or unattended agent was created. Source worktree stayed clean. These files retain the campaign label2026-09-07; native run logs crossed into2026-09-08UTC and their original timestamps are preserved rather than rewritten.

## Next research decision
The9m point is an alternate systems comparator, not a replacement for the8.38m geometry already used for the cooling studies. Before spending more neutron or equipment-comparison compute, establish a consistent experimental confinement/radiation-power definition and a profile/transport validation route from published workflows. Then select which geometry merits a fully matched blanket/source/cooling/fuel calculation. No existing headline from either branch can simply be added to the other's output.

The measured-circulator branch reached a specific legitimate evidence barrier: the retrieved publication supplies operating points but not compatible total-state, electrical/shaft and uncertainty definitions or full map coverage. A curve fit at that stage would manufacture evidence. The confinement work proceeded instead, through two unsuccessful solves, a successful bridge, a direct inverse search and a native-objective cross-check. No request for new spending or account permissions is needed for source review and these existing-environment tests.

Primary references used before computation:
- PROCESS confinement/radiation conventions: https://ukaea.github.io/PROCESS/physics-models/plasma_confinement/
- Exact PROCESS source: https://github.com/ukaea/PROCESS/tree/c0ae5b28649f2b20fb7efc7904628b6defe4151c ; core/solver/objectives.py, core/caller.py, models/physics/confinement_time.py, source-default/input/constraint definitions.
- Slendebroek et al., Elevating zero dimensional global scaling predictions to self-consistent theory-based simulations: https://arxiv.org/html/2305.07285v2 . This is prior art and a higher-fidelity validation pathway, not a calculation executed in this turn.

The read-only portable replay was subsequently run from a separate temporary directory, verified source hashes, reproduced all saved audit rows exactly and passed17tests. It did not rerun the optimizer. Original failures, custom-objective labeling and initialization deviation remain in the evidence.
