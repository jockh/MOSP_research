import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.stats import pearsonr, spearmanr

import statsmodels.api as sm


# ============================================================
# Paths
# ============================================================

SCRIPT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

EXP03_DIR = os.path.join(
    SCRIPT_DIR,
    "results",
    "experiment_03"
)

os.makedirs(
    EXP03_DIR,
    exist_ok=True
)


INPUT_FILE = os.path.join(
    SCRIPT_DIR,
    "results",
    "experiment_03_route_diversity_raw.csv"
)


# ============================================================
# Load data
# ============================================================

df = pd.read_csv(
    INPUT_FILE
)


# ============================================================
# Metrics
# ============================================================

ROUTE_METRICS = [
    "distinct_route_count",
    "distinct_alternative_count",
    "mean_pairwise_diversity",
    "shortest_hops"
]

WORKLOAD_METRICS = [
    "target_pareto_labels",
    "generated_labels",
    "dominance_checks",
    "runtime_seconds",
    "max_labels_per_node"
]


# ============================================================
# 1. Data check
# ============================================================

print()
print(
    "=========================================="
)
print(
    "EXPERIMENT 3 DATA CHECK"
)
print(
    "=========================================="
)
print()

print(
    "Total observations:",
    len(df)
)

print(
    "Networks:",
    df[
        "network_id"
    ].nunique()
)

print(
    "Unique edge counts:",
    sorted(
        df[
            "num_edges"
        ].unique()
    )
)

print(
    "Missing values:",
    int(
        df.isna().sum().sum()
    )
)

print()

print(
    "Route-count ceiling cases:",
    int(
        df[
            "route_count_ceiling"
        ].sum()
    )
)

print(
    "Candidate-search ceiling cases:",
    int(
        df[
            "candidate_ceiling"
        ].sum()
    )
)


# ============================================================
# 2. Descriptive statistics
# ============================================================

print()
print(
    "=========================================="
)
print(
    "DESCRIPTIVE STATISTICS"
)
print(
    "=========================================="
)


summary_columns = (
    ROUTE_METRICS
    + WORKLOAD_METRICS
)

summary = (
    df[
        summary_columns
    ]
    .agg([
        "mean",
        "std",
        "min",
        "median",
        "max"
    ])
    .T
)

print()
print(
    summary.round(
        4
    )
)


# ============================================================
# 3. Correlations
# ============================================================

print()
print(
    "=========================================="
)
print(
    "ROUTE DIVERSITY VS MOSP WORKLOAD"
)
print(
    "=========================================="
)


correlation_rows = []


for predictor in [
    "distinct_route_count",
    "distinct_alternative_count",
    "mean_pairwise_diversity",
    "shortest_hops"
]:

    print()
    print(
        f"--- Predictor: "
        f"{predictor} ---"
    )

    for outcome in WORKLOAD_METRICS:

        x = df[
            predictor
        ]

        y = df[
            outcome
        ]

        pearson_r, pearson_p = (
            pearsonr(
                x,
                y
            )
        )

        spearman_rho, spearman_p = (
            spearmanr(
                x,
                y
            )
        )

        correlation_rows.append({

            "predictor":
                predictor,

            "outcome":
                outcome,

            "pearson_r":
                pearson_r,

            "pearson_p":
                pearson_p,

            "spearman_rho":
                spearman_rho,

            "spearman_p":
                spearman_p
        })

        print(
            f"{outcome:25s} "
            f"Pearson r = "
            f"{pearson_r: .4f}, "
            f"Spearman rho = "
            f"{spearman_rho: .4f}"
        )


correlation_df = pd.DataFrame(
    correlation_rows
)


# ============================================================
# 4. Predictor correlations
# ============================================================

print()
print(
    "=========================================="
)
print(
    "PREDICTOR CORRELATIONS"
)
print(
    "=========================================="
)


predictor_corr = (
    df[
        [
            "distinct_route_count",
            "mean_pairwise_diversity",
            "shortest_hops"
        ]
    ]
    .corr(
        method="spearman"
    )
)

print()
print(
    predictor_corr.round(
        4
    )
)


# ============================================================
# 5. Prepare variables
# ============================================================

analysis_df = df.copy()


def zscore(series):

    std = series.std(
        ddof=1
    )

    if std == 0:

        return series * 0

    return (
        series
        - series.mean()
    ) / std


analysis_df[
    "z_distinct_routes"
] = zscore(
    analysis_df[
        "distinct_route_count"
    ]
)

analysis_df[
    "z_mean_diversity"
] = zscore(
    analysis_df[
        "mean_pairwise_diversity"
    ]
)

analysis_df[
    "z_shortest_hops"
] = zscore(
    analysis_df[
        "shortest_hops"
    ]
)


# ------------------------------------------------------------
# Outcome transformations
# ------------------------------------------------------------

analysis_df[
    "log_pareto"
] = np.log1p(
    analysis_df[
        "target_pareto_labels"
    ]
)

analysis_df[
    "log_generated"
] = np.log1p(
    analysis_df[
        "generated_labels"
    ]
)

analysis_df[
    "log_checks"
] = np.log1p(
    analysis_df[
        "dominance_checks"
    ]
)

analysis_df[
    "log_runtime"
] = np.log(
    analysis_df[
        "runtime_seconds"
    ]
)


# ============================================================
# 6. Regression
# ============================================================

print()
print(
    "=========================================="
)
print(
    "REGRESSION ANALYSIS"
)
print(
    "=========================================="
)


REGRESSION_OUTCOMES = {

    "log_pareto":
        "log(1 + Pareto Labels)",

    "log_generated":
        "log(1 + Generated Labels)",

    "log_checks":
        "log(1 + Dominance Checks)",

    "log_runtime":
        "log(Runtime)"
}


regression_rows = []


for outcome, display_name in (
    REGRESSION_OUTCOMES.items()
):

    print()
    print(
        "------------------------------------------"
    )
    print(
        display_name
    )
    print(
        "------------------------------------------"
    )


    # ========================================================
    # Model A
    # ========================================================

    X_a = analysis_df[
        [
            "z_distinct_routes",
            "z_shortest_hops"
        ]
    ]

    X_a = sm.add_constant(
        X_a
    )

    model_a = sm.OLS(
        analysis_df[
            outcome
        ],
        X_a
    ).fit(
        cov_type="HC3"
    )

    print()
    print(
        "Model A:"
    )

    print(
        "Route count + shortest hops"
    )

    print()

    print(
        model_a.summary()
    )


    for variable in [
        "z_distinct_routes",
        "z_shortest_hops"
    ]:

        conf_int = (
            model_a.conf_int()
        )

        regression_rows.append({

            "outcome":
                outcome,

            "model":
                "route_count_control_hops",

            "variable":
                variable,

            "coef":
                model_a.params[
                    variable
                ],

            "std_error":
                model_a.bse[
                    variable
                ],

            "p_value":
                model_a.pvalues[
                    variable
                ],

            "ci_lower":
                conf_int.loc[
                    variable,
                    0
                ],

            "ci_upper":
                conf_int.loc[
                    variable,
                    1
                ],

            "r_squared":
                model_a.rsquared,

            "adj_r_squared":
                model_a.rsquared_adj
        })


    # ========================================================
    # Model B
    # ========================================================

    X_b = analysis_df[
        [
            "z_distinct_routes",
            "z_mean_diversity",
            "z_shortest_hops"
        ]
    ]

    X_b = sm.add_constant(
        X_b
    )

    model_b = sm.OLS(
        analysis_df[
            outcome
        ],
        X_b
    ).fit(
        cov_type="HC3"
    )

    print()
    print(
        "Model B:"
    )

    print(
        "Route count + mean diversity "
        "+ shortest hops"
    )

    print()

    print(
        model_b.summary()
    )


    for variable in [
        "z_distinct_routes",
        "z_mean_diversity",
        "z_shortest_hops"
    ]:

        conf_int = (
            model_b.conf_int()
        )

        regression_rows.append({

            "outcome":
                outcome,

            "model":
                "route_count_diversity_control_hops",

            "variable":
                variable,

            "coef":
                model_b.params[
                    variable
                ],

            "std_error":
                model_b.bse[
                    variable
                ],

            "p_value":
                model_b.pvalues[
                    variable
                ],

            "ci_lower":
                conf_int.loc[
                    variable,
                    0
                ],

            "ci_upper":
                conf_int.loc[
                    variable,
                    1
                ],

            "r_squared":
                model_b.rsquared,

            "adj_r_squared":
                model_b.rsquared_adj
        })


regression_df = pd.DataFrame(
    regression_rows
)


# ============================================================
# 7. Route-count grouped summary
# ============================================================

print()
print(
    "=========================================="
)
print(
    "DISTINCT ROUTE COUNT GROUP SUMMARY"
)
print(
    "=========================================="
)


analysis_df[
    "route_count_group"
] = np.where(
    analysis_df[
        "distinct_route_count"
    ] >= 10,
    "10+",
    analysis_df[
        "distinct_route_count"
    ].astype(str)
)


group_order = [
    str(i)
    for i in range(
        1,
        10
    )
] + [
    "10+"
]


group_summary = (
    analysis_df
    .groupby(
        "route_count_group"
    )
    .agg(

        observations=(
            "distinct_route_count",
            "size"
        ),

        mean_pareto=(
            "target_pareto_labels",
            "mean"
        ),

        mean_generated=(
            "generated_labels",
            "mean"
        ),

        mean_checks=(
            "dominance_checks",
            "mean"
        ),

        mean_runtime=(
            "runtime_seconds",
            "mean"
        ),

        mean_shortest_hops=(
            "shortest_hops",
            "mean"
        ),

        mean_pairwise_diversity=(
            "mean_pairwise_diversity",
            "mean"
        )
    )
    .reindex(
        group_order
    )
    .dropna(
        how="all"
    )
)

print()
print(
    group_summary.round(
        4
    )
)


# ============================================================
# 8. Plot helper
# ============================================================

def scatter_with_trend(
    x_column,
    y_column,
    xlabel,
    ylabel,
    title,
    filename
):

    x = analysis_df[
        x_column
    ].to_numpy(
        dtype=float
    )

    y = analysis_df[
        y_column
    ].to_numpy(
        dtype=float
    )

    fig, ax = plt.subplots(
        figsize=(
            8,
            5.5
        )
    )

    ax.scatter(
        x,
        y,
        alpha=0.35,
        s=28
    )

    slope, intercept = (
        np.polyfit(
            x,
            y,
            1
        )
    )

    x_line = np.linspace(
        x.min(),
        x.max(),
        200
    )

    y_line = (
        slope
        * x_line
        + intercept
    )

    ax.plot(
        x_line,
        y_line,
        linewidth=2
    )

    rho, _ = (
        spearmanr(
            x,
            y
        )
    )

    ax.text(
        0.04,
        0.95,
        (
            f"Spearman ρ = "
            f"{rho:.3f}"
        ),
        transform=
            ax.transAxes,
        verticalalignment=
            "top",
        fontsize=11
    )

    ax.set_xlabel(
        xlabel
    )

    ax.set_ylabel(
        ylabel
    )

    ax.set_title(
        title
    )

    ax.grid(
        alpha=0.3
    )

    plt.tight_layout()

    output_path = os.path.join(
        EXP03_DIR,
        filename
    )

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches=
            "tight"
    )

    plt.close()

    print(
        "Saved:",
        output_path
    )


# ============================================================
# 9. Figures
# ============================================================

scatter_with_trend(

    x_column=
        "distinct_route_count",

    y_column=
        "target_pareto_labels",

    xlabel=
        "Number of Distinct Reasonable Routes",

    ylabel=
        "Pareto Labels at Destination",

    title=
        "Route Diversity vs Pareto Set Size",

    filename=
        "fig_01_route_count_vs_pareto.png"
)


scatter_with_trend(

    x_column=
        "distinct_route_count",

    y_column=
        "generated_labels",

    xlabel=
        "Number of Distinct Reasonable Routes",

    ylabel=
        "Generated Labels",

    title=
        "Route Diversity vs Label Generation",

    filename=
        "fig_02_route_count_vs_generated.png"
)


scatter_with_trend(

    x_column=
        "distinct_route_count",

    y_column=
        "dominance_checks",

    xlabel=
        "Number of Distinct Reasonable Routes",

    ylabel=
        "Dominance Checks",

    title=
        "Route Diversity vs Dominance Workload",

    filename=
        "fig_03_route_count_vs_checks.png"
)


scatter_with_trend(

    x_column=
        "distinct_route_count",

    y_column=
        "runtime_seconds",

    xlabel=
        "Number of Distinct Reasonable Routes",

    ylabel=
        "Runtime (seconds)",

    title=
        "Route Diversity vs Runtime",

    filename=
        "fig_04_route_count_vs_runtime.png"
)


scatter_with_trend(

    x_column=
        "mean_pairwise_diversity",

    y_column=
        "target_pareto_labels",

    xlabel=
        "Mean Pairwise Route Diversity",

    ylabel=
        "Pareto Labels at Destination",

    title=
        "Route Dissimilarity vs Pareto Set Size",

    filename=
        "fig_05_mean_diversity_vs_pareto.png"
)


# ============================================================
# 10. Output files
# ============================================================

SUMMARY_FILE = os.path.join(
    EXP03_DIR,
    "experiment_03_descriptive_summary.csv"
)

CORRELATION_FILE = os.path.join(
    EXP03_DIR,
    "experiment_03_correlations.csv"
)

REGRESSION_FILE = os.path.join(
    EXP03_DIR,
    "experiment_03_regression_results.csv"
)

GROUP_FILE = os.path.join(
    EXP03_DIR,
    "experiment_03_route_count_groups.csv"
)

PREDICTOR_CORR_FILE = os.path.join(
    EXP03_DIR,
    "experiment_03_predictor_correlations.csv"
)


summary.to_csv(
    SUMMARY_FILE
)

correlation_df.to_csv(
    CORRELATION_FILE,
    index=False
)

regression_df.to_csv(
    REGRESSION_FILE,
    index=False
)

group_summary.to_csv(
    GROUP_FILE
)

predictor_corr.to_csv(
    PREDICTOR_CORR_FILE
)


# ============================================================
# 11. Compact result summary
# ============================================================

print()
print(
    "=========================================="
)
print(
    "KEY RESULT SUMMARY"
)
print(
    "=========================================="
)


x = analysis_df[
    "distinct_route_count"
]

y = analysis_df[
    "target_pareto_labels"
]


pearson_r, pearson_p = (
    pearsonr(
        x,
        y
    )
)

spearman_rho, spearman_p = (
    spearmanr(
        x,
        y
    )
)


print()
print(
    "Distinct routes vs Pareto labels:"
)

print(
    f"  Pearson r = "
    f"{pearson_r:.4f}"
)

print(
    f"  Spearman rho = "
    f"{spearman_rho:.4f}"
)


# ------------------------------------------------------------
# Pareto Model B
# ------------------------------------------------------------

pareto_model_b = (
    regression_df[
        (
            regression_df[
                "outcome"
            ]
            ==
            "log_pareto"
        )
        &
        (
            regression_df[
                "model"
            ]
            ==
            "route_count_diversity_control_hops"
        )
    ]
)


print()
print(
    "Pareto Model B:"
)

for _, row in (
    pareto_model_b.iterrows()
):

    print(
        f"  {row['variable']}: "
        f"coef = "
        f"{row['coef']:.4f}, "
        f"p = "
        f"{row['p_value']:.4g}"
    )


if len(
    pareto_model_b
) > 0:

    print(
        f"  R-squared = "
        f"{pareto_model_b.iloc[0]['r_squared']:.4f}"
    )


# ------------------------------------------------------------
# Dominance checks Model B
# ------------------------------------------------------------

checks_model_b = (
    regression_df[
        (
            regression_df[
                "outcome"
            ]
            ==
            "log_checks"
        )
        &
        (
            regression_df[
                "model"
            ]
            ==
            "route_count_diversity_control_hops"
        )
    ]
)


print()
print(
    "Dominance-check Model B:"
)

for _, row in (
    checks_model_b.iterrows()
):

    print(
        f"  {row['variable']}: "
        f"coef = "
        f"{row['coef']:.4f}, "
        f"p = "
        f"{row['p_value']:.4g}"
    )


if len(
    checks_model_b
) > 0:

    print(
        f"  R-squared = "
        f"{checks_model_b.iloc[0]['r_squared']:.4f}"
    )


# ------------------------------------------------------------
# Runtime Model B
# ------------------------------------------------------------

runtime_model_b = (
    regression_df[
        (
            regression_df[
                "outcome"
            ]
            ==
            "log_runtime"
        )
        &
        (
            regression_df[
                "model"
            ]
            ==
            "route_count_diversity_control_hops"
        )
    ]
)


print()
print(
    "Runtime Model B:"
)

for _, row in (
    runtime_model_b.iterrows()
):

    print(
        f"  {row['variable']}: "
        f"coef = "
        f"{row['coef']:.4f}, "
        f"p = "
        f"{row['p_value']:.4g}"
    )


if len(
    runtime_model_b
) > 0:

    print(
        f"  R-squared = "
        f"{runtime_model_b.iloc[0]['r_squared']:.4f}"
    )


# ============================================================
# 12. Output summary
# ============================================================

print()
print(
    "=========================================="
)
print(
    "OUTPUT FILES"
)
print(
    "=========================================="
)

print(
    "Raw:",
    INPUT_FILE
)

print(
    "Summary:",
    SUMMARY_FILE
)

print(
    "Correlations:",
    CORRELATION_FILE
)

print(
    "Regression:",
    REGRESSION_FILE
)

print(
    "Route-count groups:",
    GROUP_FILE
)

print(
    "Predictor correlations:",
    PREDICTOR_CORR_FILE
)

print()

print(
    "All Experiment 3 outputs saved in:"
)

print(
    EXP03_DIR
)

print()

print(
    "Experiment 3 analysis "
    "completed successfully."
)