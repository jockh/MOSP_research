from src.paths import PROJECT_ROOT, RESULTS_DIR as CANONICAL_RESULTS_DIR, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, result_path, project_path
from pathlib import Path
import re
import pandas as pd

if __name__ == "__main__":






    # =========================================================
    # PATHS
    # =========================================================

    ROOT = PROJECT_ROOT

    RESULT_DIR = (
        CANONICAL_RESULTS_DIR / 'experiment_04_taipei_main_all'
    )

    ROUTE_FILE = (
        RESULT_DIR
        / "multi_pareto_route_details.csv"
    )


    # =========================================================
    # READ DATA
    # =========================================================

    df = pd.read_csv(
        ROUTE_FILE,
        encoding="utf-8-sig"
    )


    # =========================================================
    # PARSE PATH
    # =========================================================

    NODE_PATTERN = re.compile(
        r"(.+?)\[([^\]]+)\]"
    )


    def parse_path(path_string):

        parts = [
            x.strip()
            for x in path_string.split("->")
        ]

        nodes = []

        for part in parts:

            match = NODE_PATTERN.match(part)

            if match:

                station = match.group(1).strip()
                line = match.group(2).strip()

                nodes.append(
                    (station, line)
                )

        return nodes


    # =========================================================
    # EXTRACT LINE SEQUENCE
    # =========================================================

    def extract_line_sequence(path_string):

        nodes = parse_path(
            path_string
        )

        lines = []

        for _, line in nodes:

            if (
                len(lines) == 0
                or lines[-1] != line
            ):
                lines.append(
                    line
                )

        return " -> ".join(lines)


    # =========================================================
    # EXTRACT TRANSFER STATIONS
    # =========================================================

    def extract_transfer_stations(path_string):

        nodes = parse_path(
            path_string
        )

        transfers = []

        for i in range(
            1,
            len(nodes)
        ):

            prev_station, prev_line = (
                nodes[i - 1]
            )

            curr_station, curr_line = (
                nodes[i]
            )

            if (
                prev_station == curr_station
                and prev_line != curr_line
            ):

                transfers.append(
                    curr_station
                )

        if not transfers:
            return "None"

        return " | ".join(
            transfers
        )


    # =========================================================
    # EXTRACT TRANSFER PATTERN
    # =========================================================

    def extract_transfer_pattern(path_string):

        nodes = parse_path(
            path_string
        )

        pattern = []

        for i in range(
            1,
            len(nodes)
        ):

            prev_station, prev_line = (
                nodes[i - 1]
            )

            curr_station, curr_line = (
                nodes[i]
            )

            if (
                prev_station == curr_station
                and prev_line != curr_line
            ):

                pattern.append(
                    f"{prev_line}"
                    f"->{curr_line}"
                    f"@{curr_station}"
                )

        if not pattern:
            return "Direct"

        return " | ".join(
            pattern
        )


    # =========================================================
    # APPLY PARSING
    # =========================================================

    df[
        "line_sequence"
    ] = df[
        "path"
    ].apply(
        extract_line_sequence
    )


    df[
        "transfer_stations"
    ] = df[
        "path"
    ].apply(
        extract_transfer_stations
    )


    df[
        "transfer_pattern"
    ] = df[
        "path"
    ].apply(
        extract_transfer_pattern
    )


    # =========================================================
    # SAVE ENRICHED ROUTE TABLE
    # =========================================================

    ENRICHED_FILE = (
        RESULT_DIR
        / "multi_pareto_route_patterns.csv"
    )

    df.to_csv(
        ENRICHED_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    # =========================================================
    # OD-LEVEL PAIR COMPARISON
    # =========================================================

    pair_rows = []


    for destination, group in df.groupby(
        "destination"
    ):

        group = group.sort_values(
            "travel_time_minutes"
        )

        if len(group) != 2:
            continue


        fast = group.iloc[0]
        slow = group.iloc[1]


        time_difference = (
            slow[
                "travel_time_minutes"
            ]
            -
            fast[
                "travel_time_minutes"
            ]
        )


        walking_difference = (
            fast[
                "walking_minutes"
            ]
            -
            slow[
                "walking_minutes"
            ]
        )


        transfer_difference = (
            fast[
                "transfers"
            ]
            -
            slow[
                "transfers"
            ]
        )


        # -----------------------------------------------------
        # Trade-off classification
        # -----------------------------------------------------

        if (
            walking_difference > 0
            and transfer_difference == 0
        ):

            tradeoff_type = (
                "time_vs_walking"
            )

        elif (
            transfer_difference > 0
            and walking_difference == 0
        ):

            tradeoff_type = (
                "time_vs_transfers"
            )

        elif (
            transfer_difference > 0
            and walking_difference > 0
        ):

            tradeoff_type = (
                "time_vs_transfer_and_walking"
            )

        else:

            tradeoff_type = (
                "other"
            )


        pair_rows.append({

            "destination":
                destination,

            "fast_route_time":
                fast[
                    "travel_time_minutes"
                ],

            "slow_route_time":
                slow[
                    "travel_time_minutes"
                ],

            "time_penalty_for_slow_route":
                time_difference,

            "fast_route_walking":
                fast[
                    "walking_minutes"
                ],

            "slow_route_walking":
                slow[
                    "walking_minutes"
                ],

            "walking_saved_by_slow_route":
                walking_difference,

            "fast_route_transfers":
                fast[
                    "transfers"
                ],

            "slow_route_transfers":
                slow[
                    "transfers"
                ],

            "transfer_difference":
                transfer_difference,

            "fast_transfer_pattern":
                fast[
                    "transfer_pattern"
                ],

            "slow_transfer_pattern":
                slow[
                    "transfer_pattern"
                ],

            "fast_line_sequence":
                fast[
                    "line_sequence"
                ],

            "slow_line_sequence":
                slow[
                    "line_sequence"
                ],

            "tradeoff_type":
                tradeoff_type

        })


    pair_df = pd.DataFrame(
        pair_rows
    )


    # =========================================================
    # SAVE PAIR COMPARISON
    # =========================================================

    PAIR_FILE = (
        RESULT_DIR
        / "multi_pareto_od_pair_comparison.csv"
    )

    pair_df.to_csv(
        PAIR_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    # =========================================================
    # TRADE-OFF TYPE SUMMARY
    # =========================================================

    tradeoff_summary = (
        pair_df[
            "tradeoff_type"
        ]
        .value_counts()
        .reset_index()
    )


    tradeoff_summary.columns = [
        "tradeoff_type",
        "number_of_od_pairs"
    ]


    tradeoff_summary[
        "percentage"
    ] = (
        tradeoff_summary[
            "number_of_od_pairs"
        ]
        /
        len(pair_df)
        *
        100
    )


    TRADEOFF_FILE = (
        RESULT_DIR
        / "tradeoff_type_summary.csv"
    )

    tradeoff_summary.to_csv(
        TRADEOFF_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    # =========================================================
    # TRANSFER PATTERN FREQUENCY
    # =========================================================

    transfer_pattern_summary = (
        df[
            "transfer_pattern"
        ]
        .value_counts()
        .reset_index()
    )


    transfer_pattern_summary.columns = [
        "transfer_pattern",
        "route_count"
    ]


    TRANSFER_FILE = (
        RESULT_DIR
        / "transfer_pattern_frequency.csv"
    )

    transfer_pattern_summary.to_csv(
        TRANSFER_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    # =========================================================
    # PRINT RESULTS
    # =========================================================

    print()
    print("=" * 75)
    print("TRADE-OFF TYPE SUMMARY")
    print("=" * 75)

    print(
        tradeoff_summary.to_string(
            index=False
        )
    )


    print()
    print("=" * 75)
    print("OD-LEVEL ROUTE COMPARISON")
    print("=" * 75)

    print(

        pair_df[
            [
                "destination",
                "time_penalty_for_slow_route",
                "walking_saved_by_slow_route",
                "transfer_difference",
                "tradeoff_type",
                "fast_transfer_pattern",
                "slow_transfer_pattern"
            ]
        ]

        .to_string(
            index=False
        )

    )


    print()
    print("=" * 75)
    print("MOST COMMON TRANSFER PATTERNS")
    print("=" * 75)

    print(
        transfer_pattern_summary.head(
            20
        ).to_string(
            index=False
        )
    )


    print()
    print("=" * 75)
    print("OUTPUT FILES")
    print("=" * 75)

    print(
        f"Patterns: {ENRICHED_FILE}"
    )

    print(
        f"OD comparison: {PAIR_FILE}"
    )

    print(
        f"Trade-off summary: {TRADEOFF_FILE}"
    )

    print(
        f"Transfer patterns: {TRANSFER_FILE}"
    )

    print()

    print(
        "Experiment 4B completed successfully."
    )