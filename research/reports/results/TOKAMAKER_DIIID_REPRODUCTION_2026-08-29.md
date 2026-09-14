# TokaMaker v26.6 official DIII-D VDE reproduction

## Result

The exact frozen OpenFUSIONToolkit `v26.6` DIII-D notebook executed successfully with all original source cells unchanged.

- Source commit: `f3556a9e13298e646a00e1850c72211e185ed2c3`
- Dominant linear growth rate, full precision: `945.977599984245 s^-1`
- Printed notebook value: `945.98 s^-1`
- Linear e-folding time: `1.057107483 ms`
- Official timestep: `0.105710748 ms`
- Timestep identity error: `0.0`
- Time steps: `40`
- Final shifted trace time: `4.122719185 ms`
- First recorded relative magnetic-axis displacement: `-0.010080852363 m`
- Final relative magnetic-axis displacement: `-0.706777221575 m`
- Absolute displacement amplification: `70.110859x`
- Dominant-eigenvalue exponential amplification over the same shifted interval: `49.402449x`
- Generated `g192185_tokamaker` gEQDSK preserved and hashed
- Exact run artifact digest: `sha256:0227c1d88d7729a40155475f56b4765ed2bcac37a18a4db62b84ab5f812ea416`

## Documentation discrepancy

The versioned documentation prose says approximately `807 s^-1`, while the saved notebook output says approximately `945.98 s^-1`. The exact pinned runtime result is:

`945.977599984245 s^-1`

so the saved notebook output matches the reproduced dominant eigenvalue.

The nonlinear physical-output transient grows more slowly at first:

- axis-displacement log fit, first 10 points: `816.737272 s^-1` (`R^2=0.999991049`)
- axis-displacement log fit, first 20 points: `823.219257 s^-1` (`R^2=0.999978025`)
- eigenmode-projection log fit, first 10 points: `809.787586 s^-1` (`R^2=0.999982647`)
- eigenmode-projection log fit, first 20 points: `822.078562 s^-1` (`R^2=0.999939894`)

This could help explain why an older prose value near `807 s^-1` persisted, but source history or author confirmation would be needed to establish that interpretation. It is not treated as proven intent.

## Next gate

Run two independent controlled executions with tolerances frozen before the second run, then define a matched-physical-quantity contract for a future cross-solver case.

## Evidence boundary

This is a reproduction of one official simulated DIII-D example. It is not experimental DIII-D validation, a matched FreeGSNKE comparison, a controller recovery result, an ITER result, reactor safety evidence, or sustainable fusion.
