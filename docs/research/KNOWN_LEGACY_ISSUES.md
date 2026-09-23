# Known Legacy Qbot Issues

> 初始记录日期：2026-09-13；Phase 3 状态复核：2026-09-22
> 状态：仅记录，FactorLab Phase 1–3 均未重构 Legacy Qbot。

本文只列出审计时在当前恢复快照中实际观察到的问题。FactorLab 通过 `qbot.research` 的单向隔离规避它们；只有问题直接阻断研究核心时才会做最小修复。

## 高风险：不应在默认测试或研究进程中导入

### 1. `qbot_main.py` 导入即联网并进入无限循环

文件在模块顶层导入 Tushare、TA-Lib、TensorFlow、桌面通知等库，立即请求历史行情、打开交互绘图，然后执行 `while True`。导入该文件可能阻塞测试进程、访问网络并发送桌面通知。

**FactorLab 处置：** 永不导入此入口；`python -m qbot.research.cli` 是独立入口。

### 2. Legacy pytest 收集具有真实外部副作用

实际例子包括：

- `tests/backtest_test.py`、`tests/test_backtest.py` 和 `tests/test_trade.py` 在顶层创建 easyquant 交易引擎，读取 `account.json`，使用 online quotation 并调用 `start()`。
- `tests/pync_test.py` 在顶层进入无限循环，发送桌面通知并调用系统音频命令。
- `tests/myplot_test.py` 在顶层请求 Tushare 数据并调用 `plt.show()`。
- `tests/send_email_test.py` 和 `tests/test_send_email.py` 包含向硬编码外部邮箱收件人发信的测试。
- `tests/test_unit.py` 在类定义/初始化期创建目录，并在 `setUpClass` 中下载数据、初始化 Qlib。

**FactorLab 处置：** `pytest.ini` 默认只收集 `tests/research`；网络测试另用 marker 显式运行。Legacy tests 仅在隔离环境中人工启动。

### 3. 实盘/模拟交易代码与研究边界混杂

`qbot/engine/trade/` 和 `pytrader/easyquant/` 包含券商、easytrader、浏览器/客户端自动化、账户配置和网络行情代码。这些路径不应在论文实验的数据或因子构建期执行。

**FactorLab 处置：** 永久默认 `live_trading: false`；Phase 1–3 不读券商账户、不要求 API 密钥、不发送真实订单。Phase 3 的 Execution Backtest 只在内存中模拟研究订单，不连接模拟盘或实盘。

## 中风险：依赖、配置与包结构

### 4. 配置模块重复且 import 期写入文件系统

`qbot/common/config.py` 和 `qbot/engine/config.py` 大量重复路径常量，并在模块导入结尾对多个 `data/`、`results/` 和 `docs/` 路径执行 `mkdir`。这使“仅导入配置”也成为写操作，并增加测试隔离难度。

**FactorLab 处置：** 使用无导入副作的独立 dataclass/YAML 配置；只在显式 CLI 操作中创建运行目录。

### 5. 根依赖不可复现且平台冲突风险高

`requirements.txt` 和 `dev/requirements.txt` 大多数包没有版本约束，同时包含老版 `matplotlib==3.2.2`、`pyglet==1.5.0`、GitHub 直装 pyfolio，以及 wxPython、TA-Lib、TensorFlow、Backtrader、加密货币和桌面相关工具链。`dev/environment.yaml` 是大型平台环境导出，`dev/` 还同时携带 Python 3.8/3.9 和多平台 wheel。

**FactorLab 处置：** 仅安装 `dev/requirements-research.txt`；目标 Python 3.9，不因 FactorLab 升级整个 Legacy 环境。Phase 3 在该隔离清单中固定 LightGBM/XGBoost 版本，并在实际拟合时延迟导入；没有安装可选运行库时明确失败，不污染或静默借用 Legacy 模型环境。

### 6. 包元数据与根许可证不一致

根 `LICENSE` 是 MIT License，Copyright (c) 2022 UFund-Me。`qbot/setup.py` 却声明 `license='Apache'` 并使用 Apache classifier；同时 console entry point 为 `sample=sample:main`，并非有效的 Qbot 命令入口。

**FactorLab 处置：** 不修改或删除原 `LICENSE`/版权信息，不依赖 Legacy setup entry point；本问题留待上游或单独包治理任务处理。

### 7. `qbot/` 根未提供常规 `__init__.py`

当前 tree 中 `qbot/__init__.py` 不存在，只能依赖 Python 3 命名空间包行为进行 `qbot.*` 导入。这对直接从仓库根运行的 Python 3.9+ 可用，但某些打包、IDE 或旧工具可能不一致。

**FactorLab 处置：** 不为修复 Legacy 包结构而全局改造；`qbot/research/__init__.py` 明确创建，CLI 从仓库根运行并通过离线导入测试验证。

## 研究正确性缺口

### 8. `dump_pit.py` 不能作为历史指数成分股池

`qbot/data/dump_pit.py` 的 `PIT_DIR_NAME` 为 `financial`，处理季度/年度财务字段的修订版本。它不提供某个交易日的 CSI500 成员资格。

**FactorLab 处置：** 使用独立 `PointInTimeUniverseProvider`、BaoStock 逐交易日快照和经验证导入器；缺失时 fail fast，绝不用当前成分回填。

### 9. Legacy 行情层没有统一研究 Schema

`pytrader/easyquant/quotation.py` 同时导入 JQData、Tushare、easyquotation/easytrader，依赖外部配置，并用平台实现决定字段和交易日语义。当前系统未统一 canonical symbol、tz-naive 日期、原始/复权价并存、volume 和 turnover 单位，也没有可审计的原子增量 Parquet 缓存。

**FactorLab 处置：** 新建 Provider ABC、严格 schema 和缓存；因子/标签不直接调用 AKShare/BaoStock。

### 10. Legacy 回测不是横截面执行引擎

`qbot/engine/backtest/backtest_base.py` 使用单标的 bar 和简单 position signal 计算收益；`backtest_main.py` 在顶层请求 JQData 并打开图表。这些路径没有 PIT 横截面股票池、next-open 交易时点、交易日 purge 边界或本课题需要的 A 股细则。

**FactorLab 处置：** 因子和模型引擎不依赖 Backtrader。Phase 2 已用 Pandas/NumPy 实现目标权重 Fast Research Backtest；Phase 3 又在 `qbot.research.backtest` 内独立实现规则执行回测，覆盖次日开盘、FIFO T+1、100 股整手、现金、停牌、费用和按板块/日期生效的开盘涨跌停拒单。Legacy/Backtrader 最终未被复用。

该执行层仍是日线研究仿真：不能重建盘口队列、集合竞价、部分成交、冲击成本、盘中路径或跨日委托生命周期。这是显式模型边界，不是调用 Legacy 回测的理由。

## 低风险与文档偏差

### 11. 架构文档的部分路径已过期

`DEVELOPMENT.md` 描述 `qbot/strategy/`、`qbot/analyser/`、`qbot/notify/`、`backend/` 等路径，但当前 tree 中的实际路径或实现不完全匹配。

**FactorLab 处置：** 以当前文件系统和可执行代码为准，新文档不依赖过时路径。

### 12. 日志、输出和错误处理不统一

Legacy 示例同时使用 `print`、`logging`、`loguru`、GUI 控件和桌面通知，部分网络/交易流程在顶层运行，错误边界不适合批量数据任务。

**FactorLab 处置：** 使用标准 `logging`和统一错误类；单股下载失败可继续并产生清单，但 schema、benchmark 和 PIT 错误严格失败。

## 未处理项

- 未运行 Legacy 全量测试，因为其已知副作与本阶段范围冲突。
- 未统一根依赖或修改 `qbot/setup.py`，避免为研究模块重构整仓库。
- 未修复 GUI、实盘、邮件、桌面通知或第三方子项目。
- 未将 Qlib 作为 FactorLab 强制依赖。

## FactorLab 当前交付边界

这些边界不是 Legacy 缺陷已被修复的证明：

- Phase 3 的 Market Regime、LightGBM、XGBoost、规则执行回测和四模型统一比较报告已经在隔离命名空间实现；
- Phase 4 的未来激活收据、冻结模型与 append-only Paper Signal 也已在隔离命名空间实现，不调用 Legacy 实盘接口；
- 真实五年行情、证券状态和逐日 PIT 股票池仍未因公开端点/网络前置完成，因此没有可用于论文结论的正式五年实验结果；
- 正式 Forward Test 尚未激活且没有真实信号；已经错过的 2026-09-14 不得用历史重跑或 Legacy 模拟/实盘能力冒充。

如后续必须触及上述 Legacy 路径，应先新建独立 issue，记录责任边界、副作、回归测试和许可证影响。
