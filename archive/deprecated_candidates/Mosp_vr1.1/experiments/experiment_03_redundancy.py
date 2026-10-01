import csv
import os
import random
import time
from collections import defaultdict

import networkx as nx

from src.graph import Graph
from src.mosp import mosp


# ============================================================
# Experiment 3 — Formal Version
# Transit Route Redundancy
#
# Main idea:
#   Keep |V|, |E|, objective dimension, OD pairs, and
#   cost-generation mechanism controlled.
#
#   Change only HOW cross-line links are arranged.
#
# Conditions:
#   low    = concentrated interchange corridors
#   medium = spatially distributed adjacent-line connections
#   high   = spatially distributed connections across many lines
# ============================================================


# ============================================================
# Global settings
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

MIN_COST = 1
MAX_COST = 100

MASTER_SEED = 42


# ------------------------------------------------------------
# IMPORTANT:
#
# Each line has 19 undirected adjacent links.
#
# 5 × 19 = 95 undirected base links
# Bidirectional representation:
# 95 × 2 = 190 directed edges
#
# Add exactly 36 undirected cross-links:
# 36 × 2 = 72 directed edges
#
# Total:
# 190 + 72 = 262 directed edges
# ------------------------------------------------------------

NUM_CROSS_LINKS = 36

EXPECTED_DIRECTED_EDGES = (
    NUM_LINES
    * (STATIONS_PER_LINE - 1)
    * 2
    +
    NUM_CROSS_LINKS
    * 2
)


REDUNDANCY_LEVELS = [
    "low",
    "medium",
    "high"
]


# ============================================================
# Alternative-route metric settings
# ============================================================

# Count at most the first K loopless shortest alternatives.
MAX_ALTERNATIVE_PATHS = 50

# A path is considered a "reasonable alternative" if:
#
# hops(path) <= shortest_hops * PATH_STRETCH
#
PATH_STRETCH = 1.50


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


def node_position(node):
    return (
        node % STATIONS_PER_LINE
    )


# ============================================================
# Base transit lines
# ============================================================

def generate_base_edges():
    """
    Five independent bidirectional transit lines.

    Each line:
        ●—●—●— ... —●

    Returns directed edges.
    """

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

            edges.add((u, v))
            edges.add((v, u))

    return edges


# ============================================================
# Utility for adding bidirectional cross-links
# ============================================================

def add_cross_link(
    cross_links,
    line_a,
    pos_a,
    line_b,
    pos_b
):
    """
    Store an undirected cross-link canonically.

    The directed version is created later.
    """

    u = node_id(
        line_a,
        pos_a
    )

    v = node_id(
        line_b,
        pos_b
    )

    if u == v:
        return False

    edge = tuple(
        sorted((u, v))
    )

    if edge in cross_links:
        return False

    cross_links.add(edge)

    return True


# ============================================================
# LOW redundancy
# ============================================================

def generate_low_cross_links(rng):
    """
    LOW REDUNDANCY

    Same number of cross-links as all other conditions,
    but links are concentrated around only a few
    interchange zones.

    Adjacent line pairs:
        0-1
        1-2
        2-3
        3-4

    Each pair receives 9 links.

    Those 9 links form a local 3x3 interchange cluster.
    Therefore many links exist, but they are spatially
    concentrated and create bottleneck-like structure.
    """

    cross_links = set()

    # Choose a local interchange center away from boundaries.
    center = rng.randint(
        5,
        STATIONS_PER_LINE - 6
    )

    positions = [
        center - 1,
        center,
        center + 1
    ]

    adjacent_pairs = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4)
    ]

    for line_a, line_b in adjacent_pairs:

        # Complete 3 × 3 local cluster
        # = 9 cross-links per line pair
        for pos_a in positions:

            for pos_b in positions:

                add_cross_link(
                    cross_links,
                    line_a,
                    pos_a,
                    line_b,
                    pos_b
                )

    assert (
        len(cross_links)
        == NUM_CROSS_LINKS
    )

    return cross_links


# ============================================================
# MEDIUM redundancy
# ============================================================

def generate_medium_cross_links(rng):
    """
    MEDIUM REDUNDANCY

    Still mainly connects adjacent transit lines,
    but interchange locations are spread along the corridor.

    Same:
        36 undirected cross-links

    Unlike LOW:
        cross-links are no longer concentrated
        at one interchange region.
    """

    cross_links = set()

    adjacent_pairs = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4)
    ]

    # 9 positions spread across the transit line.
    base_positions = [
        1, 3, 5, 7, 9,
        11, 13, 15, 17
    ]

    # Give each network slight positional variation.
    jittered_positions = []

    for p in base_positions:

        shift = rng.choice(
            [-1, 0, 1]
        )

        new_p = max(
            0,
            min(
                STATIONS_PER_LINE - 1,
                p + shift
            )
        )

        jittered_positions.append(
            new_p
        )

    # Resolve duplicate positions if jitter generated any.
    # Fall back to original spread positions.
    if len(set(jittered_positions)) < 9:
        jittered_positions = (
            base_positions.copy()
        )

    for line_a, line_b in adjacent_pairs:

        # Shuffle destination matching slightly,
        # while keeping links spatially distributed.
        destination_positions = (
            jittered_positions.copy()
        )

        rng.shuffle(
            destination_positions
        )

        for pos_a, pos_b in zip(
            jittered_positions,
            destination_positions
        ):

            add_cross_link(
                cross_links,
                line_a,
                pos_a,
                line_b,
                pos_b
            )

    assert (
        len(cross_links)
        == NUM_CROSS_LINKS
    )

    return cross_links


# ============================================================
# HIGH redundancy
# ============================================================

def generate_high_cross_links(rng):
    """
    HIGH REDUNDANCY

    Cross-links are distributed:
      - across many line pairs
      - across many station positions

    This creates:
      - more cycles between lines
      - more alternative corridors
      - fewer single interchange bottlenecks

    Still exactly 36 undirected cross-links.
    """

    cross_links = set()

    all_line_pairs = []

    for line_a in range(NUM_LINES):

        for line_b in range(
            line_a + 1,
            NUM_LINES
        ):

            all_line_pairs.append(
                (line_a, line_b)
            )

    # 5 lines -> C(5,2) = 10 line pairs.
    assert len(all_line_pairs) == 10

    # Allocate:
    #
    # first 6 line pairs -> 4 links
    # remaining 4 pairs -> 3 links
    #
    # 6*4 + 4*3 = 36

    rng.shuffle(
        all_line_pairs
    )

    allocations = (
        [4] * 6
        +
        [3] * 4
    )

    for (
        line_a,
        line_b
    ), count in zip(
        all_line_pairs,
        allocations
    ):

        attempts = 0
        added = 0

        used_positions_a = set()
        used_positions_b = set()

        while added < count:

            attempts += 1

            if attempts > 10000:
                raise RuntimeError(
                    "Could not generate "
                    "high-redundancy links."
                )

            # Spread links throughout the lines.
            pos_a = rng.randint(
                1,
                STATIONS_PER_LINE - 2
            )

            pos_b = rng.randint(
                1,
                STATIONS_PER_LINE - 2
            )

            # Prefer using different station positions
            # for each connection of the same line pair.
            if (
                pos_a in used_positions_a
                or pos_b in used_positions_b
            ):
                continue

            success = add_cross_link(
                cross_links,
                line_a,
                pos_a,
                line_b,
                pos_b
            )

            if not success:
                continue

            used_positions_a.add(
                pos_a
            )

            used_positions_b.add(
                pos_b
            )

            added += 1

    assert (
        len(cross_links)
        == NUM_CROSS_LINKS
    )

    return cross_links


# ============================================================
# Generate complete topology
# ============================================================

def generate_topology(
    level,
    seed
):

    rng = random.Random(seed)

    base_edges = (
        generate_base_edges()
    )

    if level == "low":

        cross_links = (
            generate_low_cross_links(
                rng
            )
        )

    elif level == "medium":

        cross_links = (
            generate_medium_cross_links(
                rng
            )
        )

    elif level == "high":

        cross_links = (
            generate_high_cross_links(
                rng
            )
        )

    else:

        raise ValueError(
            f"Unknown redundancy level: "
            f"{level}"
        )

    directed_edges = set(
        base_edges
    )

    for u, v in cross_links:

        directed_edges.add(
            (u, v)
        )

        directed_edges.add(
            (v, u)
        )

    assert (
        len(directed_edges)
        == EXPECTED_DIRECTED_EDGES
    )

    return directed_edges


# ============================================================
# Controlled edge costs
# ============================================================

def stable_edge_seed(
    network_seed,
    u,
    v
):
    """
    Deterministic seed for one directed edge.

    If the same directed edge occurs in LOW / MEDIUM / HIGH
    for the same network replicate, it receives the same
    objective-cost vector.

    This reduces unnecessary cost-distribution confounding.
    """

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

        edge_rng = random.Random(
            stable_edge_seed(
                network_seed,
                u,
                v
            )
        )

        costs = tuple(
            edge_rng.randint(
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
# Matched OD generation
# ============================================================

def generate_matched_queries(
    rng
):
    """
    Same OD pairs are used in LOW / MEDIUM / HIGH.

    Prefer different-line trips because these are more
    informative for transit interchange / redundancy.
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
                "Could not generate "
                "matched OD pairs."
            )

        source = rng.randrange(
            NUM_NODES
        )

        target = rng.randrange(
            NUM_NODES
        )

        if source == target:
            continue

        # Transit relevance:
        # source and target should be on different lines.
        if (
            node_line(source)
            ==
            node_line(target)
        ):
            continue

        pair = (
            source,
            target
        )

        queries.add(
            pair
        )

    return list(
        sorted(queries)
    )


# ============================================================
# Redundancy metric 1:
# Edge-disjoint path count
# ============================================================

def edge_disjoint_path_count(
    G,
    source,
    target
):

    try:

        return nx.edge_connectivity(
            G,
            source,
            target
        )

    except nx.NetworkXError:

        return 0


# ============================================================
# Redundancy metric 2:
# Reasonable alternative routes
# ============================================================

def count_reasonable_alternative_paths(
    G,
    source,
    target,
    max_paths=MAX_ALTERNATIVE_PATHS,
    stretch=PATH_STRETCH
):
    """
    Count loopless alternative routes whose hop length
    is no more than:

        shortest_hops × stretch

    Search stops after max_paths qualifying / examined
    shortest-simple-path candidates.

    This is NOT claimed as the unique definition of
    transportation route redundancy.

    It is used here as a controlled synthetic proxy.
    """

    try:

        shortest_hops = (
            nx.shortest_path_length(
                G,
                source,
                target
            )
        )

    except nx.NetworkXNoPath:

        return 0, None

    max_hops = max(
        shortest_hops,
        int(
            shortest_hops
            * stretch
        )
    )

    count = 0
    examined = 0

    try:

        generator = (
            nx.shortest_simple_paths(
                G,
                source,
                target
            )
        )

        for path in generator:

            examined += 1

            hops = (
                len(path) - 1
            )

            # shortest_simple_paths is ordered
            # by path length for unweighted graph.
            if hops > max_hops:
                break

            count += 1

            if count >= max_paths:
                break

    except nx.NetworkXNoPath:

        return 0, shortest_hops

    return (
        count,
        shortest_hops
    )


# ============================================================
# Graph structural metrics
# ============================================================

def calculate_graph_metrics(G):

    degrees = [
        G.out_degree(node)
        for node in G.nodes
    ]

    avg_out_degree = (
        sum(degrees)
        /
        len(degrees)
    )

    max_out_degree = max(
        degrees
    )

    return {
        "avg_out_degree":
            avg_out_degree,

        "max_out_degree":
            max_out_degree
    }


# ============================================================
# Run experiment
# ============================================================

def run_experiment():

    master_rng = random.Random(
        MASTER_SEED
    )

    results = []

    # Store manipulation information
    # during execution.
    redundancy_debug = defaultdict(
        list
    )

    for network_id in range(
        NUM_NETWORKS
    ):

        print()
        print(
            f"===== Network "
            f"{network_id + 1}/"
            f"{NUM_NETWORKS} ====="
        )

        # ----------------------------------------------------
        # One matched network seed
        # ----------------------------------------------------

        network_seed = (
            master_rng.randint(
                0,
                10**9
            )
        )

        # ----------------------------------------------------
        # SAME OD pairs for all three conditions
        # ----------------------------------------------------

        query_rng = random.Random(
            network_seed
            + 1234567
        )

        queries = (
            generate_matched_queries(
                query_rng
            )
        )

        # ----------------------------------------------------
        # Generate each topology condition
        # ----------------------------------------------------

        for level_index, level in enumerate(
            REDUNDANCY_LEVELS
        ):

            print(
                f"  {level}"
            )

            topology_seed = (
                network_seed
                + level_index
                * 10_000_019
            )

            topology = (
                generate_topology(
                    level,
                    topology_seed
                )
            )

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

            nx_graph = (
                build_nx_graph(
                    topology
                )
            )

            # All topologies should be strongly connected.
            if not nx.is_strongly_connected(
                nx_graph
            ):

                raise RuntimeError(
                    f"{level} topology "
                    f"is not strongly connected."
                )

            graph_metrics = (
                calculate_graph_metrics(
                    nx_graph
                )
            )

            num_edges = (
                nx_graph.number_of_edges()
            )

            assert (
                num_edges
                ==
                EXPECTED_DIRECTED_EDGES
            )

            # ------------------------------------------------
            # Run matched queries
            # ------------------------------------------------

            for query_id, (
                source,
                target
            ) in enumerate(
                queries
            ):

                # --------------------------------------------
                # Redundancy metrics
                # --------------------------------------------

                edge_disjoint = (
                    edge_disjoint_path_count(
                        nx_graph,
                        source,
                        target
                    )
                )

                (
                    alternative_count,
                    shortest_hops
                ) = (
                    count_reasonable_alternative_paths(
                        nx_graph,
                        source,
                        target
                    )
                )

                # --------------------------------------------
                # MOSP
                # --------------------------------------------

                start_time = (
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
                    -
                    start_time
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

                # --------------------------------------------
                # Save observation
                # --------------------------------------------

                row = {

                    "redundancy_level":
                        level,

                    "network_id":
                        network_id,

                    "query_id":
                        query_id,

                    "source":
                        source,

                    "target":
                        target,

                    "source_line":
                        node_line(source),

                    "target_line":
                        node_line(target),

                    "num_nodes":
                        NUM_NODES,

                    "num_edges":
                        num_edges,

                    "avg_out_degree":
                        graph_metrics[
                            "avg_out_degree"
                        ],

                    "max_out_degree":
                        graph_metrics[
                            "max_out_degree"
                        ],

                    "shortest_hops":
                        shortest_hops,

                    "edge_disjoint_paths":
                        edge_disjoint,

                    "reasonable_alternative_paths":
                        alternative_count,

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
                }

                results.append(
                    row
                )

                redundancy_debug[
                    level
                ].append(
                    (
                        edge_disjoint,
                        alternative_count
                    )
                )

    return (
        results,
        redundancy_debug
    )


# ============================================================
# Save raw results
# ============================================================

def save_results(results):

    script_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    results_dir = os.path.join(
        script_dir,
        "results"
    )

    os.makedirs(
        results_dir,
        exist_ok=True
    )

    output_path = os.path.join(
        results_dir,
        "experiment_03_redundancy_formal_raw.csv"
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
# Manipulation check
# ============================================================

def print_manipulation_check(
    results
):

    print()
    print(
        "=========================================="
    )

    print(
        "EXPERIMENT 3 FORMAL MANIPULATION CHECK"
    )

    print(
        "=========================================="
    )

    print()

    for level in REDUNDANCY_LEVELS:

        subset = [
            row
            for row in results
            if row[
                "redundancy_level"
            ] == level
        ]

        mean_edges = (
            sum(
                row[
                    "num_edges"
                ]
                for row in subset
            )
            /
            len(subset)
        )

        mean_degree = (
            sum(
                row[
                    "avg_out_degree"
                ]
                for row in subset
            )
            /
            len(subset)
        )

        mean_disjoint = (
            sum(
                row[
                    "edge_disjoint_paths"
                ]
                for row in subset
            )
            /
            len(subset)
        )

        mean_alternatives = (
            sum(
                row[
                    "reasonable_alternative_paths"
                ]
                for row in subset
            )
            /
            len(subset)
        )

        mean_shortest_hops = (
            sum(
                row[
                    "shortest_hops"
                ]
                for row in subset
            )
            /
            len(subset)
        )

        print(level.upper())

        print(
            f"  Observations = "
            f"{len(subset)}"
        )

        print(
            f"  Mean directed edges = "
            f"{mean_edges:.3f}"
        )

        print(
            f"  Mean avg out-degree = "
            f"{mean_degree:.3f}"
        )

        print(
            f"  Mean edge-disjoint paths = "
            f"{mean_disjoint:.3f}"
        )

        print(
            f"  Mean reasonable alternatives = "
            f"{mean_alternatives:.3f}"
        )

        print(
            f"  Mean shortest hops = "
            f"{mean_shortest_hops:.3f}"
        )

        print()


# ============================================================
# Matched-design check
# ============================================================

def print_matched_design_check(
    results
):

    groups = defaultdict(
        set
    )

    for row in results:

        key = (
            row[
                "network_id"
            ],
            row[
                "query_id"
            ],
            row[
                "source"
            ],
            row[
                "target"
            ]
        )

        groups[
            key
        ].add(
            row[
                "redundancy_level"
            ]
        )

    fully_matched = sum(
        1
        for levels in groups.values()
        if levels
        ==
        set(
            REDUNDANCY_LEVELS
        )
    )

    print(
        "===== MATCHED DESIGN CHECK ====="
    )

    print(
        "Unique network-OD cases:",
        len(groups)
    )

    print(
        "Cases containing all three levels:",
        fully_matched
    )

    print()


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    results, _ = (
        run_experiment()
    )

    save_results(
        results
    )

    print_manipulation_check(
        results
    )

    print_matched_design_check(
        results
    )

    expected = (
        NUM_NETWORKS
        *
        QUERIES_PER_NETWORK
        *
        len(
            REDUNDANCY_LEVELS
        )
    )

    print(
        "Total observations:",
        len(results)
    )

    print(
        "Expected observations:",
        expected
    )

    assert (
        len(results)
        == expected
    )

    print()

    print(
        "Expected directed edges "
        "per topology:",
        EXPECTED_DIRECTED_EDGES
    )

    print()

    print(
        "Experiment 3 formal run "
        "completed successfully."
    )