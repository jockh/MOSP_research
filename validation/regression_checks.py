"""Reproducibility checks; no formal output or experiment defaults are modified."""
from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.util
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.paths import PROJECT_ROOT, TAIPEI_METRO_DATA_DIR
from src.mosp import mosp
from src.taipei_metro import build_taipei_metro_graph


def original_module(name):
    """Load archived source definitions without running historical I/O or loops."""
    path = PROJECT_ROOT / 'archive/original_sources/Mosp_vr1.1/experiments' / name
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    excluded = {'ROOT', 'PROJECT_ROOT', 'CURRENT_DIR', 'OUTPUT_DIR', 'OUTPUT_FILE', 'SCRIPT_DIR'}
    body = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef)):
            body.append(node)
        elif isinstance(node, ast.Assign):
            names = {t.id for t in node.targets if isinstance(t, ast.Name)}
            if not names & excluded:
                body.append(node)
    namespace = {'__file__': str(path), '__name__': 'archived_source_definitions'}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def graph_signature(graph):
    return [(node, [(edge.to, edge.costs) for edge in graph.neighbors(node)]) for node in graph.nodes()]


def assert_stats(graph, source, target, objectives, row):
    labels, stats = mosp(graph, source, objectives, return_stats=True)
    assert len(labels[target]) == row.target_pareto_labels
    for key, value in stats.items():
        assert value == row[key], (key, value, row[key])
    return len(labels[target])


def main():
    os.environ.pop('MOSP_RESULTS_DIR', None)
    checks = {}
    # Compilation and package import checks cover every active research module.
    imports = []
    for folder in ['src', 'experiments', 'validation', 'analysis']:
        for path in sorted((PROJECT_ROOT / folder).rglob('*.py')):
            compile(path.read_text(encoding='utf-8-sig'), str(path), 'exec')
            module = '.'.join(path.relative_to(PROJECT_ROOT).with_suffix('').parts)
            if module.endswith('.__init__'):
                module = module[:-9]
            if module != __name__:
                importlib.import_module(module)
            imports.append(module)
    checks['import_smoke'] = {'modules': len(imports), 'passed': True}

    # Core/model byte identity is stronger than merely matching a few outputs.
    core = {}
    for name in ['graph.py', 'label.py', 'dominance.py', 'mosp.py', 'brute_force.py']:
        current = (PROJECT_ROOT / 'src' / name).read_bytes()
        for project in ['Mosp_vr1.1', 'Real_case1']:
            assert current == (PROJECT_ROOT / 'archive/original_sources' / project / 'src' / name).read_bytes()
        core[name] = hashlib.sha256(current).hexdigest()
    assert (PROJECT_ROOT / 'src/taipei_metro.py').read_bytes() == (PROJECT_ROOT / 'archive/original_sources/Real_case1/src/taipei_metro.py').read_bytes()
    checks['shared_core_and_model_bytes'] = core

    # Import-safety changes cannot permit analysis modules to write formal files.
    manifest = json.loads((PROJECT_ROOT / 'audit/migration_manifest.json').read_text(encoding='utf-8'))
    preserved = 0
    for item in manifest:
        if item['role'] in ['saved result', 'saved figure', 'saved All-OD result/analysis/figure', 'formal model input', 'website coordinate input (not a model input)']:
            assert hashlib.sha256((PROJECT_ROOT / item['destination']).read_bytes()).hexdigest() == item['source_sha256'], item['destination']
            preserved += 1
    checks['formal_artifact_hashes'] = {'files': preserved, 'unchanged': True}

    pairs = {'experiment_01': 'experiment_01_objectives.py', 'experiment_02a': 'experiment_02a_correlation.py', 'experiment_02b': 'experiment_02b_dependence_3d.py', 'experiment_03a': 'experiment_03a_route_quantity.py', 'experiment_03b': 'experiment_03b_route_overlap.py'}
    modules = {}
    unchanged_functions = {}
    for new, old in pairs.items():
        module = importlib.import_module('experiments.synthetic.' + new)
        baseline = original_module(old)
        modules[new] = (module, baseline)
        old_tree = ast.parse((PROJECT_ROOT / 'archive/original_sources/Mosp_vr1.1/experiments' / old).read_text(encoding='utf-8-sig'))
        new_tree = ast.parse((PROJECT_ROOT / 'experiments/synthetic' / (new + '.py')).read_text(encoding='utf-8-sig'))
        old_functions = {n.name: ast.dump(n, include_attributes=False) for n in old_tree.body if isinstance(n, ast.FunctionDef)}
        new_functions = {n.name: ast.dump(n, include_attributes=False) for n in new_tree.body if isinstance(n, ast.FunctionDef)}
        changed = [name for name in old_functions if old_functions[name] != new_functions[name]]
        assert set(changed) <= {'save_results', 'save_csv', 'save_correlation_checks', 'main'}, changed
        unchanged_functions[new] = {'unchanged': [n for n in old_functions if n not in changed], 'path_only': changed}
        for key, value in baseline.items():
            if key.isupper() and key not in {'ROOT', 'PROJECT_ROOT', 'CURRENT_DIR', 'OUTPUT_DIR', 'OUTPUT_FILE', 'SCRIPT_DIR'}:
                actual = getattr(module, key)
                if isinstance(value, dict):
                    assert value.keys() == actual.keys()
                    for k in value: np.testing.assert_array_equal(value[k], actual[k])
                else: np.testing.assert_array_equal(value, actual)
    checks['scientific_functions_and_settings'] = unchanged_functions

    # Experiment 1: preserve full original RNG consumption before selecting query 0.
    mod, old = modules['experiment_01']
    rng = random.Random(mod.SEED)
    topology = mod.generate_topology(rng)
    queries = mod.generate_queries(rng)
    seed = rng.randint(0, 10**9)
    costs = mod.generate_full_costs(topology, seed)
    old_rng = random.Random(old['SEED'])
    assert topology == old['generate_topology'](old_rng)
    assert queries == old['generate_queries'](old_rng)
    assert costs == old['generate_full_costs'](topology, old_rng.randint(0, 10**9))
    saved = pd.read_csv(PROJECT_ROOT / 'results/experiment_01/experiment_01_formal_raw.csv')
    sizes = {}
    for objectives in mod.OBJECTIVES:
        graph = mod.build_graph(topology, costs, objectives)
        assert graph_signature(graph) == graph_signature(old['build_graph'](topology, costs, objectives))
        row = saved[(saved.network_id == 0) & (saved.query_id == 0) & (saved.objectives == objectives)].iloc[0]
        sizes[str(objectives)] = assert_stats(graph, *queries[0], objectives, row)
    checks['experiment_01'] = {'nodes': mod.NUM_NODES, 'edges': len(topology), 'pareto_counts': sizes, 'matches_saved_statistics': True}

    for exp, raw in [('experiment_02a', 'experiment_02a_correlation_raw.csv'), ('experiment_02b', 'experiment_02b_dependence_3d_raw.csv')]:
        mod, old = modules[exp]
        rng = random.Random(mod.SEED)
        topology = mod.generate_topology(rng)
        queries = mod.generate_queries(rng)
        seed = rng.randint(0, 10**9)
        saved = pd.read_csv(PROJECT_ROOT / 'results' / exp / raw)
        conditions = mod.CORRELATIONS if exp == 'experiment_02a' else list(mod.DEPENDENCE_STRUCTURES)
        base = mod.generate_base_normals(len(topology), seed)
        counts = {}
        for condition in conditions:
            if exp == 'experiment_02a':
                costs, observed = mod.generate_correlated_costs(topology, *base, condition)
                old_costs, old_observed = old['generate_correlated_costs'](topology, *base, condition)
                row = saved[(saved.network_id == 0) & (saved.query_id == 0) & (saved.target_rho == condition)].iloc[0]
            else:
                matrix = mod.DEPENDENCE_STRUCTURES[condition]
                mod.validate_correlation_matrix(matrix, condition)
                np.linalg.cholesky(matrix)
                costs, observed = mod.generate_costs(topology, base, matrix)
                old_costs, old_observed = old['generate_costs'](topology, base, matrix)
                row = saved[(saved.network_id == 0) & (saved.query_id == 0) & (saved.structure == condition)].iloc[0]
            assert costs == old_costs
            np.testing.assert_array_equal(observed, old_observed)
            assert all(all(mod.MIN_COST <= c <= mod.MAX_COST for c in vector) for vector in costs.values())
            graph = mod.build_graph(topology, costs)
            counts[str(condition)] = assert_stats(graph, *queries[0], mod.NUM_OBJECTIVES, row)
        checks[exp] = {'generation_matches_original': True, 'matches_saved_statistics': True, 'pareto_counts': counts}

    mod, old = modules['experiment_03a']
    topology = mod.create_master_topology()
    assert topology == old['create_master_topology']()
    saved = pd.read_csv(PROJECT_ROOT / 'results/experiment_03a/experiment_03a_route_quantity_raw.csv')
    cases = 0
    for replicate in [0, 1, 499]:
        costs = mod.generate_master_costs(topology, random.Random(mod.SEED + replicate))
        assert costs == old['generate_master_costs'](topology, random.Random(mod.SEED + replicate))
        for k in mod.ROUTE_COUNTS:
            graph, nodes, edges = mod.build_graph(topology, costs, k)
            assert graph_signature(graph) == graph_signature(old['build_graph'](topology, costs, k)[0])
            row = saved[(saved.replicate_id == replicate) & (saved.route_count == k)].iloc[0]
            assert_stats(graph, topology['source'], topology['target'], mod.NUM_OBJECTIVES, row)
            assert len(nodes) == row.num_nodes and len(edges) == row.num_edges
            cases += 1
    checks['experiment_03a'] = {'cases': cases, 'generation_and_saved_statistics_match': True}

    mod, old = modules['experiment_03b']
    saved = pd.read_csv(PROJECT_ROOT / 'results/experiment_03b/experiment_03b_overlap_position_raw.csv')
    cases = 0
    for shared in mod.SHARED_LENGTHS:
        for replicate in [0, 1, 499]:
            seed = mod.BASE_SEED + shared * 100000 + replicate
            args = (mod.ROUTE_COUNT, mod.ROUTE_LENGTH, shared, mod.OBJECTIVES)
            shared_costs, unique_costs = mod.generate_cost_bank(np.random.default_rng(seed), *args)
            original_costs = old['generate_cost_bank'](np.random.default_rng(seed), *args)
            np.testing.assert_array_equal(shared_costs, original_costs[0])
            np.testing.assert_array_equal(unique_costs, original_costs[1])
            pareto_sets = []
            for structure in mod.STRUCTURES:
                built = getattr(mod, 'build_' + structure + '_graph')(shared_costs, unique_costs)
                # The original builder returns graph/source/target/node/edge metadata.
                graph, source, target = built[:3]
                assert graph_signature(graph) == graph_signature(old['build_' + structure + '_graph'](shared_costs, unique_costs)[0])
                labels, stats = mosp(graph, source, mod.OBJECTIVES, return_stats=True)
                pareto_sets.append({l.costs for l in labels[target]})
                row = saved[(saved.replicate_id == replicate) & (saved.shared_length == shared) & (saved.structure == structure)].iloc[0]
                assert len(labels[target]) == row.target_pareto_labels == row.reference_pareto_labels
                for key in stats: assert stats[key] == row[key]
                cases += 1
            assert pareto_sets[0] == pareto_sets[1]
    checks['experiment_03b'] = {'cases': cases, 'paired_costs_and_pareto_sets_equal': True, 'saved_statistics_match': True}

    graph, stats = build_taipei_metro_graph(
        TAIPEI_METRO_DATA_DIR / '臺北捷運路線車站資料服務_NEW_fixed (1).csv',
        TAIPEI_METRO_DATA_DIR / '臺北捷運相鄰兩站間之行駛時間及停靠站時間(1150830).csv',
        TAIPEI_METRO_DATA_DIR / '臺北捷運轉乘車站轉乘步行時間資料.csv',
        include_circular_line=True, dapinglin_transfer_minutes=3.0)
    assert stats['circular_line_included'] and stats['skipped_travel_rows'] == 0
    baseline = json.loads((PROJECT_ROOT / 'audit/preflight.json').read_text(encoding='utf-8'))
    # JSON converts tuples to lists; normalize both for exact graph-build statistics.
    assert json.loads(json.dumps(stats, ensure_ascii=False)) == baseline['build_stats']
    checks['taipei_metro'] = {'physical_stations': len(graph.states_by_name), 'route_states': len(graph.nodes()), 'build_stats_match_original': True, 'circular_line_included': True, 'skipped_travel_rows': 0}

    all_od = PROJECT_ROOT / 'regression/runs/all_od/experiment_05_all_od'
    result_files = {}
    for path in (PROJECT_ROOT / 'results/experiment_05_all_od').glob('*.csv'):
        new = pd.read_csv(all_od / path.name, encoding='utf-8-sig')
        saved = pd.read_csv(path, encoding='utf-8-sig')
        if path.name == 'source_mosp_statistics.csv':
            new = new.drop(columns=['runtime_seconds']); saved = saved.drop(columns=['runtime_seconds'])
        pd.testing.assert_frame_equal(new, saved, check_exact=True)
        result_files[path.name] = len(saved)
    checks['all_od_full_recomputation'] = {'files': result_files, 'all_non_runtime_fields_exact_match': True}

    # Exercise HTTP routing and the actual CSV readers through ASGI, without a server.
    backend = PROJECT_ROOT / 'web/taipei-pareto-explorer/backend/main.py'
    spec = importlib.util.spec_from_file_location('canonical_web_backend', backend)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    from fastapi.testclient import TestClient
    with TestClient(module.app) as client:
        health = client.get('/api/health'); assert health.status_code == 200
        data = health.json(); assert data['ok'] and data['pareto_csv_found']
        assert data['missing_station_count'] == 0, data
        routes = client.get('/api/routes', params={'origin': '東湖站', 'destination': '中原站'})
        assert routes.status_code == 200, routes.text
        checks['web_backend'] = {'health_status': health.status_code, 'health': data, 'example_routes_status': routes.status_code, 'example_routes': routes.json()}

    out = PROJECT_ROOT / 'regression/checks.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in checks.items() if k not in {'scientific_functions_and_settings', 'web_backend'}}, ensure_ascii=False, indent=2))
    print('WEB:', health.status_code, 'matched stations', data['matched_station_count'])
    print('All regression checks passed. Evidence:', out)


if __name__ == '__main__':
    main()
