# 中证指数官方调样来源归档（2026-10-10）

## 本次进展与严格边界

已经实现独立的 `universe/official_sources.py` 与可运行示例
`examples/research/collect_official_notices.py`。它们从中证指数公开网页实际使用的
公告接口读取目录、正文和附件，保存原始字节、获取时刻、请求条件和 SHA-256。
它们不是 `PointInTimeUniverseProvider`，不生成成员、不自动推断生效日期，也没有
修改 BaoStock 的正式数据消费门禁。

用户没有可供导入的外部历史文件。本次开始取得可独立复查的官方证据，但仍没有
研究起点的权威500只成员基线、完整定期/临时调整链或逐日 ST/停牌状态。因此正式
dataset、真实横截面 RankIC、五年四模型实证与真实 Forward 仍未完成。

## 实际公开接口与查询范围

Firecrawl 在官方网页的实际网络请求中确认下列端点，本机随后直接读取成功：

- [新闻与公告目录](https://www.csindex.com.cn/#/about/newsCenter?typelist=announcement&related_topics=index_rebalance)。
- 目录：`POST https://www.csindex.com.cn/csindex-home/announcement/queryAnnouncementByVo`。
- 正文：`GET https://www.csindex.com.cn/csindex-home/announcement/queryAnnouncementById?id=13716`。

这是观察到的公开网站实现，不是供应商承诺长期稳定的正式 API。归档使用合同版本
`csindex-public-announcements-observed-20261010-v1`；结构、分页或总量变化时明确
失败，不猜字段、不跳缺页。

完整查询条件为：`lang=cn`、空 `searchInput`、`indexList=[csi_index]`、
`relatedTopics=[index_rebalance]`、`typeList=[announcement]`，每页100条。
当次得到726条、8页，逐条 ID 唯一。发布日窗口2021-01-01至2026-09-11内有246条。
2021年初的扩展窗口用于寻找起点前的调整证据，不改变正式研究起点。

“该查询8页完整”只表示当前网站目录响应的分页完整，不能证明网站历史记录无遗漏，
更不能证明中证500有效成员链完整。没有按标题只筛“中证500”来宣称覆盖全部临时调整。
正文读取覆盖所选发布日窗口；默认附件下载仅选择正文/标题实际提到“中证500”的
公告，其余附件明确为 `NOT_SELECTED`。仅在附件里出现中证500的公告可能漏选，
后续需要扩大附件核验，不能用这一选择规则直接建正式 PIT。

## 已实际核对的两份 XLSX

### 研究起点附近的临时调整

[官方公告13716](https://www.csindex.com.cn/#/about/newsDetail?id=13716) 发布于
2021-09-08，正文明确调整在2021-09-10收盘后生效。
[实际附件](https://oss-ch.csindex.com.cn/notice/20210923083520-%E8%B0%83%E6%95%B4%E5%90%8D%E5%8D%95.xlsx)
的两张表中，按精确指数代码 `000905` 核对：

| 原始工作表/单元格 | 中证500变更 |
| --- | --- |
| 调入，A6:D6 | 600297，广汇汽车 |
| 调出，A10:D10 | 600260，ST凯乐 |

电子表格技能要求按原始表头和真实标识符核验；使用独立的 bundled Artifact Tool
只读导入，保留六位代码的前导零，没有编辑或另存官方工作簿。证券代码规范化后为
`600297.SH` 与 `600260.SH`。这给出了研究起点前一交易日收盘后的一个真实边界，
但没有提供其余499只成员。

附件 SHA-256：

    9cce0059324cb7c876fb067c2655649e216a52302cf9bc22470135567dfcab35

网页当前附件路径/`createAt` 为2021-09-23，晚于公告日期。不能据此声称当前下载的
这些附件字节在9月8日已经公开，获取时刻也不是第三方当时发布证明。历史生效事实、
公告日期、附件上传日期和本次抓取日期分别保留。

### 2026年临时调整

[官方公告3006027](https://www.csindex.com.cn/#/about/newsDetail?id=3006027) 发布于
2026-01-06，正文明确2026-01-09收盘后生效。
[附件](https://oss-ch.csindex.com.cn/notice/20260106171931-%E6%8C%87%E6%95%B0%E6%A0%B7%E6%9C%AC%E8%B0%83%E6%95%B4%E5%90%8D%E5%8D%95.xlsx)
已只读核对：两张表的 A3:D3 对应中证500，调出600079（ST人福）、调入688037（芯源微）。
SHA-256 为 `49371333c7c39c2c9be21707f98b39d5664870ad3a2d32c8779d015ee3019f61`。
公告日不等于成员有效日，不使用周更新日期替代。

另一份已读取的 [2026-09-09公告](https://www.csindex.com.cn/#/about/newsDetail?id=3006227)
以相关证券实际退市日为条件，不给出可直接采用的固定生效日。这类条件必须另查
交易所生效证据及实际附件，不能默认公告当天就调整，也不能排除它一定不影响中证500。

## 实际运行、失败与校验

已执行：

```text
.venv-py39\python.exe -m examples.research.collect_official_notices --notice-ids 13716 --archive-root data/research/diagnostics/official-notices/20261010-csi-rebalance --max-retries 1 --timeout-seconds 10
.venv-py39\python.exe -m examples.research.collect_official_notices --archive-root data/research/diagnostics/official-notices/20261010-csi-rebalance --max-retries 1 --timeout-seconds 10
.venv-py39\python.exe -m examples.research.collect_official_notices --notice-ids 13716 3006027 --archive-root data/research/diagnostics/official-notices/20261010-csi-rebalance --cache-only
```

- 单公告首轮：`20261010T090903.528726Z-collect-official-notices-27db3240`，成功。
- 全窗口首轮因中文 URL 未编码产生 `UnicodeEncodeError`；后续已修复并增加精确
  编码/避免二次编码的测试。失败 run `20261010T091015.846840Z-collect-official-notices-2e203d26`
  有明确终止状态恢复说明，未捕获的真实结束时刻仍为 null，不补造时间或成功结果。
- 全窗口重跑 `20261010T091108.688290Z-collect-official-notices-7a4e2538`：
  **partial**，46条正文、7份附件（2 XLSX、5 PDF），200条正文读取失败（HTTP 403）。
  8份目录响应、46份正文和7份附件共61份原始对象的 SHA-256 已独立复核全部一致。
  初始时 PDF 仅归档，随后进行了下节的跨页候选提取；不能说已全量独立核验。
- 该批量失败暴露站点拒绝后仍逐公告请求的问题。当前代码已改为首次401/403后
  停止本批所有后续 HTTP 读取；只允许继续读已经验证的缓存，未请求项明确标记
  `SKIPPED_AFTER_SITE_DENIAL`。该规则有单测，不把旧批量的200次失败说成新规则的结果。
  不更换代理、IP、身份、cookies，不要求账号或 key，也不绕过访问拒绝。
- 两份公告缓存复跑 `20261010T091607.165739Z-collect-official-notices-640da045`：
  成功，**0 HTTP请求、12次已校验缓存读取**，2条正文及2份附件。这是显式子集成功，
  不冒充246条全部成功。

每个 run 生成 `catalogue.json`、`notices.json`、`source_evidence.json` 及运行 manifest；
成功/失败/未选择分别记录，生成文件也绑定 SHA-256。原始字节放在忽略的
`data/research/diagnostics/official-notices/`，报告放在 `results/diagnostics/official-notices/`。
没有把官方大数据或原始附件提交进 Git。

## PDF 跨页候选核对（不是完整股票池）

PDF 技能引导先读取标题、表格边界并渲染实际页面。bundled pypdf/pdfplumber 对五份
PDF 的全部文本页只读提取；2026-05-29附件第1、2页另用 Poppler 渲染并实际查看。
其第1页中证500表只有14条，第2页延续36条，后面单列“备选名单”；按关键词只抓
标题页会缺记录，把备选名单加进调入又会错误增加成员。

候选提取只使用“中证500指数样本调整名单”至下一指数调整标题之间的六位代码对，
跨页保持方向，排除备选名单，并检查两个方向各自去重、数量相等及公告正文声明的
更换数量。公告 HTML 先按真实文本节点还原，不能在 `<font>` 标签里直接匹配数值。

| 公告 | 发布日 | PDF页数 | 候选调入/调出 | 正文声明更换 |
| --- | --- | --- | --- | --- |
| [15267](https://www.csindex.com.cn/#/about/newsDetail?id=15267) | 2024-05-31 | 5 | 50/50 | 50 |
| [15471](https://www.csindex.com.cn/#/about/newsDetail?id=15471) | 2024-11-29 | 7 | 50/50 | 50 |
| [15690](https://www.csindex.com.cn/#/about/newsDetail?id=15690) | 2025-05-30 | 6 | 50/50 | 50 |
| [3006000](https://www.csindex.com.cn/#/about/newsDetail?id=3006000) | 2025-11-28 | 6 | 50/50 | 50 |
| [3006137](https://www.csindex.com.cn/#/about/newsDetail?id=3006137) | 2026-05-29 | 7 | 50/50 | 50 |

合计500条候选是 **5次 ×（50调入 + 50调出）**，绝不是500只完整基线成员或逐日
股票池。候选 CSV 与检查清单位于忽略的 `data/research/diagnostics/official-pdf-inspection/`；
每行保留公告ID、发布日、PDF内容SHA和页码，标记 `PARSED_SOURCE_CANDIDATE_NOT_PIT`。
它没有 `date,symbol,is_member` 的正式日级 Schema，未调用 PIT importer。
`inspection_manifest.json` 记录实际 bundled Python/包版本、提取脚本哈希、输入PDF
及输出CSV哈希。这是独立来源检查，不把 bundled 环境说成研究的固定Python3.9环境。

当前提取是特定已观察布局的诊断，没有把临时分析脚本升格为支持任意公告的生产
解析器。五份PDF还缺完整逐行视觉/独立交叉核对，历史证券代码与条件生效事件仍
未核验；数量对上并不证明每个符号正确。正式 PIT 门禁不变。

## 下载与缓存合同

- 仅访问观察到的 `www.csindex.com.cn` 公告接口、`oss-ch.csindex.com.cn/notice/`，
  以及本轮新增的 `www.sse.com.cn/market/sseindex/diclosure/c/c_<日期>_<ID>.shtml`；
  限定 HTTPS、无凭证、无非标准端口，重定向仍验证允许目标。
- 原始对象按内容哈希保存，临时文件 fsync 后原子发布；请求收据同样原子替换。
  断点续跑按请求 URL/方法/查询体/合同版本定位，重新核验对象字节 SHA。
- 复用缓存保留最初获取时刻，绝不改称本次重新观察。需要新目录快照时指定新
  `--archive-root`，既有证据不清空。`--cache-only` 缺失即报错，没有网络回退。
- JSON上限2 MiB、附件20 MiB；空响应、非法 UTF-8 JSON、错误身份、截断页、重复ID、
  格式签名不符均明确失败。仅暂态HTTP/传输错误有限重试，最多3次指数退避1/2/4秒。
  401/403触发批量停止；其他永久HTTP错误不重试。
- 默认0.25秒请求间隔。urllib 超时约束单次连接/读操作，不等同整个批次的总耗时上限。
- 不直接解析附件生成成员，不用公告日填有效日，也不把上传日等同当时可得时刻。

## 验收与下一步

新增来源模块47项单测通过；与既有 BaoStock 生效语义门禁合计61项通过。覆盖缓存
校验/篡改拒绝、分页、日期和ID、暂态重试、永久错误、站点拒绝停止、缓存离线模式、
URL范围、中文编码、附件空/超限/错误签名。所有 API 单测都是人工合同响应，不是
真实成员证据。

最终冻结源码已实际执行：

```text
.venv-py39\python.exe -m pytest -q --tb=short --junitxml=results/runs/official-source-final-full-20261010.xml
.venv-py39\python.exe -m compileall -q qbot/research/universe/official_sources.py examples/research/collect_official_notices.py
git diff --check
```

全量 **1739 passed、2 deselected、13个既有 Matplotlib/Pyparsing 警告，557.01秒**；
独立解析 XML 为1739 tests、0 failures、0 errors、0 skipped。network测试没有运行，
不将离线通过解释为公网可访问。两次初始失败均保留：大型人工字节参数的 pytest ID
导致临时路径过长（已给参数设置短ID），及中文URL编码错误（已修复）；最终冻结轮
没有错误。编译和 diff 检查通过，LICENSE 的 blob 仍为
`9fb99866c50772b1afadab1657cc45cc72cdc2d4`，未修改 Legacy 或研究协议。

本轮 Changed files：来源模块、归档示例和47项测试；新增本文，并更新架构审计、
入门、数据及 BaoStock 来源文档。只组织本地代码/文档提交，不 push，不改变因子、
模型、验证、交易参数或 Forward 启用状态。

下一步是独立逐行复核已归档的 PDF 候选，取得缺失的官方调整证据与完整起点名单。
还需检查只在附件提及中证500的公告、证券代码变化和条件生效事件；完成全部链条
后才能建立新的受审计 PIT 来源合同，再解决 ST/停牌/上市日期输入与正式实证。
现有 `POINT-IN-TIME UNIVERSE REQUIRED` 错误仍是正式数据消费的正确结果。

## 早期定期公告的独立浏览器证据与候选解析

此前的本机 HTTP 403 清单完整保留。公开只读浏览器另外读到五份公告，保存为
`data/research/diagnostics/official-browser-notices/20261010/*.observation.json`。
它们没有注入原 `OfficialNoticeSource` 请求缓存，不能把独立浏览器成功改写成
本机下载成功，或用它取消第一次401/403后停止当前批 HTTP 请求的规则。

新增 `universe/browser_observations.py` 严格读取这些本地容器：核验 Schema、唯一
JSON键、公开 URL/公告 ID、成功响应、发布日和明确 UTC 的保存时刻；分别绑定
完整容器字节 SHA-256 与原 `response.text()` 字符串编码为 UTF-8 后的 SHA-256。
这不是压缩 HTTP 线缆字节哈希，也没有第三方时间戳或独立来源认证证明。
正文是当下读取的历史公告，不等于这些当前字节在历史发布日已经可获得。

新增 `universe/notice_review.py` 只支持本轮实际观察到的内嵌调整表布局。
它先还原可见文本节点，忽略 script/style，精确选择“中证500指数样本调整名单”；
排除备选名单和其他指数。表头必须明确调出／调入方向，证券代码保留六位并做
canonical 转换；两个方向分别去重、无交集且均与正文声明的更换数量相符。
嵌套表、rowspan、未闭合单元格、多个生效日或冲突数量均要求独立复核，而非猜测。

| 公告 | 发布日 | 正文明示收盘后日期 | 内嵌候选调出／调入 |
| --- | --- | --- | --- |
| [13888](https://www.csindex.com.cn/#/about/newsDetail?id=13888) | 2021-11-26 | 2021-12-10 | 50／50 |
| [14223](https://www.csindex.com.cn/#/about/newsDetail?id=14223) | 2022-05-27 | 2022-06-10 | 50／50 |
| [14497](https://www.csindex.com.cn/#/about/newsDetail?id=14497) | 2022-11-25 | 2022-12-09 | 50／50 |
| [14796](https://www.csindex.com.cn/#/about/newsDetail?id=14796) | 2023-05-26 | 2023-06-09 | 无内嵌表，待 PDF |
| [15044](https://www.csindex.com.cn/#/about/newsDetail?id=15044) | 2023-11-24 | 2023-12-08 | 无内嵌表，待 PDF |

三个表合计300条是 **3次 ×（50调出 + 50调入）**，不是300只完整起点成员。
`explicit_after_close_date` 保留正文陈述；不直接当作当日开盘成员日期，不自动
推断下一交易日，也不生成正式 `date,symbol,is_member` 数据。
同一显式日期重复出现可以接受；条件生效而未给固定日期时不会代用公告日。

可运行入口默认完全离线，保存原容器的逐 run 独占副本、候选 CSV、复核 JSON
和完整运行清单。缺少内嵌表是 `ATTACHMENT_OR_LAYOUT_REVIEW_REQUIRED`，不是已
核验的零调整；解析失败为 `REVIEW_FAILED` 并使诊断状态 partial。诊断成功也只
表示这个显式输入子集处理完成，不能表示调整链或 PIT 完整。

```text
.venv-py39\python.exe -m examples.research.review_browser_notices --input-directory data/research/diagnostics/official-browser-notices/20261010
.venv-py39\python.exe -m examples.research.review_browser_notices --input-directory data/research/diagnostics/official-browser-notices/20261010 --download-attachments --archive-root data/research/diagnostics/official-browser-attachments/20261010-early-regular
```

显式附件下载仍使用本机标准公开 HTTP 客户端、原限速/权限拒绝规则，记录独立
HTTP 请求收据；默认离线复核不实例化该客户端。观察到两条附件 URL 使用
`/notice%2F...`，范围核验只解码一次并拒绝目录穿越/重复编码，保存及请求身份
仍保留原 URL；没有猜测或替换另一文件。

实际运行与失败：

- 离线初轮 `20261010T100008.621992Z-review-browser-notices-afe81336`：5份正文，
  3张表，300候选事件，0 HTTP 请求。
- 第一轮附件 `20261010T100405.682635Z-review-browser-notices-1353684c`：failed，
  1次请求，Python 3.9 `socket.timeout`，未取得附件。失败清单未重写。
- 补充直接 socket/read 异常分类与单测后，重跑
  `20261010T100709.308505Z-review-browser-notices-addcd5a4`：partial，5次请求，
  5个附件均超时，0归档附件；继续处理其他附件的行为已真实执行。
  只识别明确网络异常，普通 OSError 仍 fatal；权限拒绝仍停止后续 HTTP。
- 两个 PDF 的独立公开浏览器请求也在8秒中止限制内失败，没有读到文件或 HTTP
  状态；实际错误保存在 `data/research/diagnostics/browser-attachment-failures/20261010.json`，
  其 `archived_at_utc` 是保存记录的时刻，不补造失败响应时刻。浏览器已释放。
- 冻结代码离线复跑 `20261010T101512.328012Z-review-browser-notices-eb7c255e`：
  success，5份正文/300候选/0 HTTP；5个源容器与逐 run 副本、CSV/JSON文件 SHA
  已另用 PowerShell 独立复核一致，运行记录仍诚实标明 dirty 工作区。
- 原两份 XLSX 来源缓存复跑
  `20261010T101515.010643Z-collect-official-notices-6f70486b`：success，0 HTTP、
  12次已核验缓存读取。新合同没有破坏旧请求缓存身份。

旧46份正文与新增5份 ID 无交集，合计51个不同公告正文；仍远少于目录窗口246条。
研究区间十次定期公告的正文证据现已覆盖，但2023年两份 PDF 尚未取得，完整
临时调整、退市条件、历史代码变更、完整起点500成员与证券状态仍未核验。
这些差距不因候选事件数量对上而消失；正式建数据集门禁和 Forward 启用状态不变。

## 独立交易所公告

新增只读示例 `examples/research/collect_exchange_article.py`，只读取实际观察到的
上交所指数公告路径，保留原 HTML 字节及 SHA；文件链接只发现、不自动下载。
它不把网站重生成日期、模板页日期或多个 title 拼接当作公告日期/起点名单。

[上交所2021-05-28公告](https://www.sse.com.cn/market/sseindex/diclosure/c/c_20210528_5476672.shtml)
本机实际 HTTP 200取得29496字节，正文概要指出中证500更换50个样本；没有完整
500成员基线，也没有发现实际附件链接。首轮运行
`20261010T093935.209133Z-collect-exchange-article-38634c54` 保留原记录；修正模板
重复 title 处理后只读缓存复跑
`20261010T101513.704012Z-collect-exchange-article-d5675660` 成功，0 HTTP、1缓存。
另一次 Firecrawl scrape 失败不是该公开文件不存在的证明；其他有限检索也没有
取得2021年完整成员。不能由当前中证500成分或ETF持仓偷偷补出历史起点。

## 本轮软件验收

194项定向测试通过（来源71、HTML候选48、浏览器容器/CLI61、BaoStock门禁14），
JUnit：`results/runs/browser-notice-targeted-final2-20261010.xml`。
它们使用明确人工响应，只验证软件合同；上面的实际公开数据运行另行记录，
不把 mock 成功算作真实附件下载成功。没有升级核心依赖、修改 Legacy 或许可证。

冻结代码的完整研究测试实际通过 **1872 passed、2 deselected、13 warnings，311.38秒**；
JUnit：`results/runs/browser-notice-full-final-20261010.xml`，独立 XML 检查1872个测试、
0失败/0错误/0跳过。两个 deselected 是默认排除的网络测试；13个警告仍是既有
Matplotlib/Pyparsing弃用提示。没有执行具联网、邮件或GUI副作用的 Legacy suite。
5份解码正文 UTF-8 哈希也另用 .NET SHA-256 独立复核一致；原 LICENSE 对象哈希
仍为 `9fb99866c50772b1afadab1657cc45cc72cdc2d4`。CLI `audit` 实际成功，运行
`20261010T102029.249530Z-audit-acc36f20`，没有生成或授权正式研究数据。

## 旧式正文附件与起点前补证

同日继续读取3份实际公开正文；保存方式与上面的浏览器观察合同相同，分别保留
原始 `response.text()` 字符串、输入容器和 UTF-8 哈希。采集时刻使用标准 ISO UTC
`Z` 表示，读取器针对 Python 3.9 解析为 UTC，仍保留原表示，不补造外部时间戳。

| 公告 | 发布日 | 原文明示的生效语义 | 正文中实际文件链接 |
| --- | --- | --- | --- |
| [13307](https://www.csindex.com.cn/#/about/newsDetail?id=13307) | 2021-03-03 | 自2021年3月15日起 | 1份 XLSX |
| [12470](https://www.csindex.com.cn/#/about/newsDetail?id=12470) | 2021-05-28 | 2021年6月11日收盘后 | 2版 XLSX |
| [13420](https://www.csindex.com.cn/#/about/newsDetail?id=13420) | 2021-08-30 | 自中国能建上市日起 | 1份 XLSX |

三份的 `enclosureList` 都为空，文件链接实际上在 HTML `<a href=...>` 中。
只遍历该元数据字段会漏掉真实附件。因此新增 `notice_attachments.py`，供官方
收集器和浏览器正文复核共同调用。精确发现正文文件链接，保留原 href、解析 URL、
可见标签/实际 title、出现位置及元数据来源；忽略普通官网链接和 script/style。
相同编码请求别名可合并来源，`/notice%2F` 与 `/notice/` 不猜成相同资源；不同
日期目录的两个实际文件保留为两版，不以更新日期选择历史可用版本。嵌套、重复
属性或未闭合的锚点明确失败。发现链接不意味着授权下载，客户端仍核验来源路径。

实际观察的旧式路径范围仅为：

```text
https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/info/files/YYYYMMDD/16位数字.xlsx
```

新增独立合同 `csindex-legacy-static-notice-attachments-observed-20261010-v1`，
不扩展为任意 static 文件或当前 constituents 文件；旧 API、`/notice/` 与 SSE
缓存请求身份不变。目录穿越、反斜线、重复编码、外站或该旧式路径 query 均拒绝；
401/403 后停止同批后续 HTTP，缓存仍按原收据逐次核验。

候选语义字段另加 `explicit_start_date` 和 `conditional_effective_clause`，与
`explicit_after_close_date` 并存。不把“上市日起”改成公告日或 URL 日期，不把
“自某日起”改成收盘后，也不自动平移至下一交易日。两种明确日期或额外条件
同时出现时要求独立复核；不产生正式成员有效日期。

### 实际下载的四个历史文件

运行 `20261010T104038.381041Z-review-browser-notices-1e22aba3` 实际成功：
3份输入正文、4次 HTTP、4份附件，无失败。该次与此前5份附件超时是不同资源，
不能重写此前失败历史。档案位于
`data/research/diagnostics/official-browser-attachments/20261010-starting-boundaries/`。

| 公告/版本 | 实际原始 URL | 字节数 | SHA-256 |
| --- | --- | ---: | --- |
| 13307 | [20210312/1615540258900287.xlsx](https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/info/files/20210312/1615540258900287.xlsx) | 13898 | `72b98f7c258494d57a2af39c9daa18f52a7fce07b7519226e94103b2b85fbe49` |
| 12470，6月1日目录 | [20210601/1622509386248149.xlsx](https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/info/files/20210601/1622509386248149.xlsx) | 789788 | `ea291da157e677490e8d7287f1fa33aa17f69665e76fe6b71b295b038b360e54` |
| 12470，6月10日目录 | [20210610/1623319091660435.xlsx](https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/info/files/20210610/1623319091660435.xlsx) | 772131 | `07e8c58d5f02cbaaf5e5b4a98f7c541208218d7a3de9b9627fbff37f31770a07` |
| 13420 | [20210830/1630328886593411.xlsx](https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/info/files/20210830/1630328886593411.xlsx) | 12000 | `1a8f0c4d1e172eb3ec503b636d64ef06f237ce085604fb02ad97a78217b4b306` |

HTTP 收据均为200，保留 Content-Type、ETag 与 Last-Modified。四个 Last-Modified
都是2024-11-30，不能将它们、2021目录名或当前抓取时刻当作2021历史可用性证明。
浏览器容器获取时间也仅是供应的观察标签，不是外部可信时戳或历史来源认证。

### 独立只读名单核验

使用技能要求的 bundled Artifact Tool 导入，没有编辑、导出或重写源工作簿。
按真实工作表和精确指数代码字符串 `000905` 取行，保留代码前导零和方向：

- 12470两版：各50调入、50调出；动作/证券代码/证券简称全部一致，也与独立
  HTML 候选解析的100条记录逐项一致。两版各25行“备选名单”都有独立“排序”列，
  不是已调入成员，全部排除。其他指数行不参与中证500统计。
- 13307：调入表 A10:D11 为600764（中国海防）、600956（新天绿能）；调出表
  A12:D13 为000564（*ST大集）、600515（*ST基础）。这是2对变更，不是500基线。
- 13420：Sheet1!A11:F11 为调出600068（葛洲坝），调入代码原值为 `-`，名称
  中国能建。诊断保留 `UNRESOLVED_SYMBOL_NOT_FILLED`，不从当前证券代码补齐。

完整 typed values 的只读检查文件位于
`data/research/diagnostics/workbook-inspector/20261010-starting-boundaries/`；
独立比较结果 `csi500-comparison.json` 的 SHA 为
`8f59e3838ccd6d7e326b1fce8d304c4f0c4eaf80f95655452a3b8cd51c996d07`。
检查文件绑定原 XLSX 哈希与检查脚本哈希，原始文件读取前后均校验未改变。
脚本仍在同一个 `inspect.mjs` 上增量维护，旧版本按 SHA 独占保留在 `helper_versions/`。
首轮比较遇到备选名单额外“排序”列时明确报错，没有输出猜测结果；读取真实表头
后按实际列修正，重新比较成功。保留该失败脚本版本
`d4fd7b55dad1c115a1810db0be97d9433b0b546ffa3d6903d5ef52a39cebb8e7`。
只读导入版本脚本 SHA 为 `ccae39d427a1cdd47eac1e62921a69b2c967d252053531b643783f5fa8cabf05`，
最终比较脚本 SHA 为 `89016cf991990cbe6722a82df509c4c6afb2743ff44392668fa4113bd2dffb21`。
这些独立工具不进入 FactorLab 运行依赖，没有修改研究 Provider 或数据集入口。

另实际读取 [上交所葛洲坝终止上市公告](http://www.sse.com.cn/disclosure/announcement/listing/stock/c/c_20210909_82957014.shtml)，
发布于2021-09-09，写明2021-09-13起终止股票上市交易。仅能证明交易所退市事实，
不能替代指数公司“自中国能建上市日起”的成员事件日期。独立保存的是 Firecrawl
当前页面 markdown，明确不是原始 HTML 字节，容器 SHA 为
`bfdacc16fdba17246e14ec68cb57e545c655ee9bf4cc6b9e701efaff677d7399`，文件
`data/research/diagnostics/sse-corporate-source/20261010-gezhouba-delisting.observation.json`。
有限检索没有取得可独立核验的完整2021年500成员基线；不以搜索摘要推断日期、
不把股票退市日期和指数成员退出日期混同，不用499快照加猜测证券补出500。

### 最新复跑与验收

实际执行下面四个命令，前三个没有 HTTP 回退：

```text
.venv-py39\python.exe -m examples.research.review_browser_notices --input-directory data/research/diagnostics/official-browser-notices/20261010
.venv-py39\python.exe -m examples.research.review_browser_notices --input-directory data/research/diagnostics/official-browser-subsets/20261010-starting-boundaries --download-attachments --cache-only --archive-root data/research/diagnostics/official-browser-attachments/20261010-starting-boundaries
.venv-py39\python.exe -m examples.research.collect_official_notices --notice-ids 13716 3006027 --archive-root data/research/diagnostics/official-notices/20261010-csi-rebalance --cache-only
.venv-py39\python.exe -m qbot.research.cli audit --config configs/research/csi500_5y.yaml
```

- `20261010T110640.990434Z-review-browser-notices-f70feaf3`：success，8份正文、
  4张内嵌表、400候选变更、9个实际附件链接、0 HTTP。
- `20261010T110641.096256Z-review-browser-notices-fb43e9b8`：success，3份正文、
  4份已验证缓存附件、0 HTTP。
- `20261010T110641.095255Z-collect-official-notices-8d5fd713`：success，原2份公告、
  12次已验证缓存读取、0 HTTP；原缓存合同未失效。
- `20261010T110641.608707Z-audit-4d0051e5`：success。以上 run 诚实记录未提交工作区。

另用 PowerShell/.NET 独立核验8份容器、各 run 快照和响应 UTF-8 哈希，候选 CSV、
review JSON、4个 XLSX 和原 HTTP 收据、检查 JSON 与旧脚本 SHA 全部一致。
46份旧正文与当前8份 ID 无交集，合计54个独立公告正文；不是246条目录窗口完整覆盖。
新的公开浏览器会话已实际释放；没有改用代理、认证、API key 或绕过站点权限拒绝。

定向测试实际 **241 passed**（来源77、HTML候选56、浏览器容器/CLI67、正文链接27、
BaoStock门禁14）；JUnit 为 `results/runs/body-link-targeted-final-20261010.xml`。
冻结生产代码的完整研究测试实际 **1919 passed、2 deselected、13 warnings，608.18秒**，
命令：`.venv-py39\python.exe -m pytest -q --tb=short --junitxml=results/runs/body-link-full-final-20261010.xml`。
独立 JUnit 检查1919个测试、0失败/0错误/0跳过；默认排除的2个网络测试不算通过。
13条警告仍是原 Matplotlib/Pyparsing 弃用提示，Legacy suite 没有运行。

当前仍无完整起点500成员、完整临时链和真实逐日证券状态；2023年两份 PDF 未取得。
正式 dataset、真实横截面 RankIC、五年四模型实证和真实 Forward 仍未完成。
本轮不启用 Forward，不放行 BaoStock 周更新股票池，下一阶段入口仍是完成可核验
历史成员链和状态输入后，运行真实多股票 CLI，再进行冻结五年研究。

## 明确正文覆盖缺口的离线审计

同日再次尝试两份2023年 PDF 原链接：运行
`20261010T111459.591141Z-review-browser-notices-be131164` 为 partial，2次本机 HTTP，
2个请求超时，0附件；没有将失败重写成不存在或零调整，也没有更换路径或代理。

随后从已绑定目录中选出尚未读取的192个 ID，不以“标题没提中证500”为排除规则。
普通公开浏览器逐条读取，匿名 `credentials=omit`，间隔1秒，单次8秒中止、每批
有时间上限。前24份得到200，ID、标题、发布日期与目录逐项一致；第25个受控
正文请求（[12466](https://www.csindex.com.cn/#/about/newsDetail?id=12466)）返回403，
停止全部剩余受控读取，随后实际释放浏览器，没有重新开启会话或改变认证/代理。
403响应文本也保存，单独标记为拒绝，绝不包装成200正文观察。

24份成功容器位于 `data/research/diagnostics/official-browser-notices/20261010-remaining/`。
`capture.receipt.json` 保留192项实际目录工作清单、各批受控请求状态、24个成功 ID、
拒绝响应及观察时刻，SHA 为
`0d8fa97a17317fa7fe80d9c2e0d2bbe55ebbaea9d64d12fb60f2ed001ec1795a`。
25是显式正文 fetch 数，不包含页面导航、预检或应用自行加载的资源；没有声称
观察到了整个浏览器的 HTTP 总数。保存时刻不是失败发生时刻或外部认证时戳。

新增纯标准库 `universe/source_coverage.py` 与独立入口
`examples/research/audit_official_coverage.py`，默认且唯一模式为离线：

```text
.venv-py39\python.exe -m examples.research.audit_official_coverage --archive-root data/research/diagnostics/official-notices/20261010-csi-rebalance --browser-directories data/research/diagnostics/official-browser-notices/20261010 data/research/diagnostics/official-browser-notices/20261010-remaining
```

HTTP档案由原 `OfficialNoticeSource(cache_only=True)` 重新检查请求身份、字节和 SHA，
浏览器容器由原严格读取器检查，彼此保持不同原表示。目录缺页、重复 ID、正文
身份不符、坏缓存、未知容器字段或同 ID 多版本明确失败；不自动选新版本或重抓。
输入全部验证后才保存逐 run 独占字节快照、覆盖 CSV/JSON、附件缺口 JSON 和摘要，
每份输入快照与输出都绑定内容 SHA。源码不提供 `get_members` 或正式 PIT 发布入口。

首次实际运行 `20261010T112651.687929Z-audit-official-coverage-5d218f34`：

- 目录726条，本次发布日窗口246条；46份已验证 HTTP 正文＋32份浏览器正文＝78。
- 168份正文缺失，返回码1、manifest 为 partial；完整数据消费者仍保持阻断。
- 15份正文提到中证500，不足以排除其他公告附件中的中证500事件。
- 发现54个附件引用：无论是否另已归档，本次覆盖审计都未检查其内容，统一明确
  标注 `CONTENT_NOT_REVIEWED_BY_THIS_AUDIT`，不误报为54个文件缺失或54个已审核。
- 缺正文时，附件数量和中证500提及状态为 null/unknown，不填0；没有发现文件
  链接也不是“无成员调整”。目录窗口正文齐全亦不能证明完整 PIT 或历史可用性。
- 全程0 HTTP、54次已验证缓存读取；绑定86份输入（8页目录、46份HTTP正文、
  32份浏览器容器）。没有创建股票池、dataset、RankIC 或 Forward 信号。

PowerShell独立核验86份原输入/快照、四个输出 SHA 均一致；24份成功容器与各 ID
相符。清单诚实记录未提交工作区。新测试实际42项通过（纯逻辑26、文件/CLI16），
JUnit 为 `results/runs/source-coverage-targeted-20261010.xml`；包括缺正文的 partial、
零HTTP、哈希/快照、来源表示不混淆、重复版本与目录身份拒绝、旧输出不覆盖和
写入异常终止收据。人工响应只用于软件验收，不构成真实历史成员证据。

剩余168份正文、2023年两份 PDF、完整成员基线、条件事件实际生效及证券状态
仍缺；不能用本轮目录覆盖改善替代真正五年研究或真实样本外结果。

正式配置入口亦实际复核：
`python -m qbot.research.cli build-dataset --config configs/research/csi500_5y.yaml`
运行 `20261010T113601.500013Z-build-dataset-0f3c5834` 为 failed，先在读取旧基准
缓存时报告 `unsupported cache metadata version for 000905.SH: 1`，尚未进入
成员读取阶段，不能把这一次失败原因称为已触发 PIT 门禁。没有写正式 dataset，
也没有修改旧缓存的版本号/来源字段来放行。后续须按新合同实际重新取数；即使
基准刷新成功，未核验 BaoStock 成员生效日及完整证券状态的问题仍不因此解决。
CLI `audit` 同日正常成功，run 为 `20261010T113344.435806Z-audit-0a975517`。

冻结生产代码的全量研究测试实际 **1961 passed、2 deselected、13 warnings，650.26秒**，
JUnit `results/runs/source-coverage-full-final-20261010.xml`；独立 XML 检查0失败、
0错误、0跳过。命令为 `.venv-py39\python.exe -m pytest -q --tb=short --junitxml=results/runs/source-coverage-full-final-20261010.xml`。
新42项与原BaoStock生效语义门禁14项联合验收 **56 passed**，JUnit为
`results/runs/source-coverage-targeted-final-20261010.xml`。2项网络测试默认未运行，
13条警告仍是旧 Matplotlib/Pyparsing 弃用提示，不包括 Legacy 副作用测试。
正式入口失败记录也未删除；许可证对象仍为原 `9fb99866c50772b1afadab1657cc45cc72cdc2d4`。

原拒绝捕获收据不修改，另追加 `capture.catalogue-binding.json`：保存原目录 producer
run/提交及完整目录文件 SHA `b7c47695844db8c014dfe89bda8ada230e8150cded105c01afea3260be713281`，
已经独立与原producer输出清单匹配；同时保存浏览器成功释放的工具结果。
追加绑定文件的 SHA 为 `d3b3bae95b17d19ad5d5c2af202932d8b15da4c298484b65da25779e435f3a0a`。
本輪另独立核验32份解码正文 UTF-8 哈希；86份原输入/快照与4个输出均保持匹配。

## 三份早期定期工作簿的补齐与只读比较

同日稍后，使用已观察到的原附件链接进行一次新的显式子集下载，运行
`20261010T142707.396052Z-review-browser-notices-9fa2a500` 实际 success：3份正文、
300条内嵌候选事件、3次附件 HTTP 请求、3份 XLSX，失败0。此前5份附件超时和
两份2023 PDF失败均原样保留，未重写为本次成功；没有重开已被拒绝的公告读取流程。

档案：`data/research/diagnostics/official-browser-attachments/20261010-regular-workbooks/`。

| 公告 | 工作簿 SHA-256 | 字节数 | 调入真实范围 | 调出真实范围 | 备选真实范围 |
| --- | --- | ---: | --- | --- | --- |
| [13888](https://www.csindex.com.cn/#/about/newsDetail?id=13888) | `f6b9d596f3fa6072258aa1eb2c036517bf20cc74c7879eaad1069cb8e1747909` | 872904 | 调入!A1034:D1083 | 调出!A838:D887 | 备选名单!A22:E46 |
| [14223](https://www.csindex.com.cn/#/about/newsDetail?id=14223) | `a3cceb28f6df96a77d4747a804b10a346a17f22d9b521261c222bdb03d4ca7a5` | 754024 | 调入!A947:D996 | 调出!A771:D820 | 备选名单!A17:E41 |
| [14497](https://www.csindex.com.cn/#/about/newsDetail?id=14497) | `acbf06876606a980fd65c3e3185b7725634ad7530f4fa83ee1d3a3963ee23490` | 673136 | 调入!A987:D1036 | 调出!A725:D774 | 备选名单!A17:E41 |

三个工作簿均只读导入，按六位文本指数代码 `000905` 和真实表头筛选，证券代码
不丢前导零。各50条调入、50条调出与各自公告 HTML 的动作、canonical symbol、
证券简称逐项一致。各25条备选保留独立排序，合计75条全部排除成员统计。
300是三次变更事件数，不是300个完整成员，也不证明逐日500成员链完整。

沿用并增量扩展原 `inspect.mjs`，先按 SHA 保存旧版本，未另造工作簿或重导出
源文件。原导入脚本 SHA 为 `89016cf991990cbe6722a82df509c4c6afb2743ff44392668fa4113bd2dffb21`；
新增严格附件哈希绑定的比较模式 SHA 为
`50a82f001659b75453a8b5c94bb66f82041b50ae1c54f43c678588cada6b5cb4`。
新模式拒绝未知表头、缺失/重复绑定、代码/名称冲突、重复备选代码/排序或正文
与工作簿不一致。原四个起点前工作簿比较也实际复跑，仍保留新增代码 `-` 和未解析状态。

检查 JSON 位于 `data/research/diagnostics/official-workbook-inspection/20261010-regular-workbooks/`。
`csi500-comparison.json` SHA 为
`2c87c86be166ab086947aa6ae3669f93278ba20a2fd17263e07dd83fac8f9796`。
输入检查文件、原工作簿、下载收据和独立 HTML 来源分别绑定，读取前后原文件 SHA 一致。
本轮附加模型/PDF来源核验没有修改任何历史公告容器或原附件。

不能把当前附件当作原发布日期时可得的同一版本：13888附件 `createAt` 为2021-11-30，
14497为2022-12-07（正文分别发布于2021-11-26、2022-11-25）；三份 HTTP
`Last-Modified` 都为2024-11-30。所有日期保留原含义，不用它们代替成员生效日期。

实际缓存复跑与定向回归：

```text
.venv-py39\python.exe -m examples.research.review_browser_notices --input-directory data/research/diagnostics/official-browser-subsets/20261010-regular-workbooks --download-attachments --cache-only --archive-root data/research/diagnostics/official-browser-attachments/20261010-regular-workbooks
.venv-py39\python.exe -m pytest -q --tb=short tests/research/test_official_sources.py tests/research/test_notice_attachments.py tests/research/test_notice_review.py tests/research/test_browser_notice_observations.py tests/research/test_baostock_effective_semantics.py --junitxml=results/runs/regular-workbook-source-targeted-20261010.xml
```

缓存 run `20261010T144217.512073Z-review-browser-notices-d571067e` success：0 HTTP、
3次已核验附件缓存读取；另有3份逐 run 正文快照与300候选事件。
定向 **241 passed，10.40秒**；独立 JUnit 检查241 tests、0失败、0错误、0跳过。
这些是软件合同回归，真实工作簿比较是上述独立检查，二者不互相冒充。
生产研究源码没有变化，最近的完整1992项回归仍见 [BENCHMARK_RECOVERY.md](BENCHMARK_RECOVERY.md)。

另保存了此前8次限定公开检索的原 MCP 响应，文件
`data/research/diagnostics/pit-baseline-discovery/20261010-bounded-search/search-responses.json`，
SHA 为 `ba735859eb9f3d007c715ea3018ce2b1742bae15b2883f0de7b25decf02fb4f4`。
这是搜索摘要而非原始出版物字节；返回包含窗口外日期、其他500指数和基金持仓，
日期过滤本身没有证明2021年名单完整。本次有限检索没有取得合格起点基线，
不据此宣称所有公开来源都不存在该数据。

“中国能建上市日起”的条件事件又取得两份实际披露 PDF、相关页文本和视觉核验，
见 [CONDITIONAL_EVENT_EVIDENCE.md](CONDITIONAL_EVENT_EVIDENCE.md)。上市事实的补证
没有生成成员日期或填写原表 `-`，也没有解除正式 PIT 门禁。
仍需完整起点500成员、全部定期/临时链、过渡期成员语义和逐日证券状态；2023年
两份定期 PDF仍未取得。正式 dataset、横截面 RankIC、五年实证和真实 Forward尚未完成。

## 两份2023年定期 PDF 的后续补齐

2026-10-11（UTC运行时间仍为2026-10-10）后续限定重查已实际取得14796、15044，
原超时记录保留。两份各5页，Poppler查看各1/2页目标表和5页备选名单；
研究 Python 3.9的新离线解析入口各生成50调入、50调出，全程0 HTTP。
pdfplumber独立提取比较200条动作/代码/名称/所在页一致，50条备选单独排除。
新增纯解析模块、运行入口、可选依赖和测试详见 [PDF_NOTICE_REVIEW.md](PDF_NOTICE_REVIEW.md)。

因此上文“两份2023 PDF仍未取得”仅表示当时的失败状态，不再是当前附件缺口。
正文覆盖仍为78/246，完整起点500成员、临时链、过渡期成员语义和证券状态仍缺。
候选事件没有导入正式 universe，PIT/Forward门禁和未完成真实五年研究的结论不变。
