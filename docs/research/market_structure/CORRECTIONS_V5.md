# V5 更正与获准同步 main 的验收

NO LIVE MONEY。Formal/Forward 持续 BLOCKED，不自动合并。V1–V4 原始证据及哈希保持原字节，追加 V5。

Codex 对 e6d48d1 的复审新增 discussion_r4313275912 与 discussion_r4313275919。先在合入 main、但市场结构源码仍与被审查版本逐字节相同的 5db02fb 上保存两个失败反例，再修复：

- 未请求 minute_amount 时不生成金额守恒断言；请求金额时区分 VERIFIED 和 INCOMPLETE_AMOUNT_COVERAGE，实际零成交额与未知金额有不同状态。
- 供应链要求活动范围具有明确且一致的 namespace、taxonomy_version。不同范围不能合并为完整图；一致的重复证据可以保留。输出使用实际范围 namespace；显式标注范围的边必须完整且匹配，无范围时返回缺失。未来才可知的冲突不能改变原快照。

用户另行明确授权同步最新 main，合入 f1ad2d4f05d7676f9d49e23af9a8e0ec0615e19e，合并提交为 7fb1f1e53755f5655c19d31f3aa0697c8cdd0b74；初始固定基线 39eecf8 及其历史验收记录不改写。同步后 134 项原独立回归通过，实际 Python 3.9 源码三频率 CLI 运行成功。

新 main 的分钟发布门禁对整个 PR 扫描，尝试将 V2 原始 red-phase 日志按 UTF-8 解码，造成跨模块失败。用户明确授权兼容修复：仅该分钟门禁显式选择 --scope-yhh30m；发布扫描报告所属路径与范围外路径，所有原分钟测试、源码合同和覆盖率校验保留，正式门禁变动仍全局检查。review_yhh30m_release 的默认完整扫描行为保持严格。该例外只修改新分钟 workflow 和其发布检查脚本，不修改原正式 CI、分钟实现、分钟测试或其历史合同。7 项新兼容用例修复前 6 失败、1 通过，修复后与原发布检查合计 15 项通过；原完整分钟工程测试 42 项通过。准确触发解码失败的文件是 evidence/v2/red/red-tests.log，不是 V1 日志。

本轮完整回归、源码 XML/JSON 覆盖清单、静态命令、三频率运行、32 项合同状态、历史证据保护及 SHA-256 清单追加于 evidence/v5。源码运行验收不等于安装包验收；命名空间继续无 __init__.py，find_packages 可能遗漏，wheel/安装后入口 NOT_VALIDATED。合成结果不支持预测收益能力或可交易 Alpha 声明。SOFTWARE_MVP_SUCCESS 与 REAL_RESEARCH_BLOCKED 同时适用，远端 CI 及 Codex Review 按最终 HEAD 单独核对。
