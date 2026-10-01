from dataclasses import dataclass
from collections import defaultdict
import copy
import re

import pandas as pd


# =========================================================
# Basic graph structure compatible with mosp()
# =========================================================

@dataclass
class Edge:
    to: str
    costs: tuple
    kind: str = ""
    info: dict = None


class TransitGraph:

    def __init__(self):
        self.adj = defaultdict(list)

        # node -> metadata
        self.node_info = {}

        # physical station name -> [route/service-state nodes]
        self.states_by_name = defaultdict(list)

    def add_node(self, node, **info):
        if node not in self.adj:
            self.adj[node] = []
        self.node_info[node] = info

    def add_edge(self, u, v, costs, kind="", info=None):
        self.adj[u].append(
            Edge(
                to=v,
                costs=tuple(costs),
                kind=kind,
                info=info or {}
            )
        )

        # Make sure v exists
        if v not in self.adj:
            self.adj[v] = []

    def nodes(self):
        return list(self.adj.keys())

    def neighbors(self, node):
        return self.adj[node]

    def copy(self):
        return copy.deepcopy(self)


# =========================================================
# Helpers
# =========================================================

STATION_PATTERN = re.compile(
    r"\{(\d+),'([^']+)','([^']+)',\}"
)


# =========================================================
# Circular Line (Y) metadata
# =========================================================
#
# The station metadata file used in this project does not contain the
# Circular Line, but the travel-time file does contain the complete
# 13 adjacent segments from 新北產業園區 to 大坪林.
#
# We therefore reconstruct ONE Y service-state from the travel-time
# chain instead of silently discarding those 13 rows.
# =========================================================

CIRCULAR_LINE_STATION_IDS = {
    "大坪林站": "Y07",
    "十四張站": "Y08",
    "秀朗橋站": "Y09",
    "景平站": "Y10",
    "景安站": "Y11",
    "中和站": "Y12",
    "橋和站": "Y13",
    "中原站": "Y14",
    "板新站": "Y15",
    "板橋站": "Y16",
    "新埔民生站": "Y17",
    "頭前庄站": "Y18",
    "幸福站": "Y19",
    "新北產業園區站": "Y20",
}

CIRCULAR_SERVICE_NAME = "新北產業園區-大坪林"


def clean_line_id(value):
    return (
        str(value)
        .strip()
        .strip("'")
        .strip('"')
    )


def clean_station_name(value):
    name = str(value).strip()

    # Example: 捷運台北車站 -> 台北車站
    if name.startswith("捷運"):
        name = name[2:]

    return name


def pair_key(a, b):
    return tuple(sorted((a, b)))


def parse_seconds(value):
    """
    Convert a time value into integer seconds.

    Supported formats:
        102
        102.0
        "102"
        "01:42"
        "00:01:42"
    """
    if pd.isna(value):
        return 0

    text = str(value).strip()

    if text == "":
        return 0

    if ":" in text:
        parts = text.split(":")

        # HH:MM:SS
        if len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return int(
                round(
                    hours * 3600
                    + minutes * 60
                    + seconds
                )
            )

        # MM:SS
        if len(parts) == 2:
            minutes = float(parts[0])
            seconds = float(parts[1])
            return int(
                round(
                    minutes * 60
                    + seconds
                )
            )

    return int(round(float(text)))


def representative_seconds(values):
    """
    If duplicated service-pattern rows give several stop-time
    observations for the same route-state, use the median.
    """
    values = [
        int(value)
        for value in values
        if value is not None
    ]

    if not values:
        return 0

    # In the official file, a zero stop time is also used when a
    # service pattern STARTS at that station.
    #
    # If at least one positive observation exists, estimate the
    # station dwell from positive observations only.
    positive_values = [
        value
        for value in values
        if value > 0
    ]

    if positive_values:
        values = positive_values

    values.sort()
    n = len(values)

    if n % 2 == 1:
        return values[n // 2]

    return int(
        round(
            (
                values[n // 2 - 1]
                + values[n // 2]
            ) / 2
        )
    )


def _parse_route_rows(station_df):
    """
    Parse each row of the station metadata into a route definition.

    Each route definition is a dict with:
        seqno
        line_id
        route_key
        stations = [(order, station_id, station_name), ...]
    """
    routes = []

    for _, row in station_df.iterrows():

        seqno = int(row["SEQNO"])
        line_id = clean_line_id(row["LineID"])
        route_key = f"{line_id}#{seqno}"

        stations = []

        for (
            station_order,
            station_id,
            station_name
        ) in STATION_PATTERN.findall(
            str(row["Stations"])
        ):

            stations.append(
                (
                    int(station_order),
                    station_id,
                    clean_station_name(
                        station_name
                    )
                )
            )

        routes.append(
            {
                "seqno": seqno,
                "line_id": line_id,
                "route_key": route_key,
                "stations": stations,
                "expanded_from_parent": False,
                "parent_route_key": None,
                "junction_station": None,
            }
        )

    return routes


# =========================================================
# Add Circular Line from travel-time data
# =========================================================

def _append_circular_line_route_from_travel_data(
    routes,
    travel_df
):
    """
    Reconstruct the operating first-stage Circular Line
    Y07--Y20 from the adjacent-station rows already present
    in the travel-time CSV.

    The station metadata CSV used by this project contains
    BR/R/G/O/BL and R-3/G-3, but no Y row.

    The travel-time CSV contains:

        新北產業園區 -> ... -> 十四張 -> 大坪林

    Running times and dwell times still come from the
    supplied travel-time CSV.
    """

    # If future metadata already contains Y,
    # do not add it again.
    if any(
        route.get("line_id") == "Y"
        for route in routes
    ):
        return routes, None

    if "stationbus" not in travel_df.columns:
        return routes, None

    circular_rows = travel_df[
        travel_df["stationbus"]
        .astype(str)
        .str.strip()
        == CIRCULAR_SERVICE_NAME
    ].copy()

    if circular_rows.empty:
        return routes, None

    # Preserve order in travel-time data
    if "SeqNo" in circular_rows.columns:
        circular_rows = circular_rows.sort_values(
            "SeqNo"
        )

    station_names = []

    for _, row in circular_rows.iterrows():

        a = clean_station_name(
            row["stationA"]
        )

        b = clean_station_name(
            row["stationB"]
        )

        if not station_names:
            station_names.extend(
                [a, b]
            )
            continue

        if station_names[-1] == a:
            station_names.append(b)

        elif station_names[-1] == b:
            station_names.append(a)

        else:
            raise ValueError(
                "Circular Line travel-time rows "
                "do not form one continuous "
                "station chain."
            )

    # Remove accidental consecutive duplicates
    compact_names = []

    for name in station_names:

        if (
            not compact_names
            or compact_names[-1] != name
        ):
            compact_names.append(name)

    station_names = compact_names

    expected = set(
        CIRCULAR_LINE_STATION_IDS
    )

    actual = set(
        station_names
    )

    if actual != expected:

        missing = sorted(
            expected - actual
        )

        extra = sorted(
            actual - expected
        )

        raise ValueError(
            "Circular Line station chain "
            "does not match Y07--Y20. "
            f"Missing={missing}, "
            f"extra={extra}"
        )

    # Create synthetic Y route
    next_seqno = (
        max(
            route["seqno"]
            for route in routes
        )
        + 1
    )

    route_key = f"Y#{next_seqno}"

    stations = []

    for order, name in enumerate(
        station_names,
        start=1
    ):

        stations.append(
            (
                order,
                CIRCULAR_LINE_STATION_IDS[name],
                name,
            )
        )

    circular_route = {
        "seqno": next_seqno,
        "line_id": "Y",
        "route_key": route_key,
        "stations": stations,
        "expanded_from_parent": False,
        "parent_route_key": None,
        "junction_station": None,
        "synthetic_from_travel_time": True,
    }

    routes = copy.deepcopy(
        routes
    )

    routes.append(
        circular_route
    )

    info = {
        "route_key": route_key,
        "line_id": "Y",
        "service_name":
            CIRCULAR_SERVICE_NAME,
        "station_count":
            len(stations),
        "segment_count":
            max(
                0,
                len(stations) - 1
            ),
        "stations": [
            name
            for _, _, name
            in stations
        ],
    }

    return routes, info


# =========================================================
# Expand same-line branch services
# =========================================================

def _expand_same_line_branch_services(
    routes
):
    """
    Expand a branch row that starts at a junction
    on another row of the SAME LineID.

    Example:

        O#4 :
        南勢角 ... 大橋頭 ... 迴龍

        O#5 :
                    大橋頭 ... 蘆洲

    The travel-time file contains through service
    南勢角-蘆洲.

    Therefore O#5 is expanded to:

        南勢角 ... 大橋頭 ... 蘆洲

    O#4 and O#5 remain DISTINCT service states.

    R-3 and G-3 are NOT expanded because their
    LineID differs from the main line.
    """

    expanded = copy.deepcopy(
        routes
    )

    by_line = defaultdict(list)

    for route in expanded:

        by_line[
            route["line_id"]
        ].append(route)

    for (
        line_id,
        line_routes
    ) in by_line.items():

        if len(line_routes) < 2:
            continue

        line_routes_sorted = sorted(
            line_routes,
            key=lambda r: len(
                r["stations"]
            )
        )

        for child in line_routes_sorted:

            if not child["stations"]:
                continue

            child_first = (
                child["stations"][0]
            )

            child_first_order = (
                child_first[0]
            )

            child_first_id = (
                child_first[1]
            )

            child_first_name = (
                child_first[2]
            )

            # Branch row begins at order > 1
            if child_first_order <= 1:
                continue

            best_parent = None
            best_parent_index = None

            for parent in line_routes:

                if (
                    parent["route_key"]
                    == child["route_key"]
                ):
                    continue

                for (
                    idx,
                    station
                ) in enumerate(
                    parent["stations"]
                ):

                    (
                        order,
                        station_id,
                        station_name
                    ) = station

                    if (
                        order
                        == child_first_order
                        and station_id
                        == child_first_id
                        and station_name
                        == child_first_name
                    ):

                        if idx > 0:

                            if (
                                best_parent
                                is None
                                or idx
                                > best_parent_index
                            ):
                                best_parent = parent
                                best_parent_index = idx

                        break

            if best_parent is None:
                continue

            parent_prefix = (
                best_parent[
                    "stations"
                ][
                    :best_parent_index + 1
                ]
            )

            child_tail = (
                child[
                    "stations"
                ][1:]
            )

            child["stations"] = (
                parent_prefix
                + child_tail
            )

            child[
                "expanded_from_parent"
            ] = True

            child[
                "parent_route_key"
            ] = best_parent[
                "route_key"
            ]

            child[
                "junction_station"
            ] = child_first_name

    return expanded


# =========================================================
# Build Taipei Metro graph
# =========================================================

def build_taipei_metro_graph(
    station_file,
    travel_time_file,
    transfer_file,
    include_circular_line=True,
    dapinglin_transfer_minutes=3.0,
):

    # -----------------------------------------------------
    # 0. Read CSV
    # -----------------------------------------------------

    station_df = pd.read_csv(
        station_file,
        encoding="utf-8-sig"
    )

    travel_df = pd.read_csv(
        travel_time_file,
        encoding="cp950"
    )

    transfer_df = pd.read_csv(
        transfer_file,
        encoding="cp950"
    )

    # Remove accidental spaces
    station_df.columns = [
        str(col).strip()
        for col
        in station_df.columns
    ]

    travel_df.columns = [
        str(col).strip()
        for col
        in travel_df.columns
    ]

    transfer_df.columns = [
        str(col).strip()
        for col
        in transfer_df.columns
    ]

    # -----------------------------------------------------
    # Check required columns
    # -----------------------------------------------------

    required_station_columns = {
        "SEQNO",
        "LineID",
        "Stations"
    }

    required_travel_columns = {
        "stationA",
        "stationB",
        "traveltime",
        "stoptime"
    }

    required_transfer_columns = {
        "station",
        "Time"
    }

    missing = (
        required_station_columns
        - set(station_df.columns)
    )

    if missing:
        raise ValueError(
            "Station file missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    missing = (
        required_travel_columns
        - set(travel_df.columns)
    )

    if missing:
        raise ValueError(
            "Travel-time file missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    missing = (
        required_transfer_columns
        - set(transfer_df.columns)
    )

    if missing:
        raise ValueError(
            "Transfer file missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    graph = TransitGraph()

    # =====================================================
    # 1. Parse route/service states
    # =====================================================

    raw_routes = _parse_route_rows(
        station_df
    )

    # -----------------------------------------------------
    # Add Circular Line Y
    # -----------------------------------------------------

    circular_route_info = None

    if include_circular_line:

        (
            raw_routes,
            circular_route_info
        ) = (
            _append_circular_line_route_from_travel_data(
                raw_routes,
                travel_df,
            )
        )

    # -----------------------------------------------------
    # Expand Orange Line branch services
    # -----------------------------------------------------

    routes = (
        _expand_same_line_branch_services(
            raw_routes
        )
    )

    pair_to_states = defaultdict(
        list
    )

    expanded_routes = []

    # -----------------------------------------------------
    # Create route-state nodes
    # -----------------------------------------------------

    for route in routes:

        line_id = route[
            "line_id"
        ]

        route_key = route[
            "route_key"
        ]

        route_nodes = []

        if route[
            "expanded_from_parent"
        ]:

            expanded_routes.append(
                {
                    "route_key":
                        route_key,

                    "parent_route_key":
                        route[
                            "parent_route_key"
                        ],

                    "junction_station":
                        route[
                            "junction_station"
                        ],
                }
            )

        for (
            station_order,
            station_id,
            station_name
        ) in route["stations"]:

            node = (
                f"{station_id}"
                f"@{route_key}"
            )

            graph.add_node(
                node,

                kind="station",

                station_id=
                    station_id,

                station_name=
                    station_name,

                line_id=
                    line_id,

                route_key=
                    route_key,

                station_order=
                    int(
                        station_order
                    ),

                stop_time=0,

                expanded_service=
                    route[
                        "expanded_from_parent"
                    ],

                parent_route_key=
                    route[
                        "parent_route_key"
                    ],

                synthetic_from_travel_time=
                    route.get(
                        "synthetic_from_travel_time",
                        False,
                    ),
            )

            graph.states_by_name[
                station_name
            ].append(
                node
            )

            route_nodes.append(
                node
            )

        # Record adjacent route-state pairs
        for (
            u,
            v
        ) in zip(
            route_nodes,
            route_nodes[1:]
        ):

            name_u = (
                graph.node_info[u][
                    "station_name"
                ]
            )

            name_v = (
                graph.node_info[v][
                    "station_name"
                ]
            )

            key = pair_key(
                name_u,
                name_v
            )

            pair_to_states[
                key
            ].append(
                (u, v)
            )

    # =====================================================
    # 2. Read station stop times
    # =====================================================

    stop_time_samples = defaultdict(
        list
    )

    for _, row in travel_df.iterrows():

        station_a = (
            clean_station_name(
                row["stationA"]
            )
        )

        station_b = (
            clean_station_name(
                row["stationB"]
            )
        )

        stop_time = (
            parse_seconds(
                row["stoptime"]
            )
        )

        key = pair_key(
            station_a,
            station_b
        )

        state_pairs = (
            pair_to_states.get(
                key,
                []
            )
        )

        for (
            u,
            v
        ) in state_pairs:

            name_u = (
                graph.node_info[u][
                    "station_name"
                ]
            )

            name_v = (
                graph.node_info[v][
                    "station_name"
                ]
            )

            # stationA corresponds to u
            if (
                name_u == station_a
                and name_v == station_b
            ):

                stop_time_samples[
                    u
                ].append(
                    stop_time
                )

            # stationA corresponds to v
            elif (
                name_v == station_a
                and name_u == station_b
            ):

                stop_time_samples[
                    v
                ].append(
                    stop_time
                )

    # -----------------------------------------------------
    # Determine stop time for each route-state
    # -----------------------------------------------------

    state_stop_times = {}

    for node in graph.nodes():

        info = graph.node_info.get(
            node,
            {}
        )

        if (
            info.get("kind")
            != "station"
        ):
            continue

        stop_time = (
            representative_seconds(
                stop_time_samples.get(
                    node,
                    []
                )
            )
        )

        state_stop_times[
            node
        ] = stop_time

        graph.node_info[
            node
        ][
            "stop_time"
        ] = stop_time

    # =====================================================
    # 3. Ride edges
    # =====================================================
    #
    # Objectives:
    #
    # C1 =
    # running time
    # + station dwell
    # + transfer walking
    #
    # C2 =
    # number of transfers
    #
    # C3 =
    # transfer walking time
    #
    # Ride edge:
    #
    # (
    #   running + departure dwell,
    #   0,
    #   0
    # )
    # =====================================================

    ride_pairs_added = set()

    skipped_travel_rows = []

    for _, row in travel_df.iterrows():

        station_a = (
            clean_station_name(
                row["stationA"]
            )
        )

        station_b = (
            clean_station_name(
                row["stationB"]
            )
        )

        travel_time = (
            parse_seconds(
                row["traveltime"]
            )
        )

        key = pair_key(
            station_a,
            station_b
        )

        state_pairs = (
            pair_to_states.get(
                key,
                []
            )
        )

        if not state_pairs:

            skipped_travel_rows.append(
                (
                    station_a,
                    station_b
                )
            )

            continue

        for (
            u,
            v
        ) in state_pairs:

            undirected_key = (
                tuple(
                    sorted(
                        (u, v)
                    )
                )
            )

            # Avoid duplicate ride edges
            if (
                undirected_key
                in ride_pairs_added
            ):
                continue

            ride_pairs_added.add(
                undirected_key
            )

            stop_u = (
                state_stop_times.get(
                    u,
                    0
                )
            )

            stop_v = (
                state_stop_times.get(
                    v,
                    0
                )
            )

            # ---------------------------------------------
            # u -> v
            # ---------------------------------------------

            total_time_uv = (
                stop_u
                + travel_time
            )

            graph.add_edge(
                u,
                v,

                (
                    total_time_uv,
                    0,
                    0
                ),

                kind="ride",

                info={
                    "travel_time":
                        travel_time,

                    "stop_time":
                        stop_u,

                    "total_time":
                        total_time_uv,
                }
            )

            # ---------------------------------------------
            # v -> u
            # ---------------------------------------------

            total_time_vu = (
                stop_v
                + travel_time
            )

            graph.add_edge(
                v,
                u,

                (
                    total_time_vu,
                    0,
                    0
                ),

                kind="ride",

                info={
                    "travel_time":
                        travel_time,

                    "stop_time":
                        stop_v,

                    "total_time":
                        total_time_vu,
                }
            )

    # =====================================================
    # 4. Transfer edges
    # =====================================================
    #
    # Transfer edge:
    #
    # (
    #   walking time,
    #   1,
    #   walking time
    # )
    #
    # Orange:
    #
    # O#4 and O#5 are separate through-service states.
    #
    # Staying on the same service does NOT require transfer.
    #
    # Switching branch service at 大橋頭 counts as transfer.
    # =====================================================

    transfer_edges_added = 0

    special_transfer_edges_added = 0

    transfer_assumptions = []

    # -----------------------------------------------------
    # Helper for adding transfer edge
    # -----------------------------------------------------

    def add_transfer_edge(
        u,
        v,
        walking_seconds,
        station_label,
        source
    ):

        nonlocal transfer_edges_added
        nonlocal special_transfer_edges_added

        # Avoid duplicate directed transfer edge
        for edge in graph.adj[u]:

            if (
                edge.to == v
                and edge.kind
                == "transfer"
            ):
                return False

        info_u = graph.node_info[
            u
        ]

        info_v = graph.node_info[
            v
        ]

        graph.add_edge(
            u,
            v,

            (
                walking_seconds,
                1,
                walking_seconds
            ),

            kind="transfer",

            info={
                "station_name":
                    station_label,

                "walking_seconds":
                    walking_seconds,

                "from_line":
                    info_u.get(
                        "line_id"
                    ),

                "to_line":
                    info_v.get(
                        "line_id"
                    ),

                "from_route":
                    info_u.get(
                        "route_key"
                    ),

                "to_route":
                    info_v.get(
                        "route_key"
                    ),

                "transfer_source":
                    source,
            },
        )

        transfer_edges_added += 1

        if (
            source
            != "transfer_csv_same_station"
        ):
            special_transfer_edges_added += 1

        return True

    # -----------------------------------------------------
    # 4A. Same physical station transfers
    # -----------------------------------------------------

    for _, row in transfer_df.iterrows():

        station_name = (
            clean_station_name(
                row["station"]
            )
        )

        walking_minutes = float(
            row["Time"]
        )

        walking_seconds = int(
            round(
                walking_minutes
                * 60
            )
        )

        states = (
            graph.states_by_name.get(
                station_name,
                []
            )
        )

        if len(states) < 2:
            continue

        for u in states:

            for v in states:

                if u == v:
                    continue

                info_u = (
                    graph.node_info[u]
                )

                info_v = (
                    graph.node_info[v]
                )

                # Same route state -> no transfer
                if (
                    info_u.get(
                        "route_key"
                    )
                    == info_v.get(
                        "route_key"
                    )
                ):
                    continue

                # -----------------------------------------
                # Special Orange-Line logic
                # -----------------------------------------
                #
                # O#4 and O#5 coexist on the common trunk.
                #
                # The transfer-time table contains physical
                # interchange stations such as:
                #
                # 民權西路
                # 松江南京
                # 忠孝新生
                # 東門
                # 古亭
                #
                # Their transfer time describes transfer
                # between DIFFERENT lines.
                #
                # It must NOT create fake O#4 <-> O#5
                # transfers at those stations.
                #
                # Same-LineID service switching is allowed
                # only at the real branch junction.
                # -----------------------------------------

                same_line_id = (
                    info_u.get(
                        "line_id"
                    )
                    == info_v.get(
                        "line_id"
                    )
                )

                if same_line_id:

                    allowed_same_line_junction = False

                    for expanded in expanded_routes:

                        if (
                            station_name
                            != expanded[
                                "junction_station"
                            ]
                        ):
                            continue

                        route_pair = {
                            expanded[
                                "route_key"
                            ],
                            expanded[
                                "parent_route_key"
                            ],
                        }

                        current_pair = {
                            info_u.get(
                                "route_key"
                            ),
                            info_v.get(
                                "route_key"
                            ),
                        }

                        if (
                            current_pair
                            == route_pair
                        ):

                            allowed_same_line_junction = True
                            break

                    if (
                        not
                        allowed_same_line_junction
                    ):
                        continue

                add_transfer_edge(
                    u,
                    v,
                    walking_seconds,
                    station_name,
                    source=
                        "transfer_csv_same_station",
                )

    # =====================================================
    # 4B. Circular-Line special interchanges
    # =====================================================
    #
    # 新埔 BL08 <-> 新埔民生 Y17
    #
    # These are different physical station names,
    # therefore generic same-name logic cannot connect them.
    #
    # The supplied transfer CSV gives 9 minutes.
    #
    # 大坪林 G04 <-> Y07
    #
    # It is an interchange but is absent from the supplied
    # transfer-walking CSV.
    #
    # Therefore dapinglin_transfer_minutes is an explicit
    # modelling parameter.
    # =====================================================

    if (
        include_circular_line
        and circular_route_info
        is not None
    ):

        # -------------------------------------------------
        # Read transfer times by station name
        # -------------------------------------------------

        transfer_time_by_name = {}

        for _, row in transfer_df.iterrows():

            name = (
                clean_station_name(
                    row["station"]
                )
            )

            transfer_time_by_name[
                name
            ] = int(
                round(
                    float(
                        row["Time"]
                    )
                    * 60
                )
            )

        # -------------------------------------------------
        # 新埔 BL <-> 新埔民生 Y
        # -------------------------------------------------

        xinpu_seconds = (
            transfer_time_by_name.get(
                "新埔站"
            )
        )

        xinpu_minsheng_seconds = (
            transfer_time_by_name.get(
                "新埔民生站"
            )
        )

        if (
            xinpu_seconds
            is not None
            and
            xinpu_minsheng_seconds
            is not None
        ):

            walking_seconds = int(
                round(
                    (
                        xinpu_seconds
                        + xinpu_minsheng_seconds
                    ) / 2
                )
            )

            bl_states = [
                node
                for node
                in graph.states_by_name.get(
                    "新埔站",
                    []
                )
                if graph.node_info[
                    node
                ].get(
                    "line_id"
                ) == "BL"
            ]

            y_states = [
                node
                for node
                in graph.states_by_name.get(
                    "新埔民生站",
                    []
                )
                if graph.node_info[
                    node
                ].get(
                    "line_id"
                ) == "Y"
            ]

            for u in bl_states:

                for v in y_states:

                    add_transfer_edge(
                        u,
                        v,
                        walking_seconds,
                        "新埔站<->新埔民生站",
                        source=
                            "transfer_csv_cross_station",
                    )

                    add_transfer_edge(
                        v,
                        u,
                        walking_seconds,
                        "新埔民生站<->新埔站",
                        source=
                            "transfer_csv_cross_station",
                    )

        # -------------------------------------------------
        # 大坪林 G <-> Y
        # -------------------------------------------------

        if (
            dapinglin_transfer_minutes
            is not None
        ):

            walking_seconds = int(
                round(
                    float(
                        dapinglin_transfer_minutes
                    )
                    * 60
                )
            )

            g_states = [
                node
                for node
                in graph.states_by_name.get(
                    "大坪林站",
                    []
                )
                if graph.node_info[
                    node
                ].get(
                    "line_id"
                ) == "G"
            ]

            y_states = [
                node
                for node
                in graph.states_by_name.get(
                    "大坪林站",
                    []
                )
                if graph.node_info[
                    node
                ].get(
                    "line_id"
                ) == "Y"
            ]

            added = 0

            for u in g_states:

                for v in y_states:

                    added += int(
                        add_transfer_edge(
                            u,
                            v,
                            walking_seconds,
                            "大坪林站",
                            source=
                                "explicit_assumption",
                        )
                    )

                    added += int(
                        add_transfer_edge(
                            v,
                            u,
                            walking_seconds,
                            "大坪林站",
                            source=
                                "explicit_assumption",
                        )
                    )

            if added:

                transfer_assumptions.append(
                    {
                        "station":
                            "大坪林站",

                        "lines":
                            ("G", "Y"),

                        "walking_minutes":
                            float(
                                dapinglin_transfer_minutes
                            ),

                        "reason":
                            (
                                "official interchange exists "
                                "but the supplied "
                                "transfer-walking CSV "
                                "has no Dapinglin row"
                            ),
                    }
                )

    # =====================================================
    # 5. Build statistics
    # =====================================================

    station_nodes = [
        node
        for node
        in graph.nodes()
        if graph.node_info.get(
            node,
            {}
        ).get(
            "kind"
        ) == "station"
    ]

    states_with_positive_stop_time = sum(
        1
        for node
        in station_nodes
        if state_stop_times.get(
            node,
            0
        ) > 0
    )

    states_with_zero_stop_time = (
        len(station_nodes)
        - states_with_positive_stop_time
    )

    states_without_stop_time_data = [
        node
        for node
        in station_nodes
        if node
        not in stop_time_samples
    ]

    build_stats = {
        "nodes":
            len(
                graph.nodes()
            ),

        "ride_segments":
            len(
                ride_pairs_added
            ),

        "ride_directed_edges":
            len(
                ride_pairs_added
            ) * 2,

        "transfer_directed_edges":
            transfer_edges_added,

        "states_with_positive_stop_time":
            states_with_positive_stop_time,

        "states_with_zero_stop_time":
            states_with_zero_stop_time,

        "states_without_stop_time_data":
            states_without_stop_time_data,

        "skipped_travel_rows":
            len(
                skipped_travel_rows
            ),

        "skipped_pairs":
            sorted(
                set(
                    skipped_travel_rows
                )
            ),

        "expanded_routes":
            expanded_routes,

        "circular_line_included":
            bool(
                include_circular_line
                and
                circular_route_info
                is not None
            ),

        "circular_route_info":
            circular_route_info,

        "special_transfer_directed_edges":
            special_transfer_edges_added,

        "transfer_assumptions":
            transfer_assumptions,
    }

    return graph, build_stats


# =========================================================
# Add physical OD
# =========================================================

def make_od_graph(
    base_graph,
    origin_name,
    destination_name
):

    graph = base_graph.copy()

    origin_name = (
        clean_station_name(
            origin_name
        )
    )

    destination_name = (
        clean_station_name(
            destination_name
        )
    )

    if (
        origin_name
        not in graph.states_by_name
    ):
        raise ValueError(
            f"Unknown origin: "
            f"{origin_name}"
        )

    if (
        destination_name
        not in graph.states_by_name
    ):
        raise ValueError(
            f"Unknown destination: "
            f"{destination_name}"
        )

    source = (
        f"__SOURCE__::"
        f"{origin_name}"
    )

    target = (
        f"__TARGET__::"
        f"{destination_name}"
    )

    graph.add_node(
        source,
        kind="virtual_source",
        station_name=
            origin_name
    )

    graph.add_node(
        target,
        kind="virtual_target",
        station_name=
            destination_name
    )

    # =====================================================
    # Remove stop time at trip origin
    # =====================================================
    #
    # Base ride edge:
    #
    # stop_time(origin)
    # + travel_time
    #
    # Passenger beginning trip should not be charged the
    # station dwell before departure.
    # =====================================================

    for state in graph.states_by_name[
        origin_name
    ]:

        for edge in graph.adj[
            state
        ]:

            if edge.kind != "ride":
                continue

            travel_time = int(
                edge.info.get(
                    "travel_time",
                    edge.costs[0]
                )
            )

            edge.costs = (
                travel_time,
                edge.costs[1],
                edge.costs[2]
            )

            edge.info[
                "origin_stop_time_removed"
            ] = True

            edge.info[
                "total_time"
            ] = travel_time

    # -----------------------------------------------------
    # Virtual source
    # -----------------------------------------------------
    #
    # Starting on any service at origin
    # does NOT count as transfer.
    # -----------------------------------------------------

    for state in graph.states_by_name[
        origin_name
    ]:

        graph.add_edge(
            source,
            state,
            (0, 0, 0),
            kind="access"
        )

    # -----------------------------------------------------
    # Virtual destination
    # -----------------------------------------------------

    for state in graph.states_by_name[
        destination_name
    ]:

        graph.add_edge(
            state,
            target,
            (0, 0, 0),
            kind="egress"
        )

    return (
        graph,
        source,
        target
    )


# =========================================================
# Human-readable path
# =========================================================

def format_path(
    graph,
    path
):

    result = []

    for node in path:

        info = (
            graph.node_info.get(
                node,
                {}
            )
        )

        # Ignore virtual source / target
        if (
            info.get("kind")
            != "station"
        ):
            continue

        station = (
            info[
                "station_name"
            ]
        )

        line = (
            info[
                "line_id"
            ]
        )

        route_key = (
            info.get(
                "route_key",
                line
            )
        )

        # If a physical station contains more than one
        # service state with the same LineID
        # (currently Orange O#4/O#5),
        # show route_key for debugging.

        same_line_states = [
            state
            for state
            in graph.states_by_name.get(
                station,
                []
            )
            if graph.node_info.get(
                state,
                {}
            ).get(
                "line_id"
            ) == line
        ]

        if (
            len(
                same_line_states
            ) > 1
        ):
            label = route_key

        else:
            label = line

        result.append(
            f"{station}[{label}]"
        )

    return " -> ".join(
        result
    )