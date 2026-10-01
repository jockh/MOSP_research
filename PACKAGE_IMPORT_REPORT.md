# Python package / import 修復報告

日期：2026-10-01。唯一正式 root：`C:\Users\xAdmin\MOSP_project\MOSP_research`。
實測 interpreter：root `.venv\Scripts\python.exe`，Python 3.13.15。

## 1. 根本原因與實際結構檢查

原來 canonical root 已有 `src/__init__.py`，`src/` 就位於 root；
`experiments`、`validation`、`analysis` 及其子 packages 也已有 `__init__.py`。
既有 pyproject 的 root package discovery 基本上正確，沒有把 `src` 誤設為
source-layout container。沒有需要為這次 import 修復再搬動的研究檔案。

問題在 interpreter 與安裝流程不一致：

- 修復前 root `.venv` 不存在；全域 Python 3.13 沒有安裝 `mosp-research`，
  也缺少研究所需的 pandas 等 dependencies。
- backend `.venv` 是獨立環境。安裝到 backend `.venv` 不會使全域 Python
  或其他 virtual environment 自動取得 canonical packages。
- 直接執行 nested script 時，Python 優先使用 script 所在目錄；未 editable
  install 的 interpreter 無法從該目錄找到 root `src`。
- 從真正 canonical root 執行 `python -m`，root 本來就可供 module lookup；
  因此不能把所有先前錯誤都歸因於錯誤的 source layout。錯誤 cwd 或另一支
  未安裝的 Python 仍可能造成相同錯誤。

這次採用同一個 root research `.venv`，安裝 `mosp-research` editable package，
所有研究執行指令明確指定該 interpreter。沒有要求 activate，沒有使用
PYTHONPATH，沒有加入 script-level `sys.path` 修改。

`archive/original_sources/` 內的兩個原專案是不可執行的 provenance snapshots，
不是第二或第三個正式 project root；它們排除在 setuptools package discovery 外。

## 2. 修改及新增檔案

| 檔案 | 變更與目的 |
| --- | --- |
| `pyproject.toml` | 明確列出 root packages 與子 packages；停用 implicit namespace discovery；排除 archive/web/audit/data/results。 |
| `README.md` | 全部研究執行範例指定 root `.venv`；說明 editable install、外部 cwd、分開的 backend environment。 |
| `setup_windows.ps1`（新增） | 以 script root 建立/重用 root `.venv`，editable install，檢查所有研究 imports；支援 `-PythonExecutable` 與 `-IncludeWeb`。 |
| `validation/check_installation.py`（新增） | 驗證 distribution、src 實際來源、50 個 modules、dependencies、資料/結果路徑，以及 active import/hack 規則。 |
| `experiments/synthetic/_cli.py`（新增） | 共用 `--smoke-test` CLI；使用原生成函式與原 seed，每個正式條件取第一個原樣本；輸出限於 `regression/`。 |
| `experiments/synthetic/experiment_01.py` | 原 main guard 新增 smoke dispatch；無 flag 時繼續原正式流程。 |
| `experiments/synthetic/experiment_02a.py` | 同上。 |
| `experiments/synthetic/experiment_02b.py` | 同上。 |
| `experiments/synthetic/experiment_03a.py` | 同上。 |
| `experiments/synthetic/experiment_03b.py` | 同上。 |

另外新增本報告，更新 `MIGRATION_REPORT.md`、`audit/migration_manifest.json`、
`audit/canonical_tree.txt`，並保存 `regression/package_fix/` 下的 logs、diff、
baseline、installation metadata 與驗證結果。root `.venv` 與 editable install
產生的 metadata 是環境檔案，不是第二套研究 solver。

`src` core、Taipei Metro model、paths、correctness script、All-OD script、
analysis scripts 的程式內容這次都沒有修改。原本 active imports 已統一使用
`src.*`，掃描後沒有需要再次改寫的 bare core imports。

## 3. 最終 package structure

```text
MOSP_research/
├── .venv/                       # 唯一 research interpreter
├── src/
│   ├── __init__.py
│   ├── graph.py
│   ├── label.py
│   ├── dominance.py
│   ├── mosp.py
│   ├── brute_force.py
│   ├── taipei_metro.py
│   └── paths.py
├── experiments/
│   ├── __init__.py
│   ├── synthetic/
│   │   ├── __init__.py
│   │   ├── _cli.py
│   │   ├── experiment_01.py
│   │   ├── experiment_02a.py
│   │   ├── experiment_02b.py
│   │   ├── experiment_03a.py
│   │   └── experiment_03b.py
│   └── real_case/
│       ├── __init__.py
│       ├── experiment_05_all_od.py
│       └── ...                  # 保留 supplementary experiments
├── validation/
│   ├── __init__.py
│   ├── test_correctness.py
│   ├── check_installation.py
│   └── regression_checks.py
├── analysis/
│   ├── __init__.py
│   ├── synthetic/__init__.py
│   ├── real_case/__init__.py
│   └── ...
├── data/taipei_metro/
├── results/
├── web/taipei-pareto-explorer/    # 獨立 backend/frontend environments
├── archive/                     # 排除在 package discovery 外
├── audit/
├── regression/
├── setup_windows.ps1
├── pyproject.toml
├── requirements.txt
├── README.md
├── MIGRATION_REPORT.md
└── PACKAGE_IMPORT_REPORT.md
```

8 個正式 package directories 都有 `__init__.py`。核心 imports 一律為：

```python
from src.graph import Graph
from src.mosp import mosp
```

完整檔案清單見 `audit/canonical_tree.txt`；該清單省略 `.venv`、node_modules、
cache 及生成的 egg-info 內容，並標示省略目錄。

## 4. 完整 pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "mosp-research"
version = "1.0.0"
description = "Exact MOSP synthetic experiments and Taipei Metro route-state study"
requires-python = ">=3.10"
dependencies = ["numpy", "pandas", "scipy", "networkx", "matplotlib", "statsmodels"]

[project.optional-dependencies]
web = ["fastapi", "uvicorn", "python-dotenv", "requests"]
test = ["httpx"]

[tool.setuptools.packages.find]
where = ["."]
namespaces = false
include = ["src", "src.*", "experiments", "experiments.*", "validation", "validation.*", "analysis", "analysis.*"]
exclude = ["archive*", "web*", "audit*", "results*", "data*"]
```

`where = ["."]` 表示從 repository root 找 packages，`include` 明確包含
`src` 本身。沒有 `package-dir = {"" = "src"}`，也沒有把 graph/mosp 當成
top-level modules。distribution 名稱是 `mosp-research`，import 名稱是 `src`。

## 5. Windows 安裝指令

目前本機 root `.venv` 已建立且 editable install 已完成，可直接執行第 6 節。
重新安裝或在新環境設定時，PowerShell 執行：

```powershell
cd C:\Users\xAdmin\MOSP_project\MOSP_research
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m validation.check_installation
```

如果 `py` launcher 不存在，建立 venv 的指令替換為：

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
```

也可以從任意 cwd 使用這次已實測的安裝腳本：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\xAdmin\MOSP_project\MOSP_research\setup_windows.ps1
```

若要用 root environment 執行 web/API regression，安裝 optional extras：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[web,test]"
```

或在安裝腳本後加 `-IncludeWeb`。本次 root `.venv` 已安裝這些 extras。
PowerShell 的 Bypass 僅限該安裝 process，沒有變更全域 execution policy。
沒有依賴 virtual environment activation。

## 6. 正式與 smoke 執行指令

從 canonical root 執行以下正式指令（會依原流程重新產生對應 results）：

```powershell
cd C:\Users\xAdmin\MOSP_project\MOSP_research
.\.venv\Scripts\python.exe -m validation.test_correctness
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_01
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_02a
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_02b
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_03a
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_03b
.\.venv\Scripts\python.exe -m experiments.real_case.experiment_05_all_od
```

短時間檢查 synthetic entry points、inputs、solver 與 output path：

```powershell
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_01 --smoke-test
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_02a --smoke-test
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_02b --smoke-test
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_03a --smoke-test
.\.venv\Scripts\python.exe -m experiments.synthetic.experiment_03b --smoke-test
.\.venv\Scripts\python.exe -m experiments.real_case.experiment_05_all_od --origin 東湖站 --output-dir regression/package_smoke/all_od
```

Synthetic smoke 不修改正式 constants 或 output definitions；只取第一個原
replicate/query，保留原生成時的 random draw 順序，且涵蓋每個原實驗條件。
它使用同一套 solver，產生獨立的 smoke evidence。沒有完整重跑五個大型
synthetic studies，正式舊 results 保持原 bytes。

外部 cwd 以完整 interpreter path 執行同一 module，例如：

```powershell
& 'C:\Users\xAdmin\MOSP_project\MOSP_research\.venv\Scripts\python.exe' -m validation.check_installation
& 'C:\Users\xAdmin\MOSP_project\MOSP_research\.venv\Scripts\python.exe' -m experiments.synthetic.experiment_01 --smoke-test
```

資料、結果與相對 output override 均由 `src.paths` anchored 到 canonical root。
module 與直接 absolute-file 執行都已從外部 cwd 實測。另一個 checkout 若有
同名 top-level `src`，普通 Python module lookup 仍可能先選 cwd 中的同名
package；不要把保留的舊 checkout 當作新的執行 root。實測也包含外部 cwd
`python -I` import，排除 cwd/PYTHONPATH 的依賴。

Website 仍可保留獨立 backend `.venv`：每個 environment 都需自己的 editable
install。先前修復的 backend `.venv` 已完成安裝，其 Windows launcher 會用
該 interpreter。詳細指令在 `web/taipei-pareto-explorer/README.md`。

## 7. sys.path hacks 與 import 掃描

所有 repository-owned Python sources（含 archive 與 website）已掃描；
venv/site-packages 與 node_modules 是第三方環境內容，不屬於需重寫的研究碼。
50 個 active research modules 的 import/AST 檢查全部通過：

- active `sys.path.append/insert`：0。
- active `from graph/mosp/dominance/label`：0。
- active cwd-based data/result access：0。
- 本次無新增或逐檔插入任何 path hack；active code 原先已在 migration 統一。

唯一保留的原始 hack：
`archive/original_sources/Mosp_vr1.1/experiments/experiment_03b_route_overlap.py:64`，
`sys.path.insert(0, PROJECT_ROOT)`。canonical Experiment 3B 已在原 migration
移除該 hack；archive 版不安裝、不供正式執行，保留原 bytes 作為研究 provenance。

## 8. 實際執行的驗證

所有以下命令使用 root Python 3.13.15，清除 PYTHONPATH，沒有依賴 activation。
完整 argv、cwd、exit code、output override、log 路徑保存在
`regression/package_fix/verification.json`，17 個 commands 全部 exit 0。

| 驗證 | 結果 |
| --- | --- |
| `import src; print(src.__file__)` | 指向 canonical `src/__init__.py`。 |
| `from src.graph import Graph` | `graph OK`。 |
| `from src.mosp import mosp` | `mosp OK`。 |
| `-m validation.test_correctness` | 1000/1000，failed 0，100.00%。 |
| Experiment 1 `--smoke-test` | 4 objective cases；原 100 nodes / cost generation / seed；與正式首筆 statistics 完全一致。 |
| Experiment 2A `--smoke-test` | 原 5 rho cases，generation / saved statistics 一致。 |
| Experiment 2B `--smoke-test` | 原 4 dependence matrices 均驗證成功，generation / statistics 一致。 |
| Experiment 3A `--smoke-test` | 原 4 K cases，graph / statistics 一致。 |
| Experiment 3B `--smoke-test` | 3 shared lengths × prefix/suffix＝6 cases；paired cost/Pareto controls 一致。 |
| All-OD one-origin | 東湖站成功；218 Pareto routes，寫入獨立 regression output。 |
| All-OD 正式 default pipeline | 完整跑完 119 origins；14042 ODs、22052 routes；7 個 CSV 所有非計時欄位 exact match。 |
| 外部 cwd `-m validation.check_installation` | 50 modules 全數匯入；3 model inputs 與正式 routes CSV 都找到。 |
| 外部 cwd `python -I -c 'import src...'` | 成功；即使 isolated mode 仍能找到已安裝的 canonical package。 |
| 直接 correctness file（root / 外部 cwd） | 兩種執行均 1000/1000。 |
| 直接 Experiment 1 file（外部 cwd） | 原 4 objective smoke cases 成功。 |
| `-m validation.regression_checks` | 全部通過；core bytes、scientific settings/functions、formal hashes、synthetic controls、Metro model、All-OD、API 均通過。 |
| `setup_windows.ps1 -IncludeWeb`（外部 cwd） | pip editable installation 成功；50 module installation check 通過。 |

23 個新增 synthetic CLI smoke cases 的 graph sizes 與 6 項 solver statistics，
均與原正式結果對應首筆相同。comprehensive regression 另外檢查更多
Experiment 3A/3B samples（12 / 18 cases）。

Correctness 未改研究設定：1000 tests、7 nodes、objectives [2,3,4,5]、
cost 1–20、master seed 20260930；與 exhaustive simple-path enumeration 一致。

Metro 檢查：119 physical stations、150 route states、Circular Line included、
skipped travel rows 0；三個正式 input 均找到。Web backend 讀取正式 canonical
routes CSV，ASGI `/api/health` HTTP 200、119 stations matched；範例 routes API
HTTP 200。先前真正 Uvicorn reload/server 測試在
`regression/backend_environment_fix.json`，使用獨立 backend Python 3.13.15。

## 9. 剩餘 import 問題與邊界

在已實測的 root `.venv`、所有 active research modules、上述 module/file
entry points 中，`No module named 'src'` 剩餘數量：**0**。
沒有替全域 Python 或未使用的其他 venv 安裝套件。使用另一支 interpreter
時，仍須在該 interpreter 做 editable install；請以此報告的明確 `.venv`
指令執行。

Supplementary Experiment 6B/7 原來缺少的 DFS input 不屬於 import 問題；
其 modules 可匯入，但本次未宣稱缺失的資料已補齊。大型 synthetic 正式
studies 用 smoke + code/settings invariance 驗證，未整批重跑。

## 10. 是否影響研究結果

**Did this refactor change any algorithm, experimental setting, or research result? No.**

證據：

- MOSP core、Taipei Metro model、paths、正式 data/results 的 protected hashes 未變。
- 五個 synthetic scripts 的 scientific functions/classes/constants，與此次
  修改前的 AST 完全一致；差別僅 main guard 的 smoke dispatch。
- 原 scientific functions/settings 與 archived sources 的 migration regression 通過。
- 23 個 CLI smoke cases 與原正式 statistics 一致。
- 完整 All-OD 在 Python 3.13 重新計算，7 個 CSV 的所有非計時欄位完全一致。
- 正式 result files 沒有被這次 checks 覆寫；重跑的時間數值只存在 regression
  output，runtime 本來就會隨環境變動。
- 原 `Mosp_vr1.1/`、`Real_case1/` 沒有修改或刪除。

執行環境的 dependency versions 記錄於
`regression/package_fix/installation.json`；完整 installed-distribution snapshot
另存 `regression/package_fix/python313_environment.json`。既有
`requirements-tested.txt` 仍保留先前 migration 測試環境的版本記錄。
