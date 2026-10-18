> Publication note: this is a path-redacted historical copy. Original hashes and public-copy hashes are listed in [the publication record](evidence/pit-publication-20261018-v1/README.md). Historical PASS results describe their original execution scope; they are not new certification.

# 2026-10-17—18数据审计与PIT验收成果归档

项目：`Wind-Maker1001/quant-tv`；分支：`codex/five-year-data-feasibility`；**NO LIVE MONEY**。
归档基点：`d9f42d6524055db029a34ccab888d1c93460d5ae`。

本次提交归档报告、检查程序和派生诊断证据，补充可在干净检出中运行的只读检查。**历史PIT与正式研究仍阻断**；资料归档、文件哈希和软件回归均不构成金融数据认证。

## 纳入范围

| 文件/目录 | 用途及认定范围 |
| --- | --- |
| [INDEPENDENT_DATA_REVIEW_2026-10-17.md](../../INDEPENDENT_DATA_REVIEW_2026-10-17.md)及`evidence/independent-data-review-20261017-v1/` | 历史行情审计结论、计数、异常键定位、原输入哈希和复核程序；不是原始行情 |
| [PIT_PHASE1_EVIDENCE_2026-10-18.md](PIT_PHASE1_EVIDENCE_2026-10-18.md)及`evidence/pit-phase1-20261018-v1/` | 14个候选事件及1008个候选动作、来源索引、身份草案和补证清单；不宣称完整历史链 |
| [EXTERNAL_PIT_ACCEPTANCE_SPEC_2026-10-18.md](EXTERNAL_PIT_ACCEPTANCE_SPEC_2026-10-18.md)、[TEST_PLAN](EXTERNAL_PIT_ACCEPTANCE_TEST_PLAN_2026-10-18.md)及`evidence/external-pit-acceptance-20261018-v1/` | 外部输入字段、500基线、13888集合差、代码映射、30类拒绝案例及历史一致性收据；真实样本验收未执行 |
| 根目录`AUDIT_SUMMARY_2026-10-17.md`与`STRICT_AUDIT_REPORT_2026-10-17.md` | 作为独立复核所对照的原审计意见快照保留。其评分、环境及“可用”断言不因入库而获认证；冲突认定以独立复核证据为准 |
| [本轮清单与检查器](evidence/audit-pit-release-20261018-v1/) | 纳入/排除清单、原始依赖登记、离线检查和干净检出收据 |
| `.gitattributes`追加规则 | 冻结上述成果字节，避免Windows/Linux换行转换破坏收据哈希；不改变研究配置或门禁 |

逐文件清单、字节数及SHA-256见`evidence/audit-pit-release-20261018-v1/release-manifest.json`。派生证据中最大的异常明细约3.75 MB，只含异常证券键、时间标签、列名和计数；未包含原始OHLCV行情。既有报告和收据原样保留，没有改写先前结论或把旧验证时间冒充本轮执行。

## 排除范围

- `<EXTERNAL_MARKET>/`中的年度ZIP、日内CSV、下载来源审计文本/脚本：外部本地输入，不提交、不重扫。
- `data/research/`和`results/diagnostics/`中的公告/附件原件、PDF/XLSX、浏览器容器、完整搜索返回、采集收据、视觉核验与临时诊断：保留现有忽略规则，只提交来源URL、原件哈希和轻量审查索引；本轮不取得或扩张再分发权限。
- `REPOSITORY_AUDIT_2026-10-15.md`：早于本轮范围，保留为未跟踪本地文件；旧保全清单对它的引用继续保留，不能在干净检出中声称已复验。
- 凭证、账户配置、环境目录、pytest临时文件、干净导出目录及重放日志不提交。本轮对拟提交文本做凭证模式检查；这仅是有限检查，不宣称完整安全认证。

历史清单里出现本地绝对路径，是原执行环境的定位信息，不是便携访问路径。本轮另登记可重定位的仓库内依赖；外部路径不静默改写或补齐。已经由旧提交跟踪的试点原件/测试夹具未新增、改写或删除；其历史哈希检查可能需要LFS内容，不能将指针当原件。

## 干净检出的推荐检查入口

仅需Python 3.9或更高版本标准库，不需供应商账号、网络、行情、pandas或git元数据。可从任意当前目录运行：

```powershell
python -B -X utf8 docs/research/evidence/audit-pit-release-20261018-v1/verify_release.py
```

检查器核对提交工件的精确字节哈希、程序语法、研究代码/配置的文本哈希、已提交统计表内部对账、候选事件及UNKNOWN保留。研究代码文本哈希明确以CRLF→LF后的字节计算，以适应跨平台文本检出；它不是正式资格实现哈希。归档证据采用`.gitattributes -text`，必须精确字节一致。

原始证据重放与金融事实认证单独输出NOT_RUN。缺文件、工件哈希不符、JSON/CSV对账失败或研究合同变化会使该入口退出非零；不会静默跳过其所声称检查的提交工件。提交后的HEAD可以变化，检查器不会要求仍停留在审计前HEAD。

## 旧程序的依赖和不可复现部分

| 程序 | 干净检出状态 | 必需但未随本包交付的输入/其他限制 |
| --- | --- | --- |
| `independent-data-review-20261017-v1/readonly_review.py` | **NOT_RUN** | 需外部行情、来源目录5个审计文件及本地`data/research/five-year-pilot/.../calendar.csv`；依赖NumPy/pandas。会全量扫描，故本轮不执行 |
| `pit-phase1-20261018-v1/review_pit_evidence.py` | **NOT_RUN** | 需`source-index.json`中的发布者字节/缓存收据、部分PDF；依赖pandas/openpyxl/pypdf及现有qbot解析器。输出必须是新目录 |
| `pit-phase1-20261018-v1/assemble_phase1_delivery.py` | **NOT_RUN** | 需忽略目录的搜索返回、新旧PDF/收据和提取/视觉记录；固定输出位置排他创建，已有归档不能原地重建 |
| `pit-phase1-20261018-v1/verify_phase1.py` | **NOT_RUN** | 首先读取忽略目录`start-preservation.json`，随后仍需原始附件、搜索归档等；无这些材料不能完成原件验证 |
| `external-pit-acceptance-20261018-v1/verify_spec.py` | **NOT_RUN（作为提交后完整重放）** | 要求全部580份旧文件、原始附件且HEAD精确等于原审计前提交；提交后即使其他条件齐备也会拒绝。保留为历史检查器，不修改或伪造旧收据 |

精确路径/已记录SHA和涉及程序见`dependency-inventory.json`；缺失列表是依赖登记，不是已验证原件列表。新入口只复核已提交范围，不会替旧程序产生假的成功收据。干净导出还实际运行了两个只读旧验证器，失败结果单独记录，用来确认上述限制。

## 本轮离线结果及边界

`offline-checks.json`记录实际命令、回归结果和失败尝试；`clean-checkout-verification.json`记录从Git暂存树导出的检查环境、完整提交工件及受保护代码检查结果、旧验证器缺证结果。导出只含验收所需Git路径，不包含忽略目录、外部行情或本机环境目录；它不是新建依赖环境或跨平台实测。Python使用现有3.9环境；新检查器另以`-I -S`运行，排除环境路径与第三方site包。

门禁回归覆盖来源绑定、每日500/窗口、历史身份、正式入口拒绝synthetic、Forward合同和严格PIT导入。此前测试尝试曾因临时父目录缺失及沙箱临时目录WinError 5失败；后续使用已批准的沙箱外离线测试，不把初始化失败写成业务通过。

本轮不训练、不回测、不执行交易，不改变模型、因子、研究窗口、正式资格或Forward状态。本地提交不自动推送、合并或创建PR。

未解决：2021-09-13权威完整500基线、候选调样的实际生效及当时版本/可知时间、完整历史调整链、合格历史证券身份，以及其余来源绑定/状态/复权等正式门禁。规范的30类拒绝案例仍是设计，未变成真实证据验收成功。
