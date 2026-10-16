# FactorLab CI 运行效率与等价性验证

状态：PARTIAL方案（保留串行，并行回退）。2026-10-16，Python 3.9，NO LIVE MONEY。
本报告记录已完成的对照及代码验收；最终文档提交的HEAD、PR合并测试SHA、运行链接和独立复审结论在[Draft PR #9](https://github.com/Wind-Maker1001/quant-tv/pull/9)的最终验收收据中单独绑定。未完成运行和UNKNOWN不得视为通过；不在文件中伪造它自身提交之后才会产生的Actions结果。

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

[真实重复事件收据](evidence/ci-runtime-optimization-v1/historical-duplicate-events.json)：同一原开发提交的研究Push [38726792784](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38726792784)与PR [38726798060](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38726798060)分别成功，几乎同时启动。去重收益针对同时满足原路径过滤且已有main PR的开发提交：完整研究运行2次降为1次。不外推整个仓库所有事件的总用量，因为纯文档PR现在也会真实全量验证。

## 3. 触发策略与保护规则兼容性

触发修改已完成，事件/分支/路径合同通过，开发分支新提交未产生额外Push验证；Draft PR #9已实际启动全部三个验证workflow。策略为main Push、面向main的所有PR和手动完整验证；
开发分支Push不再额外启动三个验证工作流。保留检查名称，移除路径过滤，所有PR路径均实际验证。
手动诊断独立分组，不替代PR验收；main与诊断按run ID隔离，只有同一PR的synchronize新提交可取消旧验证；标题/正文编辑不取消正在运行的验证。edited事件用于覆盖PR重新定向到main，元数据编辑也会实际重验。
人工合并前不能声称新main Push策略已有实际合并后运行记录。

GitHub说明[路径过滤可能使必需检查停留Pending](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)，因此移除过滤而非空作业报绿；手动dispatch不作为PR检查资格。[concurrency官方语义](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)由事件合同验证，8轮独立手动实验也没有互相取消。

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
CSV同时记录可能原因及建议，依据实际阶段、源码调用链和独立profile；未独立归因项明确保留UNKNOWN。其“按文件有限并行”是基线阶段的候选建议，本轮实验后已回退，不是最终采用配置。

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

研究实现保持不变。静态job拆分为最小固定依赖；在无NumPy/Pandas/LightGBM的新环境中保留原编译、Flake8、Black。初期52项合同，最终扩展为74项，均通过；真实tiny coverage及崩溃反例不依赖科学计算栈。

[静态测量收据](evidence/ci-runtime-optimization-v1/static-runs.json)保留原main、最小依赖仍用缓存以及关闭缓存三个阶段。
原main完整workflow95秒、job91秒、安装35秒；关闭静态pip缓存后两轮为workflow54/47秒、job49/44秒、安装4/3秒。
该测量阶段19个工具包在每轮全新Python环境实际安装（随后为真实coverage合并合同增加pytest-cov/coverage两项），未安装科学计算栈；setup-python原先会按回退key恢复科学计算下载缓存，因此静态job关闭该缓存。
研究job缓存不变。上述是实际观测，Runner检出等仍有波动，不把差值全部归因于单个变量。

唯一测试准备优化为test_cli_phase2._inputs：原配方保持原样，按配方版本及NumPy/Pandas版本缓存进程内pickle不可变字节，每次解码得到独立对象。与Git绑定的原main配方逐值、数值原始字节、dtype、索引、频率和attrs校验，并验证修改不会污染下次调用。390交易日，数据/股票bar/基准分别3900/5100/510行，规模不变。没有缓存训练、被测验证、收据或文件。45项所属文件测试通过。

输入优化的工程提交为 `11ce72b93c44c83041d4faaf34798dd6c77851dc`；其完整套件因下述旧工程字节冻结冲突失败，不能作为有效候选性能样本。
[干净提交的等价收据](evidence/ci-runtime-optimization-v1/fixture-equivalence-11ce72b.json)中，10次输入准备的两个配对微测量分别由0.795/1.578秒降至0.004/0.010秒；
该结果只说明重复输入构造被消除，不外推完整CI提速比例。11ce阶段320份冻结文件中仅此测试准备文件发生变化；最终还公开迁移下述工程冻结测试实现，研究实现和原研究依赖文件均未变。

独立119项热点profile中：schema canonicalize_bars 6627次、134.456秒inclusive；validate_bars 7791次、116.154秒inclusive；acquire_pilot 59次、138.778秒inclusive；_inputs 83次、12.816秒inclusive。以上嵌套时间不能相加。Ridge/LightGBM/XGBoost fit各37/15/15次、0.092/0.119/0.140秒inclusive，未显示训练为该样本瓶颈。
51个pytest fixture中已有5个模块级fixture；不能假设所有重复调用都可安全复用。
训练调用次数、独立重跑、防泄漏变异比较、序列化和哈希验证仍须实际执行。

同一热点profile另测：Parquet读3176次、6.020秒inclusive，写1723次、6.256秒；savefig 83次、13.762秒；
exploratory.contract.sha256_file 21606次、0.645秒。它们均包含部分嵌套调用，不能与schema、pilot时间相加。
这些操作仍属真实证据生成与核验，本次未缓存或绕过；五年pilot收据绑定绝对路径和原生响应，未强行复用其可写产物。

### 6.1 原冻结检查的精确工程迁移

完整候选测量发现此前审计遗漏：test_five_year_frozen_baseline把3个CI YAML和test_cli_phase2.py也包含在470文件的一次历史字节冻结中，
因此本任务已经授权的工程改动触发真实失败。6次失败样本全部保留在[拒绝样本收据](evidence/ci-runtime-optimization-v1/rejected-candidate-runs.json)，不作为提速验收。

没有更改旧frozen-baseline.json、旧研究收据或原`6864315bc8eeaf96356d6822d12f431ec485a94e`锚点。
门禁仍核验470项原始blob、14因子、39候选和250000行参数；另固定历史manifest blob为`e98d621ebdbc8d619de22390502ec07a79d825a3`。
新增[独立工程迁移收据](evidence/ci-runtime-optimization-v1/engineering-migration.json)，固定其SHA256后，仅接受明确授权的4个工程文件在已审工程提交中的精确Git postimage。
剩余466项仍须完全不变；不是按路径无条件豁免。原test node ID保留，但工程字节冻结检查的实现发生了此项公开迁移，不能声称它的测试体完全未变。
所有金融计算、Golden、历史收据和金融资格接受/拒绝条件保持原样。

门禁实际重跑CI事件/工作流合同和原配方逐值、原测试体AST、规模与隔离验证。
新增15项独立合同覆盖第五项金融文件变更、重命名、删除、4项字节漂移、历史manifest及迁移摘要篡改、扩张收据范围、断言改变、输入缩减和真实squash后离线单分支checkout。
工程锚点与4个postimage的对应关系在收据生成及独立复审阶段核实；运行时固定收据SHA256及精确blob，不要求将来squash/rebase合并后仍保留分支中间commit对象。缺失中间对象的合法squash通过，任一字节漂移或收据改动仍失败。
使用`--no-renames`修复原路径重命名漏检；新审计目录局部eol=lf属性保证迁移摘要在真实Windows CRLF checkout中仍可核验。
迁移阶段独立复审无遗留P0/P1，最终HEAD结论另见PR最终收据。迁移后正式候选的完整测量重新开始；研究集合仍须与冻结3144/3142清单完全相同。

## 7. 并行资源审计与实验

串行对照已通过，完整并行实验已完成并回退。比较串行、固定pytest-xdist 3.8.0的2/3 Workers，按loadfile分配。
[该版本支持Python>=3.9](https://pypi.org/project/pytest-xdist/3.8.0/)；[loadfile保持同文件Worker归属](https://pytest-xdist.readthedocs.io/en/stable/distribution.html)。并行依赖独立放置dev/requirements-parallel-ci.txt，仅供显式诊断和CI工具合同；正常研究安装仍使用原研究依赖。
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

正式并行控制器为`bf10661cdcf9df0ee483661da562546dca967408`，原main和候选均重新使用同一策略：
pytest初始conftest导入前，controller/gwN各自设置独立MPLCONFIGDIR，实际缓存路径在sessionfinish核对并记录，缓存内容不上传为验收证据。
pytest 8.3.5的lastfailed/nodeids/stepwise由controller单写；pytest-cov 6.2.1的Worker/子进程使用原生唯一后缀，仅controller统一合并。
不分别改变Worker COVERAGE_FILE。另校验每个Worker真实cov_worker_node_id及failed_workers，防止插件只警告漏覆盖贡献而仍成功。
真实0/2/3 Worker小型覆盖套件及缺Worker贡献、共享字体缓存、缺资源收据反例通过；独立复审另用真实font_manager验证私有字体缓存互异。
CI合同现共74项。最小静态依赖增加pytest-cov/coverage两项，以实际执行这些覆盖合并反例，仍不安装科学计算栈。

### 7.1 全部并行对照与回退决定

[完整环境/步骤/文件哈希](evidence/ci-runtime-optimization-v1/parallel-bf10661-runs.json)及[回退摘要](evidence/ci-runtime-optimization-v1/parallel-rollback-summary.json)保留全部8轮。Python3.9.25、70个已安装包版本、2 vCPU及镜像20261012.334.1一致；实际CPU有AMD EPYC 9V45、9V74、7763三种。两轮优化串行恰均为7763，CPU型号也是混杂因素，不能把差异都归为调度。条件为热pip下载缓存、native线程1、私有全新字体缓存。CPU配额不可读为UNKNOWN。全部pytest均3141 passed、1 skipped、2 deselected，但严格覆盖比较在三轮并行样本失败。

| 被测方案 | 实际Run | pytest秒 | 进程秒 | workflow秒 | user+system CPU秒 | 最低内存余量 | 原状态 / covered行 |
|---|---|---:|---:|---:|---:|---:|---|
| main串行 | [38891297145](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38891297145) | 628.73 | 629.610 | 723 | 624.923 | 81.4% | success / 15988 |
| 优化串行 | [38891303665](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38891303665) | 1166.65 | 1167.670 | 1258 | 1171.968 | 81.3% | success / 15988 |
| 2 Workers | [38891309461](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38891309461) | 710.16 | 710.776 | 807 | 1344.718 | 77.7% | failure / 15986 |
| 3 Workers | [38891314204](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38891314204) | 542.07 | 542.677 | 637 | 1039.604 | 74.2% | failure / 15986 |
| main串行 | [38891318921](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38891318921) | 1008.36 | 1009.814 | 1115 | 949.827 | 81.5% | success / 15988 |
| 优化串行 | [38891323318](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38891323318) | 1172.89 | 1173.979 | 1265 | 1178.766 | 81.6% | success / 15988 |
| 2 Workers | [38891327855](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38891327855) | 522.02 | 522.620 | 618 | 985.552 | 77.5% | failure / 15986 |
| 3 Workers | [38891332161](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38891332161) | 499.09 | 499.587 | 593 | 945.702 | 73.7% | success / 15988 |

三轮失败并行样本仅丢失activation.py第163/164行，原真实失败状态保留。它们没有Worker漏覆盖、漏项或重复JUnit，失败来自新增严格比较门禁。3 Workers第二轮单次workflow593秒不能替代三次连续等价通过；不继续挑选重跑。内存余量均高于20%，RSS峰值串行约1.04–1.06GB、2 Workers约1.53–1.58GB、3 Workers约2.04–2.10GB（可能重复计共享页），不是整个机器精确独占RSS。CPU消耗及墙钟受调度波动影响，不把单次比值当确定增幅。

各run CPU型号依次为：38891297145=9V45、38891303665=7763、38891309461=9V74、38891314204=9V45、38891318921=9V74、38891323318=7763、38891327855=9V45、38891332161=9V45。[独立下载复核](evidence/ci-runtime-optimization-v1/parallel-independent-revalidation.json)在临时副本上重验真实材料：5轮通过、3轮同样被严格比较拒绝，原下载及原始状态未改写。

采用最简单的串行方案，保留原native线程配置。并行及线程限制均不进入普通PR/main验证；显式手动诊断仍允许复核，不能代替PR验收。不引入多job分片。

### 7.2 生产验证与实验比较的明确边界

诊断默认experimental-strict，维持冻结15988行floor，既有失败不改判。普通job显式workers=0、production-complete，保留原validate_reports.py的coverage_threshold=None语义；只不引入本任务新增numeric floor。两种策略都验证真实退出码、所有node ID及阶段/outcome/skip、JUnit、完整133文件/18730可测行、逐行hits和汇总。Worker贡献与资源隔离在并行诊断仍必需。

生产收据明确记录policy、floor是否适用、全部lost/gained行；禁止生产policy带reference或workers，禁止严格失败自动降级。独立反例证明严格比较拒绝覆盖行下降，生产验证完整披露；漏测、篡改JUnit、额外skip、遗漏coverage文件及伪造汇总在两策略下均拒绝。生产绿色不能证明未知覆盖差异已解释：最终复审必须检查全部diff，目前仅解释activation.py163/164的合法竞争时序。

## 8. 优化前后等价性与性能对照

首轮迁移后串行候选为`e1a8e8b50da90c8fec5900d977d4c68d40310211`，控制器相同。
[完整逐轮收据](evidence/ci-runtime-optimization-v1/serial-e1a8e8b-runs.json)保留环境、所有步骤、CPU/RSS及XML/日志哈希。
以下各轮均为3141 passed、0 failed、1 skipped、2 deselected；coverage样本均15988/18730，逐文件covered/valid行与基线无差异。

| 被测代码 / 条件 | Run | pytest内部秒 | pytest进程秒 | workflow秒 | user+system CPU秒 |
|---|---|---:|---:|---:|---:|
| 原main / 热cache | 38870328099 | 667.91 | 669.136 | 780 | 710.621 |
| 原main / 热cache重复 | 38870332121 | 1269.45 | 1270.729 | 1358 | 1331.387 |
| 候选 / 热cache | 38870302346 | 1205.08 | 1206.293 | 1297 | 1266.830 |
| 候选 / 热cache重复 | 38870307069 | 1208.23 | 1209.479 | 1297 | 1269.503 |
| 候选 / 冷pip cache | 38870311290 | 1244.28 | 1245.508 | 1325 | 1306.494 |
| 候选 / 热cache无coverage | 38870315682 | 912.07 | 913.041 | 1002 | 965.595 |
| 候选 / native threads=1 | 38870319409 | 590.61 | 591.611 | 688 | 581.281 |
| 候选 / native threads=1重复 | 38870323886 | 1260.64 | 1262.022 | 1349 | 1266.614 |

各轮Python、完整研究依赖和显式诊断插件版本一致。内存可用余量采样最小值均超过80%。
两倍量级的Runner波动同时影响原main及候选，不能宣称上述数据证明整体串行提速，也不能将单次591秒全部归因于线程限制。
后续并行对照统一私有冷字体缓存，并增加CPU型号/cgroup记录；此前表格与新策略分开呈现，不混合作收益估计。
[配方调用记录](evidence/ci-runtime-optimization-v1/fixture-profile-call-counts.json)证实构造次数83→1；
[模型调用记录](evidence/ci-runtime-optimization-v1/model-call-count-equivalence.json)证实热点样本所有训练、预测、save/load次数完全相同。
保留全部轮次及失败样本，不从不同测试集合、缓存命中或Runner波动推导确定收益。

### 8.1 最终串行代码的实际验收

代码提交为`91697291ae6c22dc2552117582727e68b1c313af`；工程postimage锚点`7e57aa6add9f1f7f7f16bff9ad420870d15b84de`，迁移收据SHA256为`d08e34e905db5b0dee4750220cc5aff5b46b966796b2b554f74c5e5e2347ab9e`。
[三项实际工作流及完整收据](evidence/ci-runtime-optimization-v1/code-9169729-runs.json)：[研究38894387768](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38894387768)、[静态38894392393](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38894392393)、[actionlint38894396919](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38894396919)均成功。它们是workflow_dispatch，明确不能替代真实PR验收。

| 指标 | 冻结main的有效热缓存基线1 | 最终串行代码普通验证 |
|---|---|---|
| 精确被测SHA | 94baf83e993b47344caa12772b65c646da4e09d0 | 91697291ae6c22dc2552117582727e68b1c313af |
| 精确控制代码SHA | 22c236ca7ca443913c85fbd2a69cabd85d55f3c6 | 91697291ae6c22dc2552117582727e68b1c313af |
| Python/完整依赖 | 3.9.25 / 68包，版本清单见收据 | 3.9.25 / 同68包，完整清单逐项相等 |
| node ID集合SHA256 | 218c1838040a3d0fe09e1f1b550059c4e2d0cf1640b203ddeab6c1732fee9183 | 完全相同 |
| 收集/选中 | 3144 / 3142 | 3144 / 3142 |
| passed/failed/skipped/deselected | 3141 / 0 / 1 / 2 | 3141 / 0 / 1 / 2 |
| pytest内部秒 | 1180.35 | 1211.88 |
| pytest进程秒 | 1181.384 | 1213.071 |
| 完整workflow秒 | 1262（诊断入口） | 1290（普通完整入口） |
| 依赖安装秒 | 36 | 32 |
| coverage | 15988/18730 = 85.36% | 相同，133文件、逐行无差异 |
| JUnit/coverage验证 | 真实结果通过，SHA见收据 | 真实结果通过，SHA见收据 |
| 进程树RSS采样峰值 | 1,041,321,984字节；最低余量81.41% | 1,039,695,872字节；最低余量81.37% |
| pytest子进程树user+system CPU秒 | 1240.473 | 1272.568 |
| 金融资格门禁 | 原门禁完整 | 不变，不授予新资格 |

这不是整体提速证明：控制代码/入口有区别、CPU型号未在早期基线独立采集，完整研究墙钟未稳定达标。静态最终普通workflow61秒、job56秒、安装8秒，实际安装21个工具包；同时保留前期47/54秒观测，不只展示最快一轮。

[Windows完整结果](evidence/ci-runtime-optimization-v1/windows-9169729-run.json)：3142 passed、0 failed、0 skipped、2 deselected，pytest1653.61秒、进程1654.886秒；coverage16014/18730，原平台基线16012/18730。仅activation.py163/164新增覆盖，没有lost行。Windows原生EOF锁测试在Linux跳过、Windows实际执行，因此两平台通过数差1符合冻结合同。Windows CPU/峰值RSS/安装耗时为UNKNOWN；不把本地27分33秒与Linux做加速比较。

### 8.2 安装、执行、I/O及报告的计时边界

| 阶段 | 有效热基线1秒 | 最终串行代码秒 | 边界 |
|---|---:|---:|---|
| created→run_started | 0 | 0 | GitHub API时间戳；Runner排队与启动无法独立分离，UNKNOWN |
| job setup | 1 | 1 | 不含不可见的Runner预配 |
| Git检出 | 13+4 | 13 | 基线含额外被测worktree；入口不同，不能归为优化收益 |
| Python设置 | 16 | 18 | 含pip缓存恢复等setup-python行为 |
| 依赖安装 | 36 | 32 | 全新环境实际安装，热缓存仅指pip下载缓存 |
| pytest收集 | 8.196 | 8.954 | Observer collection hook |
| setup合计 | 265.103 | 275.305 | 真实阶段，包含该阶段所有工作 |
| call合计 | 897.154 | 916.993 | 包含计算/I/O/覆盖插桩，不能再加其内部profile耗时 |
| teardown合计 | 0.813 | 0.867 | 真实阶段 |
| sessionfinish hook | 0.094 | 0.098 | 仅该hook；不等于完整报告生成成本 |
| 报告校验 | 0 | 0 | API秒级舍入；不意味着无耗时 |
| 配置审计 | 2 | 2 | 原audit实际执行 |
| artifacts上传 | 1 | 0 | API秒级舍入，原始日志可复查 |
| workflow墙钟 | 1262 | 1290 | created→updated；与pytest秒分开报告 |

pytest-cov6.2.1在runtestloop内生成coverage XML；JUnit/sessionfinish仅部分计时可见，完整JUnit/coverage生成分离成本UNKNOWN。coverage插桩的on/off观测差分含CPU/Runner混杂，不当成确定开销。模型训练/预测、Parquet、绘图及哈希的独立profile见第6节，只记录实际调用/inclusive成本，嵌套不相加。Linux CPU指标来自resource.RUSAGE_CHILDREN所统计pytest子进程树，不含安装、父采样器或Runner其他进程；计费CPU和整个job精确CPU为UNKNOWN。

## 9. 金融安全边界

原14因子、39自动发现候选冻结结果、Golden、历史收据、PIT、HFQ与公司行为、证券身份状态、
统计接受/拒绝条件、walk-forward边界及防泄漏、Forward时间门禁、交易执行和NO LIVE MONEY保持不变。
CI性能证据和软件覆盖率不授予金融数据或实盘资格。

## 10. 失败传播与反例

采样器返回真实pytest退出码。执行证据逐项对账冻结集合、Worker报告、阶段、JUnit及coverage源码行。
已通过74项CI合同测试，包括真实小型pytest观察、重复/遗漏执行、损坏/缺失JUnit、虚假汇总、
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

### 11.1 Draft PR与最终HEAD收据

[Draft PR #9](https://github.com/Wind-Maker1001/quant-tv/pull/9)已创建。[opened事件快照](evidence/ci-runtime-optimization-v1/pr-opened-events.json)证明Draft仍实际启动研究[38897499099](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38897499099)、静态[38897499193](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38897499193)及actionlint[38897499301](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38897499301)，不是只凭YAML推断。初始PR HEAD为91697291ae6c22dc2552117582727e68b1c313af，合并测试SHA为2253246580a1d7b1aa2bafa34374b1cdfa59552d，base仍94baf83e993b47344caa12772b65c646da4e09d0。

本报告及聚合证据的后续提交将触发真实synchronize；旧HEAD可被新HEAD取消，不把取消样本当通过。最终验收收据单独列出最终40位PR HEAD、实际checkout/merge SHA、每项pull_request运行、完整Windows运行、无额外push验证及手动诊断未被PR取消的事实。只有这些真实检查完成且独立复审无P0/P1，才按PARTIAL交付；手动成功不代替PR检查。收据发布在同PR Conversation及最终交付中，避免把未来结果写入当前commit形成自指。

## 12. 独立Codex复审与最终结论

中期独立预审发现三项P1：未强制比较平台执行/覆盖范围、收据来源未校验、coverage逐行hits与汇总未对账。
已加入冻结平台合同、精确SHA/tree绑定及逐行汇总交叉验证，并扩展反例。独立Codex子代理对代码91697291ae6c22dc2552117582727e68b1c313af复审通过，无遗留P0/P1，另独立复跑29项执行合同、15项迁移合同和8项触发/workflow合同。四postimage在工程锚点、receipt、代码tree及worktree完全相等；最终文档HEAD的复审与实跑另在PR最终验收收据绑定，不冒充GitHub自动批准review。
P3输入复用另经独立只读复审：原构造体和45项测试主体保持不变；逐列无共享数组，并额外修改日期数组、索引名、attrs验证下一次调用仍精确相同，未发现P0/P1。
选择PARTIAL：重复事件调度、静态依赖和固定输入构造已有可复核资源收益；并行因严格等价证据不稳定回退，串行整体墙钟提速未获可靠证明，完整研究workflow未稳定达到10分钟。代码Windows全量和三项远程完整验证均通过；最终文档HEAD的完整Windows、真实PR检查与独立复审须以外部最终验收收据为准。

遗留风险：保护规则API UNKNOWN；Runner约2倍波动；原锁竞争覆盖分支随时序波动；Windows曾有跨盘相对路径错误及一次原生锁PermissionError，完整复跑使用同D盘全新临时根且不改锁语义；新main Push仅经合同验证，人工合并后真实运行尚未发生。

## 13. 独立复跑

以下命令均从完整Git历史的独立checkout执行，Python为3.9.25，输出目录必须不存在：

```bash
python -m pip install -r dev/requirements-research-ci.txt
python -m pip check
python .github/scripts/ci/benchmark.py --output results/diagnostics/reproduce --workers 0
python .github/scripts/ci/validate_execution.py results/diagnostics/reproduce \
  --expected docs/research/evidence/ci-runtime-optimization-v1/baseline-collection.json \
  --policy production-complete
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
Actions artifacts保留90天，需在到期前独立下载；不要将其当永久档案。Windows完整材料留存独立本地审计目录，最终交付提供带SHA256清单的本地归档；不谎称Windows材料已经上传至Ubuntu运行的artifact。所有上传均限软件执行、合成测试和聚合证据，无私有行情、凭据或未授权原始材料。
基线清单仅可在合法新增测试或研究源码变更后，经完整重新冻结与独立复审更新；不得为通过性能验收修改期望清单。
