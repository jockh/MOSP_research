from src.paths import PROJECT_ROOT, RESULTS_DIR as CANONICAL_RESULTS_DIR, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, result_path, project_path
from pathlib import Path

import pandas as pd

from src.taipei_metro import (
    build_taipei_metro_graph,
    clean_station_name,
)


# =========================================================
# 1. Locate data files
# =========================================================

ROOT = PROJECT_ROOT


def find_csv(keyword):
    matches = sorted(TAIPEI_METRO_DATA_DIR.glob(f"*{keyword}*.csv"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one model input for {keyword}: {matches}")
    return matches[0]


STATION_FILE = find_csv("路線車站")
TRAVEL_TIME_FILE = find_csv("相鄰兩站")
TRANSFER_FILE = find_csv("轉乘步行")


# =========================================================
# 2. Helpers
# =========================================================

def node_label(graph, node):

    info = graph.node_info[node]

    return (
        f"{info.get('station_name', '?')}"
        f"[{info.get('line_id', '?')}]"
        f"  ({node})"
    )


def get_ride_neighbors(graph, node):

    result = []

    for edge in graph.neighbors(node):

        if edge.kind == "ride":

            result.append(
                (
                    edge.to,
                    edge
                )
            )

    return result


def get_transfer_neighbors(graph, node):

    result = []

    for edge in graph.neighbors(node):

        if edge.kind == "transfer":

            result.append(
                (
                    edge.to,
                    edge
                )
            )

    return result


# =========================================================
# 3. Determine route endpoints
# =========================================================

def build_route_ranges(graph):

    route_orders = {}

    for node in graph.nodes():

        info = graph.node_info.get(
            node,
            {}
        )

        if info.get("kind") != "station":
            continue

        route_key = info[
            "route_key"
        ]

        order = int(
            info["station_order"]
        )

        if route_key not in route_orders:
            route_orders[route_key] = []

        route_orders[
            route_key
        ].append(order)

    route_ranges = {}

    for route_key, orders in route_orders.items():

        route_ranges[
            route_key
        ] = (
            min(orders),
            max(orders)
        )

    return route_ranges


def is_route_endpoint(
    graph,
    node,
    route_ranges
):

    info = graph.node_info[node]

    route_key = info[
        "route_key"
    ]

    order = int(
        info["station_order"]
    )

    minimum, maximum = (
        route_ranges[
            route_key
        ]
    )

    return (
        order == minimum
        or order == maximum
    )


# =========================================================
# 4. Raw travel-time rows
# =========================================================

def get_related_rows(
    travel_df,
    station_name
):

    rows = []

    for _, row in travel_df.iterrows():

        station_a = clean_station_name(
            row["stationA"]
        )

        station_b = clean_station_name(
            row["stationB"]
        )

        if (
            station_a == station_name
            or station_b == station_name
        ):

            rows.append(
                {
                    "stationA": station_a,
                    "stationB": station_b,
                    "traveltime": row[
                        "traveltime"
                    ],
                    "stoptime": row[
                        "stoptime"
                    ],
                }
            )

    return rows


# =========================================================
# 5. Check one zero-stop state
# =========================================================

def inspect_zero_state(
    graph,
    node,
    travel_df,
    route_ranges
):

    info = graph.node_info[node]

    station_name = info[
        "station_name"
    ]

    line_id = info[
        "line_id"
    ]

    route_key = info[
        "route_key"
    ]

    order = int(
        info["station_order"]
    )

    stop_time = int(
        info.get(
            "stop_time",
            0
        )
    )

    ride_neighbors = (
        get_ride_neighbors(
            graph,
            node
        )
    )

    transfer_neighbors = (
        get_transfer_neighbors(
            graph,
            node
        )
    )

    endpoint = is_route_endpoint(
        graph,
        node,
        route_ranges
    )

    print()
    print("=" * 90)

    print(
        f"{station_name}[{line_id}]"
    )

    print("-" * 90)

    print(
        f"node          : {node}"
    )

    print(
        f"route_key     : {route_key}"
    )

    print(
        f"station_order : {order}"
    )

    print(
        f"stop_time     : {stop_time} sec"
    )

    print(
        f"route endpoint: {endpoint}"
    )

    print(
        f"ride degree   : "
        f"{len(ride_neighbors)}"
    )

    print(
        f"transfer degree: "
        f"{len(transfer_neighbors)}"
    )


    # -----------------------------------------------------
    # Ride neighbors
    # -----------------------------------------------------

    print()
    print("RIDE NEIGHBORS")

    if not ride_neighbors:

        print("  None")

    else:

        for neighbor, edge in ride_neighbors:

            n_info = graph.node_info[
                neighbor
            ]

            print(
                "  -> "
                f"{n_info['station_name']}"
                f"[{n_info['line_id']}]"
            )

            print(
                f"     travel_time = "
                f"{edge.info.get('travel_time')}"
            )

            print(
                f"     stop_time used = "
                f"{edge.info.get('stop_time')}"
            )

            print(
                f"     edge C1 = "
                f"{edge.costs[0]}"
            )


    # -----------------------------------------------------
    # Transfer neighbors
    # -----------------------------------------------------

    if transfer_neighbors:

        print()
        print("TRANSFER NEIGHBORS")

        for neighbor, edge in transfer_neighbors:

            n_info = graph.node_info[
                neighbor
            ]

            print(
                "  -> "
                f"{n_info['station_name']}"
                f"[{n_info['line_id']}]"
                f"  cost={edge.costs}"
            )


    # -----------------------------------------------------
    # Raw CSV rows
    # -----------------------------------------------------

    related_rows = get_related_rows(
        travel_df,
        station_name
    )

    print()
    print("RAW TRAVEL-TIME ROWS")

    if not related_rows:

        print(
            "  *** NO RAW ROW FOUND ***"
        )

    else:

        for row in related_rows:

            print(
                f"  {row['stationA']}"
                f" -> "
                f"{row['stationB']}"
                f" | running={row['traveltime']}"
                f" | stop={row['stoptime']}"
            )


    # -----------------------------------------------------
    # Classification
    # -----------------------------------------------------

    print()
    print("CLASSIFICATION")

    if endpoint:

        print(
            "  ENDPOINT"
        )

        print(
            "  Zero stop time is potentially legitimate "
            "because this route-state is at the end "
            "of its route sequence."
        )

        return "endpoint"

    else:

        print(
            "  *** WARNING: INTERNAL ZERO-STOP STATE ***"
        )

        print(
            "  This route-state is NOT an endpoint."
        )

        print(
            "  A zero stop time here may cause travel "
            "time to be underestimated when a passenger "
            "continues through this station."
        )

        return "internal"


# =========================================================
# 6. Check all ride edges
# =========================================================

def check_zero_dwell_edges(
    graph
):

    zero_edges = []

    for u in graph.nodes():

        u_info = graph.node_info.get(
            u,
            {}
        )

        if u_info.get("kind") != "station":
            continue

        for edge in graph.neighbors(u):

            if edge.kind != "ride":
                continue

            stop_time = int(
                edge.info.get(
                    "stop_time",
                    0
                )
            )

            if stop_time == 0:

                zero_edges.append(
                    (
                        u,
                        edge.to,
                        edge
                    )
                )

    return zero_edges


# =========================================================
# 7. Main
# =========================================================

def main():

    print()
    print("=" * 90)
    print("BUILD TAIPEI METRO NETWORK")
    print("=" * 90)

    (
        graph,
        build_stats
    ) = build_taipei_metro_graph(
        STATION_FILE,
        TRAVEL_TIME_FILE,
        TRANSFER_FILE
    )


    travel_df = pd.read_csv(
        TRAVEL_TIME_FILE,
        encoding="cp950"
    )


    # =====================================================
    # Network summary
    # =====================================================

    print()
    print("=" * 90)
    print("NETWORK SUMMARY")
    print("=" * 90)

    print(
        "nodes:",
        build_stats[
            "nodes"
        ]
    )

    print(
        "states_with_positive_stop_time:",
        build_stats[
            "states_with_positive_stop_time"
        ]
    )

    print(
        "states_with_zero_stop_time:",
        build_stats[
            "states_with_zero_stop_time"
        ]
    )


    # =====================================================
    # Route ranges
    # =====================================================

    route_ranges = build_route_ranges(
        graph
    )


    # =====================================================
    # Find zero stop states
    # =====================================================

    zero_states = []

    for node in graph.nodes():

        info = graph.node_info.get(
            node,
            {}
        )

        if info.get("kind") != "station":
            continue

        stop_time = int(
            info.get(
                "stop_time",
                0
            )
        )

        if stop_time == 0:

            zero_states.append(
                node
            )


    print()
    print("=" * 90)
    print("ZERO STOP-TIME STATES")
    print("=" * 90)

    print(
        f"Total = {len(zero_states)}"
    )


    endpoint_zero = []
    internal_zero = []


    for node in zero_states:

        result = inspect_zero_state(
            graph,
            node,
            travel_df,
            route_ranges
        )

        if result == "endpoint":

            endpoint_zero.append(
                node
            )

        else:

            internal_zero.append(
                node
            )


    # =====================================================
    # Unresolved inference cases
    # =====================================================

    print()
    print("=" * 90)
    print("UNRESOLVED STOP-TIME INFERENCE")
    print("=" * 90)

    unresolved = build_stats.get(
        "unresolved_stop_times",
        []
    )

    if not unresolved:

        print(
            "None"
        )

    else:

        for item in unresolved:

            print(
                item
            )


    # =====================================================
    # Zero dwell ride edges
    # =====================================================

    zero_edges = (
        check_zero_dwell_edges(
            graph
        )
    )

    print()
    print("=" * 90)
    print("RIDE EDGES USING ZERO DWELL")
    print("=" * 90)

    print(
        f"Total = {len(zero_edges)}"
    )

    for u, v, edge in zero_edges:

        print(
            f"{node_label(graph, u)}"
        )

        print(
            "    -> "
            f"{node_label(graph, v)}"
        )

        print(
            f"    running = "
            f"{edge.info.get('travel_time')} sec"
        )

        print(
            f"    dwell   = "
            f"{edge.info.get('stop_time')} sec"
        )

        print(
            f"    C1      = "
            f"{edge.costs[0]} sec"
        )


    # =====================================================
    # Final diagnosis
    # =====================================================

    print()
    print("=" * 90)
    print("FINAL DIAGNOSIS")
    print("=" * 90)

    print(
        "Zero-stop states:",
        len(zero_states)
    )

    print(
        "Endpoint zero-stop states:",
        len(endpoint_zero)
    )

    print(
        "Internal zero-stop states:",
        len(internal_zero)
    )

    print(
        "Unresolved inference cases:",
        len(unresolved)
    )


    if len(internal_zero) == 0:

        print()
        print(
            "PASS:"
        )

        print(
            "All zero stop-time states are route endpoints."
        )

        print(
            "No internal station currently has stop_time = 0."
        )

    else:

        print()
        print(
            "*** CHECK REQUIRED ***"
        )

        print(
            "The following internal route-state nodes "
            "have stop_time = 0:"
        )

        for node in internal_zero:

            print(
                "  ",
                node_label(
                    graph,
                    node
                )
            )


    if unresolved:

        print()
        print(
            "*** CHECK unresolved_stop_times as well. ***"
        )


    print()
    print("=" * 90)
    print("DONE")
    print("=" * 90)


if __name__ == "__main__":
    main()