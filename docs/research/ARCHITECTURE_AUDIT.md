# Qbot FactorLab 架构审计

> 审计基线：UFund-Me/Qbot 上游提交 f0425ae4ae8bd02b79656b8f7039f4cd6874095e（2026-03-11）。2026-09-14 已通过官方 origin 获取完整 Git 对象；当前 `factorlab/phase-1` 直接以该上游提交为基线重放 FactorLab 提交。早期归档恢复历史完整保留在 `factorlab/phase-1-archive`，其中本地基线 `58dc392` 仅用于追溯，不属于当前分支祖先。

## 审计范围

修改前检查了根目录 README.md、DEVELOPMENT.md、LICENSE、requirements.txt、dev/requirements.txt、dev/environment.yaml、main.py、qbot_main.py，以及 qbot、pytrader、tests、docs 和 GitHub Actions。审计只确定复用边界，不重构 Legacy Qbot。

## 当前 Qbot 架构

- main.py 是 wxPython GUI 启动入口，导入即创建应用窗口；FactorLab CLI 不得依赖它。
- qbot/gui 与 qbot/engine 承载桌面界面和旧回测入口；配置、数据源与界面耦合较重。
- qbot/data 主要是 Qlib 数据 dump/转换脚本。其中 dump_pit.py 的 PIT 指财务数据修订版本，不是指数历史成分股。
- pytrader/easyquant、pytrader/strategies 和 qbot/strategies 包含行情、策略和交易示例，部分代码依赖 JQData、Tushare、TA-Lib 或平台全局对象。
- Backtrader 集成分散在 pytrader 与策略示例中，适合第二阶段作为执行层参考，不适合作为第一阶段因子引擎的依赖。
- Qlib 工作流和 Alpha158/LightGBM 示例可供后续模型阶段参考，但依赖重、标签与本研究 next-open 时点不一致。
- qbot_main.py 含硬编码环境假设和循环式在线流程，不能被研究模块导入。
- qbot/common/config.py 与 qbot/engine/config.py 存在重复及导入期文件系统副作用。
- tests 目录多为联网、GUI、邮件或实盘演示脚本，缺少安全的离线单元测试边界。

## 可直接复用的内容

- 根 LICENSE（MIT）及原项目版权声明必须原样保留。
- 现有行情/策略代码可作为字段语义和执行行为的参考资料。
- Backtrader、easyquant 和 Qlib 只在未来阶段通过适配器复用，不进入 FactorLab 核心依赖。
- 现有文档站点可在研究文档稳定后增加入口；第一阶段直接在 docs/research 独立维护。

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
- LightGBM、XGBoost、Qlib、SHAP 不进入第一阶段强制依赖。

### 测试与自动化

- 裸 pytest 会收集具有外部副作用的 Legacy 文件；需将默认 testpaths 限定到 tests/research。
- 现有 Python CI 混合未安装工具、Notebook、Qlib 和联网测试，不能作为 FactorLab 门禁。
- auto-trade 工作流与本项目 NO LIVE MONEY 原则无关，FactorLab 不接入。

## 第一阶段新增模块

FactorLab 使用 qbot/research 独立命名空间，核心模块不得导入 wxPython、Qlib、Backtrader、easyquant 或实盘接口：

- config：严格 dataclass/YAML 配置和仓库根目录路径解析。
- data：统一 Provider、Schema、指数行情交易日历和原子 Parquet 缓存。
- universe：BaoStock 历史 CSI500 快照、区间表、本地导入与日级过滤。
- factors：14 个可解释价量因子、注册表和逐日横截面预处理。
- labels：与 t 日收盘后信号一致的 t+1 open 到 t+6 open 超额收益。
- dataset：PIT 股票池、过滤、因子、标签的排序长表组装。
- metrics/reports：IC、RankIC、分位收益、相关性、换手率及无界面报告。
- cli/reproducibility/errors：argparse、运行清单和统一错误语义。

运行时大数据写入 data/research，实验产物写入 results；配置、测试 fixture 和文档进入 Git。

## 计划避免修改的 Legacy 模块

第一阶段不修改 main.py、qbot_main.py、qbot/gui、qbot/engine、qbot/data 的 Qlib dump、pytrader/easyquant、pytrader/strategies、qbot/strategies、qbot/plugins、Legacy tests 以及任何真实交易配置。只有直接阻断 FactorLab 且无法通过隔离解决时才考虑最小修复，并记录原因。

## 强制边界与失败策略

- 模型与因子只能通过 MarketDataProvider 获取数据，不直接调用 AKShare。
- PIT 股票池缺日、成员数异常或哈希不一致时抛出包含 POINT-IN-TIME UNIVERSE REQUIRED 的错误，绝不退化为当前成分股。
- 日期为无时区 datetime64[ns]，股票代码唯一采用 600000.SH / 000001.SZ，主键为 date,symbol。
- 不允许 bfill；价格不因停牌而前向填充。横截面预处理只在单日内部进行。
- 第一阶段不实现模型、Walk-Forward、回测、Market Regime、Forward Test 或 GUI 占位代码。

## 分阶段复用决策

第一阶段完全隔离研究核心。第二阶段可将快速回测保持为 Pandas/NumPy，并只为 Level 2 执行回测封装 Backtrader。第三阶段再以可选依赖接入 LightGBM/XGBoost。第四阶段实现 append-only Forward Signal；即使 Legacy 提供实盘能力，FactorLab 也永久默认 live_trading=false，不发送真实订单。
