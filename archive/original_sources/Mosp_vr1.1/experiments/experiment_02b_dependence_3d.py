import csv
import os
import random
import time

import numpy as np
from scipy.stats import norm

from src.graph import Graph
from src.mosp import mosp


# ============================================================
# Experiment 2B
# 3D Objective Dependence Structures
# ============================================================

NUM_OBJECTIVES = 3

NUM_NETWORKS = 50
QUERIES_PER_NETWORK = 10

NUM_NODES = 100
EDGE_PROBABILITY = 0.08

MIN_COST = 1
MAX_COST = 100

SEED = 42


# ============================================================
# Dependence structures
# ============================================================

DEPENDENCE_STRUCTURES = {

    "positive": np.array([
        [1.0, 0.8, 0.8],
        [0.8, 1.0, 0.8],
        [0.8, 0.8, 1.0]
    ]),

    "independent": np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ]),

    "tradeoff": np.array([
        [1.0, -0.4, -0.4],
        [-0.4, 1.0, -0.4],
        [-0.4, -0.4, 1.0]
    ]),

    "mixed": np.array([
        [1.0, 0.6, -0.4],
        [0.6, 1.0, -0.2],
        [-0.4, -0.2, 1.0]
    ])
}


# ============================================================
# 1. Validate correlation matrices
# ============================================================

def validate_correlation_matrix(matrix, name):
    """
    Verify that the correlation matrix is symmetric
    and positive definite.
    """

    if not np.allclose(matrix, matrix.T):
        raise ValueError(
            f"{name}: matrix is not symmetric."
        )

    if not np.allclose(
        np.diag(matrix),
        np.ones(matrix.shape[0])
    ):
        raise ValueError(
            f"{name}: diagonal must equal 1."
        )

    eigenvalues = np.linalg.eigvalsh(matrix)

    print(
        f"{name:12s} eigenvalues:",
        np.round(eigenvalues, 4)
    )

    if np.any(eigenvalues <= 0):
        raise ValueError(
            f"{name}: matrix is not positive definite."
        )


# ============================================================
# 2. Generate graph topology
# ============================================================

def generate_topology(rng):

    edges = []

    for u in range(NUM_NODES):

        for v in range(NUM_NODES):

            if u == v:
                continue

            if rng.random() < EDGE_PROBABILITY:
                edges.append((u, v))

    return edges


# ============================================================
# 3. Generate OD pairs
# ============================================================

def generate_queries(rng):

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
# 4. Common random base
# ============================================================

def generate_base_normals(
    num_edges,
    seed
):
    """
    Generate independent Z ~ N(0, I).

    The SAME base random matrix is reused across
    all four dependence structures.
    """

    rng = np.random.default_rng(seed)

    return rng.standard_normal(
        size=(num_edges, NUM_OBJECTIVES)
    )


# ============================================================
# 5. Apply dependence structure
# ============================================================

def apply_dependence(
    base_z,
    correlation_matrix
):
    """
    If Z ~ N(0, I), construct

        X = Z L^T

    where

        R = L L^T

    so that X approximately follows correlation R.
    """

    L = np.linalg.cholesky(
        correlation_matrix
    )

    X = base_z @ L.T

    return X


# ============================================================
# 6. Gaussian copula -> integer costs
# ============================================================

def normals_to_costs(X):

    U = norm.cdf(X)

    range_size = (
        MAX_COST
        - MIN_COST
        + 1
    )

    costs = (
        MIN_COST
        +
        np.floor(
            U * range_size
        ).astype(int)
    )

    costs = np.clip(
        costs,
        MIN_COST,
        MAX_COST
    )

    return costs


# ============================================================
# 7. Generate edge costs
# ============================================================

def generate_costs(
    topology,
    base_z,
    correlation_matrix
):

    X = apply_dependence(
        base_z,
        correlation_matrix
    )

    costs = normals_to_costs(X)

    edge_costs = {}

    for i, edge in enumerate(topology):

        edge_costs[edge] = tuple(
            int(value)
            for value in costs[i]
        )

    observed_corr = np.corrcoef(
        costs,
        rowvar=False
    )

    return (
        edge_costs,
        observed_corr
    )


# ============================================================
# 8. Build graph
# ============================================================

def build_graph(
    topology,
    edge_costs
):

    graph = Graph()

    for node in range(NUM_NODES):
        graph.add_node(node)

    for u, v in topology:

        graph.add_edge(
            u,
            v,
            edge_costs[(u, v)]
        )

    return graph


# ============================================================
# 9. Run experiment
# ============================================================

def run_experiment():

    master_rng = random.Random(
        SEED
    )

    results = []
    dependence_checks = []

    for network_id in range(
        NUM_NETWORKS
    ):

        print(
            f"Network "
            f"{network_id + 1}/"
            f"{NUM_NETWORKS}"
        )

        # Same topology
        topology = generate_topology(
            master_rng
        )

        # Same OD pairs
        queries = generate_queries(
            master_rng
        )

        # Same base randomness
        base_seed = master_rng.randint(
            0,
            10**9
        )

        base_z = generate_base_normals(
            len(topology),
            base_seed
        )

        # ----------------------------------------
        # Four dependence structures
        # ----------------------------------------

        for (
            structure_name,
            correlation_matrix
        ) in DEPENDENCE_STRUCTURES.items():

            (
                edge_costs,
                observed_corr
            ) = generate_costs(
                topology,
                base_z,
                correlation_matrix
            )

            # ------------------------------------
            # Save manipulation check
            # ------------------------------------

            dependence_checks.append({

                "network_id":
                    network_id,

                "structure":
                    structure_name,

                "rho_12":
                    observed_corr[0, 1],

                "rho_13":
                    observed_corr[0, 2],

                "rho_23":
                    observed_corr[1, 2],

                "num_edges":
                    len(topology)
            })

            graph = build_graph(
                topology,
                edge_costs
            )

            # ------------------------------------
            # Same OD pairs
            # ------------------------------------

            for query_id, (
                source,
                target
            ) in enumerate(queries):

                start = time.perf_counter()

                labels, stats = mosp(
                    graph,
                    source,
                    NUM_OBJECTIVES,
                    return_stats=True
                )

                runtime = (
                    time.perf_counter()
                    - start
                )

                pareto_labels = len(
                    labels[target]
                )

                generated = stats[
                    "generated_labels"
                ]

                pruned = stats[
                    "pruned_labels"
                ]

                if generated > 0:

                    rejection_rate = (
                        pruned
                        /
                        generated
                    )

                else:

                    rejection_rate = 0.0

                results.append({

                    "network_id":
                        network_id,

                    "query_id":
                        query_id,

                    "structure":
                        structure_name,

                    "source":
                        source,

                    "target":
                        target,

                    "num_nodes":
                        NUM_NODES,

                    "num_edges":
                        len(topology),

                    "num_objectives":
                        NUM_OBJECTIVES,

                    "rho_12":
                        observed_corr[0, 1],

                    "rho_13":
                        observed_corr[0, 2],

                    "rho_23":
                        observed_corr[1, 2],

                    "target_pareto_labels":
                        pareto_labels,

                    "generated_labels":
                        generated,

                    "kept_labels":
                        stats[
                            "kept_labels"
                        ],

                    "pruned_labels":
                        pruned,

                    "immediate_rejection_rate":
                        rejection_rate,

                    "dominance_checks":
                        stats[
                            "dominance_checks"
                        ],

                    "max_labels_per_node":
                        stats[
                            "max_labels_per_node"
                        ],

                    "runtime_seconds":
                        runtime
                })

    return (
        results,
        dependence_checks
    )


# ============================================================
# 10. Save CSV
# ============================================================

def save_csv(
    rows,
    filename
):

    script_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    output_dir = os.path.join(
        script_dir,
        "results"
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    path = os.path.join(
        output_dir,
        filename
    )

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=list(
                rows[0].keys()
            )
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        "Saved:",
        path
    )


# ============================================================
# 11. Manipulation summary
# ============================================================

def print_dependence_summary(
    checks
):

    print()
    print(
        "===== 3D DEPENDENCE MANIPULATION CHECK ====="
    )

    for structure in DEPENDENCE_STRUCTURES:

        subset = [
            row
            for row in checks
            if row["structure"]
            == structure
        ]

        r12 = np.mean([
            x["rho_12"]
            for x in subset
        ])

        r13 = np.mean([
            x["rho_13"]
            for x in subset
        ])

        r23 = np.mean([
            x["rho_23"]
            for x in subset
        ])

        print()
        print(structure)

        print(
            f"  mean rho12 = {r12:+.4f}"
        )

        print(
            f"  mean rho13 = {r13:+.4f}"
        )

        print(
            f"  mean rho23 = {r23:+.4f}"
        )


# ============================================================
# 12. Sanity check
# ============================================================

def sanity_check():

    print(
        "===== MATRIX VALIDATION ====="
    )

    for (
        name,
        matrix
    ) in DEPENDENCE_STRUCTURES.items():

        validate_correlation_matrix(
            matrix,
            name
        )

    print()
    print(
        "All correlation matrices are valid."
    )

    print()


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    sanity_check()

    (
        results,
        dependence_checks
    ) = run_experiment()

    save_csv(
        results,
        "experiment_02b_dependence_3d_raw.csv"
    )

    save_csv(
        dependence_checks,
        "experiment_02b_dependence_3d_check.csv"
    )

    print_dependence_summary(
        dependence_checks
    )

    expected = (
        NUM_NETWORKS
        *
        QUERIES_PER_NETWORK
        *
        len(
            DEPENDENCE_STRUCTURES
        )
    )

    print()
    print(
        "Total observations:",
        len(results)
    )

    print(
        "Expected observations:",
        expected
    )

    assert len(results) == expected

    print()
    print(
        "Experiment 2B completed successfully."
    )