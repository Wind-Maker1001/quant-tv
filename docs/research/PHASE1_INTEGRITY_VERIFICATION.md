# Phase 1 数据完整性复核记录

日期：2026-10-05。分支：`factorlab/phase-1`。本记录覆盖本轮缓存身份、数据日期边界和文件级整链验收；真实小样本与正式五年实证尚未通过，项目整体不应标记完成。

## Changed files

| 范围 | 文件 | 验证的行为 |
| --- | --- | --- |
| 行情来源与缓存 | `qbot/research/data/cache.py`、`data/providers/akshare.py`、`config/models.py` | metadata v2 强制绑定 Provider、包版本、端点和复权合同；拒绝孤立文件、旧版本、身份混用、哈希/行数/日期边界不一致；增量研究固定 hfq |
| CLI | `qbot/research/cli.py` | 读取时核对缓存身份；benchmark 必须包含配置起止交易日；BaoStock 单层重试；评价接收完整研究日历 |
| PIT/状态 | `qbot/research/universe/csi500.py`、`universe/filters.py` | 要求 code 字段、服务端查询日期和分页结束成功；拒绝重复/非法成员；来源合同升级到 daily-v2；缺失 ST 状态仍保守过滤 |
| 因子评价 | `qbot/research/metrics/factor.py` | 相邻日指标先在全日历计算，再按当日 regime 归组；不跨缺失/无效横截面；检查唯一主键和当日状态一致性 |
| 单元测试 | `test_data_cache.py`、`test_akshare_provider.py`、`test_config.py`、`test_baostock_status_provider.py`、`test_universe_phase1.py`、`test_cli_reproducibility.py`、`test_cli_phase2.py`、`test_factor_metrics_report_phase1.py` | 来源、日期、重试、旧缓存失效和相邻日回归 |
| 文件级整链测试 | `tests/research/test_phase1_file_pipeline.py` | 真实 YAML/CSV/Parquet 文件、四个 CLI 命令、14 因子、标签、报告、运行清单与负例 |
| 文档 | `DATA.md`、`FACTORS.md`、`GETTING_STARTED.md`、`RESEARCH_METHODOLOGY.md`、本记录 | 记录合同、迁移方式、真实网络结果和验收边界 |

本轮已保存的核心提交：`b7e2d4a`（缓存来源合同）和 `48f8d8f`（Phase 1 数据边界）。只创建本地提交。

## Tests passed 与实际命令

使用独立 Python 3.9 环境 `.venv-py39`：

```text
.venv-py39\python.exe -m pytest -q
# 398 passed, 2 deselected, 13 third-party warnings, 139.41s

.venv-py39\python.exe -m pytest -q tests/research/test_phase1_file_pipeline.py
# 1 passed

.venv-py39\python.exe -m pytest -q tests/research/test_universe_phase1.py tests/research/test_baostock_status_provider.py
# 42 passed（随后又增加了 CLI 对旧最终 PIT manifest 的拒绝用例）

.venv-py39\python.exe -m compileall -q qbot/research
git diff --check
# 均通过
```

全量默认测试不运行 Legacy 或 network 测试。13 条警告来自 Matplotlib/Pyparsing，未通过升级 Legacy 依赖来消除。

## 文件级输入与产物证据

整链测试的输入明确为人工数据：65 个预热日、20 个研究日、2 只股票，全部 14 个因子。测试只替换 Provider 工厂为无网络的缓存身份对象；配置加载、导入器、缓存、DatasetBuilder、评价器、报告和 RunManifest 均使用生产实现，没有伪造运行来源清单。

实际依次执行：

```text
import-universe --config <临时YAML> --input <PIT CSV>
import-security-data --config <临时YAML> --status <状态CSV> --listings <上市CSV>
build-dataset --config <临时YAML>
evaluate-factors --config <临时YAML>
```

四个命令均返回 0，并生成四份 success manifest。验证内容包括：

- universe/security/dataset 哈希与版本连续绑定，证券状态不可变 generation 文件实际存在；
- dataset 为 40 个唯一 `(date,symbol)` 观察，预热日期未混入研究样本；
- 全部 14 个因子非空，28 个 `EXCESS_RET5` 已成熟，尾部六个研究日保留缺失标签；
- 原始/预处理因子 Parquet、因子 CSV、Markdown 和 RankIC 图片实际生成；
- 每个因子都有有效 RankIC 日期，评价 run 明确指向成功的 build run；
- 随后导入另一份合法股票池，build 返回 1，错误命中 security/universe 身份不一致，原 dataset 文件未被改写。

人工数据的 RankIC 不代表 A 股因子有效性，不能用于论文结论。

## 真实数据复核与失败情况

2026-10-05 分别实际执行两个网络测试：

```text
.venv-py39\python.exe -m pytest -q -m network tests/research/integration/test_real_providers.py::test_real_akshare_single_security_and_benchmark --tb=short
# 本次测试进程设 NO_PROXY=*；1 failed，13.89s

.venv-py39\python.exe -m pytest -q -m network tests/research/integration/test_real_providers.py::test_real_baostock_historical_csi500_snapshot --tb=short
# 1 failed，92.49s
```

- `600000.SH`，2024-01-02 至 2024-01-12：原始价请求四次尝试后仍为 `RemoteDisconnected`，未获得完整 raw/hfq 股票数据。
- 2024-01-05 CSI500 PIT：BaoStock 登录四次尝试后仍为 socket 错误（`WinError 10057`），未取得快照。
- 未启动 500 股批量下载；本次失败证券仅验证了 `600000.SH`，不能推断其余股票是否可用。
- 2026-10-04 已验证的官方基准子步骤曾返回正式区间 1211 行，但它不证明股票、PIT、证券状态或完整真实端到端成功。

本轮没有正式五年 dataset、Baseline 实验或真实 Forward Signal。历史缓存未被自动删除或重标来源。

## Known limitations 与下一步

1. 真实小样本验收仍需稳定行情端点及可验证 PIT/证券状态输入；本地导入路径已经可执行。
2. benchmark 起止覆盖检查能发现首尾截断；从行情推导日历不能独立证明中间无遗漏交易日，正式验收仍需外部日历对照。
3. 行情缓存的 Parquet/JSON 仍为两次替换，PIT 的 daily/intervals/manifest 也不是完整 generation 事务。错误时会拒绝消费不一致产物，但中断可能损坏上一代可用缓存；下一步补不可变 generation 和 manifest 最后切换的故障注入测试。
4. CSI 指数成交量的两种已知形式仍以金额/量比例判别，需要进一步记录逐请求单位决策并加强混合尺度回归。
5. dataset 已绑定最终内容、PIT、证券状态、配置和生成环境；还需把全部原始行情缓存的身份与内容哈希聚合绑定到 dataset manifest。

后续模型软件已存在，但正式第二阶段五年 Baseline 实验仍以真实第一阶段数据验收为前置。
