# Independent-circuit reference comparison

This is a portable replay of a finite operating-point thermodynamic comparison. It is NOT a full Modelica/GETTHEM or PROCESS simulation, a compressor map, an installed cooling system, a neutron result or a new power-plant output.

Files: `DECISION.md` records the decision and qualifications; `ADMISSION.json` and `FROZEN_INPUT.json` preserve inputs; `RESULT.json` stores all four loop comparisons; `EFFICIENCY_RESULT.json` stores the explicitly adaptive follow-on; `MANIFEST.json` preserves exact file hashes; `test_circuits.py` and `replay.py` verify the implementation.

Run in an isolated Python environment (the observed execution used Python 3.10.8):

```text
python -m venv .venv
# Activate this environment using the command appropriate to your OS.
python -m pip install -r requirements.txt
python replay.py
```

The replay needs neither the larger desktop state nor PROCESS nor internet once the dependencies are installed. It verifies archived hashes, works in a temporary copy, replays all saved thermodynamic states, and executes the focused tests. `REPLAY_RESULT.json` identifies the temporary output directory. `compare_circuits.py` also preserves the original full-state calculation entry point, which expects the sibling desktop folders named in its source; it is not needed for portable replay.

Prescribed regional flows and inherited channel drops remain assumptions of the candidate comparison. Independent control prevents the particular cross-region flow competition from the preceding diagnostic, not every possible intra-region hot spot. Reduced compressor electricity is offset by reduced recovered heat. Do not add the reported net budget to the 213.69 MW conditional reactor result. Added loss, auxiliary power, hardware space and changed efficiencies must be charged against all relevant budgets together.

The cited article and full third-party Modelica source are deliberately excluded. Only their identifiers, reading scope and hashes are stored. The Python implementation is an original adapter of the published thermodynamic equations, not an exported Modelica application. Base-library source was inspected at the specified commit; the 2016 application was not reproduced.
