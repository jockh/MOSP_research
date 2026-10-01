from src.paths import PROJECT_ROOT, RESULTS_DIR as CANONICAL_RESULTS_DIR, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, result_path, project_path
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

if __name__ == "__main__":











    # =========================================================
    # BASIC SETTINGS
    # =========================================================

    CASE_ORIGIN = "東湖站"
    CASE_DESTINATION = "中原站"

    # Figure 5-9 中是否特別標出東湖 -> 中原案例
    HIGHLIGHT_CASE_IN_FIGURE_59 = True


    # =========================================================
    # FIND PROJECT ROOT
    # =========================================================
    #
    # Put this file somewhere inside your MOSP project.
    #
    # Recommended:
    #
    #   project_root/
    #   └─ experiments/
    #      └─ plot_chapter5_figures_7_9.py
    #
    # The program automatically searches upward for:
    #
    # experiments/results/experiment_05_all_od/
    # =========================================================

    SCRIPT_DIR = PROJECT_ROOT

    ROOT = PROJECT_ROOT

    pass  # canonical root is explicit


    pass  # canonical root is explicit


    # =========================================================
    # PATHS
    # =========================================================

    RESULT_DIR = (
        CANONICAL_RESULTS_DIR / 'experiment_05_all_od'
    )


    ROUTE_FILE = (
        RESULT_DIR
        / "all_od_pareto_routes.csv"
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
    # CHECK FILE
    # =========================================================

    if not ROUTE_FILE.exists():

        raise FileNotFoundError(
            f"\n找不到：\n{ROUTE_FILE}\n"
        )


    # =========================================================
    # READ DATA
    # =========================================================

    routes_df = pd.read_csv(
        ROUTE_FILE,
        encoding="utf-8-sig"
    )


    # =========================================================
    # CHECK REQUIRED COLUMNS
    # =========================================================

    required_columns = {
        "origin",
        "destination",
        "route_id",
        "travel_time_seconds",
        "travel_time_minutes",
        "transfers",
        "walking_seconds",
        "walking_minutes",
        "path",
    }


    missing_columns = (
        required_columns
        - set(routes_df.columns)
    )


    if missing_columns:

        raise ValueError(
            "\nall_od_pareto_routes.csv 缺少欄位：\n"
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )


    # =========================================================
    # GLOBAL FONT SETTINGS
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
    # THESIS STYLE
    # =========================================================

    def apply_thesis_style(
        ax,
        grid_axis="both"
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
    # SAVE FIGURE
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


        plt.savefig(
            png_path,
            dpi=600,
            bbox_inches="tight"
        )


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
    # CASE DATA
    # =========================================================

    case_df = (
        routes_df[
            (
                routes_df[
                    "origin"
                ] == CASE_ORIGIN
            )
            &
            (
                routes_df[
                    "destination"
                ] == CASE_DESTINATION
            )
        ]
        .copy()
    )


    if case_df.empty:

        raise ValueError(
            f"\n找不到案例："
            f"{CASE_ORIGIN} -> {CASE_DESTINATION}\n"
        )


    case_df = (
        case_df
        .sort_values(
            "route_id"
        )
        .reset_index(
            drop=True
        )
    )


    if len(case_df) != 5:

        print(
            "\nWARNING:"
        )

        print(
            f"{CASE_ORIGIN} -> {CASE_DESTINATION} "
            f"目前找到 {len(case_df)} 條 Pareto routes，"
            "不是預期的 5 條。"
        )


    # =========================================================
    # PRINT CASE DATA
    # =========================================================

    print()
    print("=" * 90)
    print(
        f"CASE: {CASE_ORIGIN} -> {CASE_DESTINATION}"
    )
    print("=" * 90)


    print(
        case_df[
            [
                "route_id",
                "travel_time_minutes",
                "transfers",
                "walking_minutes",
            ]
        ]
        .to_string(
            index=False
        )
    )


    # =========================================================
    # METRO LINE SETTINGS
    # =========================================================
    #
    # Used only in Figure 5-7.
    #
    # O#4 / O#5 are displayed as O because they belong to
    # the same Orange Line family in the thesis figure.
    # =========================================================

    LINE_COLORS = {

        "BR":
            "#A05A2C",

        "BL":
            "#0070BD",

        "R":
            "#E3002C",

        "G":
            "#008659",

        "O":
            "#F39800",

        "Y":
            "#FFD400",
    }


    def line_family(
        line_code
    ):

        line_code = str(
            line_code
        ).strip()

        if line_code.startswith(
            "O"
        ):

            return "O"

        return line_code


    def short_station_name(
        station
    ):

        station = str(
            station
        ).strip()

        if station.endswith(
            "站"
        ):

            station = station[:-1]

        return station


    # =========================================================
    # PATH PARSER
    # =========================================================
    #
    # Input example:
    #
    # 東湖站[BR] -> 南港軟體園區站[BR]
    # -> 南港展覽館站[BR]
    # -> 南港展覽館站[BL]
    # ...
    #
    # Output:
    #
    # [
    #   ("東湖站", "BR"),
    #   ("南港軟體園區站", "BR"),
    #   ...
    # ]
    # =========================================================

    def parse_state_path(
        path_string
    ):

        states = []

        parts = str(
            path_string
        ).split(
            " -> "
        )


        for part in parts:

            part = part.strip()

            match = re.match(
                r"^(.*?)\[(.*?)\]$",
                part
            )


            if match:

                station = (
                    match
                    .group(1)
                    .strip()
                )

                line = (
                    match
                    .group(2)
                    .strip()
                )

                states.append(
                    (
                        station,
                        line
                    )
                )


        return states


    # =========================================================
    # CONVERT PATH TO CONTIGUOUS LINE SEGMENTS
    # =========================================================
    #
    # Example:
    #
    # BR:
    # 東湖 -> 南港展覽館
    #
    # BL:
    # 南港展覽館 -> 忠孝新生
    #
    # O:
    # 忠孝新生 -> 景安
    #
    # Y:
    # 景安 -> 中原
    # =========================================================

    def path_to_segments(
        path_string
    ):

        states = parse_state_path(
            path_string
        )


        if not states:

            return []


        segments = []


        current_station = (
            states[0][0]
        )

        current_line = (
            line_family(
                states[0][1]
            )
        )

        segment_start = (
            current_station
        )

        segment_end = (
            current_station
        )


        for station, raw_line in states[1:]:

            new_line = (
                line_family(
                    raw_line
                )
            )


            if new_line == current_line:

                segment_end = station


            else:

                segments.append(
                    {
                        "line":
                            current_line,

                        "start":
                            segment_start,

                        "end":
                            segment_end,
                    }
                )


                current_line = (
                    new_line
                )

                segment_start = (
                    station
                )

                segment_end = (
                    station
                )


        segments.append(
            {
                "line":
                    current_line,

                "start":
                    segment_start,

                "end":
                    segment_end,
            }
        )


        return segments


    # =========================================================
    # PREPARE SEGMENTS FOR FIGURE 5-7
    # =========================================================

    route_segments = {}


    for _, row in (
        case_df.iterrows()
    ):

        route_id = int(
            row[
                "route_id"
            ]
        )


        route_segments[
            route_id
        ] = (
            path_to_segments(
                row[
                    "path"
                ]
            )
        )


    # =========================================================
    # FIGURE 5-7
    # ROUTE SCHEMATIC
    # =========================================================
    #
    # This is intentionally a schematic figure.
    #
    # It is NOT geographically proportional.
    #
    # Each colored box represents one continuous ride
    # on a Taipei Metro line.
    #
    # Arrows represent transfers between line segments.
    # =========================================================

    max_segments = max(
        len(x)
        for x in route_segments.values()
    )


    BOX_WIDTH = 2.15

    BOX_HEIGHT = 0.62

    BOX_GAP = 0.43


    summary_x = (
        max_segments
        * (
            BOX_WIDTH
            + BOX_GAP
        )
        + 0.15
    )


    fig, ax = plt.subplots(
        figsize=(
            13.2,
            6.3
        )
    )


    number_routes = len(
        case_df
    )


    for row_index, row in (
        case_df.iterrows()
    ):

        route_id = int(
            row[
                "route_id"
            ]
        )


        segments = (
            route_segments[
                route_id
            ]
        )


        y = (
            number_routes
            - row_index
        )


        # -----------------------------------------------------
        # Route ID on left
        # -----------------------------------------------------

        ax.text(
            -0.42,
            y,

            f"R{route_id}",

            ha="right",
            va="center",

            fontsize=11,
            fontweight="bold"
        )


        # -----------------------------------------------------
        # Draw line-segment boxes
        # -----------------------------------------------------

        for segment_index, segment in enumerate(
            segments
        ):

            x = (
                segment_index
                * (
                    BOX_WIDTH
                    + BOX_GAP
                )
            )


            line = (
                segment[
                    "line"
                ]
            )


            color = (
                LINE_COLORS.get(
                    line,
                    "#808080"
                )
            )


            rectangle = Rectangle(

                (
                    x,
                    y
                    - BOX_HEIGHT / 2
                ),

                BOX_WIDTH,
                BOX_HEIGHT,

                facecolor=color,
                edgecolor=color,

                linewidth=1.6,
                alpha=0.22
            )


            ax.add_patch(
                rectangle
            )


            start = (
                short_station_name(
                    segment[
                        "start"
                    ]
                )
            )


            end = (
                short_station_name(
                    segment[
                        "end"
                    ]
                )
            )


            if start == end:

                station_text = (
                    start
                )

            else:

                station_text = (
                    f"{start} → {end}"
                )


            segment_text = (
                f"{line}\n"
                f"{station_text}"
            )


            ax.text(
                x
                + BOX_WIDTH / 2,

                y,

                segment_text,

                ha="center",
                va="center",

                fontsize=8.7
            )


            # -------------------------------------------------
            # Transfer arrow
            # -------------------------------------------------

            if segment_index < (
                len(
                    segments
                )
                - 1
            ):

                next_x = (
                    (
                        segment_index
                        + 1
                    )
                    * (
                        BOX_WIDTH
                        + BOX_GAP
                    )
                )


                ax.annotate(
                    "",

                    xy=(
                        next_x - 0.05,
                        y
                    ),

                    xytext=(
                        x
                        + BOX_WIDTH
                        + 0.05,
                        y
                    ),

                    arrowprops={
                        "arrowstyle":
                            "->",

                        "linewidth":
                            1.0,

                        "color":
                            "0.35",
                    }
                )


        # -----------------------------------------------------
        # Cost summary on right
        # -----------------------------------------------------

        time_min = (
            row[
                "travel_time_minutes"
            ]
        )

        transfers = int(
            row[
                "transfers"
            ]
        )

        walking_min = (
            row[
                "walking_minutes"
            ]
        )


        summary_text = (

            f"{time_min:.2f} min\n"
            f"{transfers} transfers\n"
            f"{walking_min:.0f} min walk"
        )


        ax.text(
            summary_x,
            y,

            summary_text,

            ha="left",
            va="center",

            fontsize=9
        )


    # =========================================================
    # FIGURE 5-7 STYLE
    # =========================================================

    ax.set_xlim(
        -1.05,
        summary_x + 2.0
    )


    ax.set_ylim(
        0.4,
        number_routes + 0.7
    )


    ax.axis(
        "off"
    )


    # Small note at bottom
    ax.text(
        0,
        0.50,

        "Schematic only; segment lengths are not geographically proportional.",

        ha="left",
        va="center",

        fontsize=8,
        style="italic"
    )


    save_figure(
        "figure_5_7_donghu_zhongyuan_route_schematic"
    )


    # =========================================================
    # FIGURE 5-8
    # DONGHU -> ZHONGYUAN TRADE-OFF
    # =========================================================
    #
    # X = travel time
    # Y = transfer-walking time
    #
    # Marker shape = number of transfers
    # =========================================================

    fig, ax = plt.subplots(
        figsize=(
            7.4,
            5.6
        )
    )


    TRANSFER_MARKERS = {

        2:
            "o",

        3:
            "s",

        4:
            "^",

        5:
            "D",
    }


    # ---------------------------------------------------------
    # Plot by number of transfers
    # ---------------------------------------------------------

    unique_transfers = sorted(
        case_df[
            "transfers"
        ]
        .astype(int)
        .unique()
    )


    for transfer_count in unique_transfers:

        subset = (
            case_df[
                case_df[
                    "transfers"
                ].astype(int)
                == transfer_count
            ]
        )


        marker = (
            TRANSFER_MARKERS.get(
                transfer_count,
                "o"
            )
        )


        ax.scatter(

            subset[
                "travel_time_minutes"
            ],

            subset[
                "walking_minutes"
            ],

            marker=marker,

            s=90,

            alpha=0.85,

            label=(
                f"{transfer_count} transfers"
            ),

            zorder=3
        )


    # ---------------------------------------------------------
    # Annotate R1-R5
    # ---------------------------------------------------------

    ANNOTATION_OFFSETS = {

        1:
            (7, -15),

        2:
            (7, 8),

        3:
            (7, 8),

        4:
            (7, 8),

        5:
            (7, 8),
    }


    for _, row in (
        case_df.iterrows()
    ):

        route_id = int(
            row[
                "route_id"
            ]
        )


        offset = (
            ANNOTATION_OFFSETS.get(
                route_id,
                (6, 6)
            )
        )


        ax.annotate(

            f"R{route_id}",

            (
                row[
                    "travel_time_minutes"
                ],

                row[
                    "walking_minutes"
                ]
            ),

            xytext=offset,

            textcoords="offset points",

            fontsize=10,
            fontweight="bold"
        )


    # ---------------------------------------------------------
    # Axis labels
    # ---------------------------------------------------------

    ax.set_xlabel(
        "Travel Time (min)"
    )


    ax.set_ylabel(
        "Transfer-Walking Time (min)"
    )


    # ---------------------------------------------------------
    # Axis margins
    # ---------------------------------------------------------

    x_min = (
        case_df[
            "travel_time_minutes"
        ].min()
    )

    x_max = (
        case_df[
            "travel_time_minutes"
        ].max()
    )

    y_min = (
        case_df[
            "walking_minutes"
        ].min()
    )

    y_max = (
        case_df[
            "walking_minutes"
        ].max()
    )


    ax.set_xlim(
        x_min - 2.0,
        x_max + 2.3
    )


    ax.set_ylim(
        y_min - 1.2,
        y_max + 1.5
    )


    # ---------------------------------------------------------
    # Legend
    # ---------------------------------------------------------

    ax.legend(
        frameon=False,
        title="Transfer Count",
        loc="upper right"
    )


    apply_thesis_style(
        ax,
        grid_axis="both"
    )


    save_figure(
        "figure_5_8_donghu_zhongyuan_tradeoff"
    )


    # =========================================================
    # FIGURE 5-9
    # WHOLE-NETWORK PRACTICAL TRADE-OFF
    # =========================================================
    #
    # Question:
    #
    # Compared with the fastest Pareto route for each OD,
    # how much additional travel time must a traveler accept
    # to reduce walking and/or transfers?
    #
    #
    # X:
    # Additional travel time relative to fastest Pareto route
    #
    # Y:
    # Walking time saved relative to fastest Pareto route
    #
    # Y > 0:
    # alternative requires LESS walking
    #
    # Y < 0:
    # alternative requires MORE walking
    #
    #
    # Transfer saving:
    #
    # + value -> fewer transfers than fastest route
    # 0       -> same transfers
    # - value -> more transfers
    # =========================================================


    # =========================================================
    # SELECT ONE FASTEST BASELINE FOR EACH OD
    # =========================================================
    #
    # Tie-breaking rule:
    #
    # 1. lowest travel time
    # 2. fewer transfers
    # 3. shorter walking time
    # 4. lower route_id
    #
    # This makes the baseline deterministic.
    # =========================================================

    baseline_source = (
        routes_df
        .sort_values(
            [
                "origin",
                "destination",
                "travel_time_seconds",
                "transfers",
                "walking_seconds",
                "route_id",
            ]
        )
    )


    baseline_df = (
        baseline_source
        .groupby(
            [
                "origin",
                "destination",
            ],
            as_index=False
        )
        .first()
    )


    baseline_df = (
        baseline_df[
            [
                "origin",
                "destination",
                "route_id",
                "travel_time_minutes",
                "transfers",
                "walking_minutes",
            ]
        ]
        .rename(
            columns={

                "route_id":
                    "baseline_route_id",

                "travel_time_minutes":
                    "baseline_time_minutes",

                "transfers":
                    "baseline_transfers",

                "walking_minutes":
                    "baseline_walking_minutes",
            }
        )
    )


    # =========================================================
    # MERGE BASELINE INTO ALL PARETO ROUTES
    # =========================================================

    comparison_df = (
        routes_df
        .merge(
            baseline_df,

            on=[
                "origin",
                "destination",
            ],

            how="left"
        )
    )


    # =========================================================
    # REMOVE BASELINE ROUTE ITSELF
    # =========================================================

    alternative_df = (
        comparison_df[
            comparison_df[
                "route_id"
            ]
            !=
            comparison_df[
                "baseline_route_id"
            ]
        ]
        .copy()
    )


    # =========================================================
    # COMPUTE PRACTICAL TRADE-OFF VALUES
    # =========================================================

    alternative_df[
        "additional_travel_time_minutes"
    ] = (
        alternative_df[
            "travel_time_minutes"
        ]
        -
        alternative_df[
            "baseline_time_minutes"
        ]
    )


    alternative_df[
        "walking_time_saved_minutes"
    ] = (
        alternative_df[
            "baseline_walking_minutes"
        ]
        -
        alternative_df[
            "walking_minutes"
        ]
    )


    alternative_df[
        "transfer_saving"
    ] = (
        alternative_df[
            "baseline_transfers"
        ]
        -
        alternative_df[
            "transfers"
        ]
    )


    # Numerical tolerance
    alternative_df.loc[
        alternative_df[
            "additional_travel_time_minutes"
        ].abs() < 1e-10,

        "additional_travel_time_minutes"

    ] = 0.0


    alternative_df.loc[
        alternative_df[
            "walking_time_saved_minutes"
        ].abs() < 1e-10,

        "walking_time_saved_minutes"

    ] = 0.0


    # =========================================================
    # TRANSFER CATEGORY
    # =========================================================

    def transfer_category(
        value
    ):

        if value > 0:

            return "Fewer transfers"

        elif value < 0:

            return "More transfers"

        else:

            return "Same transfers"


    alternative_df[
        "transfer_category"
    ] = (
        alternative_df[
            "transfer_saving"
        ]
        .apply(
            transfer_category
        )
    )


    # =========================================================
    # SAVE FIGURE 5-9 ANALYSIS DATA
    # =========================================================

    FIGURE_59_DATA = (
        FIGURE_DIR
        / "figure_5_9_network_tradeoff_data.csv"
    )


    alternative_df[
        [
            "origin",
            "destination",
            "route_id",
            "baseline_route_id",

            "travel_time_minutes",
            "walking_minutes",
            "transfers",

            "baseline_time_minutes",
            "baseline_walking_minutes",
            "baseline_transfers",

            "additional_travel_time_minutes",
            "walking_time_saved_minutes",
            "transfer_saving",
            "transfer_category",
        ]
    ].to_csv(
        FIGURE_59_DATA,
        index=False,
        encoding="utf-8-sig"
    )


    # =========================================================
    # FIGURE 5-9
    # NETWORK-WIDE PRACTICAL TRADE-OFF — FINAL THESIS VERSION
    # =========================================================

    fig, ax = plt.subplots(
        figsize=(8.2, 6.0)
    )


    CATEGORY_STYLE = {

        "Fewer transfers": {
            "marker": "o",
            "size": 12,
            "alpha": 0.14,
        },

        "Same transfers": {
            "marker": "s",
            "size": 12,
            "alpha": 0.12,
        },

        "More transfers": {
            "marker": "^",
            "size": 12,
            "alpha": 0.12,
        },
    }


    for category in [
        "Fewer transfers",
        "Same transfers",
        "More transfers",
    ]:

        subset = alternative_df[
            alternative_df[
                "transfer_category"
            ] == category
        ]

        style = CATEGORY_STYLE[
            category
        ]

        ax.scatter(
            subset[
                "additional_travel_time_minutes"
            ],

            subset[
                "walking_time_saved_minutes"
            ],

            marker=style[
                "marker"
            ],

            s=style[
                "size"
            ],

            alpha=style[
                "alpha"
            ],

            label=category,

            rasterized=True,

            zorder=2
        )


    # ---------------------------------------------------------
    # y = 0 reference line
    # ---------------------------------------------------------

    ax.axhline(
        y=0,
        linewidth=1.0,
        linestyle="--",
        zorder=1
    )


    # =========================================================
    # HIGHLIGHT DONGHU -> ZHONGYUAN
    # =========================================================

    highlight_df = alternative_df[
        (
            alternative_df[
                "origin"
            ] == CASE_ORIGIN
        )
        &
        (
            alternative_df[
                "destination"
            ] == CASE_DESTINATION
        )
    ].copy()


    ax.scatter(
        highlight_df[
            "additional_travel_time_minutes"
        ],

        highlight_df[
            "walking_time_saved_minutes"
        ],

        marker="*",

        s=130,

        edgecolors="black",

        linewidths=0.8,

        label="Donghu → Zhongyuan",

        zorder=5
    )


    # ---------------------------------------------------------
    # Case labels
    # ---------------------------------------------------------

    label_offsets = {

        2: (6, 5),

        3: (6, -13),

        4: (6, 5),

        5: (6, 5),
    }


    for _, row in highlight_df.iterrows():

        route_id = int(
            row[
                "route_id"
            ]
        )

        ax.annotate(
            f"R{route_id}",

            (
                row[
                    "additional_travel_time_minutes"
                ],

                row[
                    "walking_time_saved_minutes"
                ]
            ),

            xytext=label_offsets.get(
                route_id,
                (6, 6)
            ),

            textcoords="offset points",

            fontsize=8.5,

            fontweight="bold",

            zorder=6
        )


    # =========================================================
    # AXES
    # =========================================================

    ax.set_xlabel(
        "Additional Travel Time vs. Fastest Route (min)"
    )

    ax.set_ylabel(
        "Transfer-Walking Time Saved vs. Fastest Route (min)"
    )


    # Give left side a little space for points near x = 0
    ax.set_xlim(
        -1.5,
        alternative_df[
            "additional_travel_time_minutes"
        ].max() + 3
    )


    # =========================================================
    # LEGEND
    # =========================================================

    ax.legend(
        frameon=False,
        loc="upper right"
    )


    apply_thesis_style(
        ax,
        grid_axis="both"
    )


    save_figure(
        "figure_5_9_network_practical_tradeoff"
    )


    # =========================================================
    # REFERENCE LINE
    # =========================================================
    #
    # y = 0:
    #
    # above -> walking is reduced
    # below -> walking is increased
    # =========================================================

    ax.axhline(
        y=0,
        linewidth=1.0,
        linestyle="--"
    )


    ax.axvline(
        x=0,
        linewidth=0.8,
        linestyle=":"
    )


    # =========================================================
    # HIGHLIGHT DONGHU -> ZHONGYUAN
    # =========================================================

    if HIGHLIGHT_CASE_IN_FIGURE_59:

        highlight_df = (
            alternative_df[
                (
                    alternative_df[
                        "origin"
                    ] == CASE_ORIGIN
                )
                &
                (
                    alternative_df[
                        "destination"
                    ] == CASE_DESTINATION
                )
            ]
            .copy()
        )


        ax.scatter(

            highlight_df[
                "additional_travel_time_minutes"
            ],

            highlight_df[
                "walking_time_saved_minutes"
            ],

            marker="*",

            s=120,

            edgecolors="black",

            linewidths=0.8,

            label=(
                "Donghu → Zhongyuan"
            ),

            zorder=5
        )


        for _, row in (
            highlight_df.iterrows()
        ):

            route_id = int(
                row[
                    "route_id"
                ]
            )


            ax.annotate(

                f"R{route_id}",

                (
                    row[
                        "additional_travel_time_minutes"
                    ],

                    row[
                        "walking_time_saved_minutes"
                    ]
                ),

                xytext=(
                    5,
                    5
                ),

                textcoords="offset points",

                fontsize=8,

                zorder=6
            )


    # =========================================================
    # AXIS LABELS
    # =========================================================

    ax.set_xlabel(
        "Additional Travel Time vs. Fastest Route (min)"
    )


    ax.set_ylabel(
        "Transfer-Walking Time Saved vs. Fastest Route (min)"
    )


    # =========================================================
    # SMALL INTERPRETATION TEXT
    # =========================================================

    ax.text(

        0.985,
        0.975,

        "Above 0: less walking\n"
        "Below 0: more walking",

        transform=ax.transAxes,

        ha="right",
        va="top",

        fontsize=8
    )


    # =========================================================
    # LEGEND
    # =========================================================

    ax.legend(
        frameon=False,
        loc="upper left"
    )


    apply_thesis_style(
        ax,
        grid_axis="both"
    )


    save_figure(
        "figure_5_9_network_practical_tradeoff"
    )


    # =========================================================
    # SUMMARY FOR FIGURE 5-9
    # =========================================================

    print()
    print("=" * 90)
    print("FIGURE 5-9 NETWORK-WIDE TRADE-OFF SUMMARY")
    print("=" * 90)


    print(
        f"Alternative Pareto routes: "
        f"{len(alternative_df)}"
    )


    print(
        f"Mean additional travel time: "
        f"{alternative_df['additional_travel_time_minutes'].mean():.2f} min"
    )


    print(
        f"Median additional travel time: "
        f"{alternative_df['additional_travel_time_minutes'].median():.2f} min"
    )


    print(
        f"Mean walking time saved: "
        f"{alternative_df['walking_time_saved_minutes'].mean():.2f} min"
    )


    print(
        f"Median walking time saved: "
        f"{alternative_df['walking_time_saved_minutes'].median():.2f} min"
    )


    walking_improved = (
        alternative_df[
            "walking_time_saved_minutes"
        ] > 0
    ).mean() * 100


    transfer_improved = (
        alternative_df[
            "transfer_saving"
        ] > 0
    ).mean() * 100


    both_improved = (
        (
            alternative_df[
                "walking_time_saved_minutes"
            ] > 0
        )
        &
        (
            alternative_df[
                "transfer_saving"
            ] > 0
        )
    ).mean() * 100


    print(
        f"Alternatives with less walking: "
        f"{walking_improved:.2f}%"
    )


    print(
        f"Alternatives with fewer transfers: "
        f"{transfer_improved:.2f}%"
    )


    print(
        f"Alternatives with both less walking "
        f"and fewer transfers: "
        f"{both_improved:.2f}%"
    )


    # =========================================================
    # DONGHU -> ZHONGYUAN RELATIVE TO FASTEST ROUTE
    # =========================================================

    case_comparison = (
        alternative_df[
            (
                alternative_df[
                    "origin"
                ] == CASE_ORIGIN
            )
            &
            (
                alternative_df[
                    "destination"
                ] == CASE_DESTINATION
            )
        ]
        [
            [
                "route_id",
                "additional_travel_time_minutes",
                "walking_time_saved_minutes",
                "transfer_saving",
            ]
        ]
        .sort_values(
            "route_id"
        )
    )


    print()
    print("=" * 90)
    print(
        f"{CASE_ORIGIN} -> {CASE_DESTINATION}: "
        "RELATIVE TO FASTEST ROUTE"
    )
    print("=" * 90)


    print(
        case_comparison.to_string(
            index=False
        )
    )


    # =========================================================
    # FINISH
    # =========================================================

    print()
    print("=" * 90)
    print("CHAPTER 5 FIGURES 5-7 TO 5-9 CREATED")
    print("=" * 90)


    print(
        "Figure 5-7 : "
        "Donghu -> Zhongyuan route schematic"
    )


    print(
        "Figure 5-8 : "
        "Donghu -> Zhongyuan Pareto trade-off"
    )


    print(
        "Figure 5-9 : "
        "Network-wide practical trade-off"
    )


    print()
    print(
        f"Figures saved to:\n"
        f"{FIGURE_DIR}"
    )


    print()
    print(
        f"Figure 5-9 data saved to:\n"
        f"{FIGURE_59_DATA}"
    )