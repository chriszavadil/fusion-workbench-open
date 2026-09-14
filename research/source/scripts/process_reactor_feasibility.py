#!/usr/bin/env python3
"""Run a small reactor-level PROCESS feasibility matrix.

Goal: test whether a generic large tokamak can simultaneously satisfy
tritium breeding, net-electric, divertor and neutron-wall-load constraints,
while recording the design changes and effective annual electric output.

This is a systems-model feasibility audit, not experimental validation.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
from pathlib import Path
from typing import Any

from process.main import SingleRun
try:
    from process.core.io.mfile import MFile
except ImportError:
    from process.core.io.mfile.base import MFile


CASES = [
    {
        "id": "baseline_generic",
        "tbrmin": None,
        "net_mw": 400.0,
        "div_limit": 10.0,
        "wall_limit": 2.0,
        "availability": 0.80,
    },
    {
        "id": "tbr105",
        "tbrmin": 1.05,
        "net_mw": 400.0,
        "div_limit": 10.0,
        "wall_limit": 2.0,
        "availability": 0.80,
    },
    {
        "id": "tbr110",
        "tbrmin": 1.10,
        "net_mw": 400.0,
        "div_limit": 10.0,
        "wall_limit": 2.0,
        "availability": 0.80,
    },
    {
        "id": "tbr115",
        "tbrmin": 1.15,
        "net_mw": 400.0,
        "div_limit": 10.0,
        "wall_limit": 2.0,
        "availability": 0.80,
    },
    {
        "id": "tbr110_net500",
        "tbrmin": 1.10,
        "net_mw": 500.0,
        "div_limit": 10.0,
        "wall_limit": 2.0,
        "availability": 0.80,
    },
    {
        "id": "tbr110_div8",
        "tbrmin": 1.10,
        "net_mw": 400.0,
        "div_limit": 8.0,
        "wall_limit": 2.0,
        "availability": 0.80,
    },
    {
        "id": "tbr110_wall15",
        "tbrmin": 1.10,
        "net_mw": 400.0,
        "div_limit": 10.0,
        "wall_limit": 1.5,
        "availability": 0.80,
    },
    {
        "id": "tbr110_avail85",
        "tbrmin": 1.10,
        "net_mw": 400.0,
        "div_limit": 10.0,
        "wall_limit": 2.0,
        "availability": 0.85,
    },
]

KEY_OUTPUTS = (
    "tbr",
    "f_blkt_li6_enrichment",
    "rmajor",
    "rminor",
    "aspect",
    "p_fusion_total_mw",
    "p_plant_electric_gross_mw",
    "p_plant_electric_net_mw",
    "p_coolant_pump_elec_total_mw",
    "p_plasma_separatrix_mw",
    "pflux_fw_neutron_mw",
    "p_hcd_primary_extra_heat_mw",
    "f_t_plant_available",
)

RELEVANT_TOKENS = (
    "tbr", "trit", "plant_electric", "fusion_total", "separatrix", "neutron",
    "div", "availability", "hcd", "inject", "blanket", "blkt", "li6",
    "rmajor", "rminor", "aspect", "cost_of_electric", "coe", "coolant_pump",
)


def scalar_jsonable(value: Any) -> Any:
    if isinstance(value, (str, bool, int)) or value is None:
        return value
    try:
        number = float(value)
    except Exception:
        return None
    if not math.isfinite(number):
        return None
    return number


def safe_get(mfile: MFile, key: str) -> Any:
    try:
        return scalar_jsonable(mfile.get(key, scan=-1))
    except Exception:
        return None


def collect_relevant_mfile(mfile: MFile) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in sorted(mfile.data):
        lower = str(key).lower()
        if any(token in lower for token in RELEVANT_TOKENS):
            value = safe_get(mfile, key)
            if value is not None:
                result[str(key)] = value
    return result


def append_overrides(text: str, case: dict[str, Any]) -> str:
    lines = [
        "",
        "* Fusion Solution Set reactor-feasibility audit overrides *",
        f"p_plant_electric_net_required_mw = {case['net_mw']}",
        f"p_div_bt_q_aspect_rmajor_max_mw = {case['div_limit']}",
        f"pflux_fw_neutron_max_mw = {case['wall_limit']}",
        f"f_t_plant_available = {case['availability']}",
    ]
    if case["tbrmin"] is not None:
        # Constraint 52 is minimum TBR. Iteration variable 98 is Li-6 enrichment.
        # This lets PROCESS search for breeding margin rather than merely checking
        # a fixed enrichment value.
        lines.extend([
            "icc = 52",
            "ixc = 98",
            "boundl(98) = 7.5",
            "boundu(98) = 90.0",
            "f_blkt_li6_enrichment = 30.0",
            f"tbrmin = {case['tbrmin']}",
        ])
    return text.rstrip() + "\n" + "\n".join(lines) + "\n"


def run_case(source_root: Path, output_root: Path, case: dict[str, Any]) -> dict[str, Any]:
    case_dir = output_root / "cases" / case["id"]
    case_dir.mkdir(parents=True, exist_ok=True)
    source_input = source_root / "examples" / "data" / "large_tokamak_IN.DAT"
    input_path = case_dir / f"{case['id']}_IN.DAT"
    input_path.write_text(
        append_overrides(source_input.read_text(encoding="utf-8"), case),
        encoding="utf-8",
    )

    result: dict[str, Any] = {
        "case": dict(case),
        "run_exception": None,
        "mfile_present": False,
        "out_present": False,
        "feasible_text": False,
        "key_outputs": {},
        "relevant_outputs": {},
    }

    try:
        run = SingleRun(input_path.as_posix())
        run.run()
        mfile_path = Path(run.mfile_path)
    except Exception as exc:
        result["run_exception"] = {"type": type(exc).__name__, "message": str(exc)}
        candidates = sorted(case_dir.glob("*MFILE.DAT"))
        mfile_path = candidates[0] if candidates else case_dir / "MFILE.DAT"

    out_candidates = sorted(case_dir.glob("*OUT.DAT"))
    out_path = out_candidates[0] if out_candidates else case_dir / "OUT.DAT"
    if out_path.is_file():
        result["out_present"] = True
        out_text = out_path.read_text(encoding="utf-8", errors="replace")
        lower = out_text.lower()
        result["feasible_text"] = (
            "feasible solution" in lower
            and "no feasible solution" not in lower
            and "infeasible solution" not in lower
        )
        (case_dir / "OUT_TAIL.txt").write_text("\n".join(out_text.splitlines()[-180:]) + "\n")

    if mfile_path.is_file():
        result["mfile_present"] = True
        try:
            mfile = MFile(filename=mfile_path)
            result["key_outputs"] = {key: safe_get(mfile, key) for key in KEY_OUTPUTS}
            result["relevant_outputs"] = collect_relevant_mfile(mfile)
        except Exception as exc:
            result["mfile_parse_error"] = {"type": type(exc).__name__, "message": str(exc)}

    key = result["key_outputs"]
    net = key.get("p_plant_electric_net_mw")
    availability = case["availability"]
    if isinstance(net, (int, float)):
        result["annualized_net_mw_average"] = net * availability
        result["annual_net_electricity_mwh"] = net * availability * 8766.0
    else:
        result["annualized_net_mw_average"] = None
        result["annual_net_electricity_mwh"] = None

    tbr = key.get("tbr")
    result["tbr_margin_over_1_10"] = None if not isinstance(tbr, (int, float)) else tbr - 1.10
    result["scientific_feasible"] = bool(
        result["run_exception"] is None
        and result["mfile_present"]
        and result["feasible_text"]
    )
    (case_dir / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def write_summary(output_root: Path, results: list[dict[str, Any]]) -> None:
    summary = {
        "schema": "fusion-solution-set.process-reactor-feasibility.v1",
        "source": {
            "code": "UKAEA PROCESS",
            "tag": "v3.4.2",
            "baseline_input": "examples/data/large_tokamak_IN.DAT",
        },
        "question": (
            "Can the generic large tokamak simultaneously retain net electric output, "
            "tritium breeding margin, divertor loading, neutron wall loading and declared availability?"
        ),
        "cases": results,
        "claim_boundary": [
            "PROCESS is a systems model; these are conceptual design feasibility results, not an experiment.",
            "TBR in PROCESS is model-derived and is not a neutronics certification.",
            "Availability is a systems assumption/model input and must not be represented as demonstrated plant availability.",
            "A feasible PROCESS point is tangible systems-design progress, not proof that fusion power is solved.",
        ],
    }
    (output_root / "PROCESS_REACTOR_FEASIBILITY_RESULT.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    fields = [
        "case", "scientific_feasible", "tbr", "tbr_margin_over_1_10",
        "li6_enrichment_pct", "rmajor_m", "fusion_power_mw", "gross_electric_mw",
        "net_electric_mw", "annualized_net_mw_average", "wall_neutron_mw_m2",
        "separatrix_power_mw", "availability", "run_exception",
    ]
    with (output_root / "PROCESS_REACTOR_FEASIBILITY_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            key = result["key_outputs"]
            writer.writerow({
                "case": result["case"]["id"],
                "scientific_feasible": result["scientific_feasible"],
                "tbr": key.get("tbr"),
                "tbr_margin_over_1_10": result.get("tbr_margin_over_1_10"),
                "li6_enrichment_pct": key.get("f_blkt_li6_enrichment"),
                "rmajor_m": key.get("rmajor"),
                "fusion_power_mw": key.get("p_fusion_total_mw"),
                "gross_electric_mw": key.get("p_plant_electric_gross_mw"),
                "net_electric_mw": key.get("p_plant_electric_net_mw"),
                "annualized_net_mw_average": result.get("annualized_net_mw_average"),
                "wall_neutron_mw_m2": key.get("pflux_fw_neutron_mw"),
                "separatrix_power_mw": key.get("p_plasma_separatrix_mw"),
                "availability": result["case"]["availability"],
                "run_exception": None if result["run_exception"] is None else result["run_exception"]["message"],
            })

    feasible = [r for r in results if r["scientific_feasible"]]
    report = [
        "# PROCESS reactor-feasibility audit",
        "",
        "This study asks a plant-level question rather than a plasma-control-only question.",
        "",
        f"Feasible cases: **{len(feasible)}/{len(results)}**.",
        "",
        "| Case | Feasible | TBR | Li-6 % | R0 m | Net MWe | Avg net MWe @ availability |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        k = r["key_outputs"]
        def fmt(v: Any, digits: int = 3) -> str:
            return "—" if v is None else f"{float(v):.{digits}f}"
        report.append(
            f"| {r['case']['id']} | {r['scientific_feasible']} | {fmt(k.get('tbr'))} | "
            f"{fmt(k.get('f_blkt_li6_enrichment'), 2)} | {fmt(k.get('rmajor'))} | "
            f"{fmt(k.get('p_plant_electric_net_mw'), 1)} | {fmt(r.get('annualized_net_mw_average'), 1)} |"
        )
    report.extend([
        "",
        "## Interpretation boundary",
        "",
        "A feasible point means the PROCESS conceptual systems constraints closed for that case. It does not validate materials, neutronics, component lifetime, tritium extraction, disruption tolerance, or economics experimentally.",
        "",
    ])
    (output_root / "PROCESS_REACTOR_FEASIBILITY_RESULT.md").write_text("\n".join(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--process-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = [run_case(args.process_root.resolve(), args.output.resolve(), case) for case in CASES]
    write_summary(args.output.resolve(), results)
    # Do not make the workflow fail merely because physics/engineering cases are infeasible.
    # A run/setup exception in every case is an execution failure; mixed/physical infeasibility is evidence.
    if all(r["run_exception"] is not None for r in results):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
