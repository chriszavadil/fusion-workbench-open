# Reproduce the local header neutron-transport study

This is a scoped computational design comparison, not a whole-reactor breeding result. Read RESEARCH_CONTEXT.md and the dated result report before interpreting it. The original driver refuses to overwrite prior runs.

## Replay the published arithmetic
In the experiment folder, install a compatible NumPy version and run `python analyze_transport.py`. The six saved `candidate_runs/*/RESULT.json`, metadata and tally-definition XML files are sufficient to reconstruct the averaged tallies, independent-run errors and admitted contrasts without another neutron run. Compare the generated object with KEY_RESULTS.json. This is arithmetic replay, not an independent transport solver.

The full local evidence archive additionally contains the six OpenMC statepoints, benchmark statepoint and execution logs. `python -m pytest -q test_transport_results.py` checks statepoint hashes and therefore needs that full archive. The graphical app reads only reviewed result projections and does not execute these scripts when a report is opened.

## Repeat neutron transport
Use a fresh separate directory with OpenMC 0.15.2 and the Python versions recorded in ENVIRONMENT.json. The original computation used an isolated Linux environment and two OpenMP threads; it did not install global packages or modify other projects. Copy the original scripts, FROZEN_INPUT.json and the reference subset preserving its relative directory names. Do not copy candidate_runs or reference_run into the fresh execution directory.

Provide the ENDFB-8.0-NNDC neutron and photon files named in DATA_MANIFEST.json. Verify their individual SHA-256 digests and save a local `local_cross_sections_path.txt` containing the absolute path of a valid OpenMC `cross_sections.xml`. This local configuration file is deliberately excluded from the shareable source. The local XML digest in DATA_MANIFEST can differ after changing its absolute file paths; individual nuclear-data file hashes must match. Nuclear data are not bundled into the app.

Run `python run_reference.py` to reproduce the untouched public OKTAVIAN-Al source/geometry/tallies with the disclosed histories, seed and thread changes. Reference code and archived computational spectra are supplied under the original repository MIT notice. Their presence is not experimental validation of the candidate's lithium/beryllium materials. The model's historical docstring mentions tungsten, but its path, actual aluminum materials and archived output define the aluminum case we used.

Run `python geometry_checks.py` to verify analytic volumes, per-nuclide inventories, representative point coverage and temperature brackets. Then run `python run_local_transport.py`. It writes a frozen run admission and executes the six specified independent streams with a 600-second timeout per run. A timeout or failed run must stay a failure; do not silently increase histories or change the geometry and retain the original experiment label.

Run `python analyze_transport.py` and the tests after all admitted runs complete. Geometry, material, source and nuclear-data uncertainties are not included in the quoted Monte Carlo standard errors. No experimental correction factor is fitted.

## Preserved execution issues
The initial isolated-environment setup required a dependency-resolution retry. The reference transport itself completed, but the first postprocessor encountered a pandas 3 compatibility error in OpenMC's DataFrame formatter; direct tally arrays were used instead, without changing or repeating the transport. A separate NumPy-scalar serialization issue was corrected before candidate execution. OpenMC Python emitted recycled-object Filter ID warnings while constructing layouts; exported tally IDs are unique and checked. These are software issues, not successful physics validations. Original local diagnostic logs are retained privately.

No model parameter or source distribution was tuned after examining candidate results. The front-header arrangement is an admitted stress case. The three layouts carry the same nuclide inventories and boundary conditions.
