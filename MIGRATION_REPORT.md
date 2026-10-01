# MIGRATION_REPORT

Canonical repository：`C:/Users/xAdmin/MOSP_project/MOSP_research/`。原兩資料夾保持不動。先在獨立暫存 root 完成雙專案 audit、來源比較與回歸，再發布到指定新 root。所有遷移是 copy + canonical path/import/entry-point edits，沒有對原 project 執行 move/delete。

## 1. 原專案內容與完整 audit

Mosp_vr1.1：generic core、synthetic 1/2A/2B/3A/3B、1000-case correctness、早期 Experiment 3、analysis/plots、CSVs/figures。Real_case1：相同 core、唯一 Taipei model、All-OD、三個 inputs、候選 Chapter 5 圖版、補充 experiments/diagnostics、完整網站與座標 cache。
所有原始 folder trees、Python/CSV/result/analysis lists、duplicates、imports/dependency references、sys.path、hard-coded/CWD/relative paths 見 `AUDIT_REPORT.md` 和 `audit/` 的 machine-readable inventories。原始所有研究檔案 SHA256 在報告生成時再次驗證為未改動。

## 2. Canonical versions 與採用理由

| Component | 採用來源 | 理由 |
|---|---|---|
| graph / label / dominance / mosp / brute_force | Mosp_vr1.1/src | 與 Real_case1 同名檔 byte-identical；5 份 diff 無差異，沒有 solver 邏輯或 stats 需要合併 |
| Taipei model | Real_case1/src/taipei_metro.py | 指定兩個 root 內唯一版本；既有 All-OD/diagnostics import 它；完整重算驗證既有正式 routes |
| Synthetic 1/2A/2B/3A/3B | Mosp_vr1.1/experiments 相應 runner | write/read dependencies 與現有 raw schemas、row counts 相符；原 seed 抽樣統計吻合 |
| Correctness | Mosp_vr1.1/test_correctness.py | 唯一 validator；独立 exhaustive filter 未改動，1000-case 設定保留 |
| All-OD | Real_case1/experiment_05_all_od.py | 唯一 All-OD runner；one MOSP/origin、dwell、virtual targets 完整保留，全 OD 與正式 CSV 一致 |
| Website | Real_case1/taipei-pareto-explorer | frontend/lockfile byte-preserved；backend 只更換檔案定位與 dotenv root |
| Figure alternatives | 所有現存 Chapter 5 candidates | 不以 final/(1) 判定新舊或論文採用；保留全部，提供內容 diffs |

沒有找到 taipei_metro(1)/(3)/(4).py。沒有依 filename 最大數字作選擇。TransitGraph 是原有捷運 metadata/edge 結構，維持 duck typing；沒有為了整齊改寫成 Graph subclass。MOSP 本體只有 src/mosp.py 一套 executable canonical implementation。archive 的 solver snapshots 不在 package discovery 或執行路徑內。

## 3. 移動、重新命名與逐檔對照

| Original | Canonical |
|---|---|
| experiments/experiment_01_objectives.py | experiments/synthetic/experiment_01.py |
| experiments/experiment_02a_correlation.py | experiments/synthetic/experiment_02a.py |
| experiments/experiment_02b_dependence_3d.py | experiments/synthetic/experiment_02b.py |
| experiments/experiment_03a_route_quantity.py | experiments/synthetic/experiment_03a.py |
| experiments/experiment_03b_route_overlap.py | experiments/synthetic/experiment_03b.py |
| test_correctness.py | validation/test_correctness.py |
| Real_case1/experiment_05_all_od.py | experiments/real_case/experiment_05_all_od.py |
| Real_case1/experiments/plot_chapter5_thesis_final (1).py | analysis/real_case/plot_chapter5_thesis_final.py |
| Synthetic analyzes/plots | analysis/synthetic/ 同名檔 |
| Real analyzes/plots/diagnostics | analysis/real_case/ 同名檔 |
| Supplementary real-case experiments 4/6/7 | experiments/real_case/ 同名檔 |
| Real_case1/data/*.csv | data/taipei_metro/ 保留原檔名及 encoding |
| Backend station-coordinate cache | data/taipei_metro/taipei_metro_station_positions.csv |
| Saved formal results | results/experiment_01/02a/02b/03a/03b/correctness_validation/experiment_05_all_od/ |
| Shared 3A/3B figures | results/experiment_03_comparison/figures/ |
| Website | web/taipei-pareto-explorer/ |

完整每檔 source/destination、原 SHA256、遷移後 SHA256、modified flag 與 role 見 `audit/migration_manifest.json`。有修改的 source diffs 見 `audit/migration_diffs/`。所有原研究 Python 檔皆另保留 byte-identical provenance snapshot。所有 non-generated 原檔均已納入 canonical、snapshot 或 deprecated_candidates，沒有遺漏不確定結果。

## 4. Imports / packaging / entry points

所有研究 solver imports 都指向 `src.*`；solver 與 model 原 imports 不需要改。新增各 package 的 __init__.py 與 setuptools pyproject，支援 editable install。移除 3B 的 sys.path injection。分析/補充腳本新增 __main__ guard，避免 import 時執行大型實驗或重寫正式圖表。All-OD 的兩個 virtual-node functions、迴圈與結果 calculations 保留，原 executable body 放進 main；只新增明確 smoke origins/output 選項，預設仍處理全 119 origins。

Backend 新增 `from src.paths import ...`；獨立 backend venv 透過 launcher editable-install canonical package，因此不使用 sys.path hack。React dependencies 仍只在 frontend。所有 canonical Python modules compile/import 通過。

## 5. Paths

新增 src/paths.py：__file__ → canonical root → data/results。所有研究 reader/writer paths 都從它取得，移除 ROOT 尋找、舊 project sibling 搜尋與 CWD guessing。保持原 CSV filenames/columns/encodings。相對 MOSP_RESULTS_DIR / backend override / All-OD output override 均以 canonical root 解析。
AST 掃描 active src/experiments/analysis/validation/backend：sys.path.insert/append、os.getcwd、Path.cwd 呼叫數均為 0。archive/audit 裡舊路徑保留作 provenance，不作 executable canonical dependency。Canonical tree 在 audit/canonical_tree.txt。

## 6. 正式 inputs 與模型

三個模型 inputs 是 `臺北捷運路線車站資料服務_NEW_fixed (1).csv`（station/service metadata）、`臺北捷運相鄰兩站間之行駛時間及停靠站時間(1150830).csv`（travel/dwell）、`臺北捷運轉乘車站轉乘步行時間資料.csv`（walking）。三個檔 byte-preserved，沒有轉換 encoding、更新資料或改數值。另有網站座標 CSV，不能把 route metadata 誤當 coordinate data。
建構結果維持：119 physical stations、150 route states、141 ride segments / 282 directed ride edges、54 directed transfer edges。環狀 Y07–Y20 有 14 stations / 13 segments。新埔/新埔民生及大坪林特殊 transfer edges 共 4；大坪林 explicit assumption 3.0 minutes 未變。skipped travel rows=0。9 個 endpoint/service states 原本缺 dwell observation 的清單照原 build_stats 保留，沒有為通過測試填入新的觀測值。

## 7. 保存結果與 provenance 限制

90 個正式 input/result/figure/website-coordinate artifacts 的 SHA256 與原檔完全一致。Synthetic raw counts：1=2000、2A=2500、2B=2000、3A=2000、3B=3000；correctness=1000。All-OD=14042 pairs、22052 routes。CSV headers 皆保留。
正式結果來源判斷由實際 read/write dependencies、schema、數量及 deterministic regeneration 支持。沒有論文正文/run manifests 可以證明 alternate plot 版型的作者選擇，因此沒有宣稱所有「final」檔都是論文唯一版。保留全部 existing Chapter 5 output directories 和所有候選 scripts；不要直接覆蓋/刪除候選圖版。

## 8. Duplicates / archive candidates / deletion advice

原專案沒有刪除。`archive/original_sources/` 保留全部原 Python sources，包括兩邊相同 core。`archive/deprecated_candidates/` 保留早期 Experiment 3 designs/results、experiments/figures duplicate figures 及其它不確定檔。早期 redundancy 與 route diversity 是不同研究設計，沒有自動併進 3A/3B。alternate thesis/7–9 plots 仍有不同版型與輸出，不以名稱刪除。
通過回歸後，可將整個舊 Mosp_vr1.1 / Real_case1 搬到唯讀備份 archive（由使用者決定）。必須保留一份 original source snapshot、三個模型 inputs、正式 raw/summary/routes/figures、網站 source/lockfile、座標與 audit/manifest。先不要刪除有 provenance 不確定性的圖版/舊結果。可重建、可考慮清除的只是舊 __pycache__、node_modules、.venv；它們不是研究結果，沒有移植進新 repository。新環境由 dependency files 重建。未找到原 runtime lock，所以無法宣稱完全復原歷史軟體版本。

## 9. Regression checks（實際執行）

| Check | 結果 |
|---|---|
| Compile/import smoke | 48 active modules PASS |
| Correctness command | Total 1000 / Passed 1000 / Failed 0 / Pass rate 100.00%；7481 simple paths |
| Experiment 1 | 原 seed / 100 nodes / 753 edges；所有 4 objective dimensions 的第 1 query workload stats 與原 raw 完全一致 |
| Experiment 2A | 全 5 rho generation、cost transformation、原 source definitions 一致；第 1 query workload stats 與 raw 一致 |
| Experiment 2B | 4 matrices symmetric/positive-definite、Cholesky 成功；generation/statistics 與原始碼/raw 一致 |
| Experiment 3A | replicates 0/1/499 × 4 K，共 12 graphs / stats 與原 source/raw 一致 |
| Experiment 3B | replicates 0/1/499 × 3 overlap × prefix/suffix，共 18 cases；paired costs、Pareto sets、原 workload stats 一致 |
| Core/model integrity | 5 core files 與兩 project snapshots byte-identical；Taipei model byte-identical |
| Scientific settings/functions | All uppercase scientific constants unchanged；生成與算法 functions AST identical，僅 I/O functions 有 path edits |
| Taipei graph | build stats 全部符合原 preflight；Circular Line=true，skipped travel=0 |
| One-origin module CLI | 東湖站 startup + 全 118 destinations，218 routes exact-match；由外部 CWD 執行也成功 |
| Full All-OD module run | 119 origins 完整完成；7 個結果 CSV 所有非 runtime fields exact-match 原正式結果 |
| Web health/routes | ASGI HTTP health 200/ok；route API 200，東湖→中原 5 routes；matched coordinates 119/119 |
| Formal artifact hashes | 90 檔原 bytes 保存 |
| External-CWD correctness | editable install 後，在非 project cwd 重跑 1000/1000 PASS，輸出仍落 canonical regression/runs |
| Forbidden path calls | 0（active modules/backend） |

詳見 regression/checks.json、regression/environment.json、regression/*log。正規回歸只寫 regression/runs，未以 smoke 降低 source 中正式參數。網站 health 是透過 FastAPI TestClient/ASGI 真的 HTTP routing 測試，沒有啟動常駐 server。frontend 沒有改 source/lockfile；此次未另作 npm build 或互動 UI 測試。Supplementary DFS Experiment 6B/7 需要的歷史 input outputs 不在來源資料夾，因此只做 compile/import，沒有假稱完成那些研究。

## 10. 是否有研究數值變化

既有正式檔案沒有任何數值/bytes 改動。完整 Taipei 重算與抽樣 synthetic 重算的 costs、Pareto sets、routes、workload statistics 都符合保存結果。新測試測量的 runtime_seconds 自然隨硬體/環境變動；只在 regression 隔離輸出，不覆蓋任何原 timing。所有非 runtime 欄位採 exact comparison。此遷移沒有變動 objectives、seeds、cost generation、Cholesky、K/L/overlap/paired samples、dwell/transfer/circular modelling 或 source-to-all design。

## 11. 正式執行方式與限制

由 new root 建立 venv 並 `python -m pip install -e .`；所有七個要求的 `python -m ...` 指令、analysis/website 指令與隔離驗證見 README。root-scoped data/results 與 arbitrary-CWD execution 經驗證。Python search path 若刻意包含舊 checkout 的另一個 src，仍會依一般 Python shadowing 規則；建議使用新環境。此處沒有默默把 import 改成會改變研究的另一套 solver。

## 12. Required final answer

**Did this refactor change any algorithm, experimental setting, or research result?**

**No.**

這個結論指 canonical 算法/實驗設定/既有研究 artifact 皆沒有改動；驗證範圍及測量時間的自然差異已明確列出，不宣稱已重跑全部大型 synthetic studies。

## Per-file migration list

- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\analyze_experiment_01.py` → `archive/original_sources/Mosp_vr1.1/experiments/analyze_experiment_01.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\analyze_experiment_02a.py` → `archive/original_sources/Mosp_vr1.1/experiments/analyze_experiment_02a.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\analyze_experiment_02b.py` → `archive/original_sources/Mosp_vr1.1/experiments/analyze_experiment_02b.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\analyze_experiment_03.py` → `archive/original_sources/Mosp_vr1.1/experiments/analyze_experiment_03.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\analyze_experiment_03a.py` → `archive/original_sources/Mosp_vr1.1/experiments/analyze_experiment_03a.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\analyze_experiment_03b.py` → `archive/original_sources/Mosp_vr1.1/experiments/analyze_experiment_03b.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_01_objectives.py` → `archive/original_sources/Mosp_vr1.1/experiments/experiment_01_objectives.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_02a_correlation.py` → `archive/original_sources/Mosp_vr1.1/experiments/experiment_02a_correlation.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_02b_dependence_3d.py` → `archive/original_sources/Mosp_vr1.1/experiments/experiment_02b_dependence_3d.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_03_redundancy.py` → `archive/original_sources/Mosp_vr1.1/experiments/experiment_03_redundancy.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_03_route_diversity.py` → `archive/original_sources/Mosp_vr1.1/experiments/experiment_03_route_diversity.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_03a_route_quantity.py` → `archive/original_sources/Mosp_vr1.1/experiments/experiment_03a_route_quantity.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_03b_route_overlap.py` → `archive/original_sources/Mosp_vr1.1/experiments/experiment_03b_route_overlap.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\figures\experiment_03\fig_01_route_count_vs_pareto.png` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/figures/experiment_03/fig_01_route_count_vs_pareto.png` — historical duplicate figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\figures\experiment_03\fig_02_route_count_vs_generated.png` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/figures/experiment_03/fig_02_route_count_vs_generated.png` — historical duplicate figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\figures\experiment_03\fig_03_route_count_vs_checks.png` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/figures/experiment_03/fig_03_route_count_vs_checks.png` — historical duplicate figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\figures\experiment_03\fig_04_route_count_vs_runtime.png` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/figures/experiment_03/fig_04_route_count_vs_runtime.png` — historical duplicate figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\figures\experiment_03\fig_05_mean_diversity_vs_pareto.png` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/figures/experiment_03/fig_05_mean_diversity_vs_pareto.png` — historical duplicate figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\plot_experiment_01.py` → `archive/original_sources/Mosp_vr1.1/experiments/plot_experiment_01.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\plot_experiment_02a.py` → `archive/original_sources/Mosp_vr1.1/experiments/plot_experiment_02a.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\plot_experiment_02b.py` → `archive/original_sources/Mosp_vr1.1/experiments/plot_experiment_02b.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\plot_experiment_03.py` → `archive/original_sources/Mosp_vr1.1/experiments/plot_experiment_03.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\correctness_validation\correctness_validation_cases.csv` → `results/correctness_validation/correctness_validation_cases.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\correctness_validation\correctness_validation_summary.txt` → `results/correctness_validation/correctness_validation_summary.txt` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_01_figures\fig1_pareto_labels.png` → `results/experiment_01/figures/fig1_pareto_labels.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_01_figures\fig2_generated_labels.png` → `results/experiment_01/figures/fig2_generated_labels.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_01_figures\fig3_dominance_checks.png` → `results/experiment_01/figures/fig3_dominance_checks.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_01_figures\fig4_runtime.png` → `results/experiment_01/figures/fig4_runtime.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_01_figures\fig5_checks_vs_runtime.png` → `results/experiment_01/figures/fig5_checks_vs_runtime.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_01_figures\objective_growth.pdf` → `results/experiment_01/figures/objective_growth.pdf` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_01_figures\objective_growth.png` → `results/experiment_01/figures/objective_growth.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_01_formal_raw.csv` → `results/experiment_01/experiment_01_formal_raw.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02a_correlation_check.csv` → `results/experiment_02a/experiment_02a_correlation_check.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02a_correlation_raw.csv` → `results/experiment_02a/experiment_02a_correlation_raw.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02a_figures\fig1_pareto_vs_correlation.png` → `results/experiment_02a/figures/fig1_pareto_vs_correlation.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02a_figures\fig2_generated_vs_correlation.png` → `results/experiment_02a/figures/fig2_generated_vs_correlation.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02a_figures\fig3_checks_vs_correlation.png` → `results/experiment_02a/figures/fig3_checks_vs_correlation.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02a_figures\fig4_runtime_vs_correlation.png` → `results/experiment_02a/figures/fig4_runtime_vs_correlation.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02a_figures\fig5_checks_vs_runtime.png` → `results/experiment_02a/figures/fig5_checks_vs_runtime.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02a_figures\objective_correlation_workload.pdf` → `results/experiment_02a/figures/objective_correlation_workload.pdf` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02a_figures\objective_correlation_workload.png` → `results/experiment_02a/figures/objective_correlation_workload.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02a_summary.csv` → `results/experiment_02a/experiment_02a_summary.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02b\fig_01_pareto_labels.png` → `results/experiment_02b/figures/fig_01_pareto_labels.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02b\fig_02_generated_labels.png` → `results/experiment_02b/figures/fig_02_generated_labels.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02b\fig_03_dominance_checks.png` → `results/experiment_02b/figures/fig_03_dominance_checks.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02b\fig_04_runtime.png` → `results/experiment_02b/figures/fig_04_runtime.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02b\fig_05_mixed_vs_independent_paired.png` → `results/experiment_02b/figures/fig_05_mixed_vs_independent_paired.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02b_dependence_3d_check.csv` → `results/experiment_02b/experiment_02b_dependence_3d_check.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02b_dependence_3d_raw.csv` → `results/experiment_02b/experiment_02b_dependence_3d_raw.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02b_mixed_vs_independent.csv` → `results/experiment_02b/experiment_02b_mixed_vs_independent.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_02b_summary.csv` → `results/experiment_02b/experiment_02b_summary.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03\experiment_03_correlations.csv` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/results/experiment_03/experiment_03_correlations.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03\experiment_03_descriptive_summary.csv` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/results/experiment_03/experiment_03_descriptive_summary.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03\experiment_03_predictor_correlations.csv` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/results/experiment_03/experiment_03_predictor_correlations.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03\experiment_03_regression_results.csv` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/results/experiment_03/experiment_03_regression_results.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03\experiment_03_route_count_groups.csv` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/results/experiment_03/experiment_03_route_count_groups.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03\fig_01_route_count_vs_pareto.png` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/results/experiment_03/fig_01_route_count_vs_pareto.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03\fig_02_route_count_vs_generated.png` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/results/experiment_03/fig_02_route_count_vs_generated.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03\fig_03_route_count_vs_checks.png` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/results/experiment_03/fig_03_route_count_vs_checks.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03\fig_04_route_count_vs_runtime.png` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/results/experiment_03/fig_04_route_count_vs_runtime.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03\fig_05_mean_diversity_vs_pareto.png` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/results/experiment_03/fig_05_mean_diversity_vs_pareto.png` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03_route_diversity_raw.csv` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/results/experiment_03_route_diversity_raw.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03a_route_quantity_raw.csv` → `results/experiment_03a/experiment_03a_route_quantity_raw.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03a_route_quantity_summary.csv` → `results/experiment_03a/experiment_03a_route_quantity_summary.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03b_overlap_position_analysis.csv` → `results/experiment_03b/experiment_03b_overlap_position_analysis.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03b_overlap_position_paired_analysis.csv` → `results/experiment_03b/experiment_03b_overlap_position_paired_analysis.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03b_overlap_position_raw.csv` → `results/experiment_03b/experiment_03b_overlap_position_raw.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\results\experiment_03b_overlap_position_summary.csv` → `results/experiment_03b/experiment_03b_overlap_position_summary.csv` — saved result; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\route_diversity_test.py` → `archive/original_sources/Mosp_vr1.1/experiments/route_diversity_test.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\figures\prefix_suffix_dominance_checks.pdf` → `results/experiment_03_comparison/figures/prefix_suffix_dominance_checks.pdf` — saved figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\figures\prefix_suffix_structure.pdf` → `results/experiment_03_comparison/figures/prefix_suffix_structure.pdf` — saved figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\figures\route_quantity_growth.pdf` → `results/experiment_03_comparison/figures/route_quantity_growth.pdf` — saved figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\src\brute_force.py` → `archive/original_sources/Mosp_vr1.1/src/brute_force.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\src\dominance.py` → `archive/original_sources/Mosp_vr1.1/src/dominance.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\src\graph.py` → `archive/original_sources/Mosp_vr1.1/src/graph.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\src\label.py` → `archive/original_sources/Mosp_vr1.1/src/label.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\src\mosp.py` → `archive/original_sources/Mosp_vr1.1/src/mosp.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\test_correctness.py` → `archive/original_sources/Mosp_vr1.1/test_correctness.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\check_stop_times.py` → `archive/original_sources/Real_case1/check_stop_times.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\data\臺北捷運相鄰兩站間之行駛時間及停靠站時間(1150830).csv` → `data/taipei_metro/臺北捷運相鄰兩站間之行駛時間及停靠站時間(1150830).csv` — formal model input; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\data\臺北捷運路線車站資料服務_NEW_fixed (1).csv` → `data/taipei_metro/臺北捷運路線車站資料服務_NEW_fixed (1).csv` — formal model input; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\data\臺北捷運轉乘車站轉乘步行時間資料.csv` → `data/taipei_metro/臺北捷運轉乘車站轉乘步行時間資料.csv` — formal model input; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\diagnose_taipei_route.py` → `archive/original_sources/Real_case1/diagnose_taipei_route.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiment_05_all_od.py` → `archive/original_sources/Real_case1/experiment_05_all_od.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\analyze_experiment_04b_route_patterns.py` → `archive/original_sources/Real_case1/experiments/analyze_experiment_04b_route_patterns.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\analyze_experiment_05_all.py` → `archive/original_sources/Real_case1/experiments/analyze_experiment_05_all.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\analyze_experiment_05b_objective_correlation.py` → `archive/original_sources/Real_case1/experiments/analyze_experiment_05b_objective_correlation.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\experiment_04_taipei_main.py` → `archive/original_sources/Real_case1/experiments/experiment_04_taipei_main.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\experiment_04_taipei_main_all.py` → `archive/original_sources/Real_case1/experiments/experiment_04_taipei_main_all.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\experiment_06_bruteforce_simple_paths.py` → `archive/original_sources/Real_case1/experiments/experiment_06_bruteforce_simple_paths.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\experiment_06b_all_od_dfs.py` → `archive/original_sources/Real_case1/experiments/experiment_06b_all_od_dfs.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\experiment_07_origin_level_dfs_vs_mosp.py` → `archive/original_sources/Real_case1/experiments/experiment_07_origin_level_dfs_vs_mosp.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\plot_chapter5.py` → `archive/original_sources/Real_case1/experiments/plot_chapter5.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\plot_chapter5_thesis.py` → `archive/original_sources/Real_case1/experiments/plot_chapter5_thesis.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\plot_chapter5_thesis_final (1).py` → `archive/original_sources/Real_case1/experiments/plot_chapter5_thesis_final (1).py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\all_od_pareto_routes.csv` → `results/experiment_05_all_od/all_od_pareto_routes.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\all_od_summary.csv` → `results/experiment_05_all_od/all_od_summary.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\analysis\max_pareto_od_pairs.csv` → `results/experiment_05_all_od/analysis/max_pareto_od_pairs.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\analysis\max_pareto_routes.csv` → `results/experiment_05_all_od/analysis/max_pareto_routes.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\analysis\pareto_validation.csv` → `results/experiment_05_all_od/analysis/pareto_validation.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\analysis\representative_case_candidates.csv` → `results/experiment_05_all_od/analysis/representative_case_candidates.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\analysis\suspected_duplicate_routes.csv` → `results/experiment_05_all_od/analysis/suspected_duplicate_routes.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures\figure_5_2_pareto_set_distribution.png` → `results/experiment_05_all_od/chapter5_figures/figure_5_2_pareto_set_distribution.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures\figure_5_3_station_multi_pareto_rate.png` → `results/experiment_05_all_od/chapter5_figures/figure_5_3_station_multi_pareto_rate.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures\figure_5_4_frequency_vs_richness.png` → `results/experiment_05_all_od/chapter5_figures/figure_5_4_frequency_vs_richness.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures\figure_5_5_pareto_size_vs_time_range.png` → `results/experiment_05_all_od/chapter5_figures/figure_5_5_pareto_size_vs_time_range.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures\figure_5_6_pareto_size_vs_walking_range.png` → `results/experiment_05_all_od/chapter5_figures/figure_5_6_pareto_size_vs_walking_range.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures\figure_5_6_pareto_size_vs_walking_range_thesis.png` → `results/experiment_05_all_od/chapter5_figures/figure_5_6_pareto_size_vs_walking_range_thesis.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures\pareto_tradeoff_summary.csv` → `results/experiment_05_all_od/chapter5_figures/pareto_tradeoff_summary.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_2_pareto_set_distribution.pdf` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_2_pareto_set_distribution.pdf` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_2_pareto_set_distribution.png` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_2_pareto_set_distribution.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_3_station_multi_pareto_rate.pdf` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_3_station_multi_pareto_rate.pdf` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_3_station_multi_pareto_rate.png` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_3_station_multi_pareto_rate.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_4_frequency_vs_richness.pdf` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_4_frequency_vs_richness.pdf` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_4_frequency_vs_richness.png` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_4_frequency_vs_richness.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_5_pareto_size_vs_time_range.pdf` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_5_pareto_size_vs_time_range.pdf` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_5_pareto_size_vs_time_range.png` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_5_pareto_size_vs_time_range.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_6_pareto_size_vs_walking_range.pdf` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_6_pareto_size_vs_walking_range.pdf` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_6_pareto_size_vs_walking_range.png` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_6_pareto_size_vs_walking_range.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_7_donghu_zhongyuan_route_schematic.pdf` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_7_donghu_zhongyuan_route_schematic.pdf` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_7_donghu_zhongyuan_route_schematic.png` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_7_donghu_zhongyuan_route_schematic.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_8_donghu_zhongyuan_tradeoff.pdf` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_8_donghu_zhongyuan_tradeoff.pdf` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_8_donghu_zhongyuan_tradeoff.png` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_8_donghu_zhongyuan_tradeoff.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_9_network_practical_tradeoff.pdf` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_9_network_practical_tradeoff.pdf` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_9_network_practical_tradeoff.png` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_9_network_practical_tradeoff.png` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\figure_5_9_network_tradeoff_data.csv` → `results/experiment_05_all_od/chapter5_figures_thesis/figure_5_9_network_tradeoff_data.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\chapter5_figures_thesis\pareto_tradeoff_summary.csv` → `results/experiment_05_all_od/chapter5_figures_thesis/pareto_tradeoff_summary.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\destination_summary.csv` → `results/experiment_05_all_od/destination_summary.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\multi_pareto_od_pairs.csv` → `results/experiment_05_all_od/multi_pareto_od_pairs.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\origin_summary.csv` → `results/experiment_05_all_od/origin_summary.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\pareto_set_size_distribution.csv` → `results/experiment_05_all_od/pareto_set_size_distribution.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\results\experiment_05_all_od\source_mosp_statistics.csv` → `results/experiment_05_all_od/source_mosp_statistics.csv` — saved All-OD result/analysis/figure; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\plot_chapter5_figures_7_9.py` → `archive/original_sources/Real_case1/plot_chapter5_figures_7_9.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\plot_chapter5_figures_7_9_final.py` → `archive/original_sources/Real_case1/plot_chapter5_figures_7_9_final.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\src\brute_force.py` → `archive/original_sources/Real_case1/src/brute_force.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\src\dominance.py` → `archive/original_sources/Real_case1/src/dominance.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\src\graph.py` → `archive/original_sources/Real_case1/src/graph.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\src\label.py` → `archive/original_sources/Real_case1/src/label.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\src\mosp.py` → `archive/original_sources/Real_case1/src/mosp.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\src\taipei_metro.py` → `archive/original_sources/Real_case1/src/taipei_metro.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\.gitignore` → `web/taipei-pareto-explorer/.gitignore` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\backend\.env.example` → `web/taipei-pareto-explorer/backend/.env.example` — website; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\backend\cache\taipei_metro_station_positions.csv` → `data/taipei_metro/taipei_metro_station_positions.csv` — website coordinate input (not a model input); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\backend\main.py` → `archive/original_sources/Real_case1/taipei-pareto-explorer/backend/main.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\backend\main.py` → `web/taipei-pareto-explorer/backend/main.py` — website; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\backend\requirements.txt` → `web/taipei-pareto-explorer/backend/requirements.txt` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\frontend\index.html` → `web/taipei-pareto-explorer/frontend/index.html` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\frontend\package-lock.json` → `web/taipei-pareto-explorer/frontend/package-lock.json` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\frontend\package.json` → `web/taipei-pareto-explorer/frontend/package.json` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\frontend\src\api.js` → `web/taipei-pareto-explorer/frontend/src/api.js` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\frontend\src\App.jsx` → `web/taipei-pareto-explorer/frontend/src/App.jsx` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\frontend\src\components\MetroMap.jsx` → `web/taipei-pareto-explorer/frontend/src/components/MetroMap.jsx` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\frontend\src\components\RoutePanel.jsx` → `web/taipei-pareto-explorer/frontend/src/components/RoutePanel.jsx` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\frontend\src\components\TradeoffPlot.jsx` → `web/taipei-pareto-explorer/frontend/src/components/TradeoffPlot.jsx` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\frontend\src\main.jsx` → `web/taipei-pareto-explorer/frontend/src/main.jsx` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\frontend\src\styles.css` → `web/taipei-pareto-explorer/frontend/src/styles.css` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\frontend\vite.config.js` → `web/taipei-pareto-explorer/frontend/vite.config.js` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\README.md` → `web/taipei-pareto-explorer/README.md` — website; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\start_backend.ps1` → `web/taipei-pareto-explorer/start_backend.ps1` — website; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\taipei-pareto-explorer\start_frontend.ps1` → `web/taipei-pareto-explorer/start_frontend.ps1` — website; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\test_taipei_case.py` → `archive/original_sources/Real_case1/test_taipei_case.py` — original source snapshot (not executable canonical code); byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\src\graph.py` → `src/graph.py` — canonical shared core, identical in both sources; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\src\label.py` → `src/label.py` — canonical shared core, identical in both sources; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\src\dominance.py` → `src/dominance.py` — canonical shared core, identical in both sources; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\src\mosp.py` → `src/mosp.py` — canonical shared core, identical in both sources; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\src\brute_force.py` → `src/brute_force.py` — canonical shared core, identical in both sources; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Real_case1\src\taipei_metro.py` → `src/taipei_metro.py` — only route-state model source; byte-preserved; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_01_objectives.py` → `experiments/synthetic/experiment_01.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_02a_correlation.py` → `experiments/synthetic/experiment_02a.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_02b_dependence_3d.py` → `experiments/synthetic/experiment_02b.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_03a_route_quantity.py` → `experiments/synthetic/experiment_03a.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_03b_route_overlap.py` → `experiments/synthetic/experiment_03b.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\analyze_experiment_01.py` → `analysis/synthetic/analyze_experiment_01.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\analyze_experiment_02a.py` → `analysis/synthetic/analyze_experiment_02a.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\analyze_experiment_02b.py` → `analysis/synthetic/analyze_experiment_02b.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\analyze_experiment_03.py` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/analyze_experiment_03.py` — historical experiment; no canonical selection inferred; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\analyze_experiment_03a.py` → `analysis/synthetic/analyze_experiment_03a.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\analyze_experiment_03b.py` → `analysis/synthetic/analyze_experiment_03b.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_03_redundancy.py` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/experiment_03_redundancy.py` — historical experiment; no canonical selection inferred; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\experiment_03_route_diversity.py` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/experiment_03_route_diversity.py` — historical experiment; no canonical selection inferred; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\plot_experiment_01.py` → `analysis/synthetic/plot_experiment_01.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\plot_experiment_02a.py` → `analysis/synthetic/plot_experiment_02a.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\plot_experiment_02b.py` → `analysis/synthetic/plot_experiment_02b.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\plot_experiment_03.py` → `analysis/synthetic/plot_experiment_03.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\experiments\route_diversity_test.py` → `archive/deprecated_candidates/Mosp_vr1.1/experiments/route_diversity_test.py` — historical experiment; no canonical selection inferred; byte-preserved.
- `C:\Users\xAdmin\MOSP_project\Mosp_vr1.1\test_correctness.py` → `validation/test_correctness.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\check_stop_times.py` → `analysis/real_case/check_stop_times.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\diagnose_taipei_route.py` → `analysis/real_case/diagnose_taipei_route.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiment_05_all_od.py` → `experiments/real_case/experiment_05_all_od.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\plot_chapter5_figures_7_9.py` → `analysis/real_case/plot_chapter5_figures_7_9.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\plot_chapter5_figures_7_9_final.py` → `analysis/real_case/plot_chapter5_figures_7_9_final.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\test_taipei_case.py` → `analysis/real_case/test_taipei_case.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\analyze_experiment_04b_route_patterns.py` → `analysis/real_case/analyze_experiment_04b_route_patterns.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\analyze_experiment_05b_objective_correlation.py` → `analysis/real_case/analyze_experiment_05b_objective_correlation.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\analyze_experiment_05_all.py` → `analysis/real_case/analyze_experiment_05_all.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\experiment_04_taipei_main.py` → `experiments/real_case/experiment_04_taipei_main.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\experiment_04_taipei_main_all.py` → `experiments/real_case/experiment_04_taipei_main_all.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\experiment_06b_all_od_dfs.py` → `experiments/real_case/experiment_06b_all_od_dfs.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\experiment_06_bruteforce_simple_paths.py` → `experiments/real_case/experiment_06_bruteforce_simple_paths.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\experiment_07_origin_level_dfs_vs_mosp.py` → `experiments/real_case/experiment_07_origin_level_dfs_vs_mosp.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\plot_chapter5.py` → `analysis/real_case/plot_chapter5.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\plot_chapter5_thesis.py` → `analysis/real_case/plot_chapter5_thesis.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\MOSP_project\Real_case1\experiments\plot_chapter5_thesis_final (1).py` → `analysis/real_case/plot_chapter5_thesis_final.py` — canonical script; only imports/paths/entry point changed; modified paths/imports/entry point.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\brute_force.py.diff` → `audit/brute_force.py.diff` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\dependencies.json` → `audit/dependencies.json` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\dominance.py.diff` → `audit/dominance.py.diff` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\duplicates.json` → `audit/duplicates.json` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\graph.py.diff` → `audit/graph.py.diff` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\inventory.csv` → `audit/inventory.csv` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\inventory.json` → `audit/inventory.json` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\label.py.diff` → `audit/label.py.diff` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\mosp.py.diff` → `audit/mosp.py.diff` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\Mosp_vr1.1_tree.txt` → `audit/Mosp_vr1.1_tree.txt` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\path_audit.json` → `audit/path_audit.json` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\preflight.json` → `audit/preflight.json` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\preflight_routes.json` → `audit/preflight_routes.json` — pre-migration audit evidence; byte-preserved.
- `C:\Users\xAdmin\.codex\visualizations\2026\09\30\01a0f2fd-3f3d-7192-83e4-2f2f74955234\migration_support\audit\Real_case1_tree.txt` → `audit/Real_case1_tree.txt` — pre-migration audit evidence; byte-preserved.

## Post-migration backend environment repair (2026-10-01)

The user's separate Python 3.13 backend `.venv` contained the pinned website
dependencies but did not contain `mosp-research`; therefore `uvicorn main:app`
failed on `from src.paths import ...`. The previous ASGI regression ran in the
isolated migration test environment and did not cover this newly created venv.
Installed only the canonical package via this venv's `python -m pip install
--no-deps -e <canonical root>`. No solver, modelling, input or formal-result files
were changed. Updated web README with explicit independent-venv setup.

Retested using the actual Python 3.13.15 backend environment with Uvicorn 0.34.0
and `--reload`: spawned server process successfully imported the canonical package;
live localhost `/api/health` returned HTTP 200/ok, all 119 station coordinates
matched, and 東湖站→中原站 returned 5 routes. The test ran from an external cwd
on a temporary free port and stopped only its own temporary process tree.
Evidence: `regression/backend_environment_fix.json` and
`regression/backend_reload_smoke.log`.

## Systematic research package / interpreter repair (2026-10-01)

Created the root research `.venv` using the user's Python 3.13.15 and installed the
canonical repository editable with research/web/test dependencies. Root `src` was
already a real package; the failure came from missing installation in the chosen
interpreter, not a need to change scientific code or move the core again. Package
discovery now explicitly includes all root research packages/subpackages, disables
implicit namespaces and excludes archives/data/results/web. No PYTHONPATH or
script-level sys.path workaround was added.

Added Windows setup and installation verification, explicit venv commands in the
README, and shared synthetic smoke dispatch under existing main guards. Default
scientific functions/constants remain AST-identical to the pre-repair version.
The setup script was actually run from an external cwd and verified 50 modules.

All 17 requested/extended Python commands passed in the root Python 3.13 venv,
including 1000/1000 correctness, 23 synthetic smoke conditions matching saved
statistics, one-origin and complete All-OD, external/isolated imports, direct-file
execution from root/external cwd, and comprehensive migration/API regression.
Complete All-OD has 119 origins, 14042 ODs and 22052 routes; all seven CSVs match
all saved non-runtime fields exactly. Protected core/model/data/formal-result
hashes remain unchanged. No algorithm, experimental setting or research result
was changed. The only retained sys.path hack is in an excluded original archive.

See `PACKAGE_IMPORT_REPORT.md` for the full requested ten-part report and full
pyproject/install/run commands. Evidence: `regression/package_fix/verification.json`,
`installation.json`, per-command logs, baseline and diff. Source provenance hashes
in the migration manifest are preserved; destination hashes for changed canonical
entry points are updated. Original projects remain untouched.

## Responsive and Render deployment preparation (2026-10-01)

Frontend changes add responsive CSS/layout, viewport/safe-area handling, map resize behavior and accessible touch controls. API configuration uses `VITE_API_BASE_URL`; local Vite dev/preview proxies `/api`. Backend CORS uses `FRONTEND_ORIGIN` plus localhost:5173; health diagnostics redact absolute paths. No solver, model, scientific setting or formal result file changed. The original projects remain untouched.

Local fresh-environment installation, imports, live health/CORS, representative API data equality, frontend clean installation/build and 1000/1000 correctness checks passed. Actual public deployment is authorized but in progress after successful GitHub and Render CLI authentication. See `DEPLOYMENT.md`, `RESPONSIVE_REPORT.md` and `regression/deployment/verification.json`. Remaining device/browser tests are explicitly pending.

Did this refactor change any algorithm, experimental setting, or research result? **No.**

## Public Render deployment (2026-10-01)

GitHub: https://github.com/jockh/MOSP_research; frontend: https://taipei-pareto-explorer.onrender.com; backend: https://mosp-taipei-api.onrender.com. Backend free and Static Site live; public health/CORS/data API and five-route OD checks passed. render.yaml validated without application. Browser UI tests are blocked by the explicit domain access denial and remain pending. Research bytes/settings/algorithm remain unchanged.
