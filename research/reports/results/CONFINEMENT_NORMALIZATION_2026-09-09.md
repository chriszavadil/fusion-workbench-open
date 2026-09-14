# Confinement comparison: match the energy and power boundaries

## Decision and prior art
We resolved a reporting-definition ambiguity for the two stored reactor concepts. This is application of established confinement accounting, not new fusion physics, a new reactor optimization or evidence of experimental feasibility. UKAEA issue 652 already discussed reversing exactly the radiation subtraction in 2018; issue 3534 later documented that the 0.31 exponent is not appropriate to every confinement scaling. We therefore did not submit a duplicate discovery claim or start another H-factor sweep.

The existing STEP-0D work couples equilibrium, pedestal and transport models. It remains a higher-fidelity reference to reproduce, not an experiment we have completed. Our two scalar conversions alone do not replace that validation.

## The question answered
Can the displayed internal confinement multipliers be compared directly to each other and to an experimental global H98 value? Not without matching definitions. Both archived inputs select IPB98(y,2), mode 34, and core-radiation subtraction, mode 1. For these inputs, power used in the confinement scaling is deposited heating minus core radiation. The scaling varies as P^-0.69.

Keeping the same thermal stored energy W and all other scaling inputs fixed, changing from transport power P_tr to deposited heating P_heat changes the normalized factor by:

    H_thermal,deposited = H_internal * (P_tr / P_heat)^0.31

This follows independently from dividing W/P_heat by the IPB98 confinement time evaluated at P_heat. It is a steady-state, thermal-energy, deposited-power normalization within this model, NOT an independently measured experimental H98.

## A known accounting issue matters in our archived version
The pinned code defines core radiation as impurity core radiation plus synchrotron radiation. Its stored inner-radiation power therefore already includes synchrotron radiation. The H* reporting expression nevertheless adds both inner-radiation power and synchrotron power back to P_tr. That adds the synchrotron term twice. We reproduced the archived H* and compared it with undoing exactly the subtraction used by the solver. Original files and accepted power outputs are unchanged.

| Configuration | Internal factor | Archived H* reproduced | Matched thermal/deposited-power factor |
|---|---:|---:|---:|
| r838, 8.38 m reference | 1.200000 | 1.065390 | 1.086393 |
| r900, approximately 9 m comparator | 1.030000 | 0.922935 | 0.937743 |

The correction raises this converted diagnostic by approximately 1.97% and 1.60% respectively. It does not create extra power, change geometry, prove stability or certify a confinement margin. The 0.937743 value must not be advertised as experimental proof that the larger reactor is feasible below H98=1.

## Checks and limits
The two archive hashes and scalar inputs were frozen before evaluation. The factor was computed by algebra and independently by thermal energy divided by the explicit IPB98 power law. Both original internal factors and both archived H* values were reproduced; heating equals transport plus the original core-radiation term. The pinned upstream static scaling function is an additional cross-check of the equation-level implementation. These are numerical and definition checks, not independent physical evidence.

Thermal stored energy is about 85% of the total beta-derived energy in these records; these energy quantities must not be interchanged. Fast-particle losses, input versus absorbed auxiliary heating, transient dW/dt, geometry/elongation definitions and the calibration domain of a real confinement database still need to match. No current candidate is promoted to experimentally validated status.

No new full PROCESS optimization, hardware experiment, neutron calculation or random parameter sweep was run for this audit. The existing model power averages remain unchanged. The next evidence gate is an externally grounded profile/transport or experimental reference with those exact definitions; the app now exposes the ambiguity rather than hiding it behind one H-factor label.

## Reproduction and sources
Run `python audit.py` in `research/source/experiments/confinement_normalization_2026_09_09`; it reads the privacy-safe frozen scalar input and writes `KEY_RESULTS.json`. The original raw MFILE files remain private; their hashes are in the frozen input. This reduced replay does not require the full solver.

- UKAEA PROCESS confinement conventions: https://ukaea.github.io/PROCESS/physics-models/plasma_confinement/
- Existing correction discussion: https://github.com/ukaea/PROCESS/issues/652
- Scaling-scope issue: https://github.com/ukaea/PROCESS/issues/3534
- Pinned source: https://github.com/ukaea/PROCESS/tree/c0ae5b28649f2b20fb7efc7904628b6defe4151c
- Source interfaces: `process/models/physics/radiation_power.py`, `physics.py`, and `confinement_time.py` at that pin; full file hashes recorded.
- STEP-0D prior art, Slendebroek et al.: https://arxiv.org/abs/2305.07285

The software findings and literature above were read on 9 September 2026. No uniqueness claim is made for the correction; the existing issue history is part of the result.
