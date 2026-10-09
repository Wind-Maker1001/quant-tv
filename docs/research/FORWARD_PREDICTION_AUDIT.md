# Forward 完整预测证据与读取语义补强

日期：2026-10-09（Asia/Shanghai）。范围为研究模块软件正确性，不是真实 Forward 实验。

## 发现与处理

原 CLI 在评分后只保存 Top-K；将来无法仅凭这些记录诚实计算全股票池 Prediction IC、
Bottom-K 或完整 Train/Validation/Historical Test/Real Forward 差距。修复先保存当日
完整合格横截面，再从同一排名选择 Top-K。任何 score 非有限都停止发布，不允许
丢弃异常行后声称完整覆盖。

Schema 3 在同一个 staging 和原子新版本目录发布 `signals.csv` 与 `predictions.csv`。
完整表与组合表的元数据一致，股票代码唯一、分数有限、排名连续且并列按代码排序；
Top-K 必须精确等于完整表前缀。完整表同时绑定预期横截面大小、行数、独立字节哈希、
列集合、模型/数据/PIT/source 身份。完成收据绑定成功 producer 的预测行数、SHA-256
和产物路径。读取校验与解析来自同一字节快照。

旧 schema 2 保持 Top-K-only；新 legacy 写入明确记录 `TOP_K_ONLY`。可以读取组合，
但 `load_prediction_record()` 明确拒绝把它用作完整预测。往旧目录添加预测文件、
覆盖旧版本、事后重新评分并伪装成原始完整预测均不允许。

复核还发现 writer 的时间语义未在 reader 完整重复验证。现在共享原有校验：未来
`data_asof`、早于信号日的 local/UTC 生成日期、未知 timeliness、异日 ON_TIME、
ON_TIME 带重发原因和无原因 LATE_REISSUE，即使 CSV/manifest 一致重哈希，也会在
读取时被拒。该修复不读取当前时钟，不阻止合法旧记录读取，也不新增时区政策。

完整重写文件、摘要、成功清单和本机时间的恶意操作者仍可能伪造一致证据；本地 SHA-256
不是第三方可信时间戳。本文不把语义校验称为外部防伪能力。正式启用流程仍要求事先
冻结配置/模型、未来激活、干净 Git、PIT 前置和源码合同，见 [FORWARD_TEST.md](FORWARD_TEST.md)。

## Changed files

- 核心：`qbot/research/forward/signal_recorder.py`、`forward/__init__.py`、`cli.py`。
- 可运行人工示例：`examples/research/phase4_synthetic_demo.py`。
- 新测试：`tests/research/test_forward_full_predictions.py`（58项）、
  `test_forward_temporal_read_validation.py`（38项）。
- 原测试扩展：`test_cli_phase4.py`、`test_phase4_synthetic_example.py`。
- 文档：本文件、`FORWARD_TEST.md`、`GETTING_STARTED.md`、`PHASE4_DELIVERY_REPORT.md`、
  `RESEARCH_METHODOLOGY.md`、`ARCHITECTURE_AUDIT.md`、`BAOSTOCK_SOURCE_AUDIT.md`。

没有修改 Legacy、许可证、固定依赖、正式配置参数、系统代理或真实交易入口。

## 实际执行与验收

模块最初验收：完整预测与原 recorder 共81 passed；加入 CLI/示例/activation/contract/
policy 的回归110 passed，7.26秒，JUnit 为
`results/runs/forward-full-predictions-targeted-20261009.xml`。

人工示例最初有1 failed/8 passed，因为 Windows 的 `dtype=int` 是 int32，而 CSV
读取的 rank 是 int64；改为显式 `np.int64`，保留逐值精确比较，随后9 passed。
时间语义新测试38 passed，与 full/原 recorder/policy/CLI 合计130 passed。

实际运行：

```powershell
.venv-py39\python.exe -m examples.research.phase4_synthetic_demo `
  --output results/examples/phase4-full-predictions-20261009 --seed 42
```

该目录明确标注 `SYNTHETIC SOFTWARE DEMO ONLY - NOT A RESEARCH RESULT`，没有网络、
真实行情、真实 PIT 或真实 CLI Forward。人工训练48行，其中36行标签成熟、12行尾部
被排除；评分6个人工证券，Top3与全部6预测分别保存，模拟 ON_TIME 与 LATE_REISSUE
两个不可覆盖版本，读取器验证成功完成收据及两份完整预测。此示例的2099年日期和
synthetic 来源标记不是实际信号时刻，不能冒充2026-09-14或任何真实 Forward。

最终全量实际通过：**1261 passed、2 deselected、13 warnings，366.17秒**。
JUnit 为 `results/runs/forward-prediction-full-20261009.xml`；XML独立核验1261 tests、
0 failures、0 errors、0 skipped。两个 deselected 为默认排除的网络测试，13 warnings
为既有 Matplotlib/Pyparsing 警告。没有运行含联网/邮件/GUI副作用的 Legacy suite。

同时实际执行真实单股只读复跑：

```powershell
.venv-py39\python.exe -m examples.research.real_factor_label_smoke `
  --config configs/research/csi500_smoke.yaml `
  --start 2023-06-01 --end 2024-01-12 `
  --read-only-cache-root data/research/diagnostics/download-contract
```

成功清单为 `results/runs/20261009T083350.758652Z-real-factor-label-smoke-c8731a6b/manifest.json`。
153个真实交易日、14因子均有有效值、147个成熟标签、尾部6天保持缺标签。
四份输出Parquet的实际SHA-256与清单逐项一致；没有网络请求、缓存补写或旧产物覆盖。
这是旧真实缓存的另一次可审计复跑，不是新下载、正式PIT数据集、真实RankIC或Forward。
两个人工版本的完整预测CSV哈希也与人工manifest独立核对一致。

其他实际命令：

```powershell
.venv-py39\python.exe -m pytest -q --junitxml=results/runs/forward-prediction-full-20261009.xml
.venv-py39\python.exe -m pytest -q tests/research/test_cli_phase4.py tests/research/test_phase4_synthetic_example.py
.venv-py39\python.exe -m compileall -q qbot/research examples/research tests/research
.venv-py39\python.exe -m qbot.research.cli audit --config configs/research/csi500_smoke.yaml
git diff --check
```

Audit 成功清单为 `results/runs/20261009T083438.097469Z-audit-ef845cbf/manifest.json`，
如实记录本轮尚未提交的工作区、Python3.9.25和seed42。编译与diff检查通过，原LICENSE
Git blob与审计的上游提交一致。普通运行产物仍处于忽略目录；本次没有发布任何
`results/forward/` 正式信号，没有500股任务或可被隐藏的单股失败名单。

## 已知限制与下一步

用户没有外部历史数据文件。官方来源的有限网页观察与 BaoStock 匿名接口诊断均不能
替代逐日实际生效的完整 PIT 股票池；当前正式数据集、真实横截面 RankIC、五年四模型
实验与真正实时 Forward 仍缺输入，不解除任何安全门禁。详见
[BAOSTOCK_SOURCE_AUDIT.md](BAOSTOCK_SOURCE_AUDIT.md)。

本次只补全预测存档与读取守卫，**未实现成熟 Forward 标签关联/evaluate-forward CLI**，
也未补齐完整 Train IC 报告。Q4 仍不能据现有产物全部回答。下一步在继续核验 PIT 来源
的同时实现只追加的成熟标签关联及分期评价，严格使用当时完整预测，不重评分旧日，
不利用未来结果选择版本。正式启用仍需研究者事先批准未到来的新起点，原始
2026-09-14永久没有可追补的 ON_TIME 证据。
