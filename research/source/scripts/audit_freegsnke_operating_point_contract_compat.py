#!/usr/bin/env python3
"""Compatibility entry point for the FreeGSNKE operating-point contract.

The first preserved run showed that example05 contains multiple official cases
(diverted and limited). The contract concerns the first evolutive ``stepping``
case that generated the accepted example05 nonlinear baseline. This wrapper
retains only the exact notebook prefix through that solver constructor before
calling the unchanged contract logic.

The example05 pickle explicitly contains zero-valued passive-structure currents,
whereas example10 specifies only the 12 active coils and leaves passive currents
at their constructor defaults. For the active-current contract we therefore
compare the same ordered 12 labels, while separately requiring every explicit
example05 non-active entry to be exactly zero.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Mapping


_IMPL_PATH = Path(__file__).with_name(
    "audit_freegsnke_operating_point_contract.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "_fss_freegsnke_operating_point_contract_impl", _IMPL_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Unable to load operating-point contract: {_IMPL_PATH}")
_IMPL = importlib.util.module_from_spec(_SPEC)
# Python 3.10 dataclasses resolve postponed annotations through sys.modules
# while the class decorator executes. Register the dynamic module before
# executing it, exactly as the import machinery would for a normal import.
sys.modules[_SPEC.name] = _IMPL
_SPEC.loader.exec_module(_IMPL)


ACTIVE_COIL_LABELS = (
    "Solenoid",
    "PX",
    "D1",
    "D2",
    "D3",
    "Dp",
    "D5",
    "D6",
    "D7",
    "P4",
    "P5",
    "P6",
)

_EXAMPLE05_NON_ACTIVE_SUMMARY: dict[str, Any] | None = None
_ORIGINAL_SERIALIZABLE_CASE = _IMPL.serializable_case


def prefix_through_assigned_call(
    notebook: Any,
    *,
    target_name: str,
    function_suffix: str,
) -> Any:
    """Retain cells through the first requested constructor assignment."""
    retained: list[Any] = []
    found = False
    for cell in notebook.cells:
        retained.append(cell)
        if cell.get("cell_type") != "code":
            continue
        source = _IMPL.source_text(cell)
        tree = ast.parse(source)
        for statement in tree.body:
            if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                continue
            target = statement.targets[0]
            if (
                isinstance(target, ast.Name)
                and target.id == target_name
                and isinstance(statement.value, ast.Call)
                and _IMPL.call_name(statement.value.func).endswith(function_suffix)
            ):
                found = True
                break
        if found:
            break
    if not found:
        raise _IMPL.ContractError(
            f"could not locate {target_name}={function_suffix} constructor"
        )
    return _IMPL.nbformat.v4.new_notebook(
        cells=list(retained),
        metadata=dict(notebook.metadata),
    )


def active_currents_for_case(
    *,
    name: str,
    currents: Mapping[str, float],
) -> dict[str, float]:
    """Return one exact ordered active-current vector for both official cases."""
    global _EXAMPLE05_NON_ACTIVE_SUMMARY

    missing = [label for label in ACTIVE_COIL_LABELS if label not in currents]
    if missing:
        raise _IMPL.ContractError(
            f"{name} is missing frozen active-coil currents: {missing}"
        )

    if name == "example10_growth_rate_elongated":
        labels = tuple(currents.keys())
        if labels != ACTIVE_COIL_LABELS:
            raise _IMPL.ContractError(
                "example10 active-current label/order drift: "
                f"{labels!r} != {ACTIVE_COIL_LABELS!r}"
            )
    elif name == "example05_official_evolutive_diverted":
        non_active = {
            str(label): float(value)
            for label, value in currents.items()
            if label not in ACTIVE_COIL_LABELS
        }
        nonzero = {
            label: value for label, value in non_active.items() if value != 0.0
        }
        if nonzero:
            raise _IMPL.ContractError(
                "example05 contains non-zero passive initial currents: "
                f"{nonzero}"
            )
        canonical = json.dumps(
            non_active,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        _EXAMPLE05_NON_ACTIVE_SUMMARY = {
            "explicit_non_active_entry_count": len(non_active),
            "all_values_exactly_zero": True,
            "maximum_absolute_current_A": 0.0,
            "canonical_sha256": hashlib.sha256(canonical).hexdigest(),
            "comparison_interpretation": (
                "equivalent to example10 passive currents left at zero-valued "
                "constructor defaults"
            ),
        }
    else:
        raise _IMPL.ContractError(f"unrecognized frozen case: {name}")

    return {label: float(currents[label]) for label in ACTIVE_COIL_LABELS}


def parse_case(
    upstream: Path,
    *,
    name: str,
    notebook_relative: Path,
    solver_variable: str,
    currents: Mapping[str, float],
):
    notebook_path = upstream / notebook_relative
    notebook = _IMPL.nbformat.read(notebook_path, as_version=4)
    notebook = prefix_through_assigned_call(
        notebook,
        target_name=solver_variable,
        function_suffix="nonlinear_solve.nl_solver",
    )

    machine_kwargs, machine_source = _IMPL.assigned_call(
        notebook,
        target_name="tokamak",
        function_suffix="build_machine.tokamak",
    )
    equilibrium_kwargs, equilibrium_source = _IMPL.assigned_call(
        notebook,
        target_name="eq",
        function_suffix="equilibrium_update.Equilibrium",
    )
    profile_kwargs, profile_source = _IMPL.assigned_call(
        notebook,
        target_name="profiles",
        function_suffix="ConstrainPaxisIp",
    )
    solver_kwargs, solver_source = _IMPL.assigned_call(
        notebook,
        target_name=solver_variable,
        function_suffix="nonlinear_solve.nl_solver",
    )

    effective_solver = dict(_IMPL.SOLVER_DEFAULTS)
    for key, value in solver_kwargs.items():
        if key in effective_solver:
            effective_solver[key] = value

    setup_sources = "\n\0\n".join(
        (machine_source, equilibrium_source, profile_source, solver_source)
    )
    return _IMPL.ParsedCase(
        name=name,
        notebook=notebook_relative,
        notebook_sha256=_IMPL.sha256_file(notebook_path),
        machine=_IMPL.selected(machine_kwargs, _IMPL.MACHINE_ARGUMENTS),
        equilibrium=_IMPL.selected(
            equilibrium_kwargs, _IMPL.GRID_ARGUMENTS
        ),
        profile=_IMPL.selected(profile_kwargs, _IMPL.PROFILE_ARGUMENTS),
        solver_explicit={
            key: value
            for key, value in solver_kwargs.items()
            if key not in {"eq", "profiles", "GSStaticSolver"}
        },
        solver_effective=_IMPL.selected(
            effective_solver, _IMPL.CONTRACT_SOLVER_FIELDS
        ),
        active_currents_A=active_currents_for_case(
            name=name,
            currents=_IMPL.normalized_currents(currents),
        ),
        setup_source_sha256=hashlib.sha256(
            setup_sources.encode("utf-8")
        ).hexdigest(),
    )


def serializable_case(case: Any) -> dict[str, Any]:
    value = _ORIGINAL_SERIALIZABLE_CASE(case)
    if case.name == "example05_official_evolutive_diverted":
        if _EXAMPLE05_NON_ACTIVE_SUMMARY is None:
            raise _IMPL.ContractError(
                "example05 non-active-current summary was not produced"
            )
        value["non_active_initial_currents"] = dict(
            _EXAMPLE05_NON_ACTIVE_SUMMARY
        )
    elif case.name == "example10_growth_rate_elongated":
        value["non_active_initial_currents"] = {
            "explicit_non_active_entry_count": 0,
            "comparison_interpretation": (
                "passive currents are not assigned by the frozen prefix and "
                "remain at zero-valued constructor defaults"
            ),
        }
    return value


_IMPL.parse_case = parse_case
_IMPL.serializable_case = serializable_case


if __name__ == "__main__":
    raise SystemExit(_IMPL.main())
