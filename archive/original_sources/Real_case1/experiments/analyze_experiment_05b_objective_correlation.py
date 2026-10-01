from pathlib import Path

import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
import matplotlib.pyplot as plt


# =========================================================
# PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

RESULT_DIR = (
    ROOT
    / "experiments"
    / "results"
    / "experiment_05_all_od"
)

ROUTE_FILE = (
    RESULT_DIR
    / "all_od_pareto_routes.csv"
)


# =========================================================
# READ DATA
# =========================================================

df = pd.read_csv(
    ROUTE_FILE,
    encoding="utf-8-sig"
)


OBJECTIVES = [
    "travel_time_minutes",
    "transfers",
    "walking_minutes"
]


print("=" * 80)
print("EXPERIMENT 5B")
print("REAL OBJECTIVE DEPENDENCE ANALYSIS")
print("=" * 80)

print()

print("Total Pareto route observations:", len(df))
print("Unique origins:", df["origin"].nunique())
print("Unique destinations:", df["destination"].nunique())
print(
    "Unique OD pairs:",
    df[["origin", "destination"]]
    .drop_duplicates()
    .shape[0]
)


# =========================================================
# DESCRIPTIVE STATISTICS
# =========================================================

descriptive_df = (
    df[OBJECTIVES]
    .describe()
    .T
)

DESCRIPTIVE_FILE = (
    RESULT_DIR
    / "objective_descriptive_statistics.csv"
)

descriptive_df.to_csv(
    DESCRIPTIVE_FILE,
    encoding="utf-8-sig"
)


print()
print("=" * 80)
print("OBJECTIVE DESCRIPTIVE STATISTICS")
print("=" * 80)

print(descriptive_df)


# =========================================================
# PEARSON CORRELATION
# =========================================================

pearson_matrix = (
    df[OBJECTIVES]
    .corr(method="pearson")
)

PEARSON_FILE = (
    RESULT_DIR
    / "objective_pearson_correlation.csv"
)

pearson_matrix.to_csv(
    PEARSON_FILE,
    encoding="utf-8-sig"
)


print()
print("=" * 80)
print("PEARSON CORRELATION MATRIX")
print("=" * 80)

print(pearson_matrix.round(4))


# =========================================================
# SPEARMAN CORRELATION
# =========================================================

spearman_matrix = (
    df[OBJECTIVES]
    .corr(method="spearman")
)

SPEARMAN_FILE = (
    RESULT_DIR
    / "objective_spearman_correlation.csv"
)

spearman_matrix.to_csv(
    SPEARMAN_FILE,
    encoding="utf-8-sig"
)


print()
print("=" * 80)
print("SPEARMAN CORRELATION MATRIX")
print("=" * 80)

print(spearman_matrix.round(4))


# =========================================================
# PAIRWISE TEST TABLE
# =========================================================

pairs = [
    (
        "travel_time_minutes",
        "transfers",
        "Time vs Transfers"
    ),
    (
        "travel_time_minutes",
        "walking_minutes",
        "Time vs Walking"
    ),
    (
        "transfers",
        "walking_minutes",
        "Transfers vs Walking"
    ),
]


pair_rows = []


for x, y, name in pairs:

    pearson_r, pearson_p = pearsonr(
        df[x],
        df[y]
    )

    spearman_rho, spearman_p = spearmanr(
        df[x],
        df[y]
    )

    pair_rows.append({
        "comparison":
            name,

        "pearson_r":
            pearson_r,

        "pearson_p":
            pearson_p,

        "spearman_rho":
            spearman_rho,

        "spearman_p":
            spearman_p
    })


pair_df = pd.DataFrame(
    pair_rows
)


PAIR_FILE = (
    RESULT_DIR
    / "objective_pairwise_correlations.csv"
)


pair_df.to_csv(
    PAIR_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("=" * 80)
print("PAIRWISE OBJECTIVE CORRELATIONS")
print("=" * 80)

print(
    pair_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.6f}"
    )
)


# =========================================================
# MULTI-PARETO ROUTES ONLY
#
# This is important because these are precisely the
# observations where trade-offs remain in the choice set.
# =========================================================

od_counts = (
    df
    .groupby(
        ["origin", "destination"]
    )
    .size()
    .reset_index(
        name="pareto_route_count"
    )
)


multi_keys = (
    od_counts[
        od_counts[
            "pareto_route_count"
        ] > 1
    ][
        ["origin", "destination"]
    ]
)


multi_df = df.merge(
    multi_keys,
    on=[
        "origin",
        "destination"
    ],
    how="inner"
)


print()
print("=" * 80)
print("MULTI-PARETO ROUTES ONLY")
print("=" * 80)

print(
    "Route observations:",
    len(multi_df)
)

print(
    "Multi-Pareto OD pairs:",
    multi_keys.shape[0]
)


multi_pearson = (
    multi_df[OBJECTIVES]
    .corr(method="pearson")
)

multi_spearman = (
    multi_df[OBJECTIVES]
    .corr(method="spearman")
)


MULTI_PEARSON_FILE = (
    RESULT_DIR
    / "multi_pareto_objective_pearson.csv"
)

MULTI_SPEARMAN_FILE = (
    RESULT_DIR
    / "multi_pareto_objective_spearman.csv"
)


multi_pearson.to_csv(
    MULTI_PEARSON_FILE,
    encoding="utf-8-sig"
)

multi_spearman.to_csv(
    MULTI_SPEARMAN_FILE,
    encoding="utf-8-sig"
)


print()
print("Pearson:")

print(
    multi_pearson.round(4)
)

print()
print("Spearman:")

print(
    multi_spearman.round(4)
)


# =========================================================
# WITHIN-OD DIFFERENCES
#
# Global correlation can be affected by trip length.
# Therefore we also examine trade-offs WITHIN each
# multi-Pareto OD.
# =========================================================

difference_rows = []


for (
    origin,
    destination
), group in multi_df.groupby(
    ["origin", "destination"]
):

    if len(group) < 2:
        continue

    fastest = group.loc[
        group[
            "travel_time_minutes"
        ].idxmin()
    ]

    for idx, route in group.iterrows():

        if idx == fastest.name:
            continue

        difference_rows.append({

            "origin":
                origin,

            "destination":
                destination,

            "delta_time_minutes":
                (
                    route[
                        "travel_time_minutes"
                    ]
                    -
                    fastest[
                        "travel_time_minutes"
                    ]
                ),

            "delta_transfers":
                (
                    route[
                        "transfers"
                    ]
                    -
                    fastest[
                        "transfers"
                    ]
                ),

            "delta_walking_minutes":
                (
                    route[
                        "walking_minutes"
                    ]
                    -
                    fastest[
                        "walking_minutes"
                    ]
                )
        })


difference_df = pd.DataFrame(
    difference_rows
)


DIFFERENCE_FILE = (
    RESULT_DIR
    / "within_od_tradeoff_differences.csv"
)


difference_df.to_csv(
    DIFFERENCE_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("=" * 80)
print("WITHIN-OD TRADE-OFF DIFFERENCES")
print("=" * 80)

print(
    difference_df[
        [
            "delta_time_minutes",
            "delta_transfers",
            "delta_walking_minutes"
        ]
    ]
    .describe()
    .round(4)
)


# =========================================================
# TRADE-OFF DIRECTION
# =========================================================

def classify_tradeoff(row):

    dt = row[
        "delta_time_minutes"
    ]

    dtr = row[
        "delta_transfers"
    ]

    dw = row[
        "delta_walking_minutes"
    ]

    # Relative to fastest route:
    # dt should normally be >= 0.

    if (
        dtr == 0
        and dw < 0
    ):
        return "slower_but_less_walking"

    if (
        dtr < 0
        and dw == 0
    ):
        return "slower_but_fewer_transfers"

    if (
        dtr < 0
        and dw < 0
    ):
        return (
            "slower_but_fewer_transfers_and_less_walking"
        )

    if (
        dtr > 0
        and dw < 0
    ):
        return (
            "slower_more_transfers_but_less_walking"
        )

    return "other"


difference_df[
    "tradeoff_direction"
] = (
    difference_df.apply(
        classify_tradeoff,
        axis=1
    )
)


tradeoff_direction_df = (
    difference_df[
        "tradeoff_direction"
    ]
    .value_counts()
    .reset_index()
)


tradeoff_direction_df.columns = [
    "tradeoff_direction",
    "count"
]


tradeoff_direction_df[
    "percentage"
] = (
    tradeoff_direction_df[
        "count"
    ]
    /
    len(tradeoff_direction_df
        .index.repeat(
            tradeoff_direction_df["count"]
        ))
    *
    100
)


TRADEOFF_DIRECTION_FILE = (
    RESULT_DIR
    / "within_od_tradeoff_direction_summary.csv"
)


tradeoff_direction_df.to_csv(
    TRADEOFF_DIRECTION_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("=" * 80)
print("WITHIN-OD TRADE-OFF DIRECTIONS")
print("=" * 80)

print(
    tradeoff_direction_df.to_string(
        index=False
    )
)


# =========================================================
# FIGURE 1
# TIME vs TRANSFERS
# =========================================================

plt.figure(
    figsize=(7, 5)
)

plt.scatter(
    df["travel_time_minutes"],
    df["transfers"],
    alpha=0.25
)

plt.xlabel(
    "Travel Time (min)"
)

plt.ylabel(
    "Number of Transfers"
)

plt.title(
    "Taipei Metro Pareto Routes: "
    "Travel Time vs Transfers"
)

plt.tight_layout()

FIG1 = (
    RESULT_DIR
    / "fig_05b_01_time_vs_transfers.png"
)

plt.savefig(
    FIG1,
    dpi=300
)

plt.close()


# =========================================================
# FIGURE 2
# TIME vs WALKING
# =========================================================

plt.figure(
    figsize=(7, 5)
)

plt.scatter(
    df["travel_time_minutes"],
    df["walking_minutes"],
    alpha=0.25
)

plt.xlabel(
    "Travel Time (min)"
)

plt.ylabel(
    "Transfer Walking Time (min)"
)

plt.title(
    "Taipei Metro Pareto Routes: "
    "Travel Time vs Walking"
)

plt.tight_layout()

FIG2 = (
    RESULT_DIR
    / "fig_05b_02_time_vs_walking.png"
)

plt.savefig(
    FIG2,
    dpi=300
)

plt.close()


# =========================================================
# FIGURE 3
# TRANSFERS vs WALKING
# =========================================================

plt.figure(
    figsize=(7, 5)
)

plt.scatter(
    df["transfers"],
    df["walking_minutes"],
    alpha=0.25
)

plt.xlabel(
    "Number of Transfers"
)

plt.ylabel(
    "Transfer Walking Time (min)"
)

plt.title(
    "Taipei Metro Pareto Routes: "
    "Transfers vs Walking"
)

plt.tight_layout()

FIG3 = (
    RESULT_DIR
    / "fig_05b_03_transfers_vs_walking.png"
)

plt.savefig(
    FIG3,
    dpi=300
)

plt.close()


# =========================================================
# FINAL SUMMARY
# =========================================================

print()
print("=" * 80)
print("OUTPUT FILES")
print("=" * 80)

print(DESCRIPTIVE_FILE)
print(PEARSON_FILE)
print(SPEARMAN_FILE)
print(PAIR_FILE)
print(MULTI_PEARSON_FILE)
print(MULTI_SPEARMAN_FILE)
print(DIFFERENCE_FILE)
print(TRADEOFF_DIRECTION_FILE)
print(FIG1)
print(FIG2)
print(FIG3)

print()

print(
    "Experiment 5B completed successfully."
)