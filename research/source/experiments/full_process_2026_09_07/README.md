# Full PROCESS comparison: executed desktop checkpoint

This directory preserves the exact final successful driver and runtime modules used on the authorized Windows desktop on 2026-09-07. It is not a new physical-material model or a validated fusion plant. See `results/FULL_PROCESS_LIFECYCLE_2026-09-07.md` and the compact results at repository root.

Use a fresh copy of this directory with Python3.10 and Git. The driver refuses to overwrite completed case directories. The original execution used an isolated venv, one numerical thread, and a600second timeout per optimization. On PowerShell:

```powershell
git clone --depth 1 --branch v3.4.2 https://github.com/ukaea/PROCESS.git PROCESS-v3.4.2
py -3.10 -m venv .venv
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e PROCESS-v3.4.2
.\.venv\Scripts\python.exe -c "import subprocess,sys; subprocess.run([sys.executable,'run_warm_fixed_process.py','baseline_iofix'],check=True,timeout=600)"
.\.venv\Scripts\python.exe -c "import subprocess,sys; subprocess.run([sys.executable,'run_warm_fixed_process.py','native20k'],check=True,timeout=600)"
.\.venv\Scripts\python.exe -c "import subprocess,sys; subprocess.run([sys.executable,'run_warm_fixed_process.py','adaptive20k'],check=True,timeout=600)"
.\.venv\Scripts\python.exe -c "import subprocess,sys; subprocess.run([sys.executable,'run_warm_fixed_process.py','adaptive30y_warm_fixed'],check=True,timeout=600)"
```

Always inspect RESULT.json: process exit0 is not sufficient; the numerical gate also requires no exception and ifail1. Physical validity does not follow from convergence. The baseline option without `_iofix` retains a known Windows temporary-file cleanup problem; it is preserved for provenance, not recommended as another research run. The unseeded adaptive30y case did not converge; the stored warm start did.

Windows shim only closes temporary output handles before unlink. Adaptive integration replaces the fatigue integrator at runtime without changing its constitutive law. The mission patch changes constraint90 to30-year duty from each point's actual cycle duration. Upstream source files remain untouched. The runner's runtime_shims list contains the I/O fix; the adaptive/mission interventions are identified separately by config flags and module hashes.

Exact SHA256 hashes of the four executed files:
- run_warm_fixed_process.py:3c65c901fbee719bad63e0e8a12ff48d2cc6b0674181ce27c43efda6cabe270e
- adaptive_fatigue.py:96be69c05abbfa9786591b652dac5c81262d7fb03c4a8fe3471fe42a5974949d
- windows_output_fix.py:b8f70409ce24ee9bda76e34b22e55289f60cb500697ebb2b445bea634ac0fdc7
- mission_constraint.py:d25a629240275457f24e0d3a27ff2a324e1a5100995cb31996f5104de57459db
- warm-start-overrides-corrected.txt:6afbd22b6d5863b6d094b5379117b96de8d51a9bc21669f93beaea3e247a9deb

The complete raw solver outputs, failed attempts, attempt-specific drivers, 18-test integration suite and public CSV are in the on-desktop evidence archive. They are not all copied into this repository directory. The user-facing compact download contains these exact files, the observed dependency lock, report and selected results; it excludes raw outputs/data. Results depend on empirical assumptions; fatigue is an active mathematical constraint with no newly validated engineering uncertainty margin. No same-design breeding/fuel-cycle closure is claimed. Preserve the UKAEA MIT license in UPSTREAM_LICENSE.txt for the used upstream implementation.
