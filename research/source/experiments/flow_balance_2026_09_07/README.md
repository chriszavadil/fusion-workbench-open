# Candidate cooling-flow acceptance test

This is a bounded application of established parallel-flow and heat-transfer methods to the recorded PROCESS candidate, not new cooling physics or an operational reactor design. See DECISION.md and RESULT.json. All numeric results remain conditional on the frozen geometry, heat loads, coolant correlations, flow-topology choice and temperature criterion.

## Reproduce
Use an isolated Python environment with an editable clone of official UKAEA PROCESS at commit `c0ae5b28649f2b20fb7efc7904628b6defe4151c` (v3.4.2). `requirements-observed.txt` records the actual Windows/Python3.10 environment; it is not a guarantee that every package is available unchanged on every platform. The existing authorized desktop environment is at `<LOCAL_HOME>\FusionResearch\.venv-process-310`.

From this experiment directory, run:
```text
<isolated-python> replay.py
```
The replay checks source/input hashes and the installed PROCESS revision, reads INPUT_STATE.json, writes to a fresh temporary output directory and compares the numeric output against RESULT.json. It then executes the 25 focused tests. This entry point was actually exercised from a separate parent directory to avoid relying on the original study's file paths.

`branch_balance.py` is the original calculation driver and expects the full captured-state workspace in its parent directory. Use `replay.py` for the portable subset. Its load adapter is explicit: the original full-state SHA remains provenance, while the subset SHA is verified independently. The source copy `evaluate_frozen_fw_final.py` is the unchanged inherited native-model wrapper.

PORTABLE_MANIFEST.json hashes the original calculation/replay files, not this later README or DECISION.md. The separate raw evidence ZIP includes those original files and the successful portable-replay log. Later documentation is preserved as normal repository files. Do not infer physical accuracy from exact replay or the numerical tolerances.

## Research admission
ADMISSION.json records the relevant prior work before new calculations. FROZEN_INPUT.json records the exact numeric/algorithm contract. A continuation must state the closest published baseline, remaining question, data/geometry readiness, intended difference, decision affected and finite completion/rejection rule before running. An already solved general mechanism is not a reason to repeat generic sweeps.

## Limitations
The common-pressure aggregate topology is assumed; real headers and independent controlled loops are not modeled. Extra balancing losses are inverse requirements, not free or specified hardware. Mean/outlet properties are alternatives, not uncertainty bounds. Header volume and pressure budgets must be allocated jointly with steel and neutron geometry. No increased electrical output, matched TBR or experimental cooling validation is claimed. No background or scheduled process is installed.
