# Integrated candidate path — 7 September 2026

## Status

**Promising integrated hypothesis; not a fusion breakthrough.** The purpose of this checkpoint is to identify a quantitatively testable same-design target after correcting the PR42 power-accounting, blanket-coupling and central-solenoid-fatigue errors.

## Power target that survives conservative screening

The authenticated PR42 baseline is 400.0225 MW net during flat-top but only 216.8188 MW when the complete pulse/dwell profile and assumed 80% availability are included. Its FW/blanket coolant-pump electrical load is 266.8511 MWe.

Published EU-DEMO HCPB fuel-breeder-pin studies report approximately 80–90 MW plant circulating power for an approximately 2.4 GWth helium-cooled reactor, with 16 helium blowers around 5–6 MW each. To avoid using the favorable end of that range unadjusted, this screen takes **90 MW mechanical** and scales it linearly by the PR42 FW/blanket heat load, 2595.0/2400.0, giving **97.314 MW mechanical**. Applying the PR42 87% pump electrical efficiency gives 111.855 MWe.

The current EU-DEMO pulsed-design literature repeatedly uses a **600 s dwell target**. Holding PR42 fusion power, gross electrical generation, non-pump/non-EC loads and all non-dwell pulse phases fixed gives:

| EC wall-plug→injector efficiency | Dwell | Availability-adjusted average net |
|---:|---:|---:|
| 50% | 600 s | 365.26 MW |
| 55% | 600 s | 387.77 MW |
| **58.16%** | 600 s | **400.00 MW** |
| 60% | 600 s | **406.53 MW** |

PROCESS defines `eta_ecrh_injector_wall_plug` as ECH wall-plug-to-injector efficiency. A 60% full EC-system efficiency is still an R&D target, not demonstrated plant performance. In June 2026 KIT reported the first MW-class gyrotron multistage-depressed-collector implementation with gyrotron overall efficiency above 60%; earlier DEMO technical studies projected ~61% total technical EC efficiency only with ~70% gyrotron efficiency plus high power-supply/transmission efficiencies. Therefore 58.16% is a concrete technology requirement, not a solved assumption.

## Corrected CS fatigue screen

The baseline produces only 5736.98 allowable PROCESS CS cycles because constraint 90 was omitted. The prior reduced redesign held the 8.30 mm conduit thickness fixed while raising steel fraction. That was internally inconsistent with PROCESS: its EU-DEMO turn geometry automatically thickens the conduit as steel fraction rises.

Using the PROCESS hoop-stress, EU-DEMO turn-geometry and fatigue equations together, while preserving first-order CS ampere-turns and peak field and enforcing the existing 0.7 BOP current-density ratio, gives the following symmetric-widening screens:

| PROCESS fatigue target | CS radial width | Steel fraction | Overall J | Hoop stress | Conduit | Extra radial width |
|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.5383 m | 71.5% | 18.50 MA/m² | 438.0 MPa | 8.30 mm | — |
| **20,000 cycles** | **0.7404 m** | **81.2%** | **13.45 MA/m²** | **294.0 MPa** | **9.81 mm** | **+0.2022 m** |
| 40,000 cycles | 0.9489 m | 85.3% | 10.49 MA/m² | 229.2 MPa | 10.49 mm | +0.4106 m |

The 20,000-cycle target matches PROCESS constraint 90's default and the published EU-DEMO plasma-cycle design target. External DEMO magnet studies describe fatigue as the principal CS winding-pack driver and evaluate structural/superconductor grading as a design lever. This screen is not a full PF equilibrium, flux-swing, quench, thermal-hydraulic or superconducting optimization; the candidate must survive the actual PROCESS rerun and higher-fidelity magnet analysis.

## Why this is the current lead

For the first time in this branch, one narrow parameter region simultaneously has numerical targets for: (1) >400 MW availability-adjusted average electrical output in the frozen PR42 accounting; (2) a published HCPB circulating-power architecture; (3) the published 600 s DEMO dwell target; (4) a quantified EC-system efficiency requirement; and (5) a CS geometry/stress region that closes the PROCESS 20,000-cycle fatigue equation in the reduced screen.

What is still missing is decisive: the **same physical design** must be reoptimized with constraint 90, source-matched heterogeneous HCPB neutronics/TBR and nuclear heating, tritium inventory, full PHTS/BoP transients, superconducting/flux constraints, maintenance/availability and independent validation. GitHub-hosted heavy calculations are currently failing before runner allocation (`runner_id=0`, zero executed steps), so those failures are infrastructure evidence only.

## External evidence used for targets

- HCPB fuel-breeder-pin design and 80–90 MW circulating power: Fusion Science and Technology 75 (2019), “Advancements in the Helium-Cooled Pebble Bed Breeding Blanket for the EU DEMO”; later HCPB design-status work reports 16 blowers at ~5.625 MW each.
- EU-DEMO dwell: published PF and fuel-cycle studies use 600 s between ~2 h pulses.
- EC efficiency: EUROfusion/KIT DEMO HCD studies; KIT 2026 “Realization of the First MW-Class Gyrotron Multistage Depressed Collector.”
- CS fatigue: PROCESS constraint 90 and EU-DEMO CS design literature; PROCESS source commit `c0ae5b28649f2b20fb7efc7904628b6defe4151c`.

## Claim boundary

This is a **cross-study screening hypothesis**, not an integrated reactor result. No result here establishes tritium self-sufficiency, qualified magnet lifetime, demonstrated EC-system efficiency, achieved availability, net-energy economics, reactor safety, or sustainable fusion. The next valid breakthrough gate is a source-matched integrated calculation/validation on one design, not another independent favorable subsystem result.
