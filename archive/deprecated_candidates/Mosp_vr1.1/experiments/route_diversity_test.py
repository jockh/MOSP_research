import networkx as nx


# ============================================================
# Route diversity helpers
# ============================================================

def path_edges(path):
    """
    Convert a node path into a set of directed edges.
    """
    return {
        (path[i], path[i + 1])
        for i in range(len(path) - 1)
    }


def path_diversity(path_a, path_b):
    """
    Diversity based on shorter-path overlap.

    diversity = 0:
        the shorter route is completely contained
        in the other route

    diversity = 1:
        no shared edges
    """

    edges_a = path_edges(path_a)
    edges_b = path_edges(path_b)

    if not edges_a or not edges_b:
        return 0.0

    shared = edges_a & edges_b

    shorter_length = min(
        len(edges_a),
        len(edges_b)
    )

    overlap = (
        len(shared)
        / shorter_length
    )

    return 1.0 - overlap


# ============================================================
# Distinct reasonable alternatives
# ============================================================

def find_distinct_alternative_routes(
    G,
    source,
    target,
    stretch=1.5,
    min_diversity=0.4,
    max_candidates=100,
    max_accepted=20
):
    """
    Find distinct reasonable alternative routes.

    Requirements:
    1. route length <= shortest_hops * stretch
    2. diversity >= min_diversity relative
       to every accepted route
    """

    try:
        shortest_hops = nx.shortest_path_length(
            G,
            source,
            target
        )

    except nx.NetworkXNoPath:
        return [], None

    max_hops = max(
        shortest_hops,
        int(shortest_hops * stretch)
    )

    accepted = []

    try:
        generator = nx.shortest_simple_paths(
            G,
            source,
            target
        )

        for candidate_index, path in enumerate(generator):

            if candidate_index >= max_candidates:
                break

            hops = len(path) - 1

            if hops > max_hops:
                break

            if not accepted:
                accepted.append(path)
                continue

            sufficiently_different = all(
                path_diversity(
                    path,
                    existing_path
                ) >= min_diversity

                for existing_path in accepted
            )

            if sufficiently_different:
                accepted.append(path)

            if len(accepted) >= max_accepted:
                break

    except nx.NetworkXNoPath:
        return [], shortest_hops

    return accepted, shortest_hops


# ============================================================
# Helper for printing tests
# ============================================================

def print_test_result(
    name,
    G,
    source,
    target
):

    routes, shortest_hops = (
        find_distinct_alternative_routes(
            G,
            source,
            target
        )
    )

    print()
    print(
        f"===== {name} ====="
    )

    print(
        "Shortest hops:",
        shortest_hops
    )

    print(
        "Distinct routes:",
        len(routes)
    )

    for i, route in enumerate(
        routes,
        start=1
    ):

        print(
            f"Route {i}:",
            route
        )

    # Print pairwise diversity
    if len(routes) >= 2:

        print(
            "Pairwise diversity:"
        )

        for i in range(
            len(routes)
        ):

            for j in range(
                i + 1,
                len(routes)
            ):

                d = path_diversity(
                    routes[i],
                    routes[j]
                )

                print(
                    f"  Route {i + 1} vs "
                    f"Route {j + 1}: "
                    f"{d:.3f}"
                )


# ============================================================
# Test 1
# Same corridor + small detour
# Expected:
#   1 distinct route
# ============================================================

def test_same_corridor():

    G = nx.Graph()

    G.add_edges_from([
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),

        # small detour
        (1, 5),
        (5, 2)
    ])

    print_test_result(
        "SAME CORRIDOR TEST",
        G,
        0,
        4
    )


# ============================================================
# Test 2
# Two completely separate corridors
# Expected:
#   2 distinct routes
# ============================================================

def test_two_real_corridors():

    G = nx.Graph()

    G.add_edges_from([
        # corridor A
        (0, 1),
        (1, 2),
        (2, 6),

        # corridor B
        (0, 3),
        (3, 4),
        (4, 6)
    ])

    print_test_result(
        "TWO CORRIDOR TEST",
        G,
        0,
        6
    )


# ============================================================
# Test 3
# Three completely separate corridors
# Expected:
#   3 distinct routes
# ============================================================

def test_three_corridors():

    G = nx.Graph()

    G.add_edges_from([
        # route 1
        (0, 1),
        (1, 2),
        (2, 9),

        # route 2
        (0, 3),
        (3, 4),
        (4, 9),

        # route 3
        (0, 5),
        (5, 6),
        (6, 9)
    ])

    print_test_result(
        "THREE CORRIDOR TEST",
        G,
        0,
        9
    )


# ============================================================
# Test 4
# Shared first half, then diverge
#
# Route A:
# 0-1-2-3-7
#
# Route B:
# 0-1-2-4-7
#
# They share:
# 0-1
# 1-2
#
# Each route has 4 edges
#
# overlap = 2 / 4 = 0.5
# diversity = 0.5
#
# Since threshold = 0.4,
# EXPECTED:
#   2 distinct routes
# ============================================================

def test_shared_first_half():

    G = nx.Graph()

    G.add_edges_from([
        (0, 1),
        (1, 2),

        # branch A
        (2, 3),
        (3, 7),

        # branch B
        (2, 4),
        (4, 7)
    ])

    print_test_result(
        "SHARED FIRST HALF TEST",
        G,
        0,
        7
    )


# ============================================================
# Test 5
# Shared only near origin and destination
#
# Route A:
# 0-1-2-3-8-9
#
# Route B:
# 0-1-4-5-8-9
#
# Shared edges:
# 0-1
# 8-9
#
# 5 edges per path
#
# overlap = 2/5 = 0.4
# diversity = 0.6
#
# EXPECTED:
#   2 distinct routes
# ============================================================

def test_shared_ends():

    G = nx.Graph()

    G.add_edges_from([
        # common start
        (0, 1),

        # corridor A
        (1, 2),
        (2, 3),
        (3, 8),

        # corridor B
        (1, 4),
        (4, 5),
        (5, 8),

        # common end
        (8, 9)
    ])

    print_test_result(
        "SHARED ENDS TEST",
        G,
        0,
        9
    )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    test_same_corridor()

    test_two_real_corridors()

    test_three_corridors()

    test_shared_first_half()

    test_shared_ends()