# Fusion Solution Set

A research and engineering program aimed at **working, sustainable fusion power**, not merely isolated mathematical novelty.

## Current evidence boundary

The project currently has reproducible reduced-model control/safety work and prior-art audits, but it does **not** yet have:

- a FreeGSNKE-derived machine model accepted by the repository gates;
- experimental MAST-U calibration;
- an ITER engineering prediction;
- a demonstrated quantum advantage;
- a complete fusion pilot-plant design;
- or evidence of sustainable net-electric fusion.

Current machine-validation work is tracked in issue #3. Independent solver cross-check work is tracked separately.

## Critical path

1. Reproduce the pinned upstream FreeGSNKE release without modifying its source.
2. Execute published equilibrium, evolutive and vertical-growth examples unchanged.
3. Export fully labeled plasma, active-PF, passive-conductor and actuator states.
4. Verify Jacobians, eigenvalues, perturbation responses and numerical convergence independently.
5. Reproduce an equivalent Open FUSION Toolkit/TokaMaker benchmark as a cross-solver check.
6. Freeze established watchdog, MCD/proximity, reference-governor, constrained-control, oracle and candidate-monitor predictions before nonlinear outcomes are run.
7. Score false-safe, false-unsafe, retained authority, runtime, recoverable displacement, latency and hardware reserve on identical plants.
8. Carry only validated results into existing whole-plant tools such as PROCESS or FUSE to measure availability, recirculating power, cost and net-electric consequences.
9. Advance blanket, tritium, plasma-facing-component, structural-material and RAMI workstreams through qualified existing tools and data rather than building weaker replacements.

## No-redundancy rule

A branch does not count as research progress unless it identifies:

- the concrete fusion decision it could change;
- the strongest relevant prior art;
- the established software or data it will reuse;
- a fair same-model baseline;
- a falsification experiment;
- measurable engineering value;
- and a stop or redirect condition.

We do not claim novelty for generic vertical controllers, rate limiting, anti-windup, controllability watchdogs, reference governors, disruption metrics, Grad–Shafranov solvers, whole-plant codes or tritium-transport codes that already exist.

## Quantum-computing rule

Quantum hardware is used only when a **machine-derived** workload reaches a measured classical bottleneck and a better answer could affect a real design or operating decision. Quantum output may generate hypotheses, diverse extreme-tail cases or design candidates; it never certifies plasma safety by itself. Every result must be replayed through deterministic classical physics.

## Validation ladder

- **V0:** idea or hypothesis
- **V1:** analytic result for a stated mathematical model
- **V2:** executable reduced-model validation and falsification
- **V3:** prior-art baseline reproduced on the identical plant
- **V4:** machine-derived free-boundary model with verified extraction
- **V5:** prospective MAST-U calibration or equivalent experimental evidence
- **V6:** unchanged transfer to ITER/reactor-scale scenario families
- **V7:** independent review, deployment or experimental validation

No result may be described above the level its evidence supports.

## Repository behavior

- Upstream source identities are frozen before execution.
- Unmodified failures are preserved; compatibility patches are separate proposals.
- Bulky generated traces and animations belong in GitHub Actions artifacts, not source history.
- Secrets belong only in encrypted GitHub environments or provider secret stores—never commits, issues or chat.
- The default answer to independent viable validation paths is **both**, provided each path passes the no-waste gate.

## Immediate status

The first pinned FreeGSNKE reproduction run is wired through GitHub Actions. Its immutable result is posted to the machine-validation issue and its complete logs are retained as an artifact. The next acceptable scientific milestone is an upstream reproduction result or a machine-derived validation advance—not another surrogate-only theorem number.