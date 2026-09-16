# EC equilibrium interface: force balance before actuator qualification

## Decision
The restored workstation completed four candidate-linked Grad–Shafranov equilibrium constructions and one established GENRAY reference ray. The constructions match the higher-output concept's total current and pressure-energy targets but do **not** reproduce its scalar safety-factor assumptions. We therefore do not promote the earlier electrical-output gain to an actuator-qualified reactor result or claim candidate driven-current performance.

The next calculation needs a matched diverted boundary and pressure/current-profile closure. Otherwise a ray solver would answer a different plasma problem while appearing to validate the original one. Failing this construction compatibility screen is not proof the concept is impossible. The existing actuator requirement remains 7.597810 MA from no more than170 MW credited drive, with adequate heating/control; these equilibrium cases do not solve that qualification problem.

## Prior work and recovered evidence
Before calculation we read TokaMaker's official fixed-boundary example and installed26.9 API, reviewed the project's existing DIII-D reproduction, and checked the HARE/GENRAY prior work [1–4]. The existing DIII-D example was not repeated as new reactor evidence. Established solver and launcher methods belong to their original investigators; Workbench supplies this scoped interface study.

The exact original higher-output MFILE SHA-256 is `7820f58cdf129d0f67000c570a4de0e969aa94f712c6cae03e34f0ba27d65cad`. It was reread and hash-verified without modification. All201 archived thermal, electron and ion pressure values and effective-charge values were preserved. Multiplying the previously reconstructed electron density/temperature profiles reproduces all201 archived electron-pressure values with maximum relative difference3.33e-15. This is a pressure-product reconstruction check, not independent measurement or separate-array verification of density and temperature.

The prescribed R/a are8.379533/2.793178m, elongation1.85, triangularity0.5, reference toroidal field5.280938T and current20.830235MA. Thermal energy is1.466817GJ; the beta-derived total pressure-energy target is1.725377GJ. A separate fast-particle radial pressure profile is unavailable.

## Declared construction assumptions
We use a smooth limited fixed boundary—not the original single-null separatrix, a PF-coil solution or an experimentally reconstructed equilibrium. Thermal pressure follows the exact archived shape. Missing fast pressure is assumed isotropic and co-shaped with thermal pressure, with total pressure energy matched to the archived target. The constant edge-pressure offset is removed in the fixed-boundary construction. None of those assumptions is a measurement or a physical uncertainty bound.

The original geometric radial profile is assigned iteratively to the square root of normalized enclosed volume. It is **not** silently identified with normalized poloidal flux. That volume-coordinate assignment remains a declared physical profile-mapping assumption. Enclosed volumes are calculated independently from traced closed contours using the polygon first moment about the symmetry axis; monotonicity is required.

Two FF′ shapes, `(1-psi_norm)^1` and `(1-psi_norm)^2`, are specified current-profile closures. Their amplitudes are solved under the current and pressure-energy targets. They neither span all possible current profiles nor define probabilities. Target mesh sizes0.18 and0.09m with cubic finite elements provide refinement comparisons. The admission limits each run to one thread,180seconds, six mapping iterations and100 nonlinear iterations per solve.

## Completed numerical result
| Mesh target (m) | FF′ exponent | q at flux0.01 | q at flux0.95 | Axis shift (m) |
|---:|---:|---:|---:|---:|
|0.18|1|1.521368|3.893659|0.527039|
|0.09|1|1.521450|3.895664|0.527179|
|0.18|2|1.868874|3.834757|0.614975|
|0.09|2|1.869804|3.836787|0.615482|

The flux0.01 sample is near-axis, **not exact q0**. The systems assumptions were q0=1 and q95=3. Fine-mesh q95 values are about29.86% and27.89% above3, while q95 changes only0.0515% and0.0529% under mesh refinement. Axis-shift refinement changes are approximately0.14 and0.51mm. All four imposed current/energy integrals match within the admitted0.2% tolerance and all mapping loops meet their0.002 normalized-radius criterion. Each final solve and COCOS7 export completed.

Constructed volume is1.87–1.90% above PROCESS because the prescribed smooth shape differs. The magnetic axis is0.53–0.62m outside the geometric center. Thus the zero-axis-shift/toroidal-only analytical picture is not a qualified ray equilibrium. This is a construction-to-assumption discrepancy—not the actual reactor's measured q, a unique causal diagnosis, a statistical interval or a reason to apply an ad-hoc frequency correction. Changing the unqualified boundary or current/pressure closure can change the result; mesh convergence does not resolve those physical uncertainties.

## Restored analytical screen
All56 September15 HARE/cold-wave cases were recovered and replayed, with inputs, admission and attribution preserved. Recovery is not56 new ray simulations. Higher-output nominal seeds span approximately241–257GHz; the declared width/inclination sensitivities span209–257GHz. They are analytical starting values, not verified launcher settings or probabilistic bounds.

The170GHz nominal-tail probe has intersections near36.5 and167.8keV. The intended high-energy population is the upper rather than lower-energy intersection required by this prescription. This does not generally exclude170GHz heating or ECCD under other launch conditions. All local cold O-like dispersion tests pass; no connecting candidate ray, absorbed fraction, driven-current profile or control sufficiency follows from that local test.

## GENRAY execution restored, with scope kept separate
GENRAY compiled from upstream revision`ee443d16e5aaf9bc7227fb3e95581e3ba374df89`. The unchanged upstream canonical ITER170GHz one-ray input and equilibrium produced343 recorded points and normal termination, status2: residual ray power below the configured threshold. Final/initial tracked power is about9.72e-5. Complete position, phase, path-coordinate and power arrays are preserved with input, NetCDF and binary hashes.

This is an execution/extraction check, not numerical comparison with the authors' archived reference or experiment. The source-native signed current is retained but is **not** credited to our7.598MA target. The reference has a different equilibrium, profiles and launcher. No GENRAY source/binary distribution is bundled; upstream licensing remains applicable.

## Failed adapters and setup attempts are retained
Installed TokaMaker uses`nl_tol` and returns an equilibrium object from`solve`; early wrappers used the wrong conventions and were rejected. The FSA derivative returned zero at some near-edge samples. Raw diagnostics were saved, and volume was instead computed from traced contours—not repaired by dropping zero points. An initial unsupported COCOS3 export was rejected; final exports use supportedCOCOS7, explicitly recorded for any future convention conversion. Those implementation retries are not extra independent physics cases.

GENRAY's missing plotting dependency was extracted from official Ubuntu packages into a project-local directory, without system PATH/library changes. Its first linked run exited0 but stopped at graphics initialization without a ray. A recorded output-device-only change fromVCPS toCPS enabled the Giza compatibility library. No physics equation changed. Final NetCDF and normal termination were required; exit0 was insufficient. Public failure summaries exclude private machine paths and raw tracebacks; originals remain local.

## Visual and source evidence
The EC-wave view shows actual solved contours, geometric versus magnetic axes, the complete q sample set, mesh comparisons, all analytical sensitivities and a separate labeled reference-ray replay. Playback follows recorded points for display, not physical time or live computation. Full finite-element fields, pressure/F profiles, all saved mapping iterations, contour arrays and COCOS7 files are preserved. Only contour drawing uses an explicit display limit; canonical data are not truncated.

The candidate remains unqualified. No original accepted plant output, canonical neutron source bank or released Unreal binary is changed. This is a browser/research update; historical analytic metadata saying the original study was not published describes its original execution, not present deployment status. A browser rendering/interaction check remains separate from arithmetic, data-integrity and syntax tests.

## Next falsifiable gate
The next qualified actuator calculation needs a consistent diverted equilibrium and prescribed current/pressure profiles, including a substantiated fast-particle pressure treatment, rather than selecting whichever closure makes the desired scalar values look plausible. Its source signs, flux coordinate convention, electron profiles and actuator geometry must be matched explicitly. A subsequent ray/current-drive solution must meet the total driven-current target and the retained heating/control functions together. If those requirements cannot be met, reject or reduce the systems allocation benefit.

Reopen the present equilibrium construction only for new physical profile/boundary constraints, a numerical defect or a specifically admitted closure/refinement question. Do not repeat the official DIII-D or canonical ITER example as a new reactor result, or count a larger library/test count as progress toward generated power.

## Primary references and reading scope
[1] Open FUSION Toolkit / TokaMaker official fixed-boundary example and project documentation: https://openfusiontoolkit.github.io/OpenFUSIONToolkit/docs/v26.6/doc_tMaker_fixed_ex1.html and https://openfusiontoolkit.github.io/OpenFUSIONToolkit/ . The official example and installed 26.9 Python API/source were read. The exact installed package/version is preserved; an old example is not claimed to be a complete description of a newer API.

[2] N. A. Lopez, A. Alieva, S. A. M. McNamara and X. Zhang, *Fast physics-based launcher optimization for electron cyclotron current drive*, Plasma Physics and Controlled Fusion 67, 055012 (2025), DOI 10.1088/1361-6587/adcae7. Full January 2026 arXiv v2 HTML was read: https://arxiv.org/html/2501.04619v2 .

[3] E. Poli, M. Müller, H. Zohm and M. Kovari, original HARE study, Physics of Plasmas 25, 122501 (2018), DOI https://doi.org/10.1063/1.5050345 . This work uses equations restated in [2], not a claimed reproduction of the complete original efficiency algorithm.

[4] GENRAY maintainers / A. P. Smirnov, R. W. Harvey and collaborators, upstream code and canonical test documentation at https://github.com/compxco/genray/tree/ee443d16e5aaf9bc7227fb3e95581e3ba374df89 . The `00_Genray_Regression_Tests/README_genray` describes the canonical ITER EC test with R. Prater. GENRAY code retains GPL-3.0-or-later; the binary/source distribution is not included in this Workbench export. The graphics adapter and numerical-output provenance are disclosed.

[5] UKAEA PROCESS exact source revision https://github.com/ukaea/PROCESS/tree/c0ae5b28649f2b20fb7efc7904628b6defe4151c . Original candidate input and model authors remain credited. The analytic module's `SOURCES.md` gives the profile/HELIOS and Stix dielectric references, reading scope and original source blobs.
