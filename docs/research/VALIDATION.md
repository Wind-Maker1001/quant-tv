# FactorLab 验证与数据泄漏防护

## 当前状态

Phase 1 已实现数据、Point-in-Time 股票池、因子、标签、数据集和因子评价的正确性边界。Phase 2 已实现：

- 固定权重 FactorScoreModel；
- 仅在训练集拟合缺失值处理和标准化参数的 Ridge；
- 按月推进的 Expanding Walk-Forward；
- 交易日级 Purge、Embargo 和 entry_date/exit_date 标签窗口审计；
- Train → Validation 选参 → Test 仅评估一次；
- Test 样本的 Prediction IC、RankIC、Top-K/Bottom-K 与分组汇总。
- Train-only median imputer 的 LightGBM/XGBoost，以及 Validation-only 小候选选择；
- 只依赖 t 及以前 CSI500 数据的 Market Regime 和按状态评价；
- T+1、整手、现金、停牌和开盘涨跌停拒单的执行回测测试。

LightGBM、XGBoost、Market Regime、规则执行回测和 Phase 4 append-only Paper Signal 核心已经实现；真实 Forward Test 尚未激活。实现模型验证与记录能力不等于已经取得五年正式研究结果或真实样本外结果。

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
- LightGBM/XGBoost 的中位数缺失值处理器也只 fit(Train)，固定随机种子与单线程设置进入清单。
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

### LightGBM 与 XGBoost

两个树模型使用 YAML 中预注册的克制候选集。每个候选只在 Train 拟合，使用 Validation 平均 Prediction RankIC 选择；胜出模型不读取 Test 标签，也不因 Test 收益重新拟合或调参。逐 fold 保存所选 JSON 参数和 gain feature importance。LightGBM/XGBoost 是稳健性比较，不是无界参数搜索；与 Ridge 表现相近时应优先简单模型。

## 样本外预测评价

### Train / Validation / Historical Test 分阶段诊断

每个 fold 在选中模型对 Test 预测一次之后生成 TRAIN_IN_SAMPLE 诊断；
VALIDATION_SELECTION 直接复用该候选已用于选参的分数，不重复 predict。
三阶段仍为同一个 Train-only 模型，不重拟合 Train+Validation。
Train 诊断覆盖完整审计窗口，有缺标签的行不参与 fit 但保留评价覆盖分母。
各阶段分别按日期计算 IC/RankIC 和固定 Top/Bottom 标签收益，再逐 fold 汇总。
Train folds 重复包含旧日期，不合并为独立总体；Validation 存在选参乐观偏差，
不能冒充独立最终留出。主 predictions、绩效和两级回测仍只使用 Test。

stage audit 绑定窗口/成熟边界、输入/fit 子集、已选模型文件与实际参数/协议。
CLI 从同一可信 dataset 复核源摘要，比较强制四模型同 cohort，并只解析已核验的
字节快照，不重新拟合、选参或加载模型。详见
[STAGE_DIAGNOSTICS_AUDIT.md](STAGE_DIAGNOSTICS_AUDIT.md)。

### Test-only 主评价

Prediction IC 和 Spearman RankIC 均先按 Test 交易日做横截面 complete-case 相关，再在时间维度汇总。Top-K 与 Bottom-K 的成员先仅由当日有限 score 固定，再观察其未来标签；未来标签缺失不能把下一名事后补进组合。评价表同时报告 score coverage、Top/Bottom 标签覆盖率和实际已成熟标签数，避免把尚未实现的尾部误当成完整组合。结果支持：

- Overall；
- Year；
- Quarter；
- Walk-Forward Fold；
- Regime（BULL、BEAR、SIDEWAYS）。

缺失标签保留在覆盖率分母中，但不进入已实现收益统计，也不改变 Top/Bottom 成员。因子五分位同样先按当日因子值分组，再汇总已成熟标签并报告每组标签覆盖率。指标为负、模型落后 benchmark 或复杂模型没有优势，均是有效研究结果，不是软件失败。

## 测试与网络边界

默认离线门禁：

    python -m pytest -q

pytest.ini 限制 testpaths=tests/research，并默认使用 -m "not network"。单元测试使用人工 DataFrame、供应商 mock 和小型 fixture，不要求真实账户、GUI 或网络。除 Phase 1 的 Schema、Cache、Universe、Factor、Label、Dataset/Metrics 测试外，当前离线门禁已覆盖：

- fold 日期严格有序且 Train/Validation/Test 不重叠；
- Purge/Embargo 的交易日数量；
- 标签 exit_date 不越过下一评估区间；
- Train-only imputer/scaler，修改未来 fold 不改变过去已拟合结果；
- Ridge 只由 Validation 选 alpha，Test 不参与选择；
- Test (date, symbol) 唯一；
- target/entry/exit 等语义列不能被当作模型特征；
- 未来标签缺失不会改变 Top-K 或因子分位成员；
- 预测 IC/RankIC、尾部分组、标签覆盖率和 fold 审计汇总。
- 修改未来 benchmark 价格不会改变过去 Market Regime/指数特征；
- LightGBM/XGBoost Test 标签突变不改变所选候选或 Test score；
- 四模型使用相同 OOS 键与输入版本后才允许比较；
- T+1 当日不可卖、100 股整手、现金不为负、停牌/涨跌停拒单及历史板块规则。

显式网络测试：

    python -m pytest -q -m network

AKShare/BaoStock 公开端点可能受代理、限频、断连或字段变化影响。最新真实 `download-data` run `20260922T121535.543754Z-download-data-82695c7f` 整体为 failed：benchmark 缓存可读，但 BaoStock 登录连续 4 次返回网络接收错误。本地缓存有 330 个 benchmark 交易日（研究开始日前 242 日、smoke 研究区间 88 日），下游从前者只选最后 130 日作为预热；这不表示 130+88 是整个缓存行数。AKShare 单股票网络测试仍发生 RemoteDisconnected，PIT 与个股链路均未完成。因此离线测试或 benchmark 子步骤成功不能冒充真实五年验证。真实运行的覆盖范围、失败股票和 manifest 必须据实报告。

## 研究完整性

模型或回测收益为负不是测试失败。数据时点错误、PIT 不完整、标签 off-by-one、fold 标签窗口泄漏、Test 参与选择或清单不可复现，才是必须阻止实验的错误。模型比较还要求源运行与当前运行的 Git commit、工作区 diff 指纹、包版本、数据/PIT 哈希和实际 OOS `(date,symbol,fold)` 键一致。烟雾配置和 synthetic fixture 仅验证软件链路，不能形成课程论文结论。

## 历史 Test 统计稳健性

2026-10-10：模型比较新增按相同交易日配对的 ML−FactorScore 检验，考虑5日标签
重叠：Bartlett HAC 与非循环 moving-block Bootstrap；主检验固定三个总体 RankIC
差值，双侧 p 经 Holm 校正。ICIR 不是显著性检验；其他指标/分组及个别区间未做
多重比较校正，仅探索性解释，不选模型或调参数。Train/Validation 不进入主检验。
日历来自已经验证的 benchmark，缺失日保留槽位不压缩；常数、样本不足和覆盖不足
保留缺失 p/CI。新 CLI 报告绑定完整日历并在比较时从固定 Test scores 重算指标，
不 fit/predict。详情及条件/验收见 [MODEL_INFERENCE_AUDIT.md](MODEL_INFERENCE_AUDIT.md)。
上面的2026-09网络失败记录为历史证据，最新 PIT 来源限制见
[BAOSTOCK_SOURCE_AUDIT.md](BAOSTOCK_SOURCE_AUDIT.md)。
