# Qbot FactorLab Phase 2 交付与验收报告

验收日期：2026-09-22

## 结论

Phase 2 的软件实现与离线验收已经完成：FactorScore、Ridge、Expanding Walk-Forward、Purge/Embargo、样本外预测评价、Top-K 等权组合、时间敏感费用、Fast Research Backtest、模型报告与模型比较均已接入独立的 `qbot.research` CLI。

这不等于正式研究实验已经完成。当前没有可用于论文结论的真实五年 FactorScore/Ridge 结果；真实网络烟雾在 BaoStock PIT 阶段失败，因此没有生成真实 dataset、RankIC、NAV 或模型比较。synthetic 结果只证明软件路径可运行。

## 本阶段范围

已交付：

- 固定、可解释且由 YAML 配置的 FactorScore baseline；
- Train-only 中位数缺失处理、StandardScaler 和 Ridge；
- 只用 Validation 选择 Ridge alpha，Test 只预测/评价一次；
- 按交易日计算的 Purge/Embargo，以及基于 `entry_date`/`exit_date` 的实际标签窗口审计；
- Prediction IC、RankIC、ICIR、Top/Bottom-K、年度、季度、fold 与可选 regime 分解接口；
- 确定性的 Top-K、等权和每 N 个交易日调仓；
- t 日信号、t+1 `adj_open` 执行的快速目标权重回测；
- 2023-08-28 前后不同卖出印花税，以及佣金、最低佣金、滑点和独立费率分项；
- NAV、持仓、交易、成本、换手、风险指标、Ridge 系数和模型比较报告；
- 数据集、PIT、模型产物、回测输入和 OOS 身份的 SHA-256/运行来源校验；
- 明确标注为非研究结果的离线 synthetic 端到端示例。

未在本阶段交付：

- LightGBM、XGBoost、Market Regime；
- T+1 可卖数量、100 股整数手、真实现金订单、涨跌停/停牌订单处理；
- 订单级 Execution Backtest；
- append-only Forward Test；
- 任何真实资金下单能力。

## 正确性门禁

实现中的关键 fail-fast 条件包括：

- PIT 任一天缺失、重复或不是配置要求的 500 个唯一成员时停止；
- 当前成分股不能回填历史，未带来源元数据的 PIT 日快照不能复用；
- Dataset 必须绑定成功的生产 run、配置合同、PIT 哈希及代码/环境来源；
- 模型特征不得包含 target、signal date、symbol、regime 或标签审计列；
- Train/Validation/Test 必须时序有序，Test fold 不得重叠；
- Train 标签退出日必须早于 Validation 首日，Validation 标签退出日必须早于 Test 首日；
- Future label 缺失不会改变 Top/Bottom-K 或因子分位成员；
- 损坏的 score/价格字符串不会被当成缺失值或停牌；
- 截断 benchmark 日历导致信号没有下一交易日时停止；
- 模型比较只接受配置、数据、PIT、代码环境、回测输入、完整产物清单和 OOS 标签身份一致的运行。

## 测试结果

最终离线命令：

    .\.venv-py39\python.exe -m pytest -q

结果：

    188 passed, 2 deselected, 13 warnings in 59.63s

两个 deselected 用例带 `network` marker，默认不会访问公网。13 个 warning 均来自 Matplotlib 3.8.4 与其 PyParsing 依赖的弃用提示，不是 FactorLab 测试失败。

额外静态检查：

    git diff --check
    .\.venv-py39\python.exe -m compileall -q qbot/research examples/research

两者通过。代码检索未发现研究模块使用 `train_test_split`、`shuffle=True`、`bfill`，也未引入 wxPython、Qlib、Backtrader、easyquant 或实盘交易模块。

## CLI 与 synthetic 验收

在干净工作区提交 `3677b7c0422e314f1ec3c0d5881127f64198e850` 上执行：

    .\.venv-py39\python.exe -m qbot.research.cli audit --config configs/research/csi500_smoke.yaml

结果为成功，run_id：

    20260922T034841.032720Z-audit-68b350b8

该 manifest 记录 Python 3.9.25、`git_dirty=false` 和成功状态。

离线端到端命令：

    .\.venv-py39\python.exe -m examples.research.phase2_synthetic_demo --output results/examples/phase2_synthetic_20260922_final

结果：30 个虚构 symbol；FactorScore 与 Ridge 各 5 个 fold、9,600 行 OOS prediction；两个模型报告及比较报告均生成。manifest 记录 `synthetic=true`、`network_used=false`，所有摘要包含：

    SYNTHETIC SOFTWARE DEMO ONLY - NOT A RESEARCH RESULT

这些数值不得用于 CSI500、A 股 Alpha、模型优劣或预期收益结论。

## 真实网络验证

实际执行过：

    .\.venv-py39\python.exe -m qbot.research.cli download-data --config configs/research/csi500_smoke.yaml

对应 run_id：

    20260922T032118.189388Z-download-data-66412ea2

该 run 整体状态为 `failed`，错误为 BaoStock 登录网络接收失败。在失败前 benchmark 子步骤已记录产物路径。尝试后本地 benchmark 缓存含 330 个交易日（2023-01-03 至 2024-05-17）：研究开始日前 242 日、smoke 研究区间 88 日；下游只从研究前历史中选择最后 130 日作为实际预热窗口。

独立 AKShare 单股票网络测试在绕过失效代理后仍发生 `RemoteDisconnected`。由于 PIT 尚未取得，命令按研究完整性要求停止，没有偷偷使用当前成分股，也没有进入 500 只股票批量下载，因此没有“失败股票列表”可以报告。

本次真实验证没有产生：

- 完整 PIT 股票池；
- 个股行情/状态完整缓存；
- 真实 smoke dataset；
- 有效真实 RankIC；
- 正式五年 baseline 或模型结果。

## 本地提交

- `1ea6f19` `feat(research): add phase 2 models and fast backtest`
- `8f7d3d3` `feat(research): enforce reproducible phase 2 CLI runs`
- `3677b7c` `docs(research): document phase 2 workflow and limits`

以上均为本地提交，没有 push、force-push、改写历史或删除分支。原 LICENSE 与版权信息未修改。

## 已知限制与下一步

下一步首先不是调模型，而是恢复可验证的数据链路：

1. 恢复 BaoStock 连接，或准备独立来源验证的 CSI500 逐交易日历史成员文件并以 `universe.provider=local` 导入；
2. 同时确保 ST、停牌和上市日期状态源可用；
3. 重新执行真实 smoke 的 download → build-dataset → evaluate-factors；
4. 核对失败清单、每日覆盖、真实 RankIC 和全部 manifest；
5. 再用正式配置冻结运行完整五年 FactorScore/Ridge baseline；
6. 完成上述真实基线后才进入 Phase 3 的 LightGBM、XGBoost、Market Regime 和 Execution Backtest。

原计划的 Forward Test 起始日 2026-09-14 已经过去，且当时没有实现 append-only 信号系统。Phase 4 不得事后回填并声称这些预测当时已经产生；应在功能完成后另定首个真实冻结日期。
