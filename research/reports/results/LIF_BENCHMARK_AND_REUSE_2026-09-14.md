# Existing lithium benchmark: reproduction is not experimental validation

## Decision
We completed and reviewed the already-admitted OKTAVIAN lithium-fluoride leakage benchmark rather than designing another generic neutron experiment. The one-million-history run had finished before the prior conversation interruption; this continuation recovered and checked it without repeating the transport calculation. It is a reproduction of other researchers' work, explicitly attributed below, not a new fusion experiment or reactor improvement.

The integrated neutron result agrees with the archived OpenMC calculation to approximately 0.00265%, but the corresponding comparison with the IAEA-hosted measurement table gives calculation/table = 0.934688, so the calculation is 6.53% below the table under the stated bin convention. Close agreement with another calculation must not be promoted as agreement with experiment or validation of our reactor's tritium production.

**Action:** retain the candidate's experimental-validation gate as open. Do not apply a 6.53% empirical blanket correction, fit a normalization, tune a source, or launch more identical runs. The remaining questions concern benchmark interpretation, energy-dependent model/data differences and a genuinely compatible tritium-production experiment.

## Before computing: what already existed
Ichihara, Hayashi, Kobayashi, Kimura, Yamamoto, Izumi and Takahashi reported these sphere leakage measurements at the 1988 Nuclear Data for Science and Technology meeting; their abstract explicitly names LiF. IAEA-NDS distributes the selected MCNP input and experimental tables under CC BY 4.0. The OpenMC Fusion Benchmarks project already provides the selected converted model, a helper and archived calculation. JADE already provides a validation framework and describes relevant experimental benchmarks. We reused and credited these resources; constructing another framework or presenting this benchmark as new would have been redundant.

The frozen admission asks a narrow implementation question: can this installed stack reproduce the existing transport calculation, and is its experimental-data interface consistent? Geometry, composition, source distribution and tally boundaries were not fitted. The run used OpenMC 0.15.2, ENDF/B-VIII.0-labelled processed data, two threads, 40 batches of 25,000 source histories, and a fixed seed. Exact input/library hashes are recorded. The run completed in about 232 seconds; no physics input was changed after seeing the result.

## Results with every original bin retained
| Comparison | Computed integral | Reference integral | Computed / reference |
|---|---:|---:|---:|
| Neutron surface current vs archived OpenMC | 0.586397811 | 0.586413367 | 0.999973472 |
| Neutron current vs primary table under matched bin convention | 0.586397811 | 0.627372877 | 0.934687858 |
| Photon surface current vs archived OpenMC | 0.205696844 | 0.205940402 | 0.998817342 |

Units are particles crossing the tally surface per source neutron, integrated only over the listed energy range. The measured-table integral is reconstructed, not a fresh measurement or a re-evaluation of detector response. The table coordinates were matched to the model's listed upper bin bounds. We divide computed bin current by ln(E_high/E_low) for the neutron comparison; no arbitrary area factor or fit is introduced into that primary-table comparison. Full bin arrays, original error columns and raw score values are retained.

The photon calculation is replayed and compared with the archived computation, but its experimental CSV coordinate/differential convention has not been reconciled. The app must say that explicitly instead of drawing a misleading measured curve.

## Two data-handling issues that must stay visible
The archived helper uses radius 19.95 cm while the actual model tallies the 30.5 cm outer surface. We used 4*pi*(19.95 cm)^2 only to undo the archive's documented area normalization. We did not replace the real model geometry with that helper radius. A claimed surface current density using the wrong radius would differ by the squared-radius ratio, about 2.337; the primary comparison therefore stays in surface-integrated current units.

Under the stated conversion, the archived experimental first neutron bin is about 516.79 times its IAEA table counterpart; all remaining bins map within approximately 0.9972-1.0036, consistent with a different first-bin conversion and rounding elsewhere. This is an identified interface inconsistency, not a new materials effect. The original values are preserved and exposed; the first bin is neither deleted nor silently repaired. The underlying origin of the discrepancy has not been established by author confirmation.

The final neutron bin scored zero in the finite run and reports zero estimated sampling variance. A provisional Gaussian residual would misleadingly look like a large significance because the older much longer run has a tiny positive score. We mark that residual **not evaluated**: an unscored bin is not proof of zero physical probability. All 133 eligible neutron bins and 49 photon bins lie within three combined reported Monte Carlo standard errors of the archived calculation. This is descriptive, not a multiple-comparison acceptance test or proof of physical accuracy.

## What remains unresolved
The reported measurement Error column is preserved as supplied. Its complete confidence convention, bin correlations, detector-response treatment, source/geometry systematics and the original experimental reconstruction have not been established here. We therefore do not invent a combined confidence interval for the integrated measurement difference. Our current library file hashes are known; the old archive's library label does not establish identical processing or temperature treatment.

LiF leakage is not Li4SiO4/TiBe12 blanket tritium production, and neither is recovered reusable fuel. JADE documents a FNG HCPB mock-up experiment measuring tritium in lithium-carbonate pellets within beryllium; that is a more directly relevant benchmark to acquire and reproduce with the correct rights and complete inputs. This continuation did not run that experiment. Existing documentation is recorded in the prior-work register so the next continuation does not rediscover it or substitute an unrelated aluminium benchmark for breeding validation.

## What changed in the workbench
A **Benchmarks & prior work** view compares the actual computed spectrum, archived calculation and primary neutron table, with selectable bins, all raw uncertainties, clear missing-data status and an attribution panel. Its register records what was reused, what our execution added, what must not be repeated, and the evidence required to reopen each task. The results are not displayed on the candidate reactor as though they were tests of that geometry.

The full report and register are part of the research reader. Data, credits and the live website update together. The native source's reader packet is refreshed, but the already published Windows executable is not silently relabeled as a new build; the new interactive benchmark view is presently in the browser app.

## Attribution and reproduction
Original experiment: Chihiro Ichihara et al. (1988), https://wwwndc.jaea.go.jp/nd1988/abstracts/12916-0319.html . Model/archive: OpenMC Fusion Benchmarks, MIT PSFC and contributors, pinned at c47fc573a7e2a9ca11a8958dc67155b1146adf51, https://github.com/eepeterson/openmc_fusion_benchmarks . Measurement tables/input: IAEA-NDS/open-benchmarks, pinned at 09bacd7927b581d5e0f90468a0599fec8e95f972, https://github.com/IAEA-NDS/open-benchmarks , CC BY 4.0. Benchmark framework: Davide Laghi et al. (2020), https://doi.org/10.1016/j.fusengdes.2020.112075 ; JADE experimental benchmark documentation https://jade-a-nuclear-data-libraries-vv-tool.readthedocs.io/en/latest/benchmarks/experimental.html . No endorsement is implied.

The exact files, source hashes, licenses, changes and reading scope are in `research/source/experiments/oktavian_lif_2026_09_14/ATTRIBUTION.md` and `UPSTREAM_MANIFEST.json`. `analyze_reference.py` replays this comparison without new transport. The run statepoint and original model are preserved; execution logs and nuclear-data installation paths are not published. No reactor geometry, accepted power result or experimentally validated status changed.

## Independent continuation check
A second summation using the complete original arrays shows why the legacy measurement conversion cannot be used uncritically: its reconstructed integral is 1.045614477, versus 0.627372877 from the IAEA table. The same computed result would then appear to have an integral ratio of 0.560816 instead of 0.934688. The flagged first bin accounts for essentially all of that difference (remaining-bin net difference about -0.00000231). A missing logarithmic bin-width factor alone does not explain the first-bin discrepancy. Its origin remains unconfirmed, and neither ratio is promoted as an uncertainty-qualified physical bias. Every original value is retained in INDEPENDENT_NORMALIZATION_REVIEW.json and the downloadable data.

A separate attributed review, **Breeding benchmark selection**, records Novais and Peterson's existing OpenMC HCPB validation study. Its reported mean discrepancy is not imported into our candidate as a correction or uncertainty bound.
