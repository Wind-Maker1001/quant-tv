# FactorLab 回测

> **实现状态：Fast Research Backtest 与独立的 A 股规则执行回测均已实现。**

## 目标与两级边界

回测用于回答“在可实现的信号时点和显式成本下，历史横截面排序还能保留多少 Alpha”，而不是通过忽略成本制造正收益。Factor Engine、Model Engine 和快速回测均保持与 Backtrader、wxPython、easyquant 和实盘接口隔离。

两级设计的边界是：

- Level 1（已实现）：Pandas/NumPy 目标权重研究回测，用于快速比较模型与 fold；
- Level 2（已实现）：订单、股数、现金和成交限制驱动的日线执行回测。

## Phase 2 Fast Research Backtest

### 信号与调仓

快速引擎消费样本外的 date、symbol、score，并使用中证500 benchmark 日期作为交易日历：

1. t 日收盘后按 score 从高到低排序；
2. 分数相同时按 canonical symbol 排序，确保结果确定；
3. 按交易日历每 5 个交易日选取一次调仓信号；
4. 默认选择 Top 20，并对选中股票等权；
5. 在 t 的下一个基准交易日 open 执行，不使用 t 日收盘成交。

正式调仓日的有限 score 数量必须至少达到 `max(Top-K, evaluation.min_cross_section)`；否则立即失败并报告日期、实际数量和要求数量。通过守卫后，Top 20 等权为每只 5%，不会把异常稀疏横截面静默变成少数股票的集中组合。

快速层默认使用 adj_open 计算持仓收益和 benchmark NAV，与 next-open 标签时点一致。它按理论目标权重和交易名义金额记账，适合模型横向比较，但不产生整数股数。

### 费用

FeeSchedule 按包含首尾的生效日期区间选择唯一费率规则。每个买卖名义金额分别记录：

- 佣金及最低佣金；
- 卖出印花税；
- 过户费；
- 独立买入/卖出附加费；
- 滑点。

默认卖出印花税边界为：

| 区间 | 卖出印花税 |
| --- | ---: |
| 2021-09-13 至 2023-08-27 | 10 bps |
| 2023-08-28 起 | 5 bps |

佣金、最低佣金、过户费、买卖附加费和滑点均由 YAML 独立配置。费率区间必须覆盖整个研究期且不能重叠或留空；2023-08-27/28 边界已有单元测试。快速引擎通过迭代求解“扣费后的组合价值 → 目标名义金额 → 费用”，而不是事后忽略费用。

### 行情缺失处理

调仓执行日若目标或待卖股票缺少开盘价，回测直接失败，不假设能够成交。非调仓持仓若开盘价缺失，组合保持该股票最后一个有效标记价并冻结当日收益；复牌出现新价格时，一次性确认“复牌价 / 停牌前最后有效价”的累计变化。这里保存的是持仓估值状态，不会把价格写回行情、不会让因子读取填充值，也不会静默丢失复牌跳空。更严格的停牌订单延迟与撤单逻辑仍留给执行回测。

### 产物与指标

核心引擎返回四张审计表：

- nav：Strategy NAV、CSI500 Benchmark NAV、Excess NAV、日收益、成本、换手和持仓数；
- trades：信号日、执行日、方向、排名、目标权重、名义金额、价格和分项费用；
- positions：每日 symbol、当前理论权重（非调仓日会随价格漂移）、理论市值和标记价；
- signals：实际被接受并映射到下一交易日的 Top-K 信号。

组合指标包括：

- Cumulative Return、Annualized Return、Annualized Volatility；
- Sharpe Ratio、Sortino Ratio、Maximum Drawdown、Calmar Ratio；
- Benchmark Return、Excess Return、Tracking Error、Information Ratio；
- Win Rate、Portfolio Turnover、Total Transaction Cost；
- Number of Trades、Average Holdings。

模型层另外报告每日 Prediction IC/RankIC、ICIR/RankICIR、Top-K/Bottom-K future return 和 Top-Bottom spread，并按年、季度、Walk-Forward fold 与 BULL/BEAR/SIDEWAYS 分解。只展示策略 NAV 而隐藏预测能力或成本，不符合研究报告要求。

## Level 2：规则执行回测

`AShareExecutionBacktester` 与因子/模型完全解耦，不导入 Legacy Backtrader。它消费相同的 Test-only score、原始日线和日期有效状态，按以下顺序执行：

1. t 日收盘后生成 Top-K 目标，映射到 t+1 基准交易日开盘；
2. 先卖后买，股数按 100 股整数手确定；
3. 当日买入 lot 在当日 `sellable_shares=0`，下一交易日才可卖；
4. 每笔订单按真实现金检查，现金不足时用确定性的整数手二分计算可买数量；
5. `trade_status=0`、成交量为零或缺失的证券保守拒单；
6. 按前一已知原始收盘价和日期有效涨跌幅计算上下限，开盘接近涨停拒买、接近跌停拒卖；
7. 卖出所得先扣费用再进入现金，买入名义金额与费用均不得使现金为负；
8. 每个完整成交和拒绝片段分别写入 `execution_trades` 与 `execution_rejections`。

涨跌幅配置覆盖主板、创业板和科创板；创业板 2020-08-24 前后规则分段，ST 上下限独立。研究区间内的规则、100 股整手、T+1、拒停牌和 tolerance 都进入 YAML。费用继续复用日期有效 `FeeSchedule`，因此执行层同样反映 2023-08-28 印花税调整。

执行层使用 raw open 成交、raw close 估值；价格限制也只看原始价。benchmark 从首个执行日 `adj_open` 开始，随后按 `adj_close` 每日估值，与策略首次暴露时点对齐。因子、标签和快速研究层继续使用复权价。公司行为导致的现金红利、送转股和零股处理无法仅凭当前日线 Schema 精确重建，因此执行层是“规则敏感的研究近似”，不是券商级账本。

## 日线成交限制

> Daily-bar backtest cannot perfectly reconstruct order-book liquidity.

当前实现能识别开盘接近涨停/跌停的保守拒单，但日线无法识别封单队列、集合竞价、盘中打开、部分成交或订单队列优先级。新股无涨跌幅阶段、除权现金流和临时特别规则也可能需要更细的交易所事件数据。报告必须把它列为近似，而不是把日线模拟描述成真实可成交证明。

## 结果纪律

两级回测已实现不代表已经完成正式五年实验。synthetic demo 和 smoke 配置只验证接口、时点、费用与产物，不得用于课程结论。只有正式 PIT 股票池、正式五年缓存、冻结配置和完整 manifest 下的 Test 结果，才可进入论文；策略亏损、成本侵蚀全部 Alpha 或复杂模型未优于简单模型都必须原样报告。
