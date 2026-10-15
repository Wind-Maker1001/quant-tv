# 中证500实际成员生效证据定向试点

审计日期：2026-10-15（Asia/Shanghai）。总体研究结果为 **PARTIAL**：已复用权威公告与附件，
但两项试点均没有可独立核验的实际指数成员生效证据。**认证事件0，权威完整起始基线0，
日级PIT股票池0**。这里的0是认证产物数量，不是历史成员数或历史事件数。

基线为PR #6人工合并提交 `fce2f0a25e8ae8459c1ab86709e26e5e74c9692a`。
该提交的[完整研究CI](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38733446316)和
[静态CI](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38733446247)通过后，才建立
`codex/pit-effective-membership-evidence`。证据准备阶段读取原工作区的旧档案；各独立收据
如实保留当时执行HEAD和源根目录，不把忽略目录内容说成合并提交中的Git文件。

## 三项核验结果

| 子项 | 核验所得 | 未核验/实际边界 | 结果 |
| --- | --- | --- | --- |
| 2021-09-13开盘完整起点 | 复用4批历史发现档案；找到CIIS官方授权渠道和三种时间口径 | 完整500名单、独立当日计数、葛洲坝过渡处理均缺；actual=UNKNOWN | BLOCKED |
| 常规定期公告13888 | 正文发布日2021-11-26；计划2021-12-10收市后；50调入、50调出，100项代码/名称及坐标匹配，排除25备选 | 未取得实施确认或边界成分文件；actual=UNKNOWN | PARTIAL / CANDIDATE_ONLY |
| 条件公告13420 | 正文发布日2021-08-30；自中国能建上市日起；调出600068葛洲坝，调入原代码为`-` | 独立披露佐证上市条件在2021-09-28发生；指数实际实施和退市过渡未知；actual=UNKNOWN | PARTIAL / CANDIDATE_ONLY |

详见[起点核验](PIT_BASELINE_EVIDENCE_REVIEW.md)、[定期事件](PIT_REGULAR_EVIDENCE_REVIEW.md)、
[条件事件](PIT_CONDITIONAL_EVIDENCE_REVIEW.md)。[定期候选动作](evidence/pit-effective-membership-evidence-v1/regular-review.json)
保留每项历史代码/名称、HTML行号和XLSX单元格位置；并未按同一行推断逐只经济替代关系。
[条件事件摘要](evidence/pit-effective-membership-evidence-v1/conditional-review.json)保留原占位代码和
后来独立身份映射的区别。既有工作簿解析器仍拒绝`Sheet1!E11:F11`的未解决身份，没有为了通过而改写它。

## 证据与日期边界

公告记载的发布日期、日内公开时刻、计划安排、条件触发、独立实际成员生效和本机获取时间分别记录。
两项正文均没有已认证的日内公开时刻。当前字节SHA证明本次读取内容，不证明这些字节在历史发布日期
已经公开；浏览器`response.text()`容器SHA、解码正文SHA和发行方原附件SHA也分别记录。

| 边界/事实 | 已有证据 | 不能推出 |
| --- | --- | --- |
| 13888：2021-12-10收市后 | 指数公司正文计划安排 | 12月10日交易时段已替换，或12月13日已实际实施 |
| 13888附件：createAt 2021-11-30，HTTP修改2024-11-30 | 当前附件元数据和原始获取收据 | 当前附件11月26日已可知，或没有后续更正 |
| 13420：中国能建2021-09-28上市 | 上交所托管的广发受托报告、发行人港交所托管年报 | 指数实际成员当日完成替换 |
| 葛洲坝2021-09-13正式退市 | 既有广发受托报告物理6/7页跨页叙述，本轮补做视觉核对 | 9月13日指数退出、现金替代、临时替代，或499快照缺少哪只 |
| 13716：2021-09-10收盘后的一对调整 | 既有官方正文与附件，作为起点背景 | 其余499成员、完整500基线或其实际成员日期 |

两项试点均无完整历史身份/退市链、临时插入和更正公告覆盖证明。代码与名称在事件中的出现不等于
完整时变身份认证。BaoStock `updateDate`、公告日和交易日历均未用于填写实际成员日期。

## 冲突清单与缺口

| 项目 | 性质 | 未解决原因及所需证据 |
| --- | --- | --- |
| 起点旧499响应与500硬要求 | 完整性/语义缺口 | 缺权威同口径全量名单及过渡说明；不能补1只或认定具体缺失证券 |
| 定期公告日与附件当前版本 | 历史可知性缺口 | 缺历史版本、首次公开证明和更正记录 |
| 计划收盘后与实际成员切换 | 证据范围缺口 | 缺实施确认及对应开/收盘全量成分；交易日历不能填补 |
| 条件触发与指数实际实施 | 证据范围缺口 | 上市事实已有佐证，指数实施及9月13日至28日过渡仍缺 |
| 原调入代码`-`与后来601868 | 身份解析缺口 | 不覆盖原表；需指数发行方明确的历史标识及生效映射 |
| 新基金披露与实际成员证据 | 来源用途不符 | 仅说明未来/可能参与投资，拒绝作为实施确认 |
| 正文标题/关键词未命中 | 目录覆盖缺口 | 不证明没有临时调整；全量更正/临时链仍未取得 |

没有发现足以裁定另一实际成员日期的独立直接日期冲突。上述“缺口”不能包装成已证实的日期冲突，
也不能把未发现更正理解成不存在更正。各子报告保留具体来源、哈希、失败和限制。

## 离线检查与局部重放结果

新增`event_evidence`是独立诊断检查清单，不接入正式提供者或正式资格规则。它复用既有
`pit-events.json`、来源缓存及本轮案例摘要，逐个核对显式路径与SHA，区分条件触发证据和
实际成员证据。即使人工输入满足清单，也只返回`REVIEW_READY_NOT_CERTIFIED`，不认证或发布成员。

实际运行结果及独立收据：

- [事件级矩阵](evidence/pit-effective-membership-evidence-v1/event-audit-v1/event-matrix.json)
- [局部重放准入结果](evidence/pit-effective-membership-evidence-v1/event-audit-v1/local-replay.json)
- [来源字节核验与执行收据](evidence/pit-effective-membership-evidence-v1/event-audit-v1/receipt.json)
- [起点独立收据](evidence/pit-effective-membership-evidence-v1/baseline-receipt.json)、[定期独立收据](evidence/pit-effective-membership-evidence-v1/regular-receipt.json)、[条件独立收据](evidence/pit-effective-membership-evidence-v1/conditional-receipt.json)

局部重放状态为`NOT_ATTEMPTED_AUTHORITY_BASELINE_ABSENT`：没有起始集合，故不执行成员更新。
生成成员行0，逐日500独立计数未执行，计数值保持null。没有把源表解析重放或合成测试当成真实成员重放。

在持有原档案的本机，以Python3.9运行：

```powershell
& 'D:\Code\量化TV\.venv-py39\python.exe' -X utf8 -m examples.research.audit_pit_event_evidence `
  --archive-root 'D:\Code\量化TV' `
  --case-reviews docs/research/evidence/pit-effective-membership-evidence-v1/regular-review.json docs/research/evidence/pit-effective-membership-evidence-v1/conditional-review.json `
  --annotations docs/research/evidence/pit-effective-membership-evidence-v1/conditional-review.json `
  --output results/diagnostics/pit-effective-membership-evidence/new-exclusive-run
```

退出码1表示`PARTIAL`，2表示输入字节缺失或不一致。输出目录必须全新，不能覆盖旧收据。
干净克隆不含原始材料，只能运行合成回归或取得授权档案后复核字节；不能将缺原件视为成功。
软件测试与最终CI、独立复审记录另见[交付收据](evidence/pit-effective-membership-evidence-v1/delivery-receipt.json)。

提交`13b66f5`的[完整研究CI](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38756478550)和
[静态CI](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38756478023)均通过。下载的原JUnit与覆盖率XML
经仓库既有验证器复核：3076项通过、1项Windows专属锁测试在Linux跳过，失败/错误0；覆盖率85.36%。
新增20项及原冻结测试在远端均实际执行通过。本机Windows完整回归的最终统计记录于交付收据。
初轮本机全量的3075通过/1失败日志保留：根`.gitattributes`也在470冻结路径中，故其新增规则被原测试拒绝。
最终恢复根文件，将规则改为仅匹配新文件的目录属性；冻结清单、原测试及正式门槛未修改。
独立复审另核对全部4970既有路径属性不变，结果见[独立复审收据](evidence/pit-effective-membership-evidence-v1/independent-review.json)。

## 定向获取与授权建议

本轮三个研究子代理合计14次搜索、2次页面/文档解析；搜索出现429后停止，无重试、身份替换或
重新访问此前403的CSI正文。新网络结果是工具表示，没有新发行方原字节，未将其冒充原PDF/HTML。
既有原件留在忽略目录，公开内容仅为来源链接、摘要、候选身份事实和必要审计字段。

[CIIS官方基本面数据产品页](https://www.ciis.com.hk/hongkong/sc/idata/csifundamentaldata/index.shtml)
区分当日收盘、次日开盘、拟调入。第三种口径不能证明实际纳入。页面介绍支持授权申请路径，
但2021回溯覆盖、完整临时链和历史vintage仍需书面确认。没有发送邮件、购买数据或申请付费权限。

下一次数据需求应直接给指数公司、CIIS或已授权供应商：

1. `000905`在2021-09-10收盘、9月13日开盘、9月27日收盘、9月28日开盘的完整成员文件，
   每份独立唯一计数、有效时点及葛洲坝退市至中国能建上市的处置说明。
2. 13888对应2021-12-10收市前/后及12月13日开盘成分，实施确认、改期/撤销/更正记录，
   逐项调入调出边界；不得只提供计划调整表。
3. 研究窗内全部临时、条件、更正事件和证券历史身份/代码变更/退市映射，区分有效时间与当时可知时间，
   明确时区、文件版本、生成时间、公开时间及历史版本保留政策。
4. 明确内部研究、原始字节留存、离线CI及独立复审使用，以及公开来源索引/哈希/必要摘要的许可范围。
   未获授权的原材料不进入Git或CI产物。

取得具体新材料或授权状态改变前，停止对同一批预告的重复审计。旧14因子、39候选、Golden、
正式资格规则、Forward及交易代码均不在本分支修改范围。NO LIVE MONEY。
