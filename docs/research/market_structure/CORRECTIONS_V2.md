# PR #13 三项 P2 更正与 V2 验收

NO LIVE MONEY。Formal/Forward 持续 BLOCKED，真实研究为 REAL_RESEARCH_BLOCKED。不自动合并。本文件及 evidence/v2 为追加更正；evidence/v1 全部文件保持原始字节与原哈希，不把 V1 的软件验收解释为已经覆盖本轮三个反例。

审查主体为 b30256dd9e24c3db99be5d63d4b3b4d9113b0872。三个最小反例先在该提交完全未变的 10 个产品源码文件上执行，实际结果为 3 failed；red-phase JUnit、原始日志、解释器、命令和源码哈希见 evidence/v2/red。原始 Windows 日志按原字节保存，相关字符使用当时系统代码页。

## P2-1：成对完整样本的 Spearman

对应 discussion_r4310212806。原实现先独立排名，最小反例得到 0.9819805060619659，正确值为 1.0；这可以改变高相关拒绝状态。

现在每个原生日内窗口、每一对特征先形成共同有限值掩码，再在交集内计算平均并列秩，交由原数值内核计算相关系数。排名帧保留原始全部实体和窗口；配对数量、覆盖率和缺失掩码仍从原始数值帧取得，不通过删行提高覆盖率。原 factor_discovery 未修改。

独立标量参考不使用产品排名实现，分别计算平均秩和相关系数，逐对、逐窗口核对数值、有效窗口数及状态；包含不同掩码、非配对极值、并列秩、常数、样本不足、配对覆盖不足及阈值等于/上下边界。市场单值时间序列路径原已在共同有效样本中排名，保持该边界。

## P2-2：按合同建立实际依赖

对应 discussion_r4310212810。compute_features 根据所选 FeatureSpec.required_inputs 的并集决定是否读取分钟、资金定义、行业、概念及供应链。九项 MVP 的来源合同从家族级宽泛清单细化为实际输入，definition_version 标记 v2-inputs；32 个候选 ID、14 个实现、公式、粒度及三个频率保持不变。

归属数量与关系数量不要求分钟数据；市场广度和成交集中度不读取分类或资金定义；仅请求资金时不读取分类及关系；仅请求供应链时不读取行业或概念。资金只读取本次分钟实际引用的定义 ID 与版本，关系读取与所选方向及请求证券相关的边。实际依赖的权重、历史版本、证据及资金定义继续严格校验。

FeatureResult.source_trace 声明每个所选合同的输入，并列出实际使用的事实 ID、修订、种类和 SHA-256。selected_input_sha256 仅绑定本次特征使用的记录。市场状态通过独立 include_market_context 开关处理，默认保留上下文，并用 context_records/context_input_sha256 单列来源；整体 snapshot_id 同时绑定两部分。

同一特征在单独请求和混合请求中的数值、原因、覆盖率相同。混合请求的特征来源追踪是所选依赖的并集，其整体输入摘要及快照 ID 可以与单独请求不同。追加无关分类、关系或资金定义不改变原特征值、缺失原因及输入摘要。改变可用的市场上下文可以改变整体快照，但不会改变特征输入摘要。

## P2-3：明确股票池及精确快照的广播

对应 discussion_r4310212817。ResearchFeatureAdapter.build_view 增加 target_index，市场级特征需要 broadcast_market=True 和非空明确目标，不能从无证券行的市场输入推导股票池。

target_index 必须包含 entity_id、scenario、frequency、session_id、observation_start、observation_end、as_of、decision_time。同一证券在同一快照中唯一；多个窗口可重复使用同一证券。时间必须带时区且满足完整窗口与历史决策约束，频率只能为 5/15/30。无目标、重复目标、缺少键、无法匹配的来源快照均抛出 ContractError。证券特征单独使用时，保留从已选择证券行推导目标的兼容入口。

每个输出特征列只允许一个明确 namespace；多 namespace 输入必须通过 feature_namespaces 显式选择。目标索引不承担分类 namespace 的隐式选择。连接使用全部历史键，不把缺少整条市场记录误当成缺失值；存在记录但其值为 NaN 时保留 NaN 并广播到每个明确目标。原始市场数值不变，另输出 `<feature_id>__broadcast` 标识及 broadcast_features/feature_namespaces 属性。

## 独立证据与 V1/V2 差异

本轮显式运行新增定向测试、原 55 项回归、以全部新源码为目标的分支覆盖率及源码清单、Python 3.9 语法编译和 flake8 E9/F63/F7/F82。实际结果、被测提交和命令见 evidence/v2/acceptance.json、JUnit、coverage-source-inventory.json 及静态/CLI 收据。正式 CI 不包含新独立目录，不能替代这些证据。

V1 使用 b30256d 的 Git blob 导出源码并独立重放，核对旧完整输出摘要确实匹配原收据；再与 V2 去除 selected_input_sha256/snapshot_id 的输出逐值摘要比较。特征值和缺失原因保持一致。完整输出摘要会因特征与上下文输入分离及快照绑定变更而改变；合同目录摘要会因精确依赖及版本标记改变。Spearman 窗口的实际差异另见 v1-v2-comparison.json，不覆盖 V1 相关性或原哈希。

V2 仍只说明 SOFTWARE_MVP_SUCCESS / REAL_RESEARCH_BLOCKED。无 __init__.py 的命名空间不变；find_packages 遗漏及安装包未验收限制继续适用。最终远端 CI 与重新请求的 Codex Review 以 PR #13 对最终 HEAD 的实际记录为准，V2 本地收据不预先声明远端已通过。
