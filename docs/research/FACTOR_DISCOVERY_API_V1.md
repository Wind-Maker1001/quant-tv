# 自动因子发现 v1 接口冻结

基线 `48ea4dd8c1876c1515f3172c9bb2e812f20ebe82`，研究 CI 38540055000 与静态 CI 38540055327 均 SUCCESS。旧研究入口、14 因子、Golden、数据资格、Forward 与交易实现只读。NO LIVE MONEY。

共享定义仅由主代理修改：`factor_discovery/contracts.py`。Node 使用内部数据结构，Field 的 value 为白名单名称，Const 的 value 为有限固定尺度数；时序参数在 param；args 必须为 Node 元组。禁止 Python 表达式解析执行。配置不可变，白名单和预算必须写入收据。

- engine.py：`compile_expression(node, config=DiscoveryConfig(), require_dimensionless=True) -> CompiledExpression`；`normalize_ast(node) -> dict`；`ExpressionEngine(bars, calendar, config=DiscoveryConfig(), universe=None)`；`compute(compiled) -> ExecutionResult`。返回值按原输入 index 对齐。`panel` 为证券×显式日历的密集无填价网格，用于旧因子只读计算。维度提供 `as_dict()` 及 `is_dimensionless` 属性。构造输入不读取标签。缓存为单次 engine 内共享子表达式缓存；静态及实际预算失败为 BUDGET_EXCEEDED。
- generator.py：`generate_candidates(config=DiscoveryConfig()) -> GenerationResult`，属性 records（dict 列表）、stats（计数 dict）。每条包含 candidate_id、generation_sequence、family、meaning、original_expression（字符串）、node、compiled、status（GENERATED / EXACT_DUPLICATE / REJECTED）、rejection_reason、duplicate_of。先有限模板枚举、编译及结构去重，再按冻结顺序截断；禁止传入数据、标签、分区。
- evaluation.py：主代理负责，按开发信号日期与成熟 entry/exit 日期遮罩标签，复用 preprocess_cross_sections 与 evaluate_factors 的数学。
- redundancy.py：主代理负责，逐日 Pearson/Spearman 与配对覆盖，统计仅开发窗口；结构重复、数值相同、高冗余、不冗余与证据不足分开记录。
- runner.py / synthetic.py / report.py / receipts.py：主代理负责合成运行、私有只读合同适配、公开安全报告和独立版本收据。公开输出不含真实证券级数据。
- 子代理仅写明确拥有的新文件；接口变更先联系主代理。测试由独立代理补充，主代理重新执行集成与全量回归。源码与旧产物的未修改性由 Git 差异校验。

新输出 Schema 为 FACTOR_DISCOVERY_EXPLORATORY_V1；purpose=EXPLORATORY，qualification=UNVERIFIED，formal_admission=false，forward_allowed=false，live_allowed=false。完成状态 SOFTWARE_MVP_SUCCESS 与真实数据 SUCCESS / NOT_RUN / BLOCKED 分开，合成来源 SYNTHETIC_TEST_ONLY。报告、CSV、规范表达式及收据进入新版本目录；耗时与运行身份不参与确定性数值哈希。

集成审计补充的资源字段由主代理单独加入：max_cache_bytes=134217728、max_diagnostic_records=500000。缓存字节和潜在诊断记录在分配前检查，评价及冗余还按整次运行 deadline 检查；避免只有 AST 上限却生成巨量逐日配对记录。失败保留明确 BUDGET_EXCEEDED / FAILED 收据。
