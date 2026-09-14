# FactorLab 因子定义与评价

Phase 1 只实现 14 个简单、可解释的价量因子。所有时序计算均按 symbol 独立、按交易日向后计算，不使用未来数据。

## 记号

- `P_t`：股票 t 日 `adj_close`。
- `r_t = P_t / P_{t-1} - 1`：后复权日收益。
- `MA_n(x)_t`：截至 t 日、包含 t 日的 n 日完整窗口均值。
- `SD_n(r)_t`：截至 t 日的 n 个日收益样本标准差，`ddof=1`。
- `amount_t`：人民币元；`turnover_t` 是小数，不是百分数。

rolling 窗口使用 `min_periods=window`。历史不足或窗口内缺失时保留 `NaN`，不用其他日期或其他股票填补。

## 因子公式

| 类别 | 因子 | 公式 | 最长需求 |
| --- | --- | --- | ---: |
| Reversal | `REV1` | `-(P_t/P_{t-1}-1)` | 1 日滞后 |
| Reversal | `REV5` | `-(P_t/P_{t-5}-1)` | 5 日滞后 |
| Momentum | `MOM20` | `P_t/P_{t-20}-1` | 20 日滞后 |
| Momentum | `MOM60` | `P_t/P_{t-60}-1` | 60 日滞后 |
| Volatility | `VOL5` | `SD_5(r)_t` | 6 个价格观测 |
| Volatility | `VOL20` | `SD_20(r)_t` | 21 个价格观测 |
| Volatility | `VOL60` | `SD_60(r)_t` | 61 个价格观测 |
| Liquidity | `TURN5` | `MA_5(turnover)_t` | 5 日 |
| Liquidity | `TURN20` | `MA_20(turnover)_t` | 20 日 |
| Liquidity | `VOLUME_RATIO` | `MA_5(volume)_t / MA_20(volume)_t` | 20 日 |
| Liquidity | `AMIHU20` | `MA_20(abs(r_t)/amount_t * 1e8)_t` | 21 个价格观测 |
| Trend | `PRICE_MA20` | `P_t/MA_20(P)_t-1` | 20 日 |
| Trend | `MA5_MA20` | `MA_5(P)_t/MA_20(P)_t-1` | 20 日 |
| Trend | `MA20_MA60` | `MA_20(P)_t/MA_60(P)_t-1` | 60 日 |

`VOLUME_RATIO` 的分母为 0 时置缺失。`AMIHU20` 的 `amount<=0` 时当日价格冲击为缺失，无穷值也转为缺失。

## Registry 和配置

`FACTOR_REGISTRY` 是因子名到 `Factor` 实例的唯一注册边界。Dataset Builder 从 YAML 读取名称并通过 registry 计算，不包含按名称分支的 `if/elif` 链。

未知因子、重复因子或空因子列表会在构建前失败。增加因子时应实现 `Factor.name`、`lookback`、`compute()`，注册后再增加人工序列和 lookahead 单测。

## 每日横截面预处理

预处理只在同一 `date` 内、对通过当日 PIT/可交易性过滤的样本执行。原值保留为 `raw_<factor>`，因子同名列改为预处理值。

默认 MAD 流程：

1. 在当日有限值上计算中位数 `m` 和 `MAD = median(|x-m|)`。
2. 截断到 `m ± 5 * 1.4826 * MAD`。MAD 为 0 时不做截断。
3. 使用截断后当日均值和总体标准差 `ddof=0` 转为 Z-score。
4. 有限常数列映射为 0；原缺失仍为缺失。
5. 当日有效横截面少于配置的 20 时，该日该因子的预处理值全为缺失。

底层纯函数也支持 1%/99% quantile 截断，但 Phase 1 严格 YAML/CLI 配置只允许 `winsorization: mad`，以避免未审计的实验分叉。

## 标签与因子方向

因子评价的默认目标是 `EXCESS_RET5`：信号日 t 收盘后计算因子，t+1 开盘进入，t+6 开盘退出，减去中证500同窗口收益。

正的 IC 表示因子值越大、未来相对收益越高。例如 REV 已在公式中带负号，评价时不再人工翻转。

## Phase 1 因子评价

每个有足够横截面样本的交易日计算：

- Pearson IC 和 Spearman RankIC。
- 有效观测数与当日样本覆盖率。
- 根据因子排名的 Q1–Q5 未来超额收益均值，以及 `Q5-Q1`。

总体汇总包含 IC/RankIC 均值、日度样本标准差、ICIR/RankICIR、正值比例、有效日数和平均覆盖率。Phase 1 的 `ICIR = mean(daily IC) / std(daily IC)`，不年化。

额外输出：

- 相邻可观测日的同股票因子 Spearman 自相关。
- 因子最高分位等权组合的 `0.5 * sum(abs(w_t-w_{t-1}))` 换手率。
- 每日横截面 Pearson 因子相关矩阵的跨日平均。

评价器可接收可选 `group_column`。Phase 1 只输出 `ALL`；Phase 3 加入 `MARKET_REGIME` 后可复用同一接口分解 BULL/BEAR/SIDEWAYS。

## 报告产物

`results/factors/` 包含：

- `factor_report.csv`、`daily_ic.csv`、`quantile_returns.csv`。
- `factor_autocorrelation.csv`、`factor_turnover.csv`、`factor_correlation.csv`。
- `factor_ic.png`、`rank_ic.png`、`factor_correlation.png`、`quantile_returns.png`。
- `summary.md`。

绘图使用 Matplotlib `Agg` 后端，不需要 GUI。报告只陈述配置所指数据，不因结果不好而自动调整因子方向或参数。
