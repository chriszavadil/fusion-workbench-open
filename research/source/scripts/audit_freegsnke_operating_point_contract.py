#!/usr/bin/env python3
"""Classify whether two frozen FreeGSNKE examples share one operating point.

This is a fail-closed input contract. It does not execute either solver. Instead
it verifies the exact upstream commit and Git objects, parses the setup calls
from the pinned notebooks, loads the pinned example05 current file, and compares
the effective inputs that define the equilibrium and retained linear state.

A direct comparison is allowed only when every contract field is exactly equal.
Any mismatch routes later validation to a single matched operating point.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import pickle
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import nbformat


PINNED_COMMIT = "f776e908c8c333411f9824cbcfed674fafff8dfd"
EXAMPLE05 = Path("examples/example05 - evolutive_forward_solve.ipynb")
EXAMPLE10 = Path("examples/example10 - growth_rates.ipynb")
CURRENT_FILE = Path("examples/data/simple_diverted_currents_PaxisIp.pk")

EXPECTED_GIT_OBJECTS = {
    EXAMPLE05: "c0486a7ad742a3d1e6ec09c97dc2f775a922fb11",
    EXAMPLE10: "3e6e78ce9841635d4616a5c041adcfa9907fe9eb",
    CURRENT_FILE: "eae8a38d88303cd20604f0a18289b673ae7c5f49",
    Path("machine_configs/MAST-U/MAST-U_like_active_coils.pickle"):
        "8cc6d40f6f67b5035802feaedb075c349e168012",
    Path("machine_configs/MAST-U/MAST-U_like_passive_coils.pickle"):
        "6415a803c6ed96626512b763d478e0a2e1d4655a",
    Path("machine_configs/MAST-U/MAST-U_like_limiter.pickle"):
        "7be35bfb51507a6a633423a0c45f1c8ae6ee86f8",
    Path("machine_configs/MAST-U/MAST-U_like_wall.pickle"):
        "74c2c23d28ff8bef549eaf88701bbe69fde10fb6",
}

# Exact nl_solver defaults at the pinned v3.0.1 commit. We compare effective
# settings, not merely the explicit keyword text in each notebook.
SOLVER_DEFAULTS = {
    "full_timestep": 1.0e-4,
    "max_internal_timestep": 1.0e-4,
    "automatic_timestep": False,
    "plasma_resistivity": 1.0e-6,
    "plasma_norm_factor": 1.0e3,
    "blend_hatJ": 0,
    "max_mode_frequency": 1.0e2,
    "fix_n_vessel_modes": -1,
    "threshold_dIy_dI": 0.025,
    "min_dIy_dI": 0.01,
    "mode_removal": True,
    "linearize": True,
    "target_relative_tolerance_linearization": 1.0e-8,
    "target_dIy": 1.0e-3,
    "force_core_mask_linearization": False,
    "l2_reg": 1.0e-6,
    "collinearity_reg": 1.0e-6,
}

CONTRACT_SOLVER_FIELDS = (
    "full_timestep",
    "max_internal_timestep",
    "automatic_timestep",
    "plasma_resistivity",
    "plasma_norm_factor",
    "max_mode_frequency",
    "fix_n_vessel_modes",
    "threshold_dIy_dI",
    "min_dIy_dI",
    "mode_removal",
    "linearize",
    "target_relative_tolerance_linearization",
    "target_dIy",
    "force_core_mask_linearization",
)

MACHINE_ARGUMENTS = (
    "active_coils_path",
    "passive_coils_path",
    "limiter_path",
    "wall_path",
)

GRID_ARGUMENTS = ("Rmin", "Rmax", "Zmin", "Zmax", "nx", "ny")
PROFILE_ARGUMENTS = ("paxis", "Ip", "fvac", "alpha_m", "alpha_n")


class ContractError(RuntimeError):
    """Raised when a frozen notebook cannot be classified unambiguously."""


@dataclass(frozen=True)
class ParsedCase:
    name: str
    notebook: Path
    notebook_sha256: str
    machine: dict[str, Any]
    equilibrium: dict[str, Any]
    profile: dict[str, Any]
    solver_explicit: dict[str, Any]
    solver_effective: dict[str, Any]
    active_currents_A: dict[str, float]
    setup_source_sha256: str


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True
    ).strip()


def source_text(cell: Mapping[str, Any]) -> str:
    value = cell.get("source", "")
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    return str(value)


def code_cells(notebook: Any) -> Iterable[str]:
    for cell in notebook.cells:
        if cell.get("cell_type") == "code":
            yield source_text(cell)


def safe_literal(node: ast.AST) -> Any:
    """Evaluate only arithmetic/container literals used by the pinned notebooks."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp):
        value = safe_literal(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +value
        if isinstance(node.op, ast.USub):
            return -value
        raise ContractError(f"unsupported unary literal: {ast.dump(node)}")
    if isinstance(node, ast.BinOp):
        left = safe_literal(node.left)
        right = safe_literal(node.right)
        operators = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Div: lambda a, b: a / b,
            ast.FloorDiv: lambda a, b: a // b,
            ast.Pow: lambda a, b: a ** b,
            ast.Mod: lambda a, b: a % b,
        }
        fn = operators.get(type(node.op))
        if fn is None:
            raise ContractError(f"unsupported binary literal: {ast.dump(node)}")
        return fn(left, right)
    if isinstance(node, ast.List):
        return [safe_literal(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(safe_literal(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return {
            safe_literal(key): safe_literal(value)
            for key, value in zip(node.keys, node.values, strict=True)
        }
    if isinstance(node, ast.Name):
        if node.id == "True":
            return True
        if node.id == "False":
            return False
        if node.id == "None":
            return None
        # Object references are retained symbolically and excluded from numeric
        # comparisons unless a contract explicitly selects them.
        return {"$name": node.id}
    if isinstance(node, ast.JoinedStr):
        # Machine paths are f-strings without dynamic fields in these notebooks.
        pieces: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                pieces.append(value.value)
            else:
                raise ContractError(f"dynamic f-string is not frozen: {ast.dump(node)}")
        return "".join(pieces)
    raise ContractError(f"non-literal setup expression: {ast.dump(node)}")


def call_name(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def assigned_call(
    notebook: Any,
    *,
    target_name: str,
    function_suffix: str,
) -> tuple[dict[str, Any], str]:
    matches: list[tuple[dict[str, Any], str]] = []
    for source in code_cells(notebook):
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            raise ContractError(f"could not parse notebook cell: {exc}") from exc
        for statement in tree.body:
            if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                continue
            target = statement.targets[0]
            if not isinstance(target, ast.Name) or target.id != target_name:
                continue
            if not isinstance(statement.value, ast.Call):
                continue
            if not call_name(statement.value.func).endswith(function_suffix):
                continue
            kwargs: dict[str, Any] = {}
            for keyword in statement.value.keywords:
                if keyword.arg is None:
                    raise ContractError(
                        f"{target_name} uses **kwargs; contract cannot classify it"
                    )
                kwargs[keyword.arg] = safe_literal(keyword.value)
            matches.append((kwargs, source))
    if len(matches) != 1:
        raise ContractError(
            f"expected one {target_name}={function_suffix} call, found {len(matches)}"
        )
    return matches[0]


def assigned_literal(notebook: Any, target_name: str) -> tuple[Any, str]:
    matches: list[tuple[Any, str]] = []
    for source in code_cells(notebook):
        tree = ast.parse(source)
        for statement in tree.body:
            if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                continue
            target = statement.targets[0]
            if isinstance(target, ast.Name) and target.id == target_name:
                matches.append((safe_literal(statement.value), source))
    if len(matches) != 1:
        raise ContractError(
            f"expected one literal assignment to {target_name}, found {len(matches)}"
        )
    return matches[0]


def selected(mapping: Mapping[str, Any], names: Iterable[str]) -> dict[str, Any]:
    missing = [name for name in names if name not in mapping]
    if missing:
        raise ContractError(f"required setup arguments absent: {missing}")
    return {name: mapping[name] for name in names}


def normalized_currents(value: Any) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise ContractError("coil-current object is not a mapping")
    out = {str(key): float(item) for key, item in value.items()}
    if not out or not all(math.isfinite(item) for item in out.values()):
        raise ContractError("coil-current mapping is empty or non-finite")
    return out


def parse_case(
    upstream: Path,
    *,
    name: str,
    notebook_relative: Path,
    solver_variable: str,
    currents: Mapping[str, float],
) -> ParsedCase:
    notebook_path = upstream / notebook_relative
    notebook = nbformat.read(notebook_path, as_version=4)

    machine_kwargs, machine_source = assigned_call(
        notebook, target_name="tokamak", function_suffix="build_machine.tokamak"
    )
    equilibrium_kwargs, equilibrium_source = assigned_call(
        notebook,
        target_name="eq",
        function_suffix="equilibrium_update.Equilibrium",
    )
    profile_kwargs, profile_source = assigned_call(
        notebook,
        target_name="profiles",
        function_suffix="ConstrainPaxisIp",
    )
    solver_kwargs, solver_source = assigned_call(
        notebook,
        target_name=solver_variable,
        function_suffix="nonlinear_solve.nl_solver",
    )

    effective_solver = dict(SOLVER_DEFAULTS)
    for key, value in solver_kwargs.items():
        if key in effective_solver:
            effective_solver[key] = value

    setup_sources = "\n\0\n".join(
        (machine_source, equilibrium_source, profile_source, solver_source)
    )
    return ParsedCase(
        name=name,
        notebook=notebook_relative,
        notebook_sha256=sha256_file(notebook_path),
        machine=selected(machine_kwargs, MACHINE_ARGUMENTS),
        equilibrium=selected(equilibrium_kwargs, GRID_ARGUMENTS),
        profile=selected(profile_kwargs, PROFILE_ARGUMENTS),
        solver_explicit={
            key: value for key, value in solver_kwargs.items()
            if key not in {"eq", "profiles", "GSStaticSolver"}
        },
        solver_effective=selected(effective_solver, CONTRACT_SOLVER_FIELDS),
        active_currents_A=normalized_currents(currents),
        setup_source_sha256=hashlib.sha256(
            setup_sources.encode("utf-8")
        ).hexdigest(),
    )


def exact_equal(left: Any, right: Any) -> bool:
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return (
            tuple(left.keys()) == tuple(right.keys())
            and all(exact_equal(left[key], right[key]) for key in left)
        )
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(
            exact_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    if isinstance(left, (float, int)) and isinstance(right, (float, int)):
        return float(left) == float(right)
    return left == right


def current_difference(
    left: Mapping[str, float], right: Mapping[str, float]
) -> dict[str, Any]:
    labels_equal = tuple(left.keys()) == tuple(right.keys())
    labels = sorted(set(left) | set(right))
    records: list[dict[str, Any]] = []
    max_abs = 0.0
    max_rel = 0.0
    for label in labels:
        l_value = left.get(label)
        r_value = right.get(label)
        if l_value is None or r_value is None:
            records.append(
                {
                    "label": label,
                    "example05_A": l_value,
                    "example10_A": r_value,
                    "absolute_difference_A": None,
                    "relative_difference": None,
                }
            )
            continue
        delta = r_value - l_value
        rel = abs(delta) / max(abs(l_value), abs(r_value), 1.0)
        max_abs = max(max_abs, abs(delta))
        max_rel = max(max_rel, rel)
        records.append(
            {
                "label": label,
                "example05_A": l_value,
                "example10_A": r_value,
                "signed_difference_example10_minus_example05_A": delta,
                "absolute_difference_A": abs(delta),
                "relative_difference": rel,
            }
        )
    return {
        "labels_equal_and_ordered": labels_equal,
        "exact_values_equal": labels_equal and exact_equal(left, right),
        "max_absolute_difference_A": max_abs,
        "max_relative_difference": max_rel,
        "records": records,
    }


def serializable_case(case: ParsedCase) -> dict[str, Any]:
    return {
        "name": case.name,
        "notebook": str(case.notebook),
        "notebook_sha256": case.notebook_sha256,
        "machine": case.machine,
        "equilibrium": case.equilibrium,
        "profile": case.profile,
        "solver_explicit": case.solver_explicit,
        "solver_effective": case.solver_effective,
        "active_currents_A": case.active_currents_A,
        "setup_source_sha256": case.setup_source_sha256,
    }


def markdown_report(report: Mapping[str, Any]) -> str:
    checks = report["checks"]
    decision = report["decision"]
    current_metrics = report["current_difference"]
    direct = decision["direct_example10_linear_vs_example05_nonlinear_allowed"]
    lines = [
        "# FreeGSNKE operating-point contract",
        "",
        f"Classification: **{decision['classification']}**",
        "",
        "## Exact checks",
        "",
    ]
    for name, value in checks.items():
        lines.append(f"- `{name}`: `{str(value).lower()}`")
    lines.extend(
        [
            "",
            "## Active-current difference",
            "",
            (
                "- Maximum absolute difference: "
                f"`{current_metrics['max_absolute_difference_A']:.12g} A`"
            ),
            (
                "- Maximum relative difference: "
                f"`{current_metrics['max_relative_difference']:.12g}`"
            ),
            "",
            "## Decision",
            "",
            (
                "- Direct use of the example10 151-state export against the "
                f"example05 nonlinear history: `{str(direct).lower()}`"
            ),
            f"- Required matched route: `{decision['required_matched_route']}`",
            "",
            "## Claim boundary",
            "",
            (
                "This contract classifies source-defined operating points only. "
                "It is not a nonlinear accuracy result, controller result, "
                "experimental MAST-U validation, ITER prediction, reactor-safety "
                "evidence, or sustainable-fusion evidence."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    upstream = args.upstream.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    head = git_output(upstream, "rev-parse", "HEAD")
    if head != PINNED_COMMIT:
        raise ContractError(f"FreeGSNKE commit mismatch: {head} != {PINNED_COMMIT}")

    identities: dict[str, Any] = {}
    for relative, expected_blob in EXPECTED_GIT_OBJECTS.items():
        path = upstream / relative
        if not path.is_file():
            raise ContractError(f"missing frozen input: {relative}")
        actual_blob = git_output(upstream, "hash-object", str(relative))
        if actual_blob != expected_blob:
            raise ContractError(
                f"Git object mismatch for {relative}: {actual_blob} != {expected_blob}"
            )
        identities[str(relative)] = {
            "git_blob_sha1": actual_blob,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }

    with (upstream / CURRENT_FILE).open("rb") as handle:
        example05_currents = normalized_currents(pickle.load(handle))

    example10_notebook = nbformat.read(upstream / EXAMPLE10, as_version=4)
    example10_currents_raw, _ = assigned_literal(
        example10_notebook, "current_values"
    )
    example10_currents = normalized_currents(example10_currents_raw)

    example05 = parse_case(
        upstream,
        name="example05_official_evolutive_diverted",
        notebook_relative=EXAMPLE05,
        solver_variable="stepping",
        currents=example05_currents,
    )
    example10 = parse_case(
        upstream,
        name="example10_growth_rate_elongated",
        notebook_relative=EXAMPLE10,
        solver_variable="nonlinear_solver",
        currents=example10_currents,
    )

    current_metrics = current_difference(
        example05.active_currents_A, example10.active_currents_A
    )
    checks = {
        "source_commit_equal": True,
        "machine_configuration_equal": exact_equal(
            example05.machine, example10.machine
        ),
        "equilibrium_grid_equal": exact_equal(
            example05.equilibrium, example10.equilibrium
        ),
        "profile_parameters_equal": exact_equal(
            example05.profile, example10.profile
        ),
        "active_coil_labels_and_order_equal":
            current_metrics["labels_equal_and_ordered"],
        "active_coil_currents_exactly_equal":
            current_metrics["exact_values_equal"],
        "solver_and_mode_policy_exactly_equal": exact_equal(
            example05.solver_effective, example10.solver_effective
        ),
    }
    direct_allowed = all(checks.values())
    if direct_allowed:
        classification = "same_frozen_operating_point"
        route = "direct_cross_case_comparison_permitted"
    else:
        classification = "different_frozen_operating_points"
        route = (
            "execute_linear_and_nonlinear_rollouts_from_the_exact_example10_"
            "prefix_and_151_state_basis"
        )

    report = {
        "schema": "fusion-solution-set.freegsnke-operating-point-contract.v1",
        "freegsnke_commit": head,
        "source_identity_verified": True,
        "input_identities": identities,
        "cases": {
            "example05": serializable_case(example05),
            "example10": serializable_case(example10),
        },
        "checks": checks,
        "current_difference": current_metrics,
        "decision": {
            "classification": classification,
            "direct_example10_linear_vs_example05_nonlinear_allowed":
                direct_allowed,
            "required_matched_route": route,
            "reason": (
                "Every machine, equilibrium, profile, active-current, and "
                "state-basis-defining field must be exactly equal before a "
                "linear/nonlinear model-error claim is allowed."
            ),
        },
        "claim_boundary": (
            "source-defined operating-point classification only; not nonlinear "
            "accuracy, controller recovery, experimental validation, ITER "
            "performance, reactor safety, or sustainable fusion"
        ),
    }

    json_path = output / "freegsnke-operating-point-contract.json"
    markdown_path = output / "freegsnke-operating-point-contract.md"
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    manifest = [
        f"{sha256_file(json_path)}  {json_path.name}",
        f"{sha256_file(markdown_path)}  {markdown_path.name}",
    ]
    (output / "evidence-sha256.txt").write_text(
        "\n".join(manifest) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
