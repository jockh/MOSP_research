import os
import sys
import time

import numpy as np
import pandas as pd


# ============================================================
# Experiment 3B
# Effect of Route Overlap Position on MOSP Search Workload
#
# Research idea:
#
# Keep the following conditions identical:
#   - number of objectives
#   - number of routes
#   - route length
#   - overlap ratio
#   - number of nodes
#   - number of edges
#   - edge-cost vectors
#   - complete route cost vectors
#   - final Pareto solution set
#
# Change only:
#   - where the shared segment occurs
#
# Two structures:
#
# PREFIX:
#
#                 / route 1 ---- T
# S -- shared ---<  route 2 ---- T
#                 \ route 3 ---- T
#
#
# SUFFIX:
#
#      route 1 --\
#      route 2 ---+-- shared -- T
# S -- route 3 --/
#
#
# ============================================================


# ============================================================
# 0. Project path
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        CURRENT_DIR,
        ".."
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT
    )


# ============================================================
# Import MOSP implementation
# ============================================================

from src.graph import Graph
from src.mosp import mosp


# ============================================================
# 1. Experiment settings
# ============================================================

BASE_SEED = 20260929

# Number of objectives
OBJECTIVES = 3

# Number of alternative routes
ROUTE_COUNT = 8

# Number of edges in every complete S-T route
ROUTE_LENGTH = 16

# Shared segment lengths
#
# 4 / 16  = 25%
# 8 / 16  = 50%
# 12 / 16 = 75%
#
SHARED_LENGTHS = [
    4,
    8,
    12
]

# Position of the shared segment
STRUCTURES = [
    "prefix",
    "suffix"
]

# Number of paired replications
N_REPLICATES = 500


# ============================================================
# 2. Output file
# ============================================================

OUTPUT_DIR = os.path.join(
    "experiments",
    "results"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "experiment_03b_overlap_position_raw.csv"
)


# ============================================================
# 3. Utility: add edge
# ============================================================

def add_edge(
    graph,
    u,
    v,
    costs
):

    costs = tuple(
        float(x)
        for x in costs
    )

    graph.add_edge(
        u,
        v,
        costs
    )


# ============================================================
# 4. Generate paired cost bank
# ============================================================

def generate_cost_bank(
    rng,
    route_count,
    route_length,
    shared_length,
    objectives
):

    """
    Generate one common set of edge costs.

    The same costs will be used for both
    PREFIX and SUFFIX structures.

    Therefore, for the same replicate:

        route r cost under PREFIX
        =
        route r cost under SUFFIX

    The only difference is the position
    of the shared segment.
    """

    unique_length = (
        route_length
        - shared_length
    )

    # --------------------------------------------------------
    # Shared segment costs
    # --------------------------------------------------------

    shared_costs = rng.integers(
        low=1,
        high=101,
        size=(
            shared_length,
            objectives
        )
    ).astype(float)

    # --------------------------------------------------------
    # Route-specific costs
    # --------------------------------------------------------

    unique_costs = rng.integers(
        low=1,
        high=101,
        size=(
            route_count,
            unique_length,
            objectives
        )
    ).astype(float)

    return (
        shared_costs,
        unique_costs
    )


# ============================================================
# 5. Build PREFIX-overlap network
# ============================================================

def build_prefix_graph(
    shared_costs,
    unique_costs
):

    """
    Shared segment occurs BEFORE routes diverge.

    Example:

    S -- C1 -- C2 -- C3
                       |
                       |-- R0 -- ... -- T
                       |
                       |-- R1 -- ... -- T
                       |
                       |-- R2 -- ... -- T

    All routes share the first part.
    """

    graph = Graph()

    source = "S"
    target = "T"

    route_count = (
        unique_costs.shape[0]
    )

    shared_length = (
        shared_costs.shape[0]
    )

    unique_length = (
        unique_costs.shape[1]
    )

    node_set = {
        source,
        target
    }

    edge_count = 0


    # ========================================================
    # Shared prefix
    # ========================================================

    current = source

    for j in range(
        shared_length
    ):

        next_node = (
            f"C_{j + 1}"
        )

        add_edge(
            graph,
            current,
            next_node,
            shared_costs[j]
        )

        node_set.add(
            next_node
        )

        edge_count += 1

        current = next_node


    # Node where routes diverge
    branch_node = current


    # ========================================================
    # Route-specific suffixes
    # ========================================================

    for r in range(
        route_count
    ):

        current = branch_node

        for j in range(
            unique_length
        ):

            # Last edge goes directly to T
            if (
                j
                == unique_length - 1
            ):

                next_node = target

            else:

                next_node = (
                    f"R{r}_U{j + 1}"
                )

            add_edge(
                graph,
                current,
                next_node,
                unique_costs[r, j]
            )

            node_set.add(
                next_node
            )

            edge_count += 1

            current = next_node


    return (
        graph,
        source,
        target,
        len(node_set),
        edge_count
    )


# ============================================================
# 6. Build SUFFIX-overlap network
# ============================================================

def build_suffix_graph(
    shared_costs,
    unique_costs
):

    """
    Routes diverge first and merge later.

    Example:

          R0 -- ... --\
                       \
    S --- R1 -- ... ---- M -- C1 -- C2 -- T
                       /
          R2 -- ... --/

    All routes share the final part.

    IMPORTANT:

    The same shared_costs and unique_costs
    are used as in the PREFIX structure.

    Therefore complete route costs remain identical.
    """

    graph = Graph()

    source = "S"
    target = "T"

    route_count = (
        unique_costs.shape[0]
    )

    shared_length = (
        shared_costs.shape[0]
    )

    unique_length = (
        unique_costs.shape[1]
    )

    merge_node = "M"

    node_set = {
        source,
        target,
        merge_node
    }

    edge_count = 0


    # ========================================================
    # Route-specific prefixes
    # ========================================================

    for r in range(
        route_count
    ):

        current = source

        for j in range(
            unique_length
        ):

            # Last private edge reaches merge node
            if (
                j
                == unique_length - 1
            ):

                next_node = merge_node

            else:

                next_node = (
                    f"R{r}_U{j + 1}"
                )

            add_edge(
                graph,
                current,
                next_node,
                unique_costs[r, j]
            )

            node_set.add(
                next_node
            )

            edge_count += 1

            current = next_node


    # ========================================================
    # Shared suffix
    # ========================================================

    current = merge_node

    for j in range(
        shared_length
    ):

        # Last shared edge reaches target
        if (
            j
            == shared_length - 1
        ):

            next_node = target

        else:

            next_node = (
                f"C_{j + 1}"
            )

        add_edge(
            graph,
            current,
            next_node,
            shared_costs[j]
        )

        node_set.add(
            next_node
        )

        edge_count += 1

        current = next_node


    return (
        graph,
        source,
        target,
        len(node_set),
        edge_count
    )


# ============================================================
# 7. Calculate complete route cost vectors
# ============================================================

def calculate_route_costs(
    shared_costs,
    unique_costs
):

    """
    Calculate the complete cost vector of
    each S-T route.

    Because costs are additive:

        route cost
        =
        shared part
        +
        private part

    The order does not affect the final
    complete route cost.
    """

    shared_total = (
        shared_costs.sum(
            axis=0
        )
    )

    unique_total = (
        unique_costs.sum(
            axis=1
        )
    )

    route_costs = (
        unique_total
        + shared_total
    )

    return route_costs


# ============================================================
# 8. Reference Pareto filtering
# ============================================================

def reference_pareto_count(
    route_costs
):

    """
    Directly compare the complete cost vectors
    of the K alternative routes.

    This provides a simple correctness check
    for the MOSP result.
    """

    # Remove exact duplicate cost vectors
    unique_costs = np.unique(
        route_costs,
        axis=0
    )

    n = len(
        unique_costs
    )

    pareto = np.ones(
        n,
        dtype=bool
    )

    for i in range(
        n
    ):

        for j in range(
            n
        ):

            if i == j:
                continue

            candidate = (
                unique_costs[j]
            )

            current = (
                unique_costs[i]
            )

            dominates = (
                np.all(
                    candidate
                    <= current
                )
                and
                np.any(
                    candidate
                    < current
                )
            )

            if dominates:

                pareto[i] = False

                break


    return int(
        pareto.sum()
    )


# ============================================================
# 9. Calculate cost correlations
# ============================================================

def calculate_cost_correlations(
    shared_costs,
    unique_costs
):

    """
    Calculate correlations among the
    three edge-cost objectives.

    PREFIX and SUFFIX use exactly the
    same cost vectors, so their rho values
    must be identical within each pair.
    """

    all_costs = np.vstack(
        [
            shared_costs,

            unique_costs.reshape(
                -1,
                OBJECTIVES
            )
        ]
    )

    corr = np.corrcoef(
        all_costs,
        rowvar=False
    )

    rho_12 = float(
        corr[0, 1]
    )

    rho_13 = float(
        corr[0, 2]
    )

    rho_23 = float(
        corr[1, 2]
    )

    return (
        rho_12,
        rho_13,
        rho_23
    )


# ============================================================
# 10. Read statistics safely
# ============================================================

def get_stat(
    stats,
    names,
    default=np.nan
):

    if isinstance(
        names,
        str
    ):
        names = [
            names
        ]

    for name in names:

        # ----------------------------------------------------
        # stats is dictionary
        # ----------------------------------------------------

        if isinstance(
            stats,
            dict
        ):

            if name in stats:

                return stats[
                    name
                ]

        # ----------------------------------------------------
        # stats is object
        # ----------------------------------------------------

        else:

            if hasattr(
                stats,
                name
            ):

                return getattr(
                    stats,
                    name
                )

    return default


# ============================================================
# 11. Count target Pareto labels
# ============================================================

def get_target_label_count(
    labels,
    target
):

    """
    Supports two possible MOSP result formats.

    Format A:

        labels[target]

    Format B:

        labels itself is already
        the target label list
    """

    if isinstance(
        labels,
        dict
    ):

        if target not in labels:

            return 0

        target_labels = (
            labels[target]
        )

    else:

        target_labels = labels


    return len(
        target_labels
    )


# ============================================================
# 12. Run one MOSP case
# ============================================================


# ============================================================
# 12. Run one MOSP case
# ============================================================

def run_mosp_case(
    graph,
    source,
    target,
    num_objectives
):

    """
    Run one MOSP search.

    mosp() interface:

        mosp(
            graph,
            source,
            num_objectives,
            return_stats=True
        )

    When return_stats=True:

        labels, stats = mosp(...)

    labels[node] contains the non-dominated
    labels currently retained at that node.
    """

    # ========================================================
    # Run MOSP
    # ========================================================

    start_time = time.perf_counter()

    labels, stats = mosp(
        graph,
        source,
        num_objectives,
        return_stats=True
    )

    runtime = (
        time.perf_counter()
        - start_time
    )


    # ========================================================
    # Pareto labels at target
    # ========================================================

    if target in labels:

        target_labels = [
            label
            for label in labels[target]
            if getattr(
                label,
                "active",
                True
            )
        ]

        target_pareto_labels = len(
            target_labels
        )

    else:

        target_pareto_labels = 0


    # ========================================================
    # Read MOSP statistics
    # ========================================================

    generated_labels = stats.get(
        "generated_labels",
        np.nan
    )

    kept_labels = stats.get(
        "kept_labels",
        np.nan
    )

    pruned_labels = stats.get(
        "pruned_labels",
        np.nan
    )

    dominance_checks = stats.get(
        "dominance_checks",
        np.nan
    )

    max_labels_per_node = stats.get(
        "max_labels_per_node",
        np.nan
    )


    # ========================================================
    # Comparisons per generated label
    # ========================================================

    if (
        not pd.isna(generated_labels)
        and generated_labels > 0
        and not pd.isna(dominance_checks)
    ):

        comparisons_per_generated_label = (
            dominance_checks
            /
            generated_labels
        )

    else:

        comparisons_per_generated_label = (
            np.nan
        )


    # ========================================================
    # Pruning rate
    # ========================================================

    if (
        not pd.isna(generated_labels)
        and generated_labels > 0
        and not pd.isna(pruned_labels)
    ):

        pruning_rate = (
            pruned_labels
            /
            generated_labels
        )

    else:

        pruning_rate = (
            np.nan
        )


    # ========================================================
    # Return experiment metrics
    # ========================================================

    return {

        "target_pareto_labels":
            target_pareto_labels,

        "generated_labels":
            generated_labels,

        "kept_labels":
            kept_labels,

        "pruned_labels":
            pruned_labels,

        "dominance_checks":
            dominance_checks,

        "comparisons_per_generated_label":
            comparisons_per_generated_label,

        "max_labels_per_node":
            max_labels_per_node,

        "pruning_rate":
            pruning_rate,

        "runtime_seconds":
            runtime
    }


# ============================================================
# 13. Main experiment
# ============================================================

def main():

    rows = []


    total_cases = (
        len(
            SHARED_LENGTHS
        )
        *
        len(
            STRUCTURES
        )
        *
        N_REPLICATES
    )


    completed = 0


    # ========================================================
    # Print experiment settings
    # ========================================================

    print(
        "=" * 70
    )

    print(
        "EXPERIMENT 3B"
    )

    print(
        "ROUTE OVERLAP POSITION AND MOSP SEARCH WORKLOAD"
    )

    print(
        "=" * 70
    )

    print(
        f"Objectives      : {OBJECTIVES}"
    )

    print(
        f"Route count     : {ROUTE_COUNT}"
    )

    print(
        f"Route length    : {ROUTE_LENGTH}"
    )

    print(
        f"Shared lengths  : {SHARED_LENGTHS}"
    )

    print(
        f"Structures      : {STRUCTURES}"
    )

    print(
        f"Replicates      : {N_REPLICATES}"
    )

    print(
        f"Total cases     : {total_cases}"
    )

    print()


    # ========================================================
    # Different overlap levels
    # ========================================================

    for shared_length in (
        SHARED_LENGTHS
    ):

        pairwise_overlap = (
            shared_length
            /
            ROUTE_LENGTH
        )

        pairwise_diversity = (
            1.0
            -
            pairwise_overlap
        )

        unique_length = (
            ROUTE_LENGTH
            -
            shared_length
        )


        print(
            "-" * 70
        )

        print(
            f"Shared length = "
            f"{shared_length}"
        )

        print(
            f"Pairwise overlap = "
            f"{pairwise_overlap:.2f}"
        )

        print(
            f"Pairwise diversity = "
            f"{pairwise_diversity:.2f}"
        )

        print(
            "-" * 70
        )


        # ====================================================
        # Replications
        # ====================================================

        for replicate_id in range(
            N_REPLICATES
        ):

            # =================================================
            # Deterministic paired seed
            # =================================================

            case_seed = (
                BASE_SEED
                +
                shared_length
                * 100000
                +
                replicate_id
            )

            rng = (
                np.random.default_rng(
                    case_seed
                )
            )


            # =================================================
            # Generate costs ONCE
            #
            # PREFIX and SUFFIX use the exact same costs.
            # =================================================

            (
                shared_costs,
                unique_costs
            ) = generate_cost_bank(

                rng=rng,

                route_count=(
                    ROUTE_COUNT
                ),

                route_length=(
                    ROUTE_LENGTH
                ),

                shared_length=(
                    shared_length
                ),

                objectives=(
                    OBJECTIVES
                )
            )


            # =================================================
            # Complete route costs
            # =================================================

            route_costs = (
                calculate_route_costs(
                    shared_costs,
                    unique_costs
                )
            )


            # =================================================
            # Reference Pareto count
            # =================================================

            reference_pareto = (
                reference_pareto_count(
                    route_costs
                )
            )


            # =================================================
            # Cost correlations
            # =================================================

            (
                rho_12,
                rho_13,
                rho_23
            ) = calculate_cost_correlations(
                shared_costs,
                unique_costs
            )


            # =================================================
            # Store paired results for checks
            # =================================================

            paired_results = {}


            # =================================================
            # PREFIX / SUFFIX
            # =================================================

            for structure in (
                STRUCTURES
            ):

                # =============================================
                # Build graph
                # =============================================

                if structure == "prefix":

                    (
                        graph,
                        source,
                        target,
                        num_nodes,
                        num_edges
                    ) = build_prefix_graph(
                        shared_costs,
                        unique_costs
                    )


                elif structure == "suffix":

                    (
                        graph,
                        source,
                        target,
                        num_nodes,
                        num_edges
                    ) = build_suffix_graph(
                        shared_costs,
                        unique_costs
                    )


                else:

                    raise ValueError(
                        f"Unknown structure: "
                        f"{structure}"
                    )


                # =============================================
                # Run MOSP
                #
                # FIXED:
                #
                # mosp(graph, source, OBJECTIVES)
                #
                # instead of
                #
                # mosp(graph, source, target)
                # =============================================

                metrics = run_mosp_case(
                    graph,
                    source,
                    target,
                    OBJECTIVES
                )


                # =============================================
                # Correctness check
                # =============================================

                if (
                    metrics[
                        "target_pareto_labels"
                    ]
                    !=
                    reference_pareto
                ):

                    print()
                    print(
                        "=" * 70
                    )

                    print(
                        "PARETO COUNT MISMATCH"
                    )

                    print(
                        "=" * 70
                    )

                    print(
                        "shared_length:",
                        shared_length
                    )

                    print(
                        "replicate:",
                        replicate_id
                    )

                    print(
                        "structure:",
                        structure
                    )

                    print(
                        "MOSP Pareto labels:",
                        metrics[
                            "target_pareto_labels"
                        ]
                    )

                    print(
                        "Reference Pareto labels:",
                        reference_pareto
                    )

                    print(
                        "Route costs:"
                    )

                    print(
                        route_costs
                    )

                    raise RuntimeError(
                        "Pareto count mismatch."
                    )


                # =============================================
                # Store paired Pareto result
                # =============================================

                paired_results[
                    structure
                ] = {
                    "pareto":
                        metrics[
                            "target_pareto_labels"
                        ],

                    "nodes":
                        num_nodes,

                    "edges":
                        num_edges
                }


                # =============================================
                # Save raw observation
                # =============================================

                row = {

                    "replicate_id":
                        replicate_id,

                    "case_seed":
                        case_seed,

                    "objectives":
                        OBJECTIVES,

                    "structure":
                        structure,

                    "route_count":
                        ROUTE_COUNT,

                    "route_length":
                        ROUTE_LENGTH,

                    "shared_length":
                        shared_length,

                    "unique_length":
                        unique_length,

                    "pairwise_overlap":
                        pairwise_overlap,

                    "pairwise_diversity":
                        pairwise_diversity,

                    "num_nodes":
                        num_nodes,

                    "num_edges":
                        num_edges,

                    "rho_12":
                        rho_12,

                    "rho_13":
                        rho_13,

                    "rho_23":
                        rho_23,

                    "reference_pareto_labels":
                        reference_pareto,

                    "target_pareto_labels":
                        metrics[
                            "target_pareto_labels"
                        ],

                    "generated_labels":
                        metrics[
                            "generated_labels"
                        ],

                    "kept_labels":
                        metrics[
                            "kept_labels"
                        ],

                    "pruned_labels":
                        metrics[
                            "pruned_labels"
                        ],

                    "dominance_checks":
                        metrics[
                            "dominance_checks"
                        ],

                    "comparisons_per_generated_label":
                        metrics[
                            "comparisons_per_generated_label"
                        ],

                    "max_labels_per_node":
                        metrics[
                            "max_labels_per_node"
                        ],

                    "pruning_rate":
                        metrics[
                            "pruning_rate"
                        ],

                    "runtime_seconds":
                        metrics[
                            "runtime_seconds"
                        ]
                }


                rows.append(
                    row
                )


                completed += 1


                # =============================================
                # Progress
                # =============================================

                if (
                    completed % 100
                    == 0
                ):

                    print(
                        f"Completed "
                        f"{completed}"
                        f"/"
                        f"{total_cases}"
                    )


            # =================================================
            # Paired-design checks
            # =================================================

            # Final Pareto count must be identical
            if (
                paired_results[
                    "prefix"
                ][
                    "pareto"
                ]
                !=
                paired_results[
                    "suffix"
                ][
                    "pareto"
                ]
            ):

                raise RuntimeError(
                    "\n"
                    "Prefix and suffix produced "
                    "different final Pareto counts.\n"
                )


            # Number of nodes must be identical
            if (
                paired_results[
                    "prefix"
                ][
                    "nodes"
                ]
                !=
                paired_results[
                    "suffix"
                ][
                    "nodes"
                ]
            ):

                raise RuntimeError(
                    "\n"
                    "Prefix and suffix have "
                    "different numbers of nodes.\n"
                )


            # Number of edges must be identical
            if (
                paired_results[
                    "prefix"
                ][
                    "edges"
                ]
                !=
                paired_results[
                    "suffix"
                ][
                    "edges"
                ]
            ):

                raise RuntimeError(
                    "\n"
                    "Prefix and suffix have "
                    "different numbers of edges.\n"
                )


    # ========================================================
    # 14. Create DataFrame
    # ========================================================

    df = pd.DataFrame(
        rows
    )


    # ========================================================
    # 15. Save raw data
    # ========================================================

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    # ========================================================
    # 16. Data checks
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "EXPERIMENT 3B DATA CHECK"
    )

    print(
        "=" * 70
    )

    print(
        "Total observations:",
        len(df)
    )

    print()

    print(
        "Columns:"
    )

    print(
        df.columns.tolist()
    )

    print()

    print(
        "Missing values:"
    )

    print(
        df.isna().sum()
    )


    # ========================================================
    # 17. Observations per condition
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "OBSERVATIONS PER CONDITION"
    )

    print(
        "=" * 70
    )

    condition_counts = (
        df.groupby(
            [
                "pairwise_overlap",
                "structure"
            ]
        )
        .size()
    )

    print(
        condition_counts
    )


    # ========================================================
    # 18. Experimental control check
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "EXPERIMENTAL CONTROL CHECK"
    )

    print(
        "=" * 70
    )


    control_summary = (
        df.groupby(
            [
                "pairwise_overlap",
                "structure"
            ]
        )[
            [
                "route_count",
                "route_length",
                "num_nodes",
                "num_edges",
                "rho_12",
                "rho_13",
                "rho_23",
                "target_pareto_labels"
            ]
        ]
        .mean()
    )

    print(
        control_summary.round(4)
    )


    # ========================================================
    # 19. Main workload summary
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "MAIN WORKLOAD SUMMARY"
    )

    print(
        "=" * 70
    )


    workload_summary = (
        df.groupby(
            [
                "pairwise_overlap",
                "structure"
            ]
        )[
            [
                "target_pareto_labels",
                "generated_labels",
                "dominance_checks",
                "comparisons_per_generated_label",
                "max_labels_per_node",
                "pruning_rate",
                "runtime_seconds"
            ]
        ]
        .mean()
    )

    print(
        workload_summary.round(6)
    )


    # ========================================================
    # 20. Prefix vs suffix paired differences
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "PREFIX VS SUFFIX PAIRED DIFFERENCES"
    )

    print(
        "=" * 70
    )


    paired_metrics = [
        "target_pareto_labels",
        "generated_labels",
        "dominance_checks",
        "comparisons_per_generated_label",
        "max_labels_per_node",
        "runtime_seconds"
    ]


    for overlap in sorted(
        df[
            "pairwise_overlap"
        ].unique()
    ):

        print()
        print(
            f"Overlap = "
            f"{overlap:.2f}"
        )

        print(
            "-" * 50
        )


        subset = df[
            df[
                "pairwise_overlap"
            ]
            == overlap
        ]


        for metric in (
            paired_metrics
        ):

            pivot = subset.pivot(
                index="replicate_id",
                columns="structure",
                values=metric
            )


            difference = (
                pivot["suffix"]
                -
                pivot["prefix"]
            )


            mean_diff = (
                difference.mean()
            )

            std_diff = (
                difference.std(
                    ddof=1
                )
            )

            n = (
                difference.count()
            )

            se = (
                std_diff
                /
                np.sqrt(n)
            )

            ci95 = (
                1.96
                *
                se
            )


            prefix_mean = (
                pivot[
                    "prefix"
                ].mean()
            )

            suffix_mean = (
                pivot[
                    "suffix"
                ].mean()
            )


            if prefix_mean != 0:

                ratio = (
                    suffix_mean
                    /
                    prefix_mean
                )

            else:

                ratio = np.nan


            print()

            print(
                metric
            )

            print(
                f"  Prefix mean      = "
                f"{prefix_mean:.6f}"
            )

            print(
                f"  Suffix mean      = "
                f"{suffix_mean:.6f}"
            )

            print(
                f"  Suffix - Prefix  = "
                f"{mean_diff:.6f}"
            )

            print(
                f"  95% CI           = "
                f"["
                f"{mean_diff - ci95:.6f}, "
                f"{mean_diff + ci95:.6f}"
                f"]"
            )

            print(
                f"  Suffix / Prefix  = "
                f"{ratio:.3f}x"
            )


    # ========================================================
    # 21. Strong paired-design verification
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "PAIRED DESIGN VERIFICATION"
    )

    print(
        "=" * 70
    )


    verification_columns = [
        "target_pareto_labels",
        "num_nodes",
        "num_edges",
        "rho_12",
        "rho_13",
        "rho_23"
    ]


    for column in (
        verification_columns
    ):

        pivot = df.pivot_table(
            index=[
                "shared_length",
                "replicate_id"
            ],
            columns="structure",
            values=column,
            aggfunc="first"
        )


        difference = (
            pivot[
                "suffix"
            ]
            -
            pivot[
                "prefix"
            ]
        )


        max_abs_difference = (
            difference.abs().max()
        )


        print(
            f"{column:30s}: "
            f"max absolute difference = "
            f"{max_abs_difference:.10f}"
        )


    # ========================================================
    # 22. Save summary
    # ========================================================

    SUMMARY_FILE = os.path.join(
        OUTPUT_DIR,
        "experiment_03b_overlap_position_summary.csv"
    )


    workload_summary.to_csv(
        SUMMARY_FILE
    )


    # ========================================================
    # Done
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "EXPERIMENT 3B COMPLETED"
    )

    print(
        "=" * 70
    )

    print()

    print(
        "Raw data saved to:"
    )

    print(
        OUTPUT_FILE
    )

    print()

    print(
        "Summary saved to:"
    )

    print(
        SUMMARY_FILE
    )

    print()

    print(
        "Total observations:",
        len(df)
    )

    print()

    print(
        "Experiment 3B completed successfully."
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()