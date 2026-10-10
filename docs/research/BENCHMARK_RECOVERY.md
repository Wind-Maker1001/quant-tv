# 2026-10-10 基准缓存真实恢复记录

## 结论与边界

正式中证500基准缓存已通过**真实重新取数**恢复到当前 metadata v3 来源合同，
没有手改旧版本号。正式 `build-dataset` 已越过旧基准错误，随后按预期停在：

```text
POINT-IN-TIME UNIVERSE REQUIRED: EFFECTIVE MEMBERSHIP SEMANTICS UNVERIFIED
```

这只恢复 benchmark 输入，不代表完整历史股票池、证券状态、500股行情、正式
数据集或五年四模型实验已验收。没有生成任何真实 Forward 信号或实盘订单。

## 旧缓存与可恢复归档

旧文件为 metadata v1，仅330行，实际日期2023-01-03至2024-05-17，来源字段无法
满足当前端点/调整合同。归档前检查了版本、行数和两个文件的 SHA-256；以明确
路径成对移动，不删除、不改内容。第二次移动失败时会回滚第一次移动。

归档目录：

```text
data/research/diagnostics/benchmark-cache-archive/20261010-before-refetch-74a0bfa9/
```

归档前后相同的哈希：

| 文件 | SHA-256 |
| --- | --- |
| `000905.SH.metadata.json` | `f0f4b0dead584bd8e1ff280ab79b2d3802b9f59b507dae7743db80dee9e3207d` |
| `000905.SH.parquet` | `063aacab08212604cae86f93f37e95341710a67ae7e83ca0c2c297abe7c76700` |

如需恢复旧文件，它们仍在归档目录；但 v1 仍不适用于当前正式流水线，不能用
“恢复旧文件”代替有效输入验证。

## 新的独立抓取入口

```text
.venv-py39\python.exe -m examples.research.refetch_benchmark --config configs/research/csi500_5y.yaml --deadline-seconds 120
```

`examples/research/refetch_benchmark.py`：

- 冻结展开后配置到 run-owned JSON（有效 YAML 文档），绑定其实际 SHA-256；
- 子进程只调用现有 `AKShareProvider.get_index_bars`，不直接调用网络端点；
- 该诊断显式覆盖 SDK 重试为0，并记录这个覆盖；配置中的正式重试仍为3；
- SDK 指数接口没有原生 timeout，使用子进程 deadline，不改代理、全局 socket
  或 requests；`subprocess.run` 超时后杀死并回收子进程；
- 每次创建新的 `data/research/diagnostics/benchmark-refetch/<run_id>/`，拒绝
  已存在目录及直接写正式 benchmark 路径，不复用/拼接旧缓存；
- 在缓存发布前检查 Schema、研究首尾、130日预热、必需 OHLC 和所用交易日历；
- 以现有 Parquet 缓存发布 generation，再读回并验证序列化文件；
- 父进程独立检查配置 SHA、来源身份、数据与元数据哈希、行数/预热统计和日历；
- 保留 worker log、completion、manifest、候选缓存；失败不报告恢复成功。

这里只记录1次 Provider fetch，SDK 内部 HTTP 数量未观测，不能把“1次 fetch”
写成“整个流程只有1次 HTTP”。来源哈希证明本次输入，不证明历史可用时点。

## 真实抓取与日期异常

第一次真实抓取 run：`20261010T134333.556710Z-refetch-benchmark-2206f72d`。
其成功收据保留原样；后续质量复核发现搜索起点2020-09-12为周六，价格/量额与
2020-09-14记录相同。这里只陈述观测，不推断供应商内部填充算法。

加入显式日历守卫后再次真实执行：

```text
20261010T134848.709726Z-refetch-benchmark-74a0bfa9
```

这次 run 成功，worker正常结束、returncode=0。返回1455条源记录，完整保留在
独立候选缓存；其中2020-09-12这个周末点位于**未使用的更早搜索区间**。
实际所用集合为：

- 研究日期2021-09-13至2026-09-11：1211个日期；
- 精确最后130个预热日期：从2021-03-08开始；
- 合计1341个必需日期，周末0个、必需 OHLC 缺失0行；
- benchmark `turnover` 为缺失，不伪造为0，也不用于个股换手率因子。

`TradingCalendar.from_benchmark_bars` 及 AKShare `get_trade_calendar` 现在拒绝
周末观测；不会静默删掉周末再称为完整交易日历。诊断允许保留不在使用集合内
的额外源记录，但逐项记录 `unused_weekend_observations`。这次正式发布仅选取
上述1341条数据；1455条原始候选仍保留，未覆盖或改日期。

工作日检查是必要的合理性守卫，不足以独立证明所有法定休市日、供应商历史
修订或全部真实交易日完整性；没有以静态节假日表推造任何交易日。

## 正式发布与再验收

发布 run：`20261010T135155.994790Z-publish-refetched-benchmark-ed191bd5`。
这是本次显式本地恢复操作，不是诊断脚本自动覆盖正式缓存。操作先验证成功
源 run、完整配置和候选快照，再从同一快照选取1341行，以 `ParquetBarCache.update`
创建正式新 generation。没有重新联网、没有从旧 v1 合并任何行情。

正式缓存现在是：

```text
data/research/benchmark/000905.SH.4f0b56be280e4bff88a4aa45d72cde64.parquet
data/research/benchmark/000905.SH.metadata.json
```

- 来源：`AKShareProvider`；
- 来源版本：`akshare=1.18.88;contract=stock_zh_index_hist_csindex-v1`；
- metadata：v3，覆盖2021-03-08至2026-09-11，1341行；
- 数据 SHA：`9832a898a5bba8b4fbc971d796bc1239075aebfacff35c1a736b86a9b514cd05`；
- metadata SHA：`3c5f874cc51631d02168c5e39324dc49c7fc0740cc1c3f1ca982630c2c142dd4`。

发布 manifest 另行绑定源 run manifest、候选 metadata/content SHA、旧文件归档
哈希及读回后的正式快照。实际执行：

```text
.venv-py39\python.exe -m qbot.research.cli build-dataset --config configs/research/csi500_5y.yaml
```

run `20261010T135159.026640Z-build-dataset-6680e05c` 明确 failed；错误为前述
PIT 生效语义门禁，不再是旧基准 metadata。不得把这个失败报告为数据集成功。

## 测试证据

先增量测试，再真实抓取：新抓取入口最初23项通过；扩充配置/统计篡改、周末及
目标目录防护后，抓取入口与日历共34项通过。AKShare、缓存 generation、旧缓存、
单股票因子/标签诊断定向回归257项通过。没有使用真实数据冒充合成单测。

```text
.venv-py39\python.exe -m pytest -q tests/research/test_benchmark_refetch.py tests/research/test_data_calendar.py
.venv-py39\python.exe -m pytest -q tests/research/test_akshare_provider.py tests/research/test_akshare_failure_contract.py tests/research/test_cache_generation_publication.py tests/research/test_data_cache.py tests/research/test_real_factor_label_smoke.py
```

JUnit 在 `results/runs/benchmark-refetch-guard-targeted2-20261010.xml` 和
`results/runs/benchmark-refetch-core-targeted-20261010.xml`。初次测试中的配置 fixture
字段/窗口及 Windows UTF-8 读取错误已修正，失败记录仍保留，未覆盖成通过记录。

最终同一份研究源码的完整回归：

```text
.venv-py39\python.exe -m pytest -q --tb=short --junitxml=results/runs/benchmark-refetch-full-20261010.xml
1992 passed, 2 deselected, 13 warnings in 670.93s
```

JUnit 独立复核1992个测试、0 failures、0 errors、0 skipped。两项 network 测试
按默认 marker 未收集执行；真实 benchmark 抓取为上面的单独命令。13条为现有
Matplotlib/Pyparsing 弃用警告，未据此升级 Legacy 依赖。真实五年 PIT 与正式
dataset 仍未取得，软件全测通过不是实证研究完成。
