# FactorLab CI 运行效率与等价性验证

状态：IN_PROGRESS。2026-10-16，Python 3.9，NO LIVE MONEY。
本文件随阶段更新；尚未完成的实验和未知指标不得视为验收通过。

## 1. 基线与证据来源

PR #8 已由用户人工合并。冻结 main 为 `94baf83e993b47344caa12772b65c646da4e09d0`，
源码树为 `4999830db8b05e0d9d98302cb2b791308df7039d`。

- [原 main 研究 CI](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38832198178)：3141 passed、1 skipped、2 deselected；pytest 1053.86 秒；工作流从创建至完成约1133秒。
- [原 main 静态 CI](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38832198018)：通过。
- 原 coverage：15988 / 18730 行，85.36%；真实报告无百分比验收阈值。
- 分支保护与 ruleset API：HTTP 403，UNKNOWN；用户另行人工确认 main 无必需检查和 merge queue。两类来源分开记录。

清单已在干净、精确 SHA 的独立基线 worktree 收集，并在匹配 CI 固定工具版本的 Python 3.9.25 环境复核。
全部3144项，离线选中3142项，network排除2项；没有重复 node ID。

- 选中集合 SHA256：`218c1838040a3d0fe09e1f1b550059c4e2d0cf1640b203ddeab6c1732fee9183`。
- 完整集合 SHA256：`939d4990560dd451755abb0fe5b9bc130d062004413231b5bc862a6759b6fb6b`。
- 排除集合 SHA256：`4bdd45acea8c468d35c684b233cbd0c2866f40b0fd723d74cf59f429627b0e9d`。

规范化为原始node ID排序、UTF-8、LF和末尾换行。
[冻结合同](evidence/ci-runtime-optimization-v1/baseline-collection.json)绑定原 main 的实际JUnit结果、跳过原因和133份coverage源码的可测行清单。
[源码哈希](evidence/ci-runtime-optimization-v1/baseline-source-sha256.json)保留优化前320份研究、测试、示例、配置与依赖文件的原始字节摘要。

## 2. 原工作流拓扑与重复运行

| 工作流 / job | 原自动事件 | 原执行及失败传播 |
|---|---|---|
| FactorLab research tests / phase-1-offline / Python 3.9 offline suite | 不限分支Push；不限目标分支PR；两者均有路径过滤 | 完整离线pytest、coverage、真实报告验证、配置/架构审计；命令失败使job失败，always上传不改变结果 |
| FactorLab static checks / research-static / Research syntax and static checks | main及codex分支Push；main PR；均有路径过滤 | 完整研究依赖安装、Python编译、Flake8、变更空白、CI脚本Black、合同测试 |
| FactorLab workflow validation / actionlint | main及codex分支Push；PR；均有路径过滤 | SHA256固定actionlint，检查全部活动workflow与可选CodeQL模板 |

开发分支更新且已有PR时，Push与pull_request会分别产生研究验证。原研究concurrency以github.ref分组，
分支ref与PR merge ref不同，不能去重；同分支手动dispatch又与Push共组，可能互相取消。

## 3. 触发策略与保护规则兼容性

触发修改已完成，事件/分支/路径合同通过，开发分支新提交未产生额外Push验证；PR入口真实验证待后续Draft PR。策略为main Push、面向main的所有PR和手动完整验证；
开发分支Push不再额外启动三个验证工作流。保留检查名称，移除路径过滤，所有PR路径均实际验证。
手动诊断独立分组，不替代PR验收；main与诊断按run ID隔离，只有同一PR的synchronize新提交可取消旧验证；标题/正文编辑不取消正在运行的验证。edited事件用于覆盖PR重新定向到main，元数据编辑也会实际重验。
人工合并前不能声称新main Push策略已有实际合并后运行记录。

## 4. 测量方法、冷/热缓存与环境

使用独立Actions被测worktree，原基线研究源码、测试和依赖不变，分别记录控制代码及被测SHA。
命令由benchmark.py执行完整 `tests/research -q -m "not network"`，保留durations=40、durations-min=0、JUnit及coverage。

两轮热pip缓存、一轮冷pip缓存及完整无coverage对照已完成，全部3141 passed、1 skipped、2 deselected，完整工作流均通过。热缓存仅指pip下载缓存，
每个Runner仍重新安装依赖，未复用研究结果。实际cache hit以setup-python日志为准。
独立cProfile运行不计入加速对照，inclusive时间不相加。

Windows隔离环境由现有研究包副本建立，再安装与CI一致的pytest-cov 6.2.1、coverage 7.10.6；
所有研究固定版本及pip check已验证。此前两次numpy wheel下载未通过SHA256校验，均被拒绝，未绕过校验。
本地安装过程不能作为Linux依赖安装性能数据。

## 5. 最慢40阶段与耗时分解

| 条件 | pytest进程墙钟秒 | 完整诊断工作流秒 | 安装秒 | 行覆盖率 |
|---|---:|---:|---:|---:|
| [热缓存1 / coverage](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38862847746) | 1181.384 | 1262 | 36 | 0.8536 |
| [热缓存2 / coverage](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38862851687) | 896.872 | 990 | 38 | 0.8536 |
| [冷缓存 / coverage](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38862855654) | 1222.650 | 1299 | 38 | 0.8536 |
| [热缓存 / 无coverage](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38862859060) | 709.410 | 809 | 39 | 不适用 |

四轮Python 3.9.25、完整依赖版本和测试集合一致；Runner镜像20261012.334.1、2 vCPU。热coverage两轮仍有明显CPU/墙钟波动，不能据单轮差分认定优化收益。无coverage观测差分约187–472秒，包含Runner波动，覆盖率成本仅作粗估。

完整阶段表见[最慢40项CSV](evidence/ci-runtime-optimization-v1/baseline-phase-top40.csv)。

| 排名 | 阶段 | 秒 | node ID |
|---:|---|---:|---|
| 1 | call | 109.759 | `tests/research/test_cli_phase2.py::test_walk_forward_and_compare_commands_are_offline_and_complete` |
| 2 | call | 40.828 | `tests/research/test_phase2_synthetic_example.py::test_synthetic_demo_runs_both_models_and_marks_everything_synthetic` |
| 3 | call | 28.618 | `tests/research/test_factor_performance_diagnostic.py::test_paired_benchmark_runs_both_implementations_in_fresh_processes` |
| 4 | setup | 28.576 | `tests/research/test_factor_discovery_integration.py::test_actual_40_record_full_loop_and_artifacts_verified` |
| 5 | call | 28.162 | `tests/research/test_factor_discovery_integration.py::test_actual_repeat_same_hashes_normalized_asts_and_numerical_outputs` |
| 6 | call | 23.136 | `tests/research/test_factor_discovery_integration.py::test_development_outputs_invariant_to_post_development_prices_and_labels` |
| 7 | call | 22.128 | `tests/research/test_phase3_synthetic_example.py::test_phase3_synthetic_demo_runs_complete_offline_path` |
| 8 | call | 19.186 | `tests/research/test_cli_phase2.py::test_walk_forward_pins_bar_generation_before_model_run` |
| 9 | call | 17.020 | `tests/research/test_walk_forward_runner_phase2.py::test_ridge_alpha_and_test_scores_do_not_depend_on_test_labels` |
| 10 | call | 12.319 | `tests/research/test_exploratory_safety.py::test_runner_factors_regimes_and_sample_do_not_depend_on_future_rows` |
| 11 | call | 11.281 | `tests/research/test_five_year_pilot.py::test_repeated_execution_retains_receipts_and_resumes_cache` |
| 12 | call | 10.838 | `tests/research/test_factor_discovery_integration.py::test_original14_redundancy_independent_daily_pearson_recalculation` |
| 13 | call | 10.399 | `tests/research/test_five_year_pilot.py::test_later_explicit_run_rebuilds_csi_from_latest_success_after_429` |
| 14 | call | 8.457 | `tests/research/test_walk_forward_runner_phase2.py::test_ridge_candidates_fit_train_only_and_selected_model_is_not_refit` |
| 15 | call | 8.347 | `tests/research/test_five_year_pilot.py::test_cache_source_identity_mismatch_is_auditable_not_relabelled` |
| 16 | call | 6.807 | `tests/research/test_five_year_pilot.py::test_later_explicit_run_can_recover_after_stock_access_denial[403]` |
| 17 | call | 6.690 | `tests/research/test_five_year_pilot.py::test_later_explicit_run_can_recover_after_stock_access_denial[429]` |
| 18 | call | 6.686 | `tests/research/test_five_year_pilot.py::test_later_explicit_run_can_recover_after_stock_access_denial[401]` |
| 19 | call | 6.479 | `tests/research/test_five_year_pilot.py::test_concurrent_entry_fails_before_recorder_http_or_evidence_mutation` |
| 20 | call | 6.255 | `tests/research/test_factor_discovery_integration.py::test_generic_factor_math_exactly_reused_not_a_second_ic_formula` |
| 21 | call | 6.133 | `tests/research/test_exploratory_safety.py::test_runner_reindexes_missing_session_without_skipping_calendar_offsets` |
| 22 | call | 5.878 | `tests/research/test_five_year_pilot.py::test_warmup_only_native_benchmark_failure_clears_calendar_after_assignment` |
| 23 | call | 5.785 | `tests/research/test_cli_phase2.py::test_evaluate_records_verified_dataset_provenance` |
| 24 | setup | 5.697 | `tests/research/test_model_stage_diagnostics_report.py::test_complete_stage_artifacts_preserve_selected_scores_and_test_only_outputs` |
| 25 | call | 5.648 | `tests/research/test_five_year_pilot.py::test_partial_pilot_preserves_missing_failed_and_short_history` |
| 26 | call | 5.567 | `tests/research/test_five_year_pilot.py::test_benchmark_cache_without_native_evidence_cannot_supply_calendar` |
| 27 | call | 5.383 | `tests/research/test_five_year_pilot.py::test_unit_or_calendar_failure_does_not_grant_analysis_ready_data[bad-units]` |
| 28 | call | 5.227 | `tests/research/test_five_year_pilot.py::test_unit_or_calendar_failure_does_not_grant_analysis_ready_data[weekend]` |
| 29 | call | 5.219 | `tests/research/test_forward_evaluation_synthetic_example.py::test_module_cli_runs_real_production_apis_from_another_cwd` |
| 30 | setup | 5.072 | `tests/research/test_five_year_pilot.py::test_v3_calendar_scope_cannot_claim_independent_completeness` |
| 31 | setup | 5.053 | `tests/research/test_five_year_pilot.py::test_benchmark_native_url_status_layout_and_body_cannot_be_rebound_to_cache[url]` |
| 32 | setup | 4.936 | `tests/research/test_five_year_pilot.py::test_benchmark_native_url_status_layout_and_body_cannot_be_rebound_to_cache[http-status]` |
| 33 | setup | 4.932 | `tests/research/test_five_year_pilot.py::test_benchmark_native_url_status_layout_and_body_cannot_be_rebound_to_cache[period]` |
| 34 | setup | 4.927 | `tests/research/test_five_year_pilot.py::test_legacy_schema_cannot_self_assert_native_benchmark_qualification` |
| 35 | setup | 4.926 | `tests/research/test_five_year_pilot.py::test_benchmark_native_url_status_layout_and_body_cannot_be_rebound_to_cache[body-price]` |
| 36 | setup | 4.925 | `tests/research/test_five_year_pilot.py::test_rehashed_benchmark_cache_and_calendar_must_match_fixed_native_response[extra-session]` |
| 37 | setup | 4.921 | `tests/research/test_five_year_pilot.py::test_benchmark_native_url_status_layout_and_body_cannot_be_rebound_to_cache[index-code]` |
| 38 | setup | 4.912 | `tests/research/test_five_year_pilot.py::test_rehashed_benchmark_cache_and_calendar_must_match_fixed_native_response[price]` |
| 39 | setup | 4.906 | `tests/research/test_five_year_pilot.py::test_native_csi_layout_binds_dates_prices_units_and_calendar` |
| 40 | call | 4.817 | `tests/research/test_tdx_delivery_seal.py::test_all_published_tdx_files_in_clean_checkout` |
原main JUnit中最慢单项合计102.317秒，仅用于选择诊断入口，不能解释为纯训练耗时。
采样的CPU、RSS、物理内存余量及报告生成数据以实测结果为准；不可测指标为UNKNOWN。

## 6. 串行优化与测试语义

研究实现保持不变。静态job拆分为最小固定依赖；在无NumPy/Pandas/LightGBM的新环境中，原编译、Flake8、Black及52项合同全部通过。

[静态测量收据](evidence/ci-runtime-optimization-v1/static-runs.json)保留原main、最小依赖仍用缓存以及关闭缓存三个阶段。
原main完整workflow95秒、job91秒、安装35秒；关闭静态pip缓存后两轮为workflow54/47秒、job49/44秒、安装4/3秒。
19个工具包在每轮全新Python环境实际安装，未安装科学计算栈；setup-python原先会按回退key恢复科学计算下载缓存，因此静态job关闭该缓存。
研究job缓存不变。上述是实际观测，Runner检出等仍有波动，不把差值全部归因于单个变量。

唯一测试准备优化为test_cli_phase2._inputs：原配方保持原样，按配方版本及NumPy/Pandas版本缓存进程内pickle不可变字节，每次解码得到独立对象。与Git绑定的原main配方逐值、数值原始字节、dtype、索引、频率和attrs校验，并验证修改不会污染下次调用。390交易日，数据/股票bar/基准分别3900/5100/510行，规模不变。没有缓存训练、被测验证、收据或文件。45项所属文件测试通过。

串行候选为 `11ce72b93c44c83041d4faaf34798dd6c77851dc`。
[干净提交的等价收据](evidence/ci-runtime-optimization-v1/fixture-equivalence-11ce72b.json)中，10次输入准备的两个配对微测量分别由0.795/1.578秒降至0.004/0.010秒；
该结果只说明重复输入构造被消除，不外推完整CI提速比例。320份冻结文件中仅此测试准备文件发生变化，研究实现和研究依赖文件未变。

独立119项热点profile中：schema canonicalize_bars 6627次、134.456秒inclusive；validate_bars 7791次、116.154秒inclusive；acquire_pilot 59次、138.778秒inclusive；_inputs 83次、12.816秒inclusive。以上嵌套时间不能相加。Ridge/LightGBM/XGBoost fit各37/15/15次、0.092/0.119/0.140秒inclusive，未显示训练为该样本瓶颈。
51个pytest fixture中已有5个模块级fixture；不能假设所有重复调用都可安全复用。
训练调用次数、独立重跑、防泄漏变异比较、序列化和哈希验证仍须实际执行。

同一热点profile另测：Parquet读3176次、6.020秒inclusive，写1723次、6.256秒；savefig 83次、13.762秒；
exploratory.contract.sha256_file 21606次、0.645秒。它们均包含部分嵌套调用，不能与schema、pilot时间相加。
这些操作仍属真实证据生成与核验，本次未缓存或绕过；五年pilot收据绑定绝对路径和原生响应，未强行复用其可写产物。

## 7. 并行资源审计与实验

完整并行实验待串行对照完成。候选为串行、固定pytest-xdist 3.8.0的2/3 Workers，按loadfile分配。
文件锁、generation和收据操作保留原合同；可写目录按测试/Worker隔离，Worker崩溃不自动重启。
进程树RSS含共享页重复计数的可能，另采样MemAvailable及可读cgroup限制。
采用并行前必须实测满足至少20%内存余量；无法可靠测量则不宣告资源门禁通过。

Windows的2/3 Workers高风险预检各452项通过，分别30.80/31.06秒，见[独立预检收据](evidence/ci-runtime-optimization-v1/parallel-preflights.json)。
该子集包含cache/PIT并发发布、Forward锁、Golden及Ridge/树模型；它不是完整套件验收或加速对照。
独立审计未发现跨Worker可写根：tmp_path/tmp_path_factory由xdist隔离，monkeypatch作用于各进程，模块fixture由loadfile保留在单一Worker。
现有5秒屏障、15秒子进程启动期限等不放宽。模型原有种子、单线程参数及LightGBM deterministic保持原值。
BLAS/OpenMP线程1是独立实验变量，必须与同样线程1的串行运行比较。

activation.py第163/164行对应真实O_EXCL锁争用；失败线程也可在获得已释放的锁后发现收据已存在，两者都满足原“一胜一负”断言。
若实验未覆盖前一时序，覆盖率合同继续拒绝，不自动豁免，不挑选一次偶然通过来声称稳定。

## 8. 优化前后等价性与性能对照

待填写每轮精确SHA、Python/依赖、node ID哈希、计数、pytest及CI墙钟、安装、coverage、CPU和内存。
保留全部轮次、冷/热条件和失败样本，不从不同测试集合、缓存命中或Runner波动推导确定收益。

## 9. 金融安全边界

原14因子、39自动发现候选冻结结果、Golden、历史收据、PIT、HFQ与公司行为、证券身份状态、
统计接受/拒绝条件、walk-forward边界及防泄漏、Forward时间门禁、交易执行和NO LIVE MONEY均须保持不变。
CI性能证据和软件覆盖率不授予金融数据或实盘资格。

## 10. 失败传播与反例

采样器返回真实pytest退出码。执行证据逐项对账冻结集合、Worker报告、阶段、JUnit及coverage源码行。
已通过52项CI合同测试，包括真实小型pytest观察、重复/遗漏执行、损坏/缺失JUnit、虚假汇总、
新增skip、错误skip原因、错误SHA/tree、脏被测目录、Worker异常及coverage遗漏/汇总不一致反例。
合成反例仅存在于unittest临时目录，不上传为研究CI证据。

## 11. 运行记录与回退

- 首次手动coverage诊断38860581121在启动前被同分支第二次dispatch取消；不作为性能样本。
- 原首个开发分支研究Push 38860579317在提交被替代后取消；不计作有效性能对照。
- 两轮热coverage基线：[38860726713](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38860726713)、[38860729763](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38860729763)。
- 冷coverage基线：[38860732989](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38860732989)。
- 无coverage基线：[38860584439](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38860584439)。
- 独立完整cProfile：[38861324711](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38861324711)。

上述早期诊断因pytest根目录/配置取自父checkout而被清单校验拒绝，保持原始失败状态，不用于加速验收。修复后重新采集的有效四轮为38862847746、38862851687、38862855654、38862859060；119项固定热点profile为38863504342，明确不作为完整CI或加速对照。Windows原始三失败保留，使用D盘新临时根后五轮锁窄测及完整基线均通过：3142 passed、0 skipped、2 deselected，覆盖16012/18730行（85.49%）。Windows本地CPU/RSS不可测为UNKNOWN；不将26分钟本地结果与Linux直接比较。完整下载、日志、XML和校验收据放在独立本地审计目录及对应Actions artifacts。

## 12. 独立Codex复审与最终结论

中期独立预审发现三项P1：未强制比较平台执行/覆盖范围、收据来源未校验、coverage逐行hits与汇总未对账。
已加入冻结平台合同、精确SHA/tree绑定及逐行汇总交叉验证，并扩展反例；最终HEAD复审待完成。
P3输入复用另经独立只读复审：原构造体和45项测试主体保持不变；逐列无共享数组，并额外修改日期数组、索引名、attrs验证下一次调用仍精确相同，未发现P0/P1。
最终状态与遗留风险将在远程全量验证及最终独立复审完成后填写。

## 13. 独立复跑

以下命令均从完整Git历史的独立checkout执行，Python为3.9.25，输出目录必须不存在：

```bash
python -m pip install -r dev/requirements-research-ci.txt
python -m pip check
python .github/scripts/ci/benchmark.py --output results/diagnostics/reproduce --workers 0
python .github/scripts/ci/validate_execution.py results/diagnostics/reproduce \
  --expected docs/research/evidence/ci-runtime-optimization-v1/baseline-collection.json
python .github/scripts/ci/validate_reports.py results/diagnostics/reproduce/coverage.xml \
  results/diagnostics/reproduce/research.xml
python .github/scripts/ci/validate_fixture_equivalence.py \
  --contract-root docs/research/evidence/ci-runtime-optimization-v1 \
  --output results/diagnostics/reproduce/fixture-equivalence.json
python .github/scripts/ci/summarize_runtime.py results/diagnostics/reproduce
```

手动远程采样使用现有research-tests.yml的workflow_dispatch，mode=benchmark，明确指定40位subject_sha、workers、coverage、pip_cache、profile和threads。
默认mode=verify执行真正完整coverage验证。profile=true仅运行固定119项热点用于定位，元数据和job名称均明确其不具验收资格。
下载与汇总用download_runtime_evidence.py和compile_runtime_receipts.py；原始ZIP、XML、完整版本、阶段和进程记录保存在对应Actions artifacts，聚合收据列出文件SHA256。
基线清单仅可在合法新增测试或研究源码变更后，经完整重新冻结与独立复审更新；不得为通过性能验收修改期望清单。
