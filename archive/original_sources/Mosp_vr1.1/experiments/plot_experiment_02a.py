import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# Experiment 2A Plotting
# Normalized Workload under Different Correlations
# ============================================================

INPUT_FILE = os.path.join(
    "experiments",
    "results",
    "experiment_02a_correlation_raw.csv"
)

OUTPUT_DIR = os.path.join(
    "experiments",
    "results",
    "experiment_02a_figures"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# 1. Load data
# ============================================================

df = pd.read_csv(INPUT_FILE)

print(
    "Total observations:",
    len(df)
)


# ============================================================
# 2. Derived metric
# Comparisons per generated label
# ============================================================

df["comparisons_per_generated_label"] = np.where(
    df["generated_labels"] > 0,
    df["dominance_checks"]
    / df["generated_labels"],
    0.0
)


# ============================================================
# 3. Calculate mean by correlation condition
# ============================================================

metrics = [
    "generated_labels",
    "comparisons_per_generated_label",
    "dominance_checks",
    "runtime_seconds"
]


means = (
    df
    .groupby("target_rho")[metrics]
    .mean()
    .sort_index()
)


print()
print(
    "===== RAW MEANS ====="
)

print(
    means.round(6)
)


# ============================================================
# 4. Normalize relative to rho = 0
# ============================================================

baseline_rho = 0.0

baseline = means.loc[
    baseline_rho
]


normalized = (
    means
    / baseline
)


print()
print(
    "===== NORMALIZED TO rho = 0 ====="
)

print(
    normalized.round(3)
)


# ============================================================
# 5. Plot normalized workload
# ============================================================

fig, ax = plt.subplots(
    figsize=(7.5, 5.2)
)


x = normalized.index.to_numpy()


ax.plot(
    x,
    normalized["generated_labels"],
    marker="o",
    linewidth=2,
    markersize=6,
    label="Generated labels"
)


ax.plot(
    x,
    normalized[
        "comparisons_per_generated_label"
    ],
    marker="s",
    linewidth=2,
    markersize=6,
    label="Comparisons per generated label"
)


ax.plot(
    x,
    normalized["dominance_checks"],
    marker="^",
    linewidth=2,
    markersize=6,
    label="Dominance checks"
)


ax.plot(
    x,
    normalized["runtime_seconds"],
    marker="D",
    linewidth=2,
    markersize=6,
    label="Runtime"
)


# ============================================================
# 6. Reference line
# rho = 0 baseline
# ============================================================

ax.axhline(
    y=1.0,
    linewidth=1,
    linestyle="--",
    alpha=0.6
)


# ============================================================
# 7. Axis settings
# ============================================================

ax.set_xlabel(
    r"Objective Correlation ($\rho$)",
    fontsize=12
)

ax.set_ylabel(
    r"Relative Value ($\rho=0$ = 1)",
    fontsize=12
)


ax.set_xticks(
    [-0.8, -0.4, 0.0, 0.4, 0.8]
)


ax.tick_params(
    axis="both",
    labelsize=11
)


ax.grid(
    alpha=0.20
)


ax.legend(
    fontsize=10,
    frameon=False
)


# No title:
# thesis caption will explain the figure.


plt.tight_layout()


# ============================================================
# 8. Save PNG
# ============================================================

PNG_FILE = os.path.join(
    OUTPUT_DIR,
    "objective_correlation_workload.png"
)

plt.savefig(
    PNG_FILE,
    dpi=300,
    bbox_inches="tight"
)


# ============================================================
# 9. Save PDF
# Recommended for LaTeX
# ============================================================

PDF_FILE = os.path.join(
    OUTPUT_DIR,
    "objective_correlation_workload.pdf"
)

plt.savefig(
    PDF_FILE,
    bbox_inches="tight"
)


plt.close()


print()
print(
    "Saved:",
    PNG_FILE
)

print(
    "Saved:",
    PDF_FILE
)


# ============================================================
# 10. Print key comparison
# rho = -0.8 vs rho = +0.8
# ============================================================

negative = means.loc[
    -0.8
]

positive = means.loc[
    0.8
]


print()
print(
    "===== rho = -0.8 / rho = +0.8 ====="
)


for metric in metrics:

    ratio = (
        negative[metric]
        / positive[metric]
    )

    print(
        f"{metric}: "
        f"{ratio:.3f}x"
    )


print()
print(
    "Experiment 2A figure generated successfully."
)