# Qbot FactorLab Phase 3 交付与验收报告

验收日期：2026-09-23

## 结论

Phase 3 的软件实现与离线验收已完成：CSI500 Market Regime、LightGBM、XGBoost、四模型 Validation-only 选参、gain feature importance、日线 A 股规则执行回测、市场状态分解与统一比较报告均已接入独立的 `qbot.research` 管线。FactorLab 仍不导入 Legacy GUI、Qlib、Backtrader、easyquant 或实盘接口。

这不等于五年实证研究已完成。真实烟雾仍在 BaoStock PIT/状态数据登录阶段失败，因此尚无可用于论文结论的真实 dataset、RankIC、NAV 或四模型优劣结论。所有 synthetic 数值只是软件验收证据。

## 本阶段范围

已交付：

- 只使用 t 及以前 CSI500 `adj_close` 的 BULL/BEAR/SIDEWAYS，以及 `INDEX_RET5/20/60` 与 `INDEX_VOL20`；
- Market Regime 并入 Dataset Builder、因子评价、预测评价和模型报告；
- 统一 `ResearchModel` 合同下的 LightGBM/XGBoost，包含 Train-only median imputer、固定 seed、单线程配置和本地持久化；
- 只用 Validation Prediction RankIC 在 YAML 预注册小候选集中选参，Test 只预测一次；
- 逐 fold 保存所选 JSON 参数和归一化 gain feature importance；
- t 日收盘信号到 t+1 开盘的执行时点，FIFO T+1 可卖 lot、100 股整手、现金约束、先卖后买和确定性缩量；
- `volume`/`trade_status` 停牌守卫，以及主板、创业板、科创板按日期生效的开盘涨跌停拒单近似；
- 复用时间敏感 `FeeSchedule`，交易、现金、持仓、净值和拒单全部留表；
- 执行 benchmark 与策略在首个 t+1 `adj_open` 对齐暴露，之后按 `adj_close` 同时点估值；
- `compare-models` 固定合并 FactorScore、Ridge、LightGBM、XGBoost，验证配置、代码/环境、数据/PIT/执行输入、完整产物和 OOS 标识后客观并列，不自动选“赢家”；
- 标记为非研究结果的四模型、三市场状态、两级回测离线端到端示例。

未交付/仍需外部前置：

- 真实五年完整 PIT、个股行情与证券状态数据；
- 真实五年 FactorScore/Ridge/LightGBM/XGBoost 实验与论文结论；
- 公司行为现金流、送转股、零股、盘中队列、部分成交和跨日委托的券商级重建；
- Phase 4 append-only Forward Test；
- 任何真实资金下单能力（永不属于 FactorLab 默认路径）。

## Changed files

代码与配置主要变更：

- `qbot/research/market/`：新增市场状态与指数滞后特征；
- `qbot/research/models/lightgbm.py`、`xgboost.py`：新增树模型适配器；
- `qbot/research/validation/walk_forward.py`：新增树模型 Validation-only 选择和特征重要性；
- `qbot/research/backtest/execution.py`、`rules.py`：新增规则执行层；
- `qbot/research/config/`、两份研究 YAML：新增树模型、Market Regime 与历史涨跌停配置；
- `qbot/research/dataset/builder.py`、`cli.py`、`reports/`、`reproducibility.py`：并入状态、两级回测、四模型比较和新产物审计；
- `examples/research/phase3_synthetic_demo.py`：新增完全离线可运行示例；
- `tests/research/`：新增状态、树模型、执行回测、四模型 CLI 和示例回归测试；
- `docs/research/`：更新快速开始、数据、因子、验证、回测、方法论、架构/遗留问题与本报告。

Legacy Qbot 路径、根 `LICENSE` 与版权声明未修改。

## 测试与静态门禁

最终离线命令：

    .\.venv-py39\python.exe -m pytest -q

结果：

    215 passed, 2 deselected, 13 warnings in 96.77s

2 个 deselected 用例带 `network` marker，默认不访问公网。13 个 warning 均来自 Matplotlib 3.8.4/PyParsing 弃用提示，不是 FactorLab 错误。

额外执行：

    .\.venv-py39\python.exe -m compileall -q qbot/research
    git diff --check

两者通过。检索未发现 `qbot/research` 使用 `train_test_split`、`shuffle=True`、`bfill`，也未导入 wxPython、Qlib、Backtrader、easyquant 或实盘模块。

## 离线端到端验收

实际执行：

    .\.venv-py39\python.exe -m examples.research.phase3_synthetic_demo --output results/examples/phase3_synthetic_20260923_final --seed 42

结果：10 个虚构 symbol，2020-01-02 至 2020-12-31，BULL/BEAR/SIDEWAYS 分别为 140/48/73 个虚构交易日。四个模型各完成 1 个 fold 和 440 行 OOS prediction；Fast 回测产生 33/35 笔名义交易，Execution 回测产生 26/29 笔执行交易，树模型各留下 1 个可审计拒单。四个模型目录、树重要性、Ridge 系数、市场状态、两级 NAV 和统一比较图表均非空生成。

README、manifest 和所有模型摘要均明确包含：

    SYNTHETIC SOFTWARE DEMO ONLY - NOT A RESEARCH RESULT

这些数值不得用于 CSI500、A 股 Alpha、模型优劣或预期收益结论。

## 真实网络验证

实际重试：

    .\.venv-py39\python.exe -m qbot.research.cli download-data --config configs/research/csi500_smoke.yaml

run_id：

    20260922T121535.543754Z-download-data-82695c7f

该 run 状态为 `failed`。已验证 benchmark 缓存包含 88 个 smoke 研究交易日和 130 个裁剪后的预热交易日；随后 BaoStock 登录连续 4 次返回“网络接收错误”。管线在 PIT 阶段终止，保留错误、完整配置、Python/包版本、Git/工作区指纹和 benchmark 输出路径的 manifest。

本次未取得 PIT，因此没有启动 500 只股票的批量下载，也没有可诚实报告的失败股票列表。未生成真实 dataset、RankIC、模型或 NAV。这是“PIT 不可得就停止”的正确安全结果，不是可以用当前成分回填的理由。

## 已知局限

- 日线执行无法重建集合竞价、委托队列、部分成交、冲击成本或盘中路径；
- 现有 Schema 不足以精确处理每次现金红利、送转股和零股，Execution 回测是规则敏感的研究近似；
- 开盘接近涨停拒买/接近跌停拒卖是保守近似，无法知道封单队列；
- 真实数据前置仍未满足，不能引用 synthetic 结果回答论文 Q1–Q5；
- 原 Forward Test 起点 2026-09-14 已过，Phase 4 必须选择一个尚未到来的新起点，不得事后回填。

## 本地提交与下一步

代码/测试提交：

- `415f375` `feat(research): add phase 3 models and execution`

上述提交仅在本地 `factorlab/phase-1` 分支；没有 push、force-push、改写历史或删除分支。文档与最终验收证据在后续本地提交中保存。

下一步优先级：

1. 恢复 BaoStock 连接，或导入可独立验证的逐交易日 CSI500 历史成分，同时确保 ST/停牌/上市日期状态源可用；
2. 完成真实 smoke 的 download → build-dataset → evaluate-factors，审核覆盖率、失败列表和真实 RankIC；
3. 用冻结的正式配置跑完五年四模型与两级回测，不因 Test 结果改参数；
4. 论文结果诚实回答 Q1–Q5，包括负结果或复杂模型无优势；
5. 再实现 Phase 4 append-only Forward Test，并冻结新的未来启用日。

