# FactorLab 验证与数据泄漏防护

## 当前状态

Phase 1 已建立数据、PIT 股票池、因子、标签、数据集和因子指标的正确性边界。

Expanding Walk-Forward、Train/Validation/Test、Purge 和 Embargo 属于 **Planned: Phase 2**。当前没有模型训练或随机切分接口，因此本文不宣称已完成模型样本外验证。

## Phase 1 时点合同

对交易日 t：

```text
截至 t 收盘的历史行情
  -> 计算 t 日因子
  -> 在 t 日合法 PIT 成员/可交易样本上做横截面预处理
  -> t+1 open 为最早入场价
  -> t+6 open 为 5 个交易日持有后的退出价
```

标签是：

```text
STOCK_FWD_RET5     = stock_adj_open[t+6] / stock_adj_open[t+1] - 1
BENCHMARK_FWD_RET5 = index_adj_open[t+6] / index_adj_open[t+1] - 1
EXCESS_RET5        = STOCK_FWD_RET5 - BENCHMARK_FWD_RET5
```

`entry_date` 和 `exit_date` 连同标签保存以便审计 off-by-one。任一入口/出口开盘价或基准价缺失时，标签为缺失。

## Phase 1 泄漏禁止项

- 禁止使用当前 CSI500 成分回填历史。
- 禁止 `bfill`；不用价格 `ffill` 填充停牌日。
- 因子只使用同 symbol 在 t 及之前的 `shift(+n)`/向后 rolling 数据。
- winsorization 和 Z-score 只在单个交易日横截面内估计，不使用五年全样本均值/标准差。
- 股票池、ST、停牌、上市时间和数据质量都以 t 日及此前的状态判定。
- Dataset Builder 保留尾部缺标签行，不用未来补值伪造完整目标。

Lookahead 回归测试应构造 t+1 及以后突然暴涨的价格路径，并断言修改这些未来值不会改变 t 日任何因子。

## 默认测试边界

```bash
python -m pytest -q
```

`pytest.ini` 限制 `testpaths=tests/research`，并默认使用 `-m "not network"`。单元测试使用人工 DataFrame、供应商 mock 和小型 fixture，不要求真实账户、GUI 或网络。

测试范畴应包括：

- Schema：symbol 归一化、日期、排序、唯一主键、OHLC 和非负单位。
- Cache：前/后/中间增量区间、覆盖元数据、哈希校验和原子替换。
- Universe：缺日、非 500 成员、进入/退出/再进入边界与状态过滤。
- Factor：REV、MOM、VOL、TURN、VOLUME_RATIO、AMIHU 和均线公式。
- Label：`t+1 -> t+6`、benchmark 对齐、缺失价和尾部标签。
- Dataset/Metrics：主键、PIT fail-fast、日横截面、IC/RankIC、分位和换手定义。

网络 marker 只用于数据源端到端烟雾验证：

```bash
python -m pytest -q -m network
```

真实烟雾命令的覆盖范围、失败股票和 run manifest 必须在阶段验收时据实报告，不能用 mock 结果冒充真实数据成功。

## Planned: Phase 2 Walk-Forward

第二阶段将实现按交易日时序排序的 Expanding Walk-Forward，默认参数为：

```text
initial_train_months = 24
validation_months    = 3
test_months          = 3
step_months          = 3
purge_days           = 5 trading days
embargo_days         = 5 trading days
```

每个 fold 只能执行：

```text
Train: fit 预处理参数/模型
  -> Validation: 选择小规模超参数
  -> Test: 固定配置后评估一次
```

训练样本的 `exit_date` 不得进入 validation/test 起点及其后。Purge 删除边界上标签窗口重叠的样本，Embargo 在评估区间后预留交易日间隔。测试必须同时断言日期顺序和标签窗口不重叠，不只检查 `max(train_date) < min(test_date)`。

Scaler、PCA、特征选择、中性化、模型参数和缺失处理参数一律只能 `fit(train)`，再用于 validation/test。禁止 `train_test_split(shuffle=True)` 及任何根据最终 Test 修改因子、Top-K、市场状态或费用。

## 研究完整性

模型或回测收益为负不是测试失败。数据时点错误、PIT 不完整、标签 off-by-one、训练/测试窗口泄漏或清单不可复现才是必须阻止实验的错误。
