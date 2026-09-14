#!/usr/bin/env python3
"""Execute the frozen OpenFUSIONToolkit v26.6 DIII-D notebook unchanged.

The scientific notebook is never edited.  One audit-only cell is appended to a
copy after every original cell.  The checker uses the in-kernel full-precision
growth rate for the notebook's exact timestep identity; rounded printed text is
preserved separately as documentation evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import traceback
from pathlib import Path
from typing import Any

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

EXPECTED = {
    "notebook": (
        "src/examples/TokaMaker/DIIID/DIIID_baseline_ex.ipynb",
        "78180822cb975e403c396e78f280636acf927a7113c2bf0df3590b8b6dc2e439",
    ),
    "mesh": (
        "src/examples/TokaMaker/DIIID/DIIID_mesh.h5",
        "31c1c52cbd2f7bdedae74380a7a0a02426917179953544e7faea69606219001c",
    ),
    "geqdsk": (
        "src/examples/TokaMaker/DIIID/g192185.02440",
        "6f33a01935847f25aea6edc45e939268ab910570ea6e8adb87528056a77520d5",
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def parse_float(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def first_scalar(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        result = float(value)
        return result if math.isfinite(result) else None
    if isinstance(value, list) and value:
        return first_scalar(value[0])
    if isinstance(value, dict):
        sample = value.get("sample")
        if isinstance(sample, list) and sample:
            return first_scalar(sample[0])
    return None


AUDIT_CELL = r'''
# Fusion Solution Set audit-only cell. No upstream object is mutated.
import json as _fss_json
import math as _fss_math
import os as _fss_os
from pathlib import Path as _FssPath
import numpy as _fss_np

def _fss_jsonable(value, max_items=200):
    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, float) and not _fss_math.isfinite(value):
            return repr(value)
        return value
    if isinstance(value, _fss_np.generic):
        return _fss_jsonable(value.item(), max_items=max_items)
    if isinstance(value, dict):
        return {
            str(key): _fss_jsonable(item, max_items=max_items)
            for key, item in list(value.items())[:max_items]
        }
    if isinstance(value, (list, tuple)):
        return [_fss_jsonable(item, max_items=max_items) for item in value[:max_items]]
    try:
        array = _fss_np.asarray(value)
        if array.dtype != object:
            flat = array.reshape(-1)
            return {
                "type": type(value).__name__,
                "shape": list(array.shape),
                "dtype": str(array.dtype),
                "finite": bool(_fss_np.isfinite(array).all()) if array.size else True,
                "minimum": float(_fss_np.nanmin(array)) if array.size else None,
                "maximum": float(_fss_np.nanmax(array)) if array.size else None,
                "sample": [_fss_jsonable(item) for item in flat[:max_items]],
            }
    except Exception:
        pass
    try:
        length = len(value)
    except Exception:
        length = None
    return {"type": type(value).__name__, "length": length, "repr": repr(value)[:2000]}

_values = {
    "growth_rates": globals().get("growth_rates"),
    "times": globals().get("times"),
    "z_hist": globals().get("z_hist"),
    "eig_hist": globals().get("eig_hist"),
}
_payload = {
    "schema": "fusion-solution-set.tokamaker-diiid-audit.v2.1",
    "growth_rates": _fss_jsonable(_values["growth_rates"]),
    "dt": _fss_jsonable(globals().get("dt")),
    "times": _fss_jsonable(_values["times"]),
    "z_hist": _fss_jsonable(_values["z_hist"]),
    "eig_hist": _fss_jsonable(_values["eig_hist"]),
    "results_length": (
        len(globals().get("results"))
        if globals().get("results") is not None else None
    ),
    "mygs_type": (
        type(globals().get("mygs")).__module__ + "." + type(globals().get("mygs")).__name__
        if globals().get("mygs") is not None else None
    ),
    "working_directory": _fss_os.getcwd(),
}
_npz_path = _fss_os.environ.get("FSS_TOKAMAKER_AUDIT_NPZ")
_arrays = {}
for _name, _value in _values.items():
    try:
        _array = _fss_np.asarray(_value)
        if _array.dtype != object:
            _arrays[_name] = _array
    except Exception:
        pass
if _npz_path and _arrays:
    _FssPath(_npz_path).parent.mkdir(parents=True, exist_ok=True)
    _fss_np.savez_compressed(_npz_path, **_arrays)
    _payload["numeric_archive"] = _npz_path
else:
    _payload["numeric_archive"] = None
_json_path = _fss_os.environ.get("FSS_TOKAMAKER_AUDIT_JSON")
if _json_path:
    _FssPath(_json_path).parent.mkdir(parents=True, exist_ok=True)
    _FssPath(_json_path).write_text(
        _fss_json.dumps(_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
print("FSS_AUDIT_JSON_BEGIN")
print(_fss_json.dumps(_payload, indent=2, sort_keys=True))
print("FSS_AUDIT_JSON_END")
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, Any] = {
        "schema": "fusion-solution-set.tokamaker-diiid-execution.v2.1",
        "source_root": str(source),
        "success": False,
    }

    try:
        paths: dict[str, Path] = {}
        verified: dict[str, Any] = {}
        for name, (relative, expected_hash) in EXPECTED.items():
            path = source / relative
            if not path.is_file():
                raise FileNotFoundError(f"Missing frozen {name}: {path}")
            actual_hash = sha256_file(path)
            if actual_hash != expected_hash:
                raise RuntimeError(
                    f"{name} hash mismatch: expected {expected_hash}, got {actual_hash}"
                )
            paths[name] = path
            verified[name] = {
                "path": relative,
                "sha256": actual_hash,
                "size_bytes": path.stat().st_size,
            }
        evidence["verified_inputs"] = verified

        original = nbformat.read(paths["notebook"], as_version=4)
        original_count = len(original.cells)
        original_source_hash = source_digest(list(original.cells))
        executing = copy.deepcopy(original)
        executing.cells.append(nbformat.v4.new_code_cell(AUDIT_CELL))
        if source_digest(list(executing.cells[:-1])) != original_source_hash:
            raise RuntimeError("Original cell source changed before execution")

        audit_json = output / "audit_payload.json"
        audit_npz = output / "audit_numeric_arrays.npz"
        old_json = os.environ.get("FSS_TOKAMAKER_AUDIT_JSON")
        old_npz = os.environ.get("FSS_TOKAMAKER_AUDIT_NPZ")
        os.environ["FSS_TOKAMAKER_AUDIT_JSON"] = str(audit_json)
        os.environ["FSS_TOKAMAKER_AUDIT_NPZ"] = str(audit_npz)
        try:
            ExecutePreprocessor(
                timeout=args.timeout,
                kernel_name="python3",
                allow_errors=False,
                interrupt_on_timeout=True,
            ).preprocess(
                executing,
                {"metadata": {"path": str(paths["notebook"].parent)}},
            )
        finally:
            if old_json is None:
                os.environ.pop("FSS_TOKAMAKER_AUDIT_JSON", None)
            else:
                os.environ["FSS_TOKAMAKER_AUDIT_JSON"] = old_json
            if old_npz is None:
                os.environ.pop("FSS_TOKAMAKER_AUDIT_NPZ", None)
            else:
                os.environ["FSS_TOKAMAKER_AUDIT_NPZ"] = old_npz

        executed_path = output / "DIIID_baseline_ex.executed.ipynb"
        nbformat.write(executing, executed_path)
        if len(executing.cells) != original_count + 1:
            raise RuntimeError("Unexpected executed notebook cell count")
        executed_source_hash = source_digest(list(executing.cells[:-1]))
        if executed_source_hash != original_source_hash:
            raise RuntimeError("An original source cell changed during execution")

        text = output_text(executing)
        (output / "notebook_outputs.txt").write_text(text, encoding="utf-8")
        if not audit_json.is_file() or not audit_npz.is_file():
            raise RuntimeError("Audit outputs were not produced")
        audit = json.loads(audit_json.read_text(encoding="utf-8"))

        full_growth = first_scalar(audit.get("growth_rates"))
        printed_growth = parse_float(
            r"Growth\s+rate\s*=\s*([+\-0-9.eE]+)", text
        )
        printed_growth_time = parse_float(
            r"Growth\s+time\s*=\s*([+\-0-9.eE]+)", text
        )
        dt = first_scalar(audit.get("dt"))
        results_length = audit.get("results_length")
        if full_growth is None or full_growth <= 0.0:
            raise RuntimeError(f"Full-precision growth rate is not positive: {full_growth!r}")
        if dt is None:
            raise RuntimeError("Official timestep variable `dt` was not exposed")
        expected_dt = 0.1 / full_growth
        dt_error = abs(dt - expected_dt) / max(abs(expected_dt), 1e-300)
        if dt_error > 1e-12:
            raise RuntimeError(
                f"Timestep rule mismatch: dt={dt}, expected={expected_dt}, rel={dt_error}"
            )
        if not isinstance(results_length, int) or results_length < 41:
            raise RuntimeError(f"Time history shorter than 41: {results_length!r}")

        import numpy as np
        with np.load(audit_npz) as arrays:
            for required in ("growth_rates", "times", "z_hist", "eig_hist"):
                if required not in arrays:
                    raise RuntimeError(f"Missing numeric audit array: {required}")
                if not np.isfinite(arrays[required]).all():
                    raise RuntimeError(f"Nonfinite audit array: {required}")
            times = np.asarray(arrays["times"], dtype=float)
            z_hist = np.asarray(arrays["z_hist"], dtype=float)
            eig_hist = np.asarray(arrays["eig_hist"], dtype=float)
            if times.size < 41 or not np.all(np.diff(times) > 0.0):
                raise RuntimeError("Official time history is short or not increasing")
            if z_hist.shape[0] < 40 or z_hist.shape[1] < 2:
                raise RuntimeError(f"Unexpected z_hist shape: {z_hist.shape}")
            if eig_hist.shape[0] < 40 or eig_hist.shape[1] < 2:
                raise RuntimeError(f"Unexpected eig_hist shape: {eig_hist.shape}")

        evidence.update(
            {
                "success": True,
                "original_cell_count": original_count,
                "executed_cell_count": len(executing.cells),
                "original_cell_source_sha256": original_source_hash,
                "executed_original_cell_source_sha256": executed_source_hash,
                "dominant_growth_rate_full_precision_per_s": full_growth,
                "dominant_growth_rate_printed_per_s": printed_growth,
                "growth_time_printed_s": printed_growth_time,
                "growth_time_full_precision_s": 1.0 / full_growth,
                "official_timestep_s": dt,
                "expected_timestep_s": expected_dt,
                "timestep_relative_error": dt_error,
                "time_history_length": int(times.size),
                "time_history_final_s": float(times[-1]),
                "z_history_shape": list(z_hist.shape),
                "eigenmode_history_shape": list(eig_hist.shape),
                "documentation_prose_growth_rate_per_s": 807.0,
                "saved_notebook_growth_rate_per_s": 945.98,
                "executed_notebook_sha256": sha256_file(executed_path),
                "audit_payload_sha256": sha256_file(audit_json),
                "audit_numeric_archive_sha256": sha256_file(audit_npz),
            }
        )
    except Exception as exc:
        evidence["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        (output / "execution_summary.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n",
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
        print(json.dumps(evidence, indent=2, sort_keys=True))

    return 0 if evidence.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
