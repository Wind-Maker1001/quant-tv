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

- 仅访问观察到的 `www.csindex.com.cn` 公告接口和 `oss-ch.csindex.com.cn/notice/`；
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
