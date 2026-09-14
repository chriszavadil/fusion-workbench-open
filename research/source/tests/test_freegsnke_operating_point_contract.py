from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys

import nbformat


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "audit_freegsnke_operating_point_contract.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "audit_freegsnke_operating_point_contract", MODULE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_safe_literal_supports_frozen_arithmetic_and_symbolic_references():
    module = load_module()
    assert module.safe_literal(ast.parse("10**2.5", mode="eval").body) == 10**2.5
    assert module.safe_literal(ast.parse("-1e-3", mode="eval").body) == -1e-3
    assert module.safe_literal(ast.parse("eq", mode="eval").body) == {"$name": "eq"}


def test_assigned_call_parses_literal_keywords_without_executing_code():
    module = load_module()
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell(
                "solver = nonlinear_solve.nl_solver("
                "eq=eq, profiles=profiles, full_timestep=5e-4, "
                "max_mode_frequency=10**2.5)"
            )
        ]
    )
    kwargs, _ = module.assigned_call(
        notebook,
        target_name="solver",
        function_suffix="nonlinear_solve.nl_solver",
    )
    assert kwargs["eq"] == {"$name": "eq"}
    assert kwargs["full_timestep"] == 5e-4
    assert kwargs["max_mode_frequency"] == 10**2.5


def test_current_difference_is_exact_and_reports_scale():
    module = load_module()
    result = module.current_difference(
        {"A": 10.0, "B": -5.0},
        {"A": 12.0, "B": -5.0},
    )
    assert result["labels_equal_and_ordered"] is True
    assert result["exact_values_equal"] is False
    assert result["max_absolute_difference_A"] == 2.0
    assert result["max_relative_difference"] == 2.0 / 12.0


def test_exact_equal_rejects_mapping_order_and_numeric_changes():
    module = load_module()
    assert module.exact_equal({"a": 1.0, "b": 2}, {"a": 1, "b": 2.0})
    assert not module.exact_equal({"a": 1, "b": 2}, {"b": 2, "a": 1})
    assert not module.exact_equal({"a": 1}, {"a": 1.0 + 1e-15})
