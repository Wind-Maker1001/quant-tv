# PIT证据归档公开副本与隐私检查

NO LIVE MONEY。该PR归档43份原交付文件和5份迁移说明工件的公开副本，另附本目录控制文件及限定归档目录的字节规则。根`.gitattributes`保持main原样，不作为本PR变更。

发布前已核对初始HEAD为`f183c6502a135fc8ed7814f0b7ebeee968e33273`且worktree干净。检查发现9份历史文件含本机绝对路径，因此不能将该提交及其历史直接推送。本地保留原始提交，从记录的main基点建立仅含脱敏副本的发布历史；不会推送私有来源分支，也不会将含路径的原提交作为远程发布分支祖先。

`manifest.json`逐文件保留原始SHA-256与公开副本SHA-256。路径分别替换为`<REPO>`、`<EXTERNAL_MARKET>`等标记；受影响报告加历史范围说明。历史JSON中的数字、布尔值及统计结果未变，原始来源哈希不变；本轮不重写原审计结论。原始本地文件及提交仍保留，公开副本不是那些私有原件的逐字节副本。

原清单、保全记录和收据内的旧哈希仍指向**历史原始字节**，不能直接用来校验本次脱敏文件。两个公开版本入口`verify_release.py`及`verify_migration.py`改为明确的公开范围适配器；原实现SHA在发布映射中。它们输出公开副本一致性检查，并将原始字节/私有Git历史完整重放标记NOT_RUN，不制造旧验证成功。

```text
python -I -S -B -X utf8 docs/research/evidence/pit-publication-20261018-v1/verify_publication.py
```

新入口校验本次公开文件的字节哈希、绝对路径及有限凭证模式、Python语法、原研究文本合同、已有派生统计对账及PIT未知状态。没有读取行情、第三方附件或本机原始证据，不联网、不生成成员数据、不训练模型、不生成交易信号。

历史PIT完整基线、实际生效日期、历史证券身份和完整调整链仍未认证。Formal/Forward继续BLOCKED。历史收据中的PASS仅描述原执行范围；本次GitHub CI验证属于软件工程验证，不能替代金融数据认证。

GitHub分支保护查询若受账户计划或权限限制，须在最终PR摘要明确报告，不能将403解释为已验证没有保护。此PR不自动合并，不修改保护规则、既有研究测试断言或研究门禁。

## 首次CI失败与修正

首次发布提交`6fc2670`的研究CI运行`39054638924`实际结果为3140通过、1失败、1跳过、2个网络用例取消选择。失败项是原研究冻结保护：根`.gitattributes`新增规则改变了冻结字节，属于本PR引入的问题。原失败运行及产物保留，不重写为成功。

修正恢复main根规则，将新增归档目录的字节规则放到`docs/research/evidence/.gitattributes`，只作用于4个新归档目录。未修改冻结清单、测试断言、CI或Formal/Forward门禁。根报告和研究目录Markdown采用Git原有文本换行策略：发布映射中标记`LF_CANONICAL_TEXT`的SHA按CRLF转LF后计算；其他工件仍按原始字节计算。原始SHA及旧统计结果保持原义，未将历史收据升级为本次验证成功。

## PR #10审查修复后的验证范围

公开扫描器按路径起点识别任意POSIX根目录、Windows盘符及UNC路径，不依赖预设挂载目录。网络URL、相对路径、研究日期和脱敏占位符保留；JSON键和值以及Python字符串会解码后检查。历史组装器中明确追加到`relative_to(...)`表达式的文件名后缀按相对片段处理，普通字符串拼接不享有该例外。路径扫描独立于公开哈希检查：重新计算公开哈希不能授权本机路径。

`verify_migration.py`先验证公开副本，再读取未改写的迁移收据，核对原始哈希绑定、43份交付文件在来源和cherry-pick提交中的blob及实际字节、父提交、迁移改动范围、私有发布来源中的原收据与原验证器，以及五个受保护main树。当前脱敏发布历史不要求包含私有cherry-pick祖先；原始Git对象仅作为本地只读依赖，不联网获取，也不推送它们。

成功输出仅限`PASS_RECORDED_GIT_OBJECTS_ONLY`；`full_migration_verification`始终保留`NOT_RUN_PRIVATE_ORIGINAL_EVIDENCE_REQUIRED`。缺Git、缺对象、浅检出或缺收据时明确NOT_RUN并非零退出；收据、哈希、树或历史关系不一致时FAIL并非零退出。对象齐全但当前HEAD与记录main没有共同祖先，或共同祖先不是记录main，均属于历史不一致；真正缺失中间历史对象仍为NOT_RUN。公开检出缺少私有历史对象属于预期限制，不能用公开文件替代原件或修改旧收据使其通过。旧回归计数、旧PASS和原始SHA不代表本次重新执行结果。

新增回归放在`tests/evidence/`，保持受保护的`tests/research`树原样。`FactorLab research tests`工作流新增独立`pit-archive-evidence` Job，在面向main的PR及main推送时自动运行，也随非benchmark模式的手动工作流运行。原`Python 3.9 offline suite`仍执行原完整研究测试集合，测试范围及验收检查不变。

独立Job在干净检出中运行，PR事件检出并记录精确PR HEAD；使用Python 3.9.25及`dev/requirements-evidence-ci.txt`中的固定轻量依赖，直接执行`python -m pytest tests/evidence/test_pit_archive_verifiers.py -q --tb=short`并生成JUnit。测试退出码直接传播，不使用`continue-on-error`；每次运行保存真实通过、失败、错误、跳过数及耗时、精确commit SHA、JUnit和provenance产物。迁移用例只创建隔离的临时模拟Git仓库，不获取私有原始对象，不读取真实行情或执行正式回测。以下命令仍可用于本地检查；本地成功或旧HEAD的CI不能替代当前HEAD的远程执行证据。

验证器及本说明更新后，发布清单只同步这些公开文件的当前SHA和长度；原始SHA、原始长度、历史迁移收据及其哈希约束保持原义。旧收据包含CI目录的历史冻结树，不随新增Job重写，也不豁免树校验；本轮软件回归成功不能标记为历史迁移的完整重放成功。

```text
python -B -X utf8 -m pytest -q -p no:cacheprovider tests/evidence/test_pit_archive_verifiers.py
python -I -S -B -X utf8 docs/research/evidence/pit-release-migration-20261018-v1/verify_migration.py
```
