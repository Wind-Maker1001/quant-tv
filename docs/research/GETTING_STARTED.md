# Qbot FactorLab 快速开始

Qbot FactorLab 是 Qbot 内部隔离的 A 股横截面研究模块。它仅用于历史研究、Paper Trading 和后续的 Forward Test，不发送真实订单。

## 当前实现状态

| 能力 | 状态 |
| --- | --- |
| 严格 YAML 配置、Schema、AKShare Provider、Parquet 缓存 | Phase 1 |
| CSI500 交易日历、BaoStock/本地导入 PIT 股票池、日级过滤 | Phase 1 |
| 14 个因子、日横截面预处理、next-open 标签、数据集 | Phase 1 |
| IC/RankIC、分位收益、自相关、换手和相关矩阵报告 | Phase 1 |
| FactorScore、Ridge、Walk-Forward、Purge/Embargo、Fast Backtest | **Planned: Phase 2** |
| LightGBM、XGBoost、Market Regime、Execution Backtest | **Planned: Phase 3** |
| Append-only Forward Test | **Planned: Phase 4** |

未实现阶段没有提供伪占位逻辑。

## 1. 创建独立环境

优先使用 Python 3.9，不要将根 `requirements.txt` 的 Legacy GUI/交易依赖混入研究环境。

Windows PowerShell：

```powershell
py -3.9 -m venv .venv-research
.\.venv-research\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r dev/requirements-research.txt
```

Linux/macOS：

```bash
python3.9 -m venv .venv-research
source .venv-research/bin/activate
python -m pip install --upgrade pip
python -m pip install -r dev/requirements-research.txt
```

AKShare 和 BaoStock 仅在网络命令执行时需要；导入 `qbot.research` 不会启动 wxPython、Qlib、Backtrader 或实盘接口。

## 2. 先运行离线测试

在仓库根目录执行：

```bash
python -m pytest -q
```

`pytest.ini` 默认只收集 `tests/research`，并排除 `network` marker。这个边界是安全要求：Legacy tests 中有联网、邮件、GUI、桌面通知和无限循环示例。

显式执行网络测试：

```bash
python -m pytest -q -m network
```

网络测试可因数据源限频、端点改动或本地网络而失败，不取代离线正确性测试。

## 3. 选择配置

- `configs/research/csi500_5y.yaml`：正式区间 `2021-09-13` 至 `2026-09-11`。
- `configs/research/csi500_smoke.yaml`：仅用于端到端烟雾验证，不得用其生成论文结论。

配置加载器递归拒绝未知字段，相对路径总是相对仓库根目录解析。`live_trading` 必须为 `false`，`universe.point_in_time` 必须为 `true`。默认 `data.warmup_trading_days: 130`，用于从研究开始日前精确选取 130 个中证500交易日；预热行情/状态只参与过滤和因子滚动，PIT 验证与数据集输出仍限定在配置的研究日期。

## 4. 运行 Phase 1 流水线

```bash
python -m qbot.research.cli audit --config configs/research/csi500_smoke.yaml

python -m qbot.research.cli download-data \
  --config configs/research/csi500_smoke.yaml

python -m qbot.research.cli build-dataset \
  --config configs/research/csi500_smoke.yaml

python -m qbot.research.cli evaluate-factors \
  --config configs/research/csi500_smoke.yaml
```

Windows PowerShell 可以将每条命令写在单行，或用 PowerShell 反引号作换行符。

如已经有经独立来源验证的逐日历史成分数据，可用：

```bash
python -m qbot.research.cli import-universe \
  --config configs/research/csi500_smoke.yaml \
  --input path/to/csi500_daily.csv
```

导入文件必须至少有 `date,symbol,is_member`，覆盖配置区间的每个基准交易日，且每日恢复为 500 个唯一成员。这不是导入“当前成分列表”的入口。若配置 `universe.provider: local`，必须先成功执行此命令；之后执行 `download-data` 会复用并校验导入股票池，同时仍从 BaoStock 获取 ST、停牌与上市日期。

## 5. 关键产物

```text
data/research/
├── raw/akshare/daily/             # 单股 Parquet + metadata JSON
├── benchmark/                    # CSI500 基准行情
├── universe/
│   ├── snapshots/                # 逐交易日 PIT 快照
│   ├── csi500_daily.parquet
│   ├── csi500_intervals.parquet
│   └── manifest.json
├── features/
│   ├── raw_factors.parquet
│   └── processed_factors.parquet
└── processed/dataset.parquet

results/
├── runs/<run_id>/manifest.json
└── factors/                       # CSV、Markdown 和 PNG 因子报告
```

下载缓存是可重建的本地大数据，不进入 Git。配置、文档和 `tests/fixtures/` 应进入 Git。

## 6. 常见失败

`POINT-IN-TIME UNIVERSE REQUIRED` 是预期的安全失败，表示某个交易日的成分快照缺失、重复、成员数异常或不在请求范围。不要为让命令通过而改成当前成分股。

Schema 错误表示 symbol、日期、主键、OHLC 关系或数值单位不符合内部合同。修复数据来源映射，不要绕过验证。

网络下载可以断点续跑：成功的单股和单日 PIT 快照会保留，再次执行仅补缺失区间。严重的 benchmark、Schema 或 PIT 问题仍会阻止数据集构建。

## 7. 研究结论门槛

烟雾命令运行成功只说明管线可执行。只有正式 PIT 数据完整、正式五年配置已运行、清单与失败摘要已存档，并在 Phase 2 完成 Walk-Forward/Purge/Embargo 后，才能讨论模型比较。策略是否盈利不是验收标准。
