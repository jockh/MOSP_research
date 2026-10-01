from pathlib import Path
import time

import pandas as pd

from src.taipei_metro import build_taipei_metro_graph


# =========================================================
# PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = (
    ROOT
    / "data"
    / "taipei_metro"
)

EXP5_DIR = (
    ROOT
    / "experiments"
    / "results"
    / "experiment_05_all_od"
)

RESULT_DIR = (
    ROOT
    / "experiments"
    / "results"
    / "experiment_06b_all_od_dfs"
)

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


STATION_FILE = (
    DATA_DIR
    / "臺北捷運路線車站資料服務_NEW_fixed (1).csv"
)

TRAVEL_FILE = (
    DATA_DIR
    / "臺北捷運相鄰兩站間之行駛時間及停靠站時間(1150830).csv"
)

TRANSFER_FILE = (
    DATA_DIR
    / "臺北捷運轉乘車站轉乘步行時間資料.csv"
)


EXP5_OD_FILE = (
    EXP5_DIR
    / "all_od_summary.csv"
)


RAW_FILE = (
    RESULT_DIR
    / "all_od_dfs_raw.csv"
)

CHECKPOINT_FILE = (
    RESULT_DIR
    / "all_od_dfs_checkpoint.csv"
)

SUMMARY_FILE = (
    RESULT_DIR
    / "all_od_dfs_summary_statistics.csv"
)

MERGED_FILE = (
    RESULT_DIR
    / "dfs_vs_mosp_all_od.csv"
)

TOP_SIMPLE_FILE = (
    RESULT_DIR
    / "top_simple_path_od_pairs.csv"
)

TOP_PARTIAL_FILE = (
    RESULT_DIR
    / "top_dfs_partial_state_od_pairs.csv"
)


# =========================================================
# BUILD GRAPH
# =========================================================

graph, build_stats = build_taipei_metro_graph(
    station_file=STATION_FILE,
    travel_time_file=TRAVEL_FILE,
    transfer_file=TRANSFER_FILE
)


PHYSICAL_STATIONS = sorted(
    graph.states_by_name.keys()
)


directed_edges = sum(
    len(graph.neighbors(node))
    for node in graph.nodes()
)


print("=" * 80)
print("EXPERIMENT 6B")
print("ALL-OD EXHAUSTIVE DFS BENCHMARK")
print("=" * 80)

print()

print("Physical stations:", len(PHYSICAL_STATIONS))
print("Graph nodes:", len(graph.nodes()))
print("Directed edges:", directed_edges)

print(
    "Ordered OD pairs:",
    len(PHYSICAL_STATIONS)
    *
    (
        len(PHYSICAL_STATIONS) - 1
    )
)

print()


# =========================================================
# DFS SIMPLE PATH COUNTER
# =========================================================

def count_simple_paths(
    graph,
    origin_name,
    destination_name
):
    """
    Exhaustively enumerate all simple paths from all
    route-state nodes of origin to any route-state node
    of destination.

    No timeout.
    No path-count limit.

    A simple path cannot visit the same route-state node
    more than once.
    """

    origin_states = list(
        graph.states_by_name[
            origin_name
        ]
    )

    destination_states = set(
        graph.states_by_name[
            destination_name
        ]
    )


    path_count = 0

    explored_partial_paths = 0

    max_depth = 0


    start_time = (
        time.perf_counter()
    )


    def dfs(
        current,
        visited,
        depth
    ):

        nonlocal path_count
        nonlocal explored_partial_paths
        nonlocal max_depth


        explored_partial_paths += 1


        if depth > max_depth:
            max_depth = depth


        # ---------------------------------------------
        # Destination reached
        #
        # Once destination is reached, this path is
        # counted and NOT expanded further.
        # ---------------------------------------------

        if current in destination_states:

            path_count += 1

            return


        # ---------------------------------------------
        # Expand neighbors
        # ---------------------------------------------

        for edge in graph.neighbors(
            current
        ):

            nxt = edge.to


            # Simple-path constraint
            if nxt in visited:
                continue


            visited.add(nxt)


            dfs(
                current=nxt,
                visited=visited,
                depth=depth + 1
            )


            visited.remove(nxt)


    # =================================================
    # Origin can have multiple route-state nodes
    # =================================================

    for start_node in origin_states:

        dfs(
            current=start_node,
            visited={start_node},
            depth=1
        )


    runtime_seconds = (
        time.perf_counter()
        -
        start_time
    )


    return {

        "origin":
            origin_name,

        "destination":
            destination_name,

        "simple_path_count":
            path_count,

        "explored_partial_paths":
            explored_partial_paths,

        "max_depth":
            max_depth,

        "dfs_runtime_seconds":
            runtime_seconds

    }


# =========================================================
# RUN ALL OD PAIRS
# =========================================================

rows = []


total_stations = len(
    PHYSICAL_STATIONS
)

total_od = (
    total_stations
    *
    (
        total_stations - 1
    )
)


global_start = (
    time.perf_counter()
)


completed_od = 0


for origin_index, origin in enumerate(
    PHYSICAL_STATIONS,
    start=1
):

    print()
    print("=" * 80)

    print(
        f"ORIGIN "
        f"{origin_index}/{total_stations}: "
        f"{origin}"
    )

    print("=" * 80)


    origin_start = (
        time.perf_counter()
    )


    origin_rows = []


    for destination in PHYSICAL_STATIONS:

        if destination == origin:
            continue


        result = count_simple_paths(
            graph=graph,
            origin_name=origin,
            destination_name=destination
        )


        rows.append(result)

        origin_rows.append(result)


        completed_od += 1


        elapsed_global = (
            time.perf_counter()
            -
            global_start
        )


        print(
            f"[{completed_od}/{total_od}] "
            f"{origin} -> {destination} | "
            f"paths={result['simple_path_count']} | "
            f"partial={result['explored_partial_paths']} | "
            f"depth={result['max_depth']} | "
            f"time={result['dfs_runtime_seconds']:.6f}s"
        )


    # =================================================
    # ORIGIN SUMMARY
    # =================================================

    origin_runtime = (
        time.perf_counter()
        -
        origin_start
    )


    origin_df = pd.DataFrame(
        origin_rows
    )


    print()

    print(
        f"{origin} completed"
    )

    print(
        "  Mean simple paths:",
        f"{origin_df['simple_path_count'].mean():.3f}"
    )

    print(
        "  Max simple paths:",
        int(
            origin_df[
                "simple_path_count"
            ].max()
        )
    )

    print(
        "  Mean partial states:",
        f"{origin_df['explored_partial_paths'].mean():.3f}"
    )

    print(
        "  Max partial states:",
        int(
            origin_df[
                "explored_partial_paths"
            ].max()
        )
    )

    print(
        "  Origin runtime:",
        f"{origin_runtime:.3f}s"
    )


    # =================================================
    # CHECKPOINT AFTER EVERY ORIGIN
    # =================================================

    checkpoint_df = (
        pd.DataFrame(rows)
    )


    checkpoint_df.to_csv(
        CHECKPOINT_FILE,
        index=False,
        encoding="utf-8-sig"
    )


# =========================================================
# TOTAL RUNTIME
# =========================================================

total_runtime = (
    time.perf_counter()
    -
    global_start
)


# =========================================================
# RAW RESULTS
# =========================================================

dfs_df = pd.DataFrame(
    rows
)


dfs_df = (
    dfs_df
    .sort_values(
        [
            "origin",
            "destination"
        ]
    )
    .reset_index(
        drop=True
    )
)


dfs_df.to_csv(
    RAW_FILE,
    index=False,
    encoding="utf-8-sig"
)


# =========================================================
# DESCRIPTIVE STATISTICS
# =========================================================

stats_columns = [

    "simple_path_count",

    "explored_partial_paths",

    "max_depth",

    "dfs_runtime_seconds"
]


summary_df = (
    dfs_df[
        stats_columns
    ]
    .describe()
    .T
)


summary_df.to_csv(
    SUMMARY_FILE,
    encoding="utf-8-sig"
)


# =========================================================
# TOP SIMPLE PATH ODs
# =========================================================

top_simple_df = (

    dfs_df

    .sort_values(
        "simple_path_count",
        ascending=False
    )

    .head(50)

)


top_simple_df.to_csv(
    TOP_SIMPLE_FILE,
    index=False,
    encoding="utf-8-sig"
)


# =========================================================
# TOP DFS SEARCH-WORKLOAD ODs
# =========================================================

top_partial_df = (

    dfs_df

    .sort_values(
        "explored_partial_paths",
        ascending=False
    )

    .head(50)

)


top_partial_df.to_csv(
    TOP_PARTIAL_FILE,
    index=False,
    encoding="utf-8-sig"
)


# =========================================================
# MERGE WITH EXPERIMENT 5 MOSP RESULTS
# =========================================================

if EXP5_OD_FILE.exists():

    exp5_df = pd.read_csv(
        EXP5_OD_FILE,
        encoding="utf-8-sig"
    )


    merged_df = dfs_df.merge(
        exp5_df,
        on=[
            "origin",
            "destination"
        ],
        how="left"
    )


    # -------------------------------------------------
    # Number of simple paths per Pareto route
    # -------------------------------------------------

    merged_df[
        "simple_paths_per_pareto_route"
    ] = (

        merged_df[
            "simple_path_count"
        ]

        /

        merged_df[
            "pareto_route_count"
        ]

    )


    # -------------------------------------------------
    # Pareto efficiency ratio:
    #
    # What percentage of exhaustive simple paths
    # survive as Pareto-efficient routes?
    # -------------------------------------------------

    merged_df[
        "pareto_survival_percentage"
    ] = (

        merged_df[
            "pareto_route_count"
        ]

        /

        merged_df[
            "simple_path_count"
        ]

        *

        100

    )


    merged_df.to_csv(
        MERGED_FILE,
        index=False,
        encoding="utf-8-sig"
    )


else:

    merged_df = None

    print()
    print(
        "WARNING:"
        " Experiment 5 all_od_summary.csv "
        "was not found."
    )


# =========================================================
# FINAL SUMMARY
# =========================================================

print()
print("=" * 80)
print("ALL-OD DFS DESCRIPTIVE STATISTICS")
print("=" * 80)

print(
    summary_df.to_string()
)


# =========================================================
# SIMPLE PATH DISTRIBUTION
# =========================================================

print()
print("=" * 80)
print("SIMPLE PATH COUNT")
print("=" * 80)

print(
    "Mean:",
    f"{dfs_df['simple_path_count'].mean():.3f}"
)

print(
    "Median:",
    f"{dfs_df['simple_path_count'].median():.3f}"
)

print(
    "Minimum:",
    int(
        dfs_df[
            "simple_path_count"
        ].min()
    )
)

print(
    "Maximum:",
    int(
        dfs_df[
            "simple_path_count"
        ].max()
    )
)


# =========================================================
# DFS PARTIAL SEARCH STATES
# =========================================================

print()
print("=" * 80)
print("DFS PARTIAL SEARCH STATES")
print("=" * 80)

print(
    "Mean:",
    f"{dfs_df['explored_partial_paths'].mean():.3f}"
)

print(
    "Median:",
    f"{dfs_df['explored_partial_paths'].median():.3f}"
)

print(
    "Minimum:",
    int(
        dfs_df[
            "explored_partial_paths"
        ].min()
    )
)

print(
    "Maximum:",
    int(
        dfs_df[
            "explored_partial_paths"
        ].max()
    )
)


# =========================================================
# MAX SIMPLE PATH OD
# =========================================================

max_simple = (
    dfs_df[
        "simple_path_count"
    ]
    .max()
)


max_simple_rows = (
    dfs_df[
        dfs_df[
            "simple_path_count"
        ]
        ==
        max_simple
    ]
)


print()
print("=" * 80)
print("OD PAIRS WITH MAXIMUM SIMPLE PATH COUNT")
print("=" * 80)

print(

    max_simple_rows[
        [
            "origin",
            "destination",
            "simple_path_count",
            "explored_partial_paths",
            "max_depth",
            "dfs_runtime_seconds"
        ]
    ]

    .to_string(
        index=False
    )

)


# =========================================================
# MAX DFS WORKLOAD
# =========================================================

max_partial = (
    dfs_df[
        "explored_partial_paths"
    ]
    .max()
)


max_partial_rows = (
    dfs_df[
        dfs_df[
            "explored_partial_paths"
        ]
        ==
        max_partial
    ]
)


print()
print("=" * 80)
print("OD PAIRS WITH MAXIMUM DFS SEARCH WORKLOAD")
print("=" * 80)

print(

    max_partial_rows[
        [
            "origin",
            "destination",
            "simple_path_count",
            "explored_partial_paths",
            "max_depth",
            "dfs_runtime_seconds"
        ]
    ]

    .to_string(
        index=False
    )

)


# =========================================================
# DFS VS PARETO
# =========================================================

if merged_df is not None:

    print()
    print("=" * 80)
    print("DFS SIMPLE PATHS VS PARETO ROUTES")
    print("=" * 80)


    print(
        "Mean simple paths / Pareto route:",
        f"{merged_df['simple_paths_per_pareto_route'].mean():.3f}"
    )

    print(
        "Median simple paths / Pareto route:",
        f"{merged_df['simple_paths_per_pareto_route'].median():.3f}"
    )

    print(
        "Mean Pareto survival percentage:",
        f"{merged_df['pareto_survival_percentage'].mean():.4f}%"
    )

    print(
        "Median Pareto survival percentage:",
        f"{merged_df['pareto_survival_percentage'].median():.4f}%"
    )


    print()

    print(
        "Lowest Pareto survival OD pairs:"
    )


    lowest_survival = (

        merged_df

        .sort_values(
            "pareto_survival_percentage"
        )

        .head(20)

    )


    print(

        lowest_survival[
            [
                "origin",
                "destination",
                "simple_path_count",
                "pareto_route_count",
                "pareto_survival_percentage"
            ]
        ]

        .to_string(
            index=False
        )

    )


# =========================================================
# TOTAL RUNTIME
# =========================================================

print()
print("=" * 80)
print("TOTAL BENCHMARK RUNTIME")
print("=" * 80)

print(
    f"{total_runtime:.3f} seconds"
)

print(
    f"{total_runtime / 60:.3f} minutes"
)


# =========================================================
# OUTPUT FILES
# =========================================================

print()
print("=" * 80)
print("OUTPUT FILES")
print("=" * 80)

print(
    "Raw DFS results:",
    RAW_FILE
)

print(
    "Checkpoint:",
    CHECKPOINT_FILE
)

print(
    "Summary statistics:",
    SUMMARY_FILE
)

print(
    "Top simple paths:",
    TOP_SIMPLE_FILE
)

print(
    "Top partial states:",
    TOP_PARTIAL_FILE
)


if merged_df is not None:

    print(
        "DFS vs MOSP merged:",
        MERGED_FILE
    )


print()

print(
    "Experiment 6B completed successfully."
)