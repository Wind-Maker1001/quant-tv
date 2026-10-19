# V5 发布字节与 Windows 运行字节的补充核对

V5 delivery-manifest.json 记录实际被测 Windows 工作树字节，原文件及其 c4ef33d8… 哈希不改写。

获准修改的 minute-data-evidence.yml 与 review_yhh30m_release.py 沿用仓库原有文本属性：Windows 工作树为 CRLF，Git blob 为 LF。逐字节核对证实只有换行规范化差异。其余 V5 清单文件的工作树和 Git blob SHA-256 全部相等。

git-blob-manifest.json 追加发布对象哈希和这两个文件的工作树／Git blob 对照，并包含原 V5 清单自身的发布哈希。其主体提交明确记录为 9b82b77；后续仅追加本补充证据，市场结构源码与被测 f69c54c 一致。该补充不替换 V1–V5 的原始收据，也不重新定义它们的哈希范围。

安装包仍未验收，REAL_RESEARCH_BLOCKED、Formal/Forward BLOCKED、NO LIVE MONEY 和不自动合并的边界不变。
