# 余哈哈 A 股分钟观察数据接入

NO LIVE MONEY。该入口提供可重放的工程标准化与探索读取；不提供正式日线行情资格。
原始 ZIP/CSV 只读，现有 TDX 数据、公司行为、PIT、状态与正式门禁保持原有合同。

## 现状与证据

输入为 2021—2025 年 5 个 ZIP 及 2026 年 181 个 CSV。复用
[独立审查](../../INDEPENDENT_DATA_REVIEW_2026-10-17.md)及其
[逐日统计](evidence/independent-data-review-20261017-v1/daily-counts.csv)：
1,393 个日期、64,115,523 行、5,783 个跨年供应商代码，2021-01-04—2026-09-30。
这些是观察覆盖，并非完整交易所日历、历史有效交易代码或可交易证券的认证。

转换没有重新执行旧全量审计器。预检核验 186 个容器的字节 SHA、ZIP 成员元数据和来源集合；
必要的转换读取同时计算 CSV 内容 SHA，逐日与旧审计的记录数、证券数、标签集合、
单证券记录数分布及异常计数对账。输入读取前后及全程结束时检查 size/mtime/文件身份。

仓库的审计 JSON 是公开脱敏副本。旧 `final-verification.json` 的两个 SHA 指向私有原件；
转换器严格验证现有[公开映射](evidence/pit-publication-20261018-v1/manifest.json)中
`original_sha256 -> public_sha256` 及公开字节数，并把两套 SHA 和映射文件 SHA 写入新收据。
映射缺失或不匹配即拒绝；不修改旧收据、不猜测文本替换、不重算旧 PASS。
这属于本地证据完整性检查，不提供发布者数字签名或金融真实性证明。

## 独立分钟契约与逐字段映射

契约名 `FACTORLAB_YHH_30M_OBSERVATIONS_V1`；共 15 列。
Schema 和完整限制同时写入每份 Parquet 的 `factorlab_contract` 元数据及 JSON 收据。
源 CSV 为 UTF-8（允许 BOM）；所有列显式指定类型，不依赖第一个数据块推断。

| 原始 11 列 | 原始表示 | 标准字段与 Arrow 类型 | 转换与语义限制 |
| --- | --- | --- | --- |
| 证券代码 | 带 SH/SZ/BJ 后缀字符串 | `symbol: string`，另保留 `vendor_symbol: string` | 去首尾空白、转大写；必须六位代码及明确后缀，不按前缀猜交易所，不改写历史换码 |
| 证券名称 | 字符串 | `security_name: string` | 原值；名称不是历史 ST/停牌或证券身份依据 |
| 交易日期 | `YYYYMMDD` 字符串 | `trade_date: date32` | 必须与审计日期及时间戳日期一致 |
| 分钟时间 | `YYYY-MM-DD HH:MM:SS` 字符串 | `timestamp_local: timestamp[us]`，无时区 | 保留供应商墙上时钟；无 UTC 转换，不推定起点/终点/区间闭合方向 |
| 开盘价（元） | 数字文本 | `open: float64` | 原数值；元是源列声明，币种及价格设置尚未独立认证 |
| 最高价（元） | 数字文本 | `high: float64` | 同上 |
| 最低价（元） | 数字文本 | `low: float64` | 同上 |
| 收盘价（元） | 数字文本 | `close: float64` | 同上 |
| 成交量 | 数字文本 | `volume_vendor: float64` | 保留原单位；股/手未知，不乘 100，不转整数 |
| 成交额 | 数字文本 | `amount_vendor: float64` | 保留原单位；不按数量级猜元/万元 |
| 复权因子 | 数字文本或缺失 | `adjustment_factor_vendor: float64` | 原观察值；缺失转 Arrow null，禁止填 1 或用于推算复权 OHLC |

其余三列为 `source_id: string`（该 CSV 原始字节 SHA-256）、
`source_row: int32`（不含表头的 1 起始数据行号）、`quality_flags: uint16`。
每月收据用 `source_id` 连接容器名、ZIP 成员/松散文件名、日期、原件哈希及样本。
数字使用 float64，与既有审查的数值解析口径一致；原始十进制文本、空串/NaN 的拼写
由原件及哈希保留，不承诺重新输出完全相同的 CSV 字节。

可以可靠计算的是：规范日期/时间类型、代码字符串规范化、来源键、行号、
主键唯一性及结构性异常统计。尚不能可靠计算的是：真实区间起止、经认证的单位换算、
日线、复权四价、换手率、历史有效交易代码和证券状态。

## 与现有 18 列日线接口的差异

现有定义在 `qbot/research/data/schema.py:CANONICAL_BAR_COLUMNS`；
读取入口为 `qbot/research/data/providers/local.py:LocalParquetProvider`；
严格输入验证器为 `_strict_bars`，要求精确 18 列及日级唯一观察。
`qbot/research/data/market_qualification.py:qualify_market_data` 与 Local v2 来源绑定
仍负责复算正式资格；PIT 和证券状态是独立输入。

| 日线合同字段/能力 | 本批分钟观察可提供的内容 | 正式接入仍需补足 |
| --- | --- | --- |
| `date, symbol` | 供应商日期/代码与分钟时间 | 时段/区间合同、历史有效代码/稳定身份映射 |
| `open, high, low, close`、`raw_*` | 原供应商分钟四价 | 原价设置认证、明确日线聚合和缺失规则；本模块未生成 `raw_*` |
| `volume, amount` | `*_vendor` 原值 | 可追溯的价格/量额单位及缩放合同 |
| `turnover` | 不可用 | 可信历史换手或时点一致的流通股分母；禁止静态分母推算 |
| `adj_factor, adj_*` | 仅原始 `adjustment_factor_vendor` | 完整公司行为、算法、锚点、独立 HFQ 四价、舍入与版本证据 |
| PIT、身份、ST/停复牌 | 不可用/未验证 | 历史成员生效链、证券身份及逐日状态来源 |

本模块不继承 `MarketDataProvider`，不注册到日线配置，也不提供可被误用的 `get_bars`。
`daily_bars()` 明确拒绝。15 列分钟表传入 `_strict_bars` 同样拒绝；没有填充假的 18 列。

## 校验、异常与缺失规则

每个 CSV 的全部数据块共同验证 `(symbol, timestamp_local)` 主键；重复键、非法代码、
字段不符、非法/缺失日期或时间、日期不一致、来源哈希/审计计数不符均终止该月发布。
日级键集合随日期释放，内存不随全库规模增长。

数值和时段异常保留原记录并标记，不删除、不取绝对值、不补价、不伪造停牌：

| 位值 | 名称 | 含义 |
| --- | --- | --- |
| 1 | missing_numeric | 至少一个数值字段缺失 |
| 2 | nonfinite_numeric | 至少一个非有限数值（含缺失） |
| 4 | nonpositive_price | 四价中有非正数 |
| 8 | invalid_ohlc | 最高/最低与开收关系不符 |
| 16 | negative_volume | 原成交量为负 |
| 32 | negative_amount | 原成交额为负 |
| 64 | unrecognized_time_label | 不在既有常见九标签中，例如 15:30 |
| 128 | outside_regular_session | 不在机械比较的 09:30—11:30、13:00—15:00 范围 |

09:30、09:30—15:00 内的标签也未获得区间语义认证。零标记只表示未触发上述结构告警，
不表示数据资格通过。15:30 可能有供应商特殊定义，保留标签，不擅自删除或解释为错误。
6—10 根/日等模式仅与原审计分布对账，不补齐为 8/9 根。
所有时钟范围检查都是工程诊断，未引入新的交易所规则认证。

## CLI、分区、恢复与读取

在包含本模块的工作树内，使用已安装 `dev/requirements-research.txt` 的 Python 3.9 环境。
实现核对了 [PyArrow 17.0 增量 CSV 文档](https://arrow.apache.org/docs/17.0/python/csv.html#incremental-reading)：
使用 `open_csv` 显式类型和可配置 `block_size`，每批写入 Parquet，不展开年度 ZIP。

```powershell
# 第一阶段：完整一天及完整月份；--output 必须为新的独立目录。
python -B -X utf8 -m qbot.research.data.yhh30m convert --source <SOURCE_ROOT> --audit docs/research/evidence/independent-data-review-20261017-v1 --output data/research/yhh30m/pilot-day --start 2021-01-04 --end 2021-01-04
python -B -X utf8 -m qbot.research.data.yhh30m convert --source <SOURCE_ROOT> --audit docs/research/evidence/independent-data-review-20261017-v1 --output data/research/yhh30m/pilot-month --start 2026-02-01 --end 2026-02-28

# 独立验收：分别替换为上面一天/月的数据目录。只复读选定小样本。
python -B -X utf8 -m examples.research.accept_yhh30m --dataset data/research/yhh30m/pilot-month --source <SOURCE_ROOT> --audit docs/research/evidence/independent-data-review-20261017-v1 --output results/diagnostics/yhh30m/accept-month

# 小样本通过后，全量转换；同命令再次运行会核验并复用已经发布的月分区。
python -B -X utf8 -m qbot.research.data.yhh30m convert --source <SOURCE_ROOT> --audit docs/research/evidence/independent-data-review-20261017-v1 --output data/research/yhh30m/full-v1

# 输出回读验证，以及无需再扫描原始 CSV 的全量清单/报告。
python -B -X utf8 -m qbot.research.data.yhh30m verify --dataset data/research/yhh30m/full-v1
python -B -X utf8 -m examples.research.accept_yhh30m --dataset data/research/yhh30m/full-v1 --output results/diagnostics/yhh30m/full-acceptance
```

每月只有一份 `partitions/year=YYYY/month=MM/<identity>/bars.parquet`（Zstandard 压缩），
配一份 `receipt.json`。每个写入块最多 65,536 行/row group；CSV 默认读取块为 1 MiB。
收据记录完整选中日期及逐日对账、缺失/告警计数、每个日期 5 条可重定位原始随机样本、
软件版本、源码 SHA、输入/输出 SHA、峰值进程工作集及 Arrow 内存峰值。
逐行逻辑指纹采用 pandas 无索引、无分类编码的 64 位行哈希再 SHA-256；它验证批次切分等价性，
不替代 Parquet 文件的 SHA-256 与随机样本逐字段比对。

同一月先写 `.incomplete-*`；关闭、fsync 并回读 Schema/记录数/逻辑指纹/样本后，
以目录重命名发布。全局 `dataset.json` 通过同目录临时文件原子替换；
所有月完成且原件最终元数据检查通过前 `complete=false`，适配器拒绝不完整数据集。
如果进程中断，已发布的月会在重跑时重新核验并复用；未发布月从该月开头重跑。
`.incomplete-*` 不被读取或复用，保留用于定位失败；不会自动删除原件或其他数据。

使用 OS 文件锁排除并发写入，进程结束后锁自动释放，锁文件的存在本身不表示锁被持有。
既有文件损坏时拒绝覆盖；选择范围、契约或实现源码改变时要求新的输出根目录。
不接受原始目录/审计目录的上级、下级或相同目录作为输出；非空且无本模块标记的目录拒绝。
路径包含链接或 Windows reparse point 时拒绝。

```python
from pathlib import Path
from qbot.research.data.yhh30m import IntradayParquetProvider

provider = IntradayParquetProvider(Path("data/research/yhh30m/full-v1"), purpose="exploratory")
for batch in provider.iter_batches(start="2026-02-01", end="2026-02-28",
                                   symbols=["000001.SZ"],
                                   columns=["symbol", "timestamp_local", "close", "quality_flags"]):
    frame = batch.to_pandas()
    # 仅工程检查或明确标记的探索工作；不能将此表当日线送入原研究入口。
```

读取按选中月检查收据与数据 SHA，并支持日期、代码、列及批大小选择。
适配器不将零量解释为停牌，不将供应商代码回填成已认证历史身份。

## 验收与正式研究剩余条件

自动化测试：`python -B -X utf8 -m pytest tests/research/test_yhh30m.py -q`。
覆盖 ZIP/CSV、月分区、原值及缺失/负数保留、跨批重复键、不同块大小等价、代码/时间拒绝、
源文件/证据变更、显式脱敏映射、损坏拒绝、失败后续跑、幂等字节和 mtime、OS 锁与日线拒绝。
真实一天/整月另做一次性读取对比，以及使用独立 stdlib CSV 解析器逐原始 11 字段比对随机行。
全量按月进行输出回读，复用旧审计而非重新执行审查器。

本次实际运行结果、测试和数据清单见 [转换交付报告](YHH_30M_CONVERSION_DELIVERY.md)。
原始行情、带原始数值的每月收据和机器运行日志保存在忽略目录，不自动发布到 Git。

正式研究仍须获得：可信供应商和版本、区间/时间戳/时区/缺成交规则、价格和量额单位、
异常更正来源、稳定身份与历史换码链、独立历史日历、逐日状态与上市关系、
完整公司行为/复权方法/独立锚点、有效历史 PIT 及原有来源绑定资格。
这些条件不由 Parquet 文件数量、哈希一致性、局部四价一致或测试通过替代。
