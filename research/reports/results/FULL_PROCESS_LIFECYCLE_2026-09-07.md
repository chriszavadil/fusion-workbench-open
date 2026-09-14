# Full PROCESS execution and duty-constrained solenoid redesign

## Disposition

The full PROCESS systems framework now executes on the authorized desktop. Four complete optimizations returned ifail=1: the archived baseline, native20k, adaptive20k, and adaptive30y_warm_fixed. This is integration/design-comparison progress, not new fusion physics, a demonstrated30-year magnet, or validated power plant. Retired generic fuel/diffusion sweeps were not resumed.

The final conceptual point satisfies the implemented approximately76465-cycle CS requirement while retaining400MW net at flat top. Its pulse-cycle net multiplied by assumed80% availability is213.6913MW. That is NOT400MW continuous output. Same-design neutron breeding/heating, calibrated fuel recovery, reliability and independent physical validation are not closed.

## Execution route and exact reference

[Personal identity or local execution location omitted from this public copy.]

An initial unpatched run failed during Windows output cleanup: upstream unlinks open temporary output files. A runtime-only shim closes those two handles before unlink and reopens normal output; no equations or tolerances change. The successfully rerun baseline input exactly matches the original SHA256 5a816f638a48fd0263aed36fda58187bff46e23b5e2f787383bef8905d891e94. Its216.8187594559644MW conditional average reproduces the archived216.8187594484642MW within1e-6MW.

Successful full runs took about49-68seconds after setup/compilation. They were single-threaded with600second per-run timeouts. No GPU, paid cloud resource, system-Python change, recurring job or unattended research agent was created. This bypasses the older GitHub runner block; it does not identify or repair that service's original failure cause.

## Completed comparison

All runs retain50% EC efficiency,40% thermal-to-electric conversion,1800s dwell, the existing pumping model,80% assumed availability and8-9m radius bounds. All26 original constraint identifiers remain enabled. Fatigue cases add90; the final case also adds iteration variable37, CS current density, bounded1-18.5MA/m2.

| Full optimization | Major radius m | CS current MA/m2 | CS radial width m | Steel fraction | Adaptive-checked cycles | Conditional average net MW |
|---|---:|---:|---:|---:|---:|---:|
| Baseline, no fatigue constraint |8.0000|18.5000|0.5383|0.7151|5449.015|216.8188|
| Native20000-cycle constraint |8.2021|18.5000|0.4235|0.8554|19062.196|214.1844|
| Adaptive20000-cycle constraint |8.2220|18.5000|0.4168|0.8600|20000.000|214.1417|
| Adaptive30-year duty; CS current freed |8.3795|10.1856|0.8546|0.8975|76464.586|213.6913|

Native and adaptive20k use byte-identical input files. The native optimized point meets its native calculation but falls short under adaptive evaluation. Reoptimizing with adaptive integration closes the20k criterion inside the full framework.

The30-year constraint is reevaluated at every point as life_plant*availability*31557600/full_cycle_seconds. At the final9905.008899s cycle it requires76464.585515cycles; adaptive life is76464.585540. A separateRK45 evaluation gives76464.585529. This active-boundary result has no newly established fatigue uncertainty margin.

The final geometry has189.0204MPa hoop stress,15.1145mm conduit thickness, CS start current/critical ratio0.69093625 and TF operating/critical ratio0.699999999. No superconducting, flux, plasma, power or geometric constraint was removed to obtain it. The final and20k cases have different design-variable sets; their difference is a combined redesign comparison, not a pure lifetime-only causal penalty. No global-optimality claim is made.

## Failed attempts preserved

The first unpatched Windows baseline failed at output cleanup. The30-year cold start returned ifail5 without a feasible numerical point; this was not treated as proof of physical impossibility. One admitted warm start used the solved adaptive20k point. Its initial file was rejected before optimization due to an obsolete alpha-fraction name. Only that spelling was corrected; the warm-start solve then converged in14iterations. All three unsuccessful records remain in the raw evidence.

## Independent checks and retained warnings

Independent trapezoidal integration reproduces pulse energy within1e-5kWh and gross-plus-load profiles within1e-7MW in all four completed cases. Gross electric output equals primary heat times modeled turbine efficiency. The largestDOP853/RK45 fatigue difference is1.1e-5cycle. Eighteen focused integration checks passed; zero failures/skips. The full repository test suite was not run, and test count is not a scientific advance.

The printed plasma residual at the final point is-294.587349MW, numerically negative outer radiation. Source inspection and documented i_rad_loss=1 behavior show a convention mismatch: the enforced core balance uses core radiation while the printed diagnostic adds total radiation to that transport quantity. No diagnostic was patched and this is not by itself294.6MW of missing generated electricity.

The separate plant diagnostic is-0.554136843MW, numerically negative modeled ohmic heat; reactor residual is-0.010430535MW, electric residual about-2.3e-13MW. Values are preserved. Matching terms does not establish an independently validated physical energy account. The plant residual exceeds the upstream reporting threshold and remains a review item.

Empirical confinement/radiation assumptions, initial flaws and Paris-law material constants remain unqualified. Availability is assumed, not a reliability result; multiplying average by0.8 does not simulate all extra outage electricity. No source-matched OpenMC/TBR, experimental material-release calibration, plasma-dynamics validation or complete maintenance/economic model ran.

## Public-data access unblocked, not overinterpreted

The actual public record10.5281/zenodo.20399975 and its CSV were downloaded on the desktop. File:puff_data_v3_Zenodo.csv,2769389bytes, CC-BY-4.0; MD5 verified against record2aa367479efd8814fe4f2bcb9613c7ab; SHA2567b5e2e6e5cc67f1ed53ff4a9c882428c3795d7783010e0bec0960f8f84d9ca46.

The compilation has463rows/74columns,265source-flagged experimental and198nonexperimental rows. Eighty-nine rows have positive D-puff and actual-D-core entries; only two of those are flagged experimental. A flag does not establish every field was directly measured; one such row's comment references UEDGE. No column is explicitly named tritium. D-labeled flows cannot silently become tritium flows or recovery calibration. No scaling law was fitted and no ceramic raw time traces were obtained. Preserve per-source experimental/model distinctions before any inference.

A targeted incoming-mail search including Spam found no matching data replies during this continuation. Both requests remain sent. The user handles scheduled notifications; no monitoring automation was added.

## Preserved artifacts and next gate

Complete evidence already on the authorized desktop:
[Personal identity or local execution location omitted from this public copy.]
Size2756208bytes; SHA256371cd3829c9373f424587d20cdf52181b21f57b28a4fc5a9269e1fb30f5f22cd.
It contains raw successful/failed outputs, logs, inputs, attempt-specific source,18-test suite, package records, external CSV/metadata and file hashes; excludes the installed venv and full source clone. The separate chat download is a compact reproducer, not that raw archive.

Exact executed final runner/runtime modules and warm seed are in experiments/full_process_2026_09_07. The current scientific point is now this frozen30-year-duty design, not the superseded406.5MW cross-study candidate. Next: export the full geometry/material/source contract of this point and evaluate matched neutron heating/breeding and cooling, then incorporate compatible measured release/recovery data and reliability. Reuse established benchmarks and do not re-open retired generic demonstrations without a new decision-changing question.

Primary sources: pinned PROCESS repository c0ae5b28649f2b20fb7efc7904628b6defe4151c; https://ukaea.github.io/PROCESS/physics-models/plasma_confinement/ ; https://ukaea.github.io/PROCESS/physics-models/plasma_power_balance/ ; https://ukaea.github.io/PROCESS/eng-models/central-solenoid/ (its no-fatigue-constraint sentence is outdated versus source90); https://zenodo.org/records/20399975 . Prior project checkpoint:d57fb2305ecd84374fccec49e4ed5e73d364ac8a.
