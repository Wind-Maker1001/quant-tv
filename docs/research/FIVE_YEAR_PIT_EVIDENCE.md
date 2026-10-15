# 五年历史股票池、身份与证券状态证据审计

审计日：2026-10-15（Asia/Shanghai）。研究窗口：2021-09-13 至 2026-09-11。
本报告新增来源核验，不重新采集指数成分、不发布证券级行情或公告原文附件，不改变正式门禁。
当前结论为 **PIT_UNVERIFIED / FORMAL_ADMISSION_BLOCKED**。

十次定期调样的正文、附件及明确的收盘后安排已经取得；完整起点500成员、全部临时调整链、
实际日级成员区间和完整历史状态链仍未取得。可核验公告事件与可正式消费的历史股票池是不同交付物。
本审计认证的完整500成员基线、逐日成员区间和完整ST/停复牌区间均为0；这表示尚未认证，不能解读为历史上没有这些事件。

## 本次可复核产物

- [pit-events.json](evidence/five-year-data-feasibility-v1/pit-events.json)：14个来源事件的发布日期、明确安排、条件条款、实际生效未知项、附件哈希及来源；其中10个为研究期内定期事件。
- [pit-gaps.json](evidence/five-year-data-feasibility-v1/pit-gaps.json)：目录缺口、BaoStock语义、独立身份事件和证券状态缺口。
- [pit-source-index.json](evidence/five-year-data-feasibility-v1/pit-source-index.json)：223份本地原输入、独立快照、收据及派生审计文件的字节复核索引；223不是供应商原响应数量。

原文、PDF、图片、失败收据和工具解析返回只保存在忽略目录
`results/diagnostics/five-year-data-feasibility-v1/pit-source-audit/`。公开JSON仅含链接、日期、哈希、统计和事件级身份事实。
旧档案没有重命名、升级或重写，草稿元数据也分代保留。

## 五种日期分别记录

| 字段 | 本报告含义 | 不能替代的内容 |
| --- | --- | --- |
| 公告发布日期 | 发行主体当前正文明确给出的日期 | 不等于交易时段成员变化日；附件目录日期不自动作为发布日期 |
| 计划/明示生效安排 | 原文的“某日收盘后”“自某日起”或条件条款 | 不自动平移成下一交易日实际成员 |
| 实际生效日期 | 对应目标成员/状态的实际生效事实，须有独立证据 | 不能仅从日历或供应商查询成功推定 |
| 接口更新日期 | 如BaoStock的`updateDate` | 不等于公告、上市、退市或指数调整生效日期 |
| 本机获取日期 | 具体响应/附件被本机取得的UTC时刻 | 不证明当前字节在历史发布日期已公开 |

另外单列附件`createAt`、HTTP `Last-Modified`、文件URL目录日和发行人签署日。
公告接口没有提供一个可认证的“接口更新日”，因此该字段保持null。
所有14个指数事件的`actual_effective_member_date`仍为null，没有把星期五收盘后安排填成星期五开盘成员。

## 定期事件：明确安排可查，逐日成员仍未认证

下表日期直接复读严格本地缓存/浏览器容器，经既有`notice_review`解析器取得。
“50/50”是该次调入/调出候选事件数，十次合计1000条变更事件，不能当作完整500成员基线。

| 官方公告 | 发布日 | 正文明示收盘后日期 | 候选调入/调出 | 已有独立检查范围 |
| --- | --- | --- | --- | --- |
| [13888](https://www.csindex.com.cn/#/about/newsDetail?id=13888) | 2021-11-26 | 2021-12-10 | 50/50 | HTML与XLSX动作/代码/名称逐项一致 |
| [14223](https://www.csindex.com.cn/#/about/newsDetail?id=14223) | 2022-05-27 | 2022-06-10 | 50/50 | HTML与XLSX逐项一致 |
| [14497](https://www.csindex.com.cn/#/about/newsDetail?id=14497) | 2022-11-25 | 2022-12-09 | 50/50 | HTML与XLSX逐项一致 |
| [14796](https://www.csindex.com.cn/#/about/newsDetail?id=14796) | 2023-05-26 | 2023-06-09 | 50/50 | pypdf/pdfplumber独立比较，目标页视觉核验 |
| [15044](https://www.csindex.com.cn/#/about/newsDetail?id=15044) | 2023-11-24 | 2023-12-08 | 50/50 | pypdf/pdfplumber独立比较，目标页视觉核验 |
| [15267](https://www.csindex.com.cn/#/about/newsDetail?id=15267) | 2024-05-31 | 2024-06-14 | 50/50 | 既有PDF候选与正文计数相符，未完成全部逐行视觉检查 |
| [15471](https://www.csindex.com.cn/#/about/newsDetail?id=15471) | 2024-11-29 | 2024-12-13 | 50/50 | 同上 |
| [15690](https://www.csindex.com.cn/#/about/newsDetail?id=15690) | 2025-05-30 | 2025-06-13 | 50/50 | 同上 |
| [3006000](https://www.csindex.com.cn/#/about/newsDetail?id=3006000) | 2025-11-28 | 2025-12-12 | 50/50 | 同上 |
| [3006137](https://www.csindex.com.cn/#/about/newsDetail?id=3006137) | 2026-05-29 | 2026-06-12 | 50/50 | 既有跨页候选；目标表前两页视觉检查，非全部逐行视觉认证 |

本次重新绑定全部10份原附件的真实字节哈希和原获取收据，0次新的CSI正文HTTP。
2023年的两份PDF已在既有后续工作中补齐，不能沿用旧报告中的“尚缺这两份附件”结论。
其当前字节仍没有历史vintage保证；例如早期附件HTTP修改日在2024年，晚于正文历史发布日期。
既有检查范围见[官方归档](OFFICIAL_SOURCE_ARCHIVE.md)和[2023 PDF复核](PDF_NOTICE_REVIEW.md)。

## 临时事件与研究起点缺口

| 来源 | 已证实的来源事实 | 仍未证实 |
| --- | --- | --- |
| [13716，2021-09-08](https://www.csindex.com.cn/#/about/newsDetail?id=13716) | 明示2021-09-10收盘后，当前XLSX中目标指数有一对调整 | 其余499成员、当前附件在9月8日是否已经公开；附件`createAt`为9月23日 |
| [13420，2021-08-30](https://www.csindex.com.cn/#/about/newsDetail?id=13420) | 明示自中国能建上市日起；原表新证券代码为`-`；后续独立披露佐证2021-09-28上市 | 2021-09-13起点完整500基线、葛洲坝退市至新股上市的指数过渡期语义；没有回填`-` |
| [3006027，2026-01-06](https://www.csindex.com.cn/#/about/newsDetail?id=3006027) | 明示2026-01-09收盘后，目标指数一对候选调整 | 完整成员链及实际日级成员日期 |
| [3006227，2026-09-09](https://www.csindex.com.cn/#/about/newsDetail?id=3006227) | 当前附件目标指数一对变更，原文条件是相关证券退市日起 | 不能用9月9日或附件10月9日代替实际生效日；当前附件在研究截止后修改，缺历史vintage |

3006227正文没有“中证500”关键词，但附件包含目标指数。因此正文关键词未命中、标题泛化或未发现附件，
均不能作为“没有中证500变更”的阴性证据。不能以当前指数、ETF持仓、申赎篮子或499快照再补一只股票建立起点。
中国能建的既有独立来源及其局限见[条件事件证据](CONDITIONAL_EVENT_EVIDENCE.md)，泛标题反例见[工作簿复核](WORKBOOK_NOTICE_REVIEW.md)。

## 当前目录覆盖与BaoStock资格

本轮实际再次执行原有离线来源覆盖入口，生成独立run
`20261014T162105.566249Z-audit-official-coverage-9fdc020f`，返回码1、manifest状态`partial`。
当前目录726条，发布日范围2021-01-01至2026-09-11共246条，已绑定78份正文，168份未知。
本轮0 HTTP、54次经校验缓存读取；86份输入与快照、4份审计输出另重新核验字节哈希。
54个附件引用的内容并非由该覆盖审计逐一审查；独立文件检查不改变这一范围。
研究起点仍为2021-09-13，目录向前扩到1月是为寻找起点证据。

```powershell
.venv-py39\python.exe -X utf8 -m examples.research.audit_official_coverage --config configs/research/csi500_5y.yaml --archive-root data/research/diagnostics/official-notices/20261010-csi-rebalance --browser-directories data/research/diagnostics/official-browser-notices/20261010 data/research/diagnostics/official-browser-notices/20261010-remaining
```

旧403响应和停止收据保留。本轮没有重开已拒绝的CSI正文流程、变换身份/代理或以新会话继续访问受限内容。
“78/246”只描述这份当前目录的发布日窗口，既不是完整历史调样目录证明，也不是可自动重建逐日股票池的覆盖率。

[BaoStock官方接口说明](https://www.baostock.com/mainContent?file=pythonAPI.md#query_zz500_stocks)
本次工具读取仍明确每周一更新，`date`是查询日、`updateDate`是更新日期，未承诺实际日级调样生效语义。
工具命中2026-10-13缓存的事实保留，未包装成发布方当日原始字节。
既有独立匿名0.9.4探针在研究起点返回499、终点500，终点`updateDate=2026-09-07`；
本轮没有重复调用同一499响应，也没有放宽500门槛。接口错误码0、500行和日期匹配都不能替代日级PIT认证。

## 冻结试点的身份与状态解释

本次针对冻结试点定向取得原交易所公告，不根据收益或RankIC改变样本。
冻结清单中的上市年份stratum原为未核验假设；**601059应解释为2023年上市，001289为2022年上市**。
保留原冻结样本及其哈希，在此记录核验差异，不能修改清单追认原标签正确。

| 证券/事件 | 新取得官方证据 | 证据等级和日期限制 |
| --- | --- | --- |
| 001289龙源电力上市 | [深交所2022-01-20原公告](https://www.szse.cn/disclosure/notice/company/t20220120_590746.html)明示2022-01-24；[1月24日上市成功报道](https://www.szse.cn/aboutus/trends/news/t20220124_590933.html)独立确认同日实现 | 两份本机原HTML、SHA和收据；可解释上市前缺失。不能自动拼接被吸收的000780历史价格 |
| 601059信达证券上市 | [上交所2023-01-31原公告](https://www.sse.com.cn/disclosure/announcement/listing/ipo/c/c_20230131_88217306.shtml)明示2023-02-01上市交易 | 原HTML成功；宣布上市日已核验，本报告未据此认证完整身份和逐日状态链 |
| 000961中南建设终止上市 | [深交所2024-06-24决定](https://www.szse.cn/disclosure/notice/company/t20240624_607846.html)及[发行人摘牌PDF](https://disc.static.szse.cn/disc/disk03/finalpage/2024-07-09/db94667a-0122-48f5-83e7-c70e0c62523f.PDF)明确摘牌2024-07-11 | 原HTML/PDF均成功；PDF第1页实际视觉检查。PDF署名为7月10日，URL目录是7月9日，独立发布日期未知；不能把URL日冒充发布日期。原文宣布的摘牌日与独立事后实际成员/状态证明分别记录 |
| 600112天成终止上市 | [上交所托管发行人PDF](http://static.sse.com.cn/disclosure/listedinfo/announcement/c/new/2024-08-09/600112_20240809_JOQX.pdf)的工具解析文本明示8月8日决定、8月15日摘牌 | 本机原链接未完成合格PDF归档，独立失败收据为`READ_FAILED/ValueError`，响应未保留，不能进一步断定原因；只有工具解析表示，**publisher原字节SHA=null**。原文签署8月8日，URL目录8月9日，认证发布日期未知 |
| 300114变更302132 | [深交所托管发行人实施PDF](https://disc.static.szse.cn/disc/disk03/finalpage/2025-02-15/cedb693a-f5ee-4463-9682-ea33d406b569.PDF)明示2025-02-17开市变更 | 原PDF成功，第1页视觉检查；签署2月14日、URL目录2月15日，认证发布日期未知；禁止把新代码反向用于全部历史 |
| 601059研究期后的退市安排 | [上交所2026-10-12公告](https://www.sse.com.cn/disclosure/announcement/listing/stock/c/c_20261012_10834561.shtml)决定2026-10-19起终止 | 原HTML成功。10月19日晚于审计日10月15日，`actual=null`；不能变成研究期9月9日的实际替换事件 |

此次8次有限受控GET中7份原响应成功，1次失败，无凭证、不修改代理、不重试失败URL。
本机获取时间为UTC 2026-10-14 16:18:56至16:18:59附近，对应上海2026-10-15凌晨。
每份确切时刻、HTTP头、响应字节SHA和收据SHA在`pit-source-index.json`中保留。
受控GET数不代表已观测所有底层重定向/代理请求数量；后者unknown。

BaoStock日线可提供`tradestatus`和`isST`，官方定义分别为1正常交易/0停牌和1是ST/0否。
但完整试点状态链与独立交易所复核尚未认证；不能由零成交、无行情或股票简称猜测ST/停牌。
官方还说明停牌日OHLC会填前收盘、量额为0，因此供应商返回有价格不代表当日存在成交行情；
后续接入须保留原响应与停牌标记，并按FactorLab缺失规则处理，不补造交易价格。
本轮不将这些字段宣称为正式金融数据资格，不从最新上市表倒推全部历史身份。

## 可用范围与下一阶段

这组证据足以支持带明确限制的来源覆盖分析、冻结样本缺失解释和长窗口探索性数据接入审查。
它不能支持宣称“历史中证500正式五年回测”、无幸存者偏差或真实Forward检验。
本轮没有改动因子、39候选表达式、方向、参数、旧统计结果、Golden、PIT/HFQ或交易门禁。
既有2025至2026年开发样本仍不独立；新取得2021至2025年只可称跨周期回溯复核，不能因日期早而称前瞻测试。

下一阶段优先补完整基线、全部临时/条件链与历史状态资格，取得可授权核验的来源和历史版本证据；
并行扩大冻结样本的行情覆盖与失败收据。在相应资格改善前，可开展有明确便利样本偏差说明的探索性研究，
不把便利样本升级为历史中证500。冻结因子历史复核的时间划分和开发用途须事先登记，正式最终测试不参与开发决策。
本报告没有建立另一套缓存/Schema，也没有申请付费接口、公开原供应商数据或触达实盘资金。
