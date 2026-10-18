# 源码身份更正与重新验证（V2）

NO LIVE MONEY。Formal / Forward 均 BLOCKED。V1目录原字节未改，其Git目录树仍为
`79bcd31d025127d76c1b23b7e4440e20150e946c`。

| 证据 | 分类 | 结论 |
|---|---|---|
| `../model-readiness-v1/` | 原始实测 | 原耗时/内存/预测保留；未重新测量500×1200 |
| `original-head-forensics.json` | 历史身份复核 | 原138文件，34个原工作树字节差异全为CRLF/LF；可精确重建原始`c4c5e400…` |
| `historical-equivalence.json` | 更正/限制 | 撤回原raw字节匹配Git的声明；记录旧规模HEAD缺少5个诊断源文件；原运行内源码漂移未记录 |
| `current-head-views.json`及三个视图JSON | 修复提交身份复核 | 受测提交`4bec2efcc3db9ca2aed2f9b1c8986b498fd2ad06`的139个源文件，Git/原Windows/干净CRLF/干净LF规范化摘要一致 |
| `canonical-reference.json` | 独立算法复算 | 不导入FactorLab生产哈希实现，从Git原始blob独立构造公开V2清单，复算同一摘要 |
| `regression.xml` | 从已提交源码重新验证 | 干净CRLF稀疏检出，85 passed，无跳过/失败 |
| `revalidation/` | 从已提交源码重新验证 | 干净LF稀疏检出，完整小规模入口PASS；含61项比较反例及开始/结束/子进程结束源码快照 |
| `infrastructure-attempt.json` | 失败尝试说明 | 初次比较子进程被Windows沙箱目录权限阻断；原输出保留在工作区，新目录获准重跑 |

V2协议`factorlab-model-readiness-source-v2`规范化摘要为
`fd4487a10a25253bf581035720e3e7e95996f44854cc1b4513fd3e51f9ac5505`。
这里的`current-head-views.json`记录的是生成时的修复提交，不冒称未来新增证据文档提交已经被重新运行。
源文件在后续证据归档提交中保持不变；Git完整提交身份与规范化内容摘要分别记录。

新的四模型预测表SHA及两级回测结果SHA都与原小规模实测一致。此比较只证明本合成场景的结果
未因修复改变，不代替新500×1200实测，也不授予金融数据资格。

`source-start.json/source-end.json/source-final.json`逐字节一致；清单同时保留Git与工作树原始
摘要，不能将CRLF/LF不同的原始摘要当成V2内容摘要比较。不同检出中原始摘要可不同，V2摘要
必须一致。完整合同和复现命令见[更正记录](../../MODEL_READINESS_SOURCE_HASH_CORRECTION.md)。

这两个新检出均运行在Windows，LF检出不是Linux运行。原正式CI继续验证冻结原套件；新增85项
独立套件另行运行，正式CI与Codex重新评审的最终状态见[PR #11检查](https://github.com/Wind-Maker1001/quant-tv/pull/11/checks)。
目录`.gitattributes`保留原始证据字节，`index.json`保存归档文件SHA。

可从仓库根目录独立复算受测实现：

```powershell
.\.venv-py39\python.exe -B -X utf8 `
  docs/research/evidence/model-readiness-source-v2/recompute_canonical.py `
  --repository . --revision 4bec2ef --output results/diagnostics/model-readiness-source-v2/independent.json
```
