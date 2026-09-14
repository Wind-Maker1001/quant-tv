# FactorLab 回测设计

> **实现状态：Planned — Phase 2/3。**
> Phase 1 没有组合回测引擎，本文是已冻结的后续设计边界，不是已产生绩效的声明。

## 目标

回测用于回答“在可实现的交易时点、成本和 A 股限制下，历史横截面排序能保留多少 Alpha”，而不是通过忽略执行问题制造正收益。

Factor Engine 和 Model Engine 保持与 Backtrader 无关，共用 Phase 1 的 PIT 股票池、canonical schema、next-open 标签和交易日历。

## Planned: Phase 2 快速研究回测

Pandas/NumPy 引擎用于快速比较 fold 和模型：

- 在 t 日收盘后生成 `symbol,score,rank`。
- 下一个可交易日开盘进入，不假设能以 t 日收盘价成交。
- 默认选 Top 20，等权 5%，每 5 个交易日调仓。
- 与中证500同时线对齐，输出 Strategy NAV、Benchmark NAV 和 Excess NAV。
- 对换手、佣金、印花税、过户费和滑点做显式记账。

快速引擎用于研究迭代，不声称完全复原真实订单成交。Top-K、调仓频率、权重和费用都必须由配置固定，不能根据最终 Test 修改。

## Planned: Phase 3 执行回测

第二级引擎将在适配层考察 Legacy Qbot/Backtrader，模拟：

- 订单、现金、持仓和成交失败。
- A 股 T+1：当日买入的股份当日不可卖出。
- 100 股整手、现金约束与最低佣金。
- 停牌以及涨停无法正常买入、跌停无法正常卖出的日线近似。
- ST 与不同板块的涨跌幅、历史规则生效日和 configurable tolerance。

Legacy Backtrader 示例不直接成为 FactorLab 数据或模型依赖。适配前必须用与快速引擎共用的交易事件和费用合同进行回归测试。

## 日线成交限制

> Daily-bar backtest cannot perfectly reconstruct order-book liquidity.

日线数据只能用开盘价与按历史规则计算的涨跌停价作近似。开盘价接近涨停价时将买单视为无法成交，接近跌停价时将卖单视为无法成交；但这不能识别封单队列、盘中打开或个人订单的队列优先级。报告必须把该近似列为限制。

## Planned FeeSchedule

费用不写在策略代码中，而是按生效日区间查表。至少包含：

```text
effective_from, effective_to
commission, minimum_commission
buy_fee, sell_fee
stamp_duty, transfer_fee
slippage
```

印花税卖出费率的默认研究边界：

| 区间 | 卖出印花税 |
| --- | ---: |
| 2021-09-13 至 2023-08-27 | 10 bps |
| 2023-08-28 起 | 5 bps |

其他费率必须独立配置。正式运行应在 manifest 中存档整个费用表，并用边界日期单测确认 2023-08-27 与 2023-08-28 的卖出成本不同。

## Planned 绩效产物

组合层至少输出：

- Cumulative/Annualized Return、Annualized Volatility、Sharpe、Sortino、Maximum Drawdown、Calmar。
- Benchmark Return、Excess Return、Tracking Error、Information Ratio、Win Rate。
- Portfolio Turnover、Total Transaction Cost、Number of Trades、Average Holdings。
- `trades.csv`、`positions.csv`、`nav.csv`，以及 NAV、回撤、换手和成本图。

模型层同时报告 Prediction IC/RankIC、ICIR、Top-K/Bottom-K 未来收益和 Top-Bottom spread，按年、季度、市场状态和 Walk-Forward fold 分解。不允许只展示策略 NAV。

## 还未产生的内容

Phase 1 不会生成 `nav.csv`、`trades.csv`、`positions.csv`、模型绩效或交易成本结果。如在本阶段看到这些文件，应确认它们是否来自 Legacy Qbot，不得当作 FactorLab Phase 1 产物。
