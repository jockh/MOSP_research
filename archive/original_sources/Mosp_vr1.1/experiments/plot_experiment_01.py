import os

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# File settings
# ============================================================

INPUT_FILE = (
    "experiments/results/"
    "experiment_01_formal_raw.csv"
)

OUTPUT_DIR = (
    "experiments/results/"
    "experiment_01_figures"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# Load data
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("Total observations:", len(df))

print(
    "Objective settings:",
    sorted(df["objectives"].unique())
)


# ============================================================
# Calculate mean values
# ============================================================

metrics = [
    "generated_labels",
    "dominance_checks",
    "runtime_seconds"
]

summary = (
    df.groupby("objectives")[metrics]
    .mean()
    .sort_index()
)


# ============================================================
# Normalize using m = 2 as baseline
# ============================================================

baseline = summary.loc[2]

relative = summary.divide(
    baseline,
    axis="columns"
)


# ============================================================
# Print relative growth
# ============================================================

print()
print("===== RELATIVE GROWTH (m = 2 baseline) =====")

for m in relative.index:

    print(
        f"m={m}: "
        f"Generated labels = "
        f"{relative.loc[m, 'generated_labels']:.2f}x, "
        f"Dominance checks = "
        f"{relative.loc[m, 'dominance_checks']:.2f}x, "
        f"Runtime = "
        f"{relative.loc[m, 'runtime_seconds']:.2f}x"
    )


# ============================================================
# Plot relative growth
# ============================================================

plt.figure(figsize=(7.2, 4.8))

plt.plot(
    relative.index,
    relative["generated_labels"],
    marker="o",
    linestyle="-",
    linewidth=1.8,
    markersize=6,
    label="Generated labels"
)

plt.plot(
    relative.index,
    relative["dominance_checks"],
    marker="s",
    linestyle="--",
    linewidth=1.8,
    markersize=6,
    label="Dominance checks"
)

plt.plot(
    relative.index,
    relative["runtime_seconds"],
    marker="^",
    linestyle="-.",
    linewidth=1.8,
    markersize=6,
    label="Runtime"
)

plt.axhline(
    y=1,
    linestyle=":",
    linewidth=1
)

plt.xlabel(
    "Number of Objectives ($m$)",
    fontsize=11
)

plt.ylabel(
    "Normalized Value ($m=2$ = 1.0)",
    fontsize=11
)

plt.xticks([2, 3, 4, 5])

plt.grid(
    alpha=0.2
)

plt.legend(
    frameon=False,
    fontsize=10
)

plt.tight_layout()

output_path = os.path.join(
    OUTPUT_DIR,
    "objective_growth.pdf"
)

plt.savefig(
    output_path,
    bbox_inches="tight"
)

plt.close()