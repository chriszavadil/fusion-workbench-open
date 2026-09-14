# Distribution hardware is now charged to the candidate's inventory

## Decision and scope
Independently controlled inboard/outboard circuits remain the preferred published reference, as recorded in the newer repository checkpoint2629556074609ad89ee44e6e9bf0bf8e8e21ae6d. A common-pressure circuit with cross-region balancing is only a comparator, not a mandatory design. The outboard split remains a conditional local-path lead. A declared three-header-per-computational-module envelope can fit the chosen coolant/steel accounting while leaving useful pressure headroom. This is not a manufactured manifold, source-matched CAD, a qualified pressure vessel, or a fusion breakthrough. No new electrical output or tritium breeding is claimed.

The comparison now subtracts header coolant from the blanket channels and subtracts header shell/cap steel from the native structural inventory. It also charges header friction before reporting spare pressure. Headers are no longer zero-volume, zero-friction nodes. Adequacy of the remaining blanket structure is not established by this accounting.

## Research before calculation
Froio et al. (2016), DOI 10.1016/j.pnucene.2016.08.007, already describe a Modelica HCPB whole-loop model. Bertinetti et al. (2018), DOI 10.1016/j.fusengdes.2018.04.099, already describe a 1D back-support/manifold model compared with CFD. Author/publisher abstracts and available introduction text were inspected. The 2016 institutional manuscript fetch returned HTTP403; a usable Modelica package was not retrieved. This is not proof that no accessible code exists. We did not recreate their whole-loop code.

Zhou et al. (2023), DOI 10.3390/en16145377, describe the established three-stage feed/intermediate/outlet flow sequence. Verma et al. (2025), DOI 10.1016/j.fusengdes.2025.114924, describe a scaled prototype and planned tests, not measured performance for our geometry. Indexed publisher design text and parsed repository text were inspected; attempted PDF screenshots failed and no numerical dimensions were taken from those figures. Their pin-based blanket is not interchangeable with this generic PROCESS candidate.

The new calculation reuses pinned PROCESS friction, first-wall and fluid-property methods and our prior tested branch model. The question is only whether an explicitly chosen header envelope consumes the candidate's remaining pressure and space budgets. No novelty is claimed for manifold design, parallel paths, pressure balancing or the minimization algorithm.

## Frozen geometry and accounting
The source remains PROCESS c0ae5b28649f2b20fb7efc7904628b6defe4151c and the solved state SHA256 cedcfa6d695fd45d4be17ea1ee77ae40d821064ea15eb1244822804f3001f9ea. The full state and an exact five-group subset are retained. The upstream worktree is unmodified.

The envelope has three straight circular headers per native computational subdivision: 224 inboard and 384 outboard subdivisions. Each header length equals the native poloidal subdivision length (1.76995m/1.94793m). These are explicitly proposed envelope units, not verified physical segment layouts. Radius is varied only within a declared interval to minimize the known branch pressure; no new blanket optimization is performed. All stage temperatures and nominal flows come from the inherited heat balance. Full module flow is charged along each header's full length; this is a stated friction approximation, NOT an upper bound on omitted junction losses.

Wall thickness is set to radius/6 for this envelope. Steel accounting includes the cylinder and two flat-cap volume allowances. Elastic stress is calculated only for an ideal closed cylindrical barrel; cap, nozzle, weld, thermal, irradiated-material and residual-structure qualification are absent. No material allowable stress or structural pass is assigned. Breeder/multiplier/purge fractions are not increased to compensate for hardware.

The initial prescribed-flow calculation is frozen separately. A subsequent explicitly admitted fair-baseline check allows both designs to redistribute flow under a common supply/return pressure at the same total flow. All original outputs are retained; the follow-on was adaptive, not held-out validation.

## Executed comparison with distribution hardware included
| Configuration and flow treatment | Known common pressure: mean / outlet approximation (kPa) | Remaining allowance (kPa) | Local first-wall temperature result |
|---|---:|---:|---|
| Unsplit with nominal prescribed branch flows |623.032 / 657.246|-73.032 / -107.246|Below823K, but the prescribed-flow pressure requirement fails|
| Unsplit, flows redistributed at common pressure |516.469 / 546.708|33.531 / 3.292|Both below823K|
| Outboard split, flows redistributed without added balancing |237.491 / 254.929|312.509 / 295.071|Inboard820.992 / 821.572K: only2.008 / 1.428K nominal margin|
| Outboard split with nominal-flow balancing |349.759 / 373.255|200.241 / 176.745|Inboard798.241K; outboard793.405K|

The unsplit reference must not be called physically impossible: allowing its flow to redistribute makes its known pressure/first-wall screen pass. Its available pressure for omitted hardware is nevertheless small, especially in the outlet-property approximation. Both designs retain unresolved mixing, branch jets, local heat peaking and downstream temperature acceptability. The split's apparently better unbalanced pressure comes with an inboard temperature close to the assumed limit and cannot be adopted as robust cooling.

In the balanced split, differential outboard loss of141.856 /149.578kPa restores the nominal branch flows in this envelope. It is an inverse requirement, not a qualified balancing component. Known pressure after balancing is the maximum of the branch losses, not the sum of both branches. Existing losses must not be charged twice when selecting the balancing device.

## Joint inventory and pressure requirements
At the outlet-property minimum, inboard/outboard header inner radii are38.111/44.599mm. Across the candidate, this chosen header envelope reserves19.4495m3 of coolant and7.2221m3 of shell-plus-cap steel. That is approximately29.80%/26.39% of the respective inboard/outboard blanket coolant inventory and6.03%/5.35% of the respective blanket steel inventory. The mean-property minimization reserves19.9004m3 coolant and7.3919m3 steel. No new coolant or steel is added to the total inventory.

The remaining steel still has to provide the original support, walls and connections. Positive remaining volume is not proof it can do so. Likewise, these total volumes do not prove that the headers fit among actual breeder elements or that the proposed module-level connections can be manufactured.

The ideal smooth-barrel von Mises stress is about52.23MPa for the selected thickness/radius rule at8MPa. This is NOT an allowable-stress check; no irradiation-appropriate allowable, end-cap/nozzle design or pressure-vessel qualification has been supplied. Header Mach numbers are below0.09 in the nominal case, but a low Mach number does not replace a coupled pressure/temperature calculation or validate distribution losses.

The remaining loss contract is:
`max_s(known_branch_loss_s + K_s * sum(header_dynamic_heads_s)) + common_external_loss <= 550000 Pa`.
Here K_s is a deliberately defined equal additional coefficient applied to each of the three header stages in branch s; it is not a measured coefficient from a published manifold. In the outlet-property balanced case, the inboard per-stage coefficient ceiling is1.510 only if common external loss is zero. Allocating pressure to the heat exchanger or external pipes reduces that ceiling. These are competing budgets, not independent allowances.

## Numerical evidence
Nineteen focused tests passed with no failures/skips. These check exact source-state provenance, coolant/steel/cap accounting, invalid geometry rejection, saved-point reproduction, neighboring-radius pressure comparisons, the independent elastic-barrel identity, independent two-variable mass/pressure closure, fair treatment of the unsplit reference, restoration of nominal flow by balancing, and competition between fitting and external pressure allowances. This is not the full repository suite or experimental validation. The two coolant-property choices are alternative approximations, not confidence intervals.

The original prescribed-flow record and code hash are retained separately from the fair-baseline follow-on. A transient REPL syntax error while preparing the follow-on was corrected before its execution; the original driver was recovered and its hash checked against its frozen input before preservation. Scientific results were not silently overwritten. The final source and all declared inputs are archived for replay.

## Next decision, not another generic sweep
Do not optimize this assumed envelope further merely because its known-loss objective has a numerical minimum. The next work must replace a material unresolved interface: obtain or specify an actual header/take-off geometry and compatible loss evidence, establish whether its required steel can coexist with the remaining blanket structure, and resolve the spatial material layout needed by neutron transport. Before any additional simulation, compare against the published HCPB BSS/whole-loop methods and state the one acceptance decision it could change.

A viable next reference is an accessible author model or benchmark with header/take-off behavior; the examined papers establish that such methods exist but their abstract-level coefficients cannot be transplanted to this candidate. Obtaining those inputs or establishing a justified compatible geometry is a real evidence task. A full OpenMC/TBR calculation on unspecified ports, material isotopes, spatial source and hardware would still be premature.

The balanced split remains a candidate for this evidence check. The unsplit and independently controlled-loop alternatives remain legitimate references. The previous213.69MW conditional average has not been changed; no new reactor optimization, radiation transport, fuel-release calibration, physical experiment, email, paid cloud resource or autonomous service was performed here. This result changes the explicit volume/pressure acceptance requirements, not the claim that fusion has been solved.

## Primary references and reading scope
- Froio et al. (2016), DOI10.1016/j.pnucene.2016.08.007; author and publisher abstracts. The listed author manuscript was inaccessible through the attempted request; no code reproduction.
- Bertinetti et al. (2018), DOI10.1016/j.fusengdes.2018.04.099; author/publisher abstract and available introduction, including CFD comparison and planned experimental work. No measured coefficients taken.
- Zhou et al. (2023), DOI10.3390/en16145377; indexed publisher design description. Existing pin-based concept is different from this generic candidate.
- Verma et al. (2025), DOI10.1016/j.fusengdes.2025.114924; parsed paper text; no quantitative figure/table values used after screenshot failure.
- UKAEA PROCESS commit c0ae5b28649f2b20fb7efc7904628b6defe4151c; unchanged installed FirstWall/BlanketLibrary/pumping routines and candidate state.

Research-gate records are ADMISSION.json and FOLLOWON_ADMISSION.json. Exact numerical reproducibility does not validate the assumed topology, heat map or material properties.

## Integration with a newer committed reference
Before publication, the repository advanced from91648db to2629556074609ad89ee44e6e9bf0bf8e8e21ae6d with the independent-circuit study. This header study began against91648db; its original admission remains unchanged. The newer checkpoint is preserved, not overwritten or silently superseded. Its primary independent-regional-circuit reference is retained.

The direct Froio author-manuscript URL supplied by that checkpoint was subsequently accessed through the web reader. Parsed sections2,3.2.4 and4.2 confirm four independent regional circuits, omitted manifold pressure drops and omitted ex-vessel equipment in the reported simulation setup. A new Figure5 screenshot attempt failed; the topology conclusion here relies on explicit text, not unviewed diagram values. The initial403 access record therefore does not describe the final paper-access status. A runnable GETTHEM application is still not available in this study.

The header inventory and nominal branch pressure requirements are usable inputs to the preferred independent-circuit comparison: for the outlet-property split case, required known regional heads are373.255kPa IB and223.677kPa OB before omitted fittings and external equipment. No cross-region restriction is necessary merely because the common-pressure comparator needs one. These replace the channels-only pressure inputs for any future equipment comparison; the new hardware costs cannot be combined with the earlier31-34MW equipment budget without rerunning its matched thermodynamic boundary. That rerun and measured compressor qualification were not performed here. No new electricity credit is assigned.

Direct manuscript: https://iris.polito.it/retrieve/e384c42f-1249-d4b2-e053-9f05fe0a1d67/DEMO_HCPB_GlobalTHModel_review_final_static.pdf . New repository record: results/INDEPENDENT_CIRCUITS_DECISION_2026-09-07.md at2629556.
