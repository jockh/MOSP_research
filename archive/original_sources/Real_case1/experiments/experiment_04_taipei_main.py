from pathlib import Path

import pandas as pd

from src.mosp import (
    mosp,
    reconstruct_path
)

from src.taipei_metro import (
    build_taipei_metro_graph,
    make_od_graph,
    format_path
)


# =========================================================
# Paths
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = (
    ROOT
    / "data"
    / "taipei_metro"
)

RESULT_DIR = (
    ROOT
    / "experiments"
    / "results"
    / "experiment_04_taipei_main"
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


# =========================================================
# Case-study settings
# =========================================================

ORIGIN = "台北車站"

DESTINATIONS = [
    "南京復興站",
    "松江南京站",
    "行天宮站",
    "松山站",
    "大安站",
    "忠孝復興站",
    "南港展覽館站",
    "動物園站",
    "淡水站",
    "新店站",
]


# =========================================================
# Build network
# =========================================================

base_graph, build_stats = (
    build_taipei_metro_graph(
        station_file=STATION_FILE,
        travel_time_file=TRAVEL_FILE,
        transfer_file=TRANSFER_FILE
    )
)


print("=" * 70)
print("TAIPEI METRO GRAPH")
print("=" * 70)

for key, value in build_stats.items():

    if key != "skipped_pairs":
        print(f"{key}: {value}")


print()
print("Skipped travel pairs:")

for pair in build_stats["skipped_pairs"]:
    print(" ", pair)


# =========================================================
# Output containers
# =========================================================

summary_rows = []
route_rows = []


# =========================================================
# Run all ODs
# =========================================================

for destination in DESTINATIONS:

    print()
    print("=" * 70)
    print(f"{ORIGIN} -> {destination}")
    print("=" * 70)

    graph, source, target = make_od_graph(
        base_graph,
        ORIGIN,
        destination
    )

    labels, stats = mosp(
        graph=graph,
        source=source,
        num_objectives=3,
        return_stats=True
    )

    target_labels = sorted(
        labels[target],
        key=lambda label: label.costs
    )

    print(
        f"Pareto labels: {len(target_labels)}"
    )

    print()

    # -----------------------------------------
    # Route-level output
    # -----------------------------------------

    min_time = None
    min_walking = None
    min_transfers = None

    for route_id, label in enumerate(
        target_labels,
        start=1
    ):

        path = reconstruct_path(
            label
        )

        readable_path = format_path(
            graph,
            path
        )

        time_seconds = label.costs[0]
        transfers = label.costs[1]
        walking_seconds = label.costs[2]

        if min_time is None:
            min_time = time_seconds
            min_transfers = transfers
            min_walking = walking_seconds

        else:
            min_time = min(
                min_time,
                time_seconds
            )

            min_transfers = min(
                min_transfers,
                transfers
            )

            min_walking = min(
                min_walking,
                walking_seconds
            )

        print(
            f"Route {route_id}: "
            f"{time_seconds / 60:.2f} min | "
            f"{transfers} transfers | "
            f"{walking_seconds / 60:.2f} min walking"
        )

        print(
            f"  {readable_path}"
        )

        route_rows.append({

            "origin":
                ORIGIN,

            "destination":
                destination,

            "route_id":
                route_id,

            "travel_time_seconds":
                time_seconds,

            "travel_time_minutes":
                time_seconds / 60,

            "transfers":
                transfers,

            "walking_seconds":
                walking_seconds,

            "walking_minutes":
                walking_seconds / 60,

            "path":
                readable_path
        })

    # -----------------------------------------
    # OD summary
    # -----------------------------------------

    summary_rows.append({

        "origin":
            ORIGIN,

        "destination":
            destination,

        "pareto_route_count":
            len(target_labels),

        "minimum_travel_time_minutes":
            (
                min_time / 60
                if min_time is not None
                else None
            ),

        "minimum_transfers":
            min_transfers,

        "minimum_walking_minutes":
            (
                min_walking / 60
                if min_walking is not None
                else None
            ),

        # IMPORTANT:
        # These are source-to-all-node statistics,
        # not destination-specific workload.
        "generated_labels":
            stats["generated_labels"],

        "kept_labels":
            stats["kept_labels"],

        "pruned_labels":
            stats["pruned_labels"],

        "dominance_checks":
            stats["dominance_checks"],

        "max_labels_per_node":
            stats["max_labels_per_node"]
    })


# =========================================================
# Create dataframes
# =========================================================

summary_df = pd.DataFrame(
    summary_rows
)

routes_df = pd.DataFrame(
    route_rows
)


# =========================================================
# Sort for readability
# =========================================================

summary_df = summary_df.sort_values(
    [
        "pareto_route_count",
        "destination"
    ],
    ascending=[
        False,
        True
    ]
).reset_index(
    drop=True
)


routes_df = routes_df.sort_values(
    [
        "destination",
        "travel_time_seconds",
        "transfers",
        "walking_seconds"
    ]
).reset_index(
    drop=True
)


# =========================================================
# Save
# =========================================================

summary_file = (
    RESULT_DIR
    / "taipei_main_multi_od_summary.csv"
)

routes_file = (
    RESULT_DIR
    / "taipei_main_multi_od_pareto_routes.csv"
)


summary_df.to_csv(
    summary_file,
    index=False,
    encoding="utf-8-sig"
)

routes_df.to_csv(
    routes_file,
    index=False,
    encoding="utf-8-sig"
)


# =========================================================
# Print summary
# =========================================================

print()
print("=" * 70)
print("MULTI-OD SUMMARY")
print("=" * 70)

print(
    summary_df[
        [
            "destination",
            "pareto_route_count",
            "minimum_travel_time_minutes",
            "minimum_transfers",
            "minimum_walking_minutes"
        ]
    ].to_string(
        index=False
    )
)

print()
print(f"Saved summary: {summary_file}")
print(f"Saved routes:  {routes_file}")