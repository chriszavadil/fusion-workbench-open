# Reproduce the plasma-to-local-module source coupling

Read the dated source-coupling report in Research library before interpreting the numbers. The source is a parameterized direct-view proxy, not a measured magnetic equilibrium or whole-reactor transport model.

## Arithmetic and source checks
In a separate copy of this experiment directory, with compatible NumPy and SciPy installed, run `python analyze_coupling.py`. The saved RESULT.json, GEOMETRY.json and TRACKS.json projections under `runs` reconstruct the averaged scores, conditional uncertainty and contrast without new neutron histories. Compare the generated KEY_RESULTS.json and NEW_CASES.json with the published reference and app packet. This is numerical replay, not an independent transport validation.

Run `python -m pytest -q test_source_interface.py` to check the known solid-angle kernel, geometric quadrature, visibility refinement and the two included sampled NPZ source banks. The additional `test_coupled_results.py` verifies original HDF5 statepoint digests and requires the separate full local evidence archive. The application's tests include projection-only checks that do not need private logs or the nuclear-data installation.

## Repeat transport
Use OpenMC 0.15.2 and the same individual nuclear-data files recorded in the prior header study's DATA_MANIFEST.json. The baseline model/material files and FROZEN_INPUT are unchanged. The sampler uses PROCESS-emitted profile arrays preserved in PLASMA_SOURCE.json, not an arbitrary hand-selected angular distribution.

In a fresh directory without `runs`, retain the two source_banks/bank*.npz files but omit bank*.h5. Create a local `local_cross_sections_path.txt` containing a valid OpenMC cross_sections.xml path. Then `python run_coupled_transport.py` writes the corresponding HDF5 banks, freezes its admission, and executes the four declared 200,000-history cases. It refuses to overwrite previous source banks or runs. Follow with `python analyze_coupling.py` and the tests. Each run has its original two-thread, 600-second limit.

To regenerate the sampled source, use a separate copy without `source_banks`, then run `python make_surface_source.py`. This reads the preserved profiles and performs the eight declared Sobol scrambles, visibility checks and finite-bank resampling. Source-generation and finite-bank variation are not interchangeable with the OpenMC transport standard errors.

The archived `export_plasma.py` documents the actual original workstation layout and approved-input reproduction. It assumes the original project folders relative to its root; it is not a general installation script. A fresh full-profile reproduction requires the same pinned PROCESS source and runtime modules from the approved workbench SOLVER_MANIFEST, and must compare its input hash and exported profile quantities. The saved profiles remain the exact source of the present experiment.

Private execution logs and absolute local path configuration are not in this shareable experiment. No nuclear-data libraries, engine source, credentials or private Git history are included. No output from this local study should be relabeled as global tritium breeding or demonstrated electricity generation.
