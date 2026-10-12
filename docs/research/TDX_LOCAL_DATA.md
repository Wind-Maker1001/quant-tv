# 通达信 DAY：只读审计与 RAW staging

本模块只解决原始二进制行情的可追溯工程入口，永久保持 **NO LIVE MONEY**。
不生成复权价，不认证中证500成员，不推断上市、退市、ST或停牌，
不向正式缓存、DatasetBuilder或Forward发布数据。工程转换成功与金融研究合格分开记录。

## 与既有架构的关系

已审阅 ARCHITECTURE_AUDIT、DATA、LOCAL_MARKET_DATA、RESEARCH_METHODOLOGY、
VALIDATION、GETTING_STARTED、PERFORMANCE_BASELINE，以及现有 Provider、Schema、
cache、provenance、calendar、universe、config和DatasetBuilder。

生产 LocalParquet 只接受精确18列，股票后复权OHLC、turnover和adj_factor须显式提供；
缓存v3通过不可变generation和metadata指针发布，数据集还绑定PIT、状态、来源和运行证据。
生产canonical symbol只支持SH/SZ；BJ只在本模块的独立staging保留六位代码.BJ。
本任务没有修改上述生产合同、14因子、市场状态、四模型、Walk-Forward、研究YAML、
Forward开关、Legacy、交易功能或原LICENSE。

新增 `qbot/research/data/tdx.py`（发现、边界、分类、解析、审计）、
`tdx_staging.py`（原子RAW转换及诊断），两个独立examples CLI和三份离线测试。
仅使用现有NumPy/Pandas/PyArrow和标准库；Python 3.9兼容，无新增依赖。

## 只读扫描与复现

本机通过目录枚举找到如下真实路径，不是根据截图猜测名称：

```powershell
$tdxVipdoc = 'D:\Code\通达信金融终端(开心果交易版)V2025.01 2月23日更新\通达信金融终端(开心果交易版)V2025\vipdoc'
.venv-py39\python.exe -X utf8 -m examples.research.audit_tdx_local --vipdoc-root $tdxVipdoc
# 追加 --convert 才写独立RAW staging；不联网
.venv-py39\python.exe -X utf8 -m examples.research.audit_tdx_local --vipdoc-root $tdxVipdoc --convert --calendar data/research/benchmark/000905.SH.4f0b56be280e4bff88a4aa45d72cde64.parquet
```

默认审计区间2020-01-02至2026-10-09；正式研究参考区间2021-09-13至2026-09-11，
预热130日。CLI可以显式指定，不能为绕过质量要求修改研究YAML。
`--calendar`只读本地CSV/Parquet日期列；没有独立完整交易日历时覆盖结论仍为UNKNOWN/
UNVERIFIED。现有benchmark只覆盖2021-03-08至2026-09-11，可核对研究和预热，
不能据此证明完整2020—2026日历。新运行默认生成独占run_id；已有run_id直接拒绝。
返回0表示工程扫描完成；1表示存在明确异常/失败，完整报告仍保留；2表示入口失败。

递归扫描明确的sh/sz/bj三个lday目录。所有DAY（含错误文件名）进入发现清单；
非DAY单独记录。拒绝路径穿越、根边界逃逸、符号链接、Windows junction/reparse祖先、
非常规/多硬链接文件。每个输入只打开rb，同一次字节用于SHA和解析，并检查读前/中/后
文件身份、长度和时间。原文件不移动、不重编码、不删除。重复canonical symbol的
不同源副本全部报错，不自动选一份。路径检查针对本机正常文件系统；本工具不提供
对恶意管理员并发替换目录的隔离保证。

## 二进制及语义合同

候选布局为32字节小端：date:uint32，open/high/low/close:uint32，amount:float32，
volume:uint32，reserved:uint32。记录顺序、原整数、保留字段和float32信息全部保留。
源float32转float64只是精确保留其既有数值，不能恢复下载时已经丢失的成交额精度。

按全文件检查空/截断、严格递增、重复/非法日期、区间外/周末、非正或有符号负值解释
的价格、OHLC关系、负/NaN/Infinity成交额、零量及大幅价格变动。高位成交量保留
unsigned位模式，并警告有符号负值解释/溢出语义UNKNOWN；ETF可以真实超过2^31，
不能只因最高位为1就认定损坏。零量不能证明停牌，大幅变动不能证明除权或涨跌停。

代码规则是可审计的本地假设版本，不是权威证券主数据：股票/指数候选显示价÷100，
基金候选÷1000；未知或未确认尺度类型的显示OHLC为空，编码整数仍完整。上海B股
货币不假定为CNY。BJ老43/83/87代码保留AMBIGUOUS，920候选也不证明历史换码事件。
未按当前证券列表删除历史证券。`confirmed_a_share=false`、历史身份/退市UNKNOWN。

所有文件保留 `volume_unit=UNKNOWN`、`amount_unit=UNKNOWN`、
`price_scale_status=UNVERIFIED/UNKNOWN`、`adjustment_evidence_status=UNVERIFIED`。
`adjustment_status=RAW_UNADJUSTED`是禁止声称有复权的用途标签，并非本次独立证明
下载设置。amount/volume落在候选价格区间只是内部合理性检查，不能认证单位。

RAW基础列date,symbol,open,high,low,close,volume,amount旁保留tdx_*整数、保留字段、
来源路径/SHA、原行数、解析及单位状态、候选divisor、research_eligible=false。
**不调用会补出adj_*的canonicalize_bars；不添加adj_*、adj_factor或turnover假值。**

## 输出、原子发布与幂等

```text
results/diagnostics/tdx-local-data/<run_id>/
  inventory.csv, securities.csv, coverage.csv, anomalies.csv
  conversion_status.csv, verification_samples.csv
  quarantine_manifest.json, summary.md, manifest.json
data/research/staging/tdx/<market>/<symbol>/<identity>/
  data.parquet, receipt.json
```

quarantine是源身份/异常理由的逻辑隔离，绝不移动用户DAY。
按证券转换，内存不随全市场bar数累积；清单和异常随文件数增长。
staging根须为空或已有本模块标记，拒绝写入非空未标记缓存；源、报告、staging须互不重叠。
identity绑定源SHA/路径、分类、合同、解析状态与两个实现模块SHA；改代码保留新代。
临时独占目录中写Parquet及收据，fsync后重读、精确逐值比较并按dtype重建32字节
源记录，SHA完全相同才原子rename目录。无正式Provider注册。失败临时目录为
未引用orphan，不自动清理。重复运行验证已有收据、Parquet SHA和全数值，不重写
任何已有文件；损坏既有代明确失败，不自动覆盖。旧代和历史审计永远保留。

## 补充独立参考核验

`verification_samples.csv`实际选择SH股票600000、SZ股票000001、BJ920001、
指数000905、基金510300/159915、B股900901、可转债110075（存在且可解析时），
各取首/中/末记录。它是待核验清单，不是独立证据。典型实际日期：

| 证券 | 首日 | 中间日 | 末日 |
| --- | --- | --- | --- |
| 600000.SH / 000001.SZ / 000905.SH / 510300.SH / 159915.SZ | 2020-01-02 | 2023-05-23 | 2026-10-09 |
| 920001.BJ | 2022-12-27 | 2024-11-19 | 2026-10-09 |

在通达信**未复权**模式记录代码、日期、OHLC原显示精度、成交量及股/手/其他单位、
成交额及元/万元/亿元/其他货币单位、显示复权设置、来源和可复查证据。未显示的字段
继续UNKNOWN，不能从零量推断状态。另选已核验除权事件前后、停牌/复牌、ST涨跌停
和历史退市/换码例，独立提供状态/公司行为来源；不按大幅收益自己创造事件。

填写完整独立参考CSV（空模板不能当证据），列精确为：

```text
symbol,date,open,high,low,close,volume,amount,price_unit,volume_unit,amount_unit,adjustment,price_tolerance,volume_tolerance,amount_tolerance,source,evidence
```

price_unit用CNY/POINTS/USD/HKD；volume_unit用SHARES或LOTS_100_SHARES，其他用UNKNOWN；
amount_unit用CNY/TEN_THOUSAND_CNY/HUNDRED_MILLION_CNY，其他用UNKNOWN。
adjustment必须UNADJUSTED，容差须明确按界面/来源显示精度填写，不能为了匹配放宽。
source/evidence须指向真实参考；重复键、缺列/缺值、负容差和复权参考直接拒绝。

```powershell
.venv-py39\python.exe -X utf8 -m examples.research.verify_tdx_samples --report-dir results/diagnostics/tdx-local-data/<run_id> --reference <actual-reference.csv>
```

补充比较生成独立不可覆盖的新目录，绑定原审计清单、样本与参考SHA；对股票/指数
成交量1倍/100倍候选分别比较。数值匹配只限这一个证券日期；UNKNOWN单位不猜测，
不修改原报告或staging状态，不自动给全市场认证。若需要转换为正式Schema，须另行
审计证券类型、单位、调整、历史公司行为和输入范围，再按原门禁发布。

## 首轮实际审计（2026-10-11）

只读run：`20261011-tdx-audit-only-v1`，在新增重复源守卫前运行。
扫描39.356秒、读+SHA70.314秒、解析/质量/覆盖42.495秒，约283373记录/s；
进程峰值工作集168464384字节。此速度含质量/覆盖，不是纯struct解码速度。

发现9374 DAY：SH4721/SZ4303/BJ350；原始385339680字节；12041865条完整记录。
结构/数值可转换9371文件/12036951条记录；三个sh880006、sh880016、sh880036文件
存在152条OHLC关系异常，不修复。没有空文件、截断、重复或非法日期。

5572个A_SHARE_CANDIDATE、78个B股候选、1893个基金候选、104个指数候选、314个
可转债候选、1413个UNKNOWN；独立确认A股数为0/UNKNOWN，不等于没有A股。
SH/SZ首次2020-01-02，BJ首次2020-07-27；57个深市基金文件仅有2026-10-11周日
的范围外记录。因此observed_end可能超过请求末日，不裁剪原始字节掩盖异常。
已列出零量、高位成交量、大幅变化和研究日历缺口；缺口不直接解释为数据损坏。
所有文件中4520个覆盖本地参考的1211研究日+130预热日，其余缺口须结合身份/状态。
此数字含非股票，不能用于推断可研究的500成员覆盖。

## 全量RAW转换与工程验收

转换run：`20261011-tdx-raw-conversion-v1`。真实9371个文件全部成功，
12036951条记录进入独立RAW staging；3个失败文件明确拒绝，无额外转换失败。
返回1/partial反映源OHLC异常，不是偷偷跳过后报告全市场成功。

| 实测项目 | 数值 |
| --- | ---: |
| DAY总逻辑字节 | 385339680（367.489 MiB） |
| 已转换源逻辑字节 | 385182432 |
| Parquet逻辑字节 | 690756989（658.757 MiB） |
| 原始可转换字节 / Parquet字节 | 0.557624 |
| 扫描 | 34.641秒 |
| 源读取及SHA | 89.753秒 |
| 解码、质量及覆盖检查 | 48.550秒，248029记录/秒 |
| Parquet转换、重读、精确比较及源字节回验 | 886.426秒，13579记录/秒 |
| 含报告发布总计 | 1062.875秒 |
| 报告写入前测得的进程生命周期峰值工作集 | 279212032字节（266.277 MiB） |

**Parquet比原DAY更大**：增加原整数与候选显示价双份价格、来源/语义列及9371份
小文件的Schema/footer开销。这不是同列压缩实验，不能声称节省存储；原DAY已是
每记录固定32字节。内存值来自Windows GetProcessMemoryInfo，含解析/转换阶段，
采样在最后CSV报告写入前；计时为本机负载下墙钟时间，同时执行了安全研究测试集，
不是不同硬件/纯解码速度承诺。RAW表没有进入正式缓存。

本地1341行参考日历的1211研究日期+130预热：全部文件4520个完整；A股候选2968个
完整，5572候选的平均研究日期覆盖率91.8105%。这是文件覆盖，不是PIT成员键覆盖；
新上市、退市、停牌及源缺失原因仍UNKNOWN。完整2020—2026独立日历仍缺。

年度实际范围内记录见本run `summary.md`：2020/2021/2022/2023/2024/2025/2026
分别1304522、1509189、1691449、1849306、1962104、2074565、1650673条。
总计12041808条，另57条2026-10-11周日记录在配置范围外。
该年度表包含仅供诊断的失败文件可解析部分，不冒充已发布的合格行情。

两个可独立复核的来源层次须分开：24条实际跨市场/类型/历史长度样本经32字节
结构解码并保留数值；工程验收再使用标准库struct核对其编码整数、float32量额及
保留字段。它不能替代独立市场参考。另一份已取得的官方端点benchmark缓存，先经
原ParquetBarCache.load_snapshot(verify_hash=True)固定，再对000905.SH的2023-05-23
作跨源比较：四个OHLC候选值全部逐值一致；DAY量111104244×100等于缓存的
11110424400股；amount候选120628486144与缓存120628000000相差486144，零容差
比较不一致。来源表示精度可能不同，未自动放宽容差或修正源值。

补充比较见 `results/diagnostics/tdx-reference-checks/20261011-cached-benchmark/`，
输入及原缓存metadata/数据SHA见 `tdx-reference-inputs/20261011-cached-benchmark/`。
全程0网络，只证明这个指数日期的数值关系；所有股票及全文件单位/调整状态仍
UNKNOWN/UNVERIFIED，也不把指数成交量100倍套到股票或ETF。

Python 3.9.25定向42项解析通过；联合202项转换/Provider通过；含补充参考入口的
联合212项通过（其中TDX新增测试74项）。最后样本名单由不存在的113011更换为
实际110075，真实扫描验证其三个样本，没有变更解析/门禁。
安全完整研究测试 **2588 passed、2 deselected、88 warnings，592.57秒**；两个网络
测试未运行。警告来自既有Matplotlib/PyParsing及因子空分组参考/实现路径，0失败、
0错误。JUnit实际绑定以下文件：

```text
results/runs/tdx-parser-targeted-20261011.xml
results/runs/tdx-conversion-targeted-20261011.xml
results/runs/tdx-engineering-targeted-20261011.xml
results/runs/tdx-full-research-20261011.xml
```

本轮 `pip check` 无冲突，四个新增实现/CLI通过Python 3.9 py_compile，
新源码空白检查及git diff --check通过。测试使用人工字节fixture，仅证明工程；
真实覆盖和性能来自上述9374个用户DAY，不把两者混为真实市场独立验证。

正式 `build-dataset` 在禁止socket.connect的进程中真实复核，run为
`20261011T152407.782841Z-build-dataset-0e0b9a79`，返回1并在
`POINT-IN-TIME UNIVERSE REQUIRED: EFFECTIVE MEMBERSHIP SEMANTICS UNVERIFIED`
停止；网络尝试0，正式输出不变，`data/research/processed/dataset.parquet`不存在。

## 独立完整性复验与失败副本

`results/diagnostics/tdx-local-data-validation/20261011-acceptance/validation.json`
独立记录：9374个原文件在首轮审计、转换及最后重读中的SHA完全一致；16个诊断
产物SHA有效；9371份Parquet与各自收据/源SHA逐份一致。8个跨市场/类型的实际源
重新解析后均返回REUSED_VERIFIED，已有代未被重写；标准库struct独立抽样24条
记录的原日期、OHLC整数、float32成交额、无符号量及reserved全部一致。

三个失败文件的各52416字节只读副本位于同目录
`quarantine/sh/{sh880006,sh880016,sh880036}.day`，副本SHA与原文件一致，异常理由
绑定在validation.json。原run的quarantine_manifest为逻辑隔离，本补充验收另行
保存真实字节副本；未移动或覆盖原DAY/原报告。完整复验耗时155.581秒。

原转换清单SHA：`e30d5979e739b50b7145a1460204b6d6bb6f17d37d3aa043a008eaae10f65980`；
独立验收收据SHA：`280f7989d36283e8f8f4060a38bb28a97499504d5d1911d766105241937efbc1`。
两个解析/转换模块当前SHA仍与运行清单所绑定值完全一致。

执行脚本保留在上述验收目录，可用runpy检查其源码及命令。首次运行创建独占收据和
异常副本；再次完整验收应复制脚本到新诊断目录，不能覆盖旧证据。

```powershell
.venv-py39\python.exe -X utf8 -c "import runpy; runpy.run_path('results/diagnostics/tdx-local-data-validation/20261011-acceptance/verify_engineering.py', run_name='__main__')"
```

存储测量的早期GetCompressedFileSizeW结果在本机未压缩文件上等于逻辑长度，
不能将其当成含簇舍入的占用空间。因此另保留
`disk_allocation.json`，使用GetFileInformationByHandleEx(FileStandardInfo)的
AllocationSize测量真实文件数据分配，旧收据不修改。目录/MFT元数据不计入这项
文件占用口径；Parquet/完整staging及源逻辑字节分别计量，不能把收据算成行情行。

| 文件集合 | 逻辑字节 | 实际分配字节 |
| --- | ---: | ---: |
| 9374个原DAY | 385339680 | 398276480 |
| 9371个Parquet | 690756989 | 710148096 |
| 全部RAW staging（含9371收据和标记） | 707311416 | 748531808 |

分配测量215.057秒，原完整性收据SHA保持不变。这里的实际分配是本机文件系统
FileStandardInfo返回的文件数据AllocationSize，不含目录/MFT元数据。
`measure_disk_allocation.py`源码及不可变`disk_allocation.json`一并保留。
所有本轮真实审计、转换、参考比较、独立验收和存储测量均未访问外部网络。

## 修改与Git记录

本任务新增8文件、修改1文件：

| 文件 | 用途 |
| --- | --- |
| qbot/research/data/tdx.py | 安全发现、候选布局、分类及只读质量/覆盖审计 |
| qbot/research/data/tdx_staging.py | RAW不可变转换、回验、独占诊断报告 |
| examples/research/audit_tdx_local.py | 独立离线审计/转换CLI |
| examples/research/verify_tdx_samples.py | 后续真实独立参考的补充比较CLI |
| tests/research/test_tdx_day.py | 42项解析、质量与路径测试 |
| tests/research/test_tdx_staging.py | 23项转换、幂等、发布、边界及正式Schema拒绝测试 |
| tests/research/test_tdx_reference.py | 9项补充比较完整性测试 |
| docs/research/TDX_LOCAL_DATA.md | 中文技术报告与后续验收步骤 |
| docs/research/LOCAL_MARKET_DATA.md | 增加RAW staging边界说明链接 |

本任务新增Git提交：**无，变更留在工作区**，没有自动push、force-push、分支切换或
改写历史。审计/转换基线Git为`2759870329ec06929a118afc91f8609438226eed`，
运行时git_dirty=true；不能称为提交后干净运行。manifest同时绑定当时工作区及实际
两个模块SHA，源码文件未混入用户既有其他未提交工作。运行诊断/RAW属于Git忽略
产物，独立验收脚本和收据也保留在diagnostics，不进入任务提交。

## FactorLab接入仍需的证据

TDX只读解析/审计 → RAW staging → 独立单位、历史身份、状态、复权与公司行为核验
→ 显式生产18列 → 原LocalParquet导入/缓存generation → 原PIT/状态/来源门禁
→ 正式DatasetBuilder。还缺2021真实500成员基线、全部生效调样链、每日ST/停牌、
上市退市/换码、独立后复权OHLC与换手率、完整独立交易日历。
不通过放宽门槛或复制raw为adj解决，不宣称完成五年实证。

本轮没有自动push、force-push或改写Git历史；用户原有无关未提交文件保留。
