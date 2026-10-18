# 四模型软件就绪独立审计（NO LIVE MONEY）

基线：2026-10-18 开始时最新已验证 main `39eecf869c9c2075ba3f6e3c76aeba3338c63432`。
分支：`codex/model-research-readiness`。只新增独立诊断、独立测试和本文档。
所有输入均为合成数据，软件成功不能作为五年中证500实证研究成功或金融数据资格。

## 开发前代码及测试盘点

| 范围 | 已有实现及证据 | 本任务真正补充的验证 |
|---|---|---|
| Dataset | `dataset/builder.py` 调用既有14因子、每日横截面预处理、PIT成员、状态过滤及标签；`test_dataset_phase1.py` 覆盖重复键、PIT缺口、缺标签 | 从OHLCV而非手工特征开始的四模型完整链路；14因子历史前缀不变性 |
| 标签 | `labels/forward_return.py` 明确 t+1 adjusted open → t+6 adjusted open；`test_labels_phase1.py` | 独立按行情重算标签数值、日期及末6日未成熟行 |
| Walk-Forward | `validation/splitter.py` expanding、purge/embargo、实际exit_date边界；`test_validation_phase2.py`、`test_walk_forward_runner_phase2.py` | 全模型运行时fit/predict实参审计；跨Fold因果扰动；实际边界覆盖purge不足 |
| 四模型 | `models/` 固定FactorScore、Ridge、LightGBM、XGBoost；缺失处理、验证选参、Test单次预测；`test_models_phase2.py`、`test_tree_models_phase3.py` | 同一Dataset的两候选树模型压力与预测复现，不新增模型定义 |
| 阶段诊断 | `WalkForwardRunner` 已输出Train/Validation/Test身份及来源SHA；`test_walk_forward_stage_diagnostics.py` | 统一离线就绪矩阵及分阶段资源证据 |
| 比较合同 | `cli.command_compare_models` 已校验config、环境/代码版本、Dataset/PIT/行情/状态SHA、OOS keys/标签、阶段cohort和日历；`test_cli_phase2.py`、`test_comparison_snapshot.py`、`test_cli_model_inference.py` | 对真实比较入口逐项注入日期、证券、标签、版本与输入SHA反例；保留原验证逻辑 |
| 推断 | `metrics/robustness.py` 已有日度RankIC配对差、Bartlett HAC、保留缺日网格的Moving Block Bootstrap、固定3项Holm；`test_model_robustness.py` 已有独立矩阵和块抽样参考 | 序列相关的过度显著性反例、联合缺失、样本不足及极端溢出拒绝；不重写统计估计 |
| 两级回测 | `backtest/fast.py` 与 `execution.py` 已有下一开盘、成本、T+1/整手/停牌/涨跌停近似；`test_portfolio_backtest_phase2.py`、`test_execution_backtest_phase3.py` | 全链路资源测量、信号/执行日期验收；回测换仓不等同每个标的固定5日强制退出 |
| 既有演示 | `examples/research/phase3_synthetic_demo.py` 已完成手工特征四模型+回测+统计 | 本任务从DatasetBuilder开始，并做未来行情/标签扰动；不复制报告绘图功能 |

## 边界与判断

正式YAML、14因子、39发现候选、模型定义、Golden、PIT/HFQ、Forward、Legacy及冻结CI门禁均不修改。
独立测试置于 `tests/model_readiness/`，不进入现有 `tests/research` 冻结收集。
可选诊断采用namespace子包（无 `__init__.py`），独立覆盖率测量，不改变冻结研究覆盖源清单。
若发现核心缺陷，只记录最小复现和影响；本任务不修核心。

PASS 表示所列合成软件场景通过；FAIL 表示实现或合同违反；BLOCKED 表示外部证据缺失；
NOT_RUN 表示未执行，不能当作通过。Formal及Forward数据资格固定BLOCKED，诊断入口不能授予资格。

## 可复现离线入口

在仓库根目录，使用 `dev/requirements-research-ci.txt` 对应的 Python 3.9 环境。已有
NumPy、Pandas、SciPy、scikit-learn、LightGBM、XGBoost、PyArrow、pytest 即可，未新增依赖。
运行前可设置 `OMP_NUM_THREADS=1`、`OPENBLAS_NUM_THREADS=1`、`MKL_NUM_THREADS=1`。
树模型显式单线程，Ridge的BLAS线程环境被记录；不同机器/依赖版本不承诺字节相同。

```powershell
.\.venv-py39\python.exe -B -X utf8 -m qbot.research.diagnostics.model_readiness `
  --output results/diagnostics/model-readiness/small

.\.venv-py39\python.exe -B -X utf8 -m pytest -q -p no:cacheprovider `
  --basetemp=data/research/model-readiness-pytest `
  --junitxml=results/diagnostics/model-readiness-tests.xml tests/model_readiness

# 可选压力测试：不会进入默认CI；输出目录必须为空或不存在。
.\.venv-py39\python.exe -B -X utf8 -m qbot.research.diagnostics.model_readiness `
  --size scale --skip-comparison-tests --output results/diagnostics/model-readiness/scale
```

默认小规模：12只证券、300个研究交易日，另120日预热；2个完整Test Fold。
规模场景：500只证券、1200个研究交易日，另120日预热，60万Dataset行。
预热数据解决原过滤器在所给日历上计算上市天数和回看窗口的要求，不降低任何既有过滤参数。
合成交易日使用工作日序列，不冒充真实交易所日历、成分调整或复权证据。

小规模默认执行未来行情/标签扰动、同seed重建和四模型重跑，再通过pytest子进程运行真实比较器
的61个反例。比较器测试复用既有临时合成producer fixture，正式校验代码不替换，正向控制先通过。
反例覆盖四模型各自的代码/依赖/config、Dataset/PIT/行情/证券状态/回测输入SHA；删除整日、替换
证券、改变标签值/退出日期/Fold，并重新封装文件SHA，仍须被语义合同拒绝。另检查未重封装字节篡改。
FactorScore基线被篡改时，其自身阶段来源校验可能先拒绝；这是有效的保护路径。

规模模式默认省略重复/未来扰动，以免把运行量放大四倍；这两项明确NOT_RUN，可加 `--probes`。
`--skip-comparison-tests` 明确保留比较反例为NOT_RUN，适用于已有独立反例证据的纯性能测量。
程序退出码非0表示FAIL；退出码0也可能含NOT_RUN/BLOCKED，必须阅读矩阵，不能单看退出码宣称全部就绪。
`software_acceptance` 仅在所有必需软件检查PASS时为PASS；规模、完整正式参数资源测试另列。

## 隔离、因果性及推断验收口径

运行时包裹既有模型fit/predict方法，逐次核对原始DataFrame索引、全部特征和y。
每个候选只能fit于该Fold成熟且有标签的Train；Validation每候选预测一次；所选模型Test预测一次；
Train诊断额外预测一次，不能追加train+validation refit。FactorScore一个固定候选，其余模型各两个
诊断候选；没有扩大或更改正式候选集。purge/embargo=5及额外的0间隔反例均检查实际exit_date边界。

跨Fold的Test主键不能重复。较早Test在标签成熟后进入后续expanding Train属于合法行为，不能
要求所有Fold的训练日期全局互斥。未来扰动以首Fold最后Test信号日为截点：将之后的证券行情
乘7、指数行情乘3，并独立将截点以后才成熟的标签替换为极端值。历史14个原始/处理因子、指数
特征及截至截点的四模型score/selected_parameters必须逐值完全相同；截点前信号但截点后退出的
标签允许变化，它们不能被较早拟合或选参使用。后续Fold的预测允许变化。

独立按价格矩阵重算 t+6/t+1 超额标签并核对末6日NaN。两级回测检查真实成交发生于信号的下一
开盘。标签的固定5日持有和组合每5日换仓是不同合同，股票持续留在TopK时不强制第6日清仓。

主推断完全复用既有日度统计模块，默认60个有效交易日、80% coverage、HAC20lag、MBB20日块、
2000次重采样；只为反例速度将反例的重采样次数设为100，不调整正式默认值。序列相关反例把
HAC标准误与IID标准误比较，要求其显著增大；没有把该比较当成统计估计实现或模拟覆盖率证明。
联合缺失按同日配对取交集；少样本、缺日和常数不制造p值；Inf及有限极值导致的算术溢出必须拒绝。
缺失一项的Holm仍以3项族校正。Fold/Regime等探索性子组不可检验是统计状态，不是软件异常。

## 资源证据和局限

`resources.csv` 分别记录输入生成、Dataset构建、切分、候选训练、各角色预测、逐日指标、
统计评价、Fast回测和Execution回测。`walk_forward_total` 包含训练/预测/评价/诊断哈希等子阶段，
不能与子项相加。测量含独立实参断言和既有诊断开销，不声称为裸训练速度，也未预设性能SLA。

采用Windows GetProcessMemoryInfo / Linux `/proc/self/status`，包含NumPy及树模型原生内存，
不以tracemalloc替代RSS。每10ms采样并纳入阶段起止值，阶段采样峰值是下界，极短分配可能漏采；
另保存OS进程累计内存高水位，不能把累计峰值误标为可独立复位的阶段峰值。每阶段START/END
写入并fsync；异常记录阶段/模型/Fold/异常/traceback，硬终止留下最后未结束的START。
独立测试通过注入MemoryError核对故障位置收据，不实施危险的机器内存耗尽。

大规模使用8/12棵树的诊断候选，**不代表正式YAML完整候选配置的资源验收**；后者保持NOT_RUN。
软件证据不能证明模型优越性、收益、五年数据完整性或真实Forward可运行。
