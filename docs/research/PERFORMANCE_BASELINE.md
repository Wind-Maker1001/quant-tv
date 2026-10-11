# FactorLab 因子流水线规模验证

验证日期：2026-10-11。**仅合成数据工程诊断，不是 A 股历史实验。**

## 范围与复现入口

`examples/research/scale_factor_pipeline.py` 用固定随机种子生成价格、成员、上市日、
ST/交易状态及基准，调用生产 `DatasetBuilder` 和 `evaluate_factors`。全部日期
来自人工 business-day 序列，并非中国交易所日历；生成的证券代码不是经过核验的
中证500成员。该入口不调用 Provider，不联网，不发布 PIT 股票池，不训练模型，
不生成 Forward 证据，也不写入正式 `data/research/processed/`。

```powershell
.venv-py39\python.exe -X utf8 -m examples.research.scale_factor_pipeline --config configs/research/csi500_5y.yaml --stocks 500 --research-days 1200 --warmup-days 130
```

快速检查可改为 `--stocks 20 --research-days 20 --warmup-days 130`。输入大小在分配
之前验证：股票20至1000只且满足配置的最小横截面，研究日20至2000日且超过标签
窗口，预热日必须满足真实因子/过滤器要求且不超过500日，总输入不超过200万行。
修改配置提高预热需求时，应相应提高命令参数，而不是降低过滤标准。

这里从正式 YAML 读取14因子、标签时点、过滤器、MAD预处理和市场状态参数。
诊断对象的成员计数取显式 `--stocks`，完整配置和实际 build options 均保存；
正式 YAML 的500成员硬门槛没有改变。价格不跨日填充。

每次运行独占新的目录：

```text
results/diagnostics/scale-factor-pipeline/<run_id>/
  synthetic-inputs/{bars,benchmark,membership,status,listings}.parquet
  synthetic-dataset.parquet
  synthetic-features/{raw_factors,processed_factors}.parquet
  synthetic-{daily_ic,summary,quantile_returns,autocorrelation,turnover,correlation}.parquet
  measurements.json
results/runs/<run_id>/manifest.json
```

文件实际名称以 manifest 为准。输入、数据集、因子和评价表共15个产物均记录
SHA-256；manifest 另记录源码脚本摘要、Git/工作区指纹、种子、Python/包版本、
完整配置、实际人工日期和各阶段耗时。重跑保留旧目录，已存在的输出目录不会被替换。
异常写入 failed 收据，日志不转储环境变量。未完成或失败收据不能作为成功证据。

## 本机实测

运行：`20261011T110146.606304Z-scale-factor-pipeline-1b707648`。
代码基线：`095cbacc659fc437575e815e5a796c3c194bf8e2`，运行时 `git_dirty=true`。
脚本/测试尚未提交，因此该收据绑定当时的工作区指纹，不能改称提交后干净运行。
环境为 Windows、独立 Python 3.9.25。下列数值不是其他硬件的性能保证。

| 阶段 | 秒 |
| --- | ---: |
| 生成人工输入 | 0.139 |
| 保存输入 Parquet | 0.435 |
| 生产 DatasetBuilder 构建 | 20.163 |
| 修改未来价格后重建并核对 | 20.831 |
| 生产因子评价器，全体 ALL scope | 209.813 |
| 写结果 | 1.229 |
| 结束输出哈希前合计 | 252.852 |

输入为500只股票×1330个人工日，共665000行，其中130日预热。研究日期仅作人工
坐标，为2010-07-05至2015-02-06；**不是要求的2021-09-13至2026-09-11实证**。
实际产物包含：

- 600000行排序后的数据集，14个因子；
- 597000行成熟 `EXCESS_RET5`，末尾6日×500行标签缺失并保留；
- 16800行每日IC表（含末尾未成熟日期的缺失指标，不等于16800个有效日期）；
- 数据集 `memory_usage(index=True, deep=True)` 为335856128字节，约320.30 MiB。

没有测量进程峰值RSS；该内存值不包含并存的原始数据、重建副本和评价中间表。
因子评价耗时占比较高，但此规模不要求引入Spark。该测量没有验证四模型训练、
Walk-Forward、执行回测或真实成员变动/稀疏停牌数据的性能。

## 无未来特征依赖检查

在人工截止日2012-10-22之后，将股票和基准的价格/成交金额放大100万倍，重新
运行同一个 DatasetBuilder。对截止日及以前300500行的非标签列做精确逐值比较，
全部相同，覆盖原始行情、14个原始/预处理因子及市场状态/指数派生特征。

标签和 `entry_date/exit_date` 不进入过去特征比较，因为它们有意使用未来窗口。
对有限标签以 `rtol=atol=1e-12` 判断实质变化，有2500行过去标签受到未来价格
突变影响。这一容差仅避免两个价格同时放大后的比值舍入误差，特征比较仍然精确。
该检查证明本次人工输入下的因果性质，不替代其他泄漏审计或真实数据来源核验。

收据 SHA-256：`302615898d52ea8aa38e7d3af726d230c41890dbf7d55ffaea552d7a7ff62a10`。
测量文件 SHA-256：`c23507b29eac9cd2c4993edbaaeb577004264898fdfe921651c0cdc9862d25c2`。
15个产物摘要已逐项独立复核。正式 `data/research/processed/dataset.parquet` 仍不存在。

## 测试与失败记录

新增 `tests/research/test_scale_factor_pipeline.py` 的12项测试覆盖固定种子、Schema、
真实生产引擎、小规模标签尾部、未来突变、无网络、产物哈希、旧输出不变、分配前
参数边界、引擎失败收据及目录碰撞保护。

```powershell
.venv-py39\python.exe -m pytest -q --tb=short tests/research/test_scale_factor_pipeline.py tests/research/test_factors_phase1.py --junitxml=results/runs/scale-pipeline-targeted-rerun-20261011.xml
# 31 passed，20.01秒
.venv-py39\python.exe -m pytest -q --tb=short tests/research/test_labels_phase1.py tests/research/test_dataset_phase1.py --junitxml=results/runs/scale-core-timing-regression-20261011.xml
# 10 passed，1.31秒
.venv-py39\python.exe -m pytest -q --tb=short --junitxml=results/runs/scale-pipeline-full-20261011.xml
# 2147 passed，2 deselected，13 third-party warnings，536.25秒
```

全量运行已结束并以JUnit独立核对2147项、0 failures、0 errors。两个网络标记测试
没有执行；不会将离线测试数称为真实网络验收。初轮12项中2 failed、10 passed：
测试误以为 `validate_bars` 返回DataFrame，以及标签缩放舍入误差被严格不等式
误计。已修正测试返回值预期和标签实质变化计数，没有修改生产Schema、因子或标签
公式。初轮JUnit保留；另一次命令引用不存在的测试路径导致0 tests，失败XML也保留，
不计入通过数。

正式数据的当前阻塞仍是 `POINT-IN-TIME UNIVERSE REQUIRED: EFFECTIVE MEMBERSHIP
SEMANTICS UNVERIFIED`。这份规模验证不解决完整历史成员基线、调样生效日、真实
行情/ST状态、五年模型比较或真实Forward信号缺口。

同日已执行 `pip check`（无依赖冲突）、两个新增文件的 `py_compile` 及
`git diff --check`；审计CLI成功，正式构建CLI以状态码1在上述PIT门禁处停止：

```powershell
.venv-py39\python.exe -m qbot.research.cli audit --config configs/research/csi500_5y.yaml
# 20261011T111904.445845Z-audit-1909536b：success
.venv-py39\python.exe -m qbot.research.cli build-dataset --config configs/research/csi500_5y.yaml
# 20261011T111906.784851Z-build-dataset-609958e5：failed；无正式产物
```

没有因为工程测试通过而修改PIT门禁、费用、模型、研究参数或Forward开关。Legacy
代码及原项目许可证未修改；本增量只增加规模示例、测试和研究文档。
