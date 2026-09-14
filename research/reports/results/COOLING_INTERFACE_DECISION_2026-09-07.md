# Candidate-specific cooling decision — 7 September 2026

## Decision

Keep the solved8.37953287m-radius PROCESS point as a systems-model baseline, not a physically qualified reactor. Carry forward one local cooling proposal: retain4m first-wall paths inboard and split outboard paths into two separately fed2m paths. This passes the examined local channel-temperature/pressure screens under frozen assumptions, but headers, connecting pipes, flow distribution, structural space and neutron effects remain unresolved. No increased net output or validated complete cooling system is claimed.

## Prior-art decisions before computing

Humphrey et al. (published2February2026; DOI10.3389/fnuen.2025.1694684) already combines Hypnos/OpenMC/MOOSE/SLEDO for ceramic breeder mock-ups. The mock-up results and restricted underlying study data cannot be adopted as our reactor's TBR. We did not build another blanket optimizer.

Official PROCESS documentation and actual pinned FirstWall/BlanketLibrary source already implement the heat-transfer/pressure methods needed for a bounded interface check. Those native functions were reused.

Abou-Sena et al. (DOI10.1016/j.fusengdes.2017.02.072; publisher abstract/sections examined, not underlying experimental records) documents parallel HCPB first-wall channels and connection pressure losses. Parallelization is established engineering, not our invention. Only one explicit split comparison was admitted; extra distribution hardware was not treated as free.

This was a targeted prior-art review, not exhaustive proof of originality. Every run records its question, baseline, sources, changed input and completion criterion. Generic diffusion/fuel sweeps stayed retired.

## Exact candidate state and inactive defaults

One exact-input rerun exported native state groups. Input SHA2562bc99ba58a1a9305a8e395a21d9ab9a2bba64fb31c06486d05617d89d3ecb9b4; full saved-state SHA256cedcfa6d695fd45d4be17ea1ee77ae40d821064ea15eb1244822804f3001f9ea. Radius, net output and fatigue result reproduced the prior point. This rerun obtained missing state, not another claimed design advance.

The actual mode3 helium loop uses8MPa,573.13K inlet,773.13K outlet and550kPa total pressure-drop allowance. Its pinned HCPB branch calculates pumping using a specified global drop and does not invoke the detailed first-wall temperature evaluator. Stored15.5MPa,823K coolant outlet and873K peak-wall values are inactive defaults here, not evaluated mode3 temperatures. The823K native material limit is a scenario criterion, not a universal safety limit; heat peaking remains assumed1.0.

A30%Li6 default is now visible in the full state but is not used by an active TBR calculation. The1.269 blanket heat-normalization factor is not TBR. The coarse export is not unique heterogeneous CAD.

## Native local thermal checks

| Declared cooling interpretation | Inboard peak K | Outboard peak K | Versus823K criterion |
|---|---:|---:|---|
| FW separately receives full loop temperature rise |949.3271|958.0681|Both exceed|
| FW then blanket, native shared-branch heat apportionment |798.2411|779.2010|Both below|

Shared routing is an existing method, not new physics. The routing alternatives are local interpretations, not completed piping designs. These are heuristic calculations rather than CFD or material qualification.

## Coolant-volume inconsistency and pressure consequence

The blanket inventory contains5.295%pressurized coolant. The inactive hydraulic parameter is25%. Its native pipe-count equation N=fraction*V/(pi*r^2*L) implies4.7214times the channel volume. Copying25%into hydraulics while keeping5.295%in a neutron model would mix different plants. Setting counted pipe volume to5.295%is an explicit diagnostic mapping, not proof of a manufactured layout.

With that inventory-matched mapping, the original outboard FW+blanket channels require545.9636kPa using mean properties, or574.7810kPa using outlet properties. The550kPa allowance then leaves4.0364kPa or-24.7810kPa for all omitted manifolds, heat exchangers and connecting pipes. Native FW/BZ channel bends are included. The property choices are approximations, not rigorous bounds or confidence intervals. A viable complete-loop margin is not established.

## Specific intervention and selected follow-on

The one admitted intervention splits each4m FW path into two independent2m paths at fixed radius, pitch, heated area, wall thickness, total branch mass flow and in-wall channel volume. Native heat transfer and channel pressure loss were reevaluated; additional headers and connections remain explicit costs.

| Region | Existing shared peak K | Peak after split K | Margin after split to823K |
|---|---:|---:|---:|
| Inboard |798.2411|816.7621|6.2379K|
| Outboard |779.2010|793.4054|29.5946K|

Outboard FW+BZ channel pressure becomes130.8352kPa with mean properties or141.2118kPa with outlet properties. Thus the selected follow-on splits only the outboard path. Leaving the inboard unchanged avoids unnecessarily consuming its temperature margin. This selection is adaptive, not held-out validation.

For this local combination, peaks are798.2411K inboard and793.4054K outboard. The limiting branch channel losses are275.5017/294.7379kPa, leaving274.4983/255.2621kPa of the original allowance for omitted hardware in the respective approximations. Outboard FW path count rises14238to28476; in-wall channel void and total branch mass flow remain identical. Added headers may require material/void volume and affect neutron breeding; those costs are NOT zero or solved.

No pressure improvement is credited to net electricity. The prior213.69MW conditional average is unchanged and not physically validated by these tests.

## Execution and reproducibility

Sixteen focused interface tests passed, zero skips/failures. They check state identity, native-model recomputation, correlation validity, channel-volume/mass-flow conservation and pressure bookkeeping; not all repository tests or physical validation.

After the successful candidate recapture, a wrong post-processing class name caused an import failure. Saved state was reused with the correct FirstWall class; no reactor rerun was needed. An initial outlet-root bracket evaluated out-of-domain Reynolds values. A separate final evaluator restricts the bracket, explicitly checks validity, and retains the original attempt. The final four cases, split cases and accepted roots are within the declared correlation range.

The compact replay was actually executed against the pinned imported source and reproduced selected temperatures within1e-6K and pressures within0.01Pa. These numerical tolerances are not physical uncertainty. Upstream source remains unmodified. The exact wrappers, input subset and portable adapter are in experiments/cooling_interface_2026_09_07.

[Personal identity or local execution location omitted from this public copy.]

## Next decision and explicit missing evidence

Before adopting the outboard split, specify its headers and actual flow split; allocate their steel/coolant/void volumes consistently; evaluate pressure and heat-peaking/structural limits; then use an established source-normalized neutron workflow on that same geometry. The contract is still NOT ready for validated transport coupling: isotope vectors/densities, ports, spatial DT source, nuclear-library identities, matched heating and distribution hardware must be defined. No OpenMC, new TBR, complete pressure-flow network, calibrated material-release, physical experiment or unattended research service ran here.

References inspected:
- https://www.frontiersin.org/journals/nuclear-engineering/articles/10.3389/fnuen.2025.1694684/full
- https://ukaea.github.io/PROCESS/eng-models/fw-blanket/
- https://doi.org/10.1016/j.fusengdes.2017.02.072
- Exact pinned PROCESS c0ae5b28649f2b20fb7efc7904628b6defe4151c: models/fw.py; models/blankets/hcpb.py; models/blankets/blanket_library.py; models/engineering/pumping.py; constraints39.
