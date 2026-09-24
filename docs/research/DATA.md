# FactorLab 数据规范

本文保留 Phase 1 建立的原始数据边界，并补充 Phase 3 的市场状态与规则执行输入合同。其中 PIT 股票池、benchmark、证券状态和 Schema 是正式研究的硬前置，不允许静默降级。

## 数据源与责任边界

| 数据 | 来源/生成方式 | 用途 |
| --- | --- | --- |
| A 股日线 | AKShare `stock_zh_a_hist` | 原始/后复权 OHLC、量、额、换手率 |
| 中证500指数日线 | AKShare 指数端点 | benchmark、交易日历、超额收益标签、Phase 3 市场状态 |
| 中证500历史成分 | BaoStock `query_zz500_stocks(date=...)` | 逐交易日 Point-in-Time 股票池 |
| ST/交易状态、上市日期 | BaoStock | 当日可交易性过滤、Phase 3 停牌/涨跌停执行判断 |
| 用户历史成分表 | 日级快照或显式闭区间 CSV/Parquet 导入 | BaoStock 的可验证替代路径 |

因子、标签和数据集代码不直接调用任何数据供应商，只消费统一 Provider/Schema 输出。AKShare 当前成分快照不得用于历史日期。

## Canonical symbol 和日期

- 沪市：`600000.SH`；深市：`000001.SZ`。
- 六位股票代码、`sh600000`、`SH.600000` 等供应商形式在 Provider 边界转换。指数代码建议总是显式带交易所后缀。
- 日期统一为去时区、归一到零点的 `datetime64[ns]`。
- 所有日级表的逻辑主键为唯一 `(date, symbol)`，并以 `date, symbol` 稳定排序。

## 标准行情 Schema

| 字段 | 单位/语义 |
| --- | --- |
| `date` | tz-naive 交易日 |
| `symbol` | canonical symbol |
| `open/high/low/close` | 原始、未复权价；也是规则执行仿真的价格边界 |
| `volume` | 股；AKShare 返回的“手”乘以 100 |
| `amount` | 人民币元 |
| `turnover` | 小数；AKShare 百分数除以 100 |
| `adj_factor` | `adj_close / raw_close`，有效值必须为正 |
| `raw_open/raw_high/raw_low/raw_close` | 原始价的显式副本 |
| `adj_open/adj_high/adj_low/adj_close` | 配置的复权价；正式默认为后复权 `hfq` |

Schema 验证包括：必需列、日期类型、symbol 格式、排序、主键重复、OHLC 全有或全缺、`high`/`low` 关系、价格为正、量/额/换手不为负，以及 canonical OHLC 与 `raw_*` 一致。

指数日线没有个股复权问题：当前实现把 raw/adj/canonical 价设为相同，`adj_factor=1`。

## 原始价与复权价

个股下载同时请求未复权和配置的复权序列，并严格要求两者的交易日完全一致。

- 收益、技术因子和标签：仅使用 `adj_*`。
- 涨跌停判断和成交仿真：使用 `raw_*`。
- 这两类价格不允许在研究代码中隐式替换。

## 交易日历与停牌

交易日历来自中证500指数行情日期，不依赖静态节假日表。日历必须唯一、单调递增。默认 `data.warmup_trading_days: 130`：下载器先取得足够早的基准行情，再从研究开始日之前精确选取最后 130 个真实基准交易日。个股行情和 BaoStock 状态也覆盖这段预热期。

预热数据只用于上市天数、数据质量窗口和因子向后滚动计算；PIT 快照仍只要求并验证正式研究区间，最终特征和数据集也只输出 PIT 成员日期。这样首个研究日可使用既有历史，同时不会把预热日期冒充研究样本。

个股序列按该日历与 PIT 股票集重建完整网格。停牌或源数据缺失日的市场字段保留为 `NaN`：

- 禁止 `bfill`。
- 不用价格 `ffill` 伪造交易。
- rolling 窗口遇到缺失时不伪造完整历史。

## Phase 3 市场状态与指数特征

`build_market_regime_features` 对按日期严格递增、无重复且属于 `000905.SH` 的 benchmark 序列计算：

- `MARKET_REGIME`：`adj_close > MA60` 且 `MA20 > MA60` 为 BULL；`adj_close < MA60` 且 `MA20 < MA60` 为 BEAR；其余为 SIDEWAYS；
- `INDEX_RET5/20/60`：当前 `adj_close` 相对 5/20/60 个交易日前的收益；
- `INDEX_VOL20`：日收益的 20 个交易日样本标准差。

全部特征仅使用 t 日及以前的 benchmark。最初不足 60 个有效观测的状态归为 SIDEWAYS，无法计算的数值特征保留 `NaN`；benchmark 缺口不使用未来或原始价补齐。状态表按 `date` many-to-one 合并到 PIT 过滤后的横截面，因此同一交易日所有股票必须只有一个状态。`market_regime.enabled=true` 时，这些列进入数据集合同和后续模型/报告校验。

## 单股 Parquet 缓存

`ParquetBarCache` 为每个 symbol 保存一个 Parquet 和一个 metadata JSON。metadata 包含：

- 数据源及版本、更新时间、行数、实际数据起止日期。
- 已成功请求的 inclusive `covered_ranges`。
- Parquet 内容 SHA-256。

`covered_ranges` 记录请求成功的日历区间，即使周末、停牌或上市前没有 bar，也不会被无限重复请求。新请求仅填补未覆盖的前/后/中间区间，重叠日期以最后一次成功请求为准。Parquet 和 JSON 各自通过同目录临时文件加 `os.replace` 原子替换；两文件之间不是跨文件事务，异常中断后哈希不一致会 fail fast，需要重新获取该 symbol 缓存。

缓存可断点续跑，但不是不可变原始数据库。每次实验仍必须用 run manifest 记录数据区间、股票池哈希和依赖版本。

## Point-in-Time CSI500 股票池

正式流程对交易日历的每一日请求 BaoStock 历史快照。单日快照以 Parquet 加配套 JSON 独立缓存；JSON 绑定 provider 类、来源版本、指数、日期、预期成员数和内容 SHA-256。缺少或不匹配来源元数据的旧快照不会被信任，而会重新请求，避免把预置的“当前成分股”文件洗成历史 BaoStock 证据。下载失败可以续跑；但物化正式股票池前必须同时满足：

1. 覆盖全部请求交易日，无缺日、无额外日。
2. 每日恢复的 `is_member=true` 成员恰有 500 个唯一 symbol。
3. 没有重复 `(date, symbol)`，symbol 均为 canonical 形式。

通过后产生：

- `csi500_daily.parquet`：`date,symbol,is_member`。
- `csi500_intervals.parquet`：`symbol,entry_date,exit_date,interval`，首尾均包含；退出后再进入会形成新区间。
- `manifest.json`：schema、来源、来源版本、指数代码、生成时间、范围、交易日数、预期成员数和基于规范化 CSV 表达的稳定 SHA-256。消费端逐项与当前配置和 benchmark 日历核对，不只检查内容哈希。

任一不满足都抛出含 `POINT-IN-TIME UNIVERSE REQUIRED` 的错误。失败日期写入 `failures.json`。

如使用 `import-universe`，必须先把 `universe.provider` 设为 `local`。导入器只接受两种互斥布局：

- 日级快照：`date,symbol[,is_member]`；
- 显式闭区间：`symbol,entry_date,exit_date[,is_member,interval]`，语义严格为 `entry_date <= trading_date <= exit_date`；首尾都必须显式填写。若提供 `is_member`，每行都必须明确为真；`interval` 只作为输入审计列，输出会重新编号。仍有效的成员应把 `exit_date` 填为研究期末或之后的已核验日期，不能用空值代替证据。

区间只在当前 benchmark 交易日历上展开；研究区间内的首尾边界必须本身是 benchmark 交易日，不能把周末、节假日或公告日静默平移。日级和区间日期字符串都必须使用 `YYYY-MM-DD`，带时间、时区或数值时间戳会被拒绝。同一股票的闭区间不能重叠；展开后仍必须逐日恢复恰好 500 个唯一成员。输入同时含日级和区间列、包含未声明的附加列，或使用语义未定义的 `opt-in/opt-out` 列时会 fail fast，必须先依据可核验来源转换为真实生效日的闭区间。

导入 manifest v2 记录输入布局、成员语义、原始文件绝对路径与 SHA-256，并分别绑定规范化逐日表和重新压缩区间表的内容哈希；消费端会同时校验两份产物及其相互一致性。因此等价的日级和区间输入得到相同股票池版本。写入使用独占 writer lock、唯一临时文件并以 manifest 最后发布；残留锁不会被自动删除，以免两个写者错误并发。消费端为已有产物保留对严格 `user-pit-daily-import-v1` 的只读兼容；即使旧 manifest 没有区间哈希，也会把其区间表与逐日表重新压缩结果对比。新导入统一写 v2。随后 `download-data` 会校验并复用该导入股票池，绝不以 BaoStock 快照覆盖。BaoStock 在 Phase 1 中仍用于 ST、停牌状态和上市日期。使用 `provider=baostock` 的配置不能消费本地导入 manifest，反之亦然。

三个正式文件分别原子替换，manifest 最后发布，但普通文件系统无法把三个路径作为单一事务切换。进程若在中间被强制终止，消费端会因哈希不一致而 fail closed，旧版本也可能暂时不可用；应确认没有存活 writer、人工检查残留锁后重新运行导入。后续可用不可变 generation 目录加单一原子指针进一步提高故障后的可用性，这不改变当前“绝不消费混合代数据”的正确性边界。

## 当日过滤

过滤仅在已验证 PIT 成员上执行，不会借此修复成分池。默认顺序/条件为：

1. 上市至少 120 个基准交易日。
2. 非 ST/*ST；状态缺失时保守视为 ST。
3. 非停牌；交易状态缺失时保守视为停牌。
4. 最近 20 个市场交易日至少一天成交量为正。
5. 最近 60 个市场交易日的有效 OHLCV 覆盖率至少 80%。

滚动状态只使用当日及之前数据。上述窗口和阈值由 YAML 配置，不散落在策略代码中。

## 数据集输出

Builder 先验证完整 PIT，再重建股票-日历网格、过滤、计算因子、标签和可选市场状态，最后按日横截面预处理。产物为：

- `features/raw_factors.parquet`：`date,symbol,raw_<factor>`。
- `features/processed_factors.parquet`：`date,symbol,<factor>`。
- `processed/dataset.parquet`：过滤后长表，同时含原始/预处理因子、标签、`entry_date`、`exit_date`；Phase 3 默认还含 `MARKET_REGIME`、`INDEX_RET5/20/60` 和 `INDEX_VOL20`。
- `processed/dataset_manifest.json`：绑定数据集文件 SHA-256、PIT 股票池哈希、因子/标签及会影响数据集内容的配置合同，并保存生成该数据集的 run_id、Git commit、工作区 diff、Python 和包版本；模型阶段不允许在代码、环境、数据文件或该数据集合同改变后静默复用旧数据集。模型、验证、组合与费用等不改变数据集内容的配置由各模型 run 的完整配置另行审计。

区间尾部无法观测完整持有期的标签保留为缺失，不在 Builder 中删除。评价和后续训练按用途过滤标签缺失样本。

## Phase 3 规则执行输入与版本

规则执行回测不复用复权研究价伪造成交。每个实际 OOS 窗口需要：

- 个股 `raw_open`、`raw_close` 和 `volume`，用次日开盘尝试成交、收盘估值并识别无成交量状态；
- 与 `(date,symbol)` 一一对应的 `trade_status` 和 `is_st`，由 `security_status.parquet` 补齐；缺少对应价格行的状态覆盖会停止 CLI；
- 中证500 `adj_open` 与 `adj_close`：benchmark 也从首个执行日开盘开始暴露，此后与策略一样按收盘估值；
- YAML 中按主板/创业板/科创板及生效日期冻结的涨跌停比例，以及同一费用日程。

执行器从每只股票此前最后一个有效 `raw_close` 构造当日涨跌停参考价，只把它用于规则判断，不写回行情或因子。每次模型 run 分别记录 Fast Backtest 股票行情、benchmark 与附加状态后的 Execution bars 哈希；四模型统一比较要求这些版本完全一致。成交、持仓、现金、净值和拒单是模型报告产物，不会写回原始数据缓存。

## 已知限制

- 公开数据端点可能变更字段、限频或事后修订；缓存与 manifest 只提供工程可审计性，不等于交易所授权的不可变数据。
- BaoStock 的历史快照必须经真实日期烟雾验证；无法完整获取时，正式回测必须停止。
- 通用第三方成分区间档案可能使用公告日、调样基准日、排他性退出日，或把证券当前代码反向套用到全部历史。这些文件不能直接导入；必须先逐项核对官方调样生效日和历史证券代码，再转换为上述显式闭区间。系统不会猜测其语义。
- 2026-09-24 对一个公开候选档案的复核已经发现提前一个交易日调样和历史 ticker 回填，详见 [PIT_SOURCE_AUDIT.md](PIT_SOURCE_AUDIT.md)；该档案未被复制或接入。
- 日线规则执行已经实现，但不能重建盘中路径、集合竞价、委托队列、部分成交或冲击成本；开盘涨跌停拒单是保守近似。
- 截至 2026-09-24，最新干净提交 `067bc396e58bc72b16374d9d5d92feef137adf66` 上的 smoke 运行 `20260924T052738.474084Z-download-data-a0cd6342` 已验证 benchmark 覆盖（88 个研究交易日、130 个精确预热交易日），但 BaoStock PIT 登录连续四次网络接收错误后安全失败；此前 AKShare 单股票端点也曾断连。失败 run manifest 的 `git_dirty=false`、`universe_version=null`，证明没有把不完整 PIT 冒充成功产物。真实股票与状态链路未完成，因此尚无正式五年数据集或四模型实证结果，离线/synthetic 验收不能替代该前置。
