# Qbot FactorLab 架构审计

> 审计基线：UFund-Me/Qbot 上游提交 f0425ae4ae8bd02b79656b8f7039f4cd6874095e（2026-03-11）。2026-09-14 已通过官方 origin 获取完整 Git 对象；当前 `factorlab/phase-1` 分支直接以该上游提交为基线重放 FactorLab 历史提交，现已在同一隔离架构上推进至 Phase 3。早期归档恢复历史完整保留在 `factorlab/phase-1-archive`，其中本地基线 `58dc392` 仅用于追溯，不属于当前分支祖先。

## 审计范围

修改前检查了根目录 README.md、DEVELOPMENT.md、LICENSE、requirements.txt、dev/requirements.txt、dev/environment.yaml、main.py、qbot_main.py，以及 qbot、pytrader、tests、docs 和 GitHub Actions。审计只确定复用边界，不重构 Legacy Qbot。

## 当前 Qbot 架构

- main.py 是 wxPython GUI 启动入口，导入即创建应用窗口；FactorLab CLI 不得依赖它。
- qbot/gui 与 qbot/engine 承载桌面界面和旧回测入口；配置、数据源与界面耦合较重。
- qbot/data 主要是 Qlib 数据 dump/转换脚本。其中 dump_pit.py 的 PIT 指财务数据修订版本，不是指数历史成分股。
- pytrader/easyquant、pytrader/strategies 和 qbot/strategies 包含行情、策略和交易示例，部分代码依赖 JQData、Tushare、TA-Lib 或平台全局对象。
- Backtrader 集成分散在 pytrader 与策略示例中，不适合作为因子、模型或两级研究回测的依赖；Phase 3 最终没有复用它。
- Qlib 工作流和 Alpha158/LightGBM 示例只作为历史参考；其依赖、特征和标签时点与本研究不一致，Phase 3 树模型没有复用 Qlib 工作流。
- qbot_main.py 含硬编码环境假设和循环式在线流程，不能被研究模块导入。
- qbot/common/config.py 与 qbot/engine/config.py 存在重复及导入期文件系统副作用。
- tests 目录多为联网、GUI、邮件或实盘演示脚本，缺少安全的离线单元测试边界。

## 可直接复用的内容

- 根 LICENSE（MIT）及原项目版权声明必须原样保留。
- 现有行情/策略代码可作为字段语义和执行行为的参考资料。
- Backtrader、easyquant 和 Qlib 不进入 FactorLab 核心依赖；若未来确需复用，也只能通过显式适配器并保持研究时点合同。
- 研究文档在 docs/research 独立维护，并已从根 README 与 docs/_sidebar.md 增加入口；不得用 Legacy Qbot 的实盘/模型库说明替代 FactorLab 的实际阶段状态。

## 不适合直接复用的内容

- Legacy 行情接口没有满足 canonical symbol、原始价与复权价并存、原子 Parquet 增量缓存和严格 Schema。
- 当前成分股接口不能证明历史时点成员资格，禁止用于 2021 年回测。
- 旧策略的成交时点、标签方向与成本假设不统一，不能用于无未来函数的横截面研究。
- 旧配置模块具有导入副作用，且参数散落；研究模块需要严格 YAML 配置。
- Legacy 测试导入时可能联网、发邮件、打开 GUI 或进入循环，不可作为默认 pytest 集合。

## 技术债与风险

### 数据与研究正确性

- 缺少可验证的中证500逐日 Point-in-Time 股票池；这是正式数据集的硬前置条件。
- 旧代码存在按当前日期处理复权、平台隐式数据和混用价格字段的风险。
- 缺少统一交易日历、主键唯一性、单位转换和未来数据泄漏守卫。

### 依赖

- 根依赖未形成适用于研究流水线的可复现锁定，混合 wxPython、Qlib、交易与 GUI 依赖。
- dev/environment.yaml 是旧平台导出，含不可移植信息。
- 当前执行机为 Python 3.12；目标研究环境是 Python 3.9。研究依赖须单独固定，AKShare 使用最后支持 Python 3.9 的 1.18.88。
- LightGBM/XGBoost 在 Phase 3 研究环境中固定版本，但由各自模型在拟合时延迟导入，不影响 FactorScore/Ridge 或基础包导入；Qlib、SHAP 仍不进入 FactorLab 依赖。

### 测试与自动化

- 裸 pytest 会收集具有外部副作用的 Legacy 文件；需将默认 testpaths 限定到 tests/research。
- 现有 Python CI 混合未安装工具、Notebook、Qlib 和联网测试，不能作为 FactorLab 门禁。
- auto-trade 工作流与本项目 NO LIVE MONEY 原则无关，FactorLab 不接入。

## 第一阶段新增模块

FactorLab 使用 qbot/research 独立命名空间，核心模块不得导入 wxPython、Qlib、Backtrader、easyquant 或实盘接口：

- config：严格 dataclass/YAML 配置和仓库根目录路径解析。
- data：统一 Provider、Schema、指数行情交易日历和原子 Parquet 缓存。
- universe：BaoStock 历史 CSI500 快照、区间表、本地导入与日级过滤。
- universe/status：证券交易状态与上市日期采用独立、哈希绑定的 generation manifest；支持 BaoStock 完整采集或严格本地导入，PIT 成员键缺失时 fail closed，绝不以相邻日期填充。
- factors：14 个可解释价量因子、注册表和逐日横截面预处理。
- labels：与 t 日收盘后信号一致的 t+1 open 到 t+6 open 超额收益。
- dataset：PIT 股票池、过滤、因子、标签的排序长表组装。
- metrics/reports：IC、RankIC、分位收益、相关性、换手率及无界面报告。
- cli/reproducibility/errors：argparse、运行清单和统一错误语义。

运行时大数据写入 data/research，实验产物写入 results；配置、测试 fixture 和文档进入 Git。

## 第二阶段增量模块

Phase 2 延续同一隔离边界，没有重构 Legacy Qbot：

- models：统一 ResearchModel 接口、固定配置权重 FactorScore、Train-only 缺失值处理/标准化的 Ridge 和本地模型持久化；
- validation：按实际交易日映射的 Expanding Walk-Forward、Purge/Embargo、标签窗口审计及 Train → Validation → Test runner；
- portfolio/backtest：确定性 Top-K 等权目标和 Pandas/NumPy Fast Research Backtest；
- backtest/fees：按生效日期选择的佣金、最低佣金、印花税、过户费、附加费与滑点；
- metrics/reports：样本外预测指标、组合风险/收益/成本指标、逐模型报告和非自动选优的模型比较；
- examples/research：完全离线的 synthetic 端到端软件示例，产物强制标记为非研究结论。

第二阶段的上述交付状态是历史事实；当时留待 Phase 3 的 LightGBM/XGBoost、Market Regime 与规则执行回测现已完成。Phase 4 又在同一隔离边界内加入了未来激活收据、冻结模型和 append-only Paper Signal，但尚未正式激活真实日期。

## 第三阶段增量模块

Phase 3 继续沿用 `qbot.research` 单向隔离，不重构或导入 Legacy 交易链路：

- market：从中证500 `adj_close` 向后计算 MA20/MA60、`INDEX_RET5/20/60` 与 `INDEX_VOL20`，冻结 BULL/BEAR/SIDEWAYS 定义并并入数据集；
- models：新增延迟导入的 LightGBM/XGBoost 适配器，使用 Train-only median imputer、固定随机种子、单线程配置、本地模型持久化和 gain feature importance；
- validation：沿用 Phase 2 的 Expanding Walk-Forward，在 Validation 预注册候选集内选择树模型参数，Test 只预测一次；
- backtest/rules：新增独立的 Pandas/NumPy 日线执行层，处理次日开盘、FIFO T+1、100 股整手、现金、停牌、费用和按板块/日期生效的开盘涨跌停拒单；
- reports/cli：每次四模型运行同时输出 Fast 与 Execution 两级回测；统一比较报告强制核对四次源运行的配置、代码/环境、数据/PIT/价格与状态哈希、产物哈希和 OOS 身份，再并列预测、净值、执行与市场状态结果，不自动选优。

Phase 3 的“完成”指软件路径和离线正确性守卫已经实现，不表示已经取得真实五年数据或论文结论。当前公开网络/PIT 链路未完成正式数据集，真实五年四模型实验仍待数据前置满足。

## 第四阶段增量模块

Phase 4 继续不导入 Legacy 实盘链路：

- `forward/contract.py` 冻结因子、标签、预处理、验证、费用/执行、模型候选、训练截止日与 Top-K 研究合同，仅允许每日 `data.end` 滚动；
- `forward/activation.py` 要求在新起点之前原子创建激活收据，已经错过的 2026-09-14 无法补注册；
- `forward/integrity.py` 绑定研究源码与依赖摘要、拒绝 symlink/reparse 路径，并串行化完整日终流水线；
- `forward/model_bundle.py` 只拟合一个显式模型，以 `exit_date <= training_asof` 阻止未成熟标签进入训练，并用内部身份摘要绑定训练审计字段；
- `forward/policy.py` 以 Asia/Shanghai 收盘时点区分 `ON_TIME` 与必须说明原因的 `LATE_REISSUE`；
- `forward/signal_recorder.py` 使用日期锁、锁内版本分配、staging 与原子目录发布，并只在 producer run 成功后追加自包含 completion 收据；
- CLI 的 `forward-signal` 先运行独立 download/build 子清单，再核对当日 benchmark、PIT、数据集、模型和契约哈希，只输出 Paper Top-K。

正式 YAML 仍保持关闭；这表示软件路径完成但真实实验尚未启动，而不是 Phase 4 结果已经存在。

## 计划避免修改的 Legacy 模块

Phase 1–4 不修改 main.py、qbot_main.py、qbot/gui、qbot/engine、qbot/data 的 Qlib dump、pytrader/easyquant、pytrader/strategies、qbot/strategies、qbot/plugins、Legacy tests 以及任何真实交易配置。只有直接阻断 FactorLab 且无法通过隔离解决时才考虑最小修复，并记录原因。

## 强制边界与失败策略

- 模型与因子只能通过 MarketDataProvider 获取数据，不直接调用 AKShare。
- PIT 股票池缺日、成员数异常或哈希不一致时抛出包含 POINT-IN-TIME UNIVERSE REQUIRED 的错误，绝不退化为当前成分股。
- 日期为无时区 datetime64[ns]，股票代码唯一采用 600000.SH / 000001.SZ，主键为 date,symbol。
- 不允许 bfill；价格不因停牌而前向填充。横截面预处理只在单日内部进行。
- 保留 Phase 2 历史边界：FactorScore、Ridge、Walk-Forward 与目标权重 Fast Backtest 是当时交付，不倒写成包含执行约束。
- Phase 3 已实现 Market Regime、LightGBM、XGBoost 和独立规则执行回测；日线执行不能冒充盘口队列、部分成交、冲击成本或跨日委托生命周期。
- Forward Test 核心记录层已实现但尚未正式激活；激活日前信号、旧日期 `ON_TIME` 和覆盖已有版本都会失败，FactorLab 永久保持 `live_trading=false`。
- 正式数据集仍要求完整真实五年行情、证券状态与逐日 PIT 股票池；软件测试或 synthetic 产物不能替代这些输入。

## 分阶段复用决策

第一阶段完成隔离的数据与因子核心；第二阶段以 Pandas/NumPy 实现与 Legacy 无关的基线模型验证和快速回测；第三阶段以延迟导入的 LightGBM/XGBoost 扩展同一模型接口，并直接实现不依赖 Backtrader 的规则执行回测和四模型统一比较；第四阶段在独立 `forward/` 中实现预注册、冻结和 append-only Forward Signal。即使 Legacy 提供实盘能力，FactorLab 也永久默认 `live_trading=false`，不发送真实订单。
