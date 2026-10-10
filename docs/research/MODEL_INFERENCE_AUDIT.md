# 模型比较的统计稳健性检验

日期：2026-10-10。范围：补齐 Q3 的历史 Test 统计评价软件；**不是证明机器学习
优于 FactorScore，也不是完成真实五年研究**。正式 PIT 门禁、历史研究参数、
Validation-only 选参、单次 Test 预测、Forward 默认关闭和 NO LIVE MONEY 均保持不变。

## 统计对象与预注册

接口 `evaluate_model_robustness(daily, calendar, options)` 只接收四个固定模型的
`HISTORICAL_TEST` 逐日指标。模型为 FactorScore、Ridge、LightGBM、XGBoost。
观测单位是**市场交易日**，不是约60万股票—日行，更不是把扩大训练集的重复日期
作为新样本。Train 是拟合诊断，Validation 已用于选参，二者均不进入这里的主检验。

主检验固定为三个机器学习模型的总体日度 RankIC 减去同日 FactorScore RankIC，
原假设是配对均值差为0，使用双侧检验。三项 p-value 做 Holm 校正；某项不可检验时，
校正范围仍为3，不因删除坏结果而缩小。拒绝零差异不等于“更好”：必须同时看差值
方向、区间、跨时期稳定性、实际交易成本和数据局限。不自动评选赢家或反向调参。

另报告各模型均值、Pearson IC、成本前 Top-Bottom 超额标签，以及 Year、Quarter、
Fold、Regime 分组。这些都是探索性诊断，不属于上述固定三项检验的校正范围。
个别 HAC/Bootstrap 区间也未做多重比较校正，不能把任一分组的漂亮区间当成总体证明。

YAML 的 `inference` 在模型实验前进入完整 config/producer manifest：

```yaml
inference:
  enabled: true
  confidence_level: 0.95
  hac_lags: 20
  bootstrap_block_days: 20
  bootstrap_repetitions: 2000
  min_valid_days: 60
  min_coverage: 0.8
```

固定 baseline、主指标、双侧方向和三项范围不能由 YAML 改成看过 Test 后的选优策略。
seed 来自全局42，holding_days 来自标签配置。lag 至少覆盖 holding_days−1，块长
至少为 holding_days，最小样本必须多于 lag 并覆盖两块。未知键、bool 冒充数字、
非法概率、NaN/Inf 或不匹配的时间尺度严格失败；显式禁用也不会接受非法参数。
这些默认长度是事前工程选择，不声称对所有金融序列最优，不依据最终 Test 优化。

## HAC 与缺失日期

股票标签仍是 `t+1 open → t+6 open`，相邻信号日期的5日标签存在重叠。
采用 Bartlett 权重的 Newey–West HAC 来描述均值不确定性，而非普通 IID 标准误。
原方法与条件见 [Newey–West 论文](https://www.nber.org/papers/t0055)及其
[完整工作论文](https://www.nber.org/system/files/working_papers/t0055/t0055.pdf)。

对连续 benchmark 交易日网格，设有效观测指示为 m_t，n=Σm_t，
μ=Σm_t x_t/n，e_t=m_t(x_t−μ)，L=hac_lags：

```text
S = Σ e_t² + 2 Σ[l=1..L] (1 − l/(L+1)) Σ[t=l..T−1] e_t e_(t−l)
Var(μ) = S / n²
```

缺失指标或不属于该 subgroup 的日期保留原网格位置。e_t 的零贡献是 sandwich
估计方程，不是把缺失 IC/收益填成0。不会压缩缺失日或把 BULL 日期跨过 BEAR
直接当作相邻交易日。coverage 的分母是本 scope 实际计划产生预测的日期数，
不是包含 fold 间空隙的全部网格槽。ML−baseline 只在双方同日指标均有效时计算，
不是先各自删缺失再用两个不同样本的均值相减。

这里的 signal_dates 来自四模型共有的已保存 Test cohort 日期，不是名义日历窗口
或500只成员覆盖率。若某市场日完全没有合格样本而未产生预测，仍保留其网格槽，
但不能用本表的 coverage 声称该日已覆盖指数；必须另查股票池/过滤/数据质量报告。

使用渐近 normal 双侧 p-value 与置信区间，不应用未经证明的小样本修正。
不足60个有效日期、coverage低于80%、常数/退化方差时有明确 status，p/CI 留缺失，
不生成无限 t 或伪造 p=0。微小浮点误差按数值容差处理；真正非法协方差或非有限
计算直接报错。HAC 需要适当的弱依赖/稳定条件，不能保证非平稳市场中的有限样本
覆盖率；各 fold 重拟合引起的分布变化也必须谨慎解释。

## Moving-block Bootstrap

从同一完整网格的重叠连续20日块中有放回抽取，拼接后裁剪至原槽数；不把最后一日
环接第一日。配对差值保留双方的联合缺失，因此抽样的是同日配对，而非各模型
独立重采样。缺失值仍缺失，各 replicate 用自身有效观测的均值；少于95%的 replicate
有有效均值时不提供 Bootstrap CI。否则报告线性分位数 percentile CI，不据它生成
未经定义的 Bootstrap p-value。

块抽样思想来源于 [Künsch (1989)](https://projecteuclid.org/journals/annals-of-statistics/volume-17/issue-3/The-Jackknife-and-the-Bootstrap-for-General-Stationary-Observations/10.1214/aos/1176347265.full)。
本次通过 Firecrawl 读取该 publisher 页面和摘要，**未声称读取其25页全文**。
缺失网格、条件覆盖和配对组织是本工程的明确选择，不把原论文的渐近结果直接当作
本研究缺失非随机样本的保证。Holm 范围及不可用项处理另对照
[R 官方 p.adjust 说明](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html)。
没有新增 statsmodels、SHAP 或其他强制依赖；使用原有 NumPy/Pandas/SciPy。

每个模型/指标/对比/scope 的子 seed 由全局 seed 和固定身份 SHA-256 派生，输入
行顺序不改变结果，也不修改全局 NumPy RNG。分批向量化抽样，不逐股票—日循环。

## 来源绑定与 CLI

新 `walk-forward` 报告保存 `evaluation_calendar.csv/parquet`，来源为同一次验证
benchmark 的研究窗口，不从工作日频率或 score 日期反推。初次加载与固定输入的
交易日历若变化即失败。manifest 保存 `inference_input_version=1`、日历内容 SHA，
原有整目录 inventory 同时绑定两份文件字节。

`compare-models` 仍先验证四模型同源 config、环境、数据/PIT、OOS keys/labels、
stage cohort、原行情/状态版本。新增日历要求四模型完全相同；所有 CSV/Parquet
消费者只读已验证的 BytesIO 快照，不重开模型报告或当前市场缓存。日历 CSV 必须
与 canonical Parquet 值一致；重新封装 inventory 也不能使不一致的 CSV 合法。

为防止已有 Test 指标与分数不一致，比较器从固定 Test scores/labels **重算评价指标**
并逐值核对保存的 Test stage daily；不加载 pickle、不再次 predict、不 fit、不选参。
随后才调用统计模块。缺日历/新产物无版本/版本 bool 或不一致数据严格失败，输出
目录创建前检查；需要用可信输入重建旧模型报告，不静默使用紧缩日期。
显式 `inference.enabled=false` 表示不做统计检验，旧 programmatic 报告明确 unavailable；
不能把 ICIR 当作显著性证据。任何本地 SHA 都只是来源一致性证据，不是权威数据
真实性或第三方生成时间证明，不解除 BaoStock 的 PIT 语义门禁。

模型比较新增产物：

- `inference_daily.csv/parquet`：只含固定历史 Test 逐日指标；
- `model_inference.csv/parquet`：均值、样本/覆盖、HAC SE/p/CI、Bootstrap CI、
  status、三项主检验的 Holm p 与 nullable reject；
- `inference_audit.csv/parquet`：scope 日期、网格/观测摘要、seed 与研究假设；
- `inference_protocol.json`：完整协议及产生时的三表/协议摘要；
- `model_inference.png`：三项配对差值及个别区间，不可用区间不画成零；
- `summary.md`：解释主范围、探索性结果、缺失、成本前标签和未完成真实 Forward。

CLI 原命令不变。正式 dataset/PIT 验证通过后，四个 `walk-forward --model ...`
与 `compare-models` 使用同一冻结配置。现无可信完整 PIT，不能声称已运行真实五年命令。

## 增量实际验收

已实际执行（隔离 Python 3.9.25）：

```text
python -m pytest -q tests/research/test_model_robustness.py
python -m pytest -q tests/research/test_config.py tests/research/test_model_robustness.py
python -m pytest -q tests/research/test_config.py tests/research/test_model_robustness.py tests/research/test_cli_phase2.py::test_walk_forward_and_compare_commands_are_offline_and_complete --tb=short --junitxml=results/runs/model-inference-first-20261010.xml
python -m pytest -q tests/research/test_cli_model_inference.py tests/research/test_model_inference_report.py tests/research/test_config.py --tb=short --junitxml=results/runs/model-inference-input-report-20261010.xml
python -m pytest -q tests/research/test_model_robustness.py tests/research/test_cli_model_inference.py tests/research/test_model_inference_report.py --tb=short --junitxml=results/runs/model-inference-core-inputs-20261010.xml
python -m pytest -q tests/research/test_cli_phase2.py tests/research/test_cli_stage_diagnostics.py tests/research/test_phase3_synthetic_example.py tests/research/test_comparison_snapshot.py --tb=short --junitxml=results/runs/model-inference-cli-final-20261010.xml
python -m pytest -q --tb=short --junitxml=results/runs/model-inference-full-20261010.xml
python -m examples.research.phase3_synthetic_demo --output results/examples/model-inference-20261010 --seed 42
```

核心首轮40 passed；配置/核心76 passed；四模型 CLI 整链加配置/核心91 passed；
输入/报告/配置83 passed（一个新测试写坏 dtype 的警告已通过显式 object 转换修正，
未改变生产逻辑）；补强核心/输入/报告90 passed，仅13个既有 Matplotlib/Pyparsing
警告。覆盖手算 Bartlett 矩阵、缺失位置、配对样本、强正自相关、固定三项 Holm、
常数方差、不可用 replicate、RNG/行顺序/分批复现、日历字节快照和指标改写拒绝。

四模型合成示例已执行，所有证券、行情、标签及交易日期为人工生成；小 Test
保留默认60日阈值，因此主检验诚实报告 INSUFFICIENT_DATES，不降低阈值制造 CI。
提交前 manifest 记录实际 Git `7b79337` 与 dirty=true。原四模型 CLI/快照/示例
整链102 passed，13个既有警告；另补整链“语义/字节均合法但四模型日历不同”与
“单模型缺日历”拒绝，单项1 passed，输出目录未创建。

首轮全量 **1691 passed、2 deselected、13个既有警告**，XML为
`results/runs/model-inference-full-20261010.xml`，独立解析为1691 tests、0 errors、
0 failures、0 skipped。该轮进程运行期间发现统计图的状态文字与图例重叠；已经把
状态移到图外、图例移到下方，并为合成图添加显式警告。最终数值边界复核另修正
接近1的置信水平与 int64 上界浮点输入；图/核心专项66 passed。该首轮全量是
补强过程的历史证据，不能单独当作最终冻结源码的全套验收。

最终绘图后的示例为 `results/examples/model-inference-final-20261010/`：每模型
仍1 fold/440 Test行/1180 Train-Validation行，统计 daily176行、summary147行；
三项 primary 均44有效日、p/CI缺失。248个模型/比较文件的实际 SHA-256 全部由
独立 PowerShell 复核；从三个 Parquet 和 JSON 重建 RobustnessEvaluation 的
内容摘要也通过，图已实际检查不再遮挡。

真实既有缓存只读复跑 run `20261010T082643.445916Z-real-factor-label-smoke-c3a4b868`
success：153真实市场交易日、14因子有有效值、147成熟标签、尾部6日缺失；4个产物
SHA-256独立核验一致，没有新HTTP下载、PIT/状态核验或RankIC。
`audit` run `20261010T082641.867768Z-audit-9bf3bd7e` success。
正式 `evaluate-forward` run `20261010T083108.927257Z-evaluate-forward-b165fb3a`
正确 failed（Forward disabled），不当作真实 Forward 成功。直接验证当前会员入口仍报
`POINT-IN-TIME UNIVERSE REQUIRED: EFFECTIVE MEMBERSHIP SEMANTICS UNVERIFIED`。

1200个人工交易日/四模型4800条逐日指标、默认2000重采样的性能诊断实际5.421秒，
输出1029条summary、固定3项primary；这不是60万原始股票—日完整流水线计时，
更不是研究实证。导入隔离/编译/diff检查通过，LICENSE blob与上游相同。
最终冻结源码全量回归 **1692 passed、2 deselected、13个既有警告，388.37秒**，
XML为 `results/runs/model-inference-final-full-20261010.xml`。独立核验为1692 tests、
0 errors、0 failures、0 skipped；两个 network 被默认排除，不表示外部网络成功。
该最终轮含绘图修正、近1置信水平、int64边界、跨模型日历不一致与缺日历拒绝。
没有运行带邮件/GUI/联网副作用的 Legacy suite，没有把本研究目标标记完成。

## Changed files 与尚未完成

新增纯统计模块和3组专项测试；扩展配置/公共导出、CLI 日历绑定与比较消费、模型
报告、合成示例及原配置/CLI/快照测试；新增本文并更新方法论/入门/验证/架构文档。
未改 Legacy、LICENSE、费用、Top-K、因子符号、Regime 定义、模型选参或 Forward 启用。

本地代码提交为 `036d31b`（纯统计核心/配置/公式测试）和 `056f834`（日历/CLI/报告/
集成示例与测试）；文档独立提交。不 push、不改历史。提交后的干净工作区验证另用
唯一目录和 run_id 保存，保持上述提交前证据不覆盖；实际 manifest 是环境状态的
依据，不把本文说明当作事前或第三方时间证明。

真实五年 dataset、CSI500 RankIC、四模型含成本净值和真实 Forward 仍不存在。
用户没有外部历史文件，BaoStock 周更新/真实生效语义与499成员问题仍阻断正式研究。
单股153日的真实行情诊断仅验证因子/标签计算，不证明股票池身份或横截面能力。
下一阶段必须继续取得并核验全部真实输入，再依据预注册协议评估，不为漂亮 Test
结果修改统计长度或阈值；原2026-09-14不能补造成当时的 ON_TIME 信号。
