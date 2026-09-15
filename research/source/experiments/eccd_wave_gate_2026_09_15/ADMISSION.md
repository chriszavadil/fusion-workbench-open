# EC wave/deposition qualification admission — 15 September 2026

## Decision
Can an established wave/absorption/current-drive solver replace the scalar EC-efficiency assumption behind the higher-output plant case? The required candidate total remains 7.597810 MA from 170 MW credited drive power with retained heating/profile control. Do not repeat the six completed PROCESS solves or the fixed-current arithmetic gate.

## Execution change
The authorized research computer remains paired, but Desktop Commander explicitly paused calls at its monthly usage limit. No remote call will be retried to bypass that limit. The public repository's standard Ubuntu GitHub-hosted runner is used instead, with read-only contents permission and no credentials available to solver execution. No paid larger runner, private repository, ongoing schedule or unattended service is created. GitHub documents standard public-runner minutes as free. At most two short public-reference solver runs are admitted initially, each capped at 180 seconds, one thread, within a 15-minute workflow timeout. A result artifact has one-day retention; no solver binary or full installed environment is uploaded.

## Prior art and initial qualification gate
GENRAY is the existing Smirnov/Harvey/Petrov/CompX ray-tracing code, publicly distributed under GPL-3.0-or-later. Pin `compxco/genray` to `ee443d16e5aaf9bc7227fb3e95581e3ba374df89` (GENRAY v12.1). Use its own canonical ITER single-ray EC regression inputs (test5 and test5.1) before any candidate calculation. Preserve complete inputs, output arrays, license, hashes, numerical options and failures. These are computational reference cases, not this project's measurements, our reactor equilibrium, or experimental validation. Different dielectric models are a sensitivity comparison, not independent experimental evidence.

The maintainers' official makefile and dependency recipe were inspected. The only build adaptation permitted initially is the modern gfortran legacy argument-compatibility flag; do not change a physics equation or tolerance to force agreement. Build serially to respect Fortran-module dependencies. No xdraw or interactive display scripts are executed.

Lopez et al., arXiv:2501.04619, use HARE to identify a resonant interaction then reverse/forward trace it, avoiding a blind launch sweep. Seino et al., DOI 10.1016/j.fusengdes.2024.114460, show that launch position and unwanted harmonic absorption matter. These methods and results are theirs, not discoveries by this project. A candidate calculation additionally needs a consistent equilibrium, flux-coordinate definition, density/temperature/effective-charge profiles and current-profile/control targets. Do not borrow a reference plasma and label it our candidate.

## Acceptance and continuation
Require finite trajectories, nonnegative remaining power, explicit absorption and current units, and an auditable code/input/data chain. A failed solve remains failed. The canonical-reference stage may establish executable wave-model capability only. Before any candidate run, record a separate input admission showing which quantities are reproduced candidate outputs and which equilibrium/profile assumptions are provisional. A proxy-equilibrium result cannot certify current-profile stability or preserve reactor performance.

## Sources
- https://github.com/compxco/genray/tree/ee443d16e5aaf9bc7227fb3e95581e3ba374df89
- https://www.compxco.com/genray.html
- https://arxiv.org/abs/2501.04619
- https://doi.org/10.1016/j.fusengdes.2024.114460
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job

No accepted systems configuration, archived neutron result, released Unreal binary or previously blocked HCPB publication is changed by this admission.
