from pathlib import Path
import copy
import time

import pandas as pd

from src.mosp import mosp
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

DFS_DIR = (
    ROOT
    / "experiments"
    / "results"
    / "experiment_06b_all_od_dfs"
)

RESULT_DIR = (
    ROOT
    / "experiments"
    / "results"
    / "experiment_07_origin_level_dfs_vs_mosp"
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


DFS_FILE = (
    DFS_DIR
    / "all_od_dfs_raw.csv"
)


OUTPUT_FILE = (
    RESULT_DIR
    / "dfs_vs_mosp_origin_level.csv"
)

SUMMARY_FILE = (
    RESULT_DIR
    / "dfs_vs_mosp_origin_level_summary.csv"
)

TOP_REDUCTION_FILE = (
    RESULT_DIR
    / "top_search_reduction_origins.csv"
)

BOTTOM_REDUCTION_FILE = (
    RESULT_DIR
    / "bottom_search_reduction_origins.csv"
)


NUM_OBJECTIVES = 3


# =========================================================
# READ DFS RESULTS
# =========================================================

dfs_df = pd.read_csv(
    DFS_FILE,
    encoding="utf-8-sig"
)


# =========================================================
# BUILD BASE GRAPH
# =========================================================

base_graph, build_stats = (
    build_taipei_metro_graph(
        station_file=STATION_FILE,
        travel_time_file=TRAVEL_FILE,
        transfer_file=TRANSFER_FILE
    )
)


PHYSICAL_STATIONS = sorted(
    base_graph.states_by_name.keys()
)


print("=" * 80)
print("EXPERIMENT 7")
print("ORIGIN-LEVEL DFS VS MOSP BENCHMARK")
print("=" * 80)

print()
print("Physical stations:", len(PHYSICAL_STATIONS))
print("DFS OD observations:", len(dfs_df))


# =========================================================
# BUILD ALL-TARGET GRAPH
# =========================================================

def build_all_target_graph(
    base_graph
):

    graph = copy.deepcopy(
        base_graph
    )

    target_nodes = {}

    for station_name in sorted(
        graph.states_by_name.keys()
    ):

        target = (
            f"__TARGET__::{station_name}"
        )

        target_nodes[
            station_name
        ] = target


        graph.add_node(
            target,
            kind="virtual_target",
            station_name=station_name
        )


        for state in graph.states_by_name[
            station_name
        ]:

            graph.add_edge(
                state,
                target,
                (0, 0, 0),
                kind="egress"
            )


    return graph, target_nodes


# =========================================================
# ADD SOURCE
# =========================================================

def add_origin_source(
    graph,
    origin_name
):

    source = (
        f"__SOURCE__::{origin_name}"
    )

    graph.add_node(
        source,
        kind="virtual_source",
        station_name=origin_name
    )


    for state in graph.states_by_name[
        origin_name
    ]:

        graph.add_edge(
            source,
            state,
            (0, 0, 0),
            kind="access"
        )


    return source


# =========================================================
# PREPARE TARGET GRAPH
# =========================================================

all_target_graph, target_nodes = (
    build_all_target_graph(
        base_graph
    )
)


# =========================================================
# DFS ORIGIN-LEVEL AGGREGATION
# =========================================================

dfs_origin_df = (
    dfs_df
    .groupby(
        "origin"
    )
    .agg(

        dfs_destinations=(
            "destination",
            "count"
        ),

        dfs_total_simple_paths=(
            "simple_path_count",
            "sum"
        ),

        dfs_mean_simple_paths=(
            "simple_path_count",
            "mean"
        ),

        dfs_max_simple_paths=(
            "simple_path_count",
            "max"
        ),

        dfs_total_partial_states=(
            "explored_partial_paths",
            "sum"
        ),

        dfs_mean_partial_states=(
            "explored_partial_paths",
            "mean"
        ),

        dfs_max_partial_states=(
            "explored_partial_paths",
            "max"
        ),

        dfs_total_runtime_seconds=(
            "dfs_runtime_seconds",
            "sum"
        )

    )
    .reset_index()
)


# =========================================================
# RUN ONE MOSP PER ORIGIN
# =========================================================

mosp_rows = []


total_origins = len(
    PHYSICAL_STATIONS
)


for index, origin in enumerate(
    PHYSICAL_STATIONS,
    start=1
):

    print()
    print(
        f"[{index}/{total_origins}] "
        f"Running MOSP from {origin}"
    )


    graph = copy.deepcopy(
        all_target_graph
    )


    source = add_origin_source(
        graph,
        origin
    )


    start_time = (
        time.perf_counter()
    )


    labels, stats = mosp(
        graph=graph,
        source=source,
        num_objectives=NUM_OBJECTIVES,
        return_stats=True
    )


    runtime = (
        time.perf_counter()
        -
        start_time
    )


    # -----------------------------------------------------
    # Count final Pareto labels over all destinations
    # -----------------------------------------------------

    total_final_pareto_routes = 0

    multi_pareto_destinations = 0

    max_pareto_set_size = 0


    for destination in PHYSICAL_STATIONS:

        if destination == origin:
            continue


        target = target_nodes[
            destination
        ]


        pareto_size = len(
            labels[target]
        )


        total_final_pareto_routes += (
            pareto_size
        )


        if pareto_size > 1:
            multi_pareto_destinations += 1


        max_pareto_set_size = max(
            max_pareto_set_size,
            pareto_size
        )


    mosp_rows.append({

        "origin":
            origin,

        "mosp_generated_labels":
            stats[
                "generated_labels"
            ],

        "mosp_kept_labels":
            stats[
                "kept_labels"
            ],

        "mosp_pruned_labels":
            stats[
                "pruned_labels"
            ],

        "mosp_dominance_checks":
            stats[
                "dominance_checks"
            ],

        "mosp_max_labels_per_node":
            stats[
                "max_labels_per_node"
            ],

        "mosp_runtime_seconds":
            runtime,

        "mosp_total_final_pareto_routes":
            total_final_pareto_routes,

        "mosp_multi_pareto_destinations":
            multi_pareto_destinations,

        "mosp_max_pareto_set_size":
            max_pareto_set_size

    })


    print(
        "  generated labels:",
        stats[
            "generated_labels"
        ]
    )

    print(
        "  dominance checks:",
        stats[
            "dominance_checks"
        ]
    )

    print(
        "  runtime:",
        f"{runtime:.6f}s"
    )


# =========================================================
# MOSP DATAFRAME
# =========================================================

mosp_df = pd.DataFrame(
    mosp_rows
)


# =========================================================
# MERGE DFS + MOSP
# =========================================================

merged_df = dfs_origin_df.merge(
    mosp_df,
    on="origin",
    how="inner"
)


# =========================================================
# SEARCH-SPACE REDUCTION
# =========================================================

merged_df[
    "search_space_ratio_dfs_to_mosp"
] = (

    merged_df[
        "dfs_total_partial_states"
    ]

    /

    merged_df[
        "mosp_generated_labels"
    ]

)


merged_df[
    "mosp_search_percentage_of_dfs"
] = (

    merged_df[
        "mosp_generated_labels"
    ]

    /

    merged_df[
        "dfs_total_partial_states"
    ]

    *

    100

)


merged_df[
    "search_space_reduction_percentage"
] = (

    1

    -

    (
        merged_df[
            "mosp_generated_labels"
        ]

        /

        merged_df[
            "dfs_total_partial_states"
        ]
    )

) * 100


# =========================================================
# RUNTIME COMPARISON
# =========================================================

merged_df[
    "runtime_ratio_dfs_to_mosp"
] = (

    merged_df[
        "dfs_total_runtime_seconds"
    ]

    /

    merged_df[
        "mosp_runtime_seconds"
    ]

)


# =========================================================
# SIMPLE PATHS VS FINAL PARETO
# =========================================================

merged_df[
    "simple_paths_per_final_pareto_route"
] = (

    merged_df[
        "dfs_total_simple_paths"
    ]

    /

    merged_df[
        "mosp_total_final_pareto_routes"
    ]

)


merged_df[
    "pareto_survival_percentage_origin_level"
] = (

    merged_df[
        "mosp_total_final_pareto_routes"
    ]

    /

    merged_df[
        "dfs_total_simple_paths"
    ]

    *

    100

)


# =========================================================
# SORT
# =========================================================

merged_df = (
    merged_df
    .sort_values(
        "origin"
    )
    .reset_index(
        drop=True
    )
)


# =========================================================
# SAVE MAIN RESULT
# =========================================================

merged_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# =========================================================
# SUMMARY STATISTICS
# =========================================================

summary_columns = [

    "dfs_total_simple_paths",

    "dfs_total_partial_states",

    "dfs_total_runtime_seconds",

    "mosp_generated_labels",

    "mosp_dominance_checks",

    "mosp_runtime_seconds",

    "search_space_ratio_dfs_to_mosp",

    "mosp_search_percentage_of_dfs",

    "search_space_reduction_percentage",

    "runtime_ratio_dfs_to_mosp",

    "simple_paths_per_final_pareto_route",

    "pareto_survival_percentage_origin_level"

]


summary_df = (
    merged_df[
        summary_columns
    ]
    .describe()
    .T
)


summary_df.to_csv(
    SUMMARY_FILE,
    encoding="utf-8-sig"
)


# =========================================================
# TOP / BOTTOM REDUCTION ORIGINS
# =========================================================

top_reduction_df = (

    merged_df

    .sort_values(
        "search_space_ratio_dfs_to_mosp",
        ascending=False
    )

    .head(20)

)


bottom_reduction_df = (

    merged_df

    .sort_values(
        "search_space_ratio_dfs_to_mosp",
        ascending=True
    )

    .head(20)

)


top_reduction_df.to_csv(
    TOP_REDUCTION_FILE,
    index=False,
    encoding="utf-8-sig"
)

bottom_reduction_df.to_csv(
    BOTTOM_REDUCTION_FILE,
    index=False,
    encoding="utf-8-sig"
)


# =========================================================
# FINAL OUTPUT
# =========================================================

print()
print("=" * 80)
print("ORIGIN-LEVEL SUMMARY STATISTICS")
print("=" * 80)

print(
    summary_df.to_string()
)


print()
print("=" * 80)
print("KEY SEARCH-SPACE RESULTS")
print("=" * 80)

print(
    "Mean DFS/MOSP search-space ratio:",
    f"{merged_df['search_space_ratio_dfs_to_mosp'].mean():.3f}x"
)

print(
    "Median DFS/MOSP search-space ratio:",
    f"{merged_df['search_space_ratio_dfs_to_mosp'].median():.3f}x"
)

print(
    "Minimum DFS/MOSP search-space ratio:",
    f"{merged_df['search_space_ratio_dfs_to_mosp'].min():.3f}x"
)

print(
    "Maximum DFS/MOSP search-space ratio:",
    f"{merged_df['search_space_ratio_dfs_to_mosp'].max():.3f}x"
)


print()

print(
    "Mean MOSP search space as % of DFS:",
    f"{merged_df['mosp_search_percentage_of_dfs'].mean():.4f}%"
)

print(
    "Median MOSP search space as % of DFS:",
    f"{merged_df['mosp_search_percentage_of_dfs'].median():.4f}%"
)


print()
print("=" * 80)
print("RUNTIME RESULTS")
print("=" * 80)

print(
    "Mean DFS/MOSP runtime ratio:",
    f"{merged_df['runtime_ratio_dfs_to_mosp'].mean():.3f}x"
)

print(
    "Median DFS/MOSP runtime ratio:",
    f"{merged_df['runtime_ratio_dfs_to_mosp'].median():.3f}x"
)

print(
    "Minimum DFS/MOSP runtime ratio:",
    f"{merged_df['runtime_ratio_dfs_to_mosp'].min():.3f}x"
)

print(
    "Maximum DFS/MOSP runtime ratio:",
    f"{merged_df['runtime_ratio_dfs_to_mosp'].max():.3f}x"
)


# =========================================================
# BEST ORIGINS
# =========================================================

print()
print("=" * 80)
print("TOP 15 SEARCH-SPACE REDUCTION ORIGINS")
print("=" * 80)

print(

    top_reduction_df[
        [
            "origin",
            "dfs_total_partial_states",
            "mosp_generated_labels",
            "search_space_ratio_dfs_to_mosp",
            "search_space_reduction_percentage",
            "runtime_ratio_dfs_to_mosp"
        ]
    ]

    .head(15)

    .to_string(
        index=False
    )

)


# =========================================================
# LOWEST REDUCTION ORIGINS
# =========================================================

print()
print("=" * 80)
print("LOWEST 15 SEARCH-SPACE REDUCTION ORIGINS")
print("=" * 80)

print(

    bottom_reduction_df[
        [
            "origin",
            "dfs_total_partial_states",
            "mosp_generated_labels",
            "search_space_ratio_dfs_to_mosp",
            "search_space_reduction_percentage",
            "runtime_ratio_dfs_to_mosp"
        ]
    ]

    .head(15)

    .to_string(
        index=False
    )

)


# =========================================================
# GLOBAL TOTALS
# =========================================================

total_dfs_partial = (
    merged_df[
        "dfs_total_partial_states"
    ].sum()
)

total_mosp_generated = (
    merged_df[
        "mosp_generated_labels"
    ].sum()
)

total_dfs_runtime = (
    merged_df[
        "dfs_total_runtime_seconds"
    ].sum()
)

total_mosp_runtime = (
    merged_df[
        "mosp_runtime_seconds"
    ].sum()
)


global_search_ratio = (
    total_dfs_partial
    /
    total_mosp_generated
)

global_runtime_ratio = (
    total_dfs_runtime
    /
    total_mosp_runtime
)


print()
print("=" * 80)
print("GLOBAL NETWORK COMPARISON")
print("=" * 80)

print(
    "Total DFS partial states:",
    int(total_dfs_partial)
)

print(
    "Total MOSP generated labels:",
    int(total_mosp_generated)
)

print(
    "Global DFS/MOSP search-space ratio:",
    f"{global_search_ratio:.3f}x"
)

print(
    "MOSP search space as % of DFS:",
    f"{100 / global_search_ratio:.4f}%"
)


print()

print(
    "Total DFS runtime:",
    f"{total_dfs_runtime:.6f}s"
)

print(
    "Total MOSP runtime:",
    f"{total_mosp_runtime:.6f}s"
)

print(
    "Global DFS/MOSP runtime ratio:",
    f"{global_runtime_ratio:.3f}x"
)


# =========================================================
# OUTPUT FILES
# =========================================================

print()
print("=" * 80)
print("OUTPUT FILES")
print("=" * 80)

print(
    "Origin-level comparison:",
    OUTPUT_FILE
)

print(
    "Summary:",
    SUMMARY_FILE
)

print(
    "Top reduction origins:",
    TOP_REDUCTION_FILE
)

print(
    "Bottom reduction origins:",
    BOTTOM_REDUCTION_FILE
)

print()
print(
    "Experiment 7 completed successfully."
)