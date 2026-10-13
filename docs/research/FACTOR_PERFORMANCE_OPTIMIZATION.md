# 14 因子评价流水线性能优化验收

2026-10-11 启动、2026-10-12（Asia/Shanghai）完成；收据时间为 UTC。**SYNTHETIC SOFTWARE DIAGNOSTIC ONLY · NO LIVE MONEY**。
本文记录软件性能与结果等价性；人工股票、成员、证券状态、business-day 日期和价格不能作为真实中证500五年金融研究证据。

## 实现边界

生产修改仅限 `qbot/research/metrics/factor.py` 和私有 `_factor_arrays.py`。
公开 `evaluate_factors` 签名、`FactorEvaluation` 六张表、列/行顺序、dtype、索引、报告文件名及报告内容保持原合同。
14 因子公式、方向、MAD/Z-score、DatasetBuilder、标签、冻结市场状态、PIT/证券状态与 provenance 门禁、正式 YAML、模型/Walk-Forward、Forward 状态、Legacy、交易接口和 LICENSE 未修改。
没有引入依赖、并行计算框架或跨调用缓存。原有用户市场状态诊断文件保留。

优化逐项提交：

- 准备仅含日期、股票、目标、因子和可选状态的窄表，共享日期位置索引、float64 数组和有限值掩码。
- 完整且单日一致的状态列复用 ALL 每日 IC/分位结果；部分状态缺失保留子集计算，覆盖率分母保持原义。
- IC 一次配对过滤；Pearson 保留 `np.corrcoef`，RankIC 使用 SciPy 平均秩和原相关核，目标秩仅在配对掩码相同时复用，不计算未输出的 p 值。
- 自相关每对相邻日一次股票匹配，保留 current/left 行序及原 `dropna` 后观察数（无穷值仍计数），相关计算再过滤无穷值。
- 分位稳定排序等价于 `rank(method="first")`；单次调用缓存真实 `pd.qcut(1..n)` 结果，保留 Pandas 补偿分组均值。
- 换手稳定降序选股保持 `ceil(n/q)`、`nlargest(keep="first")` 成员，以股票整数代码计算原等权权重差。

自相关和换手始终沿完整日历计算；缺日或无效持仓日断开，状态结果按当前日分配。Q5 与换手持仓独立计算，不能因并列或 n/q 边界而错误共用成员。
相关矩阵及 `_summarise_ic` 数值实现保持原样，ICIR 仍为日度均值/样本标准差 `ddof=1`，未年化。
非普通 float64、缺失/非字符串股票键、重复因子名等公共接口特殊输入保留原 Pandas 路径。相关源码入口未删除。

## 冻结参考与比较规则

测试侧 `tests/research/reference/factor_reference.py` 是优化前实现的独立副本，不调用优化辅助函数。
冻结时间点源码为 `18de00687695ab17360e96d8a5c8322930dc857a` 工作区所读生产模块，原字节 SHA-256：
`160c9869f962b28434ff7124418463e7e2530bad3f006d3879660ce1cfdab2e9`。
专用 `.gitattributes` 保留冻结混合换行字节；小型 Golden Parquet 明确不用 Git LFS，可离线检出。
`fixtures/factor_golden/manifest.json` 冻结输入、六张表及逐日平均秩、分位代码、股票成员、换手成员摘要。

比较规则在优化前固定并由参考元数据核验：

- 索引、列、dtype、行序、整数观察数、日期、scope、NaN 位置、正负无穷位置完全一致。
- 排名、分位代码及持仓成员按原 Pandas 原语完全一致。
- 有限浮点满足 `abs(new-old) <= 1e-12 + 1e-12*abs(old)`；未扩大容差。
- 该量级沿用因子公式验证尺度，覆盖常规 float64 运算舍入；不保证病态数值的任意误差。大偏移小方差、1e300、±1e100 取消误差均作差分验证，超差应保留原核或回滚。

差分案例包括正常、独立缺失、相同样本数但不同有效成员掩码、无穷、常数、并列、股票进出、缺日、全无效日、尾部未成熟标签、状态切换、全/部分缺失状态、极端值、接近零日度标准差、单日、打乱行序及重复索引、日历边界、float32、nullable Float64、缺失股票键、分类状态含空类别、字面 ALL 状态及空/错误输入。
另对 n=2..64、q=2/3/5/7 的所有有效组合精确核验 qcut 与 top 成员。
标签缺失不改变分位选择、自相关和换手；原未来突变守卫继续由完整规模入口执行。

## 历史记录与本轮证据

[PERFORMANCE_BASELINE.md](PERFORMANCE_BASELINE.md) 的 209.813 秒评价、20.163 秒构建、252.852 秒诊断和 320.30 MiB 数据集内存均保留为历史记录，未重新认证。
计划阶段单次 202.389 秒函数计时也不是优化收益的分母。

本轮固定源收据：`20261011T110146.606304Z-scale-factor-pipeline-1b707648`。
600000 行源数据集 SHA-256：`15d66f7dd0a4b0a5fe736b988ea164d006b48601edafe8219ae4c14ac2121eb2`。
500 股票、1200 研究日、130 预热日、种子42、14因子，3000 行未成熟尾部标签保留，即末尾6日×500只股票；成熟 `EXCESS_RET5` 为597000行。

2026-10-12源码、源Parquet及原manifest只读复核：`EXCESS_RET5`、
`STOCK_FWD_RET5`、`BENCHMARK_FWD_RET5`各非空597000行、空3000行，
三个字段缺失的是同一批行；`entry_date`空500行、`exit_date`空3000行。
股票与基准收益两字段的空单元格合计6000，但不是6000条不同的未成熟标签，
也没有证据确认此前文字确实由重复计数产生。本次仅修正文档错误，标签算法、
源数据集SHA和旧manifest保持不变。
Windows / i7-14700KF / Python3.9.25 / NumPy1.26.4 / Pandas2.2.3 / SciPy1.13.1。
CPU、BLAS、数值线程环境、包版本及工作区身份另见新收据；不输出无关环境变量。

首个完整工程冒烟运行：`20261011T143111.652817Z-scale-factor-pipeline-6a2b24ef`。
数据集 SHA 与历史一致，六张表通过固定比较策略，未来突变检查通过。
该单次运行评价22.782秒、构建37.047秒、二次重建37.475秒、报告落盘1.595秒；不用于正式配对中位数。
此早期运行的 legacy `process_peak_rss_measured` 标志较宽泛，内存数值应以明确的 Windows Working Set 字段解读；最终版本保留 RSS 标志仅用于 Linux，Windows 使用 `process_memory_measured` 和显式口径。

## 可复现测量入口

所有新运行独占 run_id，不替换历史产物，不将旧 manifest 修改为适配新代码。正式 CLI provenance 校验仍要求按现有合同重建。

完整合成流程（默认 ALL、不绘图的旧行为仍保留）：

```powershell
.venv-py39\python.exe -B -X utf8 -m examples.research.scale_factor_pipeline --stocks 500 --research-days 1200 --warmup-days 130 --timing-detail --measure-memory --report
.venv-py39\python.exe -B -X utf8 -m examples.research.scale_factor_pipeline --stocks 500 --research-days 1200 --warmup-days 130 --evaluation-scope regimes --timing-detail --measure-memory --report
```

固定输入、冻结原版与优化版的配对评价基准：

```powershell
.venv-py39\python.exe -B -X utf8 -m examples.research.benchmark_factor_evaluation --source-manifest results/runs/20261011T110146.606304Z-scale-factor-pipeline-1b707648/manifest.json --repeats 5 --warmup-days 20 --scopes all regimes
```

每个样本一个新进程；首次调用无计算预热，随后五对样本各先用前20日预热，再完整评价，所有单次缓存重新创建。
版本顺序逐对交替，性能进程串行运行，cProfile 不进入正常 wall-time 加速比例。
导入已在计时前完成；输入加载/哈希单列，OS 文件缓存不主动清除、不声称冷盘。
每对结果必须通过全部六表比较才会写成功汇总；参考、生产、数组核、计时器及基准入口 SHA 在开始/结束核对。
每个 worker 也保存完整六 CSV、五图和 Markdown 报告及产物哈希。

`--input-case sparse` 在同源600000行上固定种子删除2%股票日及一个完整中间日，增加5%因子缺失和3%目标缺失，保留原完整日历；作为独立稀疏/变动股票池验收，不冒充标准满格600000行。
单独 profile 使用规模入口 `--profile`，结果明确 `profiled_not_normal_wall_time=true`。

详细计时包含 Pearson、RankIC、分位、自相关、换手、相关矩阵、汇总、状态行分配、准备工作和各报告文件。
小核时间包含在外层统计时间中，**不能相加**；两核之外的配对过滤/排行缓存等成本仍在 `_daily_ic` 中。
`total_before_output_hashing` 保留旧定义。`performance-completion.json` 单独追加结束收据 SHA、哈希/收据耗时及含成功收据的总时间，避免循环自哈希；它不重新写 measurements 或旧收据。
完整诊断含两次构建；其总时间不能称为单次 build→evaluate→report 时间。

## 内存口径

Windows 用标准库 ctypes `GetProcessMemoryInfo`，分别记录 Working Set、进程生命周期 Peak Working Set、Private Commit，字段依据 [Microsoft PROCESS_MEMORY_COUNTERS_EX](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex)。
50ms 后台采样按阶段记录最大 Working Set；采样受调度影响，不是阶段精确峰值，嵌套短阶段可能没有样本。
内存按当时最内层阶段记录；评价期间的采样最大值应取准备、IC、分位、时序、矩阵和组装等阶段的最大值，不能只取外层 `factor_evaluation` 的非嵌套样本。
生命周期峰值在评价结束、报告开始前取快照，仍包括导入、加载和预热；完整流程另含构建及未来突变重建，不能当评价阶段独占峰值。
Linux 有 `/proc/self/status` 时使用 VmRSS/VmHWM，其他平台明确 unsupported。
DataFrame deep bytes 独立保留，不称为进程峰值。未用 tracemalloc 结果冒充 RSS。

## 回滚与复核

共享上下文、IC、自相关、分位、换手均有独立提交，可普通 revert；不重写历史、不自动 push。
任何离散结果/缺失位置差异、超容差浮点、非相邻日期连接或门禁变化均应撤回对应优化。
若后续同环境连续三次配对测量出现耗时或峰值内存恶化，应回滚该候选并保留失败产物。
在串行路径仍有实测瓶颈前，不引入局部并行、Spark/Dask/GPU；Builder、相关矩阵和报告数值算法不扩展本次范围。

## 本轮配对结果

配对运行：`20261011T145437.545384Z-factor-performance-benchmark-11eb6365`。
表中为五次重复中位数，首次调用另列；采样指标受本机背景负载和调度影响，不作为其他硬件性能保证。

| 范围 | 原版评价秒 | 优化评价秒 | 降幅 | 原版范围秒 | 优化范围秒 |
| --- | ---: | ---: | ---: | --- | --- |
| ALL | 180.162 | 13.253 | 92.64% | 169.595–206.844 | 10.217–19.551 |
| ALL + BULL/BEAR/SIDEWAYS | 334.969 | 14.750 | 95.60% | 281.396–345.380 | 9.935–21.467 |

ALL 首次调用197.088→21.952秒，不进入重复中位数。其五对结果及首次配对均通过六表 Golden。
状态首次调用264.368→21.893秒，同样不进入重复中位数。全部12对（含首次）通过固定容差及精确离散合同。
性能 worker 串行；观测到另一个持续运行的 Python 进程和并行工作区变更，**整机背景负载未隔离**。
代码、包、硬件、输入和单次缓存策略固定，但不能将这些范围较宽的测量称为独占空闲机器的受控实验。

| ALL 阶段，独立中位数 | 原版秒 | 优化秒 |
| --- | ---: | ---: |
| IC/RankIC 合计 | 71.106 | 3.155 |
| Pearson 路径，包含在上行 | 19.813 | 0.741 |
| RankIC 路径，包含在上行 | 35.174 | 2.042 |
| 分位收益 | 51.768 | 5.036 |
| 自相关 | 41.393 | 2.937 |
| 换手 | 15.611 | 0.690 |
| 相关矩阵 | 0.494 | 0.438 |
| 汇总 | 0.008 | 0.008 |
| 完整报告落盘 | 0.822 | 0.801 |

原版相关路径含重复 Pandas 过滤和 SciPy 未输出的 p 值计算；优化路径是数组核，不能将该行解释成纯 NumPy/SciPy 数值核之间的对比。
阶段各自取中位数，不能相加重构总时间中位数；内嵌核也不能与外层合计相加。
ALL 的评价结束前进程生命周期 Peak Working Set 中位数1387.69→1099.62 MiB，包含导入、读取和预热，下降约20.76%。
状态模式同口径的原始中位数1939439616→1280253952 bytes；不能与含两次构建的完整流程峰值混算。

## 完整流程重复验证

归档复现脚本、逐次记录及汇总：
`results/diagnostics/factor-performance-validation/full-flow-20261011T151233-d04bdd7e/`。
每个 scope 一次首次调用、五次独立进程重复；未额外运行评价核预热，构建本身是正常流程的一部分。
12份运行均重新生成固定种子输入、调用原 Builder、完成未来突变重建、完整报告、全部产物哈希及六表参考比较，数据集SHA均与历史一致。
该系列没有执行原版完整流程的同环境配对，**不能从历史252.852秒推导本轮全流程加速比例**。

| 完整诊断阶段，中位数秒 | ALL | 状态模式 |
| --- | ---: | ---: |
| 构建 | 39.050 | 37.287 |
| 未来突变重建与核验 | 41.137 | 34.471 |
| 评价 | 24.688 | 15.864 |
| 完整报告落盘 | 1.708 | 1.161 |
| 结果写入 | 2.044 | 1.364 |
| 输出哈希 | 0.424 | 0.330 |
| 成功收据写入 | 0.012 | 0.006 |
| 合计，旧定义的输出哈希之前 | 109.692 | 91.422 |
| 合计，包含成功收据、排除解释器启动 | 110.100 | 91.758 |
| CLI进程，包含解释器启动 | 111.659 | 93.180 |

CLI范围分别98.112–115.631秒、69.582–112.139秒。完整流程内的评价阶段与独立加载后的评价基准具有不同前序负载和预热路径，应分别解读。
完整流程 Peak Working Set 中位数分别2349555712、2349084672 bytes（约2.24GiB）；历史未测量同口径峰值，不能宣称全流程峰值下降。
各阶段独立取中位数，不能逐项相加重构整体中位数。

## 稀疏输入与最终验收

稀疏配对运行：`20261011T161429.402515Z-factor-performance-benchmark-5c39fbfe`。
实际587621行，完整日历仍为1200日；两个scope各一次首次调用、一次预热重复。四对均通过六表、行序/dtype/缺失位置和产物哈希核验。
重复样本为 ALL 199.125→10.190秒、状态模式195.930→10.438秒；**仅一次重复，不用于主加速结论**。
首次分别251.150→23.016秒、197.809→10.480秒。不同背景负载及样本规模不能混作统一分母。

新 profile 运行：`20261011T145354.533637Z-scale-factor-pipeline-99b197f7`，500股票×100研究日。
`qcut`实际一次、`spearmanr`零次、`merge`零次、`_safe_correlation`零次；平均秩仍由SciPy计算。
这个独立合成样本含六日未成熟标签，与计划阶段从600000行截取前100日的输入不同，不做两次profile秒数的加速比较。
主结论完全来自完整600000行配对及逐阶段计时。

最终全量离线回归：**2588 passed、2 deselected、88 warnings，404.69秒**。
显式收集 `tests/research`，默认排除网络；JUnit独立核验2588执行、0 failures、0 errors、0 skipped，两个网络测试未收集。
该计数包含运行期间新增的未提交通达信测试；这些文件及本地市场数据文档保留，未纳入本次提交。
第三方弃用警告、常数/全缺失矩阵的空均值警告和分类状态原GroupBy的observed默认值警告均保留，未通过屏蔽警告或放宽断言制造通过。

```powershell
.venv-py39\python.exe -B -X utf8 -m pytest tests/research -q --junitxml=results/diagnostics/factor-performance-validation/<new-id>/offline-research.xml
.venv-py39\python.exe -B -X utf8 -m pip check
```

每次为 `<new-id>` 建立新的目录，避免覆盖旧JUnit。最终文件与追加审计位于：
`results/diagnostics/factor-performance-validation/final-20261011T163245-edd3fc80/`。
`verification.json` SHA-256：`3a11dd27781e0e751f4695313418106d191190226986c89ffa0b09d6d3439b61`。
审计驱动 `verify_evidence.py` 留存，绑定两个配对汇总、完整流程汇总、JUnit及自身源码摘要，复核旧收据和所有历史产物保持原SHA。
全部16对的有限值最大绝对差：IC/summary/分位/自相关/相关矩阵均0；换手最大`2.6645352591003757e-15`，来自原权重差公式的求和顺序，远低于事前固定容差。
没有改动冻结参考或其期望表。冻结过程中夹具目录、LFS及换行问题均通过独立修正提交处理；早期插桩测试未达IC阈值的测试输入问题也已修正，不改变生产最小横截面。

验收结果：

- [x] 14因子、统计定义、方向、ICIR样本标准差和未年化口径保持；指定生产边界路径Git差异为空。
- [x] 六表、排名、分位/持仓成员、计数、日期、dtype/索引与缺失合同通过Golden；容差没有放宽。
- [x] 正常/缺失/并列/极端/股票池变化/状态切换/特殊输入/空表错误合同通过；原测试没有删除或放宽。
- [x] 自相关与换手遵循完整相邻日历，标签缺失不改成员；12次全规模未来突变检查通过。
- [x] Python3.9全量离线回归、测量工具测试、包依赖检查通过。
- [x] ALL和状态模式有五次配对重复；每份完整报告为六CSV、五图、一Markdown；全流程另有五次重复。
- [x] 数据集deep bytes、阶段采样最大值、评价前序生命周期峰值和全流程峰值分别标记；未把Working Set伪称精确阶段RSS。
- [x] PIT/证券状态门禁、正式配置、四模型/Walk-Forward、Forward、LICENSE和Legacy未因本任务改变；真实研究阻塞保留。
- [x] 原产物与审计保留，新增产物明确绑定合成诊断/NO LIVE MONEY；本地独立提交，无push、force-push或历史重写。

本次两个标准scope均超过50%挑战目标。耗时范围较宽、整机背景负载未隔离，实际稀疏比例和未来公共接口的慢路径比例会影响可迁移收益。
Builder和全流程内存仍是后续独立profile的对象；本次不扩大到金融协议、数据门禁或模型调参。
