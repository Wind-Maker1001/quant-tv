# Train / Validation / Historical Test 分阶段诊断

范围：补齐研究问题 Q4 的历史阶段评价软件与可复现证据，**不是完成真实五年或
真实 Forward 实证**。用户没有外部历史文件；正式 PIT 门禁与 Forward 默认关闭不变。

## 研究解释

| stage | 用途 | 可作何种解释 |
| --- | --- | --- |
| TRAIN_IN_SAMPLE | diagnostic_only | 已选模型对自身训练期的拟合诊断，不是样本外预测 |
| VALIDATION_SELECTION | selection_and_diagnostic | 已用于选择预注册候选，存在 selection optimism，不是独立最终留出 |
| HISTORICAL_TEST | evaluation_only | 已选 Train-only 模型对历史测试期的一次预测 |

每个 fold 使用同一个已选模型，拟合范围固定 `train_only`，不做 Train+Validation
重拟合。所有候选仍只在有成熟标签的 Train 行上拟合，再各预测 Validation 一次。
选中候选的已有 Validation 分数直接保存；不重新预测 Validation。Test 先预测一次，
之后才追加选中模型对完整已审计 Train 的诊断预测，Train 诊断指标不能反向参与选参。

训练期中标签缺失的行仍可被评分，保留在覆盖率分母；这些行没有进入模型 fit。
splitter 原有 purge/embargo、标签窗口完整性与成熟边界检查不变。
扩大训练集会在不同 folds 重复包含旧日期，不能把所有 Train folds 拼成一条独立
收益序列或一个总体训练 IC。指标逐 fold、逐 stage 单独评价，再列 Year/Quarter/
Regime 等分组。Test 的主 `predictions` 表、指标和两级回测输入仍只有 Test。

## 输出

每个新 `walk-forward` 模型报告增加：

- `stage_predictions.csv/parquet`：已选模型的 Train/Validation 原始分数、排名、
  标签、开平仓日期、fold、stage、fit_scope、selection_usage；不复制 Test 原表。
- `stage_prediction_daily.csv/parquet`：三阶段逐交易日 IC、RankIC、Top/Bottom
  成本前未来收益、spread 和标签/分数覆盖率。
- `stage_prediction_summary.csv/parquet`：按 fold/stage 独立汇总 IC/RankIC、ICIR、
  正值比例、尾部收益与分组指标；不生成 pooled Train 总体。
- `stage_prediction_audit.csv/parquet`：每 fold 三行，保存实际信号/标签窗口、
  成熟边界、全体/有标签/已评分行数、模型路径、所选及实际解析后的模型参数、
  特征列表、目标、固定选参指标、Top-K、最小横截面、seed 与内容摘要。
- `stage_ic_comparison.png`：逐 fold 三阶段 IC/RankIC；样本不足时保留 NaN，
  不把缺失显示为零。

所有表保留原值。Top/Bottom 成员先由 score 固定，缺标签不晋升后续候选。
这些未来收益是 **next-open 到 next-open 的成本前超额标签，不是成交后 NAV**。
模型相同也不代表不同时间段的难度相同；不能仅凭 Train-Test 差值证明过拟合。

`compare-models` 在同一输入/配置/环境合同下合并三个小型 stage 指标/审计表。
庞大的 Train/Validation 原始预测留在逐模型目录，不四模型拼接，不重复累计训练行。
比较主表仍只含 Test 绩效，不自动选赢家。summary 明确说明训练内诊断和验证选参偏差。

## 来源绑定与严格失败

新增运行清单字段：`stage_diagnostics_version=1` 与
`stage_diagnostic_provenance`。合同固定三阶段用途、一次 Test、Validation 分数复用、
train_only 与逐 fold 评价。provenance 绑定 dataset/PIT 版本、四表内容摘要/行数和
真实保存的每 fold 模型文件摘要；原有全目录产物字节 SHA-256 也保留。

CLI 在同一份已经通过正式来源校验的内存 dataset 上重新验证及拆分，仅重算 keys、
特征、标签窗口、状态和实际有标签 Train 子集的内容摘要，**不 fit、predict 或选参**。
审核器检查三阶段完整性、唯一键、选中模型/协议一致性、实际窗口、成熟边界、
计数和 score/metric 摘要；保存模型必须位于该报告 fold_models 内且匹配目录 inventory。
这些本地摘要证明一致性，不替代权威 PIT 语义或第三方时间证明。

比较器先验证共享输入与原有 Test 键/标签，再验证新增诊断；CSV/Parquet 均读取
通过文件摘要核验的同一字节快照，后续不得重开可能已被修改的路径。
三个小型指标/审计 CSV 的列、行和单元格还必须与可信 Parquet 的规范序列化一致；
仅修改 CSV 并重新计算 inventory 不会被接受。比较使用这些 Parquet 快照，保留
浮点精度与 datetime64 类型，而不是再次从 CSV 推断类型。
Train 原始 CSV 只流式哈希；其 Parquet 在逐模型诊断核验后释放。模型只核对摘要，
比较不反序列化 pickle。四模型的 stage cohort 和有标签 fit-input 摘要必须相同；
分数与合法的模型参数当然可以不同。

缺表、坏哈希、错误角色、来源/模型/协议不一致都严格失败，不生成部分成功比较。
仅四字段全部为空的旧 programmatic `WalkForwardResult` 可写旧报告，明确
`Train/Validation diagnostics unavailable`，不事后重评分或推测。正式新 CLI 必须完整；
四模型新旧诊断不能混合比较。新产物缺 producer version/provenance 不能冒充旧报告。

## 运行方式

真实数据具备且同一配置正式 dataset 已验证后，原命令不变：

```text
python -m qbot.research.cli walk-forward --model ridge --config configs/research/csi500_5y.yaml
python -m qbot.research.cli compare-models --config configs/research/csi500_5y.yaml
```

其他三个模型使用同样的 `walk-forward --model ...`。新增源码会改变输入 provenance，
旧 dataset 或模型不能偷偷换新代码消费；应按现有合同从可信原始输入重建。

可重复运行的软件示例（全部行情、标签、证券和交易日期为人工构造）：

```text
python -m examples.research.phase3_synthetic_demo --output results/examples/stage-diagnostics-unique --seed 42
```

应使用未占用的新 output 目录，保留历史示例证据。示例完整配置、实际 Git/dirty 状态、
Python/包版本、synthetic input 摘要与逐文件 SHA 都进入 manifest；不绕过正式 CLI 的
PIT 来源校验。它的直接模型/报告 API 演示不是正式五年 CLI 实证。

## 实际增量验收

新诊断/来源绑定/报告及旧字节快照测试合计103项通过，13个既有 Matplotlib/Pyparsing
警告，51.93秒。旧四模型 CLI 整链曾发现两处错误提示优先顺序回归，保留并优先运行
原有输入/OOS 门禁后单项通过，71.09秒；没有放松校验或改掉原有失败断言。
第一轮新增 CLI fixture 错设 quantiles=5、min_cross_section=4，导致34个 setup errors；
只改 fixture 为4分位，正式配置约束不变。另补 fixture 的空执行报告及纠正新测试
英文单复数断言，不替代真实执行链路覆盖。

已实际运行四模型合成示例：`results/examples/stage-diagnostics-20261010/`，
2020-01-02～2020-12-31、10个人工证券、每模型1 fold、440个 Test 行、1180个
Train/Validation 行、3个 stage audit 行。快速/执行交易各模型均非空；独立 PowerShell
核对240个报告/模型/比较文件的 SHA-256 全部一致，图已检查可读。
该次记录实际基线 Git `6f4ccda` 与 `git_dirty=true`，不能声称提交后干净验收。
扩大训练集和训练日期重复的守卫另由多 fold 单测与四模型 CLI 整链检验。

随后扩展原四模型 CLI 检验新旧诊断不能混合、三阶段比较表和主 Test 边界；连同
新增 CLI 来源测试与示例测试 **80 passed**，13个既有警告，251.25秒，XML 为
`results/runs/stage-diagnostics-cli-20261010.xml`。示例/旧报告专项另6项通过。

本次实际执行（解释器 `.venv-py39/python.exe`，Python 3.9.25）：

```text
python -m pytest -q tests/research/test_cli_stage_diagnostics.py tests/research/test_walk_forward_stage_diagnostics.py tests/research/test_model_stage_diagnostics_report.py tests/research/test_comparison_snapshot.py
python -m pytest -q tests/research/test_cli_phase2.py tests/research/test_cli_stage_diagnostics.py tests/research/test_phase3_synthetic_example.py --junitxml=results/runs/stage-diagnostics-cli-20261010.xml
python -m examples.research.phase3_synthetic_demo --output results/examples/stage-diagnostics-20261010 --seed 42
python -m examples.research.real_factor_label_smoke --config configs/research/csi500_smoke.yaml --start 2023-06-01 --end 2024-01-12 --read-only-cache-root data/research/diagnostics/download-contract
python -m qbot.research.cli audit --config configs/research/csi500_smoke.yaml
python -m qbot.research.cli evaluate-forward --as-of 2026-10-09 --config configs/research/csi500_smoke.yaml
python -m compileall -q qbot/research examples/research/phase3_synthetic_demo.py
git diff --check
```

真实缓存只读复跑 run `20261009T175759.432841Z-real-factor-label-smoke-63dfde9a`
success：153行情交易日、14因子均有有效值、147成熟标签、尾部6日缺标签；四文件
SHA 独立核对一致，没有新 HTTP 下载或500股任务。Windows manifest 一次临时
winerror=5 经原有重试成功，warning 保留。`audit` run
`20261009T175801.917302Z-audit-62201417` success。真实时钟下正式 `evaluate-forward`
run `20261009T175858.016567Z-evaluate-forward-73c90dea` 正确 failed：Forward disabled，
outputs 为空。这不是正式 Forward 端到端成功；三清单如实记录提交前 dirty 工作区。

第一轮冻结全套回归 **1573 passed、2 deselected、13个既有警告，602.71秒**，XML
`results/runs/stage-diagnostics-full-20261010.xml`。后续只读复核发现比较还从 CSV
汇总新增指标，而 producer 语义摘要基于 Parquet；于是进一步补强三小表的成对一致性
与保留精度/日期类型的 Parquet 汇总，并添加针对重新计算文件 inventory 的测试。
该轮1573是补强之前的历史证据，不是后来源码的最终全套验收。
成对校验首轮48项通过；四模型 CLI 单项通过但暴露一个新增 pandas all-NA concat
FutureWarning。现对比较审计表的可选 selected_alpha 列显式使用 float64，保留缺失
值与列、不回填 alpha。补强专项最终 **49 passed**、13个既有警告，25.13秒；
XML `results/runs/stage-diagnostics-paired-final-20261010.xml`。

最终源码冻结后实际执行：

```text
python -m pytest -q --tb=short --junitxml=results/runs/stage-diagnostics-final-full-20261010.xml
```

**1579 passed、2 deselected、13个既有 Matplotlib/Pyparsing 警告，608.21秒**。
独立 XML 解析为1579 tests、0 errors、0 failures、0 skipped；两项 network 被默认
排除，不代表本次外部网络成功。新增 concat warning 已消除。最终全套覆盖三小表
CSV/Parquet 一致性、保留日期/精度的比较、可选 alpha 的缺失证据与全部原有回归。
源码/依赖隔离检查通过，无 wx/Qlib/Backtrader/easyquant/Legacy GUI/engine 导入；
原 LICENSE blob 与固定上游 f0425ae4 一致。编译和 diff 检查通过。

代码已按功能创建本地提交：`403d58e`（runner 与分阶段诊断测试）、`b740427`
（CLI/报告来源绑定、示例及集成测试）。文档另独立提交，没有 push、改历史或修改
研究参数以追求收益。这里只完成三阶段诊断增量，不把总体研究目标标为完成。

## Changed files

核心：`validation/walk_forward.py`、`reports/model.py`、公共导出与 `cli.py`。
测试：新增 runner、report、CLI 三组 stage diagnostics，扩展旧 runner/report/四模型 CLI
及 phase3 synthetic example。示例：`examples/research/phase3_synthetic_demo.py`。
文档：本审计、VALIDATION、GETTING_STARTED、RESEARCH_METHODOLOGY 及架构/Forward
审计的后续说明。没有修改 Legacy、LICENSE、PIT 门禁或真实 Forward 启用配置。

## 尚未完成

正式真实五年 CSI500 dataset、横截面 RankIC、四模型净值及真实 Forward 结果仍缺。
BaoStock 周更新/调样生效语义未核验，起点查询499成员，正式研究仍失败；见
[BAOSTOCK_SOURCE_AUDIT.md](BAOSTOCK_SOURCE_AUDIT.md)。单股票153交易日的真实因子/
标签示例只证明该小样本价格计算，不证明 CSI500 身份、证券状态或横截面预测能力。
原2026-09-14永久不能补写 ON_TIME。软件补齐三阶段诊断后，Q4 的完整实证答案仍
必须等待可信历史数据、事前批准的新真实激活日与成熟真实 Forward 标签。
小横截面 N<2K 时，沿用预测指标的互不重叠 capped tails，Top/Bottom 数量会缩减；
不能把这种标签统计解读为实际完整 Top20 组合收益。
