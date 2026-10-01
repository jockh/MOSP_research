from src.paths import PROJECT_ROOT, RESULTS_DIR as CANONICAL_RESULTS_DIR, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, result_path, project_path
import os
import numpy as np
import pandas as pd

if __name__ == "__main__":







    # ============================================================
    # Experiment 3A Analysis
    # Effect of Route Quantity on MOSP Search Workload
    # ============================================================

    INPUT_FILE = result_path('experiment_03a_route_quantity_raw.csv')

    OUTPUT_FILE = result_path('experiment_03a_route_quantity_summary.csv')


    # ============================================================
    # 1. Load data
    # ============================================================

    df = pd.read_csv(INPUT_FILE)


    print("=" * 60)
    print("EXPERIMENT 3A DATA CHECK")
    print("=" * 60)

    print("Total observations:", len(df))

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nMissing values:")
    print(df.isna().sum())

    print()


    # ============================================================
    # 2. Automatically identify route-quantity variable
    # ============================================================

    possible_route_columns = [
        "route_quantity",
        "num_routes",
        "route_count",
        "distinct_route_count",
        "num_alternative_routes",
        "alternative_count"
    ]

    route_column = None

    for column in possible_route_columns:

        if column in df.columns:

            route_column = column
            break


    if route_column is None:

        raise ValueError(
            "Cannot find route quantity column.\n"
            "Available columns are:\n"
            f"{df.columns.tolist()}"
        )


    print(
        "Route quantity variable:",
        route_column
    )

    print(
        "Route quantity levels:",
        sorted(
            df[route_column]
            .dropna()
            .unique()
        )
    )

    print()


    # ============================================================
    # 3. Observations per route-quantity condition
    # ============================================================

    print("=" * 60)
    print("OBSERVATIONS PER ROUTE-QUANTITY CONDITION")
    print("=" * 60)

    counts = (
        df
        .groupby(route_column)
        .size()
    )

    print(counts)

    print()


    # ============================================================
    # 4. Additional metrics
    # ============================================================

    # ------------------------------------------------------------
    # Comparisons per generated label
    # ------------------------------------------------------------

    df[
        "comparisons_per_generated_label"
    ] = np.where(
        df["generated_labels"] > 0,

        df["dominance_checks"]
        /
        df["generated_labels"],

        np.nan
    )


    # ------------------------------------------------------------
    # Pruning rate
    # ------------------------------------------------------------

    if (
        "pruned_labels" in df.columns
        and
        "generated_labels" in df.columns
    ):

        df["pruning_rate"] = np.where(
            df["generated_labels"] > 0,

            df["pruned_labels"]
            /
            df["generated_labels"],

            np.nan
        )


    # ============================================================
    # 5. Summary function
    # ============================================================

    def metric_summary(metric):

        summary = (
            df
            .groupby(route_column)[metric]
            .agg(
                mean="mean",
                median="median",
                std="std",
                count="count"
            )
        )

        summary["se"] = (
            summary["std"]
            /
            np.sqrt(
                summary["count"]
            )
        )

        summary["ci95"] = (
            1.96
            *
            summary["se"]
        )

        return summary


    # ============================================================
    # 6. Metrics
    # ============================================================

    metrics = {

        "target_pareto_labels":
            "Pareto Labels",

        "generated_labels":
            "Generated Labels",

        "dominance_checks":
            "Dominance Checks",

        "comparisons_per_generated_label":
            "Comparisons Per Generated Label",

        "max_labels_per_node":
            "Max Labels Per Node",

        "runtime_seconds":
            "Runtime"
    }


    # Add optional metrics if available

    if "pruning_rate" in df.columns:

        metrics[
            "pruning_rate"
        ] = "Pruning Rate"


    if "immediate_rejection_rate" in df.columns:

        metrics[
            "immediate_rejection_rate"
        ] = "Immediate Rejection Rate"


    # ============================================================
    # 7. Detailed summaries
    # ============================================================

    print("=" * 60)
    print("DETAILED METRIC SUMMARIES")
    print("=" * 60)


    summaries = {}


    for metric, label in metrics.items():

        if metric not in df.columns:

            print(
                f"\nSkipping {metric}: "
                f"column not found."
            )

            continue


        summary = metric_summary(
            metric
        )

        summaries[
            metric
        ] = summary


        print()
        print(
            f"--- {label} ---"
        )

        print(
            summary[
                [
                    "mean",
                    "median",
                    "std",
                    "ci95"
                ]
            ].round(6)
        )


    # ============================================================
    # 8. Compact summary
    # ============================================================

    compact_data = {}


    for metric in [
        "target_pareto_labels",
        "generated_labels",
        "dominance_checks",
        "comparisons_per_generated_label",
        "max_labels_per_node",
        "runtime_seconds"
    ]:

        if metric in summaries:

            compact_data[
                metric
            ] = summaries[
                metric
            ]["mean"]


    if "pruning_rate" in summaries:

        compact_data[
            "pruning_rate"
        ] = summaries[
            "pruning_rate"
        ]["mean"]


    if "immediate_rejection_rate" in summaries:

        compact_data[
            "immediate_rejection_rate"
        ] = summaries[
            "immediate_rejection_rate"
        ]["mean"]


    compact = pd.DataFrame(
        compact_data
    )


    print()
    print("=" * 60)
    print("COMPACT SUMMARY")
    print("=" * 60)

    print(
        compact.round(6)
    )


    # ============================================================
    # 9. Relative to smallest route quantity
    # ============================================================

    route_levels = sorted(
        compact.index
    )


    lowest_level = route_levels[0]

    baseline = compact.loc[
        lowest_level
    ]


    print()
    print("=" * 60)
    print(
        f"RELATIVE TO ROUTE QUANTITY = {lowest_level}"
    )
    print("=" * 60)


    ratio_columns = [

        "target_pareto_labels",

        "generated_labels",

        "dominance_checks",

        "comparisons_per_generated_label",

        "max_labels_per_node",

        "runtime_seconds"
    ]


    ratio_columns = [
        column
        for column in ratio_columns
        if column in compact.columns
    ]


    ratio_table = pd.DataFrame(
        index=compact.index
    )


    for column in ratio_columns:

        ratio_table[
            column
        ] = (
            compact[column]
            /
            baseline[column]
        )


    print(
        ratio_table.round(3)
    )


    # ============================================================
    # 10. Extreme comparison
    # Highest route quantity vs lowest route quantity
    # ============================================================

    highest_level = route_levels[-1]

    lowest = compact.loc[
        lowest_level
    ]

    highest = compact.loc[
        highest_level
    ]


    print()
    print("=" * 60)
    print("EXTREME ROUTE-QUANTITY COMPARISON")
    print("=" * 60)

    print(
        f"Lowest route quantity  = {lowest_level}"
    )

    print(
        f"Highest route quantity = {highest_level}"
    )

    print()


    for column in ratio_columns:

        if lowest[column] == 0:

            print(
                f"{column}: "
                "baseline is zero"
            )

            continue


        ratio = (
            highest[column]
            /
            lowest[column]
        )


        print(
            f"{column}: "
            f"highest is "
            f"{ratio:.3f}x lowest"
        )


    # ============================================================
    # 11. Route quantity vs MOSP outcomes
    #
    # Pearson:
    # linear association
    #
    # Spearman:
    # monotonic association
    # ============================================================

    print()
    print("=" * 60)
    print("ROUTE QUANTITY VS MOSP OUTCOMES")
    print("=" * 60)


    correlation_metrics = [

        "target_pareto_labels",

        "generated_labels",

        "dominance_checks",

        "comparisons_per_generated_label",

        "max_labels_per_node",

        "runtime_seconds"
    ]


    for metric in correlation_metrics:

        if metric not in df.columns:

            continue


        pearson_r = (
            df[
                [
                    route_column,
                    metric
                ]
            ]
            .corr(
                method="pearson"
            )
            .iloc[0, 1]
        )


        spearman_rho = (
            df[
                [
                    route_column,
                    metric
                ]
            ]
            .corr(
                method="spearman"
            )
            .iloc[0, 1]
        )


        print(
            f"{metric:35s} "
            f"Pearson r = {pearson_r: .4f}, "
            f"Spearman rho = {spearman_rho: .4f}"
        )


    # ============================================================
    # 12. Workload vs runtime
    # ============================================================

    print()
    print("=" * 60)
    print("WORKLOAD-RUNTIME CORRELATIONS")
    print("=" * 60)


    workload_metrics = [

        "target_pareto_labels",

        "generated_labels",

        "dominance_checks",

        "comparisons_per_generated_label",

        "max_labels_per_node"
    ]


    for metric in workload_metrics:

        if metric not in df.columns:

            continue


        r = (
            df[
                [
                    metric,
                    "runtime_seconds"
                ]
            ]
            .corr(
                method="pearson"
            )
            .iloc[0, 1]
        )


        print(
            f"{metric:35s} "
            f"vs runtime: "
            f"r = {r:.4f}"
        )


    # ============================================================
    # 13. Dominance checks vs runtime
    #     within each route-quantity condition
    # ============================================================

    print()
    print("=" * 60)
    print(
        "DOMINANCE CHECKS VS RUNTIME "
        "BY ROUTE QUANTITY"
    )
    print("=" * 60)


    for level in route_levels:

        subset = df[
            df[route_column] == level
        ]


        if len(subset) < 2:

            continue


        r = (
            subset[
                [
                    "dominance_checks",
                    "runtime_seconds"
                ]
            ]
            .corr(
                method="pearson"
            )
            .iloc[0, 1]
        )


        print(
            f"Route quantity = {level}: "
            f"r = {r:.4f}"
        )


    # ============================================================
    # 14. Workload amplification mechanism
    #
    # This is the important part:
    #
    # dominance checks can grow because:
    #
    # (1) more labels are generated
    # (2) each generated label requires more comparisons
    #
    # approximately:
    #
    # dominance checks
    # ~ generated labels
    # × comparisons per generated label
    #
    # ============================================================

    print()
    print("=" * 60)
    print("WORKLOAD AMPLIFICATION")
    print("=" * 60)


    if (
        lowest[
            "generated_labels"
        ] != 0
        and
        lowest[
            "comparisons_per_generated_label"
        ] != 0
    ):


        generated_ratio = (
            highest[
                "generated_labels"
            ]
            /
            lowest[
                "generated_labels"
            ]
        )


        comparison_ratio = (
            highest[
                "comparisons_per_generated_label"
            ]
            /
            lowest[
                "comparisons_per_generated_label"
            ]
        )


        checks_ratio = (
            highest[
                "dominance_checks"
            ]
            /
            lowest[
                "dominance_checks"
            ]
        )


        runtime_ratio = (
            highest[
                "runtime_seconds"
            ]
            /
            lowest[
                "runtime_seconds"
            ]
        )


        print(
            f"Generated labels: "
            f"{generated_ratio:.3f}x"
        )

        print(
            f"Comparisons per generated label: "
            f"{comparison_ratio:.3f}x"
        )

        print(
            f"Dominance checks: "
            f"{checks_ratio:.3f}x"
        )

        print(
            f"Runtime: "
            f"{runtime_ratio:.3f}x"
        )


        print()

        print(
            "Generated × comparison burden = "
            f"{generated_ratio * comparison_ratio:.3f}x"
        )


    # ============================================================
    # 15. Monotonic trend check
    # ============================================================

    print()
    print("=" * 60)
    print("MONOTONIC TREND CHECK")
    print("=" * 60)


    def check_monotonic_increase(values):

        values = list(values)

        return all(
            values[i]
            <=
            values[i + 1]

            for i in range(
                len(values) - 1
            )
        )


    for column in ratio_columns:

        values = (
            compact[
                column
            ]
            .sort_index()
        )


        result = (
            check_monotonic_increase(
                values
            )
        )


        print(
            f"{column:35s}: "
            f"monotonically increases? "
            f"{result}"
        )


    # ============================================================
    # 16. Percentage change
    # Lowest -> Highest
    # ============================================================

    print()
    print("=" * 60)
    print("LOWEST TO HIGHEST PERCENTAGE CHANGE")
    print("=" * 60)


    for column in ratio_columns:

        low_value = lowest[
            column
        ]

        high_value = highest[
            column
        ]


        if low_value == 0:

            continue


        percentage_change = (
            (
                high_value
                -
                low_value
            )
            /
            low_value
            *
            100
        )


        print(
            f"{column:35s}: "
            f"{percentage_change:+.2f}%"
        )


    # ============================================================
    # 17. Save summary
    # ============================================================

    compact.to_csv(
        OUTPUT_FILE
    )


    print()
    print(
        "Summary saved to:",
        OUTPUT_FILE
    )
    # ============================================================
    # Experimental manipulation check
    # ============================================================

    print()
    print("=" * 60)
    print("EXPERIMENTAL MANIPULATION CHECK")
    print("=" * 60)

    control_variables = [
        "route_length",
        "pairwise_overlap",
        "pairwise_diversity",
        "num_nodes",
        "num_edges",
        "rho_12",
        "rho_13",
        "rho_23"
    ]

    manipulation_check = (
        df
        .groupby("route_count")[control_variables]
        .agg(["mean", "std", "min", "max"])
    )

    print(
        manipulation_check.round(4)
    )


    print()
    print("=" * 60)
    print("MEAN CONTROL VARIABLES")
    print("=" * 60)

    mean_controls = (
        df
        .groupby("route_count")[control_variables]
        .mean()
    )

    print(
        mean_controls.round(4)
    )
    # ============================================================
    # Network-size normalized workload
    # ============================================================

    df["generated_per_edge"] = (
        df["generated_labels"]
        /
        df["num_edges"]
    )

    df["checks_per_edge"] = (
        df["dominance_checks"]
        /
        df["num_edges"]
    )

    df["runtime_per_edge"] = (
        df["runtime_seconds"]
        /
        df["num_edges"]
    )


    normalized_summary = (
        df
        .groupby("route_count")
        .agg(
            nodes=("num_nodes", "mean"),
            edges=("num_edges", "mean"),

            generated=(
                "generated_labels",
                "mean"
            ),

            generated_per_edge=(
                "generated_per_edge",
                "mean"
            ),

            checks_per_generated=(
                "comparisons_per_generated_label",
                "mean"
            ),

            dominance_checks=(
                "dominance_checks",
                "mean"
            ),

            checks_per_edge=(
                "checks_per_edge",
                "mean"
            ),

            runtime=(
                "runtime_seconds",
                "mean"
            ),

            runtime_per_edge=(
                "runtime_per_edge",
                "mean"
            )
        )
    )


    print()
    print("=" * 60)
    print("NETWORK-SIZE NORMALIZED WORKLOAD")
    print("=" * 60)

    print(
        normalized_summary.round(6)
    )


    # ============================================================
    # Extreme normalized comparison
    # ============================================================

    low = normalized_summary.loc[2]
    high = normalized_summary.loc[16]


    print()
    print("=" * 60)
    print("K = 16 VS K = 2 — NORMALIZED")
    print("=" * 60)


    for metric in [
        "edges",
        "generated",
        "generated_per_edge",
        "checks_per_generated",
        "dominance_checks",
        "checks_per_edge",
        "runtime",
        "runtime_per_edge"
    ]:

        ratio = (
            high[metric]
            /
            low[metric]
        )

        print(
            f"{metric:25s}: "
            f"{ratio:.3f}x"
        )
    # ============================================================
    # Done
    # ============================================================

    print()
    print(
        "Experiment 3A analysis "
        "completed successfully."
    )
