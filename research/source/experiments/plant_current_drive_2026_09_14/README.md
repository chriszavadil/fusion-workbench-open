# Whole-plant current-drive allocation study

Original integration code: Fusion Workbench contributors, MIT. Original generic tokamak input: James Morris, UKAEA. UKAEA PROCESS and its inputs/physics retain the existing upstream terms; this directory does not contain or relicense the full solver.

Read `research/reports/results/PLANT_CURRENT_DRIVE_DECISION_2026-09-14.md` before using the numbers. The controlled result is a candidate-specific systems-model lead, not achieved electricity or validated plasma control. The total input power and modeled current-drive efficiency are unchanged; the heating-only allocation changes from 75 to 30 MW. A fixed major radius does not mean identical optimized components.

## Rebuild the exact executed inputs without running a solver
From the repository root:

```sh
python research/source/experiments/plant_current_drive_2026_09_14/prepare_inputs.py --base research/approved_inputs/r838.IN.DAT --output plant-input-replay
```

The output directory must not already exist. Both generated input SHA-256 hashes must equal the reported executed hashes; they were verified against the original two files on the research computer. The apparent zero-heating line retained inside each file is a historical construction step; its final 75 or 30 MW assignment overrides it. The final two files differ only in that last allocation. All 27 pulsed constraints and 19 shared iteration variables remain present.

## Optional new full-model execution
Use a Python environment with the existing pinned PROCESS dependencies and the clean PROCESS source revision `c0ae5b28649f2b20fb7efc7904628b6defe4151c`. The workbench's optional setup procedure provides the pinned solver; no installation is performed by these scripts. For each selected allocation, explicitly run:

```sh
python research/source/experiments/plant_current_drive_2026_09_14/reproduce.py --workbench . --process-source PATH_TO_PINNED_PROCESS --reserve 75 --output NEW_CONTROL_DIRECTORY
python research/source/experiments/plant_current_drive_2026_09_14/reproduce.py --workbench . --process-source PATH_TO_PINNED_PROCESS --reserve 30 --output NEW_ALTERNATIVE_DIRECTORY
```

This portable reproduction wrapper is provided for contributors. The reported six solves used the exact local driver versions preserved with the research evidence; the new portable wrapper is not claimed to have undergone another full execution in this continuation. It verifies source revision/cleanliness and the three disclosed runtime-adapter hashes, reconstructs the exact input, installs the adaptive-fatigue and dynamic pulse-duty requirement, limits each child solve to 240 seconds and one thread, and writes into a new directory only. It does not modify the accepted reference, expose a worker or run untrusted submissions. Keep its raw logs local; they may include machine paths.

A zero process exit is not proof of numerical convergence: inspect `numerically_converged` and `ifail`. The original steady-state cases were unsuccessful and are not useful-power results. A converged new run must also preserve constraints, pulse-energy accounting and assumptions; cross-platform or optimization differences are an investigation, not permission to tune toward the desired number.

## Public versus full raw data
`docs/plant-decision/data.json` is the exact displayed selected-metric and scheduled-profile projection, including hashes. It is not a claim that all raw output fields were exported. The public tests reconstruct both inputs, integrate the recorded schedules, check power/current allocation, count the shared constraints/variables and retain the failed-case scope.

The original local evidence retains all six attempted inputs, raw outputs, logs, execution statuses, initial admission, successive explicit amendments and both used driver versions. No new steady-state demonstration, global optimum, experimentally sufficient 30 MW control allocation, maintained fuel supply or new qualified magnet lifetime is asserted.

## Prior-work/reopening record
The existing EU-DEMO design-space paper documents current-drive recirculation and pulsed-operation trade-offs: https://doi.org/10.1016/j.fusengdes.2022.113080 . The EU-DEMO heating-system paper documents distinct heating and control roles: https://doi.org/10.1016/j.fusengdes.2022.113159 . Sugiyama et al. demonstrate the value of integrated pulsed/current-profile modeling for JA-DEMO: https://doi.org/10.1088/1741-4326/ad49b6 . These are original authors' methods and findings, not achievements of this project.

Do not repeat the present scalar sweep. The next justified question is whether a specified EC deposition/current-profile/control solution can supply the additional current credit while meeting the retained physical functions. Only a changed, substantiated limit, numerical defect or declared robustness question justifies reopening this systems comparison. Do not borrow a neutron-benchmark discrepancy as a correction to this different reactor.

## Additional exact execution evidence
The six original input files and safe per-run result/status projections are also published under `runs/`, together with every admission amendment, independent checks, reference projections and exact original driver versions. Raw MFILEs and private logs remain in the local evidence archive. The original drivers are preserved for audit and are not portable installation scripts; use the bounded reproduction wrapper for the final pair. No raw process error trace is present in these six result projections.

## Current-drive rejection gate
Run `python actuator_gate.py` from this experiment directory to recreate the necessary current-budget check from the frozen, hash-linked scalar record. It requires no solver and gives no new power prediction. The alternative requires7.597810MA from170MW (44.692999kA/MW); passing that necessary total-current condition does not establish deposition, current-profile stability or heating/control sufficiency. The original study report credits the reviewed Seino and Lopez papers and distinguishes normalized gamma from dimensionless efficiency.
