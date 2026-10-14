# 首次真实A股14因子统计审计交付

**EXPLORATORY · UNVERIFIED · HISTORICALLY_RECONSTRUCTED · NON_PIT_CONVENIENCE · NO LIVE MONEY · NOT FORMAL CSI500 EVIDENCE**

2026-10-14，Windows / Python3.9.25。已完成冻结数据输入复核、RankIC统计推断、市场状态差异敏感性与五分位A/B对照，输出[独立中文报告](evidence/exploratory-statistical-audit-v2/report.md)、10张CSV、4张PNG、[输入证据](evidence/exploratory-statistical-audit-v2/input_audit.json)及[公开收据](evidence/exploratory-statistical-audit-v2/receipt.json)。复现步骤见[使用说明](EXPLORATORY_STATISTICAL_AUDIT.md)。

## 版本与数据边界

main基线为PR #3合并提交 `64c72ab0aee49bba59dbf7449f2c8235c61fca2c`；其[完整研究CI](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38530507226)与[静态CI](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38530507234)成功后建立 `codex/exploratory-statistical-audit`。

原数据语义版本 `2f145d173f5ddc79d303f580bc4485241023ae3971d3b40a2e8fa6e3de2e3f5f` 不变。全部410源产物哈希通过，原计算源字节与冻结v2一致，证券级因子/标签/状态精确复算一致；每日IC、覆盖、状态及原A分位聚合重放一致。242信号交易日内，每因子236有效RankIC日，末尾六日未成熟标签保持缺失；315缺标签=尾部300+内部15。

审计实际计算代码提交 `bc8ee734e28aab2df70deca0b96e867bcaee6603` 的Git blob SHA与收据实际源字节SHA逐项一致。私有审计目录为 `results/exploratory/statistical-audit/8befac2d95f7f1c4`，17个私有产物均核验；公开包仅16个白名单派生产物，另加公开收据，实际证券成员表留私有。公开收据与Git暂存blob哈希一致，局部 `-text` 属性保留Windows/Linux checkout字节。

没有新采集、扩大股票数、训练真实四模型、方向翻转、状态或标签修改。正式FactorLab数学合同、Golden参考、金融数据准入/PIT/HFQ/Forward/交易守卫和原探索v1/v2发布目录均无差异。旧收据不覆盖，私有行情、供应商响应、证券级标签和账户信息不入PR。

## 审计结论

| 诊断 | 原始p<0.05数量（HAC5/HAC20/MBB20） | Holm后统计支持 | 解释 |
| --- | --- | --- | --- |
| 14因子日均RankIC | 0 / 0 / 0 | 0 | 未拒绝零不证明因子无效，也不证明有稳定预测能力 |
| 42状态差异 | 8 / 9 / 9 | 0 | 原始差异仅描述性，不作事后选择 |
| SIDEWAYS | 45有效日、8短区间、最长12日 | 无法可靠判断 | 小样本与区间重复不足，保留近似区间和限制 |
| 五分位A/B | 成员差集中于2025-12-22/23/24/25/26/29 | 不作显著性或盈利结论 | 只测量标签可取得性选择敏感性 |

HAC20/HAC5标准误比为0.9709–1.1444，MBB20/HAC20为0.9500–1.0459。三方法均保留完整实际时间轴，状态差使用指示变量回归及完整协方差；20日非循环重叠Bootstrap为2000次、seed20261014，不先压缩状态日期。

值得扩大到独立五年周期的隔离探索，重点解决方向稳定性、更多牛熊与震荡区间、超过20日依赖/结构变化、标签选择及生存者偏差。它不批准正式中证500五年四模型研究；历史PIT、逐日证券状态、HFQ合同和vintage资格仍需另外补齐。

## 软件与独立复核

- 新增定向32项通过；Golden原参考及审计联测353项通过，最终真实产物专项核验通过。软件夹具明确SYNTHETIC_TEST_ONLY，不冒充实证。
- 完整离线研究套件：2890 passed，2 network deselected，88 warnings，1002.23秒。JUnit无失败/错误/跳过；行覆盖率84.95%，coverage/JUnit验收通过，软件覆盖不代表金融认证。
- Python3.9语法、flake8 E9/F63/F7/F82、black检查、19项CI合同测试、pip check和架构smoke通过。
- 增量测试涵盖时间相关性、独立HAC计算、缺失日期、区块邻接、状态切换与协方差、样本不足、缺失/未成熟标签、退化推断、Holm固定族、来源/计算代码/产物哈希不一致、版本失败BLOCKED、成功包完整性、公开CSV列拒绝、私有成员不发布与正式/Forward拒绝。
- 三个子代理分别独立审查统计方法、安全合同和真实结果；来源/公开列合同发现的问题已修复。独立Bartlett双重循环与实现方差误差小于1.5e-18；独立Holm、3304个证券级Spearman、33880个A/B分位桶及私有成员复核一致。四张PNG逐张视觉检查，六标识完整。

远端状态以本分支当前HEAD的完整研究CI和静态CI为准，不能用基线main CI代替。交付提交后创建独立PR并请求审查；不启用自动合并，不自行合并main。最终PR链接、当前HEAD检查与审查请求保存在任务交付消息及本地独立完成证据中。

**EXPLORATORY · UNVERIFIED · HISTORICALLY_RECONSTRUCTED · NON_PIT_CONVENIENCE · NO LIVE MONEY · NOT FORMAL CSI500 EVIDENCE**
