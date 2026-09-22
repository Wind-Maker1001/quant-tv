# FactorLab 验证与数据泄漏防护

## 当前状态

Phase 1 已实现数据、Point-in-Time 股票池、因子、标签、数据集和因子评价的正确性边界。Phase 2 已实现：

- 固定权重 FactorScoreModel；
- 仅在训练集拟合缺失值处理和标准化参数的 Ridge；
- 按月推进的 Expanding Walk-Forward；
- 交易日级 Purge、Embargo 和 entry_date/exit_date 标签窗口审计；
- Train → Validation 选参 → Test 仅评估一次；
- Test 样本的 Prediction IC、RankIC、Top-K/Bottom-K 与分组汇总。

LightGBM、XGBoost、Market Regime 属于 **Planned: Phase 3**；真实 Forward Test 属于 **Planned: Phase 4**。实现模型验证能力不等于已经取得五年正式研究结果。

## 信息时点合同

对交易日 t：

    截至 t 收盘的历史行情
      → 计算 t 日因子
      → 在 t 日合法 PIT 成员/可交易样本上做横截面预处理
      → t+1 open 为最早入场价
      → t+6 open 为 5 个交易日持有后的退出价

标签是：

    STOCK_FWD_RET5     = stock_adj_open[t+6] / stock_adj_open[t+1] - 1
    BENCHMARK_FWD_RET5 = index_adj_open[t+6] / index_adj_open[t+1] - 1
    EXCESS_RET5        = STOCK_FWD_RET5 - BENCHMARK_FWD_RET5

entry_date 和 exit_date 连同标签保存以便审计 off-by-one。任一入口/出口开盘价或基准价缺失时，标签为缺失；系统不会补造尚未成熟的未来收益。

## 全流水线泄漏禁止项

- 禁止使用当前 CSI500 成分回填历史。
- 禁止 bfill；不用价格 ffill 填充停牌日。
- 因子只使用同 symbol 在 t 及以前的 shift(+n)/向后 rolling 数据。
- winsorization 和 Z-score 只在单个交易日横截面内估计，不使用五年全样本均值/标准差。
- 股票池、ST、停牌、上市时间和数据质量都以 t 日及此前的状态判定。
- Dataset Builder 保留尾部缺标签行，不用未来补值伪造完整目标。
- 禁止 train_test_split(shuffle=True) 或任何随机金融时序切分。
- Ridge 的中位数缺失值处理器与 StandardScaler 只 fit(Train)；Validation/Test 仅 transform。
- PCA、特征选择、中性化和未来新增的训练期估计量也必须遵守相同边界。
- 最终 Test 禁止用于选因子、超参数、模型、Top-K、费用或市场状态定义。

Lookahead 回归测试构造 t+1 及以后突然暴涨的价格路径，并断言修改这些未来值不会改变 t 日任何因子。

## Expanding Walk-Forward

正式配置默认参数为：

    initial_train_months = 24
    validation_months    = 3
    test_months          = 3
    step_months          = 3
    purge_days           = 5 trading days
    embargo_days         = 5 trading days

窗口使用半开日期区间，并以中证500交易日历取实际观测日。训练起点固定，后续 fold 扩大训练区间；数据必须已经按日期排序，splitter 不会偷偷排序或打乱行。

当前实现对每个 fold 做两层隔离：

1. purge_days 删除名义训练窗口末尾的 N 个交易日；
2. embargo_days 删除名义验证窗口末尾、紧邻 Test 的 N 个交易日；
3. 数据必须包含 entry_date/exit_date；系统删除标签日期不完整的行，并强制 Train 的 exit_date < Validation 首日、Validation 的 exit_date < Test 首日。

每个 fold 的 `walk_forward_results.csv` 保存名义半开窗口、实际 Train/Validation/Test 首尾、被 purge/embargo 的完整日期列表及数量、标签不完整/跨界移除行数，以及 Train/Validation 最大 `exit_date` 与下一阶段首日。Test 窗口不得互相重叠，也不得重复输出同一 `(date, symbol)`。

## 模型拟合与选择合同

### FactorScore

FactorScore 使用 YAML 中预先固定的 14 个因子权重，输入是逐日横截面 Z-score。缺失因子贡献按中性值 0 处理；无限值仍然报错。权重不从 Train、Validation 或 Test 学习，默认按绝对权重和归一化。

### Ridge

每个配置候选 alpha 都只在 Train 上拟合：

    Train median imputer
      → Train StandardScaler
      → Ridge fit
      → Validation 排序评价

默认选择指标为 Validation 的 prediction_rank_ic_mean。也允许在代码接口显式选择 Validation Prediction IC 或 Top-Bottom spread，但选择指标必须在 Test 前固定。候选胜出后，直接使用已经在 Train 上拟合的该模型对 Test 调用一次 predict；当前实现有意不做 Train+Validation 重拟合，便于严格审计训练范围。Test 不参与 alpha 选择。

Ridge 会保存标准化特征空间中的逐 fold 系数；模型持久化文件只应加载本项目自己生成且可信的本地文件。

## 样本外预测评价

Prediction IC 和 Spearman RankIC 均先按 Test 交易日做横截面 complete-case 相关，再在时间维度汇总。Top-K 与 Bottom-K 的成员先仅由当日有限 score 固定，再观察其未来标签；未来标签缺失不能把下一名事后补进组合。评价表同时报告 score coverage、Top/Bottom 标签覆盖率和实际已成熟标签数，避免把尚未实现的尾部误当成完整组合。结果支持：

- Overall；
- Year；
- Quarter；
- Walk-Forward Fold；
- 可选 Regime（Phase 3 产生市场状态列后启用）。

缺失标签保留在覆盖率分母中，但不进入已实现收益统计，也不改变 Top/Bottom 成员。因子五分位同样先按当日因子值分组，再汇总已成熟标签并报告每组标签覆盖率。指标为负、模型落后 benchmark 或复杂模型没有优势，均是有效研究结果，不是软件失败。

## 测试与网络边界

默认离线门禁：

    python -m pytest -q

pytest.ini 限制 testpaths=tests/research，并默认使用 -m "not network"。单元测试使用人工 DataFrame、供应商 mock 和小型 fixture，不要求真实账户、GUI 或网络。除 Phase 1 的 Schema、Cache、Universe、Factor、Label、Dataset/Metrics 测试外，Phase 2 已覆盖：

- fold 日期严格有序且 Train/Validation/Test 不重叠；
- Purge/Embargo 的交易日数量；
- 标签 exit_date 不越过下一评估区间；
- Train-only imputer/scaler，修改未来 fold 不改变过去已拟合结果；
- Ridge 只由 Validation 选 alpha，Test 不参与选择；
- Test (date, symbol) 唯一；
- target/entry/exit 等语义列不能被当作模型特征；
- 未来标签缺失不会改变 Top-K 或因子分位成员；
- 预测 IC/RankIC、尾部分组、标签覆盖率和 fold 审计汇总。

显式网络测试：

    python -m pytest -q -m network

AKShare/BaoStock 公开端点可能受代理、限频、断连或字段变化影响。2026-09-22 的真实 `download-data` 尝试整体为 failed：在 BaoStock 登录失败前只完成 benchmark 子步骤。尝试后本地缓存有 330 个 benchmark 交易日（研究开始日前 242 日、smoke 研究区间 88 日），下游从前者只选最后 130 日作为预热；这不表示 130+88 是整个缓存行数。AKShare 单股票网络测试仍发生 RemoteDisconnected，PIT 与个股链路均未完成。因此离线测试或 benchmark 子步骤成功不能冒充真实五年验证。真实运行的覆盖范围、失败股票和 manifest 必须据实报告。

## 研究完整性

模型或回测收益为负不是测试失败。数据时点错误、PIT 不完整、标签 off-by-one、fold 标签窗口泄漏、Test 参与选择或清单不可复现，才是必须阻止实验的错误。模型比较还要求源运行与当前运行的 Git commit、工作区 diff 指纹、包版本、数据/PIT 哈希和实际 OOS `(date,symbol,fold)` 键一致。烟雾配置和 synthetic fixture 仅验证软件链路，不能形成课程论文结论。
