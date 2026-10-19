# 复审追加两项 P2 与 V3 证据

NO LIVE MONEY。Formal/Forward 保持 BLOCKED，不自动合并。V1 与 V2 的证据和收据全部保留原字节；本轮追加 V3。

Codex 对 f1a4eb3 的复审未再次报告原三项，另提出以下两项。先在未修改的 f1a4eb3 产品源码上执行最小反例，得到 2 failed，并保存 red-phase JUnit、源码哈希和执行收据。

- discussion_r4310349352：同一实际引用的资金定义 ID、版本下，所有当前可知记录都必须满足相同的供应商、单位、币种定义。任一冲突即阻断该版本，FLOW_NET_ACTIVE_RATIO 返回缺失与 BLOCKED_SOURCE_DEFINITION；不能由另一条合法记录使其获批。完全一致的多份证据可共同支持定义，不相关版本不参与审批。新增顺序无关、供应商/单位/币种冲突、未来才可知冲突及一致重复证据测试。
- discussion_r4310349355：市场单值时间序列没有证券截面的配对覆盖率。其有效窗口比例改为与 minimum_window_coverage 比较，独立于 minimum_pair_coverage；同时保留最低有效窗口数与交易日要求。新增两个阈值不相同时的正反例及窗口覆盖阈值边界测试。

本轮继续显式执行原 55 项、第一轮 52 项以及追加反例与边界测试；实际结果见 evidence/v3/acceptance.json、JUnit、覆盖率源码清单和静态检查收据。所有 32 个候选、14 个 MVP、5/15/30 分钟、Python 3.9 源码入口及安装包未验收限制保持不变。V1 源码重放及 V1/V2/V3 摘要比较证明默认合成特征值不变；新边界行为只在对应冲突或单独配置的诊断阈值下生效。

正式配置、原 14 因子、39 候选、四模型、PIT/HFQ、Forward、Legacy、model_readiness 和正式 CI 门禁均保持原字节。最终远端 CI 与 Codex Review 仍须针对最终 HEAD 确认，本地收据不预先声明外部审查通过。
