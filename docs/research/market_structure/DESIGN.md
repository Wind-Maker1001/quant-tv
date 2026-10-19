# 市场结构特征框架设计与验收边界

NO LIVE MONEY。所有证券、价格、关系、分类和日历都是 SYNTHETIC_TEST_ONLY。

本模块建立可扩展的软件合同；真实研究始终为 REAL_RESEARCH_BLOCKED。合成运行不提供预测收益、IC、策略收益、可交易 Alpha 或金融资格证据。

## 固定基线与文件边界

基线为 `39eecf869c9c2075ba3f6e3c76aeba3338c63432`，分支为 `codex/market-structure-feature-foundation`，独立 worktree 为 `D:/Code/quant-tv-market-structure-feature-foundation`。

仅新增 `qbot/research/exploratory/market_structure`、`tests/market_structure` 和本中文文档及证据目录。14 个原因子、39 个表达式、四模型参数、原配置、Golden、PIT/HFQ、Forward、Legacy、model_readiness 和正式 CI 都保持原字节。

## 复用审计

|已有能力|复用方式|边界|
|---|---|---|
|原 FACTOR_REGISTRY 的 14 个价量因子|保留为现有研究能力；独立测试验证名称集合不变、新名称不能注册查找|不改变任何公式、窗口或配置|
|39 个独特候选的表达式引擎|保留原价量 AST 与白名单|市场结构依赖外部历史关系，不能伪装成旧价量 Field；不扩张候选生成器|
|diagnose_redundancy|仅由 diagnostics.py 的适配层调用其稳定数值内核|显式传入内部参数对象；不用 DiscoveryConfig 默认值，不公开旧 valid_dates 字段|
|build_market_regime_features|adapters.py 过滤完成与实际可知的日频基准后直接调用|不开发第二套 BULL/BEAR/SIDEWAYS 规则；保留原缺失及预热行为|
|DatasetBuilder / ResearchModel|提供未来只读研究视图与四模型输入描述|本 PR 不连接正式 Dataset，不 fit/predict，不修改 NaN 规则或参数|
|收益标签与 evaluate_factors|本阶段不调用|没有真实研究或预测收益结论|

## 时序合同

计算请求显式包含 observation_start、observation_end、as_of、decision_time、frequency、universe、session_id 和 scenario。时间戳必须有时区，内部转 UTC。历史模拟要求 `observation_end <= as_of <= decision_time`；as_of 越过决策时间直接失败，尚未闭合窗口返回 WINDOW_NOT_CLOSED。

窗口结束不代表数据发布。每条事实保存 fact_id、revision、kind、payload、source、definition_version、evidence、valid_from、valid_to、observation_end、published_at、available_at、captured_at、historical_availability_proven 和 withdrawn。区间左闭右开。known_at 取发布时间、实际可用时间和观察结束的上界；没有历史可用证明时，另加入 captured_at。不得把采集于 2026 年的新分类未经证明设为 2021 年可知。

快照先在 known_at<=as_of 的版本中按修订号选最新版本，再处理撤销及有效区间。旧版本晚到也不能覆盖已知的新修订。新版本缩短区间或撤销后，不能重新出现旧版本。记录及嵌套 payload 不可变。快照 ID 包含请求和实际所选输入摘要；完整输入包哈希可因追加未来记录改变，但原历史所选输入及输出必须不变。

行业/概念归属粒度是 `(security_id, namespace, group_id, fact_id, revision)`。namespace 明确区分供应商体系、层级和历史范围；taxonomy_version 和 change_date 必填。未提供归属权重时同范围内等权分摊；显式权重必须非负且每证券每范围和为 1，绝对容差 1e-12，不自动修正。重复归属拒绝。完整范围与组 ID 由 scope 记录声明，空记录不能自行解释为完整空集合。

供应链边为 upstream→downstream，保留 relation_type、evidence_status、confidence 和证据引用。MVP 仅计算 SUPPLIES_TO 且 CONFIRMED_SYNTHETIC 的边；不同证据的相同对手方去重，不将可信度当作经济敞口，不推导反向或传递关系。INFERRED 关系保留审计记录，但不参与确认关系计算。关系计数为零须有明确完整图范围；上游不存在时上游收益缺失。

## 分钟聚合、资金与市场状态

一分钟 OHLCV 按显式合成连续时段聚合至 5/15/30 分钟，锚定时段起点，不跨午间休市或交易日。末尾不足完整窗口的时段不输出半窗口。聚合要求每个预期分钟均完成且在 as_of 前实际可用；不以其他分钟补价，不将缺行解释为零成交。OHLC 为首/最高/最低/末，volume、amount 和具名分类金额求和。收益 r=窗口 close/open−1，不声称为相对昨收涨跌幅。

资金定义为 SYNTHETIC_AGGRESSOR_SIDE_V1，币种和单位均为 CNY，每笔金额只计入 buy、sell、unclassified 之一。逐分钟核对三项非负且金额和等于总额，浮点金额校验 rtol=1e-12、atol=1e-8。跨分钟定义版本不一致时拒绝净比例。总额为零时比例缺失；未分类额大于零时净比例缺失，输出未分类额、占比和 INCOMPLETE_CLASSIFICATION；完全分类且 buy=sell 才可返回零。未知主力资金、单位或供应商口径返回 BLOCKED_SOURCE_DEFINITION。

市场状态适配器只取显式时段表中已结束、基准观察窗口与该日结束一致，且发布与实际可用均不晚于 as_of 的日频记录。按完整日历补出缺失日，不压缩 60 日窗口；仅调用原判定函数。返回基准交易日、版本、观察结束、发布时间、可用时间、来源哈希、上下文年龄和缺失日数。没有可用记录时返回 MARKET_CONTEXT_UNAVAILABLE。

## 候选、粒度与质量合同

完整机器目录见证据中的 catalog.json，共 32 个，14 个 IMPLEMENTED_SYNTHETIC，18 个 CONTRACT_ONLY。每项记录公式、单位、必要输入、缺失策略、时间边界、lookback 和结构签名。多对多归属的组内均值按归属权重计算；证券行业相对收益的行业均值包括证券本身。行业金额在每个体系内守恒，分摊和等于已映射证券金额，未映射金额单列。

组内至少 2 个有效成员且加权输入覆盖率>=80%；市场比例按有效观察计算，并同时披露相对明确证券范围的覆盖率，不将条件比例声称为全市场已完整覆盖。市场扩散要求至少 3 个有效行业和 80% 行业覆盖。涨跌停仅采用有明确合成定义的窗口末状态，不猜测 10%/20% 制度。

证券、行业、概念和市场保留原生粒度。ResearchFeatureAdapter 仅支持显式选择证券特征和显式允许的市场广播；组到证券投影接口保留为未来历史归属适配，不自动接通。模型描述仅列出 FactorScore、Ridge、LightGBM、XGBoost 的未来数值表输入合同，不作模型训练或兼容性通过声明。

## 冗余诊断适配

RedundancyPolicy 独立定义：证券截面至少 20 个实体、行业/概念截面至少 3 个实体、每窗口配对覆盖率>=80%、至少 20 个有效窗口、至少 3 个不同显式交易日、有效窗口比例>=80%、高相关阈值 0.98、诊断记录上限 500000。日期参数是实际窗口 UTC 时间，不采用旧日期默认范围；旧内核的日字段仅为内部兼容命名。

按 scenario、frequency、grain、namespace 分开；同窗口存在不同 as_of/decision_time 直接拒绝混合。Pearson 使用原稳定数值内核，Spearman 用同截面秩后复用内核。逐窗口核对样本和覆盖后重新汇总，不只查看平均覆盖。对外字段为 valid_observation_windows、total_observation_windows、distinct_trading_sessions；单日 60 个分钟窗口仍只有 1 个交易日。

市场单值横截面标为 NOT_APPLICABLE，另作时间序列描述，保留相同窗口数和交易日要求。横截面常数、全样本常数、重复值比例和完全数值重复分开报告。原始行情条件比例、分类粒度及方向均写入结构签名，不因形状相似就判为相同合同。诊断拒绝台账保留阈值、实际观察和重复对象；control_* 是刻意构造的工程控制，不计为研究候选。

## 源码验收与打包限制

根 pytest.ini 默认只找 tests/research，默认静态脚本也未覆盖 tests/market_structure，必须显式执行新测试与静态检查。独立覆盖率以新源码目录为 source，包含未执行文件，核对 XML/JSON 与源码清单。正式 CI 绿色仅证明原冻结范围；不能代替新增功能验收。

无 __init__.py 命名空间用于保持正式冻结覆盖率源码清单不变。现有 qbot/setup.py 使用 find_packages，可能遗漏此模块。本 PR 验证 Python 3.9 源码工作树 `python -m qbot.research.exploratory.market_structure`，不修改打包配置，不宣称 wheel、安装包或安装后入口已经验收。

## 最终状态

完整执行和证据核验通过后才可写 SOFTWARE_MVP_SUCCESS。真实历史来源、历史可知证据和预测有效性未验证，必须同时写 REAL_RESEARCH_BLOCKED。软件演示收据自身仅声明 SYNTHETIC_DEMO_COMPLETED；最终 acceptance.json 绑定独立测试、静态检查、源码清单及正式冻结回归结果。
