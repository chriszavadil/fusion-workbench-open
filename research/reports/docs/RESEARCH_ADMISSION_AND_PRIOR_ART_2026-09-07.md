# Research-value audit: retire duplication, require a decision

## Decision

The user's concern is justified. Much recent work established implementation correctness or illustrated documented mechanisms, not new fusion physics or an improved reactor. Preserve useful tests and provenance but retire generic assumed-parameter sweeps as active discovery work. More cases, code, reports, test passes or accelerator throughput are not scientific progress metrics.

This is a targeted review, not an exhaustive novelty/patent survey. Absence of an exact search match is not proof of originality. Older papers' quantitative limits remain conditional on their assumptions, not universal limits on future fusion plants.

## Prior-art / action matrix

| Project subject | Prior work actually examined | Disposition |
|---|---|---|
| Burn fraction, exhaust losses, processing reliability and breeding margin | Abdou et al. 1986 [1], Nuclear Fusion 61 (2021) [2] | Established requirements methodology; reuse as baseline, no new generic loss/burn sweeps. |
| Dynamic inventories, residence times, startup stock, reserve and availability | [2] and PathSim/PathView multi-fidelity workflow [3] | Established domain. Our periodic-orbit criterion is a standard-method application. Keep its counterexample as a regression, not a general-theory novelty claim. |
| Bulk diffusion versus surface limitation | Neutron-irradiated ceramics study from 1989 [4]; Kulsartov 2023 [5] | Known mechanisms. The assumed 10x-D/fixed-surface example is illustration, not materials discovery. |
| Shutdown temperature, desorption and concentration profile | Irradiation experiment and fitted diffusion/desorption model [5] | Documented physical issue. Our linear Robin surrogate is not the paper's nonlinear model; difference alone is not an advance. |
| Biphasic interface effects | Ran et al. 2024 [6] | Prior model includes interphase transport absent in our homogeneous sphere. Reuse relevant hypotheses, not incompatible coefficients. |
| Material release versus usable downstream fuel; component downtime | [3] | Integration concept already implemented. Our sequential reservoirs and temperature-order examples are conditional checks, not a validated control improvement. |
| Gas/wall depleted-source reproduction | [3] section4.2 identifies a TMAP/FESTIM V&V case | Completed independent replication; regression-only unless an identified code change warrants retesting. |
| Gas fueling, isotope composition, direct recycling and plasma interaction | Meschini/Moscheni June2026 [7] | Existing analysis is more coupled than our ledger. No claim that gas-puff changes leave plasma power unchanged; pump-bypass ideas are also prior art. |
| Pump-work heat feedback, enabled constraints, consistent blanket geometry | PROCESS source and our previous audits | Corrections to our own candidate construction, not new energy physics. Superseded406.5MW/20000cycle claim stays retired. |
| Native fatigue-step sensitivity changes model feasibility | Exact source/current public fixture and issues [8-11] | Narrow software-verification contribution candidate; exact reproduction completed, originality and maintainer acceptance not established. |

## A bounded useful task completed here

The fatigue discrepancy was previously checked using our mathematical reimplementation. This time the exact upstream method bodies were executed, with source Git hashes verified before use. Both the pinned version and current main reproduced the issue on the upstream authors' own public regression input. An adaptive integrator uses the SAME upstream stress-intensity function, and a separate algebraic implementation plus step refinement check the result.

Native current code gives1113.587563 cycles on its public regression input versus995.705372 with event-located integration. A deliberately selected290MPa/9.813mm case gives20718.593779 versus19755.640409, flipping a20000-cycle numerical constraint. This is not an optimized magnet, measured life, physical safety result or new fracture theory. See the review packet and executable code. No upstream issue or email was sent.

This task now has a completion point: a reviewable reproducer. Do not turn it into an indefinite sweep or substitute it for the larger fusion goal.

## Admission criteria before another research run

Record: exact unresolved question; nearest primary references; strongest reproducible baseline; actual data and compute readiness; proposed difference; the design/measurement decision that could change; and a finite falsification/completion rule. Classify the task as discovery, replication, validation, integration or software correction. Missing evidence blocks promotion as discovery, not useful bounded verification.

Accept evidence such as a verified external implementation discrepancy, a calibrated prediction that survives unused measurements, or a same-design performance improvement after costs and competing constraints. Do not use test count, hypothetical efficiencies or a failure to find prior art as substitutes.

## Revised queue

1. **Physical discrimination with compatible data.** Inspect received specimen/source/temperature/isotope traces and instrument response. Compare published diffusion/desorption baselines before adding complexity. If the data cannot distinguish mechanisms, report non-identifiability and identify the missing measurement instead of choosing a favorable fit.
2. **Same-design comparison.** Once the execution/data route exists, evaluate fuel response, thermal hydraulics, power and magnet lifecycle on one physical design. A coupling framework alone is not novel; the question is whether a justified intervention improves the design after penalties and uncertainty.
3. **Bounded upstream review.** Preserve the fatigue packet for maintainer scrutiny, duplicate assessment and full-framework checks. A possible small software correction must not become the whole research program.

Generic reservoir, perfect-sink/Robin-sphere, arbitrary temperature-order and faster-diffusion sweeps are retired as discovery leads. Reopen only for new evidence or a specified comparison that changes a decision. No GPU/plugin branch without a validated physical target and measured compute bottleneck.

## Exposure and validation

Published shutdown figures and fitted coefficients have already been seen. Later receipt of the corresponding raw files does NOT make the entire experiment unseen. Disclose prior exposure; distinguish raw-interval holdouts from genuinely independent specimens/experiments. Preserve units, instrument lag, isotope fractions and permissions. No transplanting liquid-blanket or incompatible ceramic parameters.

## Primary sources and inspected scope

[1] Abdou et al., 1986, DOI10.13182/FST86-A24715. Society/publisher abstract: https://wx1.ans.org/pubs/journals/fst/a_24715 . Precedence only, not historical numerical requirements imported as current limits.
[2] Abdou et al., Nuclear Fusion61,013001(2021;online2020), DOI10.1088/1741-4326/abbf35. Publisher abstract inspected; no raw data imported.
[3] Delaporte-Mathurin et al., arXiv:2603.25751v1,20March2026. Full HTML, especially sections2,3.4,4.2,5: https://arxiv.org/html/2603.25751v1 . No native framework run this turn.
[4] Tritium diffusivity in lithium-based ceramic breeders irradiated with neutrons, Fusion Engineering and Design8(1989)355-358, DOI10.1016/S0920-3796(89)80131-0. Publisher abstract inspected: https://www.sciencedirect.com/science/article/abs/pii/S0920379689801310 . Bulk/surface competition explicit.
[5] Kulsartov et al., NME36(2023)101489, DOI10.1016/j.nme.2023.101489. Author PDF, pages4-5 and figures inspected: https://publikationen.bibliothek.kit.edu/1000161583/151216760 . Raw histories not acquired; phenomenological-fit limits retained.
[6] Ran et al., Ceramics International50(2024)22421-22429, DOI10.1016/j.ceramint.2024.03.343. Publisher abstract/introduction/available sections, not raw data.
[7] Meschini/Moscheni, arXiv:2606.28043v1,June2026: https://arxiv.org/html/2606.28043v1 . Preprint; linked Zenodo data remain unfetched.
[8] PROCESS current source: https://github.com/ukaea/PROCESS/blob/620d1e9a38f1b3c6d2597956c8556e9ab6c17037/process/models/cs_fatigue.py ; public fixture tests/unit/models/test_cs_fatigue.py at same commit.
[9] https://github.com/ukaea/PROCESS/issues/3095 : older stress-expression corrections.
[10] https://github.com/ukaea/PROCESS/issues/4530 : dormant a>c bending exponent defect, already fixed in current source and not rediscovered here.
[11] https://github.com/ukaea/PROCESS/pull/2984 : rearchitecture/JIT and optimization convergence. Targeted searches covered ncycle, fatigue step, fatigue convergence and related PRs; no claim of exhaustive search.

Full audit narrative, exact outputs, source snapshots, tests and input archive are preserved in the downloadable research-value checkpoint. No public submission, cloud provisioning or experimental result occurred in this turn.
