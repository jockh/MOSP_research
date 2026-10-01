from __future__ import annotations

import ast
import io
import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pandas as pd
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from src.paths import PROJECT_ROOT, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, project_path


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(Path(__file__).resolve().parent / ".env")

APP_DIR = Path(__file__).resolve().parent

CACHE_DIR = APP_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# OFFICIAL TAIPEI METRO STATION COORDINATES
# ============================================================

OFFICIAL_STATION_CSV_URL = (
    "https://data.taipei/api/frontstage/tpeod/dataset/"
    "resource.download?rid=c77e91bf-067c-475e-917b-545ff62b7d76"
)
# ============================================================
# NEW TAIPEI METRO CIRCULAR LINE
# FALLBACK COORDINATES
#
# These 10 stations are not included in the current
# Taipei City station-coordinate CSV used by this demo.
#
# Coordinate order here:
#     latitude, longitude
# ============================================================

CIRCULAR_LINE_FALLBACK = {
    "十四張站": {
        "lat": 24.98447,
        "lon": 121.52759,
    },

    "秀朗橋站": {
        "lat": 24.99033,
        "lon": 121.52490,
    },

    "景平站": {
        "lat": 24.99215,
        "lon": 121.51617,
    },

    "中和站": {
        "lat": 25.00236,
        "lon": 121.49621,
    },

    "橋和站": {
        "lat": 25.00460,
        "lon": 121.49025,
    },

    "中原站": {
        "lat": 25.00818,
        "lon": 121.48427,
    },

    "板新站": {
        "lat": 25.01453,
        "lon": 121.47242,
    },

    "新埔民生站": {
        "lat": 25.02613,
        "lon": 121.46667,
    },

    "幸福站": {
        "lat": 25.04999,
        "lon": 121.45997,
    },

    "新北產業園區站": {
        "lat": 25.06127,
        "lon": 121.45981,
    },
}


# ============================================================
# REQUIRED PARETO ROUTE COLUMNS
# ============================================================


REQUIRED_ROUTE_COLUMNS = {
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


# ============================================================
# PATH TOKEN
#
# Example:
#
# 東湖站[BR#1]
#
# station = 東湖站
# state   = BR#1
# ============================================================

TOKEN_RE = re.compile(r"^(.*?)\[([^\]]+)\]$")


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Taipei Pareto Route Explorer API",
    version="0.3.0",
)


def frontend_origins() -> list[str]:
    # Local development remains available alongside the configured static site.
    origins = ["http://localhost:5173"]
    for value in os.getenv("FRONTEND_ORIGIN", "").split(","):
        origin = value.strip().rstrip("/")
        if not origin:
            continue
        parsed = urlsplit(origin)
        if (parsed.scheme not in {"http", "https"} or not parsed.netloc
                or parsed.path or parsed.query or parsed.fragment
                or parsed.username or parsed.password):
            raise ValueError("FRONTEND_ORIGIN must contain HTTP(S) origins without paths")
        if origin not in origins:
            origins.append(origin)
    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# FIND PROJECT FILES
# ============================================================

def find_upwards(relative: Path) -> Path | None:
    candidate = PROJECT_ROOT / relative
    return candidate.resolve() if candidate.is_file() else None


# ============================================================
# LOCATE PARETO CSV
# ============================================================

def locate_pareto_csv() -> Path | None:
    override = os.getenv("PARETO_CSV")
    path = project_path(override) if override else ALL_OD_RESULTS_DIR / "all_od_pareto_routes.csv"
    return path.resolve() if path.is_file() else None


# ============================================================
# LOCATE STATION COORDINATE CSV
#
# IMPORTANT:
# Do NOT treat
# 臺北捷運路線車站資料服務_NEW_fixed (1).csv
# as a coordinate file.
#
# That file is used for MOSP topology / route-state data.
# ============================================================

def locate_station_csv() -> Path | None:
    override = os.getenv("STATION_POSITION_CSV")
    path = project_path(override) if override else TAIPEI_METRO_DATA_DIR / "taipei_metro_station_positions.csv"
    return path.resolve() if path.is_file() else None


PARETO_CSV = locate_pareto_csv()


# ============================================================
# CSV HELPERS
# ============================================================

def read_csv_flexible_bytes(
    content: bytes,
) -> pd.DataFrame:

    last_error = None

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp950",
        "big5",
    ]

    for encoding in encodings:

        try:

            return pd.read_csv(
                io.BytesIO(content),
                encoding=encoding,
            )

        except Exception as exc:

            last_error = exc

    if last_error is not None:
        raise last_error

    raise ValueError(
        "Unable to decode CSV."
    )


def read_csv_flexible_path(
    path: Path,
) -> pd.DataFrame:

    return read_csv_flexible_bytes(
        path.read_bytes()
    )


# ============================================================
# GET STATION COORDINATE CSV
# ============================================================

def get_station_csv() -> Path:

    # --------------------------------------------------------
    # 1. User/local coordinate CSV
    # --------------------------------------------------------

    local = locate_station_csv()

    if local is not None:
        return local

    # --------------------------------------------------------
    # 2. Cached Taipei Open Data CSV
    # --------------------------------------------------------

    cached = (
        CACHE_DIR
        / "taipei_metro_station_positions.csv"
    )

    if cached.exists():
        return cached

    # --------------------------------------------------------
    # 3. Download Taipei Open Data
    # --------------------------------------------------------

    try:

        response = requests.get(
            OFFICIAL_STATION_CSV_URL,
            timeout=20,
        )

    except requests.exceptions.SSLError:

        # Some Windows Python installations fail certificate
        # validation for data.taipei.
        #
        # This is only used as a fallback for this public
        # government dataset.

        response = requests.get(
            OFFICIAL_STATION_CSV_URL,
            timeout=20,
            verify=False,
        )

    response.raise_for_status()

    cached.write_bytes(
        response.content
    )

    return cached


# ============================================================
# NORMALIZE STATION NAME
# ============================================================

def normalize_name(
    value: Any,
) -> str:

    text = str(value).strip()

    if (
        not text
        or text.lower() == "nan"
    ):
        return ""

    # 臺北 -> 台北
    text = text.replace(
        "臺",
        "台",
    )

    # Remove whitespace
    text = re.sub(
        r"\s+",
        "",
        text,
    )

    # 捷運東湖站 -> 東湖站
    if text.startswith("捷運"):
        text = text[2:]

    # 東湖站 -> 東湖
    if text.endswith("站"):
        text = text[:-1]

    return text


# ============================================================
# PARSE MULTILINGUAL STATION NAME
#
# Taipei Open Data actual format:
#
# "'{動物園,Taipei Zoo}'"
#
# "'{台北車站,Taipei Main Station}'"
#
# ============================================================

def parse_multilingual_name(
    value: Any,
) -> str:

    text = str(value).strip()

    if (
        not text
        or text.lower() == "nan"
    ):
        return ""

    # --------------------------------------------------------
    # Taipei Open Data format
    # --------------------------------------------------------

    cleaned = (
        text
        .strip()
        .strip('"')
        .strip("'")
        .strip()
    )

    if (
        cleaned.startswith("{")
        and cleaned.endswith("}")
    ):

        inside = cleaned[1:-1]

        chinese_name = (
            inside
            .split(",", 1)[0]
            .strip()
        )

        if chinese_name:
            return chinese_name

    # --------------------------------------------------------
    # JSON dictionary fallback
    # --------------------------------------------------------

    try:

        obj = json.loads(text)

        if isinstance(obj, dict):

            for key in [
                "Zh_tw",
                "Zh_TW",
                "zh_tw",
                "zh-TW",
                "Name",
            ]:

                value = obj.get(key)

                if value:
                    return str(value).strip()

    except Exception:
        pass

    # --------------------------------------------------------
    # Python dictionary fallback
    # --------------------------------------------------------

    try:

        obj = ast.literal_eval(text)

        if isinstance(obj, dict):

            for key in [
                "Zh_tw",
                "Zh_TW",
                "zh_tw",
                "zh-TW",
                "Name",
            ]:

                value = obj.get(key)

                if value:
                    return str(value).strip()

    except Exception:
        pass

    # --------------------------------------------------------
    # Plain text fallback
    # --------------------------------------------------------

    return cleaned


# ============================================================
# PARSE COORDINATE
#
# Taipei Open Data format:
#
# "'{121.579501,24.998205}'"
#
# order:
#
# longitude, latitude
#
# Leaflet needs:
#
# latitude, longitude
# ============================================================

def parse_position(
    value: Any,
) -> tuple[float, float] | None:

    text = str(value).strip()

    if (
        not text
        or text.lower() == "nan"
    ):
        return None

    # --------------------------------------------------------
    # 1. Taipei Open Data format
    # --------------------------------------------------------

    cleaned = (
        text
        .strip()
        .strip('"')
        .strip("'")
        .strip()
    )

    if (
        cleaned.startswith("{")
        and cleaned.endswith("}")
    ):

        inside = cleaned[1:-1]

        parts = [
            x.strip()
            for x in inside.split(",")
        ]

        if len(parts) == 2:

            try:

                first = float(parts[0])
                second = float(parts[1])

                # Taipei coordinates:
                #
                # longitude ~ 121
                # latitude  ~ 25

                if (
                    120 <= first <= 123
                    and 24 <= second <= 26
                ):

                    lon = first
                    lat = second

                    return lat, lon

                if (
                    24 <= first <= 26
                    and 120 <= second <= 123
                ):

                    lat = first
                    lon = second

                    return lat, lon

            except ValueError:
                pass

    # --------------------------------------------------------
    # 2. JSON dict
    # --------------------------------------------------------

    try:

        obj = json.loads(text)

        if isinstance(obj, dict):

            lon = (
                obj.get("PositionLon")
                or obj.get("lon")
                or obj.get("lng")
                or obj.get("Longitude")
            )

            lat = (
                obj.get("PositionLat")
                or obj.get("lat")
                or obj.get("Latitude")
            )

            if (
                lon is not None
                and lat is not None
            ):

                return (
                    float(lat),
                    float(lon),
                )

    except Exception:
        pass

    # --------------------------------------------------------
    # 3. Named longitude / latitude
    # --------------------------------------------------------

    lon_match = re.search(
        r"""PositionLon["']?\s*[:=]\s*([0-9.]+)""",
        text,
    )

    lat_match = re.search(
        r"""PositionLat["']?\s*[:=]\s*([0-9.]+)""",
        text,
    )

    if (
        lon_match
        and lat_match
    ):

        return (
            float(lat_match.group(1)),
            float(lon_match.group(1)),
        )

    # --------------------------------------------------------
    # 4. Generic numeric fallback
    # --------------------------------------------------------

    numbers = [
        float(x)
        for x in re.findall(
            r"-?\d+(?:\.\d+)?",
            text,
        )
    ]

    lat = next(
        (
            x
            for x in numbers
            if 24 <= x <= 26
        ),
        None,
    )

    lon = next(
        (
            x
            for x in numbers
            if 120 <= x <= 123
        ),
        None,
    )

    if (
        lat is not None
        and lon is not None
    ):

        return lat, lon

    return None


# ============================================================
# LINE HELPERS
# ============================================================

def clean_line(
    raw: str,
) -> str:

    line = str(raw).strip()

    # Example:
    #
    # BR#1 -> BR
    # BL#2 -> BL

    if "#" in line:
        line = line.split(
            "#",
            1,
        )[0]

    return line


# ============================================================
# PARSE ROUTE PATH
# ============================================================

def parse_path(
    path_text: str,
) -> list[dict[str, str]]:

    items: list[dict[str, str]] = []

    for token in str(
        path_text
    ).split("->"):

        token = token.strip()

        if not token:
            continue

        match = TOKEN_RE.match(
            token
        )

        if match:

            station = (
                match
                .group(1)
                .strip()
            )

            state = (
                match
                .group(2)
                .strip()
            )

            items.append(
                {
                    "station": station,
                    "line": clean_line(state),
                    "state": state,
                }
            )

        else:

            items.append(
                {
                    "station": token,
                    "line": "",
                    "state": "",
                }
            )

    # Remove virtual MOSP source / target nodes

    return [
        item
        for item in items
        if not item[
            "station"
        ].startswith("__SOURCE__")
        and not item[
            "station"
        ].startswith("__TARGET__")
    ]


# ============================================================
# LOAD PARETO ROUTES
# ============================================================

@lru_cache(maxsize=1)
def routes_df() -> pd.DataFrame:

    if PARETO_CSV is None:

        raise FileNotFoundError(
            "Cannot find all_od_pareto_routes.csv. "
            "Use the canonical web/taipei-pareto-explorer folder "
            "or set PARETO_CSV in backend/.env."
        )

    df = read_csv_flexible_path(
        PARETO_CSV
    )

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    missing = (
        REQUIRED_ROUTE_COLUMNS
        - set(df.columns)
    )

    if missing:

        raise ValueError(
            "Pareto CSV missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    df = df.copy()

    for column in [
        "origin",
        "destination",
        "path",
    ]:

        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
        )

    return df


# ============================================================
# LOAD STATION COORDINATES
# ============================================================

@lru_cache(maxsize=1)
def coordinate_lookup() -> dict[
    str,
    dict[str, Any],
]:

    station_path = get_station_csv()

    df = read_csv_flexible_path(
        station_path
    )

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    required = {
        "StationName",
        "StationPosition",
    }

    missing = (
        required
        - set(df.columns)
    )

    if missing:

        raise ValueError(
            "Station coordinate CSV missing columns "
            f"{sorted(missing)}: "
            f"{station_path}"
        )

    lookup: dict[
        str,
        dict[str, Any],
    ] = {}

    # ========================================================
    # 1. Taipei Metro coordinate CSV
    # ========================================================

    for _, row in df.iterrows():

        name = parse_multilingual_name(
            row["StationName"]
        )

        position = parse_position(
            row["StationPosition"]
        )

        if (
            not name
            or position is None
        ):
            continue

        lat, lon = position

        key = normalize_name(
            name
        )

        if not key:
            continue

        lookup[key] = {
            "name": name,
            "lat": lat,
            "lon": lon,
            "source": "taipei_open_data",
        }

    # ========================================================
    # 2. New Taipei Metro Circular Line fallback
    # ========================================================

    for (
        station_name,
        coordinate,
    ) in CIRCULAR_LINE_FALLBACK.items():

        key = normalize_name(
            station_name
        )

        # Only fill stations that are not already available
        # from the primary coordinate dataset.

        if key not in lookup:

            lookup[key] = {
                "name": station_name,
                "lat": coordinate["lat"],
                "lon": coordinate["lon"],
                "source": (
                    "new_taipei_circular_fallback"
                ),
            }

    return lookup
# ============================================================
# RESOLVE ONE MOSP STATION TO COORDINATE
# ============================================================

def resolve_coord(
    station: str,
) -> dict[str, Any] | None:

    key = normalize_name(
        station
    )

    return (
        coordinate_lookup()
        .get(key)
    )


# ============================================================
# MODEL STATIONS
# ============================================================

@lru_cache(maxsize=1)
def model_station_names() -> list[str]:

    df = routes_df()

    names = (
        set(df["origin"])
        | set(df["destination"])
    )

    return sorted(
        str(name).strip()
        for name in names
        if str(name).strip()
    )


# ============================================================
# ROUTE JSON
# ============================================================

def route_json(
    row: pd.Series,
) -> dict[str, Any]:

    raw_path = parse_path(
        row["path"]
    )

    path: list[
        dict[str, Any]
    ] = []

    for item in raw_path:

        coord = resolve_coord(
            item["station"]
        )

        path.append(
            {
                **item,

                "lat": (
                    coord["lat"]
                    if coord
                    else None
                ),

                "lon": (
                    coord["lon"]
                    if coord
                    else None
                ),
            }
        )

    # --------------------------------------------------------
    # Transfer events
    #
    # Example:
    #
    # 忠孝復興站[BR]
    # 忠孝復興站[BL]
    #
    # same physical station + line change
    # --------------------------------------------------------

    transfer_events = []

    for index, (
        a,
        b,
    ) in enumerate(
        zip(
            path,
            path[1:],
        )
    ):

        if (
            a["station"]
            == b["station"]
            and a["line"]
            != b["line"]
        ):

            transfer_events.append(
                {
                    "station": a[
                        "station"
                    ],

                    "from_line": a[
                        "line"
                    ],

                    "to_line": b[
                        "line"
                    ],

                    "path_index": index,
                }
            )

    missing_coordinate_stations = sorted(
        {
            item["station"]
            for item in path
            if item["lat"] is None
        }
    )

    return {
        "route_id": int(
            row["route_id"]
        ),

        "travel_time_seconds": float(
            row[
                "travel_time_seconds"
            ]
        ),

        "travel_time_minutes": round(
            float(
                row[
                    "travel_time_minutes"
                ]
            ),
            2,
        ),

        "transfers": int(
            row["transfers"]
        ),

        "walking_seconds": float(
            row[
                "walking_seconds"
            ]
        ),

        "walking_minutes": round(
            float(
                row[
                    "walking_minutes"
                ]
            ),
            2,
        ),

        "path_text": str(
            row["path"]
        ),

        "path": path,

        "transfer_events": (
            transfer_events
        ),

        "missing_coordinate_stations": (
            missing_coordinate_stations
        ),
    }


# ============================================================
# BUILD NETWORK JSON
# ============================================================

@lru_cache(maxsize=1)
def network_json() -> dict[
    str,
    Any,
]:

    df = routes_df()

    stations: dict[
        str,
        dict[str, Any],
    ] = {}

    edges: dict[
        tuple[str, str, str],
        dict[str, Any],
    ] = {}

    # All Pareto paths
    for text in (
        df["path"]
        .dropna()
        .astype(str)
    ):

        path = parse_path(
            text
        )

        # ----------------------------------------------------
        # Stations
        # ----------------------------------------------------

        for item in path:

            coord = resolve_coord(
                item["station"]
            )

            if not coord:
                continue

            station = stations.setdefault(
                item["station"],
                {
                    "id": item[
                        "station"
                    ],

                    "label": item[
                        "station"
                    ],

                    "lat": coord[
                        "lat"
                    ],

                    "lon": coord[
                        "lon"
                    ],

                    "lines": set(),
                },
            )

            if item["line"]:

                station[
                    "lines"
                ].add(
                    item["line"]
                )

        # ----------------------------------------------------
        # Edges
        # ----------------------------------------------------

        for a, b in zip(
            path,
            path[1:],
        ):

            # Same physical station:
            # transfer state, not geographic link.

            if (
                a["station"]
                == b["station"]
            ):
                continue

            coord_a = resolve_coord(
                a["station"]
            )

            coord_b = resolve_coord(
                b["station"]
            )

            if (
                not coord_a
                or not coord_b
            ):
                continue

            if (
                a["line"]
                == b["line"]
            ):

                line = a[
                    "line"
                ]

            else:

                line = (
                    a["line"]
                    or b["line"]
                )

            station_x, station_y = sorted(
                [
                    a["station"],
                    b["station"],
                ]
            )

            key = (
                station_x,
                station_y,
                line,
            )

            edges.setdefault(
                key,
                {
                    "id": (
                        f"{station_x}"
                        f"::{station_y}"
                        f"::{line}"
                    ),

                    "source": a[
                        "station"
                    ],

                    "target": b[
                        "station"
                    ],

                    "line": line,

                    "positions": [
                        [
                            coord_a[
                                "lat"
                            ],
                            coord_a[
                                "lon"
                            ],
                        ],
                        [
                            coord_b[
                                "lat"
                            ],
                            coord_b[
                                "lon"
                            ],
                        ],
                    ],
                },
            )

    # Convert set -> list for JSON

    station_list = []

    for value in stations.values():

        station = dict(
            value
        )

        station["lines"] = sorted(
            station["lines"]
        )

        station_list.append(
            station
        )

    return {
        "stations": sorted(
            station_list,
            key=lambda item: item[
                "id"
            ],
        ),

        "edges": list(
            edges.values()
        ),
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "name": (
            "Taipei Pareto "
            "Route Explorer API"
        ),
        "version": "0.3.0",
        "health": "/api/health",
        "stations": "/api/stations",
        "network": "/api/network",
        "routes": (
            "/api/routes"
            "?origin=東湖站"
            "&destination=中原站"
        ),
    }


# ============================================================
# HEALTH CHECK
# ============================================================

def public_data_path(path: Path | None) -> str | None:
    """Report dataset identity without exposing workstation/host absolute paths."""
    if path is None:
        return None
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.name


@app.get("/api/health")
def health():

    try:

        coordinates = (
            coordinate_lookup()
        )

        model_stations = (
            model_station_names()
        )

        matched_stations = [
            station
            for station in model_stations
            if resolve_coord(
                station
            )
            is not None
        ]

        missing_stations = [
            station
            for station in model_stations
            if resolve_coord(
                station
            )
            is None
        ]

        coordinate_file = (
            get_station_csv()
        )

        return {
            "ok": (
                PARETO_CSV
                is not None
                and len(
                    coordinates
                )
                > 0
            ),

            "pareto_csv_found": (
                PARETO_CSV
                is not None
            ),

            "pareto_csv": (
                public_data_path(
                    PARETO_CSV
                )
                if PARETO_CSV
                else None
            ),

            "station_coordinate_file": public_data_path(
                coordinate_file
            ),

            # Number of stations available
            # in coordinate source.

            "coordinate_source_count": len(
                coordinates
            ),

            "taipei_coordinate_count": sum(
                1
                for value in coordinates.values()
                if value.get("source")
                == "taipei_open_data"
            ),

            "circular_fallback_count": sum(
                1
                for value in coordinates.values()
                if value.get("source")
                == "new_taipei_circular_fallback"
            ),

            # Number of stations actually
            # used by current MOSP dataset.

            "model_station_count": len(
                model_stations
            ),

            # Successfully matched

            "matched_station_count": len(
                matched_stations
            ),

            # Missing coordinates

            "missing_station_count": len(
                missing_stations
            ),

            "missing_stations": (
                missing_stations
            ),

            "station_error": None,
        }

    except Exception as exc:

        logging.getLogger(__name__).exception("Health check failed")
        return {
            "ok": False,

            "pareto_csv_found": (
                PARETO_CSV
                is not None
            ),

            "pareto_csv": (
                public_data_path(
                    PARETO_CSV
                )
                if PARETO_CSV
                else None
            ),

            "station_error": "Station data unavailable; check backend logs.",
        }


# ============================================================
# STATION LIST
# ============================================================

@app.get("/api/stations")
def stations():

    names = (
        model_station_names()
    )

    return {
        "count": len(
            names
        ),

        "stations": names,
    }


# ============================================================
# FULL NETWORK
# ============================================================

@app.get("/api/network")
def network():

    return network_json()


# ============================================================
# PARETO ROUTES FOR ONE OD
# ============================================================

@app.get("/api/routes")
def routes(
    origin: str = Query(...),
    destination: str = Query(...),
):

    if (
        origin
        == destination
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Origin and destination "
                "must differ."
            ),
        )

    df = routes_df()

    subset = df[
        (
            df["origin"]
            == origin
        )
        &
        (
            df["destination"]
            == destination
        )
    ].copy()

    if subset.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No Pareto result: "
                f"{origin} → "
                f"{destination}"
            ),
        )

    # Stable display order:
    #
    # 1. travel time
    # 2. transfers
    # 3. walking
    # 4. original route id

    subset = subset.sort_values(
        [
            "travel_time_minutes",
            "transfers",
            "walking_minutes",
            "route_id",
        ],
        kind="stable",
    )

    result = [
        route_json(row)
        for _, row
        in subset.iterrows()
    ]

    # R1, R2, ...
    for display_id, route in enumerate(
        result,
        start=1,
    ):

        route[
            "display_id"
        ] = display_id

    missing = sorted(
        {
            station
            for route in result
            for station
            in route[
                "missing_coordinate_stations"
            ]
        }
    )

    return {
        "origin": origin,

        "destination": (
            destination
        ),

        "pareto_count": len(
            result
        ),

        "routes": result,

        "missing_coordinate_stations": (
            missing
        ),
    }