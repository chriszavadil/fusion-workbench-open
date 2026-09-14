#!/usr/bin/env python3
"""Execute the unchanged setup prefix of FreeGSNKE's growth-rate notebook.

The source notebook is never edited on disk. We retain every upstream cell
through the first construction of ``nonlinear_solver`` and append one audit-only
cell that exports the resulting matrices through our strict adapter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

import nbformat
from nbclient import NotebookClient

PINNED_COMMIT = "f776e908c8c333411f9824cbcfed674fafff8dfd"
NOTEBOOK_RELATIVE = Path("examples/example10 - growth_rates.ipynb")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()


def geometry_hashes(upstream: Path) -> dict[str, str]:
    base = upstream / "machine_configs/MAST-U"
    files = {
        "active_coils_sha256": base / "MAST-U_like_active_coils.pickle",
        "passive_coils_sha256": base / "MAST-U_like_passive_coils.pickle",
        "limiter_sha256": base / "MAST-U_like_limiter.pickle",
        "wall_sha256": base / "MAST-U_like_wall.pickle",
    }
    return {name: sha256(path) for name, path in files.items()}


def retained_prefix(notebook):
    target_index = None
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code" and "nonlinear_solver = nonlinear_solve.nl_solver(" in cell.source:
            target_index = index
            break
    if target_index is None:
        raise RuntimeError("could not locate the first nonlinear_solver construction")
    return notebook.cells[: target_index + 1], target_index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, default=Path("vendor/freegsnke"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/freegsnke-v3.0.1"))
    args = parser.parse_args()

    upstream = args.upstream.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    head = git_head(upstream)
    if head != PINNED_COMMIT:
        raise RuntimeError(f"FreeGSNKE commit mismatch: {head} != {PINNED_COMMIT}")

    notebook_path = upstream / NOTEBOOK_RELATIVE
    notebook_hash = sha256(notebook_path)
    original = nbformat.read(notebook_path, as_version=4)
    cells, target_index = retained_prefix(original)

    audit_metadata = {
        "freegsnke_commit": head,
        "freegsnke_tag": "v3.0.1",
        "source_notebook": str(NOTEBOOK_RELATIVE),
        "source_notebook_sha256": notebook_hash,
        "executed_upstream_cell_count": len(cells),
        "first_linearization_cell_index": target_index,
        "execution_kind": "unchanged_upstream_prefix_plus_audit_export_cell",
        "machine_configuration_scope": "MAST-U-like public FreeGSNKE configuration",
        "experimental_shot_provenance": None,
        **geometry_hashes(upstream),
    }

    export_code = f"""
from fusion_vertical_safety.freegsnke_adapter import export_freegsnke_linearization
import json as _json
from pathlib import Path as _Path
_audit_metadata = _json.loads({json.dumps(json.dumps(audit_metadata))})
_export_dir = _Path({json.dumps(str(output))})
export_freegsnke_linearization(
    nonlinear_solver,
    _export_dir,
    extra_metadata=_audit_metadata,
)
"""
    notebook = nbformat.v4.new_notebook(
        metadata=original.metadata,
        cells=[*cells, nbformat.v4.new_code_cell(export_code)],
    )

    executed_path = output / "example10-growth-rates-prefix-executed.ipynb"
    old_cwd = Path.cwd()
    try:
        os.chdir(notebook_path.parent)
        client = NotebookClient(
            notebook,
            timeout=7200,
            kernel_name="python3",
            allow_errors=False,
            resources={"metadata": {"path": str(notebook_path.parent)}},
        )
        client.execute()
    finally:
        os.chdir(old_cwd)
    nbformat.write(notebook, executed_path)

    run_record = {
        **audit_metadata,
        "executed_notebook_sha256": sha256(executed_path),
    }
    (output / "run_record.json").write_text(
        json.dumps(run_record, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(run_record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
