# MOSP Research

唯一 canonical root：`MOSP_research/`。Synthetic experiments 與 Taipei Metro
real case 共用完全相同的 `src.mosp`；原 `Mosp_vr1.1/`、`Real_case1/` 沒有改動。
核心、研究設定、三個模型 input 與既有結果保存原始內容；前端已加入 responsive 與 production 設定。

## Structure

```text
MOSP_research/
├── src/                       # generic core, route-state model, canonical paths
├── experiments/
│   ├── synthetic/             # experiments 1, 2A, 2B, 3A, 3B
│   └── real_case/             # All-OD + supplementary 4/6/7
├── validation/                # 1000-case correctness + migration regression
├── analysis/
│   ├── synthetic/
│   └── real_case/             # chapter 5 alternatives and diagnostics
├── data/taipei_metro/         # 3 model inputs + separate website coordinates
├── results/                   # preserved per-experiment CSVs and figures
├── web/taipei-pareto-explorer/ # independent backend/frontend environments
├── archive/                   # byte-preserved sources / historical candidates
├── audit/                     # complete original trees, hashes, imports, diffs
└── regression/                # test evidence; reruns are isolated
```

## Windows installation: one explicit research interpreter

`src` is the actual package name, located at the repository root. It is not a
source-layout container. The root `pyproject.toml` installs `src`, `experiments`,
`validation` and `analysis`; all core imports consistently use `from src...`.

Python >=3.10 is supported; the project environment is verified on Python 3.13.
Use an explicit venv interpreter for both installation and execution. Activation
is optional. Run these once in PowerShell:

```powershell
cd C:\Users\xAdmin\MOSP_project\MOSP_research
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m validation.check_installation
```

If the Python launcher is unavailable, replace the `py -3.13` venv command with:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
```

The root `setup_windows.ps1` also performs the same installation and verifies all
active module imports; it finds Python or accepts `-PythonExecutable`. If PowerShell
blocks local scripts, the following process-local command needs no policy change:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

`requirements.txt` contains research dependencies. Optional web/test dependencies:
`.\.venv\Scripts\python.exe -m pip install -e ".[web,test]"`.
The website's separate backend `.venv` needs its own editable installation; one
environment's installation does not register packages in another Python interpreter.
Use its existing `start_backend.ps1` or the website README setup commands.

Editable installation makes module and file execution work from other working
directories when using this same interpreter. It uses neither PYTHONPATH nor
script-level sys.path edits. Another checkout containing a different top-level
`src` can still shadow packages under normal Python rules; use the canonical root
or an unrelated working directory, not the old checkout as an execution root.

## Formal execution

From the canonical root, without activating the venv:

```powershell
.\.venv\Scripts\python.exe -m validation.test_correctness
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_01
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_02a
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_02b
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_03a
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_03b
.\.venv\Scripts\python.exe -m experiments.real_case.experiment_05_all_od
```

Outside the root, use the full path to `.venv/Scripts/python.exe` with the same
module names. There is no need to enter experiments/validation/analysis folders.
Formal commands regenerate the corresponding `results/<experiment>/` CSVs.
Scientific parameters, RNG logic and output definitions are unchanged.

For short end-to-end checks without rewriting formal results:

```powershell
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_01 --smoke-test
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_02a --smoke-test
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_02b --smoke-test
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_03a --smoke-test
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_03b --smoke-test
.\.venv\Scripts\python.exe -m experiments.real_case.experiment_05_all_od --origin 東湖站 --output-dir regression/package_smoke/all_od
```

Synthetic smoke uses the first original replicate/query for every original
condition, generates the original graph and costs, calls the same solver, and
writes only `regression/package_smoke/<experiment>/smoke.csv`. It does not reduce
or patch the constants of formal experiments. `--smoke-output-dir` may select
another directory within canonical `regression/`.

## Isolated validation / smoke

```powershell
$env:MOSP_RESULTS_DIR = "regression/runs"
.\.venv\Scripts\python.exe -m validation.test_correctness
Remove-Item Env:MOSP_RESULTS_DIR
.\.venv\Scripts\python.exe -m experiments.real_case.experiment_05_all_od --origin 東湖站 --output-dir regression/runs/one_origin
```

`--origin` is an explicit smoke subset and requires `--output-dir`; formal defaults
are unchanged. Relative output overrides resolve against the canonical root.
`MOSP_RESULTS_DIR` also redirects all result readers, so clear it before reading
the preserved formal data or running the comprehensive regression checker.

To reproduce migration regression (with web/test dependencies installed):

```powershell
$env:MOSP_RESULTS_DIR = "regression/runs/all_od"
.\.venv\Scripts\python.exe -m experiments.real_case.experiment_05_all_od
Remove-Item Env:MOSP_RESULTS_DIR
.\.venv\Scripts\python.exe -m validation.regression_checks
```

This checks all module imports, exact core/model byte identity, formal-artifact
hashes, synthetic settings/functions/generation against archived source, sampled
raw statistics, paired controls, every All-OD non-runtime field, and API health/routes.
It never reruns the large synthetic studies with modified defaults.

## Analysis and website

Examples:

```powershell
.\.venv\Scripts\python.exe -m analysis.synthetic.analyze_experiment_01
.\.venv\Scripts\python.exe -m analysis.synthetic.plot_experiment_03
.\.venv\Scripts\python.exe -m analysis.real_case.analyze_experiment_05_all
.\.venv\Scripts\python.exe -m analysis.real_case.plot_chapter5_thesis_final
.\.venv\Scripts\python.exe -m analysis.real_case.plot_chapter5_figures_7_9_final
./web/taipei-pareto-explorer/start_backend.ps1
./web/taipei-pareto-explorer/start_frontend.ps1
```

Analysis imports are safe; scripts execute their existing computation only under
`python -m`. Alternative Chapter 5 figure scripts are retained without assuming
which version the thesis author selected; they can overwrite the same figure names,
so use the explicit results override when comparing them. Supplementary Experiment
6B/7 require DFS data that was not present in either audited folder; their code is
preserved with canonical paths and scientific settings unchanged.

See `AUDIT_REPORT.md`, `MIGRATION_REPORT.md`, `audit/migration_manifest.json`,
`audit/canonical_tree.txt` and `regression/checks.json` for evidence and per-file moves.

See `PACKAGE_IMPORT_REPORT.md` and `regression/package_fix/verification.json` for
Python 3.13 package installation, external-cwd execution and unchanged-result checks.

## Web deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Render Static Site + FastAPI Web Service settings, live URLs, deployment commands and verification evidence. See [RESPONSIVE_REPORT.md](RESPONSIVE_REPORT.md) for responsive changes and the limits of device verification.

Public explorer: [https://taipei-pareto-explorer.onrender.com](https://taipei-pareto-explorer.onrender.com). Public backend health: [https://mosp-taipei-api.onrender.com/api/health](https://mosp-taipei-api.onrender.com/api/health). Production browser UI/device verification is still pending access permission; public APIs and infrastructure are verified.
