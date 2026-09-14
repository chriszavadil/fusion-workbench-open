# Confinement dependency experiment and read-only replay

This is a completed full-PROCESS experiment, with three numerically converged points and two rejected solver outputs. It is not a physical reactor design certificate. Read DECISION.md and both admission records before interpreting the numbers. Native physics/engineering is pinned at PROCESSv3.4.2 commit c0ae5b28649f2b20fb7efc7904628b6defe4151c. Internal hfact retains the core-radiation convention and is not blindly relabeled global experimental H98.

## Verify without rerunning optimization
Use the observed Python3.10 environment with that PROCESS revision installed. `support/` contains exact project runtime/helper files; UKAEA's license is included. The replay verifies manifest hashes, copies evidence into a temporary directory, independently reintegrates the electrical profiles and fatigue law, and reruns the17focused checks. It does not resubmit solver cases.

```
python replay.py --process-source <LOCAL_HOME>\FusionResearch\PROCESS-v3.4.2
```

Observed principal dependencies: NumPy2.2.6, SciPy1.15.3, CoolProp8.0.0, Numba0.67.0, PyVMCON2.4.2, pytest9.1.1. Full package inventory is in requirements-observed.txt. Install the pinned official PROCESS source rather than a similarly named package.

## Full solver reconstruction
The attempt-specific run_case.py/run_inverse.py/run_native_validation.py are the executed drivers, not generalized installers. They expect a workspace parent containing the pinned clone under PROCESS-v3.4.2, the helper files from support, and the original baseline IN/MFILE under runs-20260907/adaptive30y_warm_fixed. Copies of those baseline files are included as BASELINE_INPUT.DAT and BASELINE_MFILE.DAT. Input/result hashes are checked and existing case directories are never overwritten. Use a separate fresh workspace for full regeneration and600second subprocess timeouts as in execute_bounded.py.

The existing objective catalog does not include minimum-H; min_h_objective.py is a disclosed runtime-only objective adapter. The native slot1 banner is not authoritative for that one case. A subsequent native radius-objective solve is separately recorded. All five case folders include the original raw output and failed attempts. No later header/circulator assumptions are combined with these points.

Campaign folder names retain2026-09-07; raw runs crossed the UTC date boundary, which is preserved in native logs. No test or archive count is a novelty claim. Source PDFs and third-party frameworks are not bundled. No background task, cloud resource or new email is created by the replay.
