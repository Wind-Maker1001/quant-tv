# 分钟工程独立验收派生证据

总体 CONDITIONAL PASS。软件合并须最新原研究和分钟 CI 同时通过，仅限工程/探索；金融研究准入 FAIL。NO LIVE MONEY。

本目录不含原始 OHLCV 行情、价格样本或本机路径；完整数值细节只在忽略诊断目录。

- `data-review.json`：独立回读 69 分区、64,115,523 行，原件 SHA、异常组、15:30 来源分布与机械敏感性。
- `temporal-review.json`：标签断点、号段回填观察、非零源贡献及浮点求和差异说明。
- `exception-groups.csv`、`raw-exception-lexemes.json`、`factor-neighborhood.json`、`negative-forensics.json`：逐类定位及保留处置证据，不含原始数值。
- `day-reproduction.json`：仅一个完整日的原版本/修复版本字节一致性，全量数据未重转。
- `structure-boundary.json`：并行市场结构框架精确快照、实际拒绝探针及不可直接接入的字段缺口；未合并分支。
- `sources.json`：交易所官方来源、阅读范围及解析 Markdown SHA；不冒充已验证 HTTP/DOCX 原始字节。
- `ci-remediation.json`、`minute-ci-contract.json`：保留远端冻结门禁失败，完整命名空间迁移、断言等价、用例和覆盖契约。
- `test-results.json`：修复前红灯、修复后完整研究单次通过、定向与发布工具测试，以及原跨盘失败原因。
- `latest-main-review.json`：PR 创建后 main 前进的独立范围审查，保留本地测试旧基点与最新组合 CI 的区别。
- `invariants.json`：原数据清单 SHA、69 分区类型、原审计绑定及正式/Forward 门禁不变证明。

方法、完整命令与适用范围见 [独立验收报告](../../YHH_30M_INDEPENDENT_ACCEPTANCE.md)。
历史生产报告及收据保留原义，当前读取校验加固不重写其生产源码 SHA。

当前 CLI 及导入入口见 [当前工程用法](../../YHH_30M_CURRENT_USAGE.md)。历史生产报告与摘要不改签。
