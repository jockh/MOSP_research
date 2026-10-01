import csv
import os
import random
import time

import numpy as np

from src.graph import Graph
from src.mosp import mosp


# ============================================================
# Experiment 3A
# Effect of Number of Alternative Routes on MOSP
# ============================================================

SEED = 20260929

NUM_REPLICATES = 500

NUM_OBJECTIVES = 3

ROUTE_COUNTS = [
    2,
    4,
    8,
    16
]

MAX_ROUTES = max(ROUTE_COUNTS)

# Every S-T route contains:
#
# 4 common prefix edges
# + 8 branch edges
# + 4 common suffix edges
#
# = 16 edges

PREFIX_EDGES = 4
BRANCH_EDGES = 8
SUFFIX_EDGES = 4

MIN_COST = 1
MAX_COST = 100


OUTPUT_FILE = os.path.join(
    "experiments",
    "results",
    "experiment_03a_route_quantity_raw.csv"
)

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)


# ============================================================
# 1. Build master topology
# ============================================================

def create_master_topology():
    """
    Create the maximum K = 16 corridor network.

    All routes:
        S
        -> common prefix
        -> SPLIT
        -> independent branch
        -> MERGE
        -> common suffix
        -> T

    Smaller K conditions simply use the first K branches.
    """

    source = "S"
    target = "T"

    common_prefix = []
    common_suffix = []
    branches = []

    # --------------------------------------------------------
    # Common prefix
    # --------------------------------------------------------

    current = source

    # PREFIX_EDGES = 4:
    #
    # S -> P1 -> P2 -> P3 -> SPLIT

    for i in range(1, PREFIX_EDGES):

        next_node = f"P{i}"

        common_prefix.append(
            (current, next_node)
        )

        current = next_node

    split_node = "SPLIT"

    common_prefix.append(
        (current, split_node)
    )


    # --------------------------------------------------------
    # K independent branches
    # --------------------------------------------------------

    merge_node = "MERGE"

    for route_id in range(MAX_ROUTES):

        route_edges = []

        current = split_node

        # BRANCH_EDGES = 8:
        #
        # SPLIT
        # -> B_r_1
        # -> ...
        # -> B_r_7
        # -> MERGE

        for j in range(1, BRANCH_EDGES):

            next_node = (
                f"B{route_id}_{j}"
            )

            route_edges.append(
                (current, next_node)
            )

            current = next_node

        route_edges.append(
            (current, merge_node)
        )

        branches.append(
            route_edges
        )


    # --------------------------------------------------------
    # Common suffix
    # --------------------------------------------------------

    current = merge_node

    for i in range(1, SUFFIX_EDGES):

        next_node = f"Q{i}"

        common_suffix.append(
            (current, next_node)
        )

        current = next_node

    common_suffix.append(
        (current, target)
    )


    return {
        "source": source,
        "target": target,
        "prefix": common_prefix,
        "branches": branches,
        "suffix": common_suffix
    }


# ============================================================
# 2. Generate edge costs
# ============================================================

def generate_master_costs(
    topology,
    rng
):
    """
    Generate independent 3-objective edge costs.

    The same master cost realization is reused
    across K = 2, 4, 8, 16 within one replicate.

    Therefore Experiment 3A uses a paired design.
    """

    edge_costs = {}

    all_edges = []

    all_edges.extend(
        topology["prefix"]
    )

    for branch in topology["branches"]:

        all_edges.extend(
            branch
        )

    all_edges.extend(
        topology["suffix"]
    )


    for edge in all_edges:

        costs = tuple(
            rng.randint(
                MIN_COST,
                MAX_COST
            )
            for _ in range(
                NUM_OBJECTIVES
            )
        )

        edge_costs[edge] = costs


    return edge_costs


# ============================================================
# 3. Build graph for a given K
# ============================================================

def build_graph(
    topology,
    edge_costs,
    route_count
):

    g = Graph()

    selected_edges = []

    # Common prefix
    selected_edges.extend(
        topology["prefix"]
    )

    # First K branches
    for route_id in range(route_count):

        selected_edges.extend(
            topology["branches"][route_id]
        )

    # Common suffix
    selected_edges.extend(
        topology["suffix"]
    )


    # Add nodes explicitly
    nodes = set()

    for u, v in selected_edges:

        nodes.add(u)
        nodes.add(v)

    for node in nodes:

        g.add_node(node)


    # Add directed edges
    for u, v in selected_edges:

        g.add_edge(
            u,
            v,
            edge_costs[(u, v)]
        )


    return (
        g,
        nodes,
        selected_edges
    )


# ============================================================
# 4. Route-structure measures
# ============================================================

def calculate_route_structure(
    route_count
):
    """
    Because the topology is explicitly controlled,
    the number of simple S-T routes is exactly K.

    All route pairs have the same overlap/diversity.
    """

    common_edges = (
        PREFIX_EDGES
        +
        SUFFIX_EDGES
    )

    # For two different routes:
    #
    # intersection = common edges
    #
    # union =
    # common edges
    # + branch A
    # + branch B

    union_edges = (
        common_edges
        +
        2 * BRANCH_EDGES
    )

    pairwise_overlap = (
        common_edges
        /
        union_edges
    )

    pairwise_diversity = (
        1.0
        -
        pairwise_overlap
    )

    route_length = (
        PREFIX_EDGES
        +
        BRANCH_EDGES
        +
        SUFFIX_EDGES
    )

    return {
        "route_count": route_count,
        "route_length": route_length,
        "pairwise_overlap": pairwise_overlap,
        "pairwise_diversity": pairwise_diversity
    }


# ============================================================
# 5. Cost-correlation check
# ============================================================

def calculate_cost_correlations(
    selected_edges,
    edge_costs
):

    matrix = np.array(
        [
            edge_costs[edge]
            for edge in selected_edges
        ],
        dtype=float
    )

    corr = np.corrcoef(
        matrix,
        rowvar=False
    )

    return {
        "rho_12": corr[0, 1],
        "rho_13": corr[0, 2],
        "rho_23": corr[1, 2]
    }


# ============================================================
# 6. Run experiment
# ============================================================

def run_experiment():

    topology = (
        create_master_topology()
    )

    results = []


    print(
        "===== EXPERIMENT 3A ====="
    )

    print(
        "Effect of Alternative Route Quantity"
    )

    print()

    print(
        "Route counts:",
        ROUTE_COUNTS
    )

    print(
        "Replicates per condition:",
        NUM_REPLICATES
    )

    print(
        "Total MOSP runs:",
        NUM_REPLICATES
        * len(ROUTE_COUNTS)
    )

    print()


    # --------------------------------------------------------
    # Replicates
    # --------------------------------------------------------

    for replicate_id in range(
        NUM_REPLICATES
    ):

        # Each replicate has its own random costs.
        #
        # All K conditions within this replicate
        # use the SAME master costs.

        rng = random.Random(
            SEED + replicate_id
        )

        edge_costs = (
            generate_master_costs(
                topology,
                rng
            )
        )


        # ----------------------------------------------------
        # Route-count conditions
        # ----------------------------------------------------

        for route_count in ROUTE_COUNTS:

            (
                graph,
                nodes,
                selected_edges
            ) = build_graph(
                topology,
                edge_costs,
                route_count
            )


            source = (
                topology["source"]
            )

            target = (
                topology["target"]
            )


            # ------------------------------------------------
            # MOSP
            # ------------------------------------------------

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
                -
                start_time
            )


            # ------------------------------------------------
            # Main outcome variables
            # ------------------------------------------------

            pareto_labels = len(
                labels[target]
            )

            generated_labels = (
                stats[
                    "generated_labels"
                ]
            )

            dominance_checks = (
                stats[
                    "dominance_checks"
                ]
            )


            if generated_labels > 0:

                comparisons_per_generated_label = (
                    dominance_checks
                    /
                    generated_labels
                )

            else:

                comparisons_per_generated_label = 0.0


            # ------------------------------------------------
            # Manipulation checks
            # ------------------------------------------------

            route_structure = (
                calculate_route_structure(
                    route_count
                )
            )

            correlations = (
                calculate_cost_correlations(
                    selected_edges,
                    edge_costs
                )
            )


            # ------------------------------------------------
            # Save one observation
            # ------------------------------------------------

            result = {

                "replicate_id":
                    replicate_id,

                "objectives":
                    NUM_OBJECTIVES,

                "route_count":
                    route_count,

                "route_length":
                    route_structure[
                        "route_length"
                    ],

                "pairwise_overlap":
                    route_structure[
                        "pairwise_overlap"
                    ],

                "pairwise_diversity":
                    route_structure[
                        "pairwise_diversity"
                    ],

                "num_nodes":
                    len(nodes),

                "num_edges":
                    len(selected_edges),

                "rho_12":
                    correlations[
                        "rho_12"
                    ],

                "rho_13":
                    correlations[
                        "rho_13"
                    ],

                "rho_23":
                    correlations[
                        "rho_23"
                    ],

                "target_pareto_labels":
                    pareto_labels,

                "generated_labels":
                    generated_labels,

                "kept_labels":
                    stats[
                        "kept_labels"
                    ],

                "pruned_labels":
                    stats[
                        "pruned_labels"
                    ],

                "dominance_checks":
                    dominance_checks,

                "comparisons_per_generated_label":
                    comparisons_per_generated_label,

                "max_labels_per_node":
                    stats[
                        "max_labels_per_node"
                    ],

                "runtime_seconds":
                    runtime
            }

            results.append(
                result
            )


        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if (
            (replicate_id + 1)
            % 50
            == 0
        ):

            print(
                f"Completed "
                f"{replicate_id + 1}"
                f"/{NUM_REPLICATES} "
                f"replicates"
            )


    return results


# ============================================================
# 7. Save CSV
# ============================================================

def save_results(
    results
):

    if not results:

        return


    fieldnames = list(
        results[0].keys()
    )


    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            results
        )


    print()

    print(
        "Results saved to:"
    )

    print(
        OUTPUT_FILE
    )


# ============================================================
# 8. Quick summary
# ============================================================

def print_summary(
    results
):

    import pandas as pd

    df = pd.DataFrame(
        results
    )


    print()

    print(
        "===== MANIPULATION CHECK ====="
    )


    manipulation = (
        df.groupby(
            "route_count"
        )
        .agg(

            observations=(
                "route_count",
                "size"
            ),

            route_length=(
                "route_length",
                "mean"
            ),

            pairwise_diversity=(
                "pairwise_diversity",
                "mean"
            ),

            rho_12=(
                "rho_12",
                "mean"
            ),

            rho_13=(
                "rho_13",
                "mean"
            ),

            rho_23=(
                "rho_23",
                "mean"
            )
        )
    )

    print(
        manipulation.round(4)
    )


    print()

    print(
        "===== MOSP SUMMARY ====="
    )


    summary = (
        df.groupby(
            "route_count"
        )
        .agg(

            pareto_labels=(
                "target_pareto_labels",
                "mean"
            ),

            generated=(
                "generated_labels",
                "mean"
            ),

            comparisons_per_label=(
                "comparisons_per_generated_label",
                "mean"
            ),

            dominance_checks=(
                "dominance_checks",
                "mean"
            ),

            max_labels_per_node=(
                "max_labels_per_node",
                "mean"
            ),

            runtime=(
                "runtime_seconds",
                "mean"
            )
        )
    )

    print(
        summary.round(6)
    )


    # --------------------------------------------------------
    # Relative to K = 2
    # --------------------------------------------------------

    print()

    print(
        "===== RELATIVE TO K = 2 ====="
    )

    baseline = (
        summary.loc[2]
    )

    relative = (
        summary
        /
        baseline
    )

    print(
        relative.round(3)
    )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    results = (
        run_experiment()
    )

    save_results(
        results
    )

    print_summary(
        results
    )

    print()

    print(
        "Experiment 3A completed successfully."
    )