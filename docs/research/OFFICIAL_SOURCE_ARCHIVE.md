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
