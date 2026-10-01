from pathlib import Path
import re

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# =========================================================
# BASIC SETTINGS
# =========================================================

CASE_ORIGIN = "東湖站"
CASE_DESTINATION = "中原站"


# =========================================================
# FIND RESULT DIRECTORY
# =========================================================
#
# The script searches for:
# experiments/results/experiment_05_all_od/all_od_pareto_routes.csv
#
# If multiple project folders exist under MOSP_project,
# Real_case1 is preferred because this is the dataset used
# for the current Chapter 5 figures.
# =========================================================

SCRIPT_DIR = Path(__file__).resolve().parent
CWD = Path.cwd().resolve()
REL_RESULT_DIR = Path("experiments") / "results" / "experiment_05_all_od"
ROUTE_FILENAME = "all_od_pareto_routes.csv"


def locate_result_dir():
    checked = []

    for seed in [SCRIPT_DIR, CWD]:
        for base in [seed, *seed.parents]:
            # 1. Direct project root
            candidate = base / REL_RESULT_DIR
            checked.append(candidate)
            if (candidate / ROUTE_FILENAME).exists():
                return candidate

            # 2. If this is MOSP_project, prefer Real_case1
            if base.name.lower() == "mosp_project":
                preferred = base / "Real_case1" / REL_RESULT_DIR
                checked.append(preferred)
                if (preferred / ROUTE_FILENAME).exists():
                    return preferred

                # 3. Search immediate child project folders
                try:
                    children = [p for p in base.iterdir() if p.is_dir()]
                except OSError:
                    children = []

                for child in children:
                    candidate = child / REL_RESULT_DIR
                    checked.append(candidate)
                    if (candidate / ROUTE_FILENAME).exists():
                        return candidate

    message = [
        "找不到 Experiment 5 結果資料夾。",
        "需要找到：experiments/results/experiment_05_all_od/all_od_pareto_routes.csv",
        "",
        "已檢查的部分位置：",
    ]
    message.extend(str(p) for p in checked[:20])
    raise FileNotFoundError("\n".join(message))


RESULT_DIR = locate_result_dir()
ROUTE_FILE = RESULT_DIR / ROUTE_FILENAME
FIGURE_DIR = RESULT_DIR / "chapter5_figures_thesis"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

print(f"Using result directory:\n{RESULT_DIR}\n")


# =========================================================
# READ DATA
# =========================================================

routes_df = pd.read_csv(ROUTE_FILE, encoding="utf-8-sig")

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

missing_columns = required_columns - set(routes_df.columns)
if missing_columns:
    raise ValueError(
        "all_od_pareto_routes.csv 缺少欄位："
        + ", ".join(sorted(missing_columns))
    )


# =========================================================
# FONT / STYLE
# =========================================================

plt.rcParams["font.family"] = "Microsoft JhengHei"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 10
plt.rcParams["axes.labelsize"] = 11
plt.rcParams["xtick.labelsize"] = 10
plt.rcParams["ytick.labelsize"] = 10


def apply_thesis_style(ax, grid_axis="both"):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", labelsize=10)

    if grid_axis is not None:
        ax.grid(
            axis=grid_axis,
            linestyle="--",
            linewidth=0.6,
            alpha=0.30,
        )
        ax.set_axisbelow(True)


def save_figure(filename_without_extension):
    png_path = FIGURE_DIR / f"{filename_without_extension}.png"
    pdf_path = FIGURE_DIR / f"{filename_without_extension}.pdf"

    plt.tight_layout()
    plt.savefig(png_path, dpi=600, bbox_inches="tight")
    plt.savefig(pdf_path, bbox_inches="tight")
    plt.close()

    print(f"Saved PNG: {png_path}")
    print(f"Saved PDF: {pdf_path}")


# =========================================================
# CASE DATA: DONGHU -> ZHONGYUAN
# =========================================================

case_df = routes_df[
    (routes_df["origin"] == CASE_ORIGIN)
    & (routes_df["destination"] == CASE_DESTINATION)
].copy()

if case_df.empty:
    raise ValueError(f"找不到案例：{CASE_ORIGIN} -> {CASE_DESTINATION}")

case_df = case_df.sort_values("route_id").reset_index(drop=True)

print("=" * 90)
print(f"CASE: {CASE_ORIGIN} -> {CASE_DESTINATION}")
print("=" * 90)
print(
    case_df[
        [
            "route_id",
            "travel_time_minutes",
            "transfers",
            "walking_minutes",
        ]
    ].to_string(index=False)
)
print()


# =========================================================
# METRO LINE SETTINGS FOR FIGURE 5-7
# =========================================================

LINE_COLORS = {
    "BR": "#A05A2C",
    "BL": "#0070BD",
    "R": "#E3002C",
    "G": "#008659",
    "O": "#F39800",
    "Y": "#FFD400",
}


def line_family(line_code):
    line_code = str(line_code).strip()
    if line_code.startswith("O"):
        return "O"
    return line_code


def short_station_name(station):
    station = str(station).strip()
    if station.endswith("站"):
        station = station[:-1]
    return station


def parse_state_path(path_string):
    states = []

    for part in str(path_string).split(" -> "):
        part = part.strip()
        match = re.match(r"^(.*?)\[(.*?)\]$", part)

        if match:
            station = match.group(1).strip()
            line = match.group(2).strip()
            states.append((station, line))

    return states


def path_to_segments(path_string):
    states = parse_state_path(path_string)
    if not states:
        return []

    segments = []

    current_line = line_family(states[0][1])
    segment_start = states[0][0]
    segment_end = states[0][0]

    for station, raw_line in states[1:]:
        new_line = line_family(raw_line)

        if new_line == current_line:
            segment_end = station
        else:
            segments.append(
                {
                    "line": current_line,
                    "start": segment_start,
                    "end": segment_end,
                }
            )

            current_line = new_line
            segment_start = station
            segment_end = station

    segments.append(
        {
            "line": current_line,
            "start": segment_start,
            "end": segment_end,
        }
    )

    return segments


route_segments = {}
for _, row in case_df.iterrows():
    route_id = int(row["route_id"])
    route_segments[route_id] = path_to_segments(row["path"])


# =========================================================
# FIGURE 5-7
# DONGHU -> ZHONGYUAN ROUTE SCHEMATIC
# =========================================================

max_segments = max(len(x) for x in route_segments.values())

BOX_WIDTH = 2.15
BOX_HEIGHT = 0.62
BOX_GAP = 0.43

# Put the summary column immediately after the longest route.
summary_x = max_segments * (BOX_WIDTH + BOX_GAP) - BOX_GAP + 0.45

fig, ax = plt.subplots(figsize=(12.8, 6.0))
number_routes = len(case_df)

for row_index, row in case_df.iterrows():
    route_id = int(row["route_id"])
    segments = route_segments[route_id]
    y = number_routes - row_index

    ax.text(
        -0.42,
        y,
        f"R{route_id}",
        ha="right",
        va="center",
        fontsize=11,
        fontweight="bold",
    )

    for segment_index, segment in enumerate(segments):
        x = segment_index * (BOX_WIDTH + BOX_GAP)
        line = segment["line"]
        color = LINE_COLORS.get(line, "#808080")

        rectangle = Rectangle(
            (x, y - BOX_HEIGHT / 2),
            BOX_WIDTH,
            BOX_HEIGHT,
            facecolor=color,
            edgecolor=color,
            linewidth=1.6,
            alpha=0.22,
        )
        ax.add_patch(rectangle)

        start = short_station_name(segment["start"])
        end = short_station_name(segment["end"])
        station_text = start if start == end else f"{start} → {end}"

        ax.text(
            x + BOX_WIDTH / 2,
            y,
            f"{line}\n{station_text}",
            ha="center",
            va="center",
            fontsize=8.7,
        )

        if segment_index < len(segments) - 1:
            next_x = (segment_index + 1) * (BOX_WIDTH + BOX_GAP)
            ax.annotate(
                "",
                xy=(next_x - 0.05, y),
                xytext=(x + BOX_WIDTH + 0.05, y),
                arrowprops={
                    "arrowstyle": "->",
                    "linewidth": 1.0,
                    "color": "0.35",
                },
            )

    summary_text = (
        f"{row['travel_time_minutes']:.2f} min\n"
        f"{int(row['transfers'])} transfers\n"
        f"{row['walking_minutes']:.0f} min walk"
    )

    ax.text(
        summary_x,
        y,
        summary_text,
        ha="left",
        va="center",
        fontsize=9,
    )

ax.set_xlim(-1.05, summary_x + 1.45)
ax.set_ylim(0.55, number_routes + 0.6)
ax.axis("off")

save_figure("figure_5_7_donghu_zhongyuan_route_schematic")


# =========================================================
# FIGURE 5-8
# DONGHU -> ZHONGYUAN TRADE-OFF
# =========================================================

fig, ax = plt.subplots(figsize=(7.4, 5.6))

TRANSFER_MARKERS = {
    2: "o",
    3: "s",
    4: "^",
    5: "D",
}

unique_transfers = sorted(case_df["transfers"].astype(int).unique())

for transfer_count in unique_transfers:
    subset = case_df[case_df["transfers"].astype(int) == transfer_count]

    ax.scatter(
        subset["travel_time_minutes"],
        subset["walking_minutes"],
        marker=TRANSFER_MARKERS.get(transfer_count, "o"),
        s=90,
        alpha=0.85,
        label=f"{transfer_count} transfers",
        zorder=3,
    )

ANNOTATION_OFFSETS = {
    1: (7, -15),
    2: (7, 8),
    3: (7, 8),
    4: (7, 8),
    5: (7, 8),
}

for _, row in case_df.iterrows():
    route_id = int(row["route_id"])

    ax.annotate(
        f"R{route_id}",
        (row["travel_time_minutes"], row["walking_minutes"]),
        xytext=ANNOTATION_OFFSETS.get(route_id, (6, 6)),
        textcoords="offset points",
        fontsize=10,
        fontweight="bold",
    )

ax.set_xlabel("Travel Time (min)")
ax.set_ylabel("Transfer-Walking Time (min)")

x_min = case_df["travel_time_minutes"].min()
x_max = case_df["travel_time_minutes"].max()
y_min = case_df["walking_minutes"].min()
y_max = case_df["walking_minutes"].max()

ax.set_xlim(x_min - 2.0, x_max + 2.3)
ax.set_ylim(y_min - 1.2, y_max + 1.5)

ax.legend(
    frameon=False,
    title="Transfer Count",
    loc="upper right",
)

apply_thesis_style(ax, grid_axis="both")
save_figure("figure_5_8_donghu_zhongyuan_tradeoff")


# =========================================================
# FIGURE 5-9 DATA PREPARATION
# NETWORK-WIDE PRACTICAL TRADE-OFF
# =========================================================
#
# For each OD, select one fastest Pareto route as baseline.
# Tie breaking:
# 1. lower travel time
# 2. fewer transfers
# 3. shorter walking time
# 4. lower route_id
# =========================================================

baseline_source = routes_df.sort_values(
    [
        "origin",
        "destination",
        "travel_time_seconds",
        "transfers",
        "walking_seconds",
        "route_id",
    ]
)

baseline_df = (
    baseline_source.groupby(["origin", "destination"], as_index=False)
    .first()[
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
            "route_id": "baseline_route_id",
            "travel_time_minutes": "baseline_time_minutes",
            "transfers": "baseline_transfers",
            "walking_minutes": "baseline_walking_minutes",
        }
    )
)

comparison_df = routes_df.merge(
    baseline_df,
    on=["origin", "destination"],
    how="left",
)

alternative_df = comparison_df[
    comparison_df["route_id"] != comparison_df["baseline_route_id"]
].copy()

alternative_df["additional_travel_time_minutes"] = (
    alternative_df["travel_time_minutes"]
    - alternative_df["baseline_time_minutes"]
)

alternative_df["walking_time_saved_minutes"] = (
    alternative_df["baseline_walking_minutes"]
    - alternative_df["walking_minutes"]
)

alternative_df["transfer_saving"] = (
    alternative_df["baseline_transfers"]
    - alternative_df["transfers"]
)

# Numerical tolerance
alternative_df.loc[
    alternative_df["additional_travel_time_minutes"].abs() < 1e-10,
    "additional_travel_time_minutes",
] = 0.0

alternative_df.loc[
    alternative_df["walking_time_saved_minutes"].abs() < 1e-10,
    "walking_time_saved_minutes",
] = 0.0


def transfer_category(value):
    if value > 0:
        return "Fewer transfers"
    if value < 0:
        return "More transfers"
    return "Same transfers"


alternative_df["transfer_category"] = alternative_df["transfer_saving"].apply(
    transfer_category
)

FIGURE_59_DATA = FIGURE_DIR / "figure_5_9_network_tradeoff_data.csv"

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
    encoding="utf-8-sig",
)


# =========================================================
# FIGURE 5-9
# FINAL THESIS VERSION
# =========================================================

fig, ax = plt.subplots(figsize=(8.2, 6.0))

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
        alternative_df["transfer_category"] == category
    ]
    style = CATEGORY_STYLE[category]

    ax.scatter(
        subset["additional_travel_time_minutes"],
        subset["walking_time_saved_minutes"],
        marker=style["marker"],
        s=style["size"],
        alpha=style["alpha"],
        label=category,
        rasterized=True,
        zorder=2,
    )

# y = 0: above means less walking than the fastest route.
ax.axhline(
    y=0,
    linewidth=1.0,
    linestyle="--",
    zorder=1,
)

# Highlight the representative OD.
highlight_df = alternative_df[
    (alternative_df["origin"] == CASE_ORIGIN)
    & (alternative_df["destination"] == CASE_DESTINATION)
].copy()

ax.scatter(
    highlight_df["additional_travel_time_minutes"],
    highlight_df["walking_time_saved_minutes"],
    marker="*",
    s=130,
    edgecolors="black",
    linewidths=0.8,
    label="Donghu → Zhongyuan",
    zorder=5,
)

label_offsets = {
    2: (6, 5),
    3: (6, -13),
    4: (6, 5),
    5: (6, 5),
}

for _, row in highlight_df.iterrows():
    route_id = int(row["route_id"])

    ax.annotate(
        f"R{route_id}",
        (
            row["additional_travel_time_minutes"],
            row["walking_time_saved_minutes"],
        ),
        xytext=label_offsets.get(route_id, (6, 6)),
        textcoords="offset points",
        fontsize=8.5,
        fontweight="bold",
        zorder=6,
    )

ax.set_xlabel("Additional Travel Time vs. Fastest Route (min)")
ax.set_ylabel("Transfer-Walking Time Saved vs. Fastest Route (min)")

ax.set_xlim(
    -1.5,
    alternative_df["additional_travel_time_minutes"].max() + 3,
)

ax.legend(
    frameon=False,
    loc="upper right",
)

apply_thesis_style(ax, grid_axis="both")

# IMPORTANT:
# Figure 5-9 is saved exactly once.
# There is no second old plotting block after this line.
save_figure("figure_5_9_network_practical_tradeoff")


# =========================================================
# FIGURE 5-9 SUMMARY
# =========================================================

print()
print("=" * 90)
print("FIGURE 5-9 NETWORK-WIDE TRADE-OFF SUMMARY")
print("=" * 90)

print(f"Alternative Pareto routes: {len(alternative_df)}")
print(
    "Mean additional travel time: "
    f"{alternative_df['additional_travel_time_minutes'].mean():.2f} min"
)
print(
    "Median additional travel time: "
    f"{alternative_df['additional_travel_time_minutes'].median():.2f} min"
)
print(
    "Mean walking time saved: "
    f"{alternative_df['walking_time_saved_minutes'].mean():.2f} min"
)
print(
    "Median walking time saved: "
    f"{alternative_df['walking_time_saved_minutes'].median():.2f} min"
)

walking_improved = (
    alternative_df["walking_time_saved_minutes"] > 0
).mean() * 100

transfer_improved = (
    alternative_df["transfer_saving"] > 0
).mean() * 100

both_improved = (
    (alternative_df["walking_time_saved_minutes"] > 0)
    & (alternative_df["transfer_saving"] > 0)
).mean() * 100

print(f"Alternatives with less walking: {walking_improved:.2f}%")
print(f"Alternatives with fewer transfers: {transfer_improved:.2f}%")
print(
    "Alternatives with both less walking and fewer transfers: "
    f"{both_improved:.2f}%"
)


# =========================================================
# DONGHU -> ZHONGYUAN RELATIVE TO FASTEST ROUTE
# =========================================================

case_comparison = (
    alternative_df[
        (alternative_df["origin"] == CASE_ORIGIN)
        & (alternative_df["destination"] == CASE_DESTINATION)
    ][
        [
            "route_id",
            "additional_travel_time_minutes",
            "walking_time_saved_minutes",
            "transfer_saving",
        ]
    ]
    .sort_values("route_id")
)

print()
print("=" * 90)
print(f"{CASE_ORIGIN} -> {CASE_DESTINATION}: RELATIVE TO FASTEST ROUTE")
print("=" * 90)
print(case_comparison.to_string(index=False))


# =========================================================
# FINISH
# =========================================================

print()
print("=" * 90)
print("CHAPTER 5 FIGURES 5-7 TO 5-9 CREATED")
print("=" * 90)
print("Figure 5-7 : Donghu -> Zhongyuan route schematic")
print("Figure 5-8 : Donghu -> Zhongyuan Pareto trade-off")
print("Figure 5-9 : Network-wide practical trade-off")
print()
print(f"Figures saved to:\n{FIGURE_DIR}")
print()
print(f"Figure 5-9 data saved to:\n{FIGURE_59_DATA}")
