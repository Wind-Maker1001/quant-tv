# 中证500市场状态历史诊断

独立的本地历史描述工具。**历史描述性统计不是预测收益；NO LIVE MONEY。**
不训练模型，不进入正式数据集/模型比较或 Forward，不证明 PIT 成员完整性。

## 复用与边界

开发前检查了 `ARCHITECTURE_AUDIT.md`、`RESEARCH_METHODOLOGY.md`、`DATA.md`、
`FACTORS.md`、`PERFORMANCE_BASELINE.md`，以及生产市场状态、缓存单代快照、
无界面报告、运行清单和已有测试。

- 状态判定直接调用 `qbot.research.market.regime.build_market_regime_features`，
  固定使用 `adj_close`、MA20/MA60 及严格大于/小于规则；没有复制另一套状态判定。
- 本地缓存通过 `ParquetBarCache.load_snapshot(verify_hash=True)` 固定一次
  metadata 指针及其引用的 Parquet 字节。复用现有 v2/v3 结构/哈希校验，
  不读取便利别名、不调用 Provider、不请求网络、不更新缓存。
- 绘图沿用研究报告的 Matplotlib Agg；清单复用现有原子 JSON、Git/工作区指纹、
  包版本工具，但将生命周期保存在独立诊断目录，不创建正式运行收据。
- 正式 `MARKET_REGIME` 不改动。新增 `DIAGNOSTIC_REGIME` 仅在缺价、缺交易日
  或60日窗口不足/不完整时覆盖为 UNKNOWN。CSV 保留两列，便于核对差异。
- 原14因子、4模型、正式 YAML、PIT 门禁、Forward 开关、Legacy 与 LICENSE 不变。

## 命令

```powershell
.venv-py39\python.exe -X utf8 -m examples.research.diagnose_market_regime --config configs/research/csi500_5y.yaml
```

使用配置中冻结的五年区间 `2021-09-13` 至 `2026-09-11`。先用所有已缓存的
研究前历史计算向后窗口，再截取报告区间；预热不计入研究样本。输入日期必须
唯一且严格递增，缺首尾边界、非法日期/指数/价格或缓存损坏直接失败，不静默
排序、截短或补价。价格缺失保留，日收益 `pct_change(fill_method=None)`。

真实缓存不存在时退出码1，收据写 `status=failed`，不会输出人工冒充的真实图表。
只有显式选择下面的参数才生成合成价格和工作日日历：

```powershell
.venv-py39\python.exe -X utf8 -m examples.research.diagnose_market_regime --config configs/research/csi500_5y.yaml --synthetic
```

合成路径的输入、每份 CSV、PNG标题/元数据、报告和 manifest 均标记
`SYNTHETIC SOFTWARE CHECK`。这些日期不是中国交易所交易日，不能形成市场结论。

## 产物与审计

每次独占新目录，目录碰撞失败，不覆盖任何旧结果：

```text
results/diagnostics/csi500-market-regime/<UTC timestamp + UUID>/
  daily.csv                   每日价格/均线/原状态/诊断状态/UNKNOWN原因/向后特征/日收益
  state_summary.csv           各状态样本/份额/连续段/条件收益/波动率
  spells.csv                  连续段起止/交易日长度/日历长度/截尾标识/背景边界
  annual.csv                  年度样本/份额/有效收益/条件收益/波动率
  transitions.csv             相邻不同状态转换矩阵；未知边界单列
  coverage.csv                样本和覆盖率，明确分母
  market_regime_history.png   五年指数与MA20/MA60，状态背景
  market_regime_statistics.png 占比/持续期/年度/转换/条件均值/波动率
  report.md
  manifest.json
  synthetic_input.csv         仅 --synthetic 路径
```

manifest 保存完整解析配置及原 YAML 字节 SHA-256、诊断统计口径、Git SHA/dirty/
工作区摘要、所有研究 Python 源码及入口/依赖文件 SHA-256、Python/包版本、
一次读取的缓存数据/metadata SHA-256 和来源合同、产物哈希、UTC起止、总时间及
分阶段耗时。`status=success` 才表示全部结果完成；异常/中断保存失败类型/原因及
已有部分文件哈希，部分文件不构成成功报告。磁盘完全不可写时无法保证留证。
参数解析或配置加载尚未完成的错误只返回失败，因为还无法确定输出路径。

## 统计口径

- 状态占比的分母是报告内全部可观测交易日，包含 UNKNOWN，不只计算已知状态。
- 连续段以交易日行数计时，UNKNOWN 会打断段落。首尾截断或邻接 UNKNOWN 的段
  标注 censored；平均/中位/最大长度是已观测长度，不估计完整寿命或剩余时长。
- 转换仅数相邻行、不同且均已知的状态；UNKNOWN 进入/退出另列质量边界。
  不把缺口前后的两个已知状态相接。
- 条件收益是 `r[t] = adj_close[t]/adj_close[t-1]-1` 按 **同日** `state[t]`
  分组的日收益均值，不用未来收益判定状态，也没有构造前瞻收益或策略净值。
  状态与收益共同使用当日价格，有机械关联，不能解释为预测能力。
- 波动率是条件日收益样本标准差 `ddof=1`，年化仅乘 `sqrt(252)`。
  CSV/Markdown使用小数，图表转为百分数。无样本均值为空，少于2个收益波动率为空。
  样本不是独立观测数量，不给显著性或投资结论。
- 年度分布的分母为各年报告内可观测日；2021/2026是部分年份。

默认交易日历来自 benchmark 的可观测日期。覆盖率100%只意味着这些日期内
价格/状态完整，**不能证明缓存中间没有漏掉整个交易日**。纯诊断API可接收调用者
另行核验的完整实际交易日日历，将缺失行显式展开为 UNKNOWN/MISSING_SESSION；
软件只校验该日历的日期结构，不替调用者证明来源权威性，不使用通用工作日猜补。
CLI不联网取得独立日历，报告披露这一限制。

## 本地真实缓存验收（2026-10-11）

运行 `20261011T122235.136597Z-market-regime-5ec46225`，代码基线
`18de00687695ab17360e96d8a5c8322930dc857a`，`git_dirty=true`。
未提交增量由收据的源码/工作区摘要绑定，不声称提交后的干净工作区运行。

输入1341行：130个预热日 + 1211个报告日。数据来源为缓存记录的
`AKShareProvider` / `akshare=1.18.88;contract=stock_zh_index_hist_csindex-v1`。
本次没有重新请求源端点。

| 状态 | 日数 | 占比 | 连续段数 | 平均已观测长度 | 最大已观测长度 |
| --- | ---: | ---: | ---: | ---: | ---: |
| BULL | 479 | 39.55% | 23 | 20.83 | 99 |
| BEAR | 521 | 43.02% | 18 | 28.94 | 83 |
| SIDEWAYS | 211 | 17.42% | 40 | 5.28 | 12 |
| UNKNOWN | 0 | 0.00% | 0 | 不可估计 | 不可估计 |

80次已知状态转换，0次未知边界。价格/状态/日收益均覆盖1211个**缓存可观测日期**。
已查看两份真实 PNG：指数、均线、状态背景、年度和描述性统计显示清晰，标题均
标识历史描述及 NOT predictive returns。9个产物的完整字节 SHA-256 在 manifest。

| 阶段 | 秒 |
| --- | ---: |
| 本地快照读取 | 0.0736 |
| 诊断计算 | 0.0395 |
| CSV/Markdown/PNG及产物哈希 | 0.5531 |
| 总运行（含源码与环境摘要） | 1.0025 |

日表内存311832字节（约0.297MiB），不等于进程峰值RSS；并存输入/图形不在该
数值内。这是本机 Python 3.9.25 测量，不是其他硬件保证。

输入Parquet SHA-256：
`9832a898a5bba8b4fbc971d796bc1239075aebfacff35c1a736b86a9b514cd05`。
manifest SHA-256：
`88650bc7a3e1a444af0bbd59cb106135a67df30858590940be91adad225fd656`。

已独立核对9个产物哈希及85个源码/依赖哈希，缓存metadata和Parquet读取前后未变。
另在内存将真实缓存2024-03-11之后的价格放大100万倍并加入缺失值：截止该日的
601行全部每日诊断精确相同，截止日报告的daily/summary/spells/annual/transitions
及覆盖也精确不变。仅操作DataFrame副本，不写回缓存。验证收据保存在
`results/diagnostics/market-regime-validation/20261011T202233-full-cff38b91/`
的 `real-cache-causality.json`。

## 测试

```powershell
.venv-py39\python.exe -X utf8 -m pytest -q --tb=short tests/research/test_market_regime_diagnostic.py tests/research/test_market_regime_phase3.py
# 43 passed，13第三方警告，13.69秒
.venv-py39\python.exe -X utf8 -m pytest -q --tb=short tests/research -m "not network"
# 2176 passed，2 deselected，13第三方警告，708.45秒
```

定向后再执行完整安全研究集，均在独立Python 3.9.25环境完成。JUnit分别保留于
`results/diagnostics/market-regime-validation/20261011T202109-c95f4231/targeted.xml`
和 `results/diagnostics/market-regime-validation/20261011T202233-full-cff38b91/research.xml`。
完整集合0 failures/0 errors，两个network标记测试未执行；13条警告均来自现有
Matplotlib/Pyparsing弃用提示。另通过 `py_compile`、`pip check`、`git diff --check`
及受保护目录/文件对HEAD的无改动检查。新功能共增加6个文件，没有修改原文件。

新增测试覆盖冻结规则/严格不等式、保留原状态、缺价/缺行/预热不足、排序/重复/
时区/日期边界、未来价格及缺失扰动的历史每日结果与截止日报告精确不变、
条件收益/样本波动率、年度/连续段/转换守恒、CSV与图线/背景/统计柱一致性、
PNG及人工标识、无网络、缓存损坏/缺失失败清单、报告失败、重跑/碰撞不覆盖、
数据/配置/源码/产物摘要。测试数据是显式人工fixture，未安装到真实缓存。

## 剩余限制

这是一份指数历史诊断，不能补齐完整历史500成员、调样生效链、真实个股行情或
证券状态。正式研究PIT阻断和关闭的Forward继续保持。供应商可能事后修订数据；
本地哈希证明本次使用的具体字节，不是历史时点可用性的外部公证。图表不预测
收益、不包含费用/策略执行，不用于选模型或调整冻结规则。没有自动联网、push
或实盘操作。
