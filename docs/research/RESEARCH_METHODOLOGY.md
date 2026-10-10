# Qbot FactorLab 研究方法论

本文定义《基于多因子与机器学习的 A 股横截面收益预测研究——以中证500为例》的研究合同。合同优先保证时点正确、可复现和可审计；盈利与否不是软件验收条件。

> **实现状态：Phase 1–4 核心研究软件已实现：数据/因子、四模型 Expanding Walk-Forward、市场状态、样本外预测评价、两级回测，以及预注册后 append-only 的 Paper Forward Signal。** 正式 Forward Test 尚未激活，也没有真实样本外记录。实现研究管线不等于已经取得正式五年实证结果。

## 1. 研究问题与预注册边界

研究考察：使用截至交易日 t 收盘已知的价格、成交量、换手率、波动率，以及由中证500指数同期信息构造的市场状态，能否预测中证500成分股未来 5 个交易日的相对收益。最终论文应回答：

1. Reversal、Momentum、Low Volatility、Liquidity 和 Trend 因子是否具有稳定的横截面预测能力？
2. 因子有效性是否随 BULL、BEAR、SIDEWAYS 市场状态改变？
3. Ridge、LightGBM、XGBoost 是否在严格样本外检验中优于固定权重 FactorScore？
4. Train、Validation、Historical Test 与真实 Forward Test 的性能差距有多大？
5. 加入费用、滑点、涨跌停、停牌、T+1 和整手约束后，历史 Alpha 还剩多少？

历史研究区间预先固定为 2021-09-13 至 2026-09-11。原研究协议把真实样本外信号起点设为 2026-09-14；系统没有生成任何当时信号，因此绝不事后回填或把历史重跑伪装成 Forward Test。Phase 4 软件现要求正式启动前另行冻结一个尚未来到的启用日、训练截止日、模型版本和参数候选，并从该日起 append-only 记录。烟雾配置只验证工程链路，不得用于形成研究结论。最终 Test 不用于筛因子、选 Top-K、修改市场状态或调整费用。

## 2. 研究对象与 Point-in-Time 股票池

研究对象是每个交易日当时真实有效的中证500成员，而不是研究结束时仍在指数中的股票。正式成员须由可核验的历史生效日资料导入逐日 CSV/Parquet 或明确闭区间。2026-10-09 复核 [BaoStock 官方文档](https://www.baostock.com/mainContent?file=pythonAPI.md#query_zz500_stocks)发现其成分每周更新；逐交易日调用仅证明查询日，不证明实际生效日。因此该来源目前仅供诊断，正式发布与消费均拒绝，不依赖人工 `verified` 标志放行。后续只有独立调样证据与新的受审计来源合同才能解除这项限制。用户当前没有历史文件，故尚无正式中证500实证结果。

正式股票池必须满足：

- 覆盖研究区间内全部中证500基准交易日；
- 每日恰有 500 个唯一 canonical symbol；
- `(date, symbol)` 唯一，日期和代码格式合法；
- 物化文件与 manifest 中的 SHA-256 一致。

任何缺日、重复、成员数量异常或哈希不一致均以 `POINT-IN-TIME UNIVERSE REQUIRED` 终止。系统绝不使用 AKShare 当前成分股回填历史。这一约束直接防止幸存者偏差，但公开数据源自身的事后修订风险仍需在论文局限性中披露。

在 PIT 成员基础上，当日依次过滤：上市不足 120 个基准交易日、ST/*ST、停牌、最近 20 日始终零成交量、最近 60 个市场交易日有效 OHLCV 覆盖率低于 80%。阈值由 YAML 固定；过滤只使用 t 日及此前可知信息。状态缺失在过滤器内部仍按保守排除处理，但正式数据集在进入过滤前就要求状态历史完整，不能用保守排除掩盖供应链缺口。

## 3. 数据、单位与交易日历

Phase 1 以 AKShare 为行情主源。PIT 成分、证券状态和上市日期可分别选择 BaoStock 或严格本地导入；供应商调用被隔离在统一 Provider 后，因子、标签和评价器只消费内部 Schema。两类来源都选择本地时，研究数据准备不会隐式登录 BaoStock。

内部股票代码统一为 `600000.SH`、`000001.SZ`，日期统一为 tz-naive `datetime64[ns]`。日线主键为唯一 `(date, symbol)`。个股同时下载未复权和配置指定的复权序列：

- `open/high/low/close` 与 `raw_*` 是原始价，供后续执行模拟；
- `adj_*` 是复权价，因子和标签只使用该组字段；
- 使用后复权 `hfq`；Phase 1 明确拒绝会重写历史尺度、无法安全增量拼接的 `qfq`，且不允许将未复权价冒充研究价格；
- AKShare 成交量从“手”乘 100 转为“股”，成交额为人民币元，换手率从百分数除以 100 转为小数；
- `adj_factor = adj_close / raw_close`。

中证500指数行情日期定义研究交易日历。默认在正式开始日前额外精确选取 130 个真实基准交易日（`data.warmup_trading_days`），并下载同期个股行情和状态，用于上市天数、60 日质量窗口与最长因子回看。PIT 成分仍只覆盖并严格验证 2021-09-13 至 2026-09-11；Builder 在完整预热日历上计算后，只输出这些研究成员日期，预热行不是研究样本。

个股对齐到该日历后，停牌或缺失日保留空值，不进行价格 `ffill`，任何地方均禁止用 `bfill` 把未来数据填回过去。

网络数据按股票或基准独立写入 Parquet 缓存，记录已覆盖区间、来源版本、内容哈希和更新时间。下载支持前后/中间增量、重试、节流和原子替换。单股失败不会丢弃其他已成功结果，但 benchmark、Schema 或 PIT 不完整会阻止正式数据集生成。

本地证券状态合同由精确的 `date,symbol,trade_status,is_st` 日表和 `symbol,listing_date` 上市表组成。`trade_status` 不得缺失且只能是整数 `0/1`，`is_st` 可为无缺失的布尔值或 `0/1`；日期、canonical symbol、唯一主键和上市日期边界均严格校验。每个 PIT `(date,symbol)` 成员键都必须显式覆盖；允许同一历史 symbol 集在有效 benchmark 交易日上的额外预热或非成员记录，但不为退市证券虚构未来状态，也不允许 `ffill`、`bfill` 或邻日推断。发布 manifest 将输入/输出哈希同时绑定到 PIT universe、交易日历和 symbol 集；任何 PIT 键缺失、非法值、哈希或绑定不一致都会终止研究流水线，部分下载不得覆盖此前完整版本。执行回测在真实订单触达日再次要求状态存在，非订单价格行的状态缺口不会被误判为供应链失败。

## 4. 信息时点与标签

默认决策时点是 t 日收盘后，最早成交时点是下一个交易日开盘：

```text
t 日及以前的行情/PIT/状态
  -> t 日收盘后计算因子与排序
  -> t+1 open 进入
  -> t+6 open 退出（持有 5 个交易日）
```

核心标签为：

```text
STOCK_FWD_RET5     = stock_adj_open[t+6] / stock_adj_open[t+1] - 1
BENCHMARK_FWD_RET5 = index_adj_open[t+6] / index_adj_open[t+1] - 1
EXCESS_RET5        = STOCK_FWD_RET5 - BENCHMARK_FWD_RET5
```

数据集同时保留 `entry_date`、`exit_date`、股票收益和基准收益，便于审计 off-by-one。入口、出口或基准开盘价任一缺失时标签为空。区间尾部尚未成熟的标签仍保留为空，不用未来数据补齐，也不在 Builder 中提前删除。

## 5. 因子体系

第一阶段预先固定 14 个可解释价量因子：

- Reversal：`REV1`、`REV5`；
- Momentum：`MOM20`、`MOM60`；
- Volatility：`VOL5`、`VOL20`、`VOL60`；
- Liquidity：`TURN5`、`TURN20`、`VOLUME_RATIO`、`AMIHU20`；
- Trend：`PRICE_MA20`、`MA5_MA20`、`MA20_MA60`。

所有计算按 symbol 独立、按日期向后 rolling，使用包含 t 日但不包含 t+1 的 `adj_close`、成交量、成交额和换手率。波动率使用样本标准差 `ddof=1`；Amihud 为 `mean(abs(return)/amount * 1e8)`，非正成交额视为缺失。完整公式和最短历史见 `FACTORS.md`。

## 6. 横截面预处理

预处理只在同一个交易日、通过当日过滤的横截面内估计。默认流程是：

1. 计算当日中位数与 MAD；
2. 截断到 `median ± 5 × 1.4826 × MAD`；
3. 使用截断后当日均值和总体标准差 `ddof=0` 做 Z-score；
4. 常数列映射为 0，缺失保持缺失；
5. 有效横截面少于 20 时该日该因子不进入评价。

数据集同时保存 `raw_<factor>` 和预处理后的同名因子。第一阶段不做市值或行业中性化；若后续加入，中性化暴露和回归参数也必须来自当日可知信息，训练期估计量不得在全样本上拟合。

## 7. 第一阶段因子评价

对每个有效交易日分别计算 Pearson IC 和 Spearman RankIC，再汇总 IC/RankIC 均值、日度样本标准差、未年化 ICIR/RankICIR、正值比例、有效日期数和平均覆盖率。

ICIR 本身不是统计显著性。历史四模型比较另外只对 Test 逐日指标做不确定性评价：
ML−FactorScore 按同日配对，总体 RankIC 的三个差值为固定双侧主检验，并用 Holm
校正。未来5日标签重叠使用 Bartlett HAC；另用非循环 moving-block Bootstrap
给出个别 percentile CI。参数进入实验前完整配置，不以 Test 优化。日期内的股票
相关性已由逐日 IC 聚合处理，不把全部股票—日视作独立观测；缺失日不被压缩。
分期/状态等分组和其他指标属于探索性评价，个别区间未校正；非平稳、缺失非随机
及 fold 重拟合限制推断。实现/原论文来源见
[MODEL_INFERENCE_AUDIT.md](MODEL_INFERENCE_AUDIT.md)。这只增加研究工具，尚无真实
五年数据支持优劣结论，也不等于对大量因子搜索或事后选模型作了全局校正。

每个因子先仅按当日可知的因子排名固定五组，再观察未来标签，报告 Q1 至 Q5 的未来 `EXCESS_RET5` 均值、每组标签覆盖率和 Q5-Q1。未来标签是否缺失不会改变分组边界或让下一名事后补位。还报告：

- 完整 benchmark 日历中相邻交易日、同股票因子值的 Spearman 自相关；
- 完整 benchmark 日历中相邻交易日，最高分位等权持仓的单边权重换手率；
- 每日横截面 Pearson 因子相关矩阵的跨日平均。

评价接口使用市场状态分组列，同时报告 `ALL`、BULL、BEAR、SIDEWAYS，而不改变历史总体定义。自相关和换手率先在完整交易日序列计算，再按当前日状态归组，不会跨过其他状态的日期配对。因子符号不会因测试结果不好而事后翻转。

## 8. Market Regime

系统以中证500构造简单、可解释且只依赖 t 及以前数据的状态：

- BULL：`close > MA60` 且 `MA20 > MA60`；
- BEAR：`close < MA60` 且 `MA20 < MA60`；
- SIDEWAYS：其他情况。

同时加入 `INDEX_RET5/20/60` 和 `INDEX_VOL20`。MA、收益和波动率全部向后滚动；早期 MA60 不完整时归为 SIDEWAYS，数值特征保留缺失，不向过去填充。状态定义在最终 Test 前冻结，不因模型或策略收益修改。

## 9. Walk-Forward 与四模型

第二阶段采用 Expanding Walk-Forward：正式配置初始训练 24 个月、验证 3 个月、测试 3 个月、每 3 个月前移。训练起点固定并逐 fold 扩大，窗口按中证500实际交易日历映射，行从不随机打乱。

标签覆盖未来 5 个交易日，因此 fold 边界默认使用 5 个交易日 Purge 和 5 个交易日 Embargo。当前 splitter 删除名义 Train 末尾的 purge 交易日，并删除名义 Validation 末尾、紧邻 Test 的 embargo 交易日；entry_date/exit_date 是强制审计字段，系统据此保证 Train 的 exit_date 早于 Validation 首日、Validation 的 exit_date 早于 Test 首日。每个 fold 保存实际窗口、间隔日期和被标签审计移除的行数，Test (date,symbol) 不得跨 fold 重复。

处理顺序固定为：

    Train 拟合
      → Validation 选择预先给定的小规模候选
      → 已选 Train 模型对 Test 预测一次
      → Test 只用于最终评价

当前实现有意不做 Train+Validation 重拟合，使每个模型的拟合范围直接可审计。Scaler、缺失处理、未来的特征选择/中性化/PCA 和模型参数只能在 Train 上拟合。禁止根据最终 Test 选择因子、模型、Top-K、费用或状态定义。

另外保存同一已选模型逐 fold 的 TRAIN_IN_SAMPLE、VALIDATION_SELECTION 和
HISTORICAL_TEST 预测诊断。训练期诊断在 Test 预测之后追加，不影响选择；Validation
复用原候选分数，不重新预测。训练内表现不是样本外能力，验证表现受选择偏差影响，
三个不同时期差距不能单独证明过拟合。扩大训练集重复包含旧日期，因此 Train 指标
不跨 fold 池化。分阶段输入/标签/fit 子集、参数、覆盖、指标与模型文件摘要进入审计；
主 Test 指标和交易回测保持独立。见 [STAGE_DIAGNOSTICS_AUDIT.md](STAGE_DIAGNOSTICS_AUDIT.md)。

Phase 2 交付并冻结了两个基线模型：

- FactorScore：使用 YAML 预先冻结的 14 因子权重求加权和，默认除以绝对权重和；缺失因子贡献为中性值 0，权重不学习。
- Ridge：Train 内按列拟合 median imputer 和 StandardScaler，再拟合 Ridge；由 Validation 的平均 Prediction RankIC 在 alpha 候选中选参，保存标准化特征空间的逐 fold 系数。

Phase 3 在相同 `ResearchModel` 与 Walk-Forward 合同下加入：

- LightGBM：Train-only median imputer，固定随机种子和单线程配置；Validation 仅在 YAML 预注册的小候选集中按平均 Prediction RankIC 选择，保存逐 fold gain importance。
- XGBoost：使用同样的 Train-only 缺失处理、Validation-only 候选选择、固定随机种子和逐 fold gain importance 合同。

LightGBM/XGBoost 运行库延迟到实际拟合时导入；研究环境在 `dev/requirements-research.txt` 固定版本。缺少本地运行库会明确失败，不会退化为其他估计器或伪造树模型结果。两个树模型用于稳健性比较，不进行无界超参数搜索；与简单模型表现相近时优先保留简单模型。

样本外评价先在每个 Test 日期计算 Prediction IC、Spearman RankIC、Top-K/Bottom-K future return 和 Top-Bottom spread，再报告 Overall、Year、Quarter、Fold 和 Regime。IC 使用有限 score/label 的 complete cases；Top/Bottom 成员只由当日 score 固定，未来标签缺失只能降低已实现标签覆盖率，不能改变当时的选股。

Phase 3 的 `compare-models` 固定比较 FactorScore、Ridge、LightGBM、XGBoost 四个模型，不自动选赢家。它要求四次源运行具有完全相同的配置、代码与工作区指纹、Python/包环境、数据集/PIT/回测输入哈希、模型产物哈希，以及实际 OOS `(date,symbol,fold)`、标签窗口和已实现目标；随后统一输出预测指标、Fast Backtest、规则执行回测、市场状态和特征重要性/系数对照。若任何身份不一致即停止；若全部模型落后 benchmark，也必须原样报告。

## 10. 组合与交易假设

Phase 2 Fast Research Backtest 已实现：在 t 日收盘后按样本外 score 排序，按中证500交易日历每 5 日生成 Top 20 等权目标，在 t+1 adj_open 执行，并计算 Strategy、Benchmark 与 Excess NAV。分数并列按 symbol 确定性排序；正式调仓日的有限 score 数量不足 `max(Top-K, evaluation.min_cross_section)` 时直接失败，避免用未来不可接受的集中权重掩盖数据质量问题。

快速层按理论目标权重和名义金额记账，不产生整数股数。调仓目标或待卖持仓缺执行开盘价时直接失败；非调仓持仓缺价时以内部最后有效 mark 冻结估值，复牌时相对停牌前 mark 确认累计变化。该 mark 只用于组合估值，不回填行情或进入因子。

费用按生效日期查表并逐交易记录佣金、最低佣金、卖出印花税、过户费、买卖附加费和滑点。卖出印花税区分 2021-09-13 至 2023-08-27 的 10 bps 与 2023-08-28 起的 5 bps，其他费率由 YAML 独立配置。

Phase 3 已实现独立的日线规则执行回测：同一批 Test-only Top-K 信号在 t+1 `raw_open` 尝试成交，先卖后买，以 FIFO lot 记录 T+1 可卖数量，买单按 100 股整手和可用现金缩量，并逐笔计费。执行层使用 `volume`、`trade_status`、`is_st`、上一有效 `raw_close` 和按板块/日期生效的涨跌停表；停牌、缺 bar/开盘价/前收盘价、开盘触及买卖方向涨跌停、T+1、整手和现金造成的未成交数量均写入拒单表。该实现直接使用 Pandas/NumPy，不依赖 Legacy Backtrader，也不发送订单到券商。

> Daily-bar backtest cannot perfectly reconstruct order-book liquidity.

规则执行层只在目标执行日尝试订单，不把日线开盘价等同于真实可成交队列，也不模拟挂单跨日生命周期。日线无法还原封单队列、集合竞价、部分成交、冲击成本和盘中路径。所有绩效必须同时展示 benchmark、成本、换手、风险指标、拒单和预测排序能力，不能只展示一条策略净值。

## 11. Forward Test

Phase 4 已实现软件流程，但正式配置保持关闭。启用前必须在干净 Git 工作区提交研究配置，并在仍未到来的新起点之前创建不可覆盖的激活收据；注册时刻来自内部时钟，公共 API 不能注入历史时间。收据同时绑定研究合同、Git 与 FactorLab 源码/研究依赖摘要；`2026-09-14` 已经错过，永久没有资格被补写为 `ON_TIME`。最终模型必须在 activation 日前冻结，只使用 `exit_date <= training_asof` 的成熟标签，参数来自配置中显式指定的单一候选，不读取 Historical Test 自动选优。

每日 `15:30 Asia/Shanghai` 后，命令在全流程独占锁内将运行时数据截至日精确固定到信号日，增量更新行情、逐日 PIT 股票池和证券状态，重新构造当日因子并验证数据集来源。任一下载失败或当日因子非有限即停止，不允许用模型插补掩盖不完整横截面；随后用冻结模型产生 Top-K 等权 Paper Signal。记录包含信号日、数据截至日、带上海时区的生成时间、模型与版本、Git SHA、run_id、股票池/激活/研究合同/源码哈希、symbol、score、rank 和目标权重，不发送真实订单。

信号采用 append-only 语义：日期级独占锁内分配版本，完整 staging 后原子发布；producer run 成功后再原子追加包含成功运行清单快照的 completion receipt。中途崩溃留下的 orphan version 不是正式信号，后续只能新建版本而不能补改原目录。重跑旧日期只能带原因生成 `LATE_REISSUE` 新版本，不能覆盖旧记录或称为当时预测。正式评价必须按预先规定选择版本，不得事后挑选收益最好者。实现收益应在标签成熟后以关联产物追加，不能修改原始信号。

Schema 3 在同一次原子发布内分别保存 Top-K 组合与全部合格股票的完整预测，并绑定预测行数、股票池/数据/模型身份与独立内容摘要。任一分数非有限即停止，不能只保存正常股票而声称完整覆盖。Top-K 是完整排名的严格前缀；读取器验证成功完成收据及同一次读取的字节哈希。旧 schema 2 的 Top-K-only 记录无法支持全股票池 IC 或 Bottom-K，系统拒绝为其补算历史分数。

成熟关联入口 `evaluate-forward` 已实现：研究契约事前固定 FIRST_ON_TIME，每日选择最早完整且已成功完成的当日收盘后版本。后续版本与迟到重发明确排除，异常证据失败；不根据未来收益选版本。只读可信本地行情，通过实际基准交易日历关联 t+1 → t+6 的原始开盘超额标签，并追加新 run_id 报告及成功收据，原始预测、排名和信号不变。区分未成熟与已成熟但缺价，保留全体预测作覆盖率分母；Top-K 缺价不晋升候选。按年、季度、市场状态给出预测指标；若补算评价市场状态则只使用 t 及此前的基准数据，明确不是当时保存字段。该标签是成本前的预测评价，不等于执行后组合收益。

新增组件仅完成软件与合成数据验证，未生成真实 Forward IC。随后已经补齐历史
Train/Validation/Test 的逐 fold 诊断软件，但没有补齐真实研究输入。真实五年数据/PIT、
正式冻结模型与事前批准的新激活日仍缺，四阶段的完整实证差距不能据现有合成产物
回答。见 [FORWARD_EVALUATION_AUDIT.md](FORWARD_EVALUATION_AUDIT.md) 和
[STAGE_DIAGNOSTICS_AUDIT.md](STAGE_DIAGNOSTICS_AUDIT.md)。

本地文件摘要和系统时间不等于第三方可信时间戳。课程证据应把配置、激活收据、冻结模型和每日信号按顺序提交到不可改写的 Git 历史；若需更强证明，应使用受保护远端或外部时间戳/WORM 存储。详细操作见 `FORWARD_TEST.md`。

## 12. 可复现性与审计

配置成功加载后的每条 CLI 命令创建 `results/runs/<run_id>/manifest.json`，记录命令、状态、完整配置、固定随机种子、Python/包版本、Git SHA、工作区是否有未提交改动及其内容指纹、审计的上游提交、数据区间、因子列表、股票池哈希、产物路径和失败摘要；配置解析失败发生在 run 创建前，不生成实验 manifest。随机种子默认为 42。`dataset_manifest.json` 另将数据集 Parquet 的 SHA-256、PIT 版本及数据/股票池/标签/预处理配置合同，与生成数据集时的 run_id、成功 build-dataset 清单及 Git/工作区/Python/包版本绑定；因子评价和模型运行发现任一不一致即停止。每次模型运行保存模型目录全部文件以及实际 Fast/Execution 回测股票行情、benchmark 和证券状态输入的 SHA-256。`compare-models` 只接受代码/工作区/Python/包环境、完整配置、数据/PIT/回测输入版本一致，模型产物未被修改，且实际 OOS 键、标签窗口与已实现目标完全相同的源运行；比较结果按自己的 run_id 隔离存放，避免覆盖历史证据。逐模型报告保存已选候选、Validation 指标、Test-only predictions、Ridge 系数或树模型 gain importance、市场状态分解，以及 Fast/Execution 两级回测表、图片和拒单明细。

正式课程结果至少应归档：使用的 YAML、成功 manifest、PIT universe manifest、因子报告、失败股票清单和生成时间。原始网络端点可能修订数据，因此相同代码并不保证多年后重新下载得到逐字节相同内容；内容哈希用于识别而不是掩盖这种差异。

## 13. 偏差控制与测试证据

研究正确性的自动化守卫包括：

- 人工价格序列验证每个因子公式；
- 修改 t+1 及以后价格后，断言 t 日因子不变；
- 验证标签严格对应 `t+1 -> t+6`；
- 验证股票进入指数前和退出指数后不在股票池；
- 验证 Schema、唯一主键、日期顺序、OHLC 和单位；
- 验证 Purge/Embargo 后日期有序且标签窗口不重叠；
- 验证 Train-only imputer/scaler、Validation-only alpha 选择和 Test-only 输出；
- 验证 2023-08-27/28 费用边界、Top-K 等权、next-open 执行和组合指标；
- 验证市场状态与指数衍生特征只依赖 t 及以前数据，未来价格变化不改变过去输出；
- 验证 LightGBM/XGBoost 的 Train-only imputer、Validation-only 候选选择、Test 标签隔离和特征重要性；
- 验证 T+1、整手、现金、停牌和按日期/板块生效的涨跌停执行约束及明确拒单。

默认 `pytest` 只收集安全的 `tests/research` 且排除 network marker。真实网络烟雾运行必须单独执行并据实记录，mock 单测和 `python -m examples.research.phase3_synthetic_demo` 只能证明软件链路可执行，不能冒充真实数据成功或形成研究结论。

## 14. 局限性与结论纪律

- AKShare/BaoStock 是公开接口，可能限频、变更字段或事后修订；它们不等同于交易所级不可变行情库。
- 2026-09-22 的真实 `download-data` 尝试整体失败：BaoStock 登录失败前只完成 benchmark 子步骤。尝试后缓存有 330 个 benchmark 交易日（研究开始日前 242 日、smoke 研究区间 88 日），下游仅选最后 130 个研究前交易日作预热；AKShare 单股票网络测试仍断连，PIT 与真实股票数据链路未完成，尚未生成正式五年实证结果。
- 日线无法精确还原盘口流动性、停复牌盘中时点和成交优先级。
- Phase 2 快速回测仍是目标权重近似；Phase 3 规则执行回测另行近似 T+1、整数手、现金、停牌和开盘涨跌停，两层结果不可混称。
- 五年、单一指数和少量价量因子的统计功效有限，结果不应外推为所有 A 股时期或股票池的普遍规律。
- 横截面样本在日期内相关，ICIR 和组合检验需结合时间序列稳定性，不能把股票-日行数误当作完全独立样本量。
- 多次研究决策会增加数据窥探风险；任何探索性变更都应标记并在新验证期或 Forward Test 中复核。
- 公开 PIT 成分和状态无法完整获取时，正式回测停止；不得以当前成员、插值或人工猜测代替。

最终报告应同时展示有效与无效因子、正负市场阶段、模型失败、交易成本侵蚀和缺失数据。研究结论只能来自预先冻结的历史 Test 与后续真实 Forward Test；负收益或复杂模型没有优势同样是有效结论。
