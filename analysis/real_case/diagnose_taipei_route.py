from src.paths import PROJECT_ROOT, RESULTS_DIR as CANONICAL_RESULTS_DIR, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, result_path, project_path
from pathlib import Path

from src.mosp import mosp
from src.taipei_metro import (
    build_taipei_metro_graph,
    make_od_graph,
    format_path,
)


# =========================================================
# 1. Find data files
# =========================================================

ROOT = PROJECT_ROOT


def find_csv(keyword):
    matches = sorted(TAIPEI_METRO_DATA_DIR.glob(f"*{keyword}*.csv"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one model input for {keyword}: {matches}")
    return matches[0]


STATION_FILE = find_csv(
    "路線車站"
)

TRAVEL_TIME_FILE = find_csv(
    "相鄰兩站"
)

TRANSFER_FILE = find_csv(
    "轉乘步行"
)


# =========================================================
# 2. OD
# =========================================================

ORIGIN = "亞東醫院站"
DESTINATION = "公館站"

NUM_OBJECTIVES = 3


# =========================================================
# 3. Helper
# =========================================================

def format_time(seconds):

    seconds = int(seconds)

    minute = seconds // 60
    second = seconds % 60

    return f"{minute} 分 {second} 秒"


def reconstruct_path(label):

    path = []

    current = label

    while current is not None:

        path.append(
            current.node
        )

        current = (
            current.predecessor
        )

    path.reverse()

    return path


# =========================================================
# 4. Resolve physical station name
#
#    台 / 臺 automatically handled
# =========================================================

def resolve_station_name(
    graph,
    station_name
):

    # exact match
    if station_name in graph.states_by_name:
        return station_name

    candidates = [
        station_name.replace(
            "臺",
            "台"
        ),
        station_name.replace(
            "台",
            "臺"
        ),
    ]

    for candidate in candidates:

        if candidate in graph.states_by_name:
            return candidate

    raise ValueError(
        f"找不到車站：{station_name}"
    )


# =========================================================
# 5. Find route-state node
# =========================================================

def get_state(
    graph,
    station_name,
    line_id
):

    station_name = resolve_station_name(
        graph,
        station_name
    )

    candidates = []

    for node in graph.states_by_name[
        station_name
    ]:

        info = graph.node_info[
            node
        ]

        if (
            info.get("line_id")
            == line_id
        ):

            candidates.append(
                node
            )

    if len(candidates) == 0:

        raise ValueError(
            f"\n找不到 route-state："
            f"{station_name}[{line_id}]\n"
        )

    if len(candidates) > 1:

        print(
            f"WARNING: "
            f"{station_name}[{line_id}] "
            f"有多個 route-state："
        )

        for node in candidates:

            print(
                "  ",
                node
            )

        raise ValueError(
            "route-state 不唯一，"
            "請檢查路線資料。"
        )

    return candidates[0]


# =========================================================
# 6. Find edge u -> v
# =========================================================

def find_edge(
    graph,
    u,
    v
):

    candidates = [
        edge
        for edge in graph.neighbors(u)
        if edge.to == v
    ]

    if len(candidates) == 0:

        u_info = graph.node_info.get(
            u,
            {}
        )

        v_info = graph.node_info.get(
            v,
            {}
        )

        raise ValueError(
            "\n找不到 edge：\n"
            f"{u_info.get('station_name', u)}"
            f"[{u_info.get('line_id', '')}]"
            " -> "
            f"{v_info.get('station_name', v)}"
            f"[{v_info.get('line_id', '')}]"
        )

    if len(candidates) > 1:

        print(
            f"WARNING: {u} -> {v} "
            f"有 {len(candidates)} 條 edge，"
            "使用第一條。"
        )

    return candidates[0]


# =========================================================
# 7. Human-readable node
# =========================================================

def node_name(
    graph,
    node
):

    info = graph.node_info.get(
        node,
        {}
    )

    kind = info.get(
        "kind"
    )

    if kind == "station":

        return (
            f"{info['station_name']}"
            f"[{info['line_id']}]"
        )

    return node


# =========================================================
# 8. Calculate forced route
# =========================================================

def calculate_forced_route(
    graph,
    source,
    target
):

    # -----------------------------------------------------
    # Forced route:
    #
    # 亞東醫院 BL
    # -> 台北車站 BL
    # -> transfer BL -> R
    # -> 中正紀念堂 R
    # -> transfer R -> G
    # -> 公館 G
    # -----------------------------------------------------

    route_spec = [

        ("亞東醫院站", "BL"),
        ("府中站", "BL"),
        ("板橋站", "BL"),
        ("新埔站", "BL"),
        ("江子翠站", "BL"),
        ("龍山寺站", "BL"),
        ("西門站", "BL"),
        ("台北車站", "BL"),

        # transfer at Taipei Main Station
        ("台北車站", "R"),

        ("台大醫院站", "R"),
        ("中正紀念堂站", "R"),

        # transfer at Chiang Kai-Shek Memorial Hall
        ("中正紀念堂站", "G"),

        ("古亭站", "G"),
        ("台電大樓站", "G"),
        ("公館站", "G"),
    ]


    route_states = []

    for (
        station,
        line
    ) in route_spec:

        state = get_state(
            graph,
            station,
            line
        )

        route_states.append(
            state
        )


    # Include virtual source / target
    full_path = (
        [source]
        + route_states
        + [target]
    )


    total = [
        0,
        0,
        0
    ]


    print()
    print("=" * 90)
    print("FORCED ROUTE")
    print("=" * 90)

    print(
        format_path(
            graph,
            full_path
        )
    )

    print()
    print("=" * 90)
    print("FORCED ROUTE EDGE DETAILS")
    print("=" * 90)


    for u, v in zip(
        full_path,
        full_path[1:]
    ):

        edge = find_edge(
            graph,
            u,
            v
        )

        for i in range(3):

            total[i] += (
                edge.costs[i]
            )


        # -------------------------------------------------
        # Access / egress
        # -------------------------------------------------

        if edge.kind in {
            "access",
            "egress"
        }:

            continue


        # -------------------------------------------------
        # Ride
        # -------------------------------------------------

        if edge.kind == "ride":

            running = int(
                edge.info.get(
                    "travel_time",
                    0
                )
            )

            stop = int(
                edge.info.get(
                    "stop_time",
                    0
                )
            )

            removed = int(
                edge.info.get(
                    "origin_stop_time_removed",
                    0
                )
            )

            print(
                f"RIDE      "
                f"{node_name(graph, u)}"
                f" -> "
                f"{node_name(graph, v)}"
            )

            print(
                f"          running = "
                f"{running} sec"
            )

            print(
                f"          stop     = "
                f"{stop} sec"
            )

            if removed > 0:

                print(
                    f"          origin stop removed "
                    f"= {removed} sec"
                )

            print(
                f"          C = "
                f"{edge.costs}"
            )


        # -------------------------------------------------
        # Transfer
        # -------------------------------------------------

        elif edge.kind == "transfer":

            walking = int(
                edge.info.get(
                    "walking_seconds",
                    edge.costs[0]
                )
            )

            print(
                f"TRANSFER  "
                f"{node_name(graph, u)}"
                f" -> "
                f"{node_name(graph, v)}"
            )

            print(
                f"          walking = "
                f"{walking} sec"
            )

            print(
                f"          C = "
                f"{edge.costs}"
            )


    total = tuple(
        total
    )


    print()
    print("=" * 90)
    print("FORCED ROUTE TOTAL")
    print("=" * 90)

    print(
        f"C1 = {total[0]} sec "
        f"= {format_time(total[0])}"
    )

    print(
        f"C2 = {total[1]} transfers"
    )

    print(
        f"C3 = {total[2]} sec walking "
        f"= {total[2] / 60:.2f} min"
    )


    return (
        full_path,
        total
    )


# =========================================================
# 9. Dominance
# =========================================================

def dominates(
    cost_a,
    cost_b
):

    no_worse = all(
        a <= b
        for a, b
        in zip(
            cost_a,
            cost_b
        )
    )

    strictly_better = any(
        a < b
        for a, b
        in zip(
            cost_a,
            cost_b
        )
    )

    return (
        no_worse
        and strictly_better
    )


# =========================================================
# 10. Main
# =========================================================

def main():

    # -----------------------------------------------------
    # Build graph
    # -----------------------------------------------------

    print()
    print("=" * 90)
    print("BUILD TAIPEI METRO NETWORK")
    print("=" * 90)

    (
        base_graph,
        build_stats
    ) = build_taipei_metro_graph(
        STATION_FILE,
        TRAVEL_TIME_FILE,
        TRANSFER_FILE
    )


    # =====================================================
    # PART A
    # Print skipped travel rows
    # =====================================================

    print()
    print("=" * 90)
    print("SKIPPED TRAVEL ROWS")
    print("=" * 90)

    print(
        "Total skipped rows:",
        build_stats[
            "skipped_travel_rows"
        ]
    )


    skipped_pairs = (
        build_stats.get(
            "skipped_pairs",
            []
        )
    )


    print(
        "Unique skipped station pairs:",
        len(skipped_pairs)
    )

    print()


    if not skipped_pairs:

        print(
            "No skipped station pairs."
        )

    else:

        for i, pair in enumerate(
            skipped_pairs,
            start=1
        ):

            station_a = pair[0]
            station_b = pair[1]

            print(
                f"{i:2d}. "
                f"{station_a}"
                f" -> "
                f"{station_b}"
            )


    # -----------------------------------------------------
    # Other network stats
    # -----------------------------------------------------

    print()
    print("=" * 90)
    print("NETWORK STATISTICS")
    print("=" * 90)

    for key, value in build_stats.items():

        if key in {
            "skipped_pairs",
            "unresolved_stop_times",
        }:

            continue

        print(
            f"{key}: {value}"
        )


    # =====================================================
    # Build OD graph
    # =====================================================

    (
        graph,
        source,
        target
    ) = make_od_graph(
        base_graph,
        ORIGIN,
        DESTINATION
    )


    # =====================================================
    # PART B
    # Force Taipei Main Station route
    # =====================================================

    (
        forced_path,
        forced_cost
    ) = calculate_forced_route(
        graph,
        source,
        target
    )


    # =====================================================
    # Run MOSP normally
    # =====================================================

    (
        labels,
        stats
    ) = mosp(
        graph,
        source,
        NUM_OBJECTIVES,
        return_stats=True
    )


    pareto_labels = [
        label
        for label in labels[target]
        if label.active
    ]

    pareto_labels.sort(
        key=lambda x: x.costs
    )


    print()
    print("=" * 90)
    print("MOSP PARETO ROUTES")
    print("=" * 90)


    for i, label in enumerate(
        pareto_labels,
        start=1
    ):

        path = reconstruct_path(
            label
        )

        print()
        print(
            f"Pareto route {i}"
        )

        print(
            "Path:",
            format_path(
                graph,
                path
            )
        )

        print(
            "Costs:",
            label.costs
        )

        print(
            f"Time: "
            f"{format_time(label.costs[0])}"
        )

        print(
            f"Transfers: "
            f"{label.costs[1]}"
        )

        print(
            f"Walking: "
            f"{label.costs[2]} sec"
        )


    # =====================================================
    # Compare forced route with Pareto routes
    # =====================================================

    print()
    print("=" * 90)
    print("DOMINANCE CHECK")
    print("=" * 90)

    print(
        "Forced Taipei-Main route:",
        forced_cost
    )


    dominated_by = []

    for i, label in enumerate(
        pareto_labels,
        start=1
    ):

        if dominates(
            label.costs,
            forced_cost
        ):

            dominated_by.append(
                (
                    i,
                    label.costs
                )
            )


    if dominated_by:

        print()
        print(
            "RESULT: Forced route is dominated."
        )

        print(
            "Dominated by:"
        )

        for (
            index,
            costs
        ) in dominated_by:

            print(
                f"  Pareto route {index}: "
                f"{costs}"
            )

    else:

        print()
        print(
            "RESULT: Forced route is NOT dominated "
            "by the current Pareto routes."
        )


    print()
    print("=" * 90)
    print("DONE")
    print("=" * 90)


if __name__ == "__main__":

    main()