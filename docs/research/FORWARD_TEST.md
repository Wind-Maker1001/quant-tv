# FactorLab Forward Test

> **实现状态：Planned — Phase 4。**  
> 预定真实样本外记录起始日为 2026-09-14。Phase 1 不会生成或冒充该日期的 forward signal。

## 目的

历史 Walk-Forward 仍可能受研究者反复选择影响。Forward Test 的目的是保留“信号在当时确已产生”的可审计证据，以比较 Train、Validation、Historical Test 和真实 Forward Test 的差距。

Forward Test 仅是 Paper Trading/信号记录：

- 不配置真实券商账户。
- 不要求交易 API 密钥。
- 不发送订单或处理资金。
- `live_trading` 始终默认且必须为 `false`。

## Planned 日终流程

只在信号日收盘后执行：

```text
更新截至 signal_date 的数据
  -> 验证 data_asof <= signal_date
  -> 验证当日 PIT 股票池和数据状态
  -> 计算当日因子和横截面预处理
  -> 加载在历史训练窗口上冻结的当前模型
  -> 输出 Top 20 排序与目标权重
  -> 向 results/forward/ 追加不可覆盖记录
```

数据未更新、PIT 股票池缺失、模型版本不可追溯或当日尚未收盘时，命令应失败，不发布一份“尽量”信号。

## Planned append-only Schema

每条信号至少保存：

| 字段 | 语义 |
| --- | --- |
| `signal_date` | 信号所属交易日 |
| `data_asof` | 输入数据的最新交易日，不得晚于 `signal_date` |
| `generated_at` | 带时区的实际生成时间 |
| `model_name` | 模型类型 |
| `model_version` | 不可变的模型产物版本/哈希 |
| `git_commit` | 生成信号的代码 Git SHA |
| `run_id` | 运行清单关联键 |
| `universe_version` | PIT 股票池内容哈希 |
| `symbol` | canonical symbol |
| `score` | 模型横截面分数 |
| `rank` | 当日排名 |
| `target_weight` | Paper Portfolio 目标权重 |

信号文件还应关联完整配置、Python/包版本、因子列表、数据区间和失败摘要。

## 不可覆盖规则

- 已成功发布的信号文件不在原路径就地替换。
- 重新运行旧日期时生成新的 run/version，保留旧记录。
- 如同一日有多个版本，报告必须按预先固定的规则选择“当时可用”版本，不允许事后挑选收益更好者。
- 修正数据和重训模型可以发布新版本，但必须说明原因和时间，不得改写旧信号。

## Planned 事后评价

当 t+6 开盘价成为当时已知数据后，再为 t 日信号附加 realized return，而不改写原始信号记录。评价与历史模型使用相同的 Prediction IC、RankIC、Top-K、Bottom-K 和 Top-Bottom spread 定义，并单独报告交易失败或数据缺失。

## 当前阶段的文件策略

Phase 1 不创建任何真实 forward 记录，也不用历史数据伪造 2026-09-14 之后的“当时预测”。`results/forward/` 的 Git 与存储策略将在 Phase 4 连同 append-only 写入实现、锁和冲突规则一起冻结。
