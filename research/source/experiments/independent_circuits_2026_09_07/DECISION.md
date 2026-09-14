# Independent regional cooling circuits: reference-driven decision

## Decision and exact scope

Use independently controlled inboard (IB) and outboard (OB) circuits as the preferred reference for the next cooling-design comparison. Stop treating a common IB/OB pressure supply plus a balancing restriction as an unavoidable plant requirement. Retain that topology only as a clearly labeled comparator. The published arrangement does not eliminate distribution problems within a region.

This continuation changes an engineering reference and computes a conditional equipment budget. It does not establish new cooling physics, qualified compressors or manifolds, a complete loop, a higher plant output, tritium breeding, or a fusion breakthrough. The existing 213.69 MW conditional PROCESS average remains unchanged.

## What the research established before calculation

Froio et al. (2016, DOI 10.1016/j.pnucene.2016.08.007), Figure 5 and sections 2/3.2.4/4.2, describe four independent circuits: paired IB and paired OB loops. However, their manifold representation omits pressure loss, and the reported simulation configuration excludes ex-vessel equipment. The reference supports a topology, not validated losses for our hardware. Its older Be-based blanket geometry is not our TiBe12 candidate. The full manuscript and topology figure were inspected; no numerical figure/table values were transferred.

The primary ThermoPower repository was accessed and pinned at e2b011ac7fd90f9cf5771f29f1aefa160550b6ee. Its CompressorBase supplies the entropy/enthalpy and efficiency equations used here. This is equation-level reuse with a separate Python implementation, not execution of Modelica, reproduction of GETTHEM, or reuse of an actual machine performance map. Exact GETTHEM application code was not obtained; repository search timeouts do not prove it unavailable.

Chelihi et al. (2025, DOI 10.1016/j.fusengdes.2025.114872), institutional abstract and publisher text, separately identify geometry-specific manifold thermomechanical shortcomings under irradiation. We did not import a wall thickness or claim that a pressure-only calculation could qualify our manifold.

## Frozen candidate and boundary conditions

Project baseline: 91648db3ad2d6691dfe57f0b1b632ec20a36235a. Native PROCESS source: c0ae5b28649f2b20fb7efc7904628b6defe4151c. Full native-state SHA-256: cedcfa6d695fd45d4be17ea1ee77ae40d821064ea15eb1244822804f3001f9ea. Inherited flow-result SHA-256: 62ee10daa0f2ca4630095e43043e83351a7ff2aa128b8e2104bde8271b5f379a.

The test retains the previously proposed 4 m IB / 2 m OB first-wall paths, the same inferred channel pressure drops, and the same prescribed region flows: 682.5721 and 1698.0094 kg/s. External deposited heat is 708.3377 MW IB and 1762.1097 MW OB. The inlet to the blanket is compressor discharge at 8 MPa and 573.13 K. Isentropic efficiency 0.90, electrical-to-fluid-shaft efficiency 0.87, and recovered-heat conversion 0.40 are declared assumptions, not achieved hardware performance.

Two aggregate regions represent the independent-circuit option. Algebraically splitting either region into identical half-flow/half-heat circuits preserves its frozen work and fluid states; this does not reproduce the paper's counterflow heat transfer or redundant-train dynamics. The same regional flows can be supplied either independently or by common pressure with the previously required OB resistance.

For each mean/outlet property approximation from the previous hydraulic study, evaluate two external-loss cases: zero omitted loss; and equal omitted branch loss using the shared topology's remaining 550 kPa allowance. These are diagnostic endpoints, not measured manifold losses or uncertainty bounds. No additional geometric or performance sweep was run.

## The thermodynamic calculation

For each loop, suction pressure is discharge pressure minus the specified total loss. Suction temperature is solved so that an isentropic compression followed by the efficiency correction reaches the fixed discharge state. Real-helium entropy and enthalpy come from CoolProp 8.0.0. Heat deposition then raises the fluid enthalpy; the return heat exchanger brings it back to compressor suction. Ideal adiabatic flow resistance conserves stagnation enthalpy in this lumped ledger.

The loop identity is Q_HX = Q_external + W_fluid. Thus reducing compressor work saves electrical consumption, but also reduces recoverable heat. Under the declared constant conversion efficiency, the comparison is:

`net equipment budget = saved drive electricity - 0.40 * lost recovered heat`.

This is not a full power-cycle efficiency analysis. It assumes the changed cold-side temperatures and recovered heat can be accommodated. The actual suction temperatures range approximately 555.3-568.9 K across the saved independent cases; heat-exchanger approach temperatures and secondary-cycle performance are not validated. The native simplified pumping result is not replaced by this different-boundary thermodynamic calculation.

## Results: conditional operating-point budgets

| Hydraulic property approximation | Omitted-loss case | Drive electricity saved MW | Recoverable heat removed MW | Fixed-conversion net budget MW |
|---|---|---:|---:|---:|
| Mean | Channel only | 48.1455 | 41.8866 | 31.3908 |
| Mean | Shared 550 kPa allowance used | 49.0247 | 42.6515 | 31.9641 |
| Outlet | Channel only | 51.1430 | 44.4944 | 33.3452 |
| Outlet | Shared 550 kPa allowance used | 52.0116 | 45.2501 | 33.9115 |

The approximately 31-34 MW quantity is a budget that additional control, hardware, auxiliary and efficiency penalties could consume. It is a comparison against the hypothetical common-pressure, nominal-flow-balanced configuration, not an experimentally validated baseline or a claim of net improvement over the best existing HCPB design. It must not be added to 213.69 MW, annualized using assumed availability, or called achieved generation. Added manifold volume and structural/neutron effects are not included.

The unsplit alternative remains a live comparator. This calculation does not establish that the two-metre OB path is optimal, nor that independent circuits improve every possible common-pressure design. It resolves the specific decision not to require a cross-region balancing restriction merely because a diagnostic topology used shared pressures.

## The benefit is not immune to equipment penalties

A finite follow-on, admitted before its roots were evaluated, solved for efficiency degradation that would erase the budget. With the shared comparator still at 90% isentropic efficiency and equal efficiency assumed for the independent machines, the crossover is 55.77-56.01% in channel-only cases, or 71.37-72.44% in the external-loss endpoint cases. These are conditional requirements before other penalties, not predicted circulator efficiency.

Another inverse calculation finds an energy-only crossover at about 103-109 kPa of equal additional loss in both independent regions. That is NOT automatically usable pressure margin. In the endpoint that already uses the full 550 kPa allowance in the limiting region, allowable additional common loss is zero despite the positive energy-only crossover. Pressure, space and energy budgets must all pass together; the result records their joint minimum rather than quoting the most favorable one.

## Verification and non-results

Twenty-three focused tests passed. Checks include forward entropy/efficiency reconstruction, the independent ideal-gas limit, exact loop energy balance, numerical replay, zero benefit for identical heads, the two-identical-half-circuits identity, invalid inputs, and both sides of each head/efficiency crossover. Across saved operating states, maximum entropy mismatch is 3.64e-12 J/(kg K), compressor-equation residual is 3.73e-9 J/kg, and loop energy residual is 2.56e-13 MW. These verify bookkeeping and implementation, not actual performance or physical uncertainty.

The chosen property evaluations and pressure drops remain inherited approximations. There is no compressor-speed or surge/choke map, measured independent-circuit efficiency, dynamic control/failure analysis, resolved channel/header pressure field, heat-exchanger approach-temperature qualification, steam-cycle reoptimization, qualified irradiated structural design, spatial neutron heat map, or TBR. Extra circuitry is not cost-free. The paper comparison does not establish optimality among all cooling layouts.

## Next productive work, rather than another generic sweep

The reference architecture is now fixed for the next comparison: separate IB/OB control, with both the original unsplit and proposed OB-split paths retained. Next acceptance requires an explicit within-region header/control geometry and compressor/heat-exchanger performance data. Its pressure loss and material volume must be coupled to the same neutron and mechanical geometry. Do not design an added cross-region throttling element just to preserve the superseded hypothetical common-pressure arrangement.

A major breakthrough has not been established. A specific modeling detour has been removed, and the equipment penalties that could erase the local opportunity are quantified. This does not authorize adopting a guessed manifold, a better efficiency assumption, or a new electricity headline. Reference transfer and the finite numerical comparison are complete; the saved handoff identifies the remaining real interfaces.

## Preservation and reading scope

The companion experiment stores source, inputs, results, focused tests, a portable numerical replay, and source hashes. Public papers and the full third-party Modelica source are retained only in the desktop research folder and excluded from the redistributed experiment bundle. No new email, paid resource, system feature, software installation, recurring task or unattended agent was created. Native PROCESS source was not modified.

Primary sources:
- Froio et al. (2016): https://doi.org/10.1016/j.pnucene.2016.08.007 ; author manuscript https://iris.polito.it/retrieve/e384c42f-1249-d4b2-e053-9f05fe0a1d67/DEMO_HCPB_GlobalTHModel_review_final_static.pdf ; manuscript SHA-256 80bb616858c0a770aeeb84e6f876fd63428eb9226ef257db5110267255865ab4.
- ThermoPower: https://github.com/casella/ThermoPower/blob/e2b011ac7fd90f9cf5771f29f1aefa160550b6ee/ThermoPower/Gas.mo ; complete Gas.mo SHA-256 13a09b72eb02aa10731b7d1dc9553a949363e8e2b8546fe3e42ab6f3fd205f64. Equations inspected directly; no application performance data supplied by this source.
- Chelihi et al. (2025): https://doi.org/10.1016/j.fusengdes.2025.114872 ; institutional record https://publikationen.bibliothek.kit.edu/1000179404 . No geometric thickness or stress allowance transplanted.

## Continued investigation: measured circulator evidence

The next search located actual component experiments rather than another assumed-efficiency study. The 2021 KAERI paper (10.1016/j.fusengdes.2021.112299) reports circulator/recuperator tests and model comparisons. A newly indexed follow-on (10.1016/j.fusengdes.2026.116021) reports speed-dependent performance and operational testing. Publisher abstracts and section extracts were inspected, but usable numerical curves and their uncertainty records were not retrieved. The test-blanket application is not a scale-equivalent regional reactor circuit.

The follow-on has a November 2026 issue date; Crossref created its record on 20 August 2026 and deposited an update on 6 September. An exact online-publication date was not supplied. The publisher API returned HTTP 200 with metadata only and an open-access flag of zero, not the full article or curves. This is an access outcome, not evidence that the results do not exist. No paywall was bypassed and no paper was purchased.

A related motor-cooling study (10.1016/j.fusengdes.2025.115515) assumes 70% overall efficiency. It cannot supply measured isentropic efficiency for our comparison. These reading and access distinctions are saved in CIRCULATOR_EVIDENCE_GATE.json. No new experimental result, fitted curve, equipment selection or numerical plant improvement follows from locating the papers. No new email was sent.

Before any performance curve can replace the assumed efficiency, record its actual versus corrected mass-flow definition, suction/discharge pressure and temperature, rotational speed, shaft versus electrical power, efficiency definition, uncertainty and scale/similarity range. Obtain an independent test interval before model fitting. An abstract or nominal efficiency value does not meet that evidence requirement.
