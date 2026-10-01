# ============================================================
# test_correctness.py
#
# MOSP IMPLEMENTATION CORRECTNESS VALIDATION
#
# Compare:
#   1. MOSP Pareto cost set
#   2. Exhaustive simple-path enumeration Pareto cost set
#
# Validation:
#   1000 random directed graphs
#
# ============================================================

from __future__ import annotations

import csv
import random
import time
from pathlib import Path

from src.graph import Graph
from src.mosp import mosp


# ============================================================
# EXPERIMENT SETTINGS
# ============================================================

NUM_TESTS = 1000

NUM_NODES = 7

# Additional directed-edge probability.
# A backbone path is always inserted first,
# so every test has at least one source-target path.
EDGE_PROBABILITY = 0.25

# Test several objective dimensions.
OBJECTIVE_OPTIONS = [2, 3, 4, 5]

MIN_COST = 1
MAX_COST = 20

SOURCE = 0
TARGET = NUM_NODES - 1

MASTER_SEED = 20260930


# ============================================================
# OUTPUT
# ============================================================

ROOT = Path(__file__).resolve().parent

RESULT_DIR = (
    ROOT
    / "experiments"
    / "results"
    / "correctness_validation"
)

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CASE_CSV = (
    RESULT_DIR
    / "correctness_validation_cases.csv"
)

SUMMARY_TXT = (
    RESULT_DIR
    / "correctness_validation_summary.txt"
)


# ============================================================
# PARETO DOMINANCE
# ============================================================

def dominates(a, b):
    """
    Return True if cost vector a Pareto-dominates b.

    All objectives are minimization objectives.
    """

    all_not_worse = all(
        x <= y
        for x, y in zip(a, b)
    )

    at_least_one_better = any(
        x < y
        for x, y in zip(a, b)
    )

    return (
        all_not_worse
        and at_least_one_better
    )


# ============================================================
# PARETO FILTER
# ============================================================

def pareto_filter(cost_vectors):
    """
    Compute the unique non-dominated cost-vector set.

    This function is intentionally independent from
    src.dominance so the brute-force benchmark does not
    reuse the MOSP dominance implementation.
    """

    unique_costs = list(
        set(
            tuple(cost)
            for cost in cost_vectors
        )
    )

    pareto = set()

    for i, candidate in enumerate(
        unique_costs
    ):

        dominated = False

        for j, other in enumerate(
            unique_costs
        ):

            if i == j:
                continue

            if dominates(
                other,
                candidate
            ):
                dominated = True
                break

        if not dominated:
            pareto.add(candidate)

    return pareto


# ============================================================
# RANDOM GRAPH GENERATION
# ============================================================

def generate_random_graph(
    rng,
    num_objectives,
):
    """
    Generate a small directed graph.

    A source-target backbone is inserted first:

        0 -> 1 -> 2 -> ... -> TARGET

    Then additional random directed edges are added.

    Cycles are allowed.

    All edge costs are strictly positive integers.
    """

    graph = Graph()

    for node in range(NUM_NODES):
        graph.add_node(node)

    existing_edges = set()

    # --------------------------------------------------------
    # 1. Guaranteed source-target backbone
    # --------------------------------------------------------

    for u in range(
        NUM_NODES - 1
    ):

        v = u + 1

        costs = tuple(
            rng.randint(
                MIN_COST,
                MAX_COST
            )
            for _ in range(
                num_objectives
            )
        )

        graph.add_edge(
            u,
            v,
            costs
        )

        existing_edges.add(
            (u, v)
        )

    # --------------------------------------------------------
    # 2. Random additional directed edges
    # --------------------------------------------------------

    for u in range(NUM_NODES):

        for v in range(NUM_NODES):

            if u == v:
                continue

            if (
                u,
                v
            ) in existing_edges:
                continue

            if (
                rng.random()
                < EDGE_PROBABILITY
            ):

                costs = tuple(
                    rng.randint(
                        MIN_COST,
                        MAX_COST
                    )
                    for _ in range(
                        num_objectives
                    )
                )

                graph.add_edge(
                    u,
                    v,
                    costs
                )

                existing_edges.add(
                    (u, v)
                )

    return graph, existing_edges


# ============================================================
# EXHAUSTIVE SIMPLE-PATH ENUMERATION
# ============================================================

def enumerate_simple_path_costs(
    graph,
    source,
    target,
    num_objectives,
):
    """
    Enumerate every source-target simple path
    using DFS.

    Instead of storing the entire path,
    only the final cost vector is required
    for correctness comparison.
    """

    path_costs = []

    visited = {
        source
    }

    zero_cost = tuple(
        0
        for _ in range(
            num_objectives
        )
    )

    def dfs(
        current,
        accumulated_cost,
    ):

        # ----------------------------------------------------
        # Reached destination
        # ----------------------------------------------------

        if current == target:

            path_costs.append(
                accumulated_cost
            )

            return

        # ----------------------------------------------------
        # Explore outgoing edges
        # ----------------------------------------------------

        for edge in graph.neighbors(
            current
        ):

            next_node = edge.to

            # simple paths only
            if next_node in visited:
                continue

            new_cost = tuple(
                accumulated_cost[k]
                + edge.costs[k]
                for k in range(
                    num_objectives
                )
            )

            visited.add(
                next_node
            )

            dfs(
                next_node,
                new_cost
            )

            visited.remove(
                next_node
            )

    dfs(
        source,
        zero_cost
    )

    return path_costs


# ============================================================
# GET MOSP PARETO COST SET
# ============================================================

def get_mosp_pareto_costs(
    graph,
    source,
    target,
    num_objectives,
):
    """
    Run the project's actual MOSP implementation
    and extract active target-label cost vectors.
    """

    result = mosp(
        graph=graph,
        source=source,
        num_objectives=num_objectives,
        return_stats=True,
    )

    # Current project implementation returns:
    #
    #     labels, stats
    #
    labels, stats = result

    target_labels = [
        label
        for label in labels[target]
        if getattr(
            label,
            "active",
            True
        )
    ]

    costs = {
        tuple(label.costs)
        for label in target_labels
    }

    return costs, stats


# ============================================================
# FORMAT COST SET
# ============================================================

def format_cost_set(cost_set):

    if not cost_set:
        return "{}"

    ordered = sorted(
        cost_set
    )

    return (
        "{"
        + ", ".join(
            str(x)
            for x in ordered
        )
        + "}"
    )


# ============================================================
# RUN ONE TEST
# ============================================================

def run_one_test(
    test_id,
    rng,
):

    num_objectives = rng.choice(
        OBJECTIVE_OPTIONS
    )

    graph, edge_set = (
        generate_random_graph(
            rng,
            num_objectives,
        )
    )

    # --------------------------------------------------------
    # Brute-force enumeration
    # --------------------------------------------------------

    brute_start = (
        time.perf_counter()
    )

    all_path_costs = (
        enumerate_simple_path_costs(
            graph=graph,
            source=SOURCE,
            target=TARGET,
            num_objectives=num_objectives,
        )
    )

    brute_pareto = (
        pareto_filter(
            all_path_costs
        )
    )

    brute_runtime = (
        time.perf_counter()
        - brute_start
    )

    # --------------------------------------------------------
    # MOSP
    # --------------------------------------------------------

    mosp_start = (
        time.perf_counter()
    )

    mosp_pareto, stats = (
        get_mosp_pareto_costs(
            graph=graph,
            source=SOURCE,
            target=TARGET,
            num_objectives=num_objectives,
        )
    )

    mosp_runtime = (
        time.perf_counter()
        - mosp_start
    )

    # --------------------------------------------------------
    # Exact set comparison
    # --------------------------------------------------------

    passed = (
        mosp_pareto
        == brute_pareto
    )

    missing_from_mosp = (
        brute_pareto
        - mosp_pareto
    )

    extra_in_mosp = (
        mosp_pareto
        - brute_pareto
    )

    row = {
        "test_id":
            test_id,

        "objectives":
            num_objectives,

        "num_nodes":
            NUM_NODES,

        "num_edges":
            len(edge_set),

        "simple_paths":
            len(all_path_costs),

        "brute_pareto_count":
            len(brute_pareto),

        "mosp_pareto_count":
            len(mosp_pareto),

        "passed":
            passed,

        "brute_runtime_seconds":
            brute_runtime,

        "mosp_runtime_seconds":
            mosp_runtime,

        "generated_labels":
            stats.get(
                "generated_labels",
                ""
            ),

        "dominance_checks":
            stats.get(
                "dominance_checks",
                ""
            ),

        "max_labels_per_node":
            stats.get(
                "max_labels_per_node",
                ""
            ),

        "missing_from_mosp":
            format_cost_set(
                missing_from_mosp
            ),

        "extra_in_mosp":
            format_cost_set(
                extra_in_mosp
            ),
    }

    return (
        passed,
        row,
        mosp_pareto,
        brute_pareto,
        edge_set,
    )


# ============================================================
# SAVE CSV
# ============================================================

def save_cases(rows):

    if not rows:
        return

    with open(
        CASE_CSV,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(
                rows[0].keys()
            ),
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


# ============================================================
# MAIN VALIDATION
# ============================================================

def main():

    print(
        "=" * 72
    )

    print(
        "MOSP CORRECTNESS VALIDATION"
    )

    print(
        "=" * 72
    )

    print()

    print(
        f"Number of tests       : "
        f"{NUM_TESTS}"
    )

    print(
        f"Nodes per graph       : "
        f"{NUM_NODES}"
    )

    print(
        f"Additional edge prob. : "
        f"{EDGE_PROBABILITY}"
    )

    print(
        f"Objectives tested     : "
        f"{OBJECTIVE_OPTIONS}"
    )

    print(
        f"Edge cost range       : "
        f"[{MIN_COST}, "
        f"{MAX_COST}]"
    )

    print(
        f"Master seed           : "
        f"{MASTER_SEED}"
    )

    print()

    rng = random.Random(
        MASTER_SEED
    )

    rows = []

    passed_count = 0
    failed_count = 0

    total_paths = 0

    start_all = (
        time.perf_counter()
    )

    # --------------------------------------------------------
    # Run all tests
    # --------------------------------------------------------

    for test_id in range(
        1,
        NUM_TESTS + 1
    ):

        (
            passed,
            row,
            mosp_pareto,
            brute_pareto,
            edge_set,
        ) = run_one_test(
            test_id,
            rng,
        )

        rows.append(
            row
        )

        total_paths += (
            row[
                "simple_paths"
            ]
        )

        if passed:

            passed_count += 1

        else:

            failed_count += 1

            print()
            print(
                "!" * 72
            )

            print(
                f"VALIDATION FAILURE "
                f"AT TEST {test_id}"
            )

            print(
                "!" * 72
            )

            print(
                "Objectives:",
                row[
                    "objectives"
                ]
            )

            print(
                "Edges:",
                sorted(
                    edge_set
                )
            )

            print(
                "MOSP Pareto:"
            )

            print(
                sorted(
                    mosp_pareto
                )
            )

            print(
                "Brute-force Pareto:"
            )

            print(
                sorted(
                    brute_pareto
                )
            )

            print(
                "Missing from MOSP:"
            )

            print(
                sorted(
                    brute_pareto
                    - mosp_pareto
                )
            )

            print(
                "Extra in MOSP:"
            )

            print(
                sorted(
                    mosp_pareto
                    - brute_pareto
                )
            )

            print()

            # Stop immediately at first mismatch.
            #
            # This is useful during debugging because
            # the exact failed graph can be inspected.

            save_cases(
                rows
            )

            raise AssertionError(
                f"Correctness validation "
                f"failed at test "
                f"{test_id}."
            )

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if (
            test_id % 100
            == 0
        ):

            print(
                f"[{test_id:4d}/"
                f"{NUM_TESTS}] "
                f"PASS"
            )

    total_runtime = (
        time.perf_counter()
        - start_all
    )

    # --------------------------------------------------------
    # Save case-level CSV
    # --------------------------------------------------------

    save_cases(
        rows
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    pass_rate = (
        passed_count
        / NUM_TESTS
        * 100
    )

    summary_lines = [
        "=" * 72,
        "MOSP CORRECTNESS VALIDATION SUMMARY",
        "=" * 72,
        "",
        f"Total tests              : {NUM_TESTS}",
        f"Passed                   : {passed_count}",
        f"Failed                   : {failed_count}",
        f"Pass rate                : {pass_rate:.2f}%",
        "",
        f"Nodes per graph          : {NUM_NODES}",
        f"Additional edge prob.    : {EDGE_PROBABILITY}",
        f"Objectives tested        : {OBJECTIVE_OPTIONS}",
        f"Edge cost range          : [{MIN_COST}, {MAX_COST}]",
        f"Master seed              : {MASTER_SEED}",
        "",
        f"Total simple paths tested: {total_paths}",
        f"Total runtime            : {total_runtime:.4f} seconds",
        "",
        "Validation criterion:",
        "MOSP Pareto cost-vector set",
        "==",
        "Brute-force Pareto cost-vector set",
        "",
    ]

    if failed_count == 0:

        summary_lines.extend(
            [
                "RESULT:",
                "ALL TESTS PASSED.",
                "",
                (
                    "All 1,000 random test cases "
                    "produced exactly the same "
                    "non-dominated cost-vector set "
                    "under MOSP and exhaustive "
                    "simple-path enumeration."
                ),
            ]
        )

    summary_text = "\n".join(
        summary_lines
    )

    SUMMARY_TXT.write_text(
        summary_text,
        encoding="utf-8",
    )

    print()
    print(
        summary_text
    )

    print()

    print(
        "Case-level results saved to:"
    )

    print(
        CASE_CSV
    )

    print()

    print(
        "Summary saved to:"
    )

    print(
        SUMMARY_TXT
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()