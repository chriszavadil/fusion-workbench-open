#!/usr/bin/env python3
"""Inventory the exact OpenFUSIONToolkit 26.6 installation and DIII-D assets.

This script performs package/source discovery only. It does not reconstruct,
modify, or substitute for the official scientific example.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import re
import sys
from typing import Iterable

EXPECTED_VERSION = "26.6"
EXPECTED_SOURCE_COMMIT = "f3556a9e13298e646a00e1850c72211e185ed2c3"
PATTERNS = (
    re.compile(r"diii[-_d]?d", re.IGNORECASE),
    re.compile(r"g192185", re.IGNORECASE),
    re.compile(r"tokamaker.*diii", re.IGNORECASE),
    re.compile(r"doc_tmaker_diiid", re.IGNORECASE),
)
CANDIDATE_SUFFIXES = {
    ".h5", ".hdf5", ".geqdsk", ".eqdsk", ".gfile", ".ipynb",
    ".py", ".html", ".md", ".json", ".yaml", ".yml", "",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_candidates(root: Path) -> list[dict[str, object]]:
    if not root.exists():
        return []
    records: list[dict[str, object]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        if path.suffix.lower() not in CANDIDATE_SUFFIXES and not any(
            pattern.search(rel) for pattern in PATTERNS
        ):
            continue
        matched = any(pattern.search(rel) for pattern in PATTERNS)
        # Text search small source/document files even when the filename is generic.
        if not matched and path.stat().st_size <= 5_000_000 and path.suffix.lower() in {
            ".py", ".ipynb", ".html", ".md", ".json", ".yaml", ".yml"
        }:
            try:
                sample = path.read_text(errors="replace")
            except OSError:
                sample = ""
            matched = any(pattern.search(sample) for pattern in PATTERNS)
        if not matched:
            continue
        records.append(
            {
                "root": str(root),
                "relative_path": rel,
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return sorted(records, key=lambda item: str(item["relative_path"]))


def package_roots(module) -> list[Path]:
    roots: list[Path] = []
    module_file = getattr(module, "__file__", None)
    if module_file:
        roots.append(Path(module_file).resolve().parent)
    oft_root = os.environ.get("OFT_ROOTPATH")
    if oft_root:
        roots.append(Path(oft_root).resolve())
    # Preserve order while removing duplicates.
    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root)
        if key not in seen:
            unique.append(root)
            seen.add(key)
    return unique


def capture_runtime_banner() -> tuple[str, str | None]:
    try:
        from OpenFUSIONToolkit import OFT_env
    except Exception as exc:  # pragma: no cover - connected-run evidence
        return "", f"import failed: {type(exc).__name__}: {exc}"
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            env = OFT_env(nthreads=2)
        # Retain an object reference until after output capture.
        _ = env
        return buffer.getvalue(), None
    except Exception as exc:  # pragma: no cover - connected-run evidence
        return buffer.getvalue(), f"initialization failed: {type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--docs-page", type=Path, required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    version = importlib.metadata.version("OpenFUSIONToolkit")
    module = importlib.import_module("OpenFUSIONToolkit")
    roots = package_roots(module)
    runtime_banner, runtime_error = capture_runtime_banner()

    source_commit_file = args.source / ".git"
    source_commit = os.popen(
        f"git -C {args.source.resolve()} rev-parse HEAD"
    ).read().strip() if source_commit_file.exists() else None

    candidate_records: list[dict[str, object]] = []
    for root in [*roots, args.source.resolve()]:
        candidate_records.extend(safe_candidates(root))

    docs_text = args.docs_page.read_text(errors="replace")
    docs_findings = {
        "contains_mesh_name": "DIIID_mesh.h5" in docs_text,
        "contains_geqdsk_name": "g192185.02440" in docs_text,
        "contains_linear_call": "compute_linear_stability(5.E3,10,False)" in docs_text.replace(" ", ""),
        "mentions_807_per_s": bool(re.search(r"807\s*(?:s|1/s)", docs_text, re.IGNORECASE)),
        "mentions_945_98": "945.98" in docs_text or "9.4598E+02" in docs_text,
    }

    result = {
        "schema": "fusion-solution-set.tokamaker-v26.6-discovery.v1",
        "installed_version": version,
        "expected_version": EXPECTED_VERSION,
        "source_commit": source_commit,
        "expected_source_commit": EXPECTED_SOURCE_COMMIT,
        "wheel": {
            "path": str(args.wheel.resolve()),
            "size_bytes": args.wheel.stat().st_size,
            "sha256": sha256(args.wheel),
        },
        "docs_page": {
            "path": str(args.docs_page.resolve()),
            "size_bytes": args.docs_page.stat().st_size,
            "sha256": sha256(args.docs_page),
            "findings": docs_findings,
        },
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "package_roots": [str(root) for root in roots],
        "runtime_banner": runtime_banner,
        "runtime_error": runtime_error,
        "candidate_files": candidate_records,
        "candidate_file_count": len(candidate_records),
        "required_named_inputs_found": {
            "DIIID_mesh.h5": any(
                str(record["relative_path"]).endswith("DIIID_mesh.h5")
                for record in candidate_records
            ),
            "g192185.02440": any(
                str(record["relative_path"]).endswith("g192185.02440")
                for record in candidate_records
            ),
        },
        "passed_identity_gate": (
            version == EXPECTED_VERSION
            and source_commit == EXPECTED_SOURCE_COMMIT
            and runtime_error is None
        ),
        "ready_for_unchanged_example": (
            version == EXPECTED_VERSION
            and source_commit == EXPECTED_SOURCE_COMMIT
            and runtime_error is None
            and any(
                str(record["relative_path"]).endswith("DIIID_mesh.h5")
                for record in candidate_records
            )
            and any(
                str(record["relative_path"]).endswith("g192185.02440")
                for record in candidate_records
            )
        ),
        "claim_boundary": (
            "package/input discovery only; no equilibrium, stability, VDE, "
            "MAST-U, ITER, controller, or reactor claim"
        ),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["passed_identity_gate"]:
        raise SystemExit("TokaMaker v26.6 identity/import gate failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
