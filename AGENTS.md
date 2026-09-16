# Fusion Workbench research continuation

Before new scientific execution, read `project-status.json`, search `research/prior_work_register.json` and the current research library, and verify the public branch and any open contributor issues. Research primary sources before spending compute. Reuse established methods and attribute original investigators, model maintainers and data custodians; do not call replication a discovery.

Every admitted task needs a specific unresolved decision, closest prior work, preserved source/input hashes, bounds on execution, a falsification test and a reopening condition. Do not repeat closed generic demonstrations merely to accumulate test counts. Retain failed, no-score and inconclusive outputs. Do not tune inputs after seeing a measurement simply to improve agreement.

Update the dated report, prior-work register, reviewed dataset and live browser when results are ready. `tools/build_benchmark_evidence.py`, `tools/build_research_library.py` and `tools/build_pages.py` project the current evidence. Run `python -m pytest -q tests`; audit privacy and attribution before pushing; verify public Pages and hosted CI after deployment. Keep the released Windows executable version separate unless a new binary is actually built and tested.

The canonical source banks and scientific outputs must not be truncated to meet a rendering limit. Display subsampling is a separate, labeled policy. Model/simulation verification, agreement with measurements, whole-reactor fuel closure and actual generated power are different evidence levels. No percentages of fusion solved.

Never publish private correspondence, credentials, workstation details, raw private history or data without rights. Do not execute unreviewed contributor code on the development computer. Do not repeat any previously blocked destructive operation through a different tool or expose old private repositories. This public clean repository is the collaboration destination.

## Power-progress update contract
When recording a power result, update the explicit history/source/eligibility projection in `tools/build_power_progress.py`; `build_pages.py` rebuilds it. Keep conditional average net electricity as the primary model score; distinguish maintained references, exploratory designs, retired screens and failed solves. Missing measured electricity stays null, not0. Keep physical MJ yields, peak fusion MW, interval-average fusion MW and modeled electric MW separate. Add primary-source dates and uncertainty scope to `research/power_progress/WORLD_MILESTONES.json` when refreshing measurements. Preserve failed/superseded and non-record follow-ups. A qualification-only update must not manufacture a new power point or promote an unqualified record.
