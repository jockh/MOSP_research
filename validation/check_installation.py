"""Check installed packages and canonical imports without running experiments."""
import argparse
import ast
import importlib
import importlib.metadata
import json
import sys
from pathlib import Path

import src
from src.paths import PROJECT_ROOT, TAIPEI_METRO_DATA_DIR, ALL_OD_RESULTS_DIR, project_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Optional JSON evidence; relative paths use canonical root")
    args = parser.parse_args()
    distribution = importlib.metadata.distribution("mosp-research")
    assert Path(src.__file__).resolve() == PROJECT_ROOT / "src/__init__.py"
    dependencies = {name: importlib.metadata.version(name) for name in
                    ["numpy", "pandas", "scipy", "networkx", "matplotlib", "statsmodels"]}
    modules = []
    for folder in ["src", "experiments", "validation", "analysis"]:
        for path in sorted((PROJECT_ROOT / folder).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    assert ast.unparse(node.func) not in {"sys.path.insert", "sys.path.append", "os.getcwd", "Path.cwd"}, str(path)
                if isinstance(node, ast.ImportFrom):
                    assert node.module not in {"graph", "mosp", "dominance", "label"}, str(path)
            name = ".".join(path.relative_to(PROJECT_ROOT).with_suffix("").parts)
            if name.endswith(".__init__"):
                name = name[:-9]
            loaded = importlib.import_module(name)
            assert Path(loaded.__file__).resolve().is_relative_to(PROJECT_ROOT), name
            modules.append(name)
    inputs = [TAIPEI_METRO_DATA_DIR / name for name in
              ["臺北捷運路線車站資料服務_NEW_fixed (1).csv",
               "臺北捷運相鄰兩站間之行駛時間及停靠站時間(1150830).csv",
               "臺北捷運轉乘車站轉乘步行時間資料.csv"]]
    assert all(path.is_file() for path in inputs)
    assert (ALL_OD_RESULTS_DIR / "all_od_pareto_routes.csv").is_file()
    evidence = {"python": sys.executable, "python_version": sys.version, "package_version": distribution.version,
                "src_file": src.__file__, "project_root": str(PROJECT_ROOT), "dependencies": dependencies,
                "imported_modules": modules, "module_count": len(modules), "input_files_found": len(inputs),
                "all_od_routes_found": True, "sys_path_hacks": 0, "bare_core_imports": 0}
    if args.output:
        path = project_path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
