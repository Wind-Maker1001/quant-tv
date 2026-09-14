# FactorLab 数据规范

本文定义 Phase 1 的数据边界。其中 PIT 股票池、benchmark 和 Schema 是正式研究的硬前置，不允许静默降级。

## 数据源与责任边界

| 数据 | Phase 1 来源 | 用途 |
| --- | --- | --- |
| A 股日线 | AKShare `stock_zh_a_hist` | 原始/后复权 OHLC、量、额、换手率 |
| 中证500指数日线 | AKShare 指数端点 | benchmark、交易日历、超额收益标签 |
| 中证500历史成分 | BaoStock `query_zz500_stocks(date=...)` | 逐交易日 Point-in-Time 股票池 |
| ST/交易状态、上市日期 | BaoStock | 当日可交易性过滤 |
| 用户历史成分表 | CSV/Parquet 导入 | BaoStock 的可验证替代路径 |

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
| `open/high/low/close` | 原始、未复权价；也是未来执行仿真的价格边界 |
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
- 未来涨跌停判断和成交仿真：使用 `raw_*`。
- 这两类价格不允许在研究代码中隐式替换。

## 交易日历与停牌

交易日历来自中证500指数行情日期，不依赖静态节假日表。日历必须唯一、单调递增。默认 `data.warmup_trading_days: 130`：下载器先取得足够早的基准行情，再从研究开始日之前精确选取最后 130 个真实基准交易日。个股行情和 BaoStock 状态也覆盖这段预热期。

预热数据只用于上市天数、数据质量窗口和因子向后滚动计算；PIT 快照仍只要求并验证正式研究区间，最终特征和数据集也只输出 PIT 成员日期。这样首个研究日可使用既有历史，同时不会把预热日期冒充研究样本。

个股序列按该日历与 PIT 股票集重建完整网格。停牌或源数据缺失日的市场字段保留为 `NaN`：

- 禁止 `bfill`。
- 不用价格 `ffill` 伪造交易。
- rolling 窗口遇到缺失时不伪造完整历史。

## 单股 Parquet 缓存

`ParquetBarCache` 为每个 symbol 保存一个 Parquet 和一个 metadata JSON。metadata 包含：

- 数据源及版本、更新时间、行数、实际数据起止日期。
- 已成功请求的 inclusive `covered_ranges`。
- Parquet 内容 SHA-256。

`covered_ranges` 记录请求成功的日历区间，即使周末、停牌或上市前没有 bar，也不会被无限重复请求。新请求仅填补未覆盖的前/后/中间区间，重叠日期以最后一次成功请求为准。Parquet 和 JSON 各自通过同目录临时文件加 `os.replace` 原子替换；两文件之间不是跨文件事务，异常中断后哈希不一致会 fail fast，需要重新获取该 symbol 缓存。

缓存可断点续跑，但不是不可变原始数据库。每次实验仍必须用 run manifest 记录数据区间、股票池哈希和依赖版本。

## Point-in-Time CSI500 股票池

正式流程对交易日历的每一日请求 BaoStock 历史快照。单日快照独立缓存，下载失败可以续跑；但物化正式股票池前必须同时满足：

1. 覆盖全部请求交易日，无缺日、无额外日。
2. 每日恢复的 `is_member=true` 成员恰有 500 个唯一 symbol。
3. 没有重复 `(date, symbol)`，symbol 均为 canonical 形式。

通过后产生：

- `csi500_daily.parquet`：`date,symbol,is_member`。
- `csi500_intervals.parquet`：`symbol,entry_date,exit_date,interval`，首尾均包含；退出后再进入会形成新区间。
- `manifest.json`：来源、版本、生成时间、范围、交易日数、预期成员数和基于规范化 CSV 表达的稳定 SHA-256。

任一不满足都抛出含 `POINT-IN-TIME UNIVERSE REQUIRED` 的错误。失败日期写入 `failures.json`。

如使用 `import-universe`，可把 `universe.provider` 设为 `local`。随后 `download-data` 会校验并复用该导入股票池，绝不以 BaoStock 快照覆盖；BaoStock 在 Phase 1 中仍用于 ST、停牌状态和上市日期。

## 当日过滤

过滤仅在已验证 PIT 成员上执行，不会借此修复成分池。默认顺序/条件为：

1. 上市至少 120 个基准交易日。
2. 非 ST/*ST；状态缺失时保守视为 ST。
3. 非停牌；交易状态缺失时保守视为停牌。
4. 最近 20 个市场交易日至少一天成交量为正。
5. 最近 60 个市场交易日的有效 OHLCV 覆盖率至少 80%。

滚动状态只使用当日及之前数据。上述窗口和阈值由 YAML 配置，不散落在策略代码中。

## 数据集输出

Builder 先验证完整 PIT，再重建股票-日历网格、过滤、计算因子和标签，最后按日横截面预处理。产物为：

- `features/raw_factors.parquet`：`date,symbol,raw_<factor>`。
- `features/processed_factors.parquet`：`date,symbol,<factor>`。
- `processed/dataset.parquet`：过滤后长表，同时含原始/预处理因子、标签、`entry_date`、`exit_date`。

区间尾部无法观测完整持有期的标签保留为缺失，不在 Builder 中删除。评价和后续训练按用途过滤标签缺失样本。

## 已知限制

- 公开数据端点可能变更字段、限频或事后修订；缓存与 manifest 只提供工程可审计性，不等于交易所授权的不可变数据。
- BaoStock 的历史快照必须经真实日期烟雾验证；无法完整获取时，正式回测必须停止。
- 日线数据不能重建盘中路径、集合竞价或委托队列；这属于后续 Execution Backtest 的显式局限。
