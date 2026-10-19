# V8 日频索引日期与证券标识更正

NO LIVE MONEY；Formal/Forward BLOCKED，不自动合并。V1–V7 原始证据及哈希全部保留。

Codex 对 a2fbfca 提出 discussion_r4313720615、discussion_r4313720634。先在未修改的该 HEAD 保存两个失败反例，再修复。

市场状态复用原 build_market_regime_features，日期索引从显式 Session 时段的最后一个被观察瞬间推导：右开结束时刻减 1ns，取其 UTC 日期并转为无时区午夜。session_id 仅作为标识，不要求能被解析为日期，也不决定排序或日历日期；原始 ID、UTC 时段仍绑定 V7 的日历摘要。多个完成 Session 导出同一日频日期时明确 ContractError，禁止向原日频函数传入重复日期。该 UTC 索引是当前合成合同，不构成真实交易所交易日认证。

实际参与请求的有向边，其 upstream、downstream 必须均为非空、非纯空白字符串。空、数字、布尔及集合端点不能被计作确认关系，也不能在集合插入时抛出未控制的 TypeError。无关范围的边继续不进入所选输入。ComputeRequest 同时要求证券范围为非空唯一字符串序列，场景和 session_id 是明确的非空字符串，提前拒绝不可哈希证券标识。

新增不透明 ID、可解析但与时段无关／逆序的日期 ID、UTC 午夜右开边界、日频日期冲突、双方向异常端点及请求标识反例。完整回归、覆盖率源码清单、静态检查和三频率源码重放追加于 evidence/v8。默认合成 Session 原本与时段日期一致，V8 默认数值、原因、快照和输出哈希应与 V7 相同；独立比较保存其证据。32 个合同、14 个 MVP、5/15/30 分钟不变。安装包未验收，真实研究 REAL_RESEARCH_BLOCKED。
