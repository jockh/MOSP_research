from src.paths import PROJECT_ROOT, RESULTS_DIR as CANONICAL_RESULTS_DIR, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, result_path, project_path
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

if __name__ == "__main__":







    # =========================================================
    # PROJECT PATH
    # =========================================================

    ROOT = PROJECT_ROOT

    RESULT_DIR = (
        CANONICAL_RESULTS_DIR / 'experiment_05_all_od'
    )

    FIGURE_DIR = (
        RESULT_DIR
        / "chapter5_figures"
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
                f"找不到檔案：\n{file}"
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


    print("=" * 90)
    print("CHAPTER 5 FIGURE GENERATION")
    print("=" * 90)

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
    # FONT
    # =========================================================
    #
    # Windows:
    # Microsoft JhengHei usually supports Chinese.
    #
    # If Chinese text cannot display on your computer,
    # change this to another installed Chinese font.
    # =========================================================

    plt.rcParams["font.family"] = "Microsoft JhengHei"

    plt.rcParams["axes.unicode_minus"] = False


    # =========================================================
    # COMMON SAVE FUNCTION
    # =========================================================

    def save_figure(
        filename
    ):
        path = (
            FIGURE_DIR
            / filename
        )

        plt.tight_layout()

        plt.savefig(
            path,
            dpi=300,
            bbox_inches="tight"
        )

        plt.close()

        print(
            f"Saved: {path}"
        )


    # =========================================================
    # FIGURE 5-2
    # PARETO SET SIZE DISTRIBUTION
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
        figsize=(8, 5)
    )

    bars = ax.bar(
        distribution.index.astype(str),
        percentage.values
    )


    ax.set_xlabel(
        "Number of Pareto Routes"
    )

    ax.set_ylabel(
        "Percentage of OD Pairs (%)"
    )

    ax.set_title(
        "Distribution of Pareto-Set Size"
    )


    # Add percentage labels
    for bar, value in zip(
        bars,
        percentage.values
    ):

        ax.text(
            bar.get_x()
            + bar.get_width() / 2,

            bar.get_height()
            + 0.8,

            f"{value:.2f}%",

            ha="center",
            va="bottom",
            fontsize=10
        )


    ax.set_ylim(
        0,
        max(
            percentage.values
        ) * 1.15
    )


    save_figure(
        "figure_5_2_pareto_set_distribution.png"
    )


    # =========================================================
    # FIGURE 5-3
    # TOP STATIONS BY MULTI-PARETO RATE
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


    # Reverse order so largest appears at top
    top_origin = (
        top_origin
        .sort_values(
            "multi_pareto_percentage",
            ascending=True
        )
    )


    fig, ax = plt.subplots(
        figsize=(9, 7)
    )

    bars = ax.barh(
        top_origin["origin"],
        top_origin[
            "multi_pareto_percentage"
        ]
    )


    ax.set_xlabel(
        "Multi-Pareto OD Percentage (%)"
    )

    ax.set_ylabel(
        "Origin Station"
    )

    ax.set_title(
        "Top 15 Stations by Multi-Pareto OD Percentage"
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


    save_figure(
        "figure_5_3_station_multi_pareto_rate.png"
    )


    # =========================================================
    # FIGURE 5-4
    # MULTI-PARETO RATE VS MEAN PARETO SIZE
    # =========================================================

    fig, ax = plt.subplots(
        figsize=(8, 6)
    )


    ax.scatter(
        origin_df[
            "multi_pareto_percentage"
        ],
        origin_df[
            "mean_pareto_size"
        ],
        s=45,
        alpha=0.75
    )


    ax.set_xlabel(
        "Multi-Pareto OD Percentage (%)"
    )

    ax.set_ylabel(
        "Mean Pareto-Set Size"
    )

    ax.set_title(
        "Multi-Pareto Frequency and Pareto-Set Richness"
    )


    # ---------------------------------------------------------
    # Label only the most important stations
    # to avoid making the figure unreadable.
    # ---------------------------------------------------------

    label_stations = (
        origin_df
        .sort_values(
            [
                "multi_pareto_percentage",
                "mean_pareto_size"
            ],
            ascending=False
        )
        .head(10)
    )


    for _, row in (
        label_stations.iterrows()
    ):

        ax.annotate(
            row["origin"],

            (
                row[
                    "multi_pareto_percentage"
                ],
                row[
                    "mean_pareto_size"
                ]
            ),

            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )


    save_figure(
        "figure_5_4_frequency_vs_richness.png"
    )


    # =========================================================
    # MULTI-PARETO DATA ONLY
    # =========================================================
    #
    # Pareto count = 1 has no internal trade-off range,
    # so Figures 5-5 and 5-6 focus on OD pairs with
    # at least two Pareto routes.
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
        ].unique()
    )


    # =========================================================
    # FIGURE 5-5
    # PARETO COUNT VS TRAVEL-TIME RANGE
    # =========================================================

    time_box_data = []

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


    fig, ax = plt.subplots(
        figsize=(8, 5.5)
    )


    ax.boxplot(
        time_box_data,
        tick_labels=[
            str(x)
            for x in pareto_sizes
        ],
        showfliers=False
    )


    ax.set_xlabel(
        "Number of Pareto Routes"
    )

    ax.set_ylabel(
        "Travel-Time Range within Pareto Set (min)"
    )

    ax.set_title(
        "Pareto-Set Size and Travel-Time Trade-off"
    )


    save_figure(
        "figure_5_5_pareto_size_vs_time_range.png"
    )


    # =========================================================
    # FIGURE 5-6
    # PARETO COUNT VS WALKING RANGE
    # Thesis version
    # =========================================================

    walking_box_data = []
    sample_sizes = []

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

        walking_box_data.append(values)
        sample_sizes.append(len(values))


    fig, ax = plt.subplots(
        figsize=(7.2, 5.0)
    )


    bp = ax.boxplot(
        walking_box_data,

        tick_labels=[
            str(x)
            for x in pareto_sizes
        ],

        widths=0.48,

        showfliers=False,

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
    # Axis labels
    # ---------------------------------------------------------

    ax.set_xlabel(
        "Number of Pareto Routes",
        fontsize=11
    )

    ax.set_ylabel(
        "Range of Transfer-Walking Time (min)",
        fontsize=11
    )


    # ---------------------------------------------------------
    # Sample size under each category
    # ---------------------------------------------------------

    for i, n in enumerate(
        sample_sizes,
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


    # ---------------------------------------------------------
    # Explain collapsed box for Pareto = 5
    # ---------------------------------------------------------

    if 5 in pareto_sizes:

        idx = pareto_sizes.index(5)

        values = walking_box_data[idx]

        if len(values) > 0 and len(set(values)) == 1:

            y = values[0]

            ax.annotate(
                f"All observations = {y:.1f} min",
                xy=(idx + 1, y),
                xytext=(idx + 0.35, y + 1.0),
                arrowprops={
                    "arrowstyle": "->",
                    "linewidth": 0.9
                },
                fontsize=9
            )


    # ---------------------------------------------------------
    # Styling
    # ---------------------------------------------------------

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


    ax.grid(
        axis="y",
        linestyle="--",
        linewidth=0.6,
        alpha=0.35
    )


    plt.tight_layout()


    save_figure(
        "figure_5_6_pareto_size_vs_walking_range_thesis.png"
    )

    # =========================================================
    # SUMMARY TABLE FOR FIGURES 5-5 AND 5-6
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

                "mean_time_range_minutes":
                    subset[
                        "pareto_time_range_minutes"
                    ].mean(),

                "median_time_range_minutes":
                    subset[
                        "pareto_time_range_minutes"
                    ].median(),

                "mean_walking_range_minutes":
                    subset[
                        "pareto_walking_range_minutes"
                    ].mean(),

                "median_walking_range_minutes":
                    subset[
                        "pareto_walking_range_minutes"
                    ].median(),

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
    # PRINT RESULTS
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


    print()
    print("=" * 90)
    print("FIGURES CREATED")
    print("=" * 90)

    print(
        "Figure 5-2: Pareto-set size distribution"
    )

    print(
        "Figure 5-3: Station Multi-Pareto ranking"
    )

    print(
        "Figure 5-4: Frequency vs richness"
    )

    print(
        "Figure 5-5: Pareto size vs travel-time range"
    )

    print(
        "Figure 5-6: Pareto size vs walking-time range"
    )


    print()
    print(
        f"Figures saved to:\n"
        f"{FIGURE_DIR}"
    )

    print()
    print(
        "Chapter 5 figure generation completed."
    )