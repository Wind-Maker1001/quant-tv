# FactorLab 数据规范

本文保留 Phase 1 建立的原始数据边界，并补充 Phase 3 的市场状态与规则执行输入合同。其中 PIT 股票池、benchmark、证券状态和 Schema 是正式研究的硬前置，不允许静默降级。

## 数据源与责任边界

| 数据 | 来源/生成方式 | 用途 |
| --- | --- | --- |
| A 股日线 | AKShare `stock_zh_a_hist` | 原始/后复权 OHLC、量、额、换手率 |
| 中证500指数日线 | AKShare 的中证指数官方端点 | benchmark、交易日历、超额收益标签、Phase 3 市场状态 |
| 中证500历史成分 | 严格本地导入的已核验生效成员；BaoStock 接口目前仅诊断 | 逐交易日 Point-in-Time 股票池 |
| ST/交易状态、上市日期 | BaoStock 或严格本地导入 | 当日可交易性过滤、Phase 3 停牌/涨跌停执行判断 |
| 用户历史成分表 | 日级快照或显式闭区间 CSV/Parquet 导入 | BaoStock PIT 成分接口的可验证替代路径 |
| 本地历史行情文件 | `local_parquet`，显式 raw/hfq CSV/Parquet | 静态来源快照，严格单位、复权、哈希与版本合同 |

因子、标签和数据集代码不直接调用任何数据供应商，只消费统一 Provider/Schema 输出。AKShare 当前成分快照不得用于历史日期。

官方调样证据可通过 `python -m examples.research.collect_official_notices` 单独归档，
见 [OFFICIAL_SOURCE_ARCHIVE.md](OFFICIAL_SOURCE_ARCHIVE.md)。原始请求/附件哈希与获取
时刻便于逐份复查，但不能替代完整权威起点名单及实际生效链；该模块没有 PIT 发布接口。

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

Schema 验证包括：必需列、日期类型、symbol 格式、排序、主键重复、OHLC 全有或全缺、`high`/`low` 关系、价格为正、量/额/换手不为负、全部数值字段不为无穷大，以及 canonical OHLC 与 `raw_*` 一致。提供的非空 `adj_factor` 必须与 `adj_close/raw_close` 一致（`rtol=1e-8, atol=1e-10`）；不一致时明确失败而非覆盖。停牌缺失仍保留。

指数日线没有个股复权问题：当前实现把 raw/adj/canonical 价设为相同，`adj_factor=1`。

## 原始价与复权价

个股下载同时请求未复权和配置的复权序列，并严格要求两者的交易日完全一致。

- 收益、技术因子和标签：仅使用 `adj_*`。
- 涨跌停判断和成交仿真：使用 `raw_*`。
- 这两类价格不允许在研究代码中隐式替换。

FactorLab 的增量行情缓存固定使用后复权 `hfq`。后复权历史尺度在新增交易日时保持稳定，适合按区间追加；前复权 `qfq` 会在新的除权事件后重写既有历史，不能安全地由当前缓存算法增量拼接。因此 Phase 1 配置加载器会拒绝 `qfq`，而不是生成可能存在尺度断层的数据。

行情缓存 metadata v3 通过不可变 `symbol.<generation>.parquet` 与单一 `symbol.metadata.json` 指针发布。先写完并校验新数据，再原子切换清单；发布失败不会破坏上一代，未被清单引用的文件不代表已下载覆盖。读取只固定一次清单及其数据字节，哈希和 Parquet 解析使用同一份内存内容。每股更新使用 OS 文件锁保护读取、合并、发布；`cache.lock_timeout_seconds` 默认 10 秒。锁文件长期存在，进程退出自动释放 OS 锁，不能通过删除文件来解锁。严格有效的 metadata v2 可只读，下次成功更新迁移到 v3；v1 或来源身份冲突仍须归档并重建。当前不会自动清理旧 generation，以免移除运行或清单引用的数据。

Windows 对空文件也先取得原生字节锁，再初始化锁文件；打开方式为无缓冲，避免初始化写入留在临界区之外。初始化失败也释放锁；解锁失败时保留正在处理的主异常并记录 WARNING，若主操作本来成功则明确抛出 CacheError，不报告虚假成功。

`000905.SH` 基准优先调用 AKShare 的 `stock_zh_index_hist_csindex`（中证指数官方历史行情入口），不依赖当前已不稳定的东方财富指数代码映射接口。官方接口的成交金额按文档所示从亿元转换为人民币元；成交量在不同端点修订中曾分别表现为“万手”或已经换算后的“股”，Provider 以成交金额/成交量的可解释比例识别这两种已知形式，统一为股，无法验证单位时直接失败。该选择由固定 AKShare 版本和代码共同决定，不会在一次请求中静默混用多家指数价格。

## 交易日历与停牌

交易日历来自中证500指数行情日期，不依赖静态节假日表。日历必须唯一、单调递增。默认 `data.warmup_trading_days: 130`：下载器先取得足够早的基准行情，再从研究开始日之前精确选取最后 130 个真实基准交易日。个股行情和 BaoStock 状态也覆盖这段预热期。

配置的 `data.start` 与 `data.end` 必须是实际基准交易日，且两日都必须出现在缓存中。缺少任一边界时，下载和读取均明确失败，避免把仅返回半段历史的响应当成完整研究区间。周末或节假日边界也会失败，用户应将其显式改为目标研究区间的首末交易日。这项校验能识别首尾截断；仅靠从 benchmark 推导日历无法证明中间没有遗漏交易日，正式数据验收仍需独立核对完整交易日序列。

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

- 数据源及严格版本合同、更新时间、行数、实际数据起止日期。AKShare 合同同时绑定包版本、具体端点、原始/复权组合和复权方式。
- 已成功请求的 inclusive `covered_ranges`。
- Parquet 内容 SHA-256。

`covered_ranges` 记录请求成功的日历区间，即使周末、停牌或上市前没有 bar，也不会被无限重复请求。新请求仅填补未覆盖的前/后/中间区间，重叠日期以最后一次成功请求为准。新代完整写入后才通过 `os.replace` 切换 JSON 指针；异常中断不会破坏上一代，孤立的新文件不算已覆盖日期。读取固定指针所引用的数据并严格验证哈希，不读取便利别名。

正式读取会验证两文件成对存在、metadata schema 版本、symbol、来源合同、内容哈希、行数、数据起止日期以及所有 bar 是否落在已声明覆盖区间。端点、AKShare 版本或复权合同改变时，即使请求日期已经全部覆盖也会直接失败，绝不把旧数据与新数据拼接或把旧 metadata 重标为新来源。升级到本合同前生成的 v1 缓存无法证明端点身份，因此必须先人工归档，再由当前版本重新下载；程序不会自动删除用户数据。

缓存可断点续跑，旧 generation 保持不可变但尚无自动归档/清理策略。每次实验仍必须用 run manifest 记录数据区间、股票池哈希、原始行情版本和依赖版本。本地静态行情的导入、版本变更和无网络流水线见 [LOCAL_MARKET_DATA.md](LOCAL_MARKET_DATA.md)。

### 下载异常与正式研究阻断

股票循环只有明确的 `ProviderNetworkError` 可以记录失败列表后继续；Schema、来源合同、缓存完整性、文件权限和未知编程错误必须立即停止。AKShare 只对明确的 transport 错误及可辨识的 HTTP 408/425/429/5xx 执行配置的重试；不按错误消息猜测网络故障，不重试结构错误。Benchmark 是强制输入，即使网络故障也不能跳过。

致命行情错误在 `raw/download_status/` 留下跨 Provider 的不可变收据及 SHA-256 历史链，记录 symbol、请求范围、来源版本、run_id、Git SHA 和错误。未解决收据会以 `UNRESOLVED DOWNLOAD CONTRACT` 阻止数据集、因子评价、Walk-Forward、模型比较及 Forward 入口。旧完整缓存、换 Provider 或重新运行日期都不能自动解除它。重跑 `download-data` 必须实际请求包含所有旧失败窗口的区间，取得非空响应，通过 Schema 和缓存快照校验后追加 resolution；Benchmark 修复还必须由实际新响应满足研究边界和预热要求，不能靠合并的旧缓存补证据。

解除仅允许针对请求开始前已观察的同 symbol fatal 集合；若并发任务随后新增同 symbol fatal，本次取数不能把新错误一起清除。必须重新抓取并验证，不能只检查失败日期范围相同。

首次或后续收据发布中断、缺历史、孤立文件、空初始化目录和指针不一致均严格失败，不自动删除历史。永久父目录 OS 锁保护初始化和发布。完全没有创建过守卫的旧缓存仍可通过此检查，但这不是对旧下载行为的追溯认证。收据是本地误损检测，不是外部防篡改公证；完全不可写的存储无法保证留证，手动删除全部收据与引用也无法仅靠本机日志自证。备份、人工恢复和验证范围见 [DOWNLOAD_CONTRACT_VERIFICATION.md](DOWNLOAD_CONTRACT_VERIFICATION.md)。

检查在命令入口和固定输入快照时进行，不是运行期间持续监控其他进程。网络失败允许下载扫描结束为 success，但若此前仍有 fatal，清单的 `unresolved_download_receipts` 和 WARNING 明确表明正式研究仍被阻止；success 不代表所有股票已下载或正式研究就绪。

上述 Schema 验证针对 SDK 暴露的输出。本地固定 AKShare SDK 某些端点先做数值 coercion、直接解析 JSON 而没有 `raise_for_status`，Provider 不能恢复已丢失的原始异常数值或 HTTP 状态。此时无法证实为网络错误的失败按致命合同错误处理，不冒充完整的原始 payload 校验。

## Point-in-Time CSI500 股票池

2026-10-09 官方来源复核发现：BaoStock 明确说明中证500成分信息每周一更新，`date` 是查询日期，`updateDate` 是更新日期，没有在该接口文档中承诺逐日实际调样生效语义。[官方接口说明](https://www.baostock.com/mainContent?file=pythonAPI.md#query_zz500_stocks)、[官方更新时间说明](https://www.baostock.com/mainContent?file=home.md)。因此当前实现不再将逐日调用自动视为正式 PIT：BaoStock 收集器在查询、缓存读取与发布前拒绝；CLI 同时拒绝旧 BaoStock 最终 manifest，即使成员数、日期、哈希都合法。错误为 `POINT-IN-TIME UNIVERSE REQUIRED: EFFECTIVE MEMBERSHIP SEMANTICS UNVERIFIED`。没有 `verified=true` 绕过开关。研究配置不能只切换成 `local` 就信任旧 BaoStock 文件，必须通过已审计来源的真实生效日导入。来源调查、隔离新版公共节点诊断与限制见 [BAOSTOCK_SOURCE_AUDIT.md](BAOSTOCK_SOURCE_AUDIT.md)。

通用快照收集/缓存组件仍有离线测试，但不是未核验 BaoStock 的正式发布入口。正式股票池必须同时满足：

1. 覆盖全部请求交易日，无缺日、无额外日。
2. 每日恢复的 `is_member=true` 成员恰有 500 个唯一 symbol。
3. 没有重复 `(date, symbol)`，symbol 均为 canonical 形式。

BaoStock 诊断响应仍检查命名 `code` 字段、服务端查询日期、非法及重复代码、迭代后的错误码，并保留原始 `updateDate` 集合。这些检查不证明实际成员生效日，也不保证 SDK 对空分页响应一定报告错误。`baostock-query_zz500_stocks-daily-v2` 是旧查询合同，不是生效日期核验；v1/v2 最终股票池都不能进入正式研究。Provider 单层默认三次重试共四次请求，诊断可以显式零重试。

通过后产生：

- `csi500_daily.parquet`：`date,symbol,is_member`。
- `csi500_intervals.parquet`：`symbol,entry_date,exit_date,interval`，首尾均包含；退出后再进入会形成新区间。
- `manifest.json`：schema、来源、来源版本、指数代码、生成时间、范围、交易日数、预期成员数和基于规范化 CSV 表达的稳定 SHA-256。消费端逐项与当前配置和 benchmark 日历核对，不只检查内容哈希。

任一不满足都抛出含 `POINT-IN-TIME UNIVERSE REQUIRED` 的错误。失败日期写入 `failures.json`。

如使用 `import-universe`，必须先把 `universe.provider` 设为 `local`。导入器只接受两种互斥布局：

- 日级快照：`date,symbol[,is_member]`；
- 显式闭区间：`symbol,entry_date,exit_date[,is_member,interval]`，语义严格为 `entry_date <= trading_date <= exit_date`；首尾都必须显式填写。若提供 `is_member`，每行都必须明确为真；`interval` 只作为输入审计列，输出会重新编号。仍有效的成员应把 `exit_date` 填为研究期末或之后的已核验日期，不能用空值代替证据。

区间只在当前 benchmark 交易日历上展开；研究区间内的首尾边界必须本身是 benchmark 交易日，不能把周末、节假日或公告日静默平移。日级和区间日期字符串都必须使用 `YYYY-MM-DD`，带时间、时区或数值时间戳会被拒绝。同一股票的闭区间不能重叠；展开后仍必须逐日恢复恰好 500 个唯一成员。输入同时含日级和区间列、包含未声明的附加列，或使用语义未定义的 `opt-in/opt-out` 列时会 fail fast，必须先依据可核验来源转换为真实生效日的闭区间。

导入 manifest v3 记录输入布局、成员语义、原始文件绝对路径与 SHA-256，并分别绑定规范化逐日表和重新压缩区间表的内容哈希，以及两份不可变 generation 文件的字节哈希。等价的日级和区间输入得到相同语义股票池版本。消费端只保留严格 local v1/v2 的只读兼容；即使旧 manifest 没有区间哈希，也会把区间表与逐日表重新压缩结果对比。新导入写 schema 3。随后 `download-data` 会校验并复用该导入股票池，绝不以 BaoStock 快照覆盖。`universe.provider=baostock` 目前被语义门禁阻断；本地配置也不能消费 BaoStock 身份的 manifest。导入器能验证结构、范围和哈希，不能替用户证明文件来自真实官方历史成员；切勿把每周快照改列名后导入冒充真实生效数据。

先完整写 `csi500_daily.<generation>.parquet` 与 `csi500_intervals.<generation>.parquet`，最后原子替换 `manifest.json`。读取端固定一次 manifest，只读取它指向的两份文件，并验证路径、字节哈希和语义一致性。无后缀的 canonical 文件仅是 commit 后 best-effort 更新的便利别名；别名失败仅记 WARNING，不影响已发布数据。新代写入或清单切换失败时，上一代仍可读取；旧 schema 升级失败也不会提前改动其别名。PIT 发布仍采用独占 writer lock；进程强制终止可能留下 `.universe-write.lock`，它不影响读取旧代，但再次发布前必须确认无存活 writer，再人工恢复。不要自动猜测或删除锁。

## 证券状态与上市日期

证券状态来源由 `universe.status_provider` 独立选择：`baostock` 表示联网取得历史状态，`local` 表示只消费经过严格验证的本地导入。它与 `universe.provider` 彼此独立；两者都设为 `local` 时，PIT 成分、ST/停牌状态和上市日期链路完全绕过 BaoStock，不会为了状态数据隐式登录网络服务。

本地导入命令为：

    python -m qbot.research.cli import-security-data --config path/to/csi500_local.yaml --status path/to/security_status.csv --listings path/to/listing_dates.csv

输入只接受下列精确列，不接受未声明的附加列：

- 状态表：`date,symbol,trade_status,is_st`；主键 `(date,symbol)` 必须唯一，`trade_status` 必须是无缺失的整数 `0/1`，`is_st` 可使用无缺失的布尔值或 `0/1`。
- 上市日期表：`symbol,listing_date`；每个 symbol 必须恰有一行。

symbol 必须已经是 canonical 形式，日期必须是严格 `YYYY-MM-DD`，不能包含时分秒、时区、数值时间戳或模糊格式。上市日期不得晚于该股票首次 PIT 成员日期；落在本次 benchmark 覆盖区间内的上市日期必须本身是 benchmark 交易日。

导入器以已验证的 PIT 股票池和 benchmark 日历为边界执行完整性检查：上市日期表的 symbol 集必须与 PIT 历史出现过的 symbol 集完全相等；PIT 中每个有效的 `(date,symbol)` 成员键都必须有一条明确状态。输入可以额外包含同一历史 symbol 集在有效 benchmark 交易日上的预热、入指前或退指后状态，但系统不要求为已经退市的证券伪造后续记录。系统不使用 `ffill`、`bfill`，也不从前后日期猜测 ST 或停牌状态。规则执行层另在实际订单触达的日期逐行检查状态，任何真实执行键缺少 `trade_status` 或 `is_st` 都会 fail fast。

完整校验通过后才发布 `security_status.parquet`、`listing_dates.parquet` 和 `security_data_manifest.json`。manifest 记录原始输入与规范化输出的 SHA-256，并绑定 PIT universe 哈希、benchmark 日历哈希、symbol 集、日期范围、行数、来源和来源版本；读取端会重新核对这些身份。任一缺 PIT 成员键、缺 symbol、重复、非法枚举、越界日期、哈希或绑定不一致都会以 `SECURITY STATUS DATA REQUIRED` 终止。下载失败或部分结果只按 run_id 写为 `*.partial.<run_id>.parquet` 诊断材料，不得覆盖此前完整的正式产物，也不得发布一个看似成功的 manifest；下一次验证成功会把 `status_failures.json` 重置为绑定当前 `security_data_version` 的空失败记录，旧 partial 文件不会被消费。

正式读取以 manifest 指向的不可变 `security_status.<generation>.parquet` 和 `listing_dates.<generation>.parquet` 为准；无 generation 后缀的两个文件只是便于人工查看的最新别名。发布时先完整写入新 generation，最后原子替换 manifest 指针。即使别名或新 manifest 写入中途失败，旧 manifest 仍指向上一组未变产物，消费端不会读到混合代数据。

## 当日过滤

过滤仅在已验证 PIT 成员上执行，不会借此修复成分池。默认顺序/条件为：

1. 上市至少 120 个基准交易日。
2. 非 ST/*ST。
3. 非停牌。
4. 最近 20 个市场交易日至少一天成交量为正。
5. 最近 60 个市场交易日的有效 OHLCV 覆盖率至少 80%。

滚动状态只使用当日及之前数据。上述窗口和阈值由 YAML 配置，不散落在策略代码中。过滤器自身仍会把缺失状态保守排除，但正式流水线不会依赖这种退化行为：证券状态合同必须先完整通过，缺失数据会在过滤前 fail fast。

## 数据集输出

Builder 先验证完整 PIT，再重建股票-日历网格、过滤、计算因子、标签和可选市场状态，最后按日横截面预处理。产物为：

- `features/raw_factors.parquet`：`date,symbol,raw_<factor>`。
- `features/processed_factors.parquet`：`date,symbol,<factor>`。
- `processed/dataset.parquet`：过滤后长表，同时含原始/预处理因子、标签、`entry_date`、`exit_date`；Phase 3 默认还含 `MARKET_REGIME`、`INDEX_RET5/20/60` 和 `INDEX_VOL20`。
- `processed/dataset_manifest.json`：schema 4 绑定数据集文件 SHA-256、PIT 股票池、证券状态、因子/标签配置合同及 `bar_data_provenance` / `bar_data_version`，并保存 producer run_id、Git commit、工作区 diff、Python 和包版本。行情证据来自实际输入快照，覆盖 benchmark 和 PIT 全历史 symbol 并集；尚无缓存的成员也以 missing 记录，因此补齐缺失成员会使旧数据集失效。正式消费者校验清单、成功 producer run 与当前行情语义版本；旧 schema 3 必须重新 `build-dataset`，不能手工补字段。模型、验证、组合与费用等不改变数据集内容的配置由各模型 run 的完整配置另行审计。

行情语义版本包含完整缓存字节哈希、来源合同、行数、日期范围和请求覆盖，不包含绝对路径、随机 generation 或抓取时间。同内容重发布可复用，但任一行情修订、新增成员缓存或研究窗口以外的追加也保守地要求重建数据集。完整清单仍保留 generation、文件名和 metadata 字节哈希用于审计。Walk-Forward 在训练前固定全部行情快照，Fast/Execution 回测使用同一批已验证股票和 benchmark，不在训练后重读活动缓存；四模型比较同时要求一致且可验证的原始行情语义版本。哈希不能证明供应商没有事后修订，只能证明本次实验使用的具体输入。

这些原子发布保证进程中断时不消费混合代数据；不宣称抵御所有断电、磁盘故障或目录元数据损坏。所有旧 generation 均暂时保留。

区间尾部无法观测完整持有期的标签保留为缺失，不在 Builder 中删除。评价和后续训练按用途过滤标签缺失样本。

## Phase 3 规则执行输入与版本

规则执行回测不复用复权研究价伪造成交。每个实际 OOS 窗口需要：

- 个股 `raw_open`、`raw_close` 和 `volume`，用次日开盘尝试成交、收盘估值并识别无成交量状态；
- `security_status.parquet` 中可获得的 `trade_status` 和 `is_st`；预热、入指前或退指后但不发生订单的价格行可以没有状态，实际订单触达的执行键缺少任一状态字段时立即停止；
- 中证500 `adj_open` 与 `adj_close`：benchmark 也从首个执行日开盘开始暴露，此后与策略一样按收盘估值；
- YAML 中按主板/创业板/科创板及生效日期冻结的涨跌停比例，以及同一费用日程。

执行器从每只股票此前最后一个有效 `raw_close` 构造当日涨跌停参考价，只把它用于规则判断，不写回行情或因子。每次模型 run 分别记录 Fast Backtest 股票行情、benchmark 与附加状态后的 Execution bars 哈希；四模型统一比较要求这些版本完全一致。成交、持仓、现金、净值和拒单是模型报告产物，不会写回原始数据缓存。

## 已知限制

2026-10-10 新增官方来源证据与 HTML 候选复核，见
[OFFICIAL_SOURCE_ARCHIVE.md](OFFICIAL_SOURCE_ARCHIVE.md)。公开浏览器保存的正文
和本机 HTTP 下载使用不同获取方式、不同收据；每个正文容器与其解码 UTF-8
响应文本分别绑定 SHA，不称为历史可用性或外部时间戳证明。3张早期调整表的
300条候选事件不是300只成员；另外2份 PDF 未取得，完整起点及临时调整仍缺失。
这些诊断不会生成或导入日级 universe，不改变正式数据消费者的 PIT 门禁。

- 公开数据端点可能变更字段、限频或事后修订；缓存与 manifest 只提供工程可审计性，不等于交易所授权的不可变数据。
- BaoStock 的历史快照必须经真实日期烟雾验证；无法完整获取时，正式回测必须停止。
- 通用第三方成分区间档案可能使用公告日、调样基准日、排他性退出日，或把证券当前代码反向套用到全部历史。这些文件不能直接导入；必须先逐项核对官方调样生效日和历史证券代码，再转换为上述显式闭区间。系统不会猜测其语义。
- 2026-09-24 对一个公开候选档案的复核已经发现提前一个交易日调样和历史 ticker 回填，详见 [PIT_SOURCE_AUDIT.md](PIT_SOURCE_AUDIT.md)；该档案未被复制或接入。
- 日线规则执行已经实现，但不能重建盘中路径、集合竞价、委托队列、部分成交或冲击成本；开盘涨跌停拒单是保守近似。
- 2026-10-04 的网络复核中，AKShare 中证官方端点直连成功返回 2021-09-13 至 2026-09-11 共 1211 行基准行情，量额均无缺失；但东方财富个股后复权请求仍被远端断开，BaoStock 登录也在四次重试后以 socket 错误失败。Windows 系统代理当时指向不可用的 `127.0.0.1:10808`，即使仅在测试进程绕过代理，两个股票/PIT 端点仍不稳定。因此没有启动 500 股下载，也没有把仅成功的 benchmark 冒充完整 smoke。真实股票、PIT 与状态链路仍未完成，尚无正式五年数据集或四模型实证结果，离线/synthetic 验收不能替代该前置。
- 2026-10-05 再次分别执行两个真实 Provider 测试：AKShare 个股原始价请求在四次尝试后仍为 `RemoteDisconnected`；BaoStock 登录四次尝试后仍为 socket 错误（`WinError 10057`）。两项均失败，真实小样本验收继续缺少可用行情/PIT 输入。文件级离线验收已覆盖本地 PIT、证券状态、Parquet 缓存、14 因子、标签和报告，但使用人工数据，不能据此形成研究结论。
