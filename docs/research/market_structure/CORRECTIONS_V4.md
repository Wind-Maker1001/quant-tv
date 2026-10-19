# 金额与 OHLCV 有效性隔离：V4 更正

NO LIVE MONEY。Formal/Forward 保持 BLOCKED，不自动合并。V1、V2、V3 的验收及原始收据全部保留，追加 V4。

Codex 对 58dc13b 的复审提出 discussion_r4310399296：FLOW_NET_ACTIVE_RATIO 和 SENTIMENT_AMOUNT_HHI 的金额输入仍被共享 OHLCV 校验阻断。先在该未修改源码上保存金额单独请求和混合请求两个失败反例，再修复。

聚合按声明分别处理价格/成交量、成交额、主动买卖分类。价格 reason、amount_reason 和 flow_reason 独立，完整分钟、实际可知时间及来源定义仍共享严格边界。金额只校验真实所需字段及 CNY 单位，资金继续校验定义一致性、单位、金额非负和三项守恒；有效金额不因 OHLCV 异常失效，有效价格也不因无关金额或资金字段异常失效。

计算层分别使用价格覆盖率、金额覆盖率及分类完整性。行业成交额分摊也采用金额有效证券和金额覆盖率，不使用价格掩码；IND_AMOUNT_SHARE 的合同改为 minute_amount 及历史行业归属，定义版本 v4-inputs，候选 ID、公式、粒度和 MVP 数量保持不变。混合请求中价格失败时，金额和资金结果仍与分别请求一致；其来源摘要继续绑定本次实际依赖的记录集合。

新增各个 OHLCV 字段、价格基准、金额与资金异常交叉反例、行业金额守恒、金额分钟缺口测试。原 55 项及前两轮全部用例继续执行。完整 JUnit、覆盖率源码清单、Python 3.9 静态检查、两个独立三频率重放及所有合同状态见 evidence/v4。V1 源码重放、历版数值与完整输出摘要另做对照，保留历史哈希，不覆盖旧结果。

原 14 因子、39 候选、四模型、PIT/HFQ、Forward、Legacy、正式配置及 CI 门禁无改动。安装包未验收、真实研究 REAL_RESEARCH_BLOCKED 的边界不变；最终 CI 和 Codex Review 以最终 HEAD 的外部实际记录为准。
