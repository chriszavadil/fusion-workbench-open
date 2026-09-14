# Cooling distribution decision — 7 September 2026

## Disposition
The outboard-only channel split remains a conditional component proposal, not a validated cooling system. For the explicitly tested common-supply/common-return topology, its previous assigned-flow temperature result cannot be accepted without flow balancing. The numerical test identifies the required differential resistance and the accompanying pressure/space obligations. No neutron simulation, reactor reoptimization, higher electricity output or experimental validation is claimed.

## Research before computation
The initial review found the relevant mechanisms and methods already documented. The 2016 GRICAMAN HCPB study reports measured flow distributions and local starvation caused by first-wall outlet jets; the 2017 first-wall experiment reports unequal channel and connection losses. The 2023 HCPB design describes established first-wall/manifold/breeder-zone routing. The 2025 mock-up paper presents a scaling methodology and proposed HELOKA tests, not a validation dataset for our candidate. These references motivated testing distribution instead of inventing another manifold optimizer. Publisher abstracts/section extracts were read for 2016/2017, indexed publisher text for 2023, and parsed PDF text for 2025; PDF rendering failed, so no quantitative input was taken from its figures or tables. A follow-on search also found the existing 2016 Modelica whole-loop work: reuse or assess that baseline before attempting a new whole-loop solver. None of these papers' coefficients or performance numbers were transplanted into our geometry.

## Exactly what was tested
The input is the captured PROCESS point at project commit 276c55a, carried forward by cooling checkpoint 3f1d2f6. The verified full-state SHA-256 is cedcfa6d695fd45d4be17ea1ee77ae40d821064ea15eb1244822804f3001f9ea. The local proposal keeps 4 m first-wall paths inboard and uses 2 m paths outboard. Native PROCESS heat-transfer and pressure-drop functions are reused at an 8 MPa property-evaluation pressure, with the inherited heating and 550 kPa total pressure allowance.
The new closure holds total flow fixed but solves its division by equating the aggregate inboard and outboard branch pressure losses. Both branch outlet temperatures respond to flow; they are not artificially held at their nominal values. Headers are idealized common-pressure nodes, not a constructed manifold. Separate independently controlled circuits remain an alternative. Consequently, failure of this topology is not proof that every cooling configuration for the candidate fails.
Continuum-equivalent channel counts, area/(pitch*length), preserve the heated area exactly instead of introducing the earlier integer-rounding mismatch. This changes nominal branch flow by about 0.004%, not the design conclusion. Native average-heat-capacity energy integration is independently compared with CoolProp enthalpy; the largest relative heat discrepancy in the saved operating comparisons is about 6.1e-6. No full compressible pressure/temperature network or spatial heat-flux map is solved.

## Executed comparison
| Quantity | Mean-property approximation | Outlet-property approximation |
|---|---:|---:|
| Unsplit reference, common-pressure channel drop | 435.518 kPa | 460.678 kPa |
| Split without balancing: inboard share relative to prescribed flow | 72.623% | 71.895% |
| Split without balancing: inboard wall peak | 832.560 K | 833.810 K |
| Scenario wall-temperature criterion | 823 K | 823 K |
| Differential outboard loss required at nominal flow | 144.666 kPa | 153.525 kPa |
| Split with that balancing: common channel/balancing drop | 275.505 kPa | 294.741 kPa |
| Remaining pressure allowance before other hardware/volume changes | 274.495 kPa | 255.259 kPa |
The unsplit common-pressure reference passes the local temperature criterion in both approximations. The split without balancing does not: its lower outboard resistance diverts flow from the inboard branch. The inboard flow falls roughly 27–28% below its prescribed value. With the calculated differential loss, the prescribed flow division is recovered and the original local peaks of 798.241 K inboard and 793.405 K outboard return. Mean and outlet properties are alternative approximations, not confidence bounds.

## Acceptance requirements, not a free balancing device
The 145–154 kPa differential is the inverse requirement to restore the previously prescribed flows. Actual header distribution, a controlled circuit, or deliberately added resistance might provide it, but no particular valve, orifice, or manifold has been designed or qualified. The idealized thermal boundary is about 537.114 kg/s inboard and 1221.853 kg/s outboard; the corresponding 21.31%/28.04% shortfall limits have no calibrated uncertainty or operational safety margin. They are model acceptance thresholds only.

The earlier 5.295% coolant allocation was already used entirely for blanket-channel counting. Reserving some of it for distribution hardware reduces channel count and raises channel loss. Under the outlet-property approximation, mathematical reservation ceilings are 11.272 cubic metres inboard and 34.664 cubic metres outboard, but only by using the entire 550 kPa allowance in the channels and assigning zero loss to the new hardware. These are necessary screening maxima, not feasible header sizes. They cannot be combined with the quoted 255 kPa spare-pressure budget, which applies before such channel-volume removal. Pressure, coolant void, steel and geometry must be allocated jointly.

## Numerical evidence and reproduction
Twenty-five focused tests passed, with zero failures or skips. They check an independent two-equation pressure/mass solver against the bracketed solution, temperature boundaries on both sides, native mass-flow identity, heat/enthalpy consistency, coolant-volume conservation, monotonic local response and invalid inputs. The entire repository suite was not rerun. A separate-directory portable replay reloaded the checked native subset, reproduced the saved numerical results and ran the same tests successfully. This verifies implementation consistency, not physical model accuracy.
The exact source, frozen inputs, complete result JSON, tests, observed dependency versions, UKAEA license and portable replay are in the companion experiment directory. The original raw ZIP was created before this narrative report: <LOCAL_HOME>\FusionResearch\Fusion_flow_balance_raw_evidence_2026-09-07.zip; 21,567 bytes; SHA-256 069746e49b89032136a7cb69d3bb9b0387e7f38d7a9fed65a957b528f1b71b61. Its 13 entries include the tested numerical files and portable-replay log, not this later report. The original full state remains on the desktop; the replay uses a hash-verified exact subset.

## Next research decision
Do not promote the split as a standalone cooling improvement. Compare an actual balanced distribution arrangement with the unsplit reference or independently controlled loops, using the existing published HCPB whole-loop/manifold methods. Before another calculation, identify the reference geometry and loss data, define the steel/void allocation and flow-control assumptions, and state which decision the calculation could change. Reject a proposal whose apparent pressure improvement depends on unallocated volume or unconstrained flow. No new generic whole-loop framework or parameter sweep is justified just by the existence of this local result.
The source-matched neutron model still requires explicit spatial material and source definitions. This study does not supply a TBR, physical fatigue qualification, full cooling validation or new electricity credit. The prior 213.69 MW conditional average is unchanged. No email, cloud provisioning, system setting change or autonomous monitoring was performed in this continuation; the bounded calculations are complete.

## Primary references and reading scope
1. Ilic et al., experimental HCPB coolant distribution (2016), DOI 10.1016/j.fusengdes.2015.12.026; publisher abstract/sections, not raw measurements.
2. Abou-Sena et al., first-wall channel/connection characterization (2017), DOI 10.1016/j.fusengdes.2017.02.072; publisher abstract/sections, not the full experimental data.
3. European DEMO HCPB design status (2023), DOI 10.3390/en16145377; indexed publisher text.
4. Verma et al., prototypical mock-up scaling (2025), DOI 10.1016/j.fusengdes.2025.114924; parsed paper text, not quantitative figure/table data. The paper describes planned testing.
5. Froio et al., HCPB whole-loop dynamic Modelica model (2016), DOI 10.1016/j.pnucene.2016.08.007; publisher abstract and institutional author record. Identified during follow-on research; code has not been retrieved or reproduced.
6. UKAEA PROCESS v3.4.2, commit c0ae5b28649f2b20fb7efc7904628b6defe4151c: FirstWall and BlanketLibrary native methods, same installed version as the prior candidate.
