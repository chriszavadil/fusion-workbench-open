# FreeGSNKE v3.0.1 official example05 reproduction

## Result

The complete official `example05 - evolutive_forward_solve.ipynb` executed successfully with every original source cell unchanged.

- Exact upstream commit: `f776e908c8c333411f9824cbcfed674fafff8dfd`
- FreeGS4E: `0.13.1`
- Retained evolving state dimension in the final example: `44`
- Linear history: `51` points over `25.000 ms`
- Nonlinear history: `51` points over `25.000 ms`
- Official step: `0.500 ms`
- Final linear magnetic-axis Z: `1.802009 mm`
- Final nonlinear magnetic-axis Z: `1.587459 mm`
- Maximum linear/nonlinear Z difference: `0.527760 mm`
- Z-history relative L2 difference: `0.188766`
- Complete evolving-current-history relative L2 difference: `0.015092`
- Run artifact digest: `sha256:d06876b1fe90f24a58d033f8121ef76c22bf2a3d055c8b57603e0bfbf4a404a3`

## Interpretation

This official example demonstrates that its local linear and nonlinear free-boundary trajectories are similar but not interchangeable over the complete 25 ms interval. In this reproduced case, the vertical-output relative L2 difference is approximately `18.88%`, while the full evolving-current history differs by approximately `1.51%`.

Those values belong to this exact notebook configuration. They are not yet a general recovery-certificate model-error bound.

## Next gate

1. Freeze repeatability tolerances before a second independent execution.
2. Freeze small active-voltage and initial-state perturbations before running them.
3. Compare the accepted 151-state linear export against held-out nonlinear FreeGSNKE rollouts.
4. Determine the amplitude/time region where the linear model is predictive enough for prospective safety decisions.

## Evidence boundary

This is an official public MAST-U-like solver-example reproduction. It is not experimental MAST-U validation, a controlled-recovery result, an ITER prediction, reactor safety evidence, or sustainable fusion.
