# 历史公司行为、复权与正式行情准入基础

2026-10-12，Python 3.9，**NO LIVE MONEY**。

本增量实现P0冻结和P1软件基础，并提供P2接入的拒绝门禁。
它没有把12036951条TDX RAW转换成正式后复权行情，没有认证完整历史身份、
状态或中证500PIT，没有生成正式五年数据集、模型实证或Forward信号。
价格复权不等于投资者总回报，也不等于原始价格上的执行收益。

## 已完成、未完成与依赖

| 优先级/阶段 | 实际状态 | 退出条件/依赖 |
| --- | --- | --- |
| P0-1 性能与TDX冻结 | 已完成；TDX独立提交46a163a，计数修订a72e5ba | 历史收据不改写；干净检出离线验收 |
| P0-2 来源合同 | 已实现字段、时间、单位、身份、算法与缺口合同 | 来源证据等级仍分别记录 |
| P1-1 软件基础 | 事件版本、存储、两种HFQ核、独立Golden、18列组装、资格复算与CLI已实现 | 人工fixture只证明软件 |
| P1-2 证券级真实复权 | 未通过 | 真实完整事件、历史锚点、单位、原始参考和来源算法 |
| P1-3 状态/PIT | 未通过 | 独立身份、逐日状态、实际生效成员与日历 |
| P2-1 正式数据 | 门禁已实现，真实准入未通过 | P1-2、P1-3及独立来源时间/覆盖复核 |
| P2-2 五年研究 | 未启动 | P2-1；跨权益事件的执行协议还需另行批准 |

不修改14因子、四模型、市场状态、Walk-Forward/Purge/Embargo、标签、
正式YAML、Schema、原cache/provenance、Builder、Forward、Legacy或LICENSE。
生产变更限定于Local Provider的v2证据绑定和CLI外围门禁。

## P0审计与标签修订

600000行源Parquet的SHA：
`15d66f7dd0a4b0a5fe736b988ea164d006b48601edafe8219ae4c14ac2121eb2`。

| 字段 | 非空 | 空值 |
| --- | ---: | ---: |
| EXCESS_RET5 | 597000 | 3000 |
| STOCK_FWD_RET5 | 597000 | 3000 |
| BENCHMARK_FWD_RET5 | 597000 | 3000 |
| entry_date | 599500 | 500 |
| exit_date | 597000 | 3000 |

收益缺失是同一批末尾6日×500行；entry/exit偏移为1/6个交易日。
股票与基准两个字段的空单元格相加为6000，不能称6000条未成熟标签；
没有证据确认原文字由重复计数产生。只修正文档，不修改真实标签计算。

性能源实现、24个Golden文件及历史验收来源的复核见
[FACTOR_PERFORMANCE_OPTIMIZATION.md](FACTOR_PERFORMANCE_OPTIMIZATION.md)。
13.6倍为原配对测量结论，本增量没有重测性能，不称全流程或空闲机器保证。
P0独立干净检出为a72e5ba：2559 passed、2 deselected、88 warnings，667.78秒。
原工作区另有29项未提交市场状态诊断测试，因此不能把两次测试计数混称。
当前三份TDX测试实际73项通过；旧历史报告的计数不用于本次新验收。

完整运行证据写入独占目录：
`results/diagnostics/market-data-foundation/implementation-20261012T103426Z-3e4705ca/`。
`initial-audit.json`绑定起始Git、49个冻结/用户文件SHA和标签计数；
每次JUnit及最终完整性收据使用新文件，不覆盖以前证据。

## 18列合同与RAW缺口

股票/benchmark表仍精确为：

```text
date,symbol,open,high,low,close,volume,amount,turnover,adj_factor,
raw_open,raw_high,raw_low,raw_close,adj_open,adj_high,adj_low,adj_close
```

| 项目 | 已有证据 | 未满足的正式要求 |
| --- | --- | --- |
| DAY结构、日期、编码量额、OHLC整数 | 9371份RAW及来源回验；9374份原DAY | 工程通过不能认证价格设置和金融身份 |
| OHLC候选缩放 | 三证券2026-10-09的12个显示值匹配 | 原价模式连续性、币种、全证券/历史范围 |
| volume/amount | 原uint32/float32精确保留，截图量级部分匹配 | 物理单位、范围与显示舍入认证 |
| raw_*副本 | 原价认证后可显式组装 | 禁止将候选显示价直接升级 |
| adj_* / adj_factor | 两种软件计算核 | 真实事件覆盖、锚点、算法与独立OHLC参考 |
| turnover | 严格显式输入 | 历史来源值或时点一致流通股分母 |
| 身份/上市/退市/换码 | 独立身份区间模块 | 实际A股主数据及身份关系 |
| ST/交易状态 | 复用原状态合同 | 逐日真实状态；不能由缺行或零量推断 |
| PIT/日历 | 原门禁保留，资格另外比较独立日历 | 起点500成员、完整实际生效链及独立日历 |

BJ仍仅诊断；身份模块只接受有显式A_SHARE类型的SH/SZ，不能由代码前缀认证。
已知停牌行保留空价格；供应商携带的前收盘价不能作为当日研究价格。
任何缺事件、缺因子、缺单位或缺状态都不能靠填1、填0、ffill/bfill通过。

## 来源比较和本轮真实观察

| 来源 | 证据等级与覆盖 | 修订/时点/退市 | 获取与协议兼容性 |
| --- | --- | --- | --- |
| TDX gbbq/gbbq.map | 本地文件存在，已归档字节；未解码 | 事件、退市覆盖与公告时间未知 | 单机文件成本小；只有经认证格式才开发解码，当前接口返回UNKNOWN |
| AKShare东方财富 | 600000.SH九行raw/hfq缓存可核验 | 非五年覆盖，缺历史vintage | 现有Provider合同；不能从收盘比例推所有OHLC |
| 新浪因子 | 单证券HTTP成功，29条观察原字节已归档 | 无公告时间、覆盖证明；1900哨兵独立保留 | 安全JSON解析，不执行SDK eval，不直接生成公司行为 |
| AKShare公司行为 | 文档及固定SDK确认存在 | 未取得完整事件表，比例单位须公告核对 | 分红接口不替代配股、拆合股和特殊事件 |
| BaoStock | 文档存在，历史登录曾失败，本轮未连接数据接口 | 方向说明冲突，无完整vintage证明 | 涨跌幅复权与TDX仿射可能不同；不套用文档中的未来因子回退 |
| 正式公告 | 规划阶段读到600000.SH现金分红佐证 | 本轮PDF直连TLS失败；未归档原PDF | 不关闭TLS校验；保留失败收据，不能声称取得全部事件 |
| Tushare | 文档存在，需要权限 | 实际覆盖和历史修订未知 | 当前文档因子权限2000积分起，未连接 |
| Wind/学校库 | 未连接、未授权或未交付 | 退市、因子、状态、vintage字段未知 | 索取数据字典与真实样本，不假设五年价格包含这些字段 |

官方接口依据：[AKShare](https://akshare.akfamily.xyz/data/stock/stock.html)、
[BaoStock行情](https://www.baostock.com/mainContent?file=stockKData.md)、
[BaoStock因子](https://www.baostock.com/mainContent?file=factorInfo.md)、
[Tushare](https://tushare.pro/document/2?doc_id=28)。
不同包装但同一上游来源不视为两份独立证据。文档声明的起止年份不能当作本机覆盖。

实际TDX候选归档仍`events=0`、`coverage=UNKNOWN`，不解释为无公司行为。
新浪响应SHA：`c39f33e58aff83268797c8f002b13660102d7c882f05e1dd22db465fd5e085f6`。
`real-source-comparison.json`只比较已存在九行缓存与该响应：2024-01-02
raw_open=6.63，原缓存adj_open=75.43；收盘比例11.4乘开盘得75.582，
新浪观察因子15.5459152080763乘开盘得103.06941782954587。
这是来源表示不可直接互换的实际例子，不是单位、锚点或算法认证。
TDX候选文件及新浪原字节已进入不可变证据代；未进入正式行情缓存。

## 数学合同、精度与特殊事件

设事件前有效参考收盘C、每旧股现金D、送股S、转增B、配股R、认购价K，
所有金额CNY、所有比例显式标准化为每旧股，M=1+S+B+R。
标准未取整事件参考价：`P_ref=(C-D+K*R)/M`。

* `SOURCE_AFFINE_HFQ_V1`：`H=a*P+b`；事件后
  `a_new=a_old*M`，`b_new=b_old+a_old*(D-K*R)`。
* `SOURCE_RATIO_HFQ_V1`：`F_new=F_old*C/P_ref`，`H=F*P`。
* 前复权的诊断数学表示为`Q_d=(H_d-b_T)/a_T`；生产仍拒绝qfq，未新增前复权生产接口。
* 18列的`adj_factor=adj_close/raw_close`仍只是收盘比例，不能当通用OHLC乘数。

事件核要求`STANDARD_CNY_PER_OLD_SHARE_V1`明确规则，不猜特殊规则。
送转需股份到账/可交易日；现金需派息日；配股需价格、资格、认购起止与可交易日。
拆分/合并需要显式股数倍数与方向。所有零项必须明确给出，缺失不转换为零。
登记日在有效日前。预案、取消和实施分开，事件修订有独立版本与可知时间。
同日事件必须有连续唯一sequence和经过证明的后续基数，否则拒绝。
跨日停牌内的多次特殊参考价、差异化分红或已取整/特别参考价不套标准简式；
无法满足该核时拒绝并等待新的来源规则。换码、合并重组、退市、实物等不当作普通价格事件。

固定过去锚点需原证据SHA及当时可知时间。TDX始于2020不证明所有上市前史，
不能随意设乘数1/加数0以冒充供应商上市锚点。原始量额不随价格复权调整。
Decimal精度50，输出float64，不提前按分取整。内部容差atol=rtol=1e-12。
外部只有明确认证nearest舍入时才允许半个price_quantum；UNKNOWN规则拒绝。
已公布参考价不等于标准未取整值时，也需新的明确规则，不能扩大容差接受。

## 信息时间与两类泄漏验证

每行价格必须提供自己日期的时区明确`signal_as_of`，不能用数据末日统一截止。
仅日期公告按上海当日日末上界处理，不能当作当天15:30前已知。
事件视图保留已知修订，计算核对每个交易日分别选择当时版本，并只应用已生效事件。
已知未来生效事件不调整过去。历史生效但初始信息在当时未知时明确拒绝。
晚到更正不会改已生成的过去行；拼接后的vintage序列被标记为不合格，
不能假装已经实现完整二维历史特征视图。今天事后重建标记HISTORICALLY_RECONSTRUCTED，
不能自动提升为CONTEMPORANEOUS。

晚到取消与改期也保留旧行并标记不合格；不能因取消状态或新的生效日期在请求
窗口之外就丢掉该修订。锚点不得早于证券上市，1900因子哨兵不能充当真实证券锚点。

A验收经过原Builder，对未来价及未来事件突变后，比较过去全部14个原始/处理因子、
市场状态、指数特征及固定FactorScore信号，要求精确相等。
B验收允许有意使用t+1至t+6的未来事实评价标签，断言它不进入过去特征。
训练数据仍必须满足原成熟、Purge/Embargo及真实可获知版本合同。

股票hfq比值减价格指数收益仍是冻结EXCESS_RET5，不称总回报超额收益。
原始开盘执行与hfq标签需要分别解释。执行账本尚无分红应收、送转股、配股与换股，
除权参考价也不能用普通前一raw_close替代；v2资格在事件存在时不授予执行资格。
本轮不修订这些协议，不启用Forward，不接入真实交易。

## 模块、发布与使用

新增模块都在原qbot.research内。`corporate_actions`负责原始来源、事件版本、覆盖与
不可变代；`adjustment`负责两种价格表示及独立参考；`universe/identity.py`负责身份；
`units.py`做经证据限定的单位转换；`assemble.py`生成显式18列；
`market_qualification.py`复算资格。Provider、cache、PIT、状态、Builder仍沿原管线消费。

```python
view = select_events(snapshot, effective_through="YYYY-MM-DD", knowledge_as_of="timestamp+08:00")
result = build_hfq(raw, view, method=method, anchor=anchor, signal_as_of=per_date_cutoffs)
validation = validate_adjustment(result, independent_reference, source_contract)
tables = assemble_market_data(raw, adjusted_by_identity, turnover, identity, unit_contracts,
                              source_version=version, signal_as_of=per_date_cutoffs,
                              benchmark=explicit_18_column_benchmark)
report = qualify_market_data(inputs, required_keys, calendar,
                            stocks=tables.stocks, benchmark=tables.benchmark)
manifest = publish_qualification(inputs, required_keys, calendar,
                                 stocks=tables.stocks, benchmark=tables.benchmark,
                                 output_root=new_evidence_root)
```

资格输入包括事件/锚点/参考计算recipe、单位、身份、RAW原字节、原始独立参考、
benchmark原来源、逐日状态、上市日期、成员和独立日历。所有原字节与表复制为自包含
证据包；复用不重写原代。消费者重新运行检查并比较报告，不能只相信一个PASS字段。
raw工程、调整、状态、PIT和正式准入五阶段分开保存。所有来源字段任一合成标记
都会阻止正式准入。真实资料另需独立来源时间/覆盖复核收据，不提供verified布尔开关。

真实来源复核的精确字段见`market_qualification._reviews`：角色、reviewer、原始SHA、
upstream_origin、时间/覆盖/生效依据、历史类型与覆盖范围。角色包括RAW、IDENTITY、
UNITS、ADJUSTMENT、REFERENCE、BENCHMARK、CALENDAR、STATUS、PIT。
这些是可检查的复核判断，不能认证reviewer身份，不能仅靠本地SHA证明历史时间。
来源原文、外部归档或不可改写摘要仍是必要证据；不把填写文本等同第三方认证。

```powershell
# 输出原字节与UNKNOWN覆盖，不解码、认证或发布价格。
.venv-py39\python.exe -B -X utf8 -m examples.research.diagnose_corporate_actions --source tdx-candidates --security 600000.SH --start 2020-01-02 --end 2026-09-11 --input <hq_cache> --output-root <new-evidence-root>
# 明确的单证券网络诊断。返回1表示留存了未合格观察，不是正式成功。
.venv-py39\python.exe -B -X utf8 -m examples.research.diagnose_corporate_actions --source sina-factors --security sh600000 --start 2020-01-02 --end 2026-09-11 --output-root <new-evidence-root>
# 只有完整资格包才可走v2；合成包读取/发布仅用于软件验收，正式Builder仍拒绝。
.venv-py39\python.exe -B -X utf8 -m qbot.research.cli import-market-data --config <local-config> --stocks <stocks.parquet> --benchmark <benchmark.parquet> --source <declared-source> --source-version <qualified-version> --qualification-manifest <qualification/manifest.json>
```

旧Local v1读取保持，但不提供新的历史认证；明确TDX来源的v1声明不能升级RAW。
v2把证据清单SHA、报告、计算实现SHA纳入bundle版本，源码或证据修订要产生新代。
Provider固定同一代，CLI在原四值行情快照上保留固定Provider，状态和回测不另读混合代。
新bundle来源不同，旧cache拒绝混合，原bar_data_version和dataset_manifest schema4继续绑定。
DatasetBuilder及标签逻辑没有修改。哈希同时重写全套数据仍不是本机日志能自证的攻击范围。

## 验收边界与后续工作

独立Golden位于`tests/research/fixtures/adjustment_golden/`，有字节SHA与固定容差，
期望值来自人工冻结有理数计算，明确synthetic_only，不导入生产引擎生成期望。
最终新增定向验收71 passed、13条既有第三方警告，43.04秒；另有311项Local/CLI/
provenance联合开发回归通过。开发中间工作区全量2656项通过，但期间继续修复了
取消/改期时间边界；该XML保留为中间记录，不冒充最终代码的干净验收。
最终提交`8cbc2bef173a187463578bb61712c798d2bd08f9`在独立干净检出中完成
2630项离线测试，0失败、0错误、0跳过；其中71项为新增基础测试。
JUnit记录的suite耗时703.245秒；两项真实Provider网络测试由原`pytest.ini`排除，
本验收不据此声明真实行情验证通过。验收观察和结束时检出均干净，192份研究/测试
Python文件在运行中和结束后SHA一致；原工作区的对应源码只有50份CRLF/LF差异，
归一化后内容全部一致。最初逐字节镜像断言因CLI行尾差异没有生成起始收据，
因此`release-clean-observed.json`明确记作运行期间观察，不冒充运行开始记录。

追加验收收据为
[`release-verification.json`](../../results/diagnostics/market-data-foundation/implementation-20261012T103426Z-3e4705ca/release-verification.json)，
SHA为`e116db42ce31e72183b042dcb65b260add3be959986315fbabf1fbb19e51b864`。
最终JUnit为同目录`release-clean-research.xml`，SHA为
`554d948453415768dfdc718e9bea78410c997c37af353ba5edf3718c90ea63c6`。
收据绑定测试源码、49份冻结/用户文件、原标签集及manifest、TDX原清单、旧性能收据、
24份因子Golden及新增合成Golden，并复核Python 3.9语法与`pip check`。
9374份DAY和9371份RAW/转换收据的完整逐文件核验记录保留在
`precommit-integrity.json`；本次只追加新验收，不重写旧记录。
软件覆盖无事件、现金、连续事件、送转、配股、拆合股、OHLC一致性、分段锚点、
停牌、换码、退市边界、信息时间、未来修订、幂等、篡改、发布失败保留旧代及来源修订。
正式缺资料及合成v2都必须拒绝。真实样本不齐时不把这些测试称真实市场验收。

首批候选仍冻结为600000.SH九行已有参考及2025-07-16现金事件，000001.SZ用于
深市和多事件补证，920799.BJ仅诊断。后续特殊真实事件按类型/有效日/身份排序，
在看误差之前冻结首个资料齐全者，不按拟合结果选择样本。

实际正式build run `20261012T112048.346829Z-build-dataset-34c5aa27`，
返回1，在`POINT-IN-TIME UNIVERSE REQUIRED: EFFECTIVE MEMBERSHIP SEMANTICS UNVERIFIED`
停止，禁止网络的进程中连接尝试0，正式dataset仍不存在。

未完成的退出条件：权威起点500成员与实际生效链、完整身份/退市/换码、每日ST/停复牌、
单位与历史换手、事件前史和锚点、独立OHLC参考与来源舍入、完整日历、历史vintage。
GBBQ布局/历史未认证，官方PDF直连失败，真实算法和单位认证均未通过。
配股资金、税、分红再投资、权益到账、涨跌停参考及执行账本另需协议审批。
本轮只完成安全可实施基础和拒绝门禁；不得据此运行正式五年结果或真实Forward。
