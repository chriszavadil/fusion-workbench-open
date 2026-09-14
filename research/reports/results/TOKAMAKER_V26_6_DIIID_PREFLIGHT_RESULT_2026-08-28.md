# TokaMaker v26.6 DIII-D vertical-stability preflight — 2026-08-28

## Status

**PASS: exact official source, package, notebook, mesh and gEQDSK were located and hashed.**

This is a provenance/discovery result only. No equilibrium or VDE calculation was executed by this gate.

## Frozen package and source

- Package: `OpenFUSIONToolkit==26.6`
- Linux x86_64 wheel SHA-256: `249bcb741355b3e7b20a1d8abbd9fd10fc62464b3815c15868aba51a9012190f`
- Tag: `v26.6`
- Commit: `f3556a9e13298e646a00e1850c72211e185ed2c3`
- Official notebook: `src/examples/TokaMaker/DIIID/DIIID_baseline_ex.ipynb`
- Notebook SHA-256: `78180822cb975e403c396e78f280636acf927a7113c2bf0df3590b8b6dc2e439`

## Exact required inputs

| File | SHA-256 |
|---|---|
| `DIIID_mesh.h5` | `31c1c52cbd2f7bdedae74380a7a0a02426917179953544e7faea69606219001c` |
| `g192185.02440` | `6f33a01935847f25aea6edc45e939268ab910570ea6e8adb87528056a77520d5` |

The tagged source also contains `DIIID_geom.json`, the mesh-generation notebook and the official baseline notebook, so no reconstructed geometry or replacement equilibrium is needed.

## Preserved documentation discrepancy

The official notebook/documentation says in prose that the vertical growth rate is approximately `807 s^-1`, while its saved runtime output reports:

```text
Growth rate = 9.4598E+02 s^-1
Growth time = 1.0571E-03 s
```

The reproduction will not choose either value as convenient ground truth. It will execute the exact versioned notebook and report the new runtime result, while preserving the discrepancy as documentation evidence.

## Exact official calculation to reproduce

- DIII-D gEQDSK equilibrium: `g192185.02440`
- Mesh: `DIIID_mesh.h5`
- finite-element order: 2
- vertical-stability coil pair: `F9A:+1`, `F9B:-1`
- linear call: `compute_linear_stability(5.E3,10,False)`
- time-dependent setup: `setup_td(1.E-03,1.E-13,1.E-11,pre_plasma=False)`
- timestep: `0.1 / growth_rates[0]`
- nonlinear VDE steps: 40
- official thread request: 2

## Next gate

Execute every official notebook cell unchanged and append only an audit cell that exports:

- actual growth rates;
- timestep and solver trace;
- magnetic-axis vertical displacement history;
- unstable eigenmode-amplitude history;
- early-time exponential fits;
- all input/source hashes and runtime provenance.

## Claim boundary

A successful next gate will establish reproduction of one official TokaMaker DIII-D example. It will not yet establish a matched FreeGSNKE comparison, experimental MAST-U validation, ITER performance, controller recovery, or a fusion-power-plant result.
