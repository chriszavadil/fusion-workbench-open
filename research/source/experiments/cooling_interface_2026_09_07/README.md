# Executed candidate cooling screen

This directory preserves exact executed evaluators, a verified minimal native-state subset, and a tested portable replay. It is not the full raw PROCESS archive or a physically validated plant. See results/COOLING_INTERFACE_DECISION_2026-09-07.md.

## Reproduction

From this directory, with Git and Python3.10, create an isolated environment:

```powershell
git clone --depth 1 --branch v3.4.2 https://github.com/ukaea/PROCESS.git PROCESS-v3.4.2
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e PROCESS-v3.4.2
.\.venv\Scripts\python.exe replay_cooling_gate.py --input MINIMAL_THERMAL_STATE.json --output replay-results
```

Existing desktop environment: <LOCAL_HOME>\FusionResearch\.venv-process-310\Scripts\python.exe. Reinstallation is unnecessary there. Always use a fresh replay output directory; completed results are never overwritten.

The replay verifies the imported source checkout commit and clean worktree, checks canonical JSON input identity, executes all three local screens and tests selected outputs. It was actually executed successfully: temperature agreement within1e-6K, pressure within0.01Pa. This is numerical consistency, not physical uncertainty or independent experimental validation.

The repository input is a compact serialization of exact values from the original minimal subset. Original Windows subset-file SHA25675c998edb5a105f54c2184d716a48d3d45822c2c2af490f512e639723b35000f applies to the downloadable original bytes, not this compact serialization. The adapter instead verifies canonical-content SHA256e4b60da381973ff3950e90a7edec234b26f0959925aa88e58da8f6768249f619. No field value is changed. The full original state hash is cedcfa6d695fd45d4be17ea1ee77ae40d821064ea15eb1244822804f3001f9ea.

The legacy filename SOLVED_STATE.json inside a replay contains the subset, explicitly described in REPLAY_PROVENANCE.json, not the complete324189-byte captured state. Full state, original captures, failed post-processing attempts,16 focused tests and original source/result files are retained in <LOCAL_HOME>\FusionResearch\Fusion_cooling_raw_evidence_2026-09-07.zip, SHA256b840243752f0c6237c9d7af4c25ac169166d7eed48dca56d0ad868946b99c73a,628111bytes.

Exact SHA256 of executed script bytes:
- evaluate_frozen_fw_final.py:773ab997cad8265708eab529d08723f807db168e0ec9fd5d2a26cd28fb684dae
- coolant_volume_gate.py:75226d349b3f94dd8e22c6a98c5643f7e702b5e77fe158fb4521b4f37ce76aa6
- split_fw_intervention.py:5f35fb4b5196dc7788fd34cd18f96d02fce9a2966f91ac6b1dc602bf31721762
- replay_cooling_gate.py:b9e66af66015e641e3bee0be10063b46895dab394fa59bfe2bff4c789c607f07

No higher plant electricity, new TBR, actual safe operating temperature or novel parallel-cooling physics is claimed. The outboard-only split is a selected local follow-on with added manifold/connection volume, pressure, flow-balance, structural, neutron and reliability costs still unresolved. Mean/outlet-property estimates are not confidence bounds. Native heat peaking remains assumed1.0. Retain the UKAEA MIT license when reusing the upstream implementation.
