from src.paths import PROJECT_ROOT, RESULTS_DIR as CANONICAL_RESULTS_DIR, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, result_path, project_path
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

if __name__ == "__main__":








    # =========================================================
    # CHAPTER 5 THESIS FIGURES — FINAL VERSION
    # =========================================================
    # Output:
    #   Figure 5-2  Pareto-set size distribution
    #   Figure 5-3  Top stations by Multi-Pareto OD percentage
    #   Figure 5-4  Multi-Pareto frequency vs Pareto-set richness
    #   Figure 5-5  Pareto-set size vs travel-time range
    #   Figure 5-6  Pareto-set size vs transfer-walking-time range
    #
    # Each figure is exported as:
    #   - 600 dpi PNG (for Word / thesis insertion)
    #   - PDF vector figure (for LaTeX / publication-quality output)
    #
    # The figures intentionally have no in-figure title.
    # Use the thesis caption below each figure instead.
    # =========================================================


    # =========================================================
    # 1. LOCATE PROJECT ROOT
    # =========================================================
    # Expected structure:
    #
    # <ROOT>/
    # ├─ experiments/
    # │  ├─ plot_chapter5_thesis_final.py
    # │  └─ results/
    # │     └─ experiment_05_all_od/
    # │        ├─ all_od_summary.csv
    # │        └─ origin_summary.csv
    # =========================================================

    SCRIPT_DIR = PROJECT_ROOT
    ROOT = PROJECT_ROOT

    pass  # canonical root is explicit

    pass  # canonical root is explicit


    # =========================================================
    # 2. PATHS
    # =========================================================

    RESULT_DIR = (
        CANONICAL_RESULTS_DIR / 'experiment_05_all_od'
    )

    FIGURE_DIR = (
        RESULT_DIR
        / "chapter5_figures_thesis"
    )

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OD_FILE = RESULT_DIR / "all_od_summary.csv"
    ORIGIN_SUMMARY_FILE = RESULT_DIR / "origin_summary.csv"


    # =========================================================
    # 3. READ DATA
    # =========================================================

    od_df = pd.read_csv(
        OD_FILE,
        encoding="utf-8-sig",
    )

    origin_df = pd.read_csv(
        ORIGIN_SUMMARY_FILE,
        encoding="utf-8-sig",
    )


    # =========================================================
    # 4. VALIDATE REQUIRED COLUMNS
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

    missing_od_columns = required_od_columns - set(od_df.columns)
    missing_origin_columns = required_origin_columns - set(origin_df.columns)

    if missing_od_columns:
        raise ValueError(
            "all_od_summary.csv 缺少欄位："
            + ", ".join(sorted(missing_od_columns))
        )

    if missing_origin_columns:
        raise ValueError(
            "origin_summary.csv 缺少欄位："
            + ", ".join(sorted(missing_origin_columns))
        )


    # =========================================================
    # 5. INPUT SUMMARY
    # =========================================================

    print("=" * 90)
    print("CHAPTER 5 THESIS FIGURE GENERATION — FINAL")
    print("=" * 90)
    print(f"Project root : {ROOT}")
    print(f"OD rows      : {len(od_df):,}")
    print(f"Station rows : {len(origin_df):,}")
    print(f"Output folder: {FIGURE_DIR}")


    # =========================================================
    # 6. GLOBAL THESIS STYLE
    # =========================================================
    # Microsoft JhengHei is used because Figure 5-3 / 5-4
    # contain Chinese station names on Windows.
    # =========================================================

    plt.rcParams.update(
        {
            "font.family": "Microsoft JhengHei",
            "axes.unicode_minus": False,
            "font.size": 10,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


    def apply_thesis_style(ax, grid_axis="y"):
        """Apply one consistent thesis-friendly figure style."""

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(1.0)
        ax.spines["bottom"].set_linewidth(1.0)

        ax.tick_params(
            axis="both",
            direction="out",
            width=0.9,
        )

        if grid_axis is not None:
            ax.grid(
                axis=grid_axis,
                linestyle="--",
                linewidth=0.6,
                alpha=0.30,
            )
            ax.set_axisbelow(True)


    def save_figure(fig, filename_stem, bottom_extra=0.0):
        """Save a 600-dpi PNG and a vector PDF."""

        if bottom_extra > 0:
            fig.tight_layout(
                rect=[0, bottom_extra, 1, 1]
            )
        else:
            fig.tight_layout()

        png_path = FIGURE_DIR / f"{filename_stem}.png"
        pdf_path = FIGURE_DIR / f"{filename_stem}.pdf"

        fig.savefig(
            png_path,
            dpi=600,
            bbox_inches="tight",
        )

        fig.savefig(
            pdf_path,
            bbox_inches="tight",
        )

        plt.close(fig)

        print(f"Saved PNG: {png_path}")
        print(f"Saved PDF: {pdf_path}")


    # =========================================================
    # FIGURE 5-2
    # DISTRIBUTION OF PARETO-SET SIZE
    # =========================================================
    # Research purpose:
    # Determine whether multiple Pareto routes are rare exceptions
    # or a meaningful phenomenon in the real Taipei Metro network.
    # =========================================================

    distribution = (
        od_df["pareto_route_count"]
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
        width=0.58,
        edgecolor="black",
        linewidth=0.9,
        facecolor="0.78",
    )

    ax.set_xlabel(
        "Number of Pareto Routes"
    )

    ax.set_ylabel(
        "Percentage of OD Pairs (%)"
    )

    for bar, count, pct in zip(
        bars,
        distribution.values,
        percentage.values,
    ):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + percentage.max() * 0.018,
            f"{count:,}\n({pct:.2f}%)",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_ylim(
        0,
        percentage.max() * 1.16,
    )

    apply_thesis_style(
        ax,
        grid_axis="y",
    )

    save_figure(
        fig,
        "figure_5_2_pareto_set_distribution",
    )


    # =========================================================
    # FIGURE 5-3
    # TOP 15 ORIGIN STATIONS BY MULTI-PARETO RATE
    # =========================================================
    # Research purpose:
    # Examine whether multi-Pareto OD pairs are concentrated around
    # particular parts of the real network.
    # =========================================================

    top_n = 15

    top_origin = (
        origin_df
        .sort_values(
            "multi_pareto_percentage",
            ascending=False,
        )
        .head(top_n)
        .sort_values(
            "multi_pareto_percentage",
            ascending=True,
        )
        .copy()
    )

    fig, ax = plt.subplots(
        figsize=(7.6, 6.2)
    )

    bars = ax.barh(
        top_origin["origin"],
        top_origin["multi_pareto_percentage"],
        height=0.62,
        edgecolor="black",
        linewidth=0.8,
        facecolor="0.78",
    )

    ax.set_xlabel(
        "Multi-Pareto OD Percentage (%)"
    )

    ax.set_ylabel(
        "Origin Station"
    )

    ax.set_xlim(
        0,
        100,
    )

    for bar, value in zip(
        bars,
        top_origin["multi_pareto_percentage"],
    ):
        ax.text(
            value + 1.0,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}%",
            va="center",
            fontsize=8.5,
        )

    apply_thesis_style(
        ax,
        grid_axis="x",
    )

    save_figure(
        fig,
        "figure_5_3_station_multi_pareto_rate",
    )


    # =========================================================
    # FIGURE 5-4
    # MULTI-PARETO FREQUENCY VS PARETO-SET RICHNESS
    # =========================================================
    # Research purpose:
    # Distinguish two different concepts:
    #   1. How often a station produces Multi-Pareto OD pairs.
    #   2. How many Pareto alternatives those OD pairs tend to have.
    # =========================================================

    fig, ax = plt.subplots(
        figsize=(7.2, 5.2)
    )

    ax.scatter(
        origin_df["multi_pareto_percentage"],
        origin_df["mean_pareto_size"],
        s=32,
        facecolor="0.45",
        edgecolor="black",
        linewidth=0.45,
        alpha=0.80,
    )

    ax.set_xlabel(
        "Multi-Pareto OD Percentage (%)"
    )

    ax.set_ylabel(
        "Mean Pareto-Set Size"
    )

    # Label only the most important stations to avoid clutter.
    label_stations = (
        origin_df
        .sort_values(
            [
                "multi_pareto_percentage",
                "mean_pareto_size",
            ],
            ascending=[False, False],
        )
        .head(8)
    )

    for _, row in label_stations.iterrows():
        ax.annotate(
            row["origin"],
            (
                row["multi_pareto_percentage"],
                row["mean_pareto_size"],
            ),
            xytext=(5, 4),
            textcoords="offset points",
            fontsize=8,
        )

    apply_thesis_style(
        ax,
        grid_axis="both",
    )

    save_figure(
        fig,
        "figure_5_4_frequency_vs_richness",
    )


    # =========================================================
    # MULTI-PARETO OD DATA
    # =========================================================
    # Pareto count = 1 contains no internal trade-off range.
    # Therefore Figures 5-5 and 5-6 use only OD pairs with
    # at least two Pareto routes.
    # =========================================================

    multi_df = (
        od_df[
            od_df["pareto_route_count"] > 1
        ]
        .copy()
    )

    multi_df["pareto_route_count"] = (
        multi_df["pareto_route_count"]
        .astype(int)
    )

    pareto_sizes = sorted(
        multi_df["pareto_route_count"]
        .dropna()
        .unique()
    )


    def make_boxplot_data(column):
        """Return one numpy array and one sample size per Pareto-set size."""

        data = []
        sample_sizes = []

        for count in pareto_sizes:
            values = (
                multi_df.loc[
                    multi_df["pareto_route_count"] == count,
                    column,
                ]
                .dropna()
                .to_numpy(dtype=float)
            )

            data.append(values)
            sample_sizes.append(len(values))

        return data, sample_sizes


    def thesis_boxplot(
        ax,
        data,
        showfliers=True,
    ):
        """Create the common thesis boxplot style."""

        return ax.boxplot(
            data,
            tick_labels=[str(x) for x in pareto_sizes],
            widths=0.50,
            patch_artist=True,
            showfliers=showfliers,
            medianprops={
                "color": "black",
                "linewidth": 1.8,
            },
            boxprops={
                "facecolor": "0.88",
                "edgecolor": "black",
                "linewidth": 1.2,
            },
            whiskerprops={
                "color": "black",
                "linewidth": 1.1,
            },
            capprops={
                "color": "black",
                "linewidth": 1.1,
            },
            flierprops={
                "marker": "o",
                "markerfacecolor": "none",
                "markeredgecolor": "black",
                "markersize": 3.2,
                "markeredgewidth": 0.8,
                "alpha": 0.55,
            },
        )


    def add_sample_sizes(
        ax,
        sample_sizes,
    ):
        """Display n below each x-axis category."""

        for i, n in enumerate(
            sample_sizes,
            start=1,
        ):
            ax.text(
                i,
                -0.12,
                f"n = {n:,}",
                transform=ax.get_xaxis_transform(),
                ha="center",
                va="top",
                fontsize=8.5,
            )


    def deterministic_duplicate_jitter(
        values,
        center,
        half_width=0.12,
    ):
        """
        Give duplicated observations a deterministic horizontal spread.

        This is used only for Pareto = 5 in Figure 5-6, where the box
        collapses because most observations equal 6 minutes.  The spread
        makes the actual 6 / 8 / 9 minute observations visible without
        random jitter or duplicated boxplot outliers.
        """

        values = np.asarray(values, dtype=float)
        x = np.empty(len(values), dtype=float)

        for y in np.unique(values):
            indices = np.where(values == y)[0]
            n = len(indices)

            if n == 1:
                offsets = np.array([0.0])
            else:
                offsets = np.linspace(
                    -half_width,
                    half_width,
                    n,
                )

            x[indices] = center + offsets

        return x


    # =========================================================
    # FIGURE 5-5
    # PARETO-SET SIZE VS TRAVEL-TIME RANGE
    # =========================================================
    # Research purpose:
    # Examine whether larger Pareto sets are accompanied by wider
    # differences in travel time among the available Pareto routes.
    # =========================================================

    time_box_data, time_sample_sizes = make_boxplot_data(
        "pareto_time_range_minutes"
    )

    fig, ax = plt.subplots(
        figsize=(7.2, 5.0)
    )

    thesis_boxplot(
        ax,
        time_box_data,
        showfliers=True,
    )

    ax.set_xlabel(
        "Number of Pareto Routes"
    )

    ax.set_ylabel(
        "Travel-Time Range within Pareto Set (min)"
    )

    add_sample_sizes(
        ax,
        time_sample_sizes,
    )

    apply_thesis_style(
        ax,
        grid_axis="y",
    )

    save_figure(
        fig,
        "figure_5_5_pareto_size_vs_time_range",
        bottom_extra=0.07,
    )


    # =========================================================
    # FIGURE 5-6
    # PARETO-SET SIZE VS TRANSFER-WALKING-TIME RANGE
    # =========================================================
    # Research purpose:
    # Examine whether larger Pareto sets are accompanied by greater
    # differences in transfer-walking burden.
    #
    # Special handling for Pareto = 5:
    #   36 OD pairs in the current result
    #   28 observations = 6 min
    #    6 observations = 8 min
    #    2 observations = 9 min
    #
    # Therefore Q1 = median = Q3 = 6 min and the box collapses.
    # We keep the collapsed box but replace its standard outlier symbols
    # with all actual Pareto=5 observations using deterministic jitter.
    # =========================================================

    walking_box_data, walking_sample_sizes = make_boxplot_data(
        "pareto_walking_range_minutes"
    )

    fig, ax = plt.subplots(
        figsize=(7.2, 5.0)
    )

    walking_bp = thesis_boxplot(
        ax,
        walking_box_data,
        showfliers=True,
    )

    # Show every Pareto=5 observation exactly once.
    if 5 in pareto_sizes:
        p5_index = pareto_sizes.index(5)
        p5_values = walking_box_data[p5_index]
        p5_x_position = p5_index + 1

        # Hide only the automatically drawn Pareto=5 fliers.
        # They would otherwise duplicate the 8- and 9-minute observations.
        walking_bp["fliers"][p5_index].set_visible(False)

        p5_x = deterministic_duplicate_jitter(
            p5_values,
            center=p5_x_position,
            half_width=0.12,
        )

        ax.scatter(
            p5_x,
            p5_values,
            s=15,
            facecolors="none",
            edgecolors="black",
            linewidths=0.7,
            alpha=0.65,
            zorder=3,
        )

    ax.set_xlabel(
        "Number of Pareto Routes"
    )

    ax.set_ylabel(
        "Transfer-Walking Time Range (min)"
    )

    add_sample_sizes(
        ax,
        walking_sample_sizes,
    )

    apply_thesis_style(
        ax,
        grid_axis="y",
    )

    save_figure(
        fig,
        "figure_5_6_pareto_size_vs_walking_range",
        bottom_extra=0.07,
    )


    # =========================================================
    # SUMMARY TABLE FOR FIGURES 5-5 AND 5-6
    # =========================================================

    summary_rows = []

    for count in pareto_sizes:
        subset = multi_df[
            multi_df["pareto_route_count"] == count
        ]

        summary_rows.append(
            {
                "pareto_route_count": count,
                "number_of_od_pairs": len(subset),
                "mean_time_range_minutes": subset[
                    "pareto_time_range_minutes"
                ].mean(),
                "median_time_range_minutes": subset[
                    "pareto_time_range_minutes"
                ].median(),
                "std_time_range_minutes": subset[
                    "pareto_time_range_minutes"
                ].std(),
                "mean_walking_range_minutes": subset[
                    "pareto_walking_range_minutes"
                ].mean(),
                "median_walking_range_minutes": subset[
                    "pareto_walking_range_minutes"
                ].median(),
                "std_walking_range_minutes": subset[
                    "pareto_walking_range_minutes"
                ].std(),
                "mean_transfer_range": subset[
                    "pareto_transfer_range"
                ].mean(),
                "median_transfer_range": subset[
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
        encoding="utf-8-sig",
    )


    # =========================================================
    # FINAL VALIDATION / OUTPUT
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

    if 5 in pareto_sizes:
        p5_walk = (
            multi_df.loc[
                multi_df["pareto_route_count"] == 5,
                "pareto_walking_range_minutes",
            ]
            .dropna()
        )

        print()
        print("PARETO = 5 WALKING-RANGE DISTRIBUTION")
        print("-" * 90)
        print(
            p5_walk
            .value_counts()
            .sort_index()
            .to_string()
        )

    print()
    print("=" * 90)
    print("THESIS FIGURES CREATED")
    print("=" * 90)
    print("Figure 5-2: Pareto-set size distribution")
    print("Figure 5-3: Station Multi-Pareto ranking")
    print("Figure 5-4: Multi-Pareto frequency vs richness")
    print("Figure 5-5: Pareto-set size vs travel-time range")
    print("Figure 5-6: Pareto-set size vs transfer-walking-time range")
    print()
    print(f"Summary CSV:\n{SUMMARY_FILE}")
    print()
    print(f"Figures saved to:\n{FIGURE_DIR}")
    print()
    print("Chapter 5 thesis figures completed successfully.")
