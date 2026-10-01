"""Shared smoke-only entry point; formal scientific functions/settings are untouched."""
import argparse
import csv
import importlib
import json
import random

import numpy as np

from src.mosp import mosp
from src.paths import PROJECT_ROOT, project_path


def _solve(graph, source, target, objectives, condition):
    labels, stats = mosp(graph, source, objectives, return_stats=True)
    return {"condition": str(condition), "source": source, "target": target,
            "nodes": len(graph.nodes()),
            "edges": sum(len(graph.neighbors(n)) for n in graph.nodes()),
            "target_pareto_labels": len(labels[target]), **stats}


def run_smoke(experiment, output_dir):
    module = importlib.import_module("experiments.synthetic." + experiment)
    rows = []
    if experiment in {"experiment_01", "experiment_02a", "experiment_02b"}:
        rng = random.Random(module.SEED)
        topology = module.generate_topology(rng)
        queries = module.generate_queries(rng)  # Consume all formal 10 OD draws.
        cost_seed = rng.randint(0, 10**9)
        source, target = queries[0]
        if experiment == "experiment_01":
            costs = module.generate_full_costs(topology, cost_seed)
            for objectives in module.OBJECTIVES:
                rows.append(_solve(module.build_graph(topology, costs, objectives), source, target, objectives, objectives))
        elif experiment == "experiment_02a":
            z1, z2 = module.generate_base_normals(len(topology), cost_seed)
            for rho in module.CORRELATIONS:
                costs, observed = module.generate_correlated_costs(topology, z1, z2, rho)
                row = _solve(module.build_graph(topology, costs), source, target, module.NUM_OBJECTIVES, rho)
                row["observed_rho"] = float(observed)
                rows.append(row)
        else:
            base_z = module.generate_base_normals(len(topology), cost_seed)
            for name, matrix in module.DEPENDENCE_STRUCTURES.items():
                module.validate_correlation_matrix(matrix, name)
                costs, observed = module.generate_costs(topology, base_z, matrix)
                row = _solve(module.build_graph(topology, costs), source, target, module.NUM_OBJECTIVES, name)
                row.update(rho_12=float(observed[0, 1]), rho_13=float(observed[0, 2]), rho_23=float(observed[1, 2]))
                rows.append(row)
    elif experiment == "experiment_03a":
        topology = module.create_master_topology()
        costs = module.generate_master_costs(topology, random.Random(module.SEED))
        for k in module.ROUTE_COUNTS:
            graph, _, _ = module.build_graph(topology, costs, k)
            rows.append(_solve(graph, topology["source"], topology["target"], module.NUM_OBJECTIVES, k))
    elif experiment == "experiment_03b":
        for shared_length in module.SHARED_LENGTHS:
            seed = module.BASE_SEED + shared_length * 100000
            shared, unique = module.generate_cost_bank(np.random.default_rng(seed), module.ROUTE_COUNT,
                                                       module.ROUTE_LENGTH, shared_length, module.OBJECTIVES)
            pareto_sets = []
            for structure in module.STRUCTURES:
                graph, source, target = getattr(module, "build_" + structure + "_graph")(shared, unique)[:3]
                labels = mosp(graph, source, module.OBJECTIVES)
                pareto_sets.append({label.costs for label in labels[target]})
                rows.append(_solve(graph, source, target, module.OBJECTIVES, f"{structure}:{shared_length}"))
            assert pareto_sets[0] == pareto_sets[1], "Paired controls disagree"
    else:
        raise ValueError(f"Unsupported smoke experiment: {experiment}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "smoke.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {"experiment": experiment, "smoke_only": True, "cases": len(rows),
               "project_root": str(PROJECT_ROOT), "output": str(output),
               "formal_settings_modified": False}
    (output_dir / "smoke.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def maybe_run_smoke_test(experiment):
    parser = argparse.ArgumentParser(description=f"MOSP {experiment}; default: unchanged formal experiment")
    parser.add_argument("--smoke-test", action="store_true", help="One original replicate/query per condition; no formal CSV writes")
    parser.add_argument("--smoke-output-dir", help="Optional output under regression/; relative paths use the canonical root")
    args = parser.parse_args()
    if args.smoke_output_dir and not args.smoke_test:
        parser.error("--smoke-output-dir requires --smoke-test")
    if not args.smoke_test:
        return
    output_dir = project_path(args.smoke_output_dir or f"regression/package_smoke/{experiment}")
    regression_dir = PROJECT_ROOT / "regression"
    if not output_dir.is_relative_to(regression_dir):
        parser.error("Smoke output must be within the canonical regression/ directory")
    run_smoke(experiment, output_dir)
    raise SystemExit(0)
