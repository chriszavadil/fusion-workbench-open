# Review packet: PROCESS fatigue step-size sensitivity

Status: privately prepared software-verification evidence; not sent to upstream, not maintainer-accepted, not a new fusion-physics result.

## Question

Does the specific fatigue discrepancy reported by our earlier reimplementation survive execution of the actual upstream method bodies, and can it alter a 20,000-cycle numerical decision?

## Exact inputs and scope

Upstream current main was read at commit `620d1e9a38f1b3c6d2597956c8556e9ab6c17037`. The frozen comparison is PROCESS v3.4.2, commit `c0ae5b28649f2b20fb7efc7904628b6defe4151c`.

| Snapshot | File | Verified Git blob |
|---|---|---|
| Current at audit | process/models/cs_fatigue.py | eac6720169e18bd884de90bf081c91d1cb2d8a28 |
| v3.4.2 | process/models/cs_fatigue.py | 9252217d4e1b259b02cf9b6c1dc92bba8a29ce9d |
| Current defaults | process/data_structure/cs_fatigue_variables.py | ab6a90ab9fea20366a290d2cfb8713b5245ae848 |
| Current test fixture | tests/unit/models/test_cs_fatigue.py | 33bec1e0ba367bc889acbd42725939670fe30751 |

The two numerical methods are extracted by AST from the exact source snapshots. Imports and decorators are omitted; function bodies and argument signatures are unchanged for the native run. NumPy supplies mathematical operations; an object supplies the documented data attributes. This is **not** a full PROCESS installation, full-framework run or Numba-compiled execution.

The comparison keeps the constitutive model unchanged. Adaptive integration calls the upstream stress-intensity function, integrates crack geometry/life continuously and stops at the first specified event. A separately implemented algebraic formula and native-step refinement provide additional numerical checks. Agreement between these computations is not experimental validation of material behavior.

Residual stress: 240 MPa. Initial vertical crack: 0.89 mm; initial radial crack: three times that value. Paris coefficient 65e-14, exponent 3.5, Walker coefficient 0.436, crack-size safety factors 2, fracture toughness 200 MPa sqrt(m), fast-fracture safety factor 1.5. The upstream convention of two load excursions per reported plant cycle is preserved.

## Executed results

| Case | Upstream native 0.1 mm crack step | Adaptive event-located cycles | Native excess relative to adaptive |
|---|---:|---:|---:|
| Upstream public regression input | 1113.587563 | 995.705372 | 11.8391% |
| Authenticated PR42 baseline | 5736.978618 | 5449.014936 | 5.2847% |
| Prior rounded candidate | 19999.940961 | 19070.388948 | 4.8743% |
| Deliberate 20,000-cycle decision witness | 20718.593779 | 19755.640409 | 4.8743% |

Current main and the pinned version give identical native values on these four cases. For the last case, hoop stress is 290 MPa and both conduit dimensions are 9.813 mm. It is deliberately selected near the known threshold, not an independently held-out or optimized reactor design. Native arithmetic passes 20,000; event-located integration fails. This changes a **software constraint result**, not a demonstrated safety classification for an actual magnet.

The public upstream fixture uses stress 659999225.25370133 Pa and both conduit dimensions 0.0063104538380405924 m. The native result reproduces its published expected value 1113.5875631615095.

### Refinement on that public fixture

| Crack step | Calculated cycles |
|---|---:|
| 0.1 mm (unchanged upstream) | 1113.587563 |
| 0.05 mm (explicit diagnostic edit) | 1057.514624 |
| 0.01 mm (explicit diagnostic edit) | 1007.723125 |
| 0.001 mm (explicit diagnostic edit) | 996.725405 |
| Adaptive event-located reference | 995.705372 |

Only the step assignment is changed in the labeled refinement runs. The smaller step approaches the event-located solution. Native explicit integration error and stopping beyond an event both merit attention; this packet does not separately quantify each contribution or establish a universal conservative correction factor.

All four adaptive cases terminate at the radial-crack safety limit. The DOP853/RK45 differences are below 3e-8 cycle for the chosen tolerances. Thirteen targeted tests pass, with zero skips/failures. No full-project test-count increase is claimed as a scientific advance.

## Prior reports and limits of duplicate screening

Issue #3095 already reported other surface-stress formula defects in 2024. Issue #4530 reported the a>c bending-coefficient multiplication/exponent error and has been fixed in the current source. With zero bending, the latter does not cause the discrepancy in this packet. PR #2984 concerned rearchitecture/JIT and optimization convergence. The audited current routine still assigns delta=1e-4 and retains the native loop stopping behavior.

The targeted issue/PR searches did not establish an exact prior report or accepted fix for this step-size/event-location discrepancy. That is **not** proof of originality. Maintainers may have known tolerances, additional context or unpublished comparisons. No upstream issue/PR was opened by this continuation.

## Review request to prepare, not send automatically

Ask whether the native step is intended to carry a documented error allowance and whether an event-aware or tolerance-controlled method is appropriate for near-boundary constraint evaluation. A production change should cover invalid/initially exhausted cases, all relevant geometry branches, performance, optimizer stability, regressions and actual process-framework integration. Do not replace design margins with these numerical checks or infer real material life from this model alone.

## Reproduction

The package includes upstream source snapshots with the UKAEA MIT license, this project's reproduction script/tests, inherited audit dependencies and the exact original power-result archive.

```sh
python -m pip install -r requirements-novelty-audit.txt
OPENBLAS_NUM_THREADS=1 python scripts/reproduce_upstream_fatigue.py --archive inputs/process-power-cycle-33906304781.zip --output results
FUSION_POWER_ARCHIVE=inputs/process-power-cycle-33906304781.zip OPENBLAS_NUM_THREADS=1 python -m pytest -q tests/test_upstream_fatigue_reproduction.py
```

The test fixture regenerates the study in a temporary directory when FUSION_POWER_ARCHIVE is set; it does not merely trust the saved result JSON. Missing input produces skips, not a claimed successful reproduction. The hash check prevents a different upstream file from silently being substituted. Inputs are saved before evaluation, but all cases are diagnostic continuations of prior evidence, not a blind discovery experiment.

Power archive SHA256: `5aae03f0d4dc4e7eff11b46488f6c3bddc290d29a759cd38712ea79a0b9b627b`.
Baseline MFILE SHA256: `cfc2dc341898351c41fe299ba9fcd8bcecbc8d63786a2a17476132254d66672c`.

Primary source/duplicate-screen links: see the accompanying research-value audit. Preserve the snapshot hashes rather than substituting a mutable main branch on reproduction.
