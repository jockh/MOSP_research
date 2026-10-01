"""Canonical paths, independent of the process working directory."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
TAIPEI_METRO_DATA_DIR = DATA_DIR / "taipei_metro"

def project_path(value):
    """Resolve relative overrides against the canonical repository."""
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()

# Explicit isolation for validation/smoke runs; the default remains results/.
RESULTS_DIR = project_path(os.environ.get("MOSP_RESULTS_DIR", "results"))
ALL_OD_RESULTS_DIR = RESULTS_DIR / "experiment_05_all_od"

def result_path(*parts):
    """Map preserved synthetic output filenames into per-experiment folders."""
    relative = Path(*parts)
    first = relative.parts[0] if relative.parts else ""
    folders = ("experiment_01", "experiment_02a", "experiment_02b",
               "experiment_03a", "experiment_03b")
    for folder in folders:
        if first.startswith(folder):
            if first in (folder, folder + "_figures"):
                return RESULTS_DIR / folder / "figures" / Path(*relative.parts[1:])
            return RESULTS_DIR / folder / relative
    return RESULTS_DIR / relative
