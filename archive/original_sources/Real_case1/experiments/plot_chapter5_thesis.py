from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# PROJECT ROOT
# =========================================================
#
# This script automatically searches upward for:
#
# experiments/
# └─ results/
#    └─ experiment_05_all_od/
#
# Therefore it can work whether your project folder is:
#
#   Mosp_vr1.1
#
# or:
#
#   Real_case1
#
# as long as this script is placed somewhere inside
# the same project.
# =========================================================

SCRIPT_DIR = Path(__file__).resolve().parent

ROOT = None

for candidate in [
    SCRIPT_DIR,
    *SCRIPT_DIR.parents
]:

    expected_result_dir = (
        candidate
        / "experiments"
        / "results"
        / "experiment_05_all_od"
    )

    if expected_result_dir.exists():

        ROOT = candidate
        break


if ROOT is None:

    raise FileNotFoundError(
        "\n找不到專案根目錄。\n"
        "程式需要找到：\n"
        "experiments/results/experiment_05_all_od/\n"
    )


# =========================================================
# PATHS
# =========================================================

RESULT_DIR = (
    ROOT
    / "experiments"
    / "results"
    / "experiment_05_all_od"
)


FIGURE_DIR = (
    RESULT_DIR
    / "chapter5_figures_thesis"
)


FIGURE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# INPUT FILES
# =========================================================

OD_FILE = (
    RESULT_DIR
    / "all_od_summary.csv"
)


ORIGIN_SUMMARY_FILE = (
    RESULT_DIR
    / "origin_summary.csv"
)


# =========================================================
# CHECK FILES
# =========================================================

for file in [
    OD_FILE,
    ORIGIN_SUMMARY_FILE,
]:

    if not file.exists():

        raise FileNotFoundError(
            f"\n找不到檔案：\n{file}\n"
        )


# =========================================================
# READ DATA
# =========================================================

od_df = pd.read_csv(
    OD_FILE,
    encoding="utf-8-sig"
)


origin_df = pd.read_csv(
    ORIGIN_SUMMARY_FILE,
    encoding="utf-8-sig"
)


# =========================================================
# BASIC VALIDATION
# =========================================================

required_od_columns = {
    "origin",
    "destination",
    "pareto_route_count",
    "pareto_time_range_minutes",
    "pareto_transfer_range",
    "pareto_walking_range_minutes",
}


required_origin_columns = {
    "origin",
    "multi_pareto_percentage",
    "mean_pareto_size",
    "max_pareto_size",
}


missing_od_columns = (
    required_od_columns
    - set(od_df.columns)
)


missing_origin_columns = (
    required_origin_columns
    - set(origin_df.columns)
)


if missing_od_columns:

    raise ValueError(
        "all_od_summary.csv 缺少欄位："
        + ", ".join(
            sorted(
                missing_od_columns
            )
        )
    )


if missing_origin_columns:

    raise ValueError(
        "origin_summary.csv 缺少欄位："
        + ", ".join(
            sorted(
                missing_origin_columns
            )
        )
    )


# =========================================================
# INPUT SUMMARY
# =========================================================

print("=" * 90)
print("CHAPTER 5 THESIS FIGURE GENERATION")
print("=" * 90)

print(
    f"Project root : {ROOT}"
)

print(
    f"OD rows      : {len(od_df)}"
)

print(
    f"Station rows : {len(origin_df)}"
)

print(
    f"Output folder:\n{FIGURE_DIR}"
)


# =========================================================
# FONT / GLOBAL STYLE
# =========================================================
#
# Microsoft JhengHei:
# Traditional Chinese font commonly available on Windows.
#
# Figures are intentionally kept simple and monochrome-ish
# because the thesis caption will provide the figure title.
# =========================================================

plt.rcParams[
    "font.family"
] = "Microsoft JhengHei"


plt.rcParams[
    "axes.unicode_minus"
] = False


plt.rcParams[
    "font.size"
] = 10


plt.rcParams[
    "axes.labelsize"
] = 11


plt.rcParams[
    "xtick.labelsize"
] = 10


plt.rcParams[
    "ytick.labelsize"
] = 10


# =========================================================
# COMMON FIGURE STYLE
# =========================================================

def apply_thesis_style(
    ax,
    grid_axis="y"
):

    ax.spines[
        "top"
    ].set_visible(False)

    ax.spines[
        "right"
    ].set_visible(False)

    ax.tick_params(
        axis="both",
        labelsize=10
    )

    if grid_axis is not None:

        ax.grid(
            axis=grid_axis,
            linestyle="--",
            linewidth=0.6,
            alpha=0.30
        )

        ax.set_axisbelow(True)


# =========================================================
# COMMON SAVE FUNCTION
# =========================================================

def save_figure(
    filename_without_extension
):

    png_path = (
        FIGURE_DIR
        / f"{filename_without_extension}.png"
    )

    pdf_path = (
        FIGURE_DIR
        / f"{filename_without_extension}.pdf"
    )

    plt.tight_layout()

    # High-resolution raster image
    plt.savefig(
        png_path,
        dpi=600,
        bbox_inches="tight"
    )

    # Vector version for thesis
    plt.savefig(
        pdf_path,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"Saved PNG: {png_path}"
    )

    print(
        f"Saved PDF: {pdf_path}"
    )


# =========================================================
# FIGURE 5-2
# PARETO SET SIZE DISTRIBUTION
# =========================================================
#
# Purpose:
# Show how frequently multiple Pareto routes occur
# across all ordered OD pairs.
# =========================================================

distribution = (
    od_df[
        "pareto_route_count"
    ]
    .value_counts()
    .sort_index()
)


percentage = (
    distribution
    / len(od_df)
    * 100
)


fig, ax = plt.subplots(
    figsize=(7.2, 4.8)
)


bars = ax.bar(
    distribution.index.astype(str),
    percentage.values,
    width=0.58
)


ax.set_xlabel(
    "Number of Pareto Routes"
)


ax.set_ylabel(
    "Percentage of OD Pairs (%)"
)


# Add percentage and sample count
for bar, pct, count in zip(
    bars,
    percentage.values,
    distribution.values
):

    ax.text(
        bar.get_x()
        + bar.get_width() / 2,

        bar.get_height()
        + 0.8,

        f"{pct:.2f}%\n(n={count})",

        ha="center",
        va="bottom",
        fontsize=9
    )


ax.set_ylim(
    0,
    max(
        percentage.values
    ) * 1.20
)


apply_thesis_style(
    ax,
    grid_axis="y"
)


save_figure(
    "figure_5_2_pareto_set_distribution"
)


# =========================================================
# FIGURE 5-3
# TOP STATIONS BY MULTI-PARETO RATE
# =========================================================
#
# Purpose:
# Examine whether Multi-Pareto OD pairs are spatially
# concentrated around particular origin stations.
# =========================================================

top_n = 15


top_origin = (
    origin_df
    .sort_values(
        "multi_pareto_percentage",
        ascending=False
    )
    .head(top_n)
    .copy()
)


# Reverse order:
# highest bar shown at the top.
top_origin = (
    top_origin
    .sort_values(
        "multi_pareto_percentage",
        ascending=True
    )
)


fig, ax = plt.subplots(
    figsize=(8.2, 6.5)
)


bars = ax.barh(
    top_origin[
        "origin"
    ],
    top_origin[
        "multi_pareto_percentage"
    ],
    height=0.65
)


ax.set_xlabel(
    "Multi-Pareto OD Percentage (%)"
)


ax.set_ylabel(
    "Origin Station"
)


for bar, value in zip(
    bars,
    top_origin[
        "multi_pareto_percentage"
    ]
):

    ax.text(
        value + 0.8,

        bar.get_y()
        + bar.get_height() / 2,

        f"{value:.1f}%",

        va="center",
        fontsize=9
    )


ax.set_xlim(
    0,
    min(
        100,
        top_origin[
            "multi_pareto_percentage"
        ].max() + 12
    )
)


apply_thesis_style(
    ax,
    grid_axis="x"
)


save_figure(
    "figure_5_3_station_multi_pareto_rate"
)


# =========================================================
# FIGURE 5-4
# MULTI-PARETO FREQUENCY VS PARETO-SET RICHNESS
# =========================================================
#
# Purpose:
#
# x:
#   Frequency of OD pairs with multiple Pareto routes.
#
# y:
#   Average number of Pareto routes.
#
# This distinguishes:
#
#   "how often alternatives occur"
#
# from
#
#   "how rich the alternatives are".
# =========================================================

fig, ax = plt.subplots(
    figsize=(7.2, 5.2)
)


ax.scatter(
    origin_df[
        "multi_pareto_percentage"
    ],

    origin_df[
        "mean_pareto_size"
    ],

    s=38,
    alpha=0.70
)


ax.set_xlabel(
    "Multi-Pareto OD Percentage (%)"
)


ax.set_ylabel(
    "Mean Pareto-Set Size"
)


# ---------------------------------------------------------
# Label only the most relevant stations
# ---------------------------------------------------------

label_stations = (
    origin_df
    .sort_values(
        [
            "multi_pareto_percentage",
            "mean_pareto_size"
        ],
        ascending=[
            False,
            False
        ]
    )
    .head(10)
)


for _, row in (
    label_stations.iterrows()
):

    ax.annotate(
        row[
            "origin"
        ],

        (
            row[
                "multi_pareto_percentage"
            ],

            row[
                "mean_pareto_size"
            ]
        ),

        xytext=(
            5,
            5
        ),

        textcoords="offset points",

        fontsize=8
    )


apply_thesis_style(
    ax,
    grid_axis="both"
)


save_figure(
    "figure_5_4_frequency_vs_richness"
)


# =========================================================
# MULTI-PARETO OD PAIRS ONLY
# =========================================================
#
# Pareto count = 1 has no internal trade-off range.
#
# Therefore Figures 5-5 and 5-6 use only:
#
#   pareto_route_count > 1
# =========================================================

multi_df = (
    od_df[
        od_df[
            "pareto_route_count"
        ] > 1
    ]
    .copy()
)


pareto_sizes = sorted(
    multi_df[
        "pareto_route_count"
    ]
    .dropna()
    .astype(int)
    .unique()
)


# =========================================================
# FIGURE 5-5
# PARETO COUNT VS TRAVEL-TIME RANGE
# =========================================================
#
# Purpose:
# Determine whether larger Pareto sets are associated
# with larger differences in travel time among alternatives.
# =========================================================

time_box_data = []

time_sample_sizes = []


for count in pareto_sizes:

    values = (
        multi_df[
            multi_df[
                "pareto_route_count"
            ] == count
        ][
            "pareto_time_range_minutes"
        ]
        .dropna()
        .values
    )

    time_box_data.append(
        values
    )

    time_sample_sizes.append(
        len(values)
    )


fig, ax = plt.subplots(
    figsize=(7.2, 5.0)
)


ax.boxplot(
    time_box_data,

    tick_labels=[
        str(x)
        for x in pareto_sizes
    ],

    widths=0.48,

    # Keep outliers:
    # they may represent meaningful real OD cases.
    showfliers=True,

    flierprops={
        "marker": "o",
        "markersize": 3.0,
        "alpha": 0.40
    },

    medianprops={
        "linewidth": 1.8
    },

    boxprops={
        "linewidth": 1.4
    },

    whiskerprops={
        "linewidth": 1.3
    },

    capprops={
        "linewidth": 1.3
    }
)


ax.set_xlabel(
    "Number of Pareto Routes"
)


ax.set_ylabel(
    "Range of Travel Time within Pareto Set (min)"
)


# ---------------------------------------------------------
# Sample sizes
# ---------------------------------------------------------

for i, n in enumerate(
    time_sample_sizes,
    start=1
):

    ax.text(
        i,
        -0.11,

        f"n = {n}",

        transform=ax.get_xaxis_transform(),

        ha="center",
        va="top",

        fontsize=9
    )


apply_thesis_style(
    ax,
    grid_axis="y"
)


save_figure(
    "figure_5_5_pareto_size_vs_time_range"
)


# =========================================================
# FIGURE 5-6
# PARETO COUNT VS WALKING RANGE
# =========================================================
#
# Purpose:
# Determine whether larger Pareto sets are associated
# with larger differences in transfer-walking burden.
#
# IMPORTANT:
#
# Pareto count = 5:
#
#   n = 36
#   28 observations = 6 min
#    6 observations = 8 min
#    2 observations = 9 min
#
# Since Q1 = Q2 = Q3 = 6,
# the standard box can collapse into a horizontal line.
#
# Therefore actual observations for count = 5 are
# additionally plotted with small horizontal jitter.
# =========================================================

walking_box_data = []

walking_sample_sizes = []


for count in pareto_sizes:

    values = (
        multi_df[
            multi_df[
                "pareto_route_count"
            ] == count
        ][
            "pareto_walking_range_minutes"
        ]
        .dropna()
        .values
    )

    walking_box_data.append(
        values
    )

    walking_sample_sizes.append(
        len(values)
    )


fig, ax = plt.subplots(
    figsize=(7.2, 5.0)
)


ax.boxplot(
    walking_box_data,

    tick_labels=[
        str(x)
        for x in pareto_sizes
    ],

    widths=0.48,

    # Do not hide 8 / 9 min observations
    showfliers=True,

    flierprops={
        "marker": "o",
        "markersize": 3.5,
        "alpha": 0.45
    },

    medianprops={
        "linewidth": 1.8
    },

    boxprops={
        "linewidth": 1.4
    },

    whiskerprops={
        "linewidth": 1.3
    },

    capprops={
        "linewidth": 1.3
    }
)


# ---------------------------------------------------------
# Actual observations for Pareto count = 5
# ---------------------------------------------------------

if 5 in pareto_sizes:

    idx = (
        pareto_sizes.index(5)
    )

    values = (
        walking_box_data[
            idx
        ]
    )

    x_position = (
        idx + 1
    )


    # Deterministic jitter:
    # avoids random changes every time the figure is generated.
    jitter_pattern = np.array(
        [
            -0.10,
            -0.075,
            -0.05,
            -0.025,
             0.00,
             0.025,
             0.05,
             0.075,
             0.10,
        ]
    )


    jitter = np.resize(
        jitter_pattern,
        len(values)
    )


    x_values = (
        x_position
        + jitter
    )


    ax.scatter(
        x_values,
        values,

        s=15,
        alpha=0.45,

        zorder=3
    )


ax.set_xlabel(
    "Number of Pareto Routes"
)


ax.set_ylabel(
    "Range of Transfer-Walking Time within Pareto Set (min)"
)


# ---------------------------------------------------------
# Sample sizes
# ---------------------------------------------------------

for i, n in enumerate(
    walking_sample_sizes,
    start=1
):

    ax.text(
        i,
        -0.11,

        f"n = {n}",

        transform=ax.get_xaxis_transform(),

        ha="center",
        va="top",

        fontsize=9
    )


apply_thesis_style(
    ax,
    grid_axis="y"
)


save_figure(
    "figure_5_6_pareto_size_vs_walking_range"
)


# =========================================================
# TRADE-OFF SUMMARY TABLE
# =========================================================
#
# Used for writing Chapter 5 text and interpreting
# Figures 5-5 / 5-6.
# =========================================================

summary_rows = []


for count in pareto_sizes:

    subset = (
        multi_df[
            multi_df[
                "pareto_route_count"
            ] == count
        ]
    )


    summary_rows.append(
        {
            "pareto_route_count":
                count,

            "number_of_od_pairs":
                len(subset),

            # ---------------------------------------------
            # Travel-time range
            # ---------------------------------------------

            "mean_time_range_minutes":
                subset[
                    "pareto_time_range_minutes"
                ].mean(),

            "median_time_range_minutes":
                subset[
                    "pareto_time_range_minutes"
                ].median(),

            "std_time_range_minutes":
                subset[
                    "pareto_time_range_minutes"
                ].std(),

            # ---------------------------------------------
            # Walking range
            # ---------------------------------------------

            "mean_walking_range_minutes":
                subset[
                    "pareto_walking_range_minutes"
                ].mean(),

            "median_walking_range_minutes":
                subset[
                    "pareto_walking_range_minutes"
                ].median(),

            "std_walking_range_minutes":
                subset[
                    "pareto_walking_range_minutes"
                ].std(),

            # ---------------------------------------------
            # Transfer-count range
            # ---------------------------------------------

            "mean_transfer_range":
                subset[
                    "pareto_transfer_range"
                ].mean(),

            "median_transfer_range":
                subset[
                    "pareto_transfer_range"
                ].median(),
        }
    )


summary_df = pd.DataFrame(
    summary_rows
)


SUMMARY_FILE = (
    FIGURE_DIR
    / "pareto_tradeoff_summary.csv"
)


summary_df.to_csv(
    SUMMARY_FILE,
    index=False,
    encoding="utf-8-sig"
)


# =========================================================
# PARETO = 5 WALKING-RANGE CHECK
# =========================================================

pareto_5_walking = (
    multi_df[
        multi_df[
            "pareto_route_count"
        ] == 5
    ][
        "pareto_walking_range_minutes"
    ]
    .dropna()
)


print()
print("-" * 90)
print("PARETO = 5 WALKING-RANGE CHECK")
print("-" * 90)


if len(
    pareto_5_walking
) > 0:

    print(
        pareto_5_walking
        .describe()
        .to_string()
    )

    print()

    print(
        "Value counts:"
    )

    print(
        pareto_5_walking
        .value_counts()
        .sort_index()
        .to_string()
    )

else:

    print(
        "No Pareto = 5 OD pairs."
    )


# =========================================================
# PRINT TRADE-OFF SUMMARY
# =========================================================

print()
print("=" * 90)
print("PARETO TRADE-OFF SUMMARY")
print("=" * 90)


print(
    summary_df.to_string(
        index=False
    )
)


# =========================================================
# FINAL OUTPUT
# =========================================================

print()
print("=" * 90)
print("THESIS FIGURES CREATED")
print("=" * 90)


print(
    "Figure 5-2 : Pareto-set size distribution"
)

print(
    "Figure 5-3 : Station Multi-Pareto ranking"
)

print(
    "Figure 5-4 : Multi-Pareto frequency vs richness"
)

print(
    "Figure 5-5 : Pareto-set size vs travel-time range"
)

print(
    "Figure 5-6 : Pareto-set size vs walking-time range"
)


print()

print(
    f"Summary CSV:\n{SUMMARY_FILE}"
)


print()

print(
    f"Figures saved to:\n{FIGURE_DIR}"
)


print()
print(
    "Chapter 5 thesis figure generation completed successfully."
)