from src.paths import PROJECT_ROOT, RESULTS_DIR as CANONICAL_RESULTS_DIR, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, result_path, project_path
from pathlib import Path

from src.mosp import mosp
from src.taipei_metro import (
    build_taipei_metro_graph,
    make_od_graph,
    format_path,
)


# =========================================================
# 1. File paths
# =========================================================

ROOT = PROJECT_ROOT

DATA_DIR = TAIPEI_METRO_DATA_DIR

STATION_FILE = (
    DATA_DIR
    / "臺北捷運路線車站資料服務_NEW_fixed (1).csv"
)

TRAVEL_TIME_FILE = (
    DATA_DIR
    / "臺北捷運相鄰兩站間之行駛時間及停靠站時間(1150830).csv"
)

TRANSFER_FILE = (
    DATA_DIR
    / "臺北捷運轉乘車站轉乘步行時間資料.csv"
)


# =========================================================
# 2. OD
# =========================================================

ORIGIN = "亞東醫院站"
DESTINATION = "公館站"

NUM_OBJECTIVES = 3


# =========================================================
# 3. Reconstruct path from Label
# =========================================================

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
# 4. Convert seconds to readable time
# =========================================================

def format_time(seconds):

    seconds = int(seconds)

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    return (
        f"{minutes} 分 "
        f"{remaining_seconds} 秒"
    )


# =========================================================
# 5. Show detailed edge information
# =========================================================

def show_edge_details(
    graph,
    path
):

    print()
    print("-" * 80)
    print("EDGE DETAILS")
    print("-" * 80)

    total = [
        0,
        0,
        0
    ]

    for u, v in zip(
        path,
        path[1:]
    ):

        selected_edge = None

        for edge in graph.neighbors(u):

            if edge.to == v:

                selected_edge = edge
                break

        if selected_edge is None:

            print(
                f"WARNING: edge not found: "
                f"{u} -> {v}"
            )

            continue


        edge = selected_edge

        for i in range(3):

            total[i] += (
                edge.costs[i]
            )


        # ---------------------------------------------
        # Ignore virtual access / egress in display
        # ---------------------------------------------

        if edge.kind in {
            "access",
            "egress"
        }:

            continue


        u_info = graph.node_info.get(
            u,
            {}
        )

        v_info = graph.node_info.get(
            v,
            {}
        )

        u_name = u_info.get(
            "station_name",
            u
        )

        v_name = v_info.get(
            "station_name",
            v
        )

        u_line = u_info.get(
            "line_id",
            ""
        )

        v_line = v_info.get(
            "line_id",
            ""
        )


        # ---------------------------------------------
        # Ride edge
        # ---------------------------------------------

        if edge.kind == "ride":

            running = edge.info.get(
                "travel_time",
                0
            )

            stop = edge.info.get(
                "stop_time",
                0
            )

            removed = edge.info.get(
                "origin_stop_time_removed",
                False
            )

            print(
                f"RIDE      "
                f"{u_name}[{u_line}]"
                f" -> "
                f"{v_name}[{v_line}]"
            )

            print(
                f"          running = "
                f"{running} sec"
            )

            print(
                f"          stop     = "
                f"{stop} sec"
            )

            if removed:

                print(
                    "          "
                    "(origin stop time removed)"
                )

            print(
                f"          edge C1  = "
                f"{edge.costs[0]} sec"
            )


        # ---------------------------------------------
        # Transfer edge
        # ---------------------------------------------

        elif edge.kind == "transfer":

            walking = edge.info.get(
                "walking_seconds",
                edge.costs[0]
            )

            print(
                f"TRANSFER  "
                f"{u_name}[{u_line}]"
                f" -> "
                f"{v_name}[{v_line}]"
            )

            print(
                f"          walking = "
                f"{walking} sec"
            )

            print(
                f"          transfer count +1"
            )


    print()
    print(
        "Recalculated total costs:"
    )

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


# =========================================================
# 6. Main
# =========================================================

def main():

    # -----------------------------------------------------
    # Build base Taipei Metro graph
    # -----------------------------------------------------

    print("=" * 80)
    print("BUILD TAIPEI METRO NETWORK")
    print("=" * 80)

    (
        base_graph,
        build_stats
    ) = build_taipei_metro_graph(
        STATION_FILE,
        TRAVEL_TIME_FILE,
        TRANSFER_FILE
    )


    print()
    print("Network statistics:")

    for key, value in build_stats.items():

        if key in {
            "skipped_pairs",
            "states_without_stop_time_data",
            "unresolved_stop_times",
        }:
            continue

        print(
            f"  {key}: {value}"
        )


    # -----------------------------------------------------
    # Check unresolved stop times
    # -----------------------------------------------------

    if (
        "unresolved_stop_times"
        in build_stats
    ):

        unresolved = (
            build_stats[
                "unresolved_stop_times"
            ]
        )

        print()
        print(
            "Unresolved stop times:"
        )

        print(
            unresolved
        )


    # -----------------------------------------------------
    # Build OD graph
    # -----------------------------------------------------

    print()
    print("=" * 80)
    print(
        f"OD: {ORIGIN} -> {DESTINATION}"
    )
    print("=" * 80)


    (
        graph,
        source,
        target
    ) = make_od_graph(
        base_graph,
        ORIGIN,
        DESTINATION
    )


    # -----------------------------------------------------
    # Run MOSP
    # -----------------------------------------------------

    (
        labels,
        stats
    ) = mosp(
        graph,
        source,
        NUM_OBJECTIVES,
        return_stats=True
    )


    target_labels = [
        label
        for label in labels[target]
        if label.active
    ]


    # Sort by:
    # C1 -> C2 -> C3
    target_labels.sort(
        key=lambda label:
            label.costs
    )


    # -----------------------------------------------------
    # Search statistics
    # -----------------------------------------------------

    print()
    print("MOSP SEARCH STATISTICS")
    print("-" * 80)

    for key, value in stats.items():

        print(
            f"{key}: {value}"
        )


    # -----------------------------------------------------
    # Pareto routes
    # -----------------------------------------------------

    print()
    print("=" * 80)
    print("PARETO ROUTES")
    print("=" * 80)

    print(
        f"Number of Pareto labels: "
        f"{len(target_labels)}"
    )


    if not target_labels:

        print(
            "No route found."
        )

        return


    for index, label in enumerate(
        target_labels,
        start=1
    ):

        path = reconstruct_path(
            label
        )

        c1 = label.costs[0]
        c2 = label.costs[1]
        c3 = label.costs[2]


        print()
        print(
            f"Route {index}"
        )

        print(
            "-" * 80
        )

        print(
            f"Total travel time : "
            f"{c1} sec "
            f"({c1 / 60:.2f} min)"
        )

        print(
            f"Transfers         : "
            f"{c2}"
        )

        print(
            f"Transfer walking  : "
            f"{c3} sec "
            f"({c3 / 60:.2f} min)"
        )

        print()
        print(
            format_path(
                graph,
                path
            )
        )


        # ---------------------------------------------
        # Detailed check
        # ---------------------------------------------

        show_edge_details(
            graph,
            path
        )


    print()
    print("=" * 80)
    print("DONE")
    print("=" * 80)


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":

    main()