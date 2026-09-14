#!/usr/bin/env python3
"""OpenMC upper-bound TBR screen for a Pb-17Li breeding blanket.

This is deliberately a *screening* geometry: a 4-pi spherical breeding blanket
surrounding an isotropic 14.1 MeV D-T neutron source. Full coverage makes the
calculated TBR an optimistic upper bound relative to a real tokamak with ports,
divertor gaps, penetrations, structural heterogeneity and asymmetric build.

Purpose: identify whether any practical blanket-thickness/Li-6-enrichment region
can clear TBR targets 1.05, 1.10 and 1.15 before investing in a detailed sector
model. A negative result is meaningful early falsification; a positive result is
only permission to proceed to realistic geometry.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path

import numpy as np
import openmc


THICKNESSES_CM = (20.0, 30.0, 40.0, 50.0, 60.0, 80.0, 100.0)
LI6_ENRICHMENTS_PCT = (7.5, 20.0, 40.0, 60.0, 80.0, 90.0)
TARGETS = (1.05, 1.10, 1.15)
PLASMA_RADIUS_CM = 100.0
FIRST_WALL_THICKNESS_CM = 2.0
PBLi_DENSITY_G_CM3 = 9.4
STEEL_DENSITY_G_CM3 = 7.8
SOURCE_ENERGY_EV = 14.1e6


def make_steel() -> openmc.Material:
    material = openmc.Material(name="screening_first_wall_steel")
    # Reduced EUROFER-like screening mixture. The exact composition is not a
    # materials claim; detailed geometry must replace it before reactor use.
    material.add_element("Fe", 0.90, percent_type="ao")
    material.add_element("Cr", 0.09, percent_type="ao")
    material.add_element("W", 0.01, percent_type="ao")
    material.set_density("g/cm3", STEEL_DENSITY_G_CM3)
    return material


def make_pb17li(li6_enrichment_pct: float) -> openmc.Material:
    if not 0.0 < li6_enrichment_pct < 100.0:
        raise ValueError("Li-6 enrichment must lie strictly between 0 and 100 percent")
    enrich = li6_enrichment_pct / 100.0
    material = openmc.Material(name=f"Pb17Li_Li6_{li6_enrichment_pct:g}pct")
    # Approximate eutectic Pb-17Li as 83 atom% natural lead and 17 atom% lithium.
    material.add_element("Pb", 0.83, percent_type="ao")
    material.add_nuclide("Li6", 0.17 * enrich, percent_type="ao")
    material.add_nuclide("Li7", 0.17 * (1.0 - enrich), percent_type="ao")
    material.set_density("g/cm3", PBLi_DENSITY_G_CM3)
    return material


def build_model(thickness_cm: float, li6_enrichment_pct: float, particles: int, batches: int, seed: int) -> openmc.Model:
    steel = make_steel()
    breeder = make_pb17li(li6_enrichment_pct)

    plasma_edge = openmc.Sphere(r=PLASMA_RADIUS_CM)
    fw_outer = openmc.Sphere(r=PLASMA_RADIUS_CM + FIRST_WALL_THICKNESS_CM)
    blanket_outer = openmc.Sphere(
        r=PLASMA_RADIUS_CM + FIRST_WALL_THICKNESS_CM + thickness_cm,
        boundary_type="vacuum",
    )

    plasma_cell = openmc.Cell(name="source_region", region=-plasma_edge)
    first_wall_cell = openmc.Cell(
        name="first_wall",
        fill=steel,
        region=+plasma_edge & -fw_outer,
    )
    blanket_cell = openmc.Cell(
        name="breeding_blanket",
        fill=breeder,
        region=+fw_outer & -blanket_outer,
    )
    geometry = openmc.Geometry([plasma_cell, first_wall_cell, blanket_cell])

    source = openmc.IndependentSource()
    source.space = openmc.stats.Point((0.0, 0.0, 0.0))
    source.angle = openmc.stats.Isotropic()
    source.energy = openmc.stats.Discrete([SOURCE_ENERGY_EV], [1.0])

    settings = openmc.Settings()
    settings.run_mode = "fixed source"
    settings.source = source
    settings.particles = int(particles)
    settings.batches = int(batches)
    settings.inactive = 0
    settings.seed = int(seed)
    settings.output = {"summary": False, "tallies": False}

    tbr = openmc.Tally(name="tbr")
    tbr.filters = [openmc.CellFilter(blanket_cell)]
    tbr.scores = ["(n,Xt)"]

    # Leakage is a useful sanity check: in a full-coverage sphere it should fall
    # as thickness increases. It is not a reactor shielding qualification.
    leakage = openmc.Tally(name="outer_leakage")
    leakage.filters = [openmc.SurfaceFilter(blanket_outer)]
    leakage.scores = ["current"]

    model = openmc.Model(
        geometry=geometry,
        materials=openmc.Materials([steel, breeder]),
        settings=settings,
        tallies=openmc.Tallies([tbr, leakage]),
    )
    return model


def run_case(output_root: Path, thickness_cm: float, enrichment_pct: float, particles: int, batches: int, seed: int) -> dict[str, float | int | str]:
    case_id = f"t{int(thickness_cm):03d}_e{enrichment_pct:g}".replace(".", "p")
    case_dir = output_root / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    model = build_model(thickness_cm, enrichment_pct, particles, batches, seed)
    statepoint_path = model.run(cwd=case_dir, threads=1, output=False)
    with openmc.StatePoint(statepoint_path) as sp:
        tbr_tally = sp.get_tally(name="tbr")
        leakage_tally = sp.get_tally(name="outer_leakage")
        tbr_mean = float(np.sum(tbr_tally.mean))
        tbr_std = float(math.sqrt(np.sum(np.square(tbr_tally.std_dev))))
        leakage_mean = float(np.sum(leakage_tally.mean))
        leakage_std = float(math.sqrt(np.sum(np.square(leakage_tally.std_dev))))

    result = {
        "case_id": case_id,
        "blanket_thickness_cm": float(thickness_cm),
        "li6_enrichment_pct": float(enrichment_pct),
        "tbr_mean": tbr_mean,
        "tbr_std_dev": tbr_std,
        "tbr_rel_sigma_pct": 100.0 * tbr_std / tbr_mean if tbr_mean else math.inf,
        "outer_surface_current_mean": leakage_mean,
        "outer_surface_current_std_dev": leakage_std,
        "particles_per_batch": int(particles),
        "batches": int(batches),
        "total_source_histories": int(particles * batches),
        "seed": int(seed),
    }
    (case_dir / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    # Statepoints can dominate artifact size; preserve compact numerical results
    # plus XML inputs, then remove transport state after extraction.
    Path(statepoint_path).unlink(missing_ok=True)
    return result


def frontier(results: list[dict[str, float | int | str]], target: float) -> list[dict[str, float | int | str]]:
    survivors = [r for r in results if float(r["tbr_mean"]) - 2.0 * float(r["tbr_std_dev"]) >= target]
    frontier_rows = []
    for enrichment in LI6_ENRICHMENTS_PCT:
        rows = [r for r in survivors if math.isclose(float(r["li6_enrichment_pct"]), enrichment)]
        if rows:
            frontier_rows.append(min(rows, key=lambda r: float(r["blanket_thickness_cm"])))
    return frontier_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--particles", type=int, default=20000)
    parser.add_argument("--batches", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260904)
    args = parser.parse_args()
    if args.particles < 1000 or args.batches < 2:
        raise SystemExit("screen requires at least 1000 particles and 2 batches")
    args.output.mkdir(parents=True, exist_ok=True)

    cross_sections = os.environ.get("OPENMC_CROSS_SECTIONS")
    if not cross_sections or not Path(cross_sections).is_file():
        raise SystemExit("OPENMC_CROSS_SECTIONS must point to a real cross_sections.xml")

    results: list[dict[str, float | int | str]] = []
    case_index = 0
    for thickness in THICKNESSES_CM:
        for enrichment in LI6_ENRICHMENTS_PCT:
            results.append(
                run_case(
                    args.output,
                    thickness,
                    enrichment,
                    args.particles,
                    args.batches,
                    args.seed + case_index * 7919,
                )
            )
            case_index += 1

    frontiers = {str(target): frontier(results, target) for target in TARGETS}
    payload = {
        "schema": "fusion-solution-set.openmc-pb17li-tbr-screen.v1",
        "openmc_version": openmc.__version__,
        "nuclear_data_cross_sections_xml": str(Path(cross_sections).resolve()),
        "geometry": {
            "type": "4pi_spherical_upper_bound_screen",
            "plasma_radius_cm": PLASMA_RADIUS_CM,
            "first_wall_thickness_cm": FIRST_WALL_THICKNESS_CM,
            "blanket_thicknesses_cm": list(THICKNESSES_CM),
        },
        "blanket": {
            "composition": "Pb17Li, 83 atom% natural Pb / 17 atom% Li",
            "density_g_cm3": PBLi_DENSITY_G_CM3,
            "li6_enrichment_pct": list(LI6_ENRICHMENTS_PCT),
        },
        "targets": list(TARGETS),
        "acceptance_rule": "TBR mean minus 2 statistical standard deviations >= target",
        "results": results,
        "minimum_thickness_frontier_by_target": frontiers,
        "claim_boundary": [
            "This 4-pi spherical screen is optimistic and cannot establish tokamak TBR.",
            "Ports, divertors, penetrations, blanket structure, coolant channels, realistic plasma source and detailed materials are omitted.",
            "A surviving point only advances to realistic tokamak-sector neutronics.",
            "A point that fails here is strong evidence that the same material/thickness/enrichment cannot succeed after adding real geometric losses.",
            "Nuclear-data-library uncertainty is not yet propagated; a later fusion-grade result must compare a FENDL-class library where available.",
        ],
    }
    (args.output / "OPENMC_PB17LI_TBR_SCREEN.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    with (args.output / "OPENMC_PB17LI_TBR_SCREEN.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(results[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    md = [
        "# OpenMC Pb-17Li upper-bound TBR screen",
        "",
        "This is a 4-pi spherical screening model. Positive results are not reactor TBR predictions; negative results are useful early falsification because real tokamak geometry can only add losses relative to this idealized coverage.",
        "",
        "Acceptance uses `TBR_mean - 2σ >= target`.",
        "",
        "| Target | Li-6 enrichment | Minimum surviving blanket thickness | TBR mean ± σ |",
        "|---:|---:|---:|---:|",
    ]
    for target in TARGETS:
        rows = frontiers[str(target)]
        if not rows:
            md.append(f"| {target:.2f} | — | **none in grid** | — |")
        else:
            for row in rows:
                md.append(
                    f"| {target:.2f} | {float(row['li6_enrichment_pct']):.1f}% | "
                    f"{float(row['blanket_thickness_cm']):.0f} cm | "
                    f"{float(row['tbr_mean']):.4f} ± {float(row['tbr_std_dev']):.4f} |"
                )
    md.extend([
        "",
        "## Next gate",
        "",
        "Any surviving TBR≥1.15 region must be rebuilt as a tokamak-sector model with penetrations/divertor/structure and then coupled back to PROCESS for net-electric and radial-build impact.",
        "",
    ])
    (args.output / "OPENMC_PB17LI_TBR_SCREEN.md").write_text("\n".join(md), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
