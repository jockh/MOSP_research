import csv
import os
import random
import time
from itertools import combinations

import networkx as nx

from src.graph import Graph
from src.mosp import mosp


# ============================================================
# Experiment 3
# OD-Level Route Diversity in Transit-Like Networks
# ============================================================

NUM_LINES = 5
STATIONS_PER_LINE = 20

NUM_NODES = (
    NUM_LINES
    * STATIONS_PER_LINE
)

NUM_OBJECTIVES = 3

NUM_NETWORKS = 50
QUERIES_PER_NETWORK = 10

NUM_CROSS_LINKS = 36

MIN_COST = 1
MAX_COST = 100

MASTER_SEED = 42


# ============================================================
# Route diversity settings
# ============================================================

PATH_STRETCH = 1.50

MIN_DIVERSITY = 0.40

MAX_CANDIDATES = 200

MAX_ACCEPTED_ROUTES = 20


# ============================================================
# Expected network size
# ============================================================

BASE_DIRECTED_EDGES = (
    NUM_LINES
    * (STATIONS_PER_LINE - 1)
    * 2
)

CROSS_DIRECTED_EDGES = (
    NUM_CROSS_LINKS
    * 2
)

EXPECTED_DIRECTED_EDGES = (
    BASE_DIRECTED_EDGES
    + CROSS_DIRECTED_EDGES
)


# ============================================================
# Node helpers
# ============================================================

def node_id(line, position):

    return (
        line * STATIONS_PER_LINE
        + position
    )


def node_line(node):

    return (
        node // STATIONS_PER_LINE
    )


# ============================================================
# Base transit lines
# ============================================================

def generate_base_edges():

    edges = set()

    for line in range(NUM_LINES):

        for pos in range(
            STATIONS_PER_LINE - 1
        ):

            u = node_id(
                line,
                pos
            )

            v = node_id(
                line,
                pos + 1
            )

            edges.add(
                (u, v)
            )

            edges.add(
                (v, u)
            )

    return edges


# ============================================================
# Random transit cross-links
# ============================================================

def generate_cross_links(rng):
    """
    Generate exactly NUM_CROSS_LINKS undirected
    cross-line links.

    Important:
    - only different transit lines may be connected
    - duplicate cross-links are forbidden
    - total edge count remains fixed
    """

    cross_links = set()

    attempts = 0

    while (
        len(cross_links)
        < NUM_CROSS_LINKS
    ):

        attempts += 1

        if attempts > 100000:

            raise RuntimeError(
                "Could not generate enough cross-links."
            )

        line_a, line_b = rng.sample(
            range(NUM_LINES),
            2
        )

        # Canonical line ordering
        if line_a > line_b:

            line_a, line_b = (
                line_b,
                line_a
            )

        pos_a = rng.randrange(
            STATIONS_PER_LINE
        )

        pos_b = rng.randrange(
            STATIONS_PER_LINE
        )

        u = node_id(
            line_a,
            pos_a
        )

        v = node_id(
            line_b,
            pos_b
        )

        edge = tuple(
            sorted(
                (u, v)
            )
        )

        cross_links.add(
            edge
        )

    return cross_links


# ============================================================
# Generate one transit-like topology
# ============================================================

def generate_topology(seed):

    rng = random.Random(
        seed
    )

    for attempt in range(1000):

        base_edges = (
            generate_base_edges()
        )

        cross_links = (
            generate_cross_links(
                rng
            )
        )

        edges = set(
            base_edges
        )

        for u, v in cross_links:

            edges.add(
                (u, v)
            )

            edges.add(
                (v, u)
            )

        if (
            len(edges)
            != EXPECTED_DIRECTED_EDGES
        ):

            continue

        G = nx.DiGraph()

        G.add_nodes_from(
            range(NUM_NODES)
        )

        G.add_edges_from(
            edges
        )

        if nx.is_strongly_connected(
            G
        ):

            return edges

    raise RuntimeError(
        "Unable to generate a strongly connected "
        "transit-like network."
    )


# ============================================================
# Edge costs
# ============================================================

def stable_edge_seed(
    network_seed,
    u,
    v
):

    return (
        network_seed
        + u * 1_000_003
        + v * 9_176
    )


def generate_edge_costs(
    topology,
    network_seed
):

    edge_costs = {}

    for u, v in topology:

        rng = random.Random(
            stable_edge_seed(
                network_seed,
                u,
                v
            )
        )

        costs = tuple(

            rng.randint(
                MIN_COST,
                MAX_COST
            )

            for _ in range(
                NUM_OBJECTIVES
            )
        )

        edge_costs[
            (u, v)
        ] = costs

    return edge_costs


# ============================================================
# Build MOSP graph
# ============================================================

def build_mosp_graph(
    topology,
    edge_costs
):

    graph = Graph()

    for node in range(
        NUM_NODES
    ):

        graph.add_node(
            node
        )

    for u, v in topology:

        graph.add_edge(
            u,
            v,
            edge_costs[
                (u, v)
            ]
        )

    return graph


# ============================================================
# Build NetworkX graph
# ============================================================

def build_nx_graph(
    topology
):

    G = nx.DiGraph()

    G.add_nodes_from(
        range(NUM_NODES)
    )

    G.add_edges_from(
        topology
    )

    return G


# ============================================================
# Route diversity helpers
# ============================================================

def path_edges(path):

    return {
        (
            path[i],
            path[i + 1]
        )

        for i in range(
            len(path) - 1
        )
    }


def path_diversity(
    path_a,
    path_b
):
    """
    D(Pi, Pj) =
        1 -
        shared_edges /
        min(|Ei|, |Ej|)

    0 = highly overlapping
    1 = completely edge-disjoint
    """

    edges_a = path_edges(
        path_a
    )

    edges_b = path_edges(
        path_b
    )

    if (
        not edges_a
        or not edges_b
    ):

        return 0.0

    shared = (
        edges_a
        &
        edges_b
    )

    denominator = min(
        len(edges_a),
        len(edges_b)
    )

    overlap = (
        len(shared)
        /
        denominator
    )

    return (
        1.0
        - overlap
    )


# ============================================================
# Find distinct reasonable routes
# ============================================================

def find_distinct_routes(
    G,
    source,
    target
):

    try:

        shortest_hops = (
            nx.shortest_path_length(
                G,
                source,
                target
            )
        )

    except nx.NetworkXNoPath:

        return [], None, 0

    max_hops = max(
        shortest_hops,
        int(
            shortest_hops
            * PATH_STRETCH
        )
    )

    accepted = []

    candidates_examined = 0

    try:

        generator = (
            nx.shortest_simple_paths(
                G,
                source,
                target
            )
        )

        for path in generator:

            candidates_examined += 1

            if (
                candidates_examined
                > MAX_CANDIDATES
            ):

                break

            hops = (
                len(path)
                - 1
            )

            # shortest_simple_paths is ordered
            # by path length.
            if hops > max_hops:

                break

            if not accepted:

                accepted.append(
                    path
                )

                continue

            valid = all(

                path_diversity(
                    path,
                    existing
                )
                >= MIN_DIVERSITY

                for existing in accepted
            )

            if valid:

                accepted.append(
                    path
                )

            if (
                len(accepted)
                >= MAX_ACCEPTED_ROUTES
            ):

                break

    except nx.NetworkXNoPath:

        pass

    return (
        accepted,
        shortest_hops,
        candidates_examined
    )


# ============================================================
# Mean pairwise diversity
# ============================================================

def mean_pairwise_diversity(
    routes
):

    if len(routes) < 2:

        return 0.0

    values = []

    for route_a, route_b in combinations(
        routes,
        2
    ):

        values.append(
            path_diversity(
                route_a,
                route_b
            )
        )

    return (
        sum(values)
        /
        len(values)
    )


# ============================================================
# Generate OD queries
# ============================================================

def generate_queries(
    rng
):
    """
    Prefer OD pairs on different transit lines.
    """

    queries = set()

    attempts = 0

    while (
        len(queries)
        < QUERIES_PER_NETWORK
    ):

        attempts += 1

        if attempts > 10000:

            raise RuntimeError(
                "Could not generate OD pairs."
            )

        source = rng.randrange(
            NUM_NODES
        )

        target = rng.randrange(
            NUM_NODES
        )

        if source == target:

            continue

        if (
            node_line(source)
            ==
            node_line(target)
        ):

            continue

        queries.add(
            (
                source,
                target
            )
        )

    return list(
        sorted(
            queries
        )
    )


# ============================================================
# Run experiment
# ============================================================

def run_experiment():

    master_rng = random.Random(
        MASTER_SEED
    )

    results = []

    for network_id in range(
        NUM_NETWORKS
    ):

        print(
            f"Network "
            f"{network_id + 1}/"
            f"{NUM_NETWORKS}"
        )

        network_seed = (
            master_rng.randint(
                0,
                10**9
            )
        )

        # ----------------------------------------------------
        # Topology
        # ----------------------------------------------------

        topology = (
            generate_topology(
                network_seed
            )
        )

        nx_graph = (
            build_nx_graph(
                topology
            )
        )

        # ----------------------------------------------------
        # Costs
        # ----------------------------------------------------

        edge_costs = (
            generate_edge_costs(
                topology,
                network_seed
            )
        )

        mosp_graph = (
            build_mosp_graph(
                topology,
                edge_costs
            )
        )

        # ----------------------------------------------------
        # OD queries
        # ----------------------------------------------------

        query_rng = random.Random(
            network_seed
            + 999_983
        )

        queries = (
            generate_queries(
                query_rng
            )
        )

        # ----------------------------------------------------
        # Run each OD
        # ----------------------------------------------------

        for query_id, (
            source,
            target
        ) in enumerate(
            queries
        ):

            # =================================================
            # Route-diversity measurements
            # =================================================

            (
                routes,
                shortest_hops,
                candidates_examined
            ) = (
                find_distinct_routes(
                    nx_graph,
                    source,
                    target
                )
            )

            distinct_route_count = (
                len(routes)
            )

            # shortest route itself is included.
            distinct_alternative_count = max(
                0,
                distinct_route_count - 1
            )

            mean_diversity = (
                mean_pairwise_diversity(
                    routes
                )
            )

            route_count_ceiling = int(
                distinct_route_count
                >= MAX_ACCEPTED_ROUTES
            )

            candidate_ceiling = int(
                candidates_examined
                >= MAX_CANDIDATES
            )

            # =================================================
            # MOSP
            # =================================================

            start = (
                time.perf_counter()
            )

            labels, stats = mosp(
                mosp_graph,
                source,
                NUM_OBJECTIVES,
                return_stats=True
            )

            runtime = (
                time.perf_counter()
                - start
            )

            target_pareto_labels = (
                len(
                    labels[target]
                )
            )

            generated = (
                stats[
                    "generated_labels"
                ]
            )

            pruned = (
                stats[
                    "pruned_labels"
                ]
            )

            if generated > 0:

                rejection_rate = (
                    pruned
                    /
                    generated
                )

            else:

                rejection_rate = 0.0

            # =================================================
            # Save
            # =================================================

            results.append({

                "network_id":
                    network_id,

                "query_id":
                    query_id,

                "source":
                    source,

                "target":
                    target,

                "source_line":
                    node_line(
                        source
                    ),

                "target_line":
                    node_line(
                        target
                    ),

                "num_nodes":
                    NUM_NODES,

                "num_edges":
                    len(
                        topology
                    ),

                "avg_out_degree":
                    (
                        len(topology)
                        / NUM_NODES
                    ),

                "shortest_hops":
                    shortest_hops,

                "distinct_route_count":
                    distinct_route_count,

                "distinct_alternative_count":
                    distinct_alternative_count,

                "mean_pairwise_diversity":
                    mean_diversity,

                "route_candidates_examined":
                    candidates_examined,

                "route_count_ceiling":
                    route_count_ceiling,

                "candidate_ceiling":
                    candidate_ceiling,

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
                    ],

                "runtime_seconds":
                    runtime
            })

    return results


# ============================================================
# Save results
# ============================================================

def save_results(
    results
):

    script_dir = (
        os.path.dirname(
            os.path.abspath(
                __file__
            )
        )
    )

    results_dir = (
        os.path.join(
            script_dir,
            "results"
        )
    )

    os.makedirs(
        results_dir,
        exist_ok=True
    )

    output_path = (
        os.path.join(
            results_dir,
            "experiment_03_route_diversity_raw.csv"
        )
    )

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=list(
                results[0].keys()
            )
        )

        writer.writeheader()

        writer.writerows(
            results
        )

    print()
    print(
        "Results saved to:",
        output_path
    )


# ============================================================
# Data-quality summary
# ============================================================

def print_summary(
    results
):

    n = len(
        results
    )

    print()
    print(
        "=========================================="
    )

    print(
        "EXPERIMENT 3 DATA CHECK"
    )

    print(
        "=========================================="
    )

    print()

    print(
        "Total observations:",
        n
    )

    print(
        "Expected observations:",
        (
            NUM_NETWORKS
            * QUERIES_PER_NETWORK
        )
    )

    print()

    # --------------------------------------------------------
    # Network control
    # --------------------------------------------------------

    edge_counts = {
        row[
            "num_edges"
        ]
        for row in results
    }

    print(
        "Unique directed edge counts:",
        sorted(
            edge_counts
        )
    )

    # --------------------------------------------------------
    # Route diversity
    # --------------------------------------------------------

    route_counts = [
        row[
            "distinct_route_count"
        ]
        for row in results
    ]

    alternatives = [
        row[
            "distinct_alternative_count"
        ]
        for row in results
    ]

    shortest_hops = [
        row[
            "shortest_hops"
        ]
        for row in results
    ]

    mean_diversities = [
        row[
            "mean_pairwise_diversity"
        ]
        for row in results
    ]

    print()

    print(
        "Distinct route count:"
    )

    print(
        f"  min  = "
        f"{min(route_counts)}"
    )

    print(
        f"  mean = "
        f"{sum(route_counts)/n:.3f}"
    )

    print(
        f"  max  = "
        f"{max(route_counts)}"
    )

    print()

    print(
        "Distinct alternative count:"
    )

    print(
        f"  min  = "
        f"{min(alternatives)}"
    )

    print(
        f"  mean = "
        f"{sum(alternatives)/n:.3f}"
    )

    print(
        f"  max  = "
        f"{max(alternatives)}"
    )

    print()

    print(
        "Mean pairwise diversity:"
    )

    print(
        f"  mean = "
        f"{sum(mean_diversities)/n:.3f}"
    )

    print()

    print(
        "Shortest hops:"
    )

    print(
        f"  min  = "
        f"{min(shortest_hops)}"
    )

    print(
        f"  mean = "
        f"{sum(shortest_hops)/n:.3f}"
    )

    print(
        f"  max  = "
        f"{max(shortest_hops)}"
    )

    # --------------------------------------------------------
    # Ceiling checks
    # --------------------------------------------------------

    route_ceiling_count = sum(
        row[
            "route_count_ceiling"
        ]
        for row in results
    )

    candidate_ceiling_count = sum(
        row[
            "candidate_ceiling"
        ]
        for row in results
    )

    print()

    print(
        "Route-count ceiling cases:",
        route_ceiling_count
    )

    print(
        "Candidate-search ceiling cases:",
        candidate_ceiling_count
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

    expected = (
        NUM_NETWORKS
        * QUERIES_PER_NETWORK
    )

    assert (
        len(results)
        == expected
    )

    print()
    print(
        "Experiment 3 route-diversity "
        "data generation completed successfully."
    )