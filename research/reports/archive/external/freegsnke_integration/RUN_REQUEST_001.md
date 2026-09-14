# FreeGSNKE reproduction run request 001

## Requested gate

Execute the unmodified upstream reproduction workflow for:

- repository: `FusionComputingLab/freegsnke`
- tag: `v3.0.1`
- expected commit prefix: `f776e90`
- runner: GitHub-hosted Ubuntu 22.04
- Python: 3.11

## Questions this run may answer

1. Does the frozen upstream source install without an undocumented local patch?
2. Does its upstream test suite pass in a clean, internet-enabled runner?
3. Which examples, notebooks and machine configurations are present at the frozen source identity?
4. Does installation or test execution modify the upstream checkout?
5. What exact dependencies and numerical environment are resolved?

## Questions this run may not answer

- whether a particular MAST-U discharge is reproduced;
- whether an ITER scenario is predictive;
- whether the candidate safety certificate is novel or correct;
- whether a reactor can deliver reliable net electricity;
- or whether sustainable fusion has been achieved.

## Next action is frozen before outcome

- If the untouched suite passes, select and run published equilibrium, evolutive and growth-rate examples unchanged.
- If it fails, preserve the unmodified failure and compare it with official installation requirements before proposing any compatibility patch.
- Do not tune candidate control mathematics in response to this software reproduction result.