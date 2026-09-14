# FreeGSNKE upstream reproduction — first connected run

## Status

**FAIL-CLOSED before model export.**

The local adapter unit-test job passed. The pinned upstream job checked out the
intended FreeGSNKE source and installed successfully, but FreeGSNKE's own test
suite failed before our notebook exporter was allowed to run.

## Exact provenance

- Repository: `FusionComputingLab/freegsnke`
- Tag: `v3.0.1`
- Commit: `f776e908c8c333411f9824cbcfed674fafff8dfd`
- Python: `3.10.21`
- GitHub Actions run: `33180913088`
- Upstream job: `98881558058`
- Resolved FreeGS4E in the first run: `0.14.0`

FreeGSNKE v3.0.1 declares `freegs4e~=0.12`, which permits later `0.x`
minor releases under Python packaging compatible-release semantics. The first
connected run therefore resolved the recently released FreeGS4E 0.14.0.

## Upstream test result

```text
2 failed, 5 passed, 4 skipped, 3 errors
```

All five failed/erroring physics tests reached the same exception before the
intended equilibrium solve completed:

```text
AttributeError: 'ConstrainPaxisIp' object has no attribute 'inputs'
```

The exception originates in FreeGSNKE `freegsnke/jtor_update.py` when
`Jtor_universal.copy()` unconditionally executes:

```python
obj.inputs = self.inputs[::]
```

The failures affected:

- linearised growth-rate setup;
- linearised stepper setup;
- nonlinear stepper setup;
- inverse static diverted-solve regression;
- static forward solve.

## What this does and does not establish

This establishes that **the exact tagged release plus the dependency version
selected by its declared constraint is not reproducible on the recorded runner**.
It does not yet establish whether the cause is:

1. FreeGS4E release drift within the broad `~=0.12` constraint;
2. a latent FreeGSNKE v3.0.1 copy-path defect independent of FreeGS4E version;
3. a more specific environment interaction.

Current FreeGSNKE `main` still contains the same unconditional `self.inputs`
copy, so there is no public source-level fix on `main` as of this audit.

## Frozen next experiment

Run the unmodified FreeGSNKE v3.0.1 test suite against exact FreeGS4E releases:

- 0.12.0
- 0.13.0
- 0.13.1
- 0.14.0

No source patching is permitted. A model export may run only in a matrix cell
where the complete upstream test suite passes. If no cell passes, open a
minimal upstream bug report and keep the machine-result gate closed.

## Claim boundary

No machine-derived model was produced in this run. No MAST-U, ITER, controller,
or reactor conclusion is supported by this failed reproduction.
