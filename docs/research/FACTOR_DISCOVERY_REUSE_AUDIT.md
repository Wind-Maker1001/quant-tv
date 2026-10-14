# 自动因子发现复用审计

核验基线：main `48ea4dd8c1876c1515f3172c9bb2e812f20ebe82`；研究 CI [38540055000](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38540055000)、静态 CI [38540055327](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38540055327) SUCCESS。依赖图 pip 更新任务失败，属于已有非研究任务，本次不把它记为研究检查通过。

原工作区位于已合并的统计审计分支、无受跟踪文件修改。从重新 fetch 后的 main 创建 `codex/automated-factor-discovery-mvp`。用户授权多子代理，主代理先冻结接口，分配 engine.py、generator.py 与只读审计；子代理因额度停止，主代理按目标文件允许的资源不足回退顺序接手，未删减验收。

## FactorLab

- `factors/base.py` 的 grouped_shift、rolling_transform 与 daily_return 是按股票的历史语义；它们假定每个市场交易日有对应行。新 engine 先建立证券×显式交易日历网格，原缺口保持缺失，再实现相同 shift/完整 rolling 语义。RollingStd 保留 ddof=1，RET1 定义为当前 HFQ 收盘 / 前一市场交易日 HFQ 收盘 − 1，不补缺失值。
- `factors/preprocess.py` 的 preprocess_cross_sections 直接复用，用逐日 MAD（1.4826、5 倍）和 Z-score 处理，保留原值。`metrics/factor.py` 的 evaluate_factors 直接用于任意候选列；IC、RankIC、分位评价没有第二套实现。
- 通用 evaluate_factors 按信号因子可用性先形成分位，再聚合后来可用的标签。旧 `exploratory/runner.py` 的固定包装器另将成熟标签行先筛出，不能继承到新信号分位形成中。本模块仅借用旧输入合同和旧收据校验，不调用旧分析入口。
- `data/schema.py` 用于数值类型、规范证券代码、OHLC、单位字段的校验。engine 在只含字段白名单的副本上校验，非有限值先记原因并变缺失；完整性检查用的局部 OHLC 掩码不改实际计算输入。未知证券名称、错误代码、重复日期键、含时区/日内/非法日期拒绝；允许行乱序，内部稳定排序并映射回原 index。
- 原 FACTOR_REGISTRY 固定14因子，旧 runner 固定 FACTOR_NAMES；新表达式永不写注册表。原公式完全不改，仅在密集日历面板上只读计算作为比较基准。
- MOM20/60、REV1/5、VOL5/20/60、TURN5/20、VOLUME_RATIO、PRICE_MA20、MA5_MA20、MA20_MA60 可由首版节点给出文档化等价形式；规范 AST 完全相同才为结构重复。数学等价但浮点操作次序不同的 Delta/Lag 动量不做代数合并，进入数值冗余诊断。AMIHU20 使用 abs 和 1e8 尺度及特殊量纲，不可表示为 v1 AST，仅数值比较。
- 旧 `statistical_audit/inputs.py` 同时绑定特定数据版本、冻结 v2 计算源码、样本、研究年和14因子，不调用或改写其冻结入口。新 Schema 独立为 FACTOR_DISCOVERY_EXPLORATORY_V1。

## Qlib Alpha158 / Alpha360

本地只读检查 `pytrader/strategies/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml` 和 `XGBoost/workflow_config_xgboost_Alpha360.yaml`：它们配置 qlib handler、训练/验证/测试分段和组合回测。Alpha360 YAML 将负 Ref 放在未来标签，不应成为新信号节点；Qlib 运行环境、模型与回测不导入。

2026-10-14 只读检查 Microsoft 官方 [handler](https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/handler.py) 和 [loader](https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/loader.py)：Alpha360 使用历史价量相对当前量归一化；Alpha158 有价量比例、均值、波动、回归、排序和相关等更宽运算。其 VWAP、epsilon 分母、额外窗口及更宽算子不符合本任务白名单，不能直接转移；handler 的默认填缺失流程也不继承。本模块只借鉴有限经济模板思路，源码没有导入 qlib，官方可变 main 页面仅作审计参考而非运行依赖。

## Investool

本地 `qbot/plugins/investool/README.md`、`datacenter/`、Go 模块只读查看。它是 Go 基本面选股/基金分析与数据服务，含东方财富等供应商获取、CLI 与 Web 接口。其财务选股口径、网络和服务运行时不适合本次收盘信号表达式闭环；无需复制或导入，未运行交易或下载入口。

## 私有与公开边界

原授权 manifest 字节 SHA 为 `c1aef73620bb34f43e1553aa196dcd35fd11eb2abfb34c842b7ff59c5a9b8ced`，数据版本 `2f145d173f5ddc79d303f580bc4485241023ae3971d3b40a2e8fa6e3de2e3f5f`。本地原文件存在，旧 load_dataset 验证四个输入文件与全部410源哈希。新适配器再次校验原 manifest、来源合同、冻结 v2 收据及其 derived_factor_labels.parquet SHA；只取原历史 entry/exit/EXCESS_RET5 标签，不重新定义或下载行情。

真实开发区间事前设为 2025-09-12 至 2026-06-30，之前是历史预热，后续数据不能进入生成、去重或评价。整体50股一年样本已用于旧研究，剩余历史也不宣称独立未观察测试集；非 PIT 便利样本与供应商 HFQ 保持 EXPLORATORY / UNVERIFIED / NON_PIT_CONVENIENCE。

公开白名单只有表达式、冻结配置、候选质量、逐日 IC/分位聚合、冗余汇总、中文报告和独立收据。不发布真实证券级行情、因子、收益标签、供应商响应、分组成员或可枚举成员承诺。正式 qualification、配置、Forward model bundle/signal reader 实际入口拒绝新收据；金融资格和交易能力不改变。
