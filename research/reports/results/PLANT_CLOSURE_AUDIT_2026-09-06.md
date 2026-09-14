# Fusion: whole-plant closure audit — 6 September 2026

## Verified disposition

Continue PR #42 toward a material-matched HCPB plant case. The original report's “0/8 feasible” classification is not supported: the raw evidence shows **1 numerically feasible baseline, 7 unsupported configurations, and 0 completed coupled breeding-feasibility tests**. The baseline has `ifail=1`; the seven other cases raise `Constraint 52 is only supported when running the IFE model`. No raw MFILE contains a `tbr` field. Missing values were previously reported as zeros. Those are not failed-breeding results.

This audit supersedes the old interpretation, not the immutable original outputs. Solver convergence alone is not whole-plant validation; nonconvergence alone is not proof of physical impossibility.

## Executed here

All three original archive SHA-256 hashes and their embedded per-file evidence manifests were verified. The audit independently integrated all eight power profiles, checked all seven electrical-balance time points in every case, computed 24 fixed-design accounting cases and 16 dwell-budget scenarios, assessed 42 neutron-screen points, and rejected the unmatched plant coupling. **40 tests passed, no skips.** Maximum pulse-energy disagreement: 2.33e-10 kWh. Maximum pointwise power-balance disagreement: 2.28e-13 MW.

No new PROCESS optimization, OpenMC transport, fuel-inventory simulation, or physical experiment ran in this continuation. These are new accounting and conditional uncertainty analyses of authenticated earlier outputs.

## New electricity result: hold the plant fixed

The baseline gives 400.0225 MW net at flat-top, but 271.0234 MW averaged over its complete pulse/dwell cycle and **216.8188 MW at assumed 80% additional availability**. The old flat-top-times-availability figure of about 320 MW omitted the pulse-cycle effect.

The baseline delivers 181.0551 MW of exclusively electron-cyclotron heating/current drive using 362.1102 MW of electricity. The new test fixes delivered heating, fusion power, geometry, gross generation, other electrical loads and non-dwell phase durations. Only injector electrical consumption and dwell are changed.

| Fixed-design scenario | Wall-plug efficiency assumption | Dwell | Flat-top net | Average at assumed 80% availability |
|---|---:|---:|---:|---:|
| Baseline | 50% | 1,800 s | 400.0 MW | 216.8 MW |
| Shorter dwell | 50% | 300 s | 400.0 MW | 271.7 MW |
| Shorter dwell + efficiency | 60% | 300 s | 460.4 MW | 314.4 MW |
| Shorter dwell + higher efficiency | 70% | 300 s | 503.5 MW | 344.9 MW |

The last case adds 128.1 MW, or 59.1%, in this electrical-accounting counterfactual. These efficiencies, dwell times and availability values are assumptions, not demonstrated equipment performance. Changes in injector waste-heat removal, pulse transients, storage, fatigue and maintenance remain unmodelled.

The older PROCESS sensitivity reoptimized to keep about 400 MW flat-top net. At 70% efficiency it reduced fusion power from 2,064.1 to 1,584.2 MW, and gross generation from 1,156.2 to 870.7 MW. That is a redesign, not the same fixed plant. Its nearly unchanged average electricity does not show that better heating efficiency lacks value.

### Concrete requirement budgets

At 60% heating efficiency and 80% availability, a diagnostic target of 300 MW average permits at most **612.0 s dwell**. At 70% efficiency and 80% availability, even zero dwell gives only **361.0 MW** average within this frozen-profile family, so dwell reduction alone cannot reach 400 MW. At 70% efficiency and 90% assumed availability, 400 MW requires about **98.9 s dwell or less**. These are conditional budgets, not operating recommendations or universal limits on fusion.

## Critical coupling failure

The PROCESS MFILE explicitly identifies **CCFE HCPB**, with helium coolant, lithium orthosilicate, titanium beryllide and steel. Its major/minor radii are 8.0/2.6667 m, elongation 1.85, triangularity 0.5, and inboard/outboard blanket thicknesses 0.70/1.00 m.

The OpenMC screen instead uses **liquid Pb17Li** around a 1 m-radius spherical cavity and simplified 2 cm steel wall. The geometry and material system do not match. Their outputs cannot establish one plant's electricity and fuel balance.

The new coupling identity gate rejects this pairing. It requires matching geometry, material inventory, neutron source and nuclear-heating-feedback provenance. A pass would only establish model identity, not physics validation. Native HCPB material fractions are incomplete as a spatial inventory and must not be silently renormalized; a lithium-isotope prescription is also missing from the MFILE.

## Separate Pb17Li margin diagnostic

The screen has five statistical batches per point. A one-sided Student-t/Bonferroni diagnostic for 42 points uses a multiplier of **6.847142** on the reported standard error, rather than 2. It is conditional on independent, approximately normal batch means; the original statepoints and batch histories were not retained. Nuclear-data and geometry uncertainty are not included.

| Spherical Pb17Li point | Conditional grid lower TBR | Additional fractional TBR reduction that would consume its margin over 1.15 |
|---|---:|---:|
| 60 cm, 80% Li-6 | 1.1870 | 3.1% |
| 60 cm, 90% Li-6 | 1.2229 | 6.0% |
| 80 cm, 60% Li-6 | 1.3729 | 16.2% |
| 80 cm, 80% Li-6 | 1.4271 | 19.4% |
| 80 cm, 90% Li-6 | 1.4430 | 20.3% |

These are algebraic loss-budget sensitivities, not predicted geometric losses or measured TBR. The 60 cm candidates fail a hypothetical 10% reduction stress. TBR 1.15 is a scenario threshold, not universal fuel self-sufficiency. Full spherical coverage has not been proved to upper-bound every realistic arrangement; failure of this screen does not prove a different tokamak impossible.

## Next research gate

Retain the pinned HCPB baseline, obtain a complete material/isotope/geometry/source contract, reproduce an established lawful HCPB benchmark, and carry matched neutron heating and breeding into the same power/cooling and time-dependent fuel-accounting model. Compare fixed-design and reoptimized cases separately. Do not rerun unsupported tokamak constraint 52 or enlarge an unmatched blanket sweep.

The FNG-HCPB OpenMC benchmark already exists in JADE. Issue #450 marks its inputs and experimental data as not freely redistributable and refers to SINBAD licensees. No restricted files were downloaded. This is a restriction on that identified benchmark, not proof that all useful public work is blocked. The material-matched calculation remains unfinished; the audit is not a fusion breakthrough or a reason to abandon useful follow-on work.

## Reproduction and primary sources

Source repository commit: `40cdde9f77c67e6e16fdac221fd1462a7ea3cb1f`, branch `research/reactor-feasibility-v1`, PR #42. PROCESS v3.4.2: `c0ae5b28649f2b20fb7efc7904628b6defe4151c`.

| Original ZIP | Run | Artifact ID | SHA-256 |
|---|---:|---:|---|
| process-power-cycle-33906304781.zip | 33906304781 | 9949782922 | `5aae03f0d4dc4e7eff11b46488f6c3bddc290d29a759cd38712ea79a0b9b627b` |
| openmc-pb17li-33906304435.zip | 33906304435 | 9949937103 | `3476dd8251dfd96ade76b457cb95d46b69afc026596836d0cdb6f4f3a6a965db` |
| process-reactor-feasibility-33906304626.zip | 33906304626 | 9949678670 | `8fcefa7510ab2abe8b82c9b89f0e164ac78f6e3f89216ce333db727a3c00abab` |

```sh
python -m pip install -r requirements-audit.txt
python scripts/audit_plant_closure.py --archive-dir inputs --output results
FUSION_AUDIT_ARCHIVE_DIR=inputs python -m pytest -q tests/test_plant_closure_audit.py
```

The downloadable checkpoint preserves all three exact original ZIPs, full new result JSON, source, tests and detailed report. The full result JSON SHA-256 is `7ea2bf811840dbe54788e8ddd6521da11f4f090c3f0f67c7b7c68dd904eaa4d6`; the repository summary preserves the key values and contract.

References checked 6 September 2026:
- OpenMC batch statistics and Student-t assumptions: https://docs.openmc.org/en/stable/methods/tallies.html
- OpenMC tally confidence intervals: https://docs.openmc.org/en/stable/pythonapi/generated/openmc.lib.Tally.html
- Existing benchmark and redistribution status: https://github.com/JADE-V-V/JADE/issues/450
- FNG-HCPB OpenMC benchmark publication: DOI 10.1080/15361055.2025.2567167 (abstract/index metadata only; full paper not reviewed here).
