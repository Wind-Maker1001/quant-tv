> Publication note: this is a path-redacted historical copy. Original hashes and public-copy hashes are listed in [the publication record](evidence/pit-publication-20261018-v1/README.md). Historical PASS results describe their original execution scope; they are not new certification.

# 数据审计与PIT验收成果迁移至main

项目：`Wind-Maker1001/quant-tv`。分支：`codex/pit-evidence-release`。日期：2026-10-18（Asia/Shanghai）。**NO LIVE MONEY**。

原归档提交`dbc5db408a66e8711ff8c99da446d330ef8513ef`已在独立worktree上以`cherry-pick -x`迁移。本轮获取的`origin/main`基点为`cac65a79a42bcb6c1d322180fd192a3e100c4b9c`；迁移提交、43份交付文件清单及逐文件SHA/Git blob对照见[迁移收据](evidence/pit-release-migration-20261018-v1/validation.json)。无cherry-pick冲突；原43份交付文件保持字节一致。另新增本说明、迁移检查器、收据、本地PR草稿及仅作用于该附件目录的字节规则，共5份迁移说明文件。

独立worktree位于`data/research/pit-release`（相对原工作区）。它在已有忽略目录内，不改动原分支文件或未跟踪报告。原分支仍保留`dbc5db4`；未跟踪的`REPOSITORY_AUDIT_2026-10-15.md`保持原SHA，未迁移。没有推送、创建PR或合并。

## 与main已有工作的关系

main已包含[PIT有效成员证据](PIT_EFFECTIVE_MEMBERSHIP_EVIDENCE.md)、[完整基线审查](PIT_BASELINE_EVIDENCE_REVIEW.md)、[定期事件审查](PIT_REGULAR_EVIDENCE_REVIEW.md)、[条件事件审查](PIT_CONDITIONAL_EVIDENCE_REVIEW.md)，以及`universe/event_evidence.py`和CI优化。这些文件全部保留，没有用旧分支覆盖它们。

main的事件检查即使清单齐备也只返回`REVIEW_READY_NOT_CERTIFIED`；当前基线、13888实际实施及13420指数过渡仍UNKNOWN，与原归档的阻断方向一致。原报告仍是其原日期、原版本的审查，不扩展为对main所有后续资产的认证。main新增的TDX质量、公司行为可行性和CI材料属于独立证据范围，本轮没有重演或改写其统计/结论。

## 旧收据保留及适用范围

| 历史资产 | 本轮认定 |
| --- | --- |
| 原7份报告、计数、异常键、候选动作、源URL/SHA、规范及30类负例设计 | 原样迁移；文件一致性重验不等于重扫行情或重新认证金融事实 |
| `audit-pit-release-20261018-v1/verify_release.py` | 在全新main worktree以Python `-I -S`实际运行通过；仅覆盖原41个绑定工件和135份既有研究文本，不覆盖main新增模块的全部功能 |
| 原`offline-checks.json`的106通过和旧`clean-checkout-verification.json` | 属于旧提交/旧执行环境；保留原值，不改成此次main运行。此次回归另记在迁移收据 |
| `verify_spec.py` | 原580份文件、私有原件和旧HEAD约束仍适用；此worktree缺原件且HEAD已变化，完整重放NOT_RUN。不得修改旧manifest或写假成功 |
| `verify_phase1.py` | 缺忽略目录`start-preservation.json`及附件/搜索原件，完整重放NOT_RUN |
| `readonly_review.py`、`review_pit_evidence.py`、`assemble_phase1_delivery.py` | 行情/日历、缓存原件或固定输出依赖未交付；NOT_RUN，不复制原工作区忽略数据、不重扫、不下载 |

两份旧只读验证器在新worktree的实际缺证退出信息及原件依赖登记在迁移收据。它们的失败证明无法完成本次完整重放，不能作为原审查结论失真的证据，也不能包装为数据已通过。

## 本轮检查与复现

本轮重新检查43份文件的Git blob、SHA与类型，确认没有新增原始行情、受限PDF/XLSX、凭证或临时诊断。原始源文件只保留索引与哈希。既有异常明细是派生键/标签/计数；原统计内容未修改。凭证检查仅为明确记录的有限模式检查，不称安全认证。

main相对本分支的研究代码、14个因子、模型、参数、配置、全部研究测试及CI工作流/脚本保持原Git树；只有原归档向根`.gitattributes`追加字节规则，既有规则保留。迁移新增的局部`.gitattributes`不作用于main其他目录。正式PIT每日500、研究窗口、SOURCE_BINDING、Formal/Forward及`live_trading:false`均未放宽。

离线回归覆盖原四个门禁模块，以及main新增的`test_pit_event_evidence.py`；实际结果和命令见迁移收据。它验证软件拒绝行为，不是实际500基线、有效日期或证券身份认证。完整研究CI与模型相关全量测试未在本轮执行；本轮没有训练模型或运行回测。

```powershell
python -I -S -B -X utf8 docs/research/evidence/audit-pit-release-20261018-v1/verify_release.py
python -I -S -B -X utf8 docs/research/evidence/pit-release-migration-20261018-v1/verify_migration.py
```

第二个入口需要本地Git及迁移收据中列出的Git对象，不能用于省略历史对象的浅检出。缺对象时应报错并保留NOT_RUN，不能略过比较。两个入口均只读，不联网、不写资格、不导入研究训练流水线。

PR建议：从`codex/pit-evidence-release`向main发起独立文档/证据PR，使用[本地标题与正文草稿](evidence/pit-release-migration-20261018-v1/PR_DESCRIPTION.md)，继续沿用main完整研究CI作为合并前工程检查。本轮只准备草稿，不发送至GitHub。
