# Inverse current budget: check what the plasma supplies before demanding more microwave current

## Decision changed by this study
Instead of another launcher-frequency search or a more optimistic power optimization, we asked an inverse question: **given the four already constructed equilibria, what current remains after a kinetic bootstrap-current calculation?** Bootstrap current is the plasma's pressure-gradient-driven current. It is a current contribution, not free electrical generation.

The previously quoted7.597810 MA microwave-current requirement depended on the systems model's assumed bootstrap contribution. It is not a geometry-independent target that can be carried unchanged into any more detailed equilibrium. This study quantifies that inconsistency before further actuator optimization.

The two fine-mesh constructions predict10.871218 and11.621250 MA of thermal bootstrap current **inside the evaluated poloidal-flux interval0.01–0.98**, compared with the original systems model's7.780619 MA bootstrap contribution for the entire plasma. Remaining total current in the evaluated interval is9.195727 and8.529923 MA. These are new, conditional computational results—not measured currents or validated reactor performance.

The useful lead is that self-generated current could alter the externally driven-current requirement substantially. **It is not permission to replace the systems input by the larger number and announce improved electricity.** The constructions still use an unqualified fixed boundary and prescribed pressure/current closures; q95 still differs from the intended design. They are not the original matched diverted reactor. Different models and profile assumptions are being compared, not two measurements of the same qualified plasma.

## Existing knowledge that must not be called a discovery
The original PROCESS output already contains other bootstrap correlations: for example ARIES gives a fraction of0.5183 and Wong0.6883, whereas the active Sauter estimate is0.3735. Thus the possibility of a higher bootstrap estimate is **already documented in the old output**. We preserve those alternatives in `EXISTING_SCALING_COMPARISON.json` and do not call that observation new. The added result is the geometry/profile-resolved budget and independent checks on these particular force-balanced proxies. Switching to the most favorable correlation would not establish accuracy or improved power.

## Why this was not another redundant calculation
The previous equilibrium study tested whether prescribed FF-prime shapes could reproduce scalar q assumptions while matching total current and pressure energy. It did not evaluate their bootstrap-current profile or residual current demand. We reused those saved meshes, pressure mappings and source profiles, restoring each field only to obtain geometry coefficients absent from the earlier export. Restoration is not a new discovery of equilibrium, nor a new design optimization.

Original methods are credited to Redl, Angioni, Belli, Sauter and collaborators [1], and the Open FUSION Toolkit/TokaMaker contributors [2]. Before execution, the original-contributor summary, official example, installed26.9 API/source and independent current-model research were checked. The official bootstrap workflow adjusts an imposed current amplitude to meet the target. That behavior is suitable for its example but would hide a current-budget mismatch here. We did **not** invoke automatic current rescaling or tune bootstrap strength.

A separately frozen admission defines this narrower diagnostic while the full roadmap input/actuator-qualification gates remain open. No DIII-D or canonical ITER reference case was rerun. Four bounded field restorations/evaluations were admitted, with one numerical thread each and180-second numerical limits. The first case used an interactive adapter inspection; its recorded wall time includes that inspection. The remaining cases executed the same physics pipeline without interaction. Read-only arithmetic checks added no solver runs.

## Inputs and normalization
The original higher-output MFILE is verified by SHA-256`7820f58cdf129d0f67000c570a4de0e969aa94f712c6cae03e34f0ba27d65cad`. Electron density/temperature profiles are reconstructed by the previously credited PROCESS equations and match every archived electron-pressure value. Ion temperature follows the original common-shape Ti/Te ratio of1; ion density is recovered from archived ion pressure. Its ion/electron density ratio agrees with the archived volume-average ratio0.8592890128 across all201 points. Spatial effective charge is retained rather than replaced by a favorable constant.

The four source cases retain their original shape, pressure-energy target, current and FF-prime exponents. No new target or mesh parameter is optimized. Restored q samples agree with the saved results within the admitted0.02% tolerance. As before, total pressure energy includes an assumed co-shaped isotropic fast-pressure contribution, but the bootstrap calculation here uses thermal electron/ion pressures only. Fast-particle current and actual control profiles are not supplied or invented.

## New calculated result
All currents below are in MA, or millions of amperes. Interior current is not a complete bootstrap total.

| Existing construction | Interior total current | Interior bootstrap | Interior remaining current | Opposing-current lower bound from the surface-averaged residual |
|---|---:|---:|---:|---:|
| 0.18 m mesh, FF-prime exponent 1 | 20.063797 | 10.867527 | 9.196269 | 0 in the sampled surface averages |
| 0.09 m mesh, FF-prime exponent 1 | 20.066944 | 10.871218 | 9.195727 | 0 in the sampled surface averages |
| 0.18 m mesh, FF-prime exponent 2 | 20.151310 | 11.614906 | 8.536404 | 0 in the sampled surface averages |
| 0.09 m mesh, FF-prime exponent 2 | 20.151173 | 11.621250 | 8.529923 | 0 in the sampled surface averages |

The archived whole-plasma current budget was20.830235 MA total, split into7.780619 MA bootstrap,5.451806 MA inductively supplied and7.597810 MA externally driven. On the evaluated proxy intervals, bootstrap alone exceeds the old full-plasma bootstrap allowance by3.09–3.84 MA. Adding the old external and inductive contributions to these new proxy values would not be a consistent current allocation.

The flux-surface-area-averaged residual current profile is nonnegative at every sampled surface in the evaluated interval. Thus the particular integrated opposing-current lower bound is zero. This does **not** prove that residual current is nonnegative at every poloidal position, or that a specific coil or microwave deposition profile can provide it; local and time-dependent requirements remain untested.

An explicitly optimistic lower bound allows all5.451806 MA of the original inductive contribution to be placed inside the tested interval. The minimum additional current needed there is then3.744 MA or3.078 MA on the fine meshes. Those numbers are **not a new qualified microwave-current target**, not an upper bound on the actual requirement, and not a prediction of actuator performance. Uncomputed axis/edge current, induction's physical spatial profile, current evolution and heating/control functions still matter. We deliberately do not extrapolate bootstrap to the full plasma or infer saved MW from this lower bound.

## Geometry-aware projection and independent checks
The installed Redl formula returns a parallel-current quantity involving the flux-surface-averaged current-dot-field. We use its native NRL electron Coulomb-logarithm and Zavg/Koh effective-ion collisionality conventions, with explicitly retained coefficient arrays. No negative, nonfinite or missing result is silently replaced by zero.

The source's simpler conversion uses an average-radius/toroidal-field approximation. We separately calculate a parallel-current projection with the actual field variation on each closed contour: a flux-function parallel-current coefficient times F/R, normalized by the surface average of total B squared. Area integration uses dl/(R*Bp), with its positive poloidal-flux span. This still assumes the stated parallel-current decomposition; it is not a kinetic orbit calculation or proof of a physical current profile. Its interior integral is approximately4.3–4.6% below the simpler native projection, and both are preserved.

The total-current area integral is independently compared with the difference of magnetic-field circulation at the two interval boundaries, using Ampere's law. Disagreement is0.012–0.034%, below the1% admission threshold. Bootstrap integrals change by0.034% and0.055% on mesh refinement. Using201 instead of401 flux samples changes the reported integrals by0.065% and0.148% on the fine meshes, also below1%. These are numerical checks, not physical error bars or confidence intervals.

The poloidal-flux sign convention is explicit. In these TokaMaker cases, absolute flux decreases outward; the installed Redl workflow uses an outward-positive span. Derivatives are converted before evaluating the final current, rather than taking an absolute value of a negative output. The initial unconverted diagnostic arrays are retained and tests verify the full sign reversal. The toroidal-field identity R*Bphi=F is checked on every sampled contour; total-current orientation is independently checked by magnetic circulation. A coordinate convention is not tuned to make the result favorable.

## What to do next
Prioritize a **self-consistent current allocation and equilibrium calculation**, with a matched boundary and a constrained inductive/EC deposition profile. Do not continue optimizing a launcher against a supposedly universal7.598 MA target while swapping in a different bootstrap model. Do not silently increase inductive current or scale a reference actuator until the total closes.

This diagnostic makes that next question more specific: retain the plausible larger self-current contribution as a hypothesis, test it under a consistent thermal/fast-pressure and current-profile treatment, and determine whether the remaining externally supplied profile and control functions can actually coexist. The same-design heat, fuel and material requirements remain afterward. No additional net-electric output or reactor qualification is accepted by this study.

The old construction-to-q mismatch remains unresolved. G1/G2 in the roadmap are not marked complete; this is an admitted subproblem on known unqualified proxies. A missing complete reactor package need not prevent useful necessary-condition tests, but such tests cannot be renamed complete qualification.

## Evidence, execution and limitations
All four completed401-point current-field packets, original kinetic arrays, coefficients, sign diagnostics, admission, exact used drivers and restored-state checks are in `research/source/experiments/inverse_current_budget_2026_09_16`. Independent arithmetic replay needs only the saved files and NumPy/SciPy; it does not rerun an equilibrium. Original source fields and earlier power datasets are unchanged. The companion visualization uses those recorded profiles, not animated current invented to make the design appear functional.

This is the first current-budget diagnostic for these proxies, not a reproduction counted as a new method. The original TokaMaker equilibrium restoration is explicitly reuse. Completed numerical checks cannot establish experimental accuracy of the Redl fit, fast-particle effects, edge kinetics, a real diverted boundary, an achievable launch configuration, stable current evolution or hardware lifetime. No physical experiment or new power calculation was performed, and the released Unreal binary is not rebuilt by this update.

One batched workstation read was rejected with an indeterminate tool-safety status. No safety configuration or permission was changed and that compound call was not replayed. The normal file-reading action independently exposed the completed safe result files; publication does not rely on a guessed execution status. Failed or incomplete numerical outcomes would have remained unscored rather than discarded.

## Primary prior work and original credit
[1] A. Redl, C. Angioni, E. Belli, O. Sauter and collaborators, *A new set of analytical formulae for the computation of the bootstrap current and the neoclassical conductivity in tokamaks*, Physics of Plasmas28,022502(2021), DOI https://doi.org/10.1063/5.0012664 . Original-contributor summary checked: https://fusion.gat.com/global/theory/weekly/0721 . The revised formulas and their numerical-neoclassical basis are existing research, not Workbench's discovery.

[2] Open FUSION Toolkit/TokaMaker official bootstrap-equilibrium example: https://openfusiontoolkit.github.io/OpenFUSIONToolkit/docs/v26.6/doc_tMaker_ITER_ex3.html . The installed26.9 source/API was also read. Its fitting workflow is not itself our fixed-budget experiment; we reused the native Redl coefficients without invoking automatic inductive normalization. The numerical solver and bootstrap implementation retain upstream authorship and licensing.

[3] S. Saxena, N. Ferraro, M. F. Martin and A. M. Wright, *Bootstrap Current Modeling in M3D-C1*, https://arxiv.org/abs/2507.05166 ; published study https://www.cambridge.org/core/journals/journal-of-plasma-physics/article/bootstrap-current-modeling-in-m3dc1/07AEC30A1077F0D427FF2EA7BF42AC4B . Its original validation work illustrates the need to distinguish numerical consistency from kinetic/model validation. Those authors' comparisons were not reproduced here or borrowed as validation of our plasma.

[4] UKAEA PROCESS, exact original candidate source revision https://github.com/ukaea/PROCESS/tree/c0ae5b28649f2b20fb7efc7904628b6defe4151c . The inherited generic tokamak input credits James Morris, UKAEA. Existing full-plant, analytic EC and equilibrium studies supply the exact input/output provenance. No endorsement by these investigators is implied.

## Continuation review: existing results recovered, not rerun
The interrupted work had already completed all four numerical cases and their local viewer. This continuation recovered those files, checked the recorded inputs/results and replayed the arithmetic without another equilibrium solve. Independent composite-Simpson summation, the full three-term Redl current decomposition, coefficient identities and restoration of the pressure-energy target were added to the review. The four computational cases are not counted again as four new experiments.

The parallel-current projection was cross-checked against Eq. (2) in Saxena et al. [3]: for the stated purely parallel, divergence-free source, the vector source is the surface-averaged current-dot-field divided by the surface average of B squared, multiplied by the local B vector. Our plotted toroidal contribution is that source's toroidal component, not an independently solved full transport current. The pressure/current separation, self-consistent evolution and external deposition remain qualification gaps. Source read: https://arxiv.org/html/2507.05166v1 .

The initial budget estimates do not establish lower total reactor recirculating power, greater stability or any additional electrical output. Larger thermal self-current on a different unqualified plasma is a reason to solve the coupled current budget, not a drop-in efficiency improvement. The completed study and all unfavorable/limiting facts remain visible with original attribution.
