from src.paths import PROJECT_ROOT, RESULTS_DIR as CANONICAL_RESULTS_DIR, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, result_path, project_path
import os
import numpy as np
import pandas as pd

if __name__ == "__main__":







    # ============================================================
    # Experiment 2A Analysis
    # Effect of Pairwise Objective Correlation on MOSP
    # ============================================================

    INPUT_FILE = result_path('experiment_02a_correlation_raw.csv')

    CHECK_FILE = result_path('experiment_02a_correlation_check.csv')


    # ============================================================
    # 1. Load data
    # ============================================================

    df = pd.read_csv(INPUT_FILE)
    check_df = pd.read_csv(CHECK_FILE)


    print("===== EXPERIMENT 2A DATA CHECK =====")

    print(
        "Total observations:",
        len(df)
    )

    print(
        "Expected observations:",
        2500
    )

    assert len(df) == 2500

    print()


    # ============================================================
    # 2. Check observations per rho
    # ============================================================

    print(
        "Observations per correlation condition:"
    )

    counts = (
        df.groupby("target_rho")
        .size()
    )

    print(counts)
    print()

    # 50 networks × 10 OD pairs = 500 observations
    assert all(counts == 500)


    # ============================================================
    # 3. Derived metrics
    # ============================================================

    # ------------------------------------------------------------
    # Comparisons per generated label
    #
    # IMPORTANT:
    # Calculate the ratio for EACH case first.
    # Then calculate the group mean.
    # ------------------------------------------------------------

    df["comparisons_per_generated_label"] = np.where(
        df["generated_labels"] > 0,
        df["dominance_checks"]
        / df["generated_labels"],
        0.0
    )


    # ============================================================
    # 4. Manipulation check
    # ============================================================

    print(
        "===== CORRELATION MANIPULATION CHECK ====="
    )

    correlation_summary = (
        check_df
        .groupby("target_rho")["observed_rho"]
        .agg(
            mean="mean",
            std="std",
            min="min",
            max="max"
        )
    )

    print(
        correlation_summary.round(4)
    )

    print()


    # ============================================================
    # 5. Helper function
    # Mean + SD + SE + 95% CI
    # ============================================================

    def metric_summary(
        dataframe,
        metric
    ):

        summary = (
            dataframe
            .groupby("target_rho")[metric]
            .agg(
                mean="mean",
                std="std",
                count="count"
            )
        )

        summary["se"] = (
            summary["std"]
            / np.sqrt(
                summary["count"]
            )
        )

        summary["ci95"] = (
            1.96
            * summary["se"]
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

        "runtime_seconds":
            "Runtime",

        "immediate_rejection_rate":
            "Immediate Rejection Rate",

        "max_labels_per_node":
            "Max Labels Per Node"
    }


    # ============================================================
    # 7. Detailed summaries
    # ============================================================

    print(
        "===== DETAILED METRIC SUMMARIES ====="
    )

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
                    "std",
                    "ci95"
                ]
            ].round(6)
        )


    # ============================================================
    # 8. Compact summary
    # ============================================================

    compact = pd.DataFrame({

        "observed_rho":
            correlation_summary["mean"],

        "pareto_labels":
            summaries[
                "target_pareto_labels"
            ]["mean"],

        "generated":
            summaries[
                "generated_labels"
            ]["mean"],

        "dominance_checks":
            summaries[
                "dominance_checks"
            ]["mean"],

        "comparisons_per_generated_label":
            summaries[
                "comparisons_per_generated_label"
            ]["mean"],

        "runtime":
            summaries[
                "runtime_seconds"
            ]["mean"],

        "rejection_rate":
            summaries[
                "immediate_rejection_rate"
            ]["mean"],

        "max_labels_per_node":
            summaries[
                "max_labels_per_node"
            ]["mean"]
    })


    print()
    print(
        "===== COMPACT SUMMARY ====="
    )

    print(
        compact.round(6)
    )


    # ============================================================
    # 9. Compare each condition with rho = 0 baseline
    # ============================================================

    print()
    print(
        "===== RELATIVE TO rho = 0 BASELINE ====="
    )

    baseline_rho = 0.0

    baseline = compact.loc[
        baseline_rho
    ]


    ratio_columns = [
        "pareto_labels",
        "generated",
        "dominance_checks",
        "comparisons_per_generated_label",
        "runtime",
        "max_labels_per_node"
    ]


    ratio_table = pd.DataFrame(
        index=compact.index
    )


    for column in ratio_columns:

        ratio_table[column] = (
            compact[column]
            / baseline[column]
        )


    print(
        ratio_table.round(3)
    )


    # ============================================================
    # 10. Extreme comparison
    # rho = -0.8 versus rho = +0.8
    # ============================================================

    print()
    print(
        "===== EXTREME CONDITION COMPARISON ====="
    )

    negative = compact.loc[
        -0.8
    ]

    positive = compact.loc[
        0.8
    ]


    for column in ratio_columns:

        ratio = (
            negative[column]
            / positive[column]
        )

        print(
            f"{column}: "
            f"rho=-0.8 is "
            f"{ratio:.3f}x "
            f"rho=+0.8"
        )


    # ============================================================
    # 11. Workload-runtime correlations
    # ============================================================

    print()
    print(
        "===== WORKLOAD-RUNTIME CORRELATIONS ====="
    )


    workload_metrics = [
        "target_pareto_labels",
        "generated_labels",
        "dominance_checks",
        "comparisons_per_generated_label",
        "max_labels_per_node"
    ]


    for metric in workload_metrics:

        r = df[
            [
                metric,
                "runtime_seconds"
            ]
        ].corr(
            method="pearson"
        ).iloc[0, 1]

        print(
            f"{metric} vs runtime: "
            f"r = {r:.4f}"
        )


    # ============================================================
    # 12. Dominance checks vs runtime by rho
    # ============================================================

    print()
    print(
        "===== DOMINANCE CHECKS VS RUNTIME BY RHO ====="
    )

    for rho, group in df.groupby(
        "target_rho"
    ):

        r = group[
            [
                "dominance_checks",
                "runtime_seconds"
            ]
        ].corr(
            method="pearson"
        ).iloc[0, 1]

        print(
            f"rho={rho:+.1f}: "
            f"r = {r:.4f}"
        )


    # ============================================================
    # 13. Check monotonic trend
    # ============================================================

    print()
    print(
        "===== MONOTONIC TREND CHECK ====="
    )


    def check_monotonic_decrease(
        values
    ):

        values = list(values)

        return all(
            values[i] >= values[i + 1]
            for i in range(
                len(values) - 1
            )
        )


    for column in [
        "pareto_labels",
        "generated",
        "dominance_checks",
        "comparisons_per_generated_label",
        "runtime",
        "max_labels_per_node"
    ]:

        is_decreasing = (
            check_monotonic_decrease(
                compact[column]
            )
        )

        print(
            f"{column}: "
            f"monotonically decreases "
            f"as rho increases? "
            f"{is_decreasing}"
        )


    # ============================================================
    # 14. Exp 1 baseline sanity check
    #
    # Exp 1 m = 2 corresponds approximately to
    # the independent / rho = 0 condition.
    # ============================================================

    print()
    print(
        "===== EXP 1 BASELINE SANITY CHECK ====="
    )


    EXP1_M2 = {

        "pareto_labels":
            4.646,

        "generated":
            3685.764,

        "dominance_checks":
            8666.956,

        "comparisons_per_generated_label":
            2.312544,

        "runtime":
            0.020817,

        "max_labels_per_node":
            11.590
    }


    exp2_zero = compact.loc[
        0.0
    ]


    for metric in [
        "pareto_labels",
        "generated",
        "dominance_checks",
        "comparisons_per_generated_label",
        "runtime",
        "max_labels_per_node"
    ]:

        exp1_value = (
            EXP1_M2[metric]
        )

        exp2_value = (
            exp2_zero[metric]
        )

        difference_percent = (
            (
                exp2_value
                - exp1_value
            )
            / exp1_value
            * 100
        )

        print(
            f"{metric}:"
        )

        print(
            f"  Exp 1 m=2      = "
            f"{exp1_value:.6f}"
        )

        print(
            f"  Exp 2A rho=0   = "
            f"{exp2_value:.6f}"
        )

        print(
            f"  Difference     = "
            f"{difference_percent:+.2f}%"
        )


    # ============================================================
    # 15. Save summary CSV
    # ============================================================

    OUTPUT_FILE = result_path('experiment_02a_summary.csv')


    compact.to_csv(
        OUTPUT_FILE
    )


    print()
    print(
        "Summary saved to:",
        OUTPUT_FILE
    )


    # ============================================================
    # Done
    # ============================================================

    print()
    print(
        "Experiment 2A analysis completed successfully."
    )