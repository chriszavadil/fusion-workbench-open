#!/usr/bin/env python3
"""Execute FreeGSNKE v3.0.1 example05 unchanged and export numeric histories."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import subprocess
import traceback
from pathlib import Path
from typing import Any

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

PINNED_COMMIT = "f776e908c8c333411f9824cbcfed674fafff8dfd"
NOTEBOOK = Path("examples/example05 - evolutive_forward_solve.ipynb")
EXPECTED_GIT_OBJECTS = {
    NOTEBOOK: "c0486a7ad742a3d1e6ec09c97dc2f775a922fb11",
    Path("examples/data/simple_diverted_currents_PaxisIp.pk"): "eae8a38d88303cd20604f0a18289b673ae7c5f49",
    Path("examples/data/simple_limited_currents_PaxisIp.pk"): "148f88ae4a5d88c8e85a7eddaf28aa9c8268d992",
    Path("machine_configs/MAST-U/MAST-U_like_active_coils.pickle"): "8cc6d40f6f67b5035802feaedb075c349e168012",
    Path("machine_configs/MAST-U/MAST-U_like_passive_coils.pickle"): "6415a803c6ed96626512b763d478e0a2e1d4655a",
    Path("machine_configs/MAST-U/MAST-U_like_limiter.pickle"): "7be35bfb51507a6a633423a0c45f1c8ae6ee86f8",
    Path("machine_configs/MAST-U/MAST-U_like_wall.pickle"): "74c2c23d28ff8bef549eaf88701bbe69fde10fb6",
}
REQUIRED_ARRAYS = (
    "history_times",
    "history_currents",
    "history_o_points",
    "history_elongation",
    "history_triangularity",
    "history_squareness",
    "history_area",
    "history_length",
    "history_times_nl",
    "history_currents_nl",
    "history_o_points_nl",
    "history_elongation_nl",
    "history_triangularity_nl",
    "history_squareness_nl",
    "history_area_nl",
    "history_length_nl",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True
    ).strip()


def source_text(cell: Any) -> str:
    value = cell.get("source", "")
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    return str(value)


def source_digest(cells: list[Any]) -> str:
    digest = hashlib.sha256()
    for cell in cells:
        digest.update(str(cell.get("cell_type", "")).encode("utf-8"))
        digest.update(b"\0")
        digest.update(source_text(cell).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def output_text(notebook: Any) -> str:
    chunks: list[str] = []
    for cell in notebook.cells:
        for output in cell.get("outputs", []):
            if "text" in output:
                value = output["text"]
                chunks.append("".join(value) if isinstance(value, list) else str(value))
            value = output.get("data", {}).get("text/plain")
            if value is not None:
                chunks.append("".join(value) if isinstance(value, list) else str(value))
            if output.get("ename"):
                chunks.append(
                    f"{output.get('ename')}: {output.get('evalue', '')}\n"
                    + "\n".join(output.get("traceback", []))
                )
    return "\n".join(chunks)


AUDIT_CELL = r'''
# Fusion Solution Set audit-only cell. Original upstream state is read, not changed.
import json as _fss_json
import os as _fss_os
from pathlib import Path as _FssPath
import numpy as _fss_np

_names = [
    "history_times", "history_currents", "history_o_points",
    "history_elongation", "history_triangularity", "history_squareness",
    "history_area", "history_length", "history_times_nl",
    "history_currents_nl", "history_o_points_nl", "history_elongation_nl",
    "history_triangularity_nl", "history_squareness_nl", "history_area_nl",
    "history_length_nl",
]
_arrays = {}
_summary = {}
for _name in _names:
    _value = globals().get(_name)
    if _value is None:
        _summary[_name] = {"present": False}
        continue
    try:
        _array = _fss_np.asarray(_value)
        if _array.dtype == object:
            raise TypeError("object dtype")
        _arrays[_name] = _array
        _summary[_name] = {
            "present": True,
            "shape": list(_array.shape),
            "dtype": str(_array.dtype),
            "finite": bool(_fss_np.isfinite(_array).all()),
            "minimum": float(_fss_np.nanmin(_array)) if _array.size else None,
            "maximum": float(_fss_np.nanmax(_array)) if _array.size else None,
        }
    except Exception as _exc:
        _summary[_name] = {
            "present": True,
            "numeric": False,
            "type": type(_value).__name__,
            "length": len(_value) if hasattr(_value, "__len__") else None,
            "error": repr(_exc),
        }

_stepping = globals().get("stepping")
_payload = {
    "schema": "fusion-solution-set.freegsnke-example05-audit.v1",
    "arrays": _summary,
    "max_count": globals().get("max_count"),
    "counter": globals().get("counter"),
    "t": globals().get("t"),
    "stepping_type": (
        type(_stepping).__module__ + "." + type(_stepping).__name__
        if _stepping is not None else None
    ),
    "dt_step": float(_stepping.dt_step) if _stepping is not None else None,
    "plasma_norm_factor": (
        float(_stepping.plasma_norm_factor)
        if _stepping is not None and hasattr(_stepping, "plasma_norm_factor") else None
    ),
    "state_dimension": (
        int(_fss_np.asarray(_stepping.currents_vec).size)
        if _stepping is not None and hasattr(_stepping, "currents_vec") else None
    ),
    "working_directory": _fss_os.getcwd(),
}
_json_path = _FssPath(_fss_os.environ["FSS_FREEGSNKE_EXAMPLE05_AUDIT_JSON"])
_npz_path = _FssPath(_fss_os.environ["FSS_FREEGSNKE_EXAMPLE05_AUDIT_NPZ"])
_json_path.parent.mkdir(parents=True, exist_ok=True)
_npz_path.parent.mkdir(parents=True, exist_ok=True)
_json_path.write_text(_fss_json.dumps(_payload, indent=2, sort_keys=True) + "\n")
_fss_np.savez_compressed(_npz_path, **_arrays)
print("FSS_EXAMPLE05_AUDIT_BEGIN")
print(_fss_json.dumps(_payload, indent=2, sort_keys=True))
print("FSS_EXAMPLE05_AUDIT_END")
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=10800)
    args = parser.parse_args()

    upstream = args.upstream.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "schema": "fusion-solution-set.freegsnke-example05-execution.v1",
        "success": False,
        "upstream": str(upstream),
    }

    try:
        head = git_output(upstream, "rev-parse", "HEAD")
        if head != PINNED_COMMIT:
            raise RuntimeError(f"commit mismatch: {head} != {PINNED_COMMIT}")
        result["freegsnke_commit"] = head

        identities: dict[str, Any] = {}
        for relative, expected_blob in EXPECTED_GIT_OBJECTS.items():
            path = upstream / relative
            if not path.is_file():
                raise FileNotFoundError(path)
            actual_blob = git_output(upstream, "hash-object", str(relative))
            if actual_blob != expected_blob:
                raise RuntimeError(
                    f"git object mismatch for {relative}: {actual_blob} != {expected_blob}"
                )
            identities[str(relative)] = {
                "git_blob_sha1": actual_blob,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        result["input_identities"] = identities

        notebook_path = upstream / NOTEBOOK
        original = nbformat.read(notebook_path, as_version=4)
        original_count = len(original.cells)
        original_source_hash = source_digest(list(original.cells))
        executing = copy.deepcopy(original)
        executing.cells.append(nbformat.v4.new_code_cell(AUDIT_CELL))
        if source_digest(list(executing.cells[:-1])) != original_source_hash:
            raise RuntimeError("original source changed before execution")

        audit_json = output / "audit_payload.json"
        audit_npz = output / "audit_histories.npz"
        old_json = os.environ.get("FSS_FREEGSNKE_EXAMPLE05_AUDIT_JSON")
        old_npz = os.environ.get("FSS_FREEGSNKE_EXAMPLE05_AUDIT_NPZ")
        os.environ["FSS_FREEGSNKE_EXAMPLE05_AUDIT_JSON"] = str(audit_json)
        os.environ["FSS_FREEGSNKE_EXAMPLE05_AUDIT_NPZ"] = str(audit_npz)
        try:
            ExecutePreprocessor(
                timeout=args.timeout,
                kernel_name="python3",
                allow_errors=False,
                interrupt_on_timeout=True,
            ).preprocess(
                executing,
                {"metadata": {"path": str(notebook_path.parent)}},
            )
        finally:
            if old_json is None:
                os.environ.pop("FSS_FREEGSNKE_EXAMPLE05_AUDIT_JSON", None)
            else:
                os.environ["FSS_FREEGSNKE_EXAMPLE05_AUDIT_JSON"] = old_json
            if old_npz is None:
                os.environ.pop("FSS_FREEGSNKE_EXAMPLE05_AUDIT_NPZ", None)
            else:
                os.environ["FSS_FREEGSNKE_EXAMPLE05_AUDIT_NPZ"] = old_npz

        executed_path = output / "example05-evolutive-forward-solve.executed.ipynb"
        nbformat.write(executing, executed_path)
        executed_source_hash = source_digest(list(executing.cells[:-1]))
        if len(executing.cells) != original_count + 1:
            raise RuntimeError("unexpected executed notebook cell count")
        if executed_source_hash != original_source_hash:
            raise RuntimeError("an original source cell changed during execution")
        (output / "notebook_outputs.txt").write_text(
            output_text(executing), encoding="utf-8"
        )

        if not audit_json.is_file() or not audit_npz.is_file():
            raise RuntimeError("audit outputs missing")
        audit = json.loads(audit_json.read_text(encoding="utf-8"))
        arrays = audit.get("arrays", {})
        missing = [name for name in REQUIRED_ARRAYS if not arrays.get(name, {}).get("present")]
        nonfinite = [
            name for name in REQUIRED_ARRAYS
            if arrays.get(name, {}).get("present") and not arrays.get(name, {}).get("finite", False)
        ]
        if missing:
            raise RuntimeError(f"required histories missing: {missing}")
        if nonfinite:
            raise RuntimeError(f"required histories nonnumeric or nonfinite: {nonfinite}")

        with __import__("numpy").load(audit_npz) as npz:
            import numpy as np
            linear_t = np.asarray(npz["history_times"], dtype=float)
            nonlinear_t = np.asarray(npz["history_times_nl"], dtype=float)
            if linear_t.size < 51 or nonlinear_t.size < 51:
                raise RuntimeError(
                    f"short histories: linear={linear_t.size}, nonlinear={nonlinear_t.size}"
                )
            if not np.all(np.diff(linear_t) > 0.0):
                raise RuntimeError("linear time array is not strictly increasing")
            if not np.all(np.diff(nonlinear_t) > 0.0):
                raise RuntimeError("nonlinear time array is not strictly increasing")

        result.update(
            {
                "success": True,
                "original_cell_count": original_count,
                "executed_cell_count": len(executing.cells),
                "original_cell_source_sha256": original_source_hash,
                "executed_original_cell_source_sha256": executed_source_hash,
                "linear_history_length": int(linear_t.size),
                "nonlinear_history_length": int(nonlinear_t.size),
                "linear_final_time_s": float(linear_t[-1]),
                "nonlinear_final_time_s": float(nonlinear_t[-1]),
                "state_dimension": audit.get("state_dimension"),
                "dt_step_s": audit.get("dt_step"),
                "executed_notebook_sha256": sha256_file(executed_path),
                "audit_payload_sha256": sha256_file(audit_json),
                "audit_histories_sha256": sha256_file(audit_npz),
            }
        )
    except Exception as exc:
        result["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        (output / "execution_summary.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest: list[str] = []
        for path in sorted(
            p for p in output.rglob("*")
            if p.is_file() and p.name != "evidence-sha256.txt"
        ):
            manifest.append(f"{sha256_file(path)}  {path.relative_to(output)}")
        (output / "evidence-sha256.txt").write_text(
            "\n".join(manifest) + ("\n" if manifest else ""),
            encoding="utf-8",
        )
        print(json.dumps(result, indent=2, sort_keys=True))

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
