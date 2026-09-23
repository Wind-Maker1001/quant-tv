# Qbot FactorLab 快速开始

Qbot FactorLab 是 Qbot 内部隔离的 A 股横截面研究模块。它仅用于历史研究、Paper Trading 和后续的 Forward Test，不发送真实订单，也不保证策略盈利。

## 当前实现状态

| 能力 | 状态 |
| --- | --- |
| 严格 YAML 配置、Schema、AKShare Provider、Parquet 缓存 | Phase 1 已实现 |
| CSI500 交易日历、BaoStock/本地导入 PIT 股票池、日级过滤 | Phase 1 已实现 |
| 14 个因子、日横截面预处理、next-open 标签、数据集 | Phase 1 已实现 |
| IC/RankIC、分位收益、自相关、换手和相关矩阵报告 | Phase 1 已实现 |
| FactorScore、Ridge、Expanding Walk-Forward、Purge/Embargo | Phase 2 已实现 |
| Test 预测指标、Top-K、Fast Backtest、费用与模型报告 | Phase 2 已实现 |
| LightGBM、XGBoost、Market Regime、规则执行回测 | Phase 3 已实现 |
| 未来激活、冻结模型、append-only Paper Signal | Phase 4 核心已实现，尚未正式激活 |

每次模型运行同时生成快速目标权重回测和规则执行回测。执行层包含 T+1、100 股整数手、现金、停牌及开盘涨跌停拒单；但日线仍无法还原盘口队列、部分成交和盘中路径。

当前第三阶段验收与仍存在的真实数据阻塞见 [PHASE3_DELIVERY_REPORT.md](PHASE3_DELIVERY_REPORT.md)；正式启用协议见 [FORWARD_TEST.md](FORWARD_TEST.md)。

## 1. 创建独立环境

优先使用 Python 3.9，不要将根 requirements.txt 的 Legacy GUI/交易依赖混入研究环境。

Windows PowerShell：

使用已安装 Python Launcher 时：

    py -3.9 -m venv .venv-research

若当前 `python --version` 已确认是 3.9，也可以：

    python -m venv .venv-research

然后：

    .\.venv-research\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r dev/requirements-research.txt

也可使用 `conda create -n qbot-factorlab python=3.9`。当前主机没有 `py` Launcher，因此本次验收直接使用已有的 Python 3.9 虚拟环境；不要在未核对版本时把系统默认 `python` 当作 3.9。

Linux/macOS：

    python3.9 -m venv .venv-research
    source .venv-research/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r dev/requirements-research.txt

AKShare 和 BaoStock 仅在网络命令执行时需要；LightGBM/XGBoost 只在对应模型拟合时加载。导入 qbot.research 不会启动 wxPython、Qlib、Backtrader 或实盘接口。

## 2. 先运行离线测试

在仓库根目录执行：

    python -m pytest -q

pytest.ini 默认只收集 tests/research，并排除 network marker。这个边界是安全要求：Legacy tests 中有联网、邮件、GUI、桌面通知和无限循环示例。

显式执行网络测试：

    python -m pytest -q -m network

网络测试可因数据源限频、端点改动、代理或本地网络而失败，不取代离线正确性测试。最新真实 `download-data` 尝试（run `20260923T024112.174238Z-download-data-ec762717`）整体状态为 `failed`：benchmark 缓存可读并确认 88 个研究交易日和 130 个精确预热交易日，但 BaoStock 登录连续 4 次返回网络接收错误。本地 benchmark 缓存有 330 个交易日（2023-01-03 至 2024-05-17），其中 smoke 研究区间 88 日、研究开始日前 242 日；流水线实际只会从这些历史日中选择最后 130 日作为预热。AKShare 单股票端点的独立网络测试仍发生 RemoteDisconnected，PIT 股票池和真实股票数据链路尚未完成。不能把 benchmark 子步骤成功或离线测试通过描述成真实端到端或五年数据已经验证。

## 3. 选择配置

- configs/research/csi500_5y.yaml：正式区间 2021-09-13 至 2026-09-11；
- configs/research/csi500_smoke.yaml：用于短区间端到端网络烟雾；当前环境的真实链路尚未跑通，只能在未来网络与 PIT 来源可用时继续验收。

配置加载器递归拒绝未知字段，相对路径总是相对仓库根目录解析。live_trading 必须为 false，universe.point_in_time 必须为 true。默认 data.warmup_trading_days=130，用于从研究开始日前取得真实交易日预热数据；预热行情/状态只参与过滤和因子 rolling，正式 PIT 验证与输出仍限定在研究日期。

smoke 配置、mock fixture 和 synthetic demo 均不得用于论文收益、因子有效性或模型优劣结论。

## 4. 运行数据与因子流水线

    python -m qbot.research.cli audit --config configs/research/csi500_smoke.yaml

    python -m qbot.research.cli download-data --config configs/research/csi500_smoke.yaml

    python -m qbot.research.cli build-dataset --config configs/research/csi500_smoke.yaml

    python -m qbot.research.cli evaluate-factors --config configs/research/csi500_smoke.yaml

如已经有经独立来源验证的逐日历史成分数据，先复制所需配置并明确把
`universe.provider` 改为 `local`，再用该配置导入：

    python -m qbot.research.cli import-universe --config path/to/csi500_local.yaml --input path/to/csi500_daily.csv

导入文件必须至少有 date,symbol,is_member，覆盖配置区间的每个基准交易日，且每日恢复为 500 个唯一成员。这不是导入“当前成分列表”的入口。`import-universe` 只接受 `universe.provider=local` 的配置；成功导入后，`download-data` 会复用并校验该股票池，同时仍从 BaoStock 获取 ST、停牌与上市日期。不要使用未修改、仍声明 `provider=baostock` 的正式或 smoke 配置导入本地股票池。

## 5. 运行四模型与两级回测

先确保同一配置对应的 processed/dataset.parquet、dataset_manifest.json、个股缓存、benchmark 和 PIT manifest 已经完整。模型命令会同时校验 Parquet 内容 SHA-256、生成数据集的配置合同、PIT 股票池版本，以及生成数据集时的 Git/工作区/Python/包版本指纹；任一不一致都会要求重新构建数据集。然后分别运行：

    python -m qbot.research.cli walk-forward --model factor_score --config configs/research/csi500_smoke.yaml

    python -m qbot.research.cli walk-forward --model ridge --config configs/research/csi500_smoke.yaml

    python -m qbot.research.cli walk-forward --model lightgbm --config configs/research/csi500_smoke.yaml

    python -m qbot.research.cli walk-forward --model xgboost --config configs/research/csi500_smoke.yaml

每条 walk-forward 命令都会：

1. 按配置构造 expanding Train/Validation/Test folds；
2. 执行 Purge、Embargo 和标签窗口审计；
3. FactorScore 使用冻结权重；Ridge、LightGBM、XGBoost 只由 Validation 在预注册小候选集中选参；
4. 仅对 Test 产生样本外 score/rank 和预测指标；
5. 用 t 日信号在 t+1 adj_open 运行 Top-K 等权 Fast Backtest；
6. 再用 raw open/close 运行含 T+1、整手、现金、停牌与涨跌停近似的 Execution Backtest；
7. 写模型、特征重要性/系数、状态分解、两级回测表、图片和运行 manifest。

四个模型都成功后，可以客观合并各自最新一次完整报告：

    python -m qbot.research.cli compare-models --config configs/research/csi500_smoke.yaml

compare-models 不自动挑选“赢家”，也不据 Test 调参。它读取 FactorScore、Ridge、LightGBM、XGBoost 各自最新的完整输出，并强制核对完整配置、数据/PIT 哈希、Fast/Execution 行情哈希、Git commit、工作区 diff 指纹、Python 与包版本、模型目录全部产物 SHA-256，以及 OOS 键、标签窗口和已实现目标一致；源 run_id 会写进比较结果。任一来源未知、被修改或不一致都会停止。

### 5.1 Phase 4 Paper Forward Test

正式配置默认仍关闭 Forward Test，避免系统擅自把已经过去的 `2026-09-14`
伪装成真实起点。研究者审核一个尚未到来的新起点、训练截止日、模型版本和候选索引
并提交干净工作区后，依次执行：

    python -m qbot.research.cli activate-forward --date YYYY-MM-DD --config configs/research/csi500_5y.yaml

    python -m qbot.research.cli freeze-forward-model --config configs/research/csi500_5y.yaml

    python -m qbot.research.cli forward-signal --date YYYY-MM-DD --config configs/research/csi500_5y.yaml

每日信号命令会在全流程独占锁内把运行时 `data.end` 固定到请求日，增量下载、重建
并验证数据集；任一下载失败或当日特征缺失都会停止。随后加载与 activation 共同绑定
源码摘要、且在 activation 日前冻结的模型，生成 Top-K 等权记录。旧日期只能带
`--reissue-reason` 生成明确的
`LATE_REISSUE` 新版本，不能覆盖旧文件或称为 `ON_TIME`。完整的提交顺序、目录和
证据局限见 [FORWARD_TEST.md](FORWARD_TEST.md)。该流程不发送真实订单。

## 6. 离线 synthetic 端到端示例

无需下载 A 股数据即可验证第三阶段软件链路：

    python -m examples.research.phase3_synthetic_demo

也可指定目录和种子：

    python -m examples.research.phase3_synthetic_demo --output results/examples/phase3_synthetic --seed 42

示例生成虚构 symbol、特征、标签、市场状态与价格，运行 FactorScore、Ridge、LightGBM、XGBoost、Walk-Forward、预测评价、Fast/Execution 两级回测和四模型比较。默认产物位于 results/examples/phase3_synthetic/，其中 README.md 和 manifest.json 明确标记：

    SYNTHETIC SOFTWARE DEMO ONLY - NOT A RESEARCH RESULT

这个示例的数据关系是人为构造的；任何正 IC、正收益或模型差异都不能支持关于 CSI500、A 股 Alpha、预期收益或模型优越性的结论。
历史 `phase2_synthetic_demo` 仍保留用于回归 Phase 2 基线，但不覆盖树模型、市场状态或规则执行层。

Phase 4 另提供不联网的软件生命周期示例：

    python -m examples.research.phase4_synthetic_demo --output results/examples/phase4_synthetic

它使用远未来的虚构 activation、合成 Ridge 数据和虚构股票，演示 advance-only 收据、
成熟标签冻结、`ON_TIME`、`LATE_REISSUE` 以及 producer completion receipt。所有产物
均醒目标记 `SYNTHETIC SOFTWARE DEMO ONLY - NOT A RESEARCH RESULT`，不得引用为真实
Forward Test 或论文实证。

## 7. 数据与模型产物

Phase 1 数据：

    data/research/
    ├── raw/akshare/daily/             # 单股 Parquet + metadata JSON
    ├── benchmark/                     # CSI500 基准行情
    ├── universe/
    │   ├── snapshots/                 # 逐交易日 PIT 快照
    │   ├── csi500_daily.parquet
    │   ├── csi500_intervals.parquet
    │   └── manifest.json
    ├── features/
    │   ├── raw_factors.parquet
    │   └── processed_factors.parquet
    └── processed/
        ├── dataset.parquet
        └── dataset_manifest.json       # 内容/PIT 哈希、构建合同与生产代码环境指纹

每次 walk-forward 的目录是：

    results/models/<model_name>/<run_id>/
    ├── fold_models/fold_<NNN>_<model_name>.pkl
    ├── predictions.csv / predictions.parquet
    ├── walk_forward_results.csv / .parquet
    ├── validation_results.csv / .parquet
    ├── prediction_daily.csv / .parquet
    ├── prediction_summary.csv / .parquet
    ├── nav.csv / .parquet
    ├── trades.csv / .parquet
    ├── positions.csv / .parquet
    ├── signals.csv / .parquet
    ├── portfolio_metrics.csv / .parquet
    ├── nav_curve.png
    ├── drawdown.png
    ├── prediction_ic.png
    ├── turnover.png
    ├── transaction_cost.png
    ├── regime_performance.png
    ├── execution_nav.csv / .parquet
    ├── execution_trades.csv / .parquet
    ├── execution_positions.csv / .parquet
    ├── execution_rejections.csv / .parquet
    ├── execution_portfolio_metrics.csv / .parquet
    ├── execution_nav_curve.png
    ├── execution_drawdown.png
    └── summary.md

Ridge 目录还包含 ridge_coefficients；LightGBM/XGBoost 目录包含逐 fold `feature_importance` 表和图片。模型文件使用 pickle，只加载本项目本地生成且来源可信的文件。

compare-models 以 run_id 隔离写入，历史比较证据不会被后一次运行覆盖：

    results/report/<compare_run_id>/
    ├── model_comparison.csv
    ├── walk_forward_results.csv
    ├── prediction_summary.csv
    ├── nav.csv / trades.csv / positions.csv
    ├── execution_nav.csv / execution_trades.csv / execution_rejections.csv
    ├── model_ic_comparison.png
    ├── nav_curve.png / drawdown.png
    ├── feature_importance.png / regime_performance.png
    ├── turnover.png / transaction_cost.png
    └── summary.md

Phase 4 的激活收据、冻结模型和每日信号位于：

    results/forward/
    ├── activations/<activation_id>/
    ├── models/<model_name>/<model_version>/
    └── signals/YYYY-MM-DD/vNNNNNN/
        └── completion/                 # 成功 producer run 的不可变快照与摘要

配置成功加载后的每次 CLI 命令另写 results/runs/<run_id>/manifest.json，记录命令状态、Git SHA、未提交工作区内容指纹、完整配置、随机种子、Python/包版本、数据区间、PIT/数据集/模型产物哈希、模型参数、关键指标和产物路径。若配置本身无法解析，命令在建立 run 之前以状态码 2 失败，因此不会产生误导性的实验 manifest。

## 8. 常见失败

POINT-IN-TIME UNIVERSE REQUIRED 是预期的安全失败，表示某个交易日的成分快照缺失、重复、成员数异常或不在请求范围。不要为让命令通过而改成当前成分股。

Schema 错误表示 symbol、日期、主键、OHLC 关系或数值单位不符合内部合同。修复数据来源映射，不要绕过验证。

“insufficient history for the first fold” 表示配置区间不足以容纳 Train+Validation+Test，而不是模型故障。正式配置需要约 30 个日历月才形成首个 24+3+3 fold；smoke 配置使用更短的 2+1+1 窗口。

网络下载可以断点续跑：成功的单股和单日 PIT 快照会保留，再次执行仅补缺失区间。严重的 benchmark、Schema 或 PIT 问题仍会阻止数据集构建。

## 9. 形成研究结论前

烟雾或 synthetic 命令成功只说明软件管线可执行。只有以下条件同时满足，结果才可进入课程论文：

- 正式五年配置完整运行；
- 每日严格 PIT 股票池及 manifest 哈希有效；
- 数据失败清单与覆盖率经过审阅；
- 四个模型使用同一冻结数据、配置和 OOS 键；
- Walk-Forward/Purge/Embargo 审计表完整；
- Test 未参与研究选择；
- 费用、执行拒单和日线近似局限性如实披露。

Phase 4 核心软件已经实现，但正式配置尚未激活，也没有真实 forward signal。任何模型都可能亏损或落后 benchmark；这不构成修改 Test 后参数的理由。当前公开数据端点仍未提供可验证的完整真实五年输入，因此不得把离线验收当成正式实证结果。
