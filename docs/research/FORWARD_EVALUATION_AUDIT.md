# Forward 成熟标签关联与不可覆盖评价报告

范围：Qbot FactorLab 软件正确性与可复现演示。**没有取得真实 Forward 实证结果**。
本次工作继续完善完整预测存档，不解除 PIT 门禁，不重写 Legacy，不连接券商。

## 实现结果

- 配置与研究契约 schema 2 冻结 `evaluation_version_policy: FIRST_ON_TIME`；正式
  和 smoke YAML 均仍 `forward.enabled: false`。没有擅自选择新的真实激活日。
- `forward/evidence.py` 验证日期范围内的原始信号、全横截面预测、内容摘要与成功
  producer 快照。身份不一致、orphan、非法目录或坏哈希直接失败；没有合格完整
  ON_TIME 记录时不输出空成功。每个日期选择最早的完整当日收盘后版本；最早时间
  同值时只接受无歧义的自动递增版本号。后续、迟到与旧 Top-K-only 记录有排除原因。
  不读取未来标签选版，不重新预测旧日期。
- `forward/evaluation.py` 复用生产标签与预测指标，按基准实际交易日历映射
  t+1 → t+6，仅使用截至 as-of 的已观察复权开盘价。保留原分数、排名、完整横截面、
  未成熟行及原证据身份，区分 MATURE、MATURE_MISSING_PRICE、IMMATURE。
  缺价不填充、不当作零收益、不晋升第 K+1 名。
- 评价输出 IC、RankIC、ICIR、Top/Bottom 和 spread，按 Year/Quarter/Regime
  分组，保留覆盖分母。未保存市场状态时追加 EVALUATION_MARKET_REGIME；MA20/MA60
  仅用信号当日及此前信息，不声称它是原信号保存字段。
- CLI `evaluate-forward --as-of ... [--start ... --end ...]` 验证真实时钟、收盘、
  observed benchmark session、原预注册、冻结 bundle、干净 Git 与源码身份。
  与日终信号共用独占流程锁，只读取原始预测和同一校验缓存快照。
  每个曾预测股票的覆盖区间必须齐全；不按当前成分删历史股票，不自动联网补数据、
  重建特征、fit 或 predict。来源与 cache generation 摘要进入运行与报告清单。
- `reports/forward.py` 用新 run_id、staging 与原子发布追加13个 CSV/Parquet/图片/
  Markdown 文件及 manifest。CSV 与 Parquet 的值、列、类型和行数互相验证。
  producer 成功后追加自包含 completion receipt，默认 reader 拒绝 orphan、异常
  文件集合、链接、摘要不符或不匹配的成功 producer。不覆盖已有报告或原信号。

## 使用方式

真正预注册实验具备后，单独更新行情缓存，在标签成熟后运行：

```powershell
.\.venv-py39\python.exe -m qbot.research.cli evaluate-forward `
  --as-of YYYY-MM-DD --config configs/research/csi500_5y.yaml
```

报告在 `results/forward/evaluations/<run_id>/`。生产 CLI 不接受注入历史时钟，
as-of 不能晚于上海当前日，当天需15:30以后，且是缓存中实际观测的基准交易日。
本次源码/契约新增会改变摘要；新正式实验必须基于最终审核版本事前激活和冻结，
不能偷偷给旧实验换源代码。

另有**纯合成软件演示**，不执行正式 Forward CLI：

```powershell
.\.venv-py39\python.exe -m examples.research.forward_evaluation_synthetic_demo `
  --output results/examples/forward-evaluation-20261009 --seed 42
```

2099年日历、信号时刻、价格、股票、激活/模型/数据身份都是人为构造；预期展示
FIRST_ON_TIME、后续/迟到版本排除、成熟与未成熟标签，以及排名第一但缺开盘价时
Top-K 不晋升。输出、README、manifest 和 summary 明确标注 SYNTHETIC SOFTWARE
DEMO ONLY。正负 IC 均不能支持 CSI500 Alpha 或模型优越性结论。

## Changed files

配置：`configs/research/csi500_{5y,smoke}.yaml`、`config/models.py`、
`forward/contract.py`。核心：`forward/evidence.py`、`forward/evaluation.py`、
`reports/forward.py`、`cli.py` 及 forward/reports 公共导出。
示例：`examples/research/forward_evaluation_synthetic_demo.py`。
测试：新 evidence、evaluation、report、CLI、synthetic example 五组，扩展契约测试。
文档：本审计、FORWARD_TEST、GETTING_STARTED、RESEARCH_METHODOLOGY、
ARCHITECTURE_AUDIT、PHASE4_DELIVERY_REPORT 与原预测审计的后续说明。

## 增量测试与命令证据

已实际运行核心与证据专项合计136项通过；CLI 新测试增至16项，连同旧 Phase 4
CLI 与契约合计34项通过。第一轮 CLI fixture 忘记必需 project/factors 字段，
出现12个 setup error；只修 fixture 未放松配置。随后测试发现新 CLI 错将目录传给
文件锁导致7项失败，修为现有日终流程锁路径后全部通过。每个模块先测试再集成。

第一次全套实际执行：1477 passed、2 deselected、13个既有 Matplotlib/Pyparsing
警告，226.07秒；XML `results/runs/forward-evaluation-full-20261009.xml` 独立解析
确认1477 tests、0 errors、0 failures、0 skipped。之后日期图修正重叠刻度，并添加
测试；报告/示例/CLI 联合74项通过。另补 synthetic completion 失败的 manifest 必须
记为 failed，避免“已写报告但收据失败”被称为成功。最终源冻结后的全套回归为
**1479 passed、2 deselected、13个既有警告，424.27秒**，输出
`results/runs/forward-evaluation-final-full-20261009.xml`；验收跨上海10月9日晚至10月10日。
收据失败补强后报告/示例专项59项通过（44+15）。

实际执行命令（Python为 `.venv-py39/python.exe`，3.9.25）：

```text
python -m pytest -q --junitxml=results/runs/forward-evaluation-full-20261009.xml
python -m pytest -q --junitxml=results/runs/forward-evaluation-final-full-20261009.xml
python -m qbot.research.cli audit --config configs/research/csi500_smoke.yaml
python -m examples.research.forward_evaluation_synthetic_demo --output results/examples/forward-evaluation-20261009-readable --seed 42
python -m examples.research.real_factor_label_smoke --config configs/research/csi500_smoke.yaml --start 2023-06-01 --end 2024-01-12 --read-only-cache-root data/research/diagnostics/download-contract
python -m qbot.research.cli evaluate-forward --as-of 2026-10-09 --config configs/research/csi500_smoke.yaml
python -m compileall -q qbot/research examples/research/forward_evaluation_synthetic_demo.py
git diff --check
```

合成报告：`results/examples/forward-evaluation-20261009-readable/evaluations/`
`20261009T155555.273204Z-evaluate-forward-8b771d8b/summary.md`。实际选择3/5版本、
保留18预测（成熟5、成熟缺价1、未成熟12）；原版本摘要未变，报告完成收据验证
通过。另一个实际执行目录 `forward-evaluation-20261009-root` 的35个原信号/收据
文件和13个报告文件均用独立 PowerShell SHA-256 与 manifest 逐项核对。所有日期/
信号时刻/数据/身份为 artificial；唯一成熟横截面 RankIC为-1，原样报告，不选后来
的更好版本。四张 PNG 已生成，coverage 图片检查后日期旋转显示，无重叠。

真实缓存复跑 run `20261009T154958.053233Z-real-factor-label-smoke-8efbb15a`：
153个实际行情交易日、14因子均有有效值、147成熟标签、尾部6日缺标签；4个输出
SHA 独立核对一致。只读既有单股票/基准缓存，不调用 Provider 网络端点，不表明
CSI500 成员身份、证券状态或横截面 RankIC。没有500股任务或本轮网络失败股票名单。
审计 run `20261009T154959.029847Z-audit-b29d0900` 成功；真实时钟下正式
evaluate-forward run `20261009T154959.029847Z-evaluate-forward-0f45e871` 正确失败：
Forward Test is disabled，outputs为空，没有新信号或正式评价。不能把预期门禁拒绝
称为正式端到端通过。上述清单如实记录提交前 dirty 工作区及基线 Git 7181b25。

独立只读审查重算 t+5 未成熟/t+6 成熟、第一名缺 entry 开盘价时 Top1 label_count=0
且第二名不晋升，核对原字段、选版、同一缓存 generation 与 completion 绑定，未发现
需修复的正确性问题。原 LICENSE Git blob 与固定上游 f0425ae4 一致。编译与 diff
检查通过；网络测试默认不运行，不用 synthetic 替代真实网络/实证验收。
独立解释器导入 forward/reports 后没有 wx、Qlib、Backtrader、easyquant 或 Legacy
GUI/engine 模块，研究 API 不引入实盘或 GUI 依赖。

## 已知限制与后续

用户没有外部历史行情、逐日成分或证券状态文件。BaoStock 官方接口的连接成功
不证明 actual effective membership；研究起点返回499且周快照的生效语义未核验。
正式 PIT 保持失败，不回退当前成分。详见
[BAOSTOCK_SOURCE_AUDIT.md](BAOSTOCK_SOURCE_AUDIT.md)。因此仍没有真实500股完整
五年数据集、正式横截面 RankIC、五年四模型结果或真实 Forward 信号。

这些 Top/Bottom 未来收益是**开盘到开盘的成本前超额标签，不是实际成交、Paper NAV
或执行后组合收益**。本地 SHA/时钟/提交只提供可审计一致性，不是第三方不可篡改
时间证明。小横截面 N<2K 时，沿用预测指标的互不重叠 capped tails，Top/Bottom
数量会缩减，不能读成实际 Top20 组合收益。基准源若遗漏整交易日，单凭它派生的
日历无法独立发现；完整正式源仍需外部核验。所有输入先作 schema 校验再截断：
未来合法价格变化不改变过去评价；
未来非法 schema 会严格失败，而非作为过去计算的数据。

Q4 的完整 Train/Validation/Historical Test/Real Forward 实证差距仍不能回答：
新模块补齐成熟评价软件，但未补齐完整 Train IC 报告，也没有真实输入和事前批准的
新激活日。原2026-09-14永久不得补写 ON_TIME。后续继续核验正式 PIT/行情来源，
补充训练期与验证期预测诊断，并在真实数据具备后按冻结协议运行；负结果原样报告。

后续软件进展：历史 Train/Validation/Test 逐 fold 诊断与来源绑定已加入，补齐了
当时记录的训练报告软件缺口；真实数据和真实 Forward 结果仍未补齐。原验收数字
和限制是该提交的历史证据，不倒写为当前全部验收，后续见
[STAGE_DIAGNOSTICS_AUDIT.md](STAGE_DIAGNOSTICS_AUDIT.md)。
