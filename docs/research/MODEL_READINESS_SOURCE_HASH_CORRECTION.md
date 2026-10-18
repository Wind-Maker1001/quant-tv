# PR #11 源码摘要更正记录

NO LIVE MONEY。Formal / Forward 持续 BLOCKED。此修复只涉及独立诊断的源码身份和证据说明。

## 复现及原因

Codex Review 的P1成立：[原评论](https://github.com/Wind-Maker1001/quant-tv/pull/11#discussion_r4307694385)。
原始被审HEAD：`8407a347e38bf65ef8e2d0e4d8aeed24bb494500`，研究源码共138个Python文件。
修复前使用独立脚本逐文件读Git对象，并建立两个本地干净稀疏检出：
Windows配置`core.autocrlf=true, core.eol=crlf`与LF配置`core.autocrlf=false, core.eol=lf`。
不覆盖原工作树，不修改历史收据，不把LF配置的Windows检出冒称Linux运行。

旧算法为按路径顺序拼接`UTF-8 POSIX路径 + 原始文件字节`后做SHA-256，未声明换行合同：

| 视图 | 原始摘要 | 相对Git对象字节不同的文件数 |
|---|---|---:|
| HEAD Git对象 | `abad7e91e31fbd881b81ffaaa9a7766fe1bf26850ec802f83dff7c72dd0fc64f` | 0 |
| 原Windows混合换行工作树 | `c4c5e400ff44abdd968be10c81cd66e10fc8312422987ff7009d1e8c884a00c5` | 34 |
| 干净Windows CRLF检出 | `040f929cff8688f09d12ff7c5e206d8980adc30e098d56bce8c0fad9abae75ab` | 137 |
| 干净LF检出 | `abad7e91e31fbd881b81ffaaa9a7766fe1bf26850ec802f83dff7c72dd0fc64f` | 0 |

四个视图的文件集合相同，无缺失、无额外Python文件。逐文件只将CRLF改为LF后全部与Git对象
相等，旧算法的规范化摘要也全部为`abad7e91…`；非换行内容差异为0。原工作树34个差异文件
含CRLF或混合CRLF/LF；Git系统配置`core.autocrlf=true`，因此Git diff可为空而原始字节不同。
`universe/event_evidence.py`另有既有`eol=lf`属性，所以干净Windows有137个而非138个差异文件。

完整逐文件原始/规范化SHA、字节数、换行计数、文件集合与源码Git状态，保存在
[`original-head-forensics.json`](evidence/model-readiness-source-v2/original-head-forensics.json)。
文件中的`windows_crlf_lf_ordinals`记录每个原Windows文件哪些换行使用CRLF。独立回归从原HEAD
Git对象读取文件，按该映射重建原字节，逐文件核对原始SHA，最终精确重建`c4c5e400…`。
证明不依赖当前工作树仍保留旧换行，也不靠改写历史哈希使其匹配。

## 对旧证据的更正

`model-readiness-v1/`整体按原字节保留。其`source_sha256=c4c5e400…`是原Windows原始字节摘要，
不是Git对象字节摘要，也不是V2规范化摘要。旧index中的`source_verification`和
`source_verified_against_commit`所声称的“字节与提交一致”，在此明确撤回；当时的Git diff只能
支持Git规范化后的内容一致，不能支持原始字节一致。

本次逐文件映射建立了旧Windows字节与原提交的**事后LF等价验证**，不把新摘要填入旧报告。
旧的小规模/规模耗时、内存、预测SHA和JUnit仍属于原始实测。没有重跑旧500×1200性能测量，
也不把事后身份复核说成重新训练或重新测量。原V1未记录结束快照，故不能证明旧运行期间没有
短暂修改后恢复的源码变化；本次也不能补造这种历史观察。

## V2稳定合同

协议名：`factorlab-model-readiness-source-v2`。实现仅在
`qbot/research/diagnostics/model_readiness/source_identity.py`，不修改正式资格/模型/因子/统计或CI门禁。

1. 先将revision解析为完整提交，枚举该提交`qbot/research`下所有已跟踪的常规Python文件，
   扩展名`.py`按ASCII大小写不敏感匹配；路径保留大小写，使用POSIX分隔符，按UTF-8字节排序。
   Git对象通过cat-file批量读原始blob，固定到同一个不可变提交。
2. 源码须为UTF-8字节；只将实际CRLF转成LF，拒绝单独CR。不去BOM、不改Unicode规范形式、
   空白或末尾换行。逐文件记录规范化字节长度及SHA，路径、长度和SHA均进入清单。
3. 清单含固定`protocol/scope/normalization/files`字段，用
   `json.dumps(sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')`
   编码后做SHA-256。长度取规范化后的长度，原始换行信息不进入规范化摘要。
4. 工作树的Python文件集合必须与提交相同，拒绝缺失、额外文件（含ignored与`.PY`）、链接及
   非换行内容修改。逐文件比较规范化字节，不依赖Git diff。不同机器的原始换行可不同，但
   规范化内容摘要必须与Git对象完全相同。导出的无Git目录不能冒称提交绑定的运行。
5. `source-start.json/source-end.json`同时保存协议、完整提交、规范化摘要、原始兼容摘要及
   逐文件原始SHA。开始前校验；结束后再次校验，提交、规范化内容或本次工作树原始字节变化
   都使软件验收FAIL。默认CLI在比较测试子进程完成后再写`source-final.json`并复核。
6. `readiness.json`升级schema_version=2，环境明确记录source_hash_protocol；
   `source_sha256`现在代表该协议的规范化摘要，不能与未标协议的V1原始摘要直接比较。

开始/结束快照是边界观察，不能检测两个观察点之间修改后又完全恢复的变化。新的运行证据从
已提交源码的干净检出生成，额外降低这类不确定性；不声称提供持续文件监控或历史远程证明。

## 独立验证入口

```powershell
# 历史原字节逐文件重建；读取原提交Git对象，不需要信任当前工作树换行。
.\.venv-py39\python.exe -B -X utf8 -m pytest -q -p no:cacheprovider `
  tests/model_readiness/test_source_identity.py

# 仅当源码已提交且与HEAD内容一致时才生成新快照；有脏源码会直接失败。
.\.venv-py39\python.exe -B -X utf8 -m qbot.research.diagnostics.model_readiness.source_identity `
  --root . --output results/diagnostics/model-readiness/source-current.json
```

回归包括独立清单摘要参考、CRLF/LF一致性、真实内容/空白/BOM/末尾换行反例、缺失和额外
源码、ignored源码、裸CR/非法编码、运行内原始换行变化、提交变化、继承Git路由环境，以及
原138文件逐字节重建。新增干净检出验收、独立JUnit和正式CI见本目录后续验证收据，明确按
“原始实测”“历史身份复核”“修复后重新验证”分类，绝不复写V1哈希。
