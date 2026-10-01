from src.paths import PROJECT_ROOT, RESULTS_DIR as CANONICAL_RESULTS_DIR, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, result_path, project_path
import csv
import os
import random
import time

import numpy as np
from scipy.stats import norm

from src.graph import Graph
from src.mosp import mosp


# ============================================================
# Experiment 2A
# Effect of Pairwise Objective Correlation on MOSP
# ============================================================

CORRELATIONS = [
    -0.8,
    -0.4,
    0.0,
    0.4,
    0.8
]

NUM_OBJECTIVES = 2

NUM_NETWORKS = 50
QUERIES_PER_NETWORK = 10

NUM_NODES = 100
EDGE_PROBABILITY = 0.08

MIN_COST = 1
MAX_COST = 100

SEED = 42


# ============================================================
# 1. Generate topology
# ============================================================

def generate_topology(rng):
    """
    Generate one directed random graph topology.

    The same topology will be used across all
    correlation conditions for the same network.
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
# 2. Generate OD queries
# ============================================================

def generate_queries(rng):
    """
    Generate fixed OD pairs.

    The same OD pairs are used for every rho
    within the same network.
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
# 3. Generate common random base
# ============================================================

def generate_base_normals(
    num_edges,
    seed
):
    """
    Generate two independent standard-normal variables.

    The SAME base random variables are reused for
    all correlation conditions.

    This gives us a controlled paired experiment:
    rho changes, but the underlying random sample
    remains fixed.
    """

    rng = np.random.default_rng(seed)

    z1 = rng.standard_normal(
        num_edges
    )

    z2 = rng.standard_normal(
        num_edges
    )

    return z1, z2


# ============================================================
# 4. Create correlated Gaussian variables
# ============================================================

def create_correlated_normals(
    z1,
    z2,
    rho
):
    """
    Construct two correlated standard-normal variables.

    X1 = Z1

    X2 = rho * Z1
         + sqrt(1-rho^2) * Z2

    Corr(X1, X2) is approximately rho.
    """

    if not -1.0 <= rho <= 1.0:
        raise ValueError(
            "rho must be between -1 and 1."
        )

    x1 = z1

    x2 = (
        rho * z1
        +
        np.sqrt(
            1.0 - rho ** 2
        ) * z2
    )

    return x1, x2


# ============================================================
# 5. Gaussian copula -> integer edge costs
# ============================================================

def normals_to_costs(
    x1,
    x2
):
    """
    Transform correlated Gaussian variables into
    approximately uniform integer costs from 1 to 100.

    Step 1:
        Normal CDF -> values in (0,1)

    Step 2:
        Map to integer costs 1,...,100
    """

    u1 = norm.cdf(x1)
    u2 = norm.cdf(x2)

    range_size = (
        MAX_COST
        - MIN_COST
        + 1
    )

    c1 = (
        MIN_COST
        +
        np.floor(
            u1 * range_size
        ).astype(int)
    )

    c2 = (
        MIN_COST
        +
        np.floor(
            u2 * range_size
        ).astype(int)
    )

    # Numerical safety
    c1 = np.clip(
        c1,
        MIN_COST,
        MAX_COST
    )

    c2 = np.clip(
        c2,
        MIN_COST,
        MAX_COST
    )

    return c1, c2


# ============================================================
# 6. Generate edge-cost dictionary
# ============================================================

def generate_correlated_costs(
    topology,
    z1,
    z2,
    rho
):
    """
    Generate correlated 2-dimensional costs
    for every edge.
    """

    x1, x2 = create_correlated_normals(
        z1,
        z2,
        rho
    )

    c1, c2 = normals_to_costs(
        x1,
        x2
    )

    edge_costs = {}

    for i, edge in enumerate(topology):

        edge_costs[edge] = (
            int(c1[i]),
            int(c2[i])
        )

    # ----------------------------------------
    # Observed Pearson correlation
    # ----------------------------------------

    observed_rho = np.corrcoef(
        c1,
        c2
    )[0, 1]

    return edge_costs, observed_rho


# ============================================================
# 7. Build graph
# ============================================================

def build_graph(
    topology,
    edge_costs
):
    """
    Build a 2-objective MOSP graph.
    """

    g = Graph()

    for node in range(NUM_NODES):
        g.add_node(node)

    for u, v in topology:

        g.add_edge(
            u,
            v,
            edge_costs[(u, v)]
        )

    return g


# ============================================================
# 8. Run Experiment 2A
# ============================================================

def run_experiment():

    master_rng = random.Random(
        SEED
    )

    results = []

    # Store manipulation-check results
    correlation_checks = []

    for network_id in range(
        NUM_NETWORKS
    ):

        print(
            f"Network "
            f"{network_id + 1}/"
            f"{NUM_NETWORKS}"
        )

        # ----------------------------------------
        # Same topology across rho conditions
        # ----------------------------------------

        topology = generate_topology(
            master_rng
        )

        # ----------------------------------------
        # Same OD pairs across rho conditions
        # ----------------------------------------

        queries = generate_queries(
            master_rng
        )

        # ----------------------------------------
        # Same underlying random numbers
        # across rho conditions
        # ----------------------------------------

        base_seed = master_rng.randint(
            0,
            10**9
        )

        z1, z2 = generate_base_normals(
            len(topology),
            base_seed
        )

        # ----------------------------------------
        # Test rho conditions
        # ----------------------------------------

        for rho in CORRELATIONS:

            edge_costs, observed_rho = (
                generate_correlated_costs(
                    topology,
                    z1,
                    z2,
                    rho
                )
            )

            correlation_checks.append({
                "network_id":
                    network_id,

                "target_rho":
                    rho,

                "observed_rho":
                    observed_rho,

                "num_edges":
                    len(topology)
            })

            graph = build_graph(
                topology,
                edge_costs
            )

            # ------------------------------------
            # Same 10 OD queries
            # ------------------------------------

            for query_id, (
                source,
                target
            ) in enumerate(queries):

                start_time = (
                    time.perf_counter()
                )

                labels, stats = mosp(
                    graph,
                    source,
                    NUM_OBJECTIVES,
                    return_stats=True
                )

                runtime = (
                    time.perf_counter()
                    - start_time
                )

                target_pareto_labels = len(
                    labels[target]
                )

                generated = stats[
                    "generated_labels"
                ]

                pruned = stats[
                    "pruned_labels"
                ]

                # Current implementation:
                # "pruned_labels" means new candidates
                # immediately rejected on insertion.
                if generated > 0:
                    rejection_rate = (
                        pruned / generated
                    )
                else:
                    rejection_rate = 0.0

                results.append({

                    "network_id":
                        network_id,

                    "query_id":
                        query_id,

                    "target_rho":
                        rho,

                    "observed_rho":
                        observed_rho,

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

                    "runtime_seconds":
                        runtime,

                    "target_pareto_labels":
                        target_pareto_labels,

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
                        ]
                })

    return (
        results,
        correlation_checks
    )


# ============================================================
# 9. Save raw experimental results
# ============================================================

def save_results(results):

    output_dir = CANONICAL_RESULTS_DIR / 'experiment_02a'

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    output_file = os.path.join(
        output_dir,
        "experiment_02a_correlation_raw.csv"
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
        "Raw results saved to:",
        output_file
    )


# ============================================================
# 10. Save manipulation check
# ============================================================

def save_correlation_checks(
    correlation_checks
):

    output_dir = CANONICAL_RESULTS_DIR / 'experiment_02a'

    output_file = os.path.join(
        output_dir,
        "experiment_02a_correlation_check.csv"
    )

    fieldnames = list(
        correlation_checks[0].keys()
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
            correlation_checks
        )

    print(
        "Correlation check saved to:",
        output_file
    )


# ============================================================
# 11. Print manipulation-check summary
# ============================================================

def print_correlation_summary(
    correlation_checks
):

    print()
    print(
        "===== CORRELATION MANIPULATION CHECK ====="
    )

    for target_rho in CORRELATIONS:

        observed = [
            row["observed_rho"]
            for row in correlation_checks
            if row["target_rho"]
            == target_rho
        ]

        mean_rho = np.mean(
            observed
        )

        std_rho = np.std(
            observed,
            ddof=1
        )

        print(
            f"Target rho = {target_rho:+.1f} "
            f"| Mean observed rho = "
            f"{mean_rho:+.4f} "
            f"| SD = {std_rho:.4f}"
        )


# ============================================================
# 12. Sanity check
# ============================================================

def sanity_check():

    print(
        "===== EXPERIMENT 2A SANITY CHECK ====="
    )

    rng = random.Random(
        SEED
    )

    topology = generate_topology(
        rng
    )

    z1, z2 = generate_base_normals(
        len(topology),
        seed=12345
    )

    for rho in CORRELATIONS:

        _, observed_rho = (
            generate_correlated_costs(
                topology,
                z1,
                z2,
                rho
            )
        )

        print(
            f"Target rho = {rho:+.1f} "
            f"-> Observed rho = "
            f"{observed_rho:+.4f}"
        )

    print(
        "======================================"
    )

    print()


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    from experiments.synthetic._cli import maybe_run_smoke_test
    maybe_run_smoke_test("experiment_02a")

    # ----------------------------------------
    # Verify correlation generation first
    # ----------------------------------------

    sanity_check()

    # ----------------------------------------
    # Run experiment
    # ----------------------------------------

    (
        results,
        correlation_checks
    ) = run_experiment()

    # ----------------------------------------
    # Save
    # ----------------------------------------

    save_results(
        results
    )

    save_correlation_checks(
        correlation_checks
    )

    # ----------------------------------------
    # Manipulation check
    # ----------------------------------------

    print_correlation_summary(
        correlation_checks
    )

    # ----------------------------------------
    # Verify number of observations
    # ----------------------------------------

    expected = (
        NUM_NETWORKS
        * QUERIES_PER_NETWORK
        * len(CORRELATIONS)
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
        "Experiment 2A completed successfully."
    )