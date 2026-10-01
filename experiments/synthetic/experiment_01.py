from src.paths import PROJECT_ROOT, RESULTS_DIR as CANONICAL_RESULTS_DIR, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, result_path, project_path
import csv
import os
import random
import time

from src.graph import Graph
from src.mosp import mosp


# ============================================================
# Experiment 1
# Effect of Number of Objectives on MOSP Performance
# ============================================================

OBJECTIVES = [2, 3, 4, 5]
MAX_OBJECTIVES = max(OBJECTIVES)

NUM_NETWORKS = 50
QUERIES_PER_NETWORK = 10

NUM_NODES = 100
EDGE_PROBABILITY = 0.08

MIN_COST = 1
MAX_COST = 100

SEED = 42


# ============================================================
# 1. Generate network topology
# ============================================================

def generate_topology(rng):
    """
    Generate a directed random graph topology.

    The topology is fixed across m = 2, 3, 4, 5
    for the same network.
    """

    edges = []

    for u in range(NUM_NODES):
        for v in range(NUM_NODES):

            if u == v:
                continue

            if rng.random() < EDGE_PROBABILITY:
                edges.append((u, v))

    return edges


# ============================================================
# 2. Generate fixed full-dimensional edge costs
# ============================================================

def generate_full_costs(topology, cost_seed):
    """
    Generate one fixed MAX_OBJECTIVES-dimensional
    cost vector for every edge.

    Example:
        edge (0, 3) -> (31, 82, 17, 54, 9)

    Then:
        m=2 -> (31, 82)
        m=3 -> (31, 82, 17)
        m=4 -> (31, 82, 17, 54)
        m=5 -> (31, 82, 17, 54, 9)

    This ensures that increasing m only adds
    objectives without changing existing costs.
    """

    rng = random.Random(cost_seed)

    full_costs = {}

    for u, v in topology:

        costs = tuple(
            rng.randint(MIN_COST, MAX_COST)
            for _ in range(MAX_OBJECTIVES)
        )

        full_costs[(u, v)] = costs

    return full_costs


# ============================================================
# 3. Build an m-objective graph
# ============================================================

def build_graph(
    topology,
    full_costs,
    num_objectives
):
    """
    Build a graph using the first m dimensions
    of each edge's fixed cost vector.
    """

    g = Graph()

    # Add all nodes
    for node in range(NUM_NODES):
        g.add_node(node)

    # Add edges
    for u, v in topology:

        costs = full_costs[
            (u, v)
        ][:num_objectives]

        g.add_edge(
            u,
            v,
            costs
        )

    return g


# ============================================================
# 4. Generate OD queries
# ============================================================

def generate_queries(rng):
    """
    Generate fixed source-target pairs.

    The same OD pairs are used for all objective
    dimensions within the same network.
    """

    queries = []

    for _ in range(QUERIES_PER_NETWORK):

        source, target = rng.sample(
            range(NUM_NODES),
            2
        )

        queries.append(
            (source, target)
        )

    return queries


# ============================================================
# 5. Run experiment
# ============================================================

def run_experiment():

    master_rng = random.Random(SEED)

    results = []

    for network_id in range(NUM_NETWORKS):

        print(
            f"Network "
            f"{network_id + 1}/{NUM_NETWORKS}"
        )

        # ----------------------------------------------------
        # Generate one topology
        # ----------------------------------------------------

        topology = generate_topology(
            master_rng
        )

        # ----------------------------------------------------
        # Same OD queries for m = 2, 3, 4, 5
        # ----------------------------------------------------

        queries = generate_queries(
            master_rng
        )

        # ----------------------------------------------------
        # Generate fixed 5-dimensional edge costs
        # ----------------------------------------------------

        cost_seed = master_rng.randint(
            0,
            10**9
        )

        full_costs = generate_full_costs(
            topology,
            cost_seed
        )

        # ----------------------------------------------------
        # Test m = 2, 3, 4, 5
        # ----------------------------------------------------

        for m in OBJECTIVES:

            graph = build_graph(
                topology,
                full_costs,
                m
            )

            for query_id, (
                source,
                target
            ) in enumerate(queries):

                # --------------------------------------------
                # Run MOSP
                # --------------------------------------------

                start_time = (
                    time.perf_counter()
                )

                labels, stats = mosp(
                    graph,
                    source,
                    m,
                    return_stats=True
                )

                runtime = (
                    time.perf_counter()
                    - start_time
                )

                # --------------------------------------------
                # Number of Pareto labels at destination
                # --------------------------------------------

                target_pareto_labels = len(
                    labels[target]
                )

                # --------------------------------------------
                # Store observation
                # --------------------------------------------

                results.append({

                    "network_id":
                        network_id,

                    "query_id":
                        query_id,

                    "objectives":
                        m,

                    "source":
                        source,

                    "target":
                        target,

                    "num_nodes":
                        NUM_NODES,

                    "num_edges":
                        len(topology),

                    "runtime_seconds":
                        runtime,

                    "target_pareto_labels":
                        target_pareto_labels,

                    "generated_labels":
                        stats[
                            "generated_labels"
                        ],

                    "kept_labels":
                        stats[
                            "kept_labels"
                        ],

                    "pruned_labels":
                        stats[
                            "pruned_labels"
                        ],

                    "dominance_checks":
                        stats[
                            "dominance_checks"
                        ],

                    "max_labels_per_node":
                        stats[
                            "max_labels_per_node"
                        ]
                })

    return results


# ============================================================
# 6. Save results
# ============================================================

def save_results(results):

    output_dir = CANONICAL_RESULTS_DIR / 'experiment_01'

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    output_file = os.path.join(
        output_dir,
        "experiment_01_formal_raw.csv"
    )

    fieldnames = list(
        results[0].keys()
    )

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            results
        )

    print()
    print(
        "Results saved to:",
        output_file
    )


# ============================================================
# 7. Sanity check
# ============================================================

def sanity_check():

    print(
        "===== CONTROLLED-COST SANITY CHECK ====="
    )

    rng = random.Random(SEED)

    topology = generate_topology(rng)

    cost_seed = 12345

    full_costs = generate_full_costs(
        topology,
        cost_seed
    )

    if not topology:
        raise RuntimeError(
            "Generated topology has no edges."
        )

    sample_edge = topology[0]

    print(
        "Sample edge:",
        sample_edge
    )

    for m in OBJECTIVES:

        print(
            f"m={m}:",
            full_costs[
                sample_edge
            ][:m]
        )

    print(
        "========================================"
    )
    print()


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    from experiments.synthetic._cli import maybe_run_smoke_test
    maybe_run_smoke_test("experiment_01")

    # Verify that costs are nested correctly
    sanity_check()

    # Run formal experiment
    results = run_experiment()

    # Save raw data
    save_results(results)

    print()
    print(
        "Total observations:",
        len(results)
    )

    expected = (
        NUM_NETWORKS
        * QUERIES_PER_NETWORK
        * len(OBJECTIVES)
    )

    print(
        "Expected observations:",
        expected
    )

    assert len(results) == expected

    print()
    print(
        "Experiment 1 completed successfully."
    )