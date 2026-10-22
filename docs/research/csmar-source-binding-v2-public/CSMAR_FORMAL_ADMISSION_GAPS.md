Public derivative of historical report. Original SHA256: a966542db30bd024d343a561a960fd9df793b41c2615dec46ce7c7b4e416c16e. Local references are redacted; historical conclusions are retained. This is not the original file or current execution evidence.

# CSMAR正式准入缺口与验收问题

2026-10-21。NO LIVE MONEY。

软件状态为PARTIAL：本轮交付可运行的原件解析、局部来源绑定、候选收据、既有资格引擎接入及诊断桥；没有完成所有金融角色解析和整库运营导入。金融事实总体UNKNOWN；技术核验仅在重放报告列出的文件、成员和范围内为VERIFIED_FOR_DECLARED_SCOPE。正式研究为FORMAL_ADMISSION_BLOCKED。

1. 当前CSMAR能否确定性重放：声明范围内通过固定原件ZIP/XLSX/DES/代码/依赖及选区独立重放；真实结果以CSMAR_REPLAY_TEST_REPORT为准，不外推全部1.06亿行。
2. ZIP与Parquet追溯：RAW、native和lineage三表均和原件重放比较；任意规范行能追溯到原始行。尚未声称全库转换、分卷齐全或后复权生产资格。
3. 字段单位合同：日线及000905指数窄投影已建立；其他表保留原生观察；不明确字段不得规范投影。
4. 已绑定角色：只有通过CSMAR真实原件重放的RAW技术角色。单位转换局部可验证，生产UNITS尚未解除。
5. 未绑定角色：PIT、STATUS、CALENDAR、IDENTITY、UNITS、ADJUSTMENT、REFERENCE、BENCHMARK、TURNOVER、LISTINGS、ANCHOR，分别需要独立金融事实、时间版本或额外解析器。
6. SOURCE_BINDING实际进展：不再只支持TDX原件；新增CSMAR代码拥有的RAW解析合同、大ZIP外部引用和同句柄重算。整体SOURCE_BINDING保持INCOMPLETE。
7. PIT为何不能自动通过：既有审计显示2021-09-13原生499与反向候选500在过渡处冲突，缺权威完整基线、临时/条件/更正链、实际成员边界和历史可得版本。供应商调样、当前成员或自行套动作生成的名单不能补齐。
8. ADJUSTMENT缺口：原生因子有数值不等于完整事件账本；还缺实施/更正及前史、稳定身份、可知时间、合格历史锚点、供应商算法/精度、独立HFQ四价及vintage。不能从累计因子默认填1或原价复制得到资格。
9. 部分v2材料：使用现有QualificationInputs/SourceArtifact和publish_qualification在私有隔离区生成明确INCOMPLETE包；不能作为完整真实v2研究数据发布。候选独立格式也明确BLOCKED，现有loader拒绝假冒。
10. Provider消费：已有完整18列、显式调整观察的调用方可通过诊断桥复用LocalParquetProvider，raw_*须与原件重放一致；正式入口继续因缺合格v2拒绝。原价/因子输入本身不足以填满股票18列，真实直接Provider试点保持缺口，不填造调整或换手率。
11. 金融引擎fail-closed：_unbound_real_roles未改，assert_formal_market_admission未改，Provider不能签发权限，synthetic/手写PASS/手写formal_admission不能成为证据。
12. 软件回归：见重放及负例报告的实际JUnit；广义回归实际触发旧冻结/历史发布保全拒绝，新market_qualification.py尚未登记为独立批准的代码版本。CSMAR_SOURCE_CHANGE_REVIEW.json仅是待审提案，不能自称批准；旧测试、历史收据及控制pin保持原样。未执行项不得推断通过，远端最终HEAD检查未执行，因为本任务不推送。
13. 性能瓶颈：每次重放必须完整hash ZIP及扫描所选sheet，受XML单线程解析与磁盘读取影响；选区和临时空间受硬上限限制，整库调度/缓存尚需后续设计，见性能报告。
14. 是否改变FL架构：不需要改变18列、研究流程或金融门禁；继续使用现有Provider和资格引擎。完整股票投影需要额外金融材料及合格复权/换手率输入，不是改Schema来填洞。
15. 下一轮最小任务：先独立评审本轮RAW代码、精确新旧Git blob/哈希、差异及拒绝证据，单独审定当前安全版本登记与历史保全兼容方式，恢复发布检查；不能重写旧收据或给当前字节自行签发例外。随后按一个受限证券范围补历史稳定身份/状态知识时间、单位证据、真实事件和独立锚点，分别实现角色解析。PIT优先取得2021起点/13420过渡及13888独立前后完整有效名单和版本，不重下所有价格。

没有真实下单、资金使用、真实数据上的因子发现或模型训练。现有readiness验收中的训练仅使用合成夹具。代码及提案可以送独立评审，但目前不能宣称CI全绿或满足合并条件；本轮仅本地分支交付，不推送、不创建PR、不合并。
