from pathlib import Path

import copy
import time



import pandas as pd



from src.mosp import (

    mosp,

    reconstruct_path

)



from src.taipei_metro import (

    build_taipei_metro_graph,

    format_path

)





# =========================================================

# PATHS

# =========================================================



ROOT = Path(__file__).resolve().parents[1]



DATA_DIR = (

    ROOT
    /"Real_case1"

    / "data"


)



RESULT_DIR = (

    ROOT
    /"Real_case1"

    / "experiments"

    / "results"

    / "experiment_05_all_od"

)



RESULT_DIR.mkdir(

    parents=True,

    exist_ok=True

)





STATION_FILE = (

    DATA_DIR

    / "臺北捷運路線車站資料服務_NEW_fixed (1).csv"

)



TRAVEL_FILE = (

    DATA_DIR

    / "臺北捷運相鄰兩站間之行駛時間及停靠站時間(1150830).csv"

)



TRANSFER_FILE = (

    DATA_DIR

    / "臺北捷運轉乘車站轉乘步行時間資料.csv"

)





NUM_OBJECTIVES = 3





# =========================================================

# BUILD BASE NETWORK

# =========================================================



base_graph, build_stats = (

    build_taipei_metro_graph(

        station_file=STATION_FILE,

        travel_time_file=TRAVEL_FILE,

        transfer_file=TRANSFER_FILE,

        include_circular_line=True,

        dapinglin_transfer_minutes=3.0

    )

)





if not build_stats.get(

    "circular_line_included",

    False

):

    raise RuntimeError(

        "Circular Line was not included in the network."

    )



if build_stats.get(

    "skipped_travel_rows",

    0

) != 0:

    print(

        "WARNING: skipped travel-time rows remain:",

        build_stats.get(

            "skipped_pairs",

            []

        )

    )



PHYSICAL_STATIONS = sorted(

    base_graph.states_by_name.keys()

)





print("=" * 80)

print("EXPERIMENT 5")

print("TAIPEI METRO ALL-ORIGIN ALL-DESTINATION MOSP")

print("=" * 80)



print()



print("NETWORK SUMMARY")



for key, value in build_stats.items():



    if key != "skipped_pairs":

        print(

            f"{key}: {value}"

        )





print()



print(

    "Physical stations:",

    len(PHYSICAL_STATIONS)

)



print(

    "Ordered OD pairs:",

    len(PHYSICAL_STATIONS)

    *

    (

        len(PHYSICAL_STATIONS) - 1

    )

)





print()



print("Skipped travel pairs:")



for pair in build_stats[

    "skipped_pairs"

]:

    print(

        " ",

        pair

    )





# =========================================================

# ADD VIRTUAL TARGET FOR EVERY PHYSICAL STATION

# =========================================================



def build_all_target_graph(

    base_graph

):



    graph = copy.deepcopy(

        base_graph

    )



    target_nodes = {}



    for station_name in sorted(

        graph.states_by_name.keys()

    ):



        target = (

            f"__TARGET__::{station_name}"

        )



        target_nodes[

            station_name

        ] = target





        graph.add_node(

            target,

            kind="virtual_target",

            station_name=station_name

        )





        # Every line/service state corresponding

        # to this physical station can reach

        # the same virtual destination.

        for state in graph.states_by_name[

            station_name

        ]:



            graph.add_edge(

                state,

                target,

                (0, 0, 0),

                kind="egress"

            )



    return graph, target_nodes





# =========================================================

# ADD ONE VIRTUAL SOURCE

# =========================================================



def add_origin_source(

    graph,

    origin_name

):



    source = (

        f"__SOURCE__::{origin_name}"

    )



    graph.add_node(

        source,

        kind="virtual_source",

        station_name=origin_name

    )



    # -----------------------------------------------------

    # Remove the origin-station dwell time.

    #

    # The base graph stores a ride edge as:

    #

    #     dwell at departure station + running time

    #

    # When this physical station is the trip origin, the

    # passenger should not be charged the dwell time that

    # occurs before departure.

    #

    # Each origin uses a fresh graph copy, so changing these

    # outgoing ride edges does not affect other origins.

    # -----------------------------------------------------



    for state in graph.states_by_name[

        origin_name

    ]:



        for edge in graph.adj[state]:



            if edge.kind != "ride":

                continue



            travel_time = int(

                edge.info.get(

                    "travel_time",

                    edge.costs[0]

                )

            )



            removed_stop_time = int(

                edge.info.get(

                    "stop_time",

                    0

                )

            )



            edge.costs = (

                travel_time,

                edge.costs[1],

                edge.costs[2]

            )



            edge.info[

                "origin_stop_time_removed"

            ] = removed_stop_time



            edge.info[

                "total_time"

            ] = travel_time



    # Starting on any line/service at the physical origin

    # does NOT count as a transfer.

    for state in graph.states_by_name[

        origin_name

    ]:



        graph.add_edge(

            source,

            state,

            (0, 0, 0),

            kind="access"

        )



    return source




# =========================================================

# GRAPH WITH ALL DESTINATION TARGETS

# =========================================================



all_target_graph, target_nodes = (

    build_all_target_graph(

        base_graph

    )

)





# =========================================================

# RESULT CONTAINERS

# =========================================================



od_summary_rows = []



route_rows = []



source_stats_rows = []





# =========================================================

# RUN ONE MOSP PER ORIGIN

# =========================================================



num_origins = len(

    PHYSICAL_STATIONS

)





for origin_index, origin in enumerate(

    PHYSICAL_STATIONS,

    start=1

):



    print()

    print("=" * 80)



    print(

        f"[Origin "

        f"{origin_index}/{num_origins}] "

        f"{origin}"

    )



    print("=" * 80)





    # -----------------------------------------------------

    # One graph copy for this origin

    # -----------------------------------------------------



    graph = copy.deepcopy(

        all_target_graph

    )





    source = add_origin_source(

        graph,

        origin

    )





    # -----------------------------------------------------

    # ONE source-to-all MOSP search

    # -----------------------------------------------------



    search_start = time.perf_counter()



    labels, stats = mosp(

        graph=graph,

        source=source,

        num_objectives=NUM_OBJECTIVES,

        return_stats=True

    )



    runtime_seconds = (

        time.perf_counter()

        - search_start

    )





    # -----------------------------------------------------

    # Store source-level computational statistics

    # -----------------------------------------------------



    source_stats_rows.append({



        "origin":

            origin,



        "generated_labels":

            stats[

                "generated_labels"

            ],



        "kept_labels":

            stats[

                "kept_labels"

            ],



        "pruned_labels":

            stats[

                "pruned_labels"

            ],



        "dominance_checks":

            stats[

                "dominance_checks"

            ],



        "max_labels_per_node":

            stats[

                "max_labels_per_node"

            ],



        "runtime_seconds":

            runtime_seconds



    })





    origin_pareto_routes = 0



    origin_multi_od = 0





    # =====================================================

    # READ ALL DESTINATIONS FROM SAME SEARCH

    # =====================================================



    for destination in PHYSICAL_STATIONS:



        if destination == origin:

            continue





        target = target_nodes[

            destination

        ]





        target_labels = sorted(

            [

                label

                for label in labels[target]

                if getattr(

                    label,

                    "active",

                    True

                )

            ],

            key=lambda label:

                label.costs

        )





        pareto_count = len(

            target_labels

        )





        origin_pareto_routes += (

            pareto_count

        )





        if pareto_count > 1:

            origin_multi_od += 1





        costs_for_this_od = []





        # -------------------------------------------------

        # Route-level details

        # -------------------------------------------------



        for route_id, label in enumerate(

            target_labels,

            start=1

        ):



            path = reconstruct_path(

                label

            )



            readable_path = format_path(

                graph,

                path

            )





            travel_time_seconds = (

                label.costs[0]

            )



            transfers = (

                label.costs[1]

            )



            walking_seconds = (

                label.costs[2]

            )





            travel_time_minutes = (

                travel_time_seconds

                / 60

            )



            walking_minutes = (

                walking_seconds

                / 60

            )





            costs_for_this_od.append(

                (

                    travel_time_seconds,

                    transfers,

                    walking_seconds

                )

            )





            route_rows.append({



                "origin":

                    origin,



                "destination":

                    destination,



                "route_id":

                    route_id,



                "travel_time_seconds":

                    travel_time_seconds,



                "travel_time_minutes":

                    travel_time_minutes,



                "transfers":

                    transfers,



                "walking_seconds":

                    walking_seconds,



                "walking_minutes":

                    walking_minutes,



                "path":

                    readable_path



            })





        # -------------------------------------------------

        # OD-level summary

        # -------------------------------------------------



        if pareto_count > 0:



            fastest_seconds = min(

                x[0]

                for x in costs_for_this_od

            )



            minimum_transfers = min(

                x[1]

                for x in costs_for_this_od

            )



            minimum_walking_seconds = min(

                x[2]

                for x in costs_for_this_od

            )





            slowest_seconds = max(

                x[0]

                for x in costs_for_this_od

            )



            maximum_transfers = max(

                x[1]

                for x in costs_for_this_od

            )



            maximum_walking_seconds = max(

                x[2]

                for x in costs_for_this_od

            )





            time_range_seconds = (

                slowest_seconds

                -

                fastest_seconds

            )



            transfer_range = (

                maximum_transfers

                -

                minimum_transfers

            )



            walking_range_seconds = (

                maximum_walking_seconds

                -

                minimum_walking_seconds

            )





        else:



            fastest_seconds = None



            minimum_transfers = None



            minimum_walking_seconds = None



            time_range_seconds = None



            transfer_range = None



            walking_range_seconds = None





        od_summary_rows.append({



            "origin":

                origin,



            "destination":

                destination,



            "pareto_route_count":

                pareto_count,



            "fastest_travel_time_minutes":

                (

                    fastest_seconds / 60

                    if fastest_seconds

                    is not None

                    else None

                ),



            "minimum_transfers":

                minimum_transfers,



            "minimum_walking_minutes":

                (

                    minimum_walking_seconds / 60

                    if minimum_walking_seconds

                    is not None

                    else None

                ),



            "pareto_time_range_minutes":

                (

                    time_range_seconds / 60

                    if time_range_seconds

                    is not None

                    else None

                ),



            "pareto_transfer_range":

                transfer_range,



            "pareto_walking_range_minutes":

                (

                    walking_range_seconds / 60

                    if walking_range_seconds

                    is not None

                    else None

                )



        })





    print(

        f"  Destinations: "

        f"{num_origins - 1}"

    )



    print(

        f"  Multi-Pareto ODs: "

        f"{origin_multi_od}"

    )



    print(

        f"  Total Pareto routes: "

        f"{origin_pareto_routes}"

    )



    print(

        f"  Generated labels: "

        f"{stats['generated_labels']}"

    )



    print(

        f"  Dominance checks: "

        f"{stats['dominance_checks']}"

    )



    print(

        f"  Runtime: "

        f"{runtime_seconds:.6f} sec"

    )





# =========================================================

# DATAFRAMES

# =========================================================



od_df = pd.DataFrame(

    od_summary_rows

)



routes_df = pd.DataFrame(

    route_rows

)



source_stats_df = pd.DataFrame(

    source_stats_rows

)





# =========================================================

# SORT

# =========================================================



od_df = (

    od_df

    .sort_values(

        [

            "origin",

            "destination"

        ]

    )

    .reset_index(

        drop=True

    )

)





routes_df = (

    routes_df

    .sort_values(

        [

            "origin",

            "destination",

            "travel_time_seconds",

            "transfers",

            "walking_seconds"

        ]

    )

    .reset_index(

        drop=True

    )

)





source_stats_df = (

    source_stats_df

    .sort_values(

        "origin"

    )

    .reset_index(

        drop=True

    )

)





# =========================================================

# PARETO SET SIZE DISTRIBUTION

# =========================================================



distribution_df = (

    od_df[

        "pareto_route_count"

    ]

    .value_counts()

    .sort_index()

    .reset_index()

)





distribution_df.columns = [

    "pareto_route_count",

    "number_of_od_pairs"

]





distribution_df[

    "percentage"

] = (

    distribution_df[

        "number_of_od_pairs"

    ]

    /

    len(od_df)

    *

    100

)





# =========================================================

# ORIGIN SUMMARY

# =========================================================



origin_summary_df = (

    od_df

    .groupby(

        "origin"

    )

    .agg(



        destinations=(

            "destination",

            "count"

        ),



        mean_pareto_size=(

            "pareto_route_count",

            "mean"

        ),



        max_pareto_size=(

            "pareto_route_count",

            "max"

        ),



        multi_pareto_od_count=(

            "pareto_route_count",

            lambda x:

                (x > 1).sum()

        )



    )

    .reset_index()

)





origin_summary_df[

    "multi_pareto_percentage"

] = (

    origin_summary_df[

        "multi_pareto_od_count"

    ]

    /

    origin_summary_df[

        "destinations"

    ]

    *

    100

)





# =========================================================

# DESTINATION SUMMARY

# =========================================================



destination_summary_df = (

    od_df

    .groupby(

        "destination"

    )

    .agg(



        origins=(

            "origin",

            "count"

        ),



        mean_pareto_size=(

            "pareto_route_count",

            "mean"

        ),



        max_pareto_size=(

            "pareto_route_count",

            "max"

        ),



        multi_pareto_od_count=(

            "pareto_route_count",

            lambda x:

                (x > 1).sum()

        )



    )

    .reset_index()

)





destination_summary_df[

    "multi_pareto_percentage"

] = (

    destination_summary_df[

        "multi_pareto_od_count"

    ]

    /

    destination_summary_df[

        "origins"

    ]

    *

    100

)





# =========================================================

# MULTI-PARETO ODs

# =========================================================



multi_od_df = (

    od_df[

        od_df[

            "pareto_route_count"

        ] > 1

    ]

    .copy()

    .sort_values(

        [

            "pareto_route_count",

            "pareto_time_range_minutes"

        ],

        ascending=[

            False,

            False

        ]

    )

    .reset_index(

        drop=True

    )

)





# =========================================================

# SAVE

# =========================================================



OD_FILE = (

    RESULT_DIR

    / "all_od_summary.csv"

)



ROUTE_FILE = (

    RESULT_DIR

    / "all_od_pareto_routes.csv"

)



SOURCE_STATS_FILE = (

    RESULT_DIR

    / "source_mosp_statistics.csv"

)



DISTRIBUTION_FILE = (

    RESULT_DIR

    / "pareto_set_size_distribution.csv"

)



ORIGIN_SUMMARY_FILE = (

    RESULT_DIR

    / "origin_summary.csv"

)



DEST_SUMMARY_FILE = (

    RESULT_DIR

    / "destination_summary.csv"

)



MULTI_OD_FILE = (

    RESULT_DIR

    / "multi_pareto_od_pairs.csv"

)





od_df.to_csv(

    OD_FILE,

    index=False,

    encoding="utf-8-sig"

)



routes_df.to_csv(

    ROUTE_FILE,

    index=False,

    encoding="utf-8-sig"

)



source_stats_df.to_csv(

    SOURCE_STATS_FILE,

    index=False,

    encoding="utf-8-sig"

)



distribution_df.to_csv(

    DISTRIBUTION_FILE,

    index=False,

    encoding="utf-8-sig"

)



origin_summary_df.to_csv(

    ORIGIN_SUMMARY_FILE,

    index=False,

    encoding="utf-8-sig"

)



destination_summary_df.to_csv(

    DEST_SUMMARY_FILE,

    index=False,

    encoding="utf-8-sig"

)



multi_od_df.to_csv(

    MULTI_OD_FILE,

    index=False,

    encoding="utf-8-sig"

)





# =========================================================

# FINAL RESULTS

# =========================================================



total_od = len(

    od_df

)



single_od = (

    od_df[

        "pareto_route_count"

    ]

    .eq(1)

    .sum()

)



multi_od = (

    od_df[

        "pareto_route_count"

    ]

    .gt(1)

    .sum()

)



max_pareto = (

    od_df[

        "pareto_route_count"

    ]

    .max()

)





print()

print("=" * 80)

print("PARETO SET SIZE DISTRIBUTION")

print("=" * 80)



print(

    distribution_df.to_string(

        index=False

    )

)





print()

print("=" * 80)

print("KEY RESULT SUMMARY")

print("=" * 80)



print(

    f"Physical stations: "

    f"{len(PHYSICAL_STATIONS)}"

)



print(

    f"Total ordered OD pairs: "

    f"{total_od}"

)



print(

    f"Single-Pareto ODs: "

    f"{single_od} "

    f"({single_od / total_od * 100:.2f}%)"

)



print(

    f"Multi-Pareto ODs: "

    f"{multi_od} "

    f"({multi_od / total_od * 100:.2f}%)"

)



print(

    f"Mean Pareto-set size: "

    f"{od_df['pareto_route_count'].mean():.3f}"

)



print(

    f"Median Pareto-set size: "

    f"{od_df['pareto_route_count'].median():.3f}"

)



print(

    f"Maximum Pareto-set size: "

    f"{max_pareto}"

)





print()

print("=" * 80)

print("TOP 15 ORIGINS BY MULTI-PARETO RATE")

print("=" * 80)



print(



    origin_summary_df



    .sort_values(

        "multi_pareto_percentage",

        ascending=False

    )



    .head(15)



    [

        [

            "origin",

            "multi_pareto_od_count",

            "multi_pareto_percentage",

            "mean_pareto_size",

            "max_pareto_size"

        ]

    ]



    .to_string(

        index=False

    )



)





print()

print("=" * 80)

print("TOP 15 DESTINATIONS BY MULTI-PARETO RATE")

print("=" * 80)



print(



    destination_summary_df



    .sort_values(

        "multi_pareto_percentage",

        ascending=False

    )



    .head(15)



    [

        [

            "destination",

            "multi_pareto_od_count",

            "multi_pareto_percentage",

            "mean_pareto_size",

            "max_pareto_size"

        ]

    ]



    .to_string(

        index=False

    )



)





print()

print("=" * 80)

print("OUTPUT FILES")

print("=" * 80)



print(

    f"OD summary:          {OD_FILE}"

)



print(

    f"Pareto routes:       {ROUTE_FILE}"

)



print(

    f"Source MOSP stats:   {SOURCE_STATS_FILE}"

)



print(

    f"Distribution:        {DISTRIBUTION_FILE}"

)



print(

    f"Origin summary:      {ORIGIN_SUMMARY_FILE}"

)



print(

    f"Destination summary: {DEST_SUMMARY_FILE}"

)



print(

    f"Multi-Pareto ODs:    {MULTI_OD_FILE}"

)



print()



print(

    "Experiment 5 completed successfully."

)