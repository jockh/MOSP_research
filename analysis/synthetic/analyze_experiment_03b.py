from src.paths import PROJECT_ROOT, RESULTS_DIR as CANONICAL_RESULTS_DIR, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, result_path, project_path
import os
import numpy as np
import pandas as pd

if __name__ == "__main__":







    # ============================================================
    # Experiment 3B Analysis
    #
    # Effect of Shared-Path Position on MOSP Search Workload
    #
    # Core comparison:
    #   prefix vs suffix
    #
    # under the same:
    #   - replicate
    #   - route count
    #   - route length
    #   - overlap level
    #   - cost realization
    #   - Pareto solution count
    #
    # ============================================================


    INPUT_FILE = result_path('experiment_03b_overlap_position_raw.csv')

    SUMMARY_FILE = result_path('experiment_03b_overlap_position_analysis.csv')

    PAIRED_FILE = result_path('experiment_03b_overlap_position_paired_analysis.csv')


    # ============================================================
    # 1. Load data
    # ============================================================

    df = pd.read_csv(INPUT_FILE)


    print("=" * 70)
    print("EXPERIMENT 3B DATA CHECK")
    print("=" * 70)

    print("Total observations:", len(df))

    print()

    print("Columns:")
    print(df.columns.tolist())

    print()

    print("Missing values:")
    print(df.isna().sum())


    # ============================================================
    # 2. Basic experimental design check
    # ============================================================

    print()
    print("=" * 70)
    print("EXPERIMENTAL CONDITIONS")
    print("=" * 70)

    print("Objectives:")
    print(sorted(df["objectives"].unique()))

    print()

    print("Structures:")
    print(df["structure"].value_counts())

    print()

    print("Overlap levels:")
    print(sorted(df["pairwise_overlap"].unique()))

    print()

    print("Route counts:")
    print(sorted(df["route_count"].unique()))

    print()

    print("Route lengths:")
    print(sorted(df["route_length"].unique()))


    # ============================================================
    # 3. Observations per condition
    # ============================================================

    print()
    print("=" * 70)
    print("OBSERVATIONS PER CONDITION")
    print("=" * 70)

    condition_counts = (
        df
        .groupby(
            [
                "pairwise_overlap",
                "structure"
            ]
        )
        .size()
        .unstack()
    )

    print(condition_counts)


    # ============================================================
    # 4. Manipulation check
    # ============================================================

    print()
    print("=" * 70)
    print("MANIPULATION CHECK")
    print("=" * 70)


    control_columns = [
        "route_count",
        "route_length",
        "shared_length",
        "unique_length",
        "pairwise_overlap",
        "pairwise_diversity",
        "num_nodes",
        "num_edges",
        "rho_12",
        "rho_13",
        "rho_23"
    ]


    manipulation_summary = (
        df
        .groupby(
            [
                "pairwise_overlap",
                "structure"
            ]
        )[control_columns]
        .mean()
    )

    print(
        manipulation_summary.round(4)
    )


    # ============================================================
    # 5. Check whether prefix and suffix are truly paired
    # ============================================================

    print()
    print("=" * 70)
    print("PAIRED DESIGN CHECK")
    print("=" * 70)


    pair_counts = (
        df
        .groupby(
            [
                "replicate_id",
                "pairwise_overlap"
            ]
        )["structure"]
        .nunique()
    )


    print(
        "Number of replicate-overlap pairs:",
        len(pair_counts)
    )

    print(
        "Pairs containing both prefix and suffix:",
        int((pair_counts == 2).sum())
    )

    assert all(
        pair_counts == 2
    ), (
        "Some replicate-overlap combinations "
        "do not contain both prefix and suffix."
    )


    # ============================================================
    # 6. Check controlled variables within paired cases
    # ============================================================

    print()
    print("=" * 70)
    print("WITHIN-PAIR CONTROL CHECK")
    print("=" * 70)


    pair_control_columns = [

        "route_count",
        "route_length",
        "shared_length",
        "unique_length",

        "pairwise_overlap",
        "pairwise_diversity",

        "num_nodes",
        "num_edges",

        "rho_12",
        "rho_13",
        "rho_23",

        "reference_pareto_labels",
        "target_pareto_labels"
    ]


    control_check = (
        df
        .groupby(
            [
                "replicate_id",
                "pairwise_overlap"
            ]
        )[pair_control_columns]
        .nunique()
    )


    for column in pair_control_columns:

        max_unique = (
            control_check[column]
            .max()
        )

        print(
            f"{column:30s}: "
            f"max unique within pair = "
            f"{max_unique}"
        )


    # ============================================================
    # 7. Strong assertion:
    # prefix/suffix should have same Pareto result
    # ============================================================

    pareto_consistency = (
        control_check[
            "target_pareto_labels"
        ]
        == 1
    )


    print()
    print(
        "Pairs with identical Pareto-label count:",
        f"{pareto_consistency.mean() * 100:.1f}%"
    )


    if pareto_consistency.all():

        print(
            "All prefix/suffix pairs have the same "
            "target Pareto-label count."
        )

    else:

        print(
            "WARNING: Some prefix/suffix pairs "
            "have different Pareto-label counts."
        )


    # ============================================================
    # 8. Helper function:
    # Mean + median + SD + SE + 95% CI
    # ============================================================

    def metric_summary(
        dataframe,
        metric
    ):

        summary = (
            dataframe
            .groupby(
                [
                    "pairwise_overlap",
                    "structure"
                ]
            )[metric]
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
    # 9. Metrics
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

        "pruning_rate":
            "Pruning Rate",

        "runtime_seconds":
            "Runtime"
    }


    # ============================================================
    # 10. Detailed summaries
    # ============================================================

    print()
    print("=" * 70)
    print("DETAILED METRIC SUMMARIES")
    print("=" * 70)


    summaries = {}


    for metric, label in metrics.items():

        summary = metric_summary(
            df,
            metric
        )

        summaries[metric] = summary

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
    # 11. Compact summary table
    # ============================================================

    compact_rows = []


    for overlap in sorted(
        df["pairwise_overlap"].unique()
    ):

        for structure in [
            "prefix",
            "suffix"
        ]:

            subset = df[
                (
                    df["pairwise_overlap"]
                    == overlap
                )
                &
                (
                    df["structure"]
                    == structure
                )
            ]

            compact_rows.append({

                "pairwise_overlap":
                    overlap,

                "structure":
                    structure,

                "pareto_labels":
                    subset[
                        "target_pareto_labels"
                    ].mean(),

                "generated_labels":
                    subset[
                        "generated_labels"
                    ].mean(),

                "dominance_checks":
                    subset[
                        "dominance_checks"
                    ].mean(),

                "comparisons_per_generated_label":
                    subset[
                        "comparisons_per_generated_label"
                    ].mean(),

                "max_labels_per_node":
                    subset[
                        "max_labels_per_node"
                    ].mean(),

                "pruning_rate":
                    subset[
                        "pruning_rate"
                    ].mean(),

                "runtime_seconds":
                    subset[
                        "runtime_seconds"
                    ].mean()
            })


    compact = pd.DataFrame(
        compact_rows
    )


    print()
    print("=" * 70)
    print("COMPACT SUMMARY")
    print("=" * 70)

    print(
        compact.round(6).to_string(
            index=False
        )
    )


    # ============================================================
    # 12. Build paired prefix-suffix dataset
    # ============================================================

    paired_metrics = [

        "target_pareto_labels",

        "generated_labels",

        "dominance_checks",

        "comparisons_per_generated_label",

        "max_labels_per_node",

        "pruning_rate",

        "runtime_seconds"
    ]


    wide = (
        df[
            [
                "replicate_id",
                "pairwise_overlap",
                "structure"
            ]
            +
            paired_metrics
        ]
        .pivot(
            index=[
                "replicate_id",
                "pairwise_overlap"
            ],
            columns="structure",
            values=paired_metrics
        )
    )


    # Flatten MultiIndex columns

    wide.columns = [

        f"{metric}_{structure}"

        for metric, structure
        in wide.columns
    ]


    wide = wide.reset_index()


    # ============================================================
    # 13. Calculate paired differences
    #
    # difference = suffix - prefix
    #
    # Positive:
    # suffix requires more work
    #
    # Negative:
    # prefix requires more work
    # ============================================================

    for metric in paired_metrics:

        wide[
            f"{metric}_difference"
        ] = (

            wide[
                f"{metric}_suffix"
            ]

            -

            wide[
                f"{metric}_prefix"
            ]
        )


    # ============================================================
    # 14. Helper:
    # paired comparison
    # ============================================================

    def paired_analysis(
        dataframe,
        metric
    ):

        prefix = dataframe[
            f"{metric}_prefix"
        ]

        suffix = dataframe[
            f"{metric}_suffix"
        ]

        difference = (
            suffix
            -
            prefix
        )

        n = len(
            difference
        )

        mean_difference = (
            difference.mean()
        )

        std_difference = (
            difference.std(
                ddof=1
            )
        )

        se_difference = (
            std_difference
            /
            np.sqrt(n)
        )

        ci = (
            1.96
            *
            se_difference
        )

        prefix_mean = (
            prefix.mean()
        )

        suffix_mean = (
            suffix.mean()
        )

        if prefix_mean != 0:

            ratio = (
                suffix_mean
                /
                prefix_mean
            )

        else:

            ratio = np.nan

        suffix_greater = (
            difference > 0
        ).mean()

        equal = (
            difference == 0
        ).mean()

        suffix_lower = (
            difference < 0
        ).mean()

        return {

            "n":
                n,

            "prefix_mean":
                prefix_mean,

            "suffix_mean":
                suffix_mean,

            "mean_difference":
                mean_difference,

            "ci_lower":
                mean_difference - ci,

            "ci_upper":
                mean_difference + ci,

            "suffix_prefix_ratio":
                ratio,

            "suffix_greater_pct":
                suffix_greater * 100,

            "equal_pct":
                equal * 100,

            "suffix_lower_pct":
                suffix_lower * 100
        }


    # ============================================================
    # 15. Paired analysis by overlap level
    # ============================================================

    print()
    print("=" * 70)
    print("PREFIX VS SUFFIX — PAIRED ANALYSIS")
    print("=" * 70)


    paired_summary_rows = []


    for overlap in sorted(
        wide["pairwise_overlap"].unique()
    ):

        print()
        print(
            "#" * 70
        )

        print(
            f"PAIRWISE OVERLAP = {overlap:.2f}"
        )

        print(
            "#" * 70
        )

        subset = wide[
            wide[
                "pairwise_overlap"
            ]
            == overlap
        ]

        for metric in paired_metrics:

            result = paired_analysis(
                subset,
                metric
            )

            paired_summary_rows.append({

                "pairwise_overlap":
                    overlap,

                "metric":
                    metric,

                **result
            })

            print()
            print(metric)

            print(
                f"  Prefix mean       = "
                f"{result['prefix_mean']:.6f}"
            )

            print(
                f"  Suffix mean       = "
                f"{result['suffix_mean']:.6f}"
            )

            print(
                f"  Difference        = "
                f"{result['mean_difference']:+.6f}"
            )

            print(
                f"  95% CI difference = "
                f"["
                f"{result['ci_lower']:.6f}, "
                f"{result['ci_upper']:.6f}"
                f"]"
            )

            print(
                f"  Suffix / Prefix   = "
                f"{result['suffix_prefix_ratio']:.3f}x"
            )

            print(
                f"  Suffix > Prefix   = "
                f"{result['suffix_greater_pct']:.1f}%"
            )

            print(
                f"  Suffix = Prefix   = "
                f"{result['equal_pct']:.1f}%"
            )

            print(
                f"  Suffix < Prefix   = "
                f"{result['suffix_lower_pct']:.1f}%"
            )


    paired_summary = pd.DataFrame(
        paired_summary_rows
    )


    # ============================================================
    # 16. Overall prefix vs suffix comparison
    # ============================================================

    print()
    print("=" * 70)
    print("OVERALL PREFIX VS SUFFIX")
    print("=" * 70)


    for metric in paired_metrics:

        result = paired_analysis(
            wide,
            metric
        )

        print()
        print(metric)

        print(
            f"  Prefix mean       = "
            f"{result['prefix_mean']:.6f}"
        )

        print(
            f"  Suffix mean       = "
            f"{result['suffix_mean']:.6f}"
        )

        print(
            f"  Mean difference   = "
            f"{result['mean_difference']:+.6f}"
        )

        print(
            f"  Suffix / Prefix   = "
            f"{result['suffix_prefix_ratio']:.3f}x"
        )


    # ============================================================
    # 17. Search-workload amplification
    #
    # dominance checks approximately depend on:
    #
    # number of generated labels
    # ×
    # comparisons required per generated label
    #
    # ============================================================

    print()
    print("=" * 70)
    print("SEARCH-WORKLOAD AMPLIFICATION")
    print("=" * 70)


    for overlap in sorted(
        df["pairwise_overlap"].unique()
    ):

        subset = compact[
            compact[
                "pairwise_overlap"
            ]
            == overlap
        ].set_index(
            "structure"
        )

        generated_ratio = (

            subset.loc[
                "suffix",
                "generated_labels"
            ]

            /

            subset.loc[
                "prefix",
                "generated_labels"
            ]
        )

        comparison_ratio = (

            subset.loc[
                "suffix",
                "comparisons_per_generated_label"
            ]

            /

            subset.loc[
                "prefix",
                "comparisons_per_generated_label"
            ]
        )

        checks_ratio = (

            subset.loc[
                "suffix",
                "dominance_checks"
            ]

            /

            subset.loc[
                "prefix",
                "dominance_checks"
            ]
        )

        runtime_ratio = (

            subset.loc[
                "suffix",
                "runtime_seconds"
            ]

            /

            subset.loc[
                "prefix",
                "runtime_seconds"
            ]
        )

        print()
        print(
            f"Overlap = {overlap:.2f}"
        )

        print(
            f"  Generated labels ratio      = "
            f"{generated_ratio:.3f}x"
        )

        print(
            f"  Comparison burden ratio     = "
            f"{comparison_ratio:.3f}x"
        )

        print(
            f"  Product                     = "
            f"{generated_ratio * comparison_ratio:.3f}x"
        )

        print(
            f"  Dominance checks ratio      = "
            f"{checks_ratio:.3f}x"
        )

        print(
            f"  Runtime ratio               = "
            f"{runtime_ratio:.3f}x"
        )


    # ============================================================
    # 18. Dominance checks vs runtime
    # ============================================================

    print()
    print("=" * 70)
    print("DOMINANCE CHECKS VS RUNTIME")
    print("=" * 70)


    overall_r = (

        df[
            [
                "dominance_checks",
                "runtime_seconds"
            ]
        ]
        .corr(
            method="pearson"
        )
        .iloc[
            0,
            1
        ]
    )


    print(
        f"Overall Pearson r = "
        f"{overall_r:.4f}"
    )


    for overlap in sorted(
        df["pairwise_overlap"].unique()
    ):

        for structure in [
            "prefix",
            "suffix"
        ]:

            subset = df[
                (
                    df[
                        "pairwise_overlap"
                    ]
                    == overlap
                )
                &
                (
                    df[
                        "structure"
                    ]
                    == structure
                )
            ]

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
                .iloc[
                    0,
                    1
                ]
            )

            print(
                f"Overlap={overlap:.2f}, "
                f"{structure:6s}: "
                f"r = {r:.4f}"
            )


    # ============================================================
    # 19. Check effect on final Pareto solution
    # ============================================================

    print()
    print("=" * 70)
    print("PARETO SOLUTION INVARIANCE CHECK")
    print("=" * 70)


    pareto_diff = (

        wide[
            "target_pareto_labels_suffix"
        ]

        -

        wide[
            "target_pareto_labels_prefix"
        ]
    )


    print(
        "Mean Pareto-label difference:",
        pareto_diff.mean()
    )

    print(
        "Maximum absolute difference:",
        pareto_diff.abs().max()
    )

    print(
        "Identical Pareto-label count:",
        f"{(pareto_diff == 0).mean() * 100:.1f}%"
    )


    # ============================================================
    # 20. Overlap-level descriptive trend
    #
    # IMPORTANT:
    #
    # num_nodes and num_edges change when overlap changes.
    # Therefore this section is descriptive only.
    #
    # It should NOT be interpreted as a pure causal effect
    # of overlap.
    # ============================================================

    print()
    print("=" * 70)
    print("DESCRIPTIVE TREND ACROSS OVERLAP LEVELS")
    print("=" * 70)

    print(
        "NOTE:"
    )

    print(
        "Network size changes with overlap level, "
        "so cross-overlap comparisons are descriptive "
        "rather than a pure overlap effect."
    )


    for structure in [
        "prefix",
        "suffix"
    ]:

        print()
        print(
            f"--- {structure.upper()} ---"
        )

        subset = (
            compact[
                compact[
                    "structure"
                ]
                == structure
            ]
            .sort_values(
                "pairwise_overlap"
            )
        )

        print(
            subset[
                [
                    "pairwise_overlap",
                    "generated_labels",
                    "dominance_checks",
                    "comparisons_per_generated_label",
                    "runtime_seconds"
                ]
            ]
            .round(6)
            .to_string(
                index=False
            )
        )


    # ============================================================
    # 21. Key result table:
    # suffix relative to prefix
    # ============================================================

    print()
    print("=" * 70)
    print("SUFFIX RELATIVE TO PREFIX")
    print("=" * 70)


    relative_rows = []


    for overlap in sorted(
        df[
            "pairwise_overlap"
        ].unique()
    ):

        subset = compact[
            compact[
                "pairwise_overlap"
            ]
            == overlap
        ].set_index(
            "structure"
        )

        row = {
            "pairwise_overlap":
                overlap
        }

        for metric in [

            "pareto_labels",

            "generated_labels",

            "dominance_checks",

            "comparisons_per_generated_label",

            "max_labels_per_node",

            "runtime_seconds"
        ]:

            row[
                f"{metric}_suffix_prefix"
            ] = (

                subset.loc[
                    "suffix",
                    metric
                ]

                /

                subset.loc[
                    "prefix",
                    metric
                ]
            )

        relative_rows.append(
            row
        )


    relative_table = pd.DataFrame(
        relative_rows
    )


    print(
        relative_table
        .round(3)
        .to_string(
            index=False
        )
    )


    # ============================================================
    # 22. Save results
    # ============================================================

    compact.to_csv(
        SUMMARY_FILE,
        index=False
    )


    paired_summary.to_csv(
        PAIRED_FILE,
        index=False
    )


    print()
    print("=" * 70)
    print("FILES SAVED")
    print("=" * 70)

    print(
        "Summary saved to:"
    )

    print(
        SUMMARY_FILE
    )

    print()

    print(
        "Paired analysis saved to:"
    )

    print(
        PAIRED_FILE
    )


    # ============================================================
    # Done
    # ============================================================

    print()
    print(
        "Experiment 3B analysis completed successfully."
    )