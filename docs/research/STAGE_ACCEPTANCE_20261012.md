# quant-tv 阶段代码验收与真实复权证据状态

验收开始：2026-10-12；跨日交付：2026-10-13（Asia/Shanghai）。Python 3.9，**NO LIVE MONEY**。

本报告按用户后续指令收缩范围：继续已有工作区，停止外部网页请求，完成定向测试、必要修复和阶段交付。
未重新执行全量研究测试、600000 行性能配对基准或完整真实证券认证；这些事项不能声明为本轮通过。

## 1. 三项退出结论

| 验收 | 本阶段结论 | 适用边界 |
| --- | --- | --- |
| A. 工程验收 | **可进入本阶段增量的 PR 审查** | 817 项定向测试通过；完整分支的本轮全量验收及新提交云端 CI 尚未执行 |
| B. 600000.SH 真实复权 | **部分取证完成，真实认证未通过** | 有真实 RAW、历史 HFQ 观察及现金公告；缺少经证明的历史锚点、来源算法合同、完整事件和 vintage |
| C. 正式五年数据准入 | **继续拒绝** | 原正式配置构建返回 1，PIT 成员生效语义未验证；正式数据集不存在 |

本阶段的软件通过数不等于真实证券的认证通过数。600000.SH 通过真实 HFQ 认证的交易日数为 **0**。

## 2. 起始检查、CI 和变更来源

- 指定分支：`codex/factor-evaluation-performance`。
- 起始 HEAD：`365a1c9086d0e4f22a79874acbf3f8d64139b242`；起始 Git 工作区干净。
- 刷新后的 `origin/main`：`18de00687695ab17360e96d8a5c8322930dc857a`；起始分支多 17 个提交，三点差异为 84 个文件、10061 行增加、28 行删除。
- 续作开始时仅有本任务产生的两个修改文件：`.github/workflows/greetings.yml` 和 `tests/research/test_adjustment_foundation.py`。全部保留，没有覆盖用户其他工作。
- 已阅读性能、TDX、数据复权基础、市场状态、研究方法论文档和 `configs/research/csi500_5y.yaml`，并检查既有研究测试、配置、数据、资格复核与正式入口。

暂停外部请求前查得起始 HEAD 的 [FactorLab research tests](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38253367300) 成功，Python 3.9 离线测试及架构审计步骤成功。
[greetings 工作流](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38253365301) 返回 failure，没有可取得的 job 日志。
本地对其冻结原文独立重现第 15 行 YAML `ParserError`：HTML 属性双引号未转义。
本轮只修复该字符串转义，修复后 `yaml.safe_load` 成功。未修改触发事件、权限或消息内容语义，未主动发送 GitHub 消息。
暂停后没有查询新 CI，也没有推送或合并。

## 3. 新增和修改文件

| Git 文件 | 实际变化 |
| --- | --- |
| `.github/workflows/greetings.yml` | 一行 HTML 属性引号转义，修复原有 YAML 语法错误 |
| `tests/research/test_adjustment_foundation.py` | 原整条 Builder 时间扰动用例扩展为两种 HFQ 算法 × 四种扰动，共 8 个案例，比原用例增加 7 项 |
| `docs/research/STAGE_ACCEPTANCE_20261012.md` | 本阶段中文交付报告 |

未修改生产复权核、原 14 因子、方向、MAD/Z-score、六张评价表、四模型、市场状态规则、Walk-Forward、标签、正式 YAML、PIT/状态/来源门禁、Forward 或真实交易接口。

本地忽略目录另保存新的日志、JUnit、环境、原文、逐字段状态表、离线检查脚本及哈希收据：

```text
results/diagnostics/real-adjustment-acceptance/20261012-stage-review-v1/
```

这些本机产物没有随 Git 提交上传；旧实验收据和数据均保留。原始抓取失败记录及 HTTP 200 返回 HTML 的非 PDF 响应也保留，未冒充成功公告。

## 4. 定向测试及其覆盖

| 执行批次 | 通过 | 失败 / 错误 / 跳过 | 警告 | pytest 控制台耗时 |
| --- | ---: | --- | ---: | ---: |
| 已启动的基础定向测试 | 525 | 0 / 0 / 0 | 88 | 110.37 秒 |
| 续作补充本地集成测试 | 292 | 0 / 0 / 0 | 13 | 79.84 秒 |
| 合计，两个文件集合不重叠 | **817** | **0 / 0 / 0** | 101 次输出 | 不作为性能基准 |

JUnit suite 时间分别为 109.718 和 79.150 秒；包装进程时间分别为 111.335 和 89.193 秒。
这些计时口径分别保留，未混称。警告来自既有 Matplotlib/PyParsing、空分组均值和 Pandas 分类分组行为提示。

基础批次涵盖：

- 因子独立冻结 Golden、六表结构/缺失位置/排序/成员和固定 `atol=rtol=1e-12`；没有放宽浮点容差。
- TDX DAY、staging、来源回验及独立参考检查的软件合同。
- 正式 MA20/MA60 BULL/BEAR/SIDEWAYS 与诊断 UNKNOWN 的区别、缺日和未来价格扰动。
- 两种复权核的独立有理数 Golden、事件版本、历史可知时间、身份、单位、独立参考、资格重放和篡改拒绝。
- 未来事件、晚到更正、晚到取消和改期：过去时点全部 14 个原始及处理后因子、市场/指数特征和固定 FactorScore 信号精确不变；晚到修订的拼接 vintage 保持不合格。允许未来收益标签按定义改变。

补充批次涵盖 Local Provider、公开 CLI、本地合成软件链路、DatasetBuilder、PIT 发布失败、性能测量工具、因子报告、配置、证券状态及 BaoStock 生效语义拒绝。
人工 fixture 的工作日日历和合成证券仅用于软件测试，未进入真实缓存或正式研究。

其他实际检查：Python 3.9 源码编译成功；`pip check` 返回 `No broken requirements found`；修复后的 YAML 可解析；`git diff --check` 通过。
补充检查脚本第一次直接执行时因未加入仓库导入路径而在 pytest 启动前失败，执行测试数为 0；已修正并保存 `stage-checks-startup-failure.json`。这不是 pytest 失败，也没有删除该记录。

### 可复现命令

```powershell
.venv-py39\python.exe -B -X utf8 -m pytest -q --tb=short tests/research/test_adjustment_foundation.py tests/research/test_market_data_qualification.py tests/research/test_factor_metrics_golden.py tests/research/test_tdx_day.py tests/research/test_tdx_staging.py tests/research/test_tdx_reference.py tests/research/test_market_regime_diagnostic.py tests/research/test_market_regime_phase3.py

.venv-py39\python.exe -B -X utf8 -m pytest -q --tb=short tests/research/test_local_market_provider.py tests/research/test_local_cli_pipeline.py tests/research/test_cli_download_contract.py tests/research/test_dataset_phase1.py tests/research/test_pit_snapshot_failure.py tests/research/test_factor_performance_diagnostic.py tests/research/test_factor_metrics_report_phase1.py tests/research/test_config.py tests/research/test_security_status_import.py tests/research/test_baostock_effective_semantics.py

.venv-py39\python.exe -B -X utf8 -m pip check
```

原实际命令含唯一 JUnit 输出路径，完整命令、退出码和起止 UTC 时间分别保存在 `targeted-command.json`、`stage-integration-command.json` 和 `pip-check-command.json`。
重跑应使用新的输出目录，不覆盖上述收据。

环境：Windows `10.0.26340`、x86_64、28 个逻辑 CPU、Python 3.9.25；NumPy 1.26.4、Pandas 2.2.3、PyArrow 17.0.0、SciPy 1.13.1、pytest 8.3.5。
OpenBLAS 配置和数值线程环境保存在 `stage-environment.json`；该环境信息未声称机器空闲。

### 本阶段未执行

按用户收缩后的范围，未重跑全量安全离线研究集、600000 行同环境配对性能基准、全部 RAW 重新转换和新提交云端 Actions。
性能工具定向测试通过只证明计时/隔离/收据逻辑，没有产生新的全规模加速比。旧文档的性能测量和 12,036,951 条 RAW 原始转换结果保持历史记录属性。

## 5. 600000.SH 已有真实资料与未完成认证

本节只复核暂停前已取得的本地字节，没有新增网页请求。

| 资料 | 实际覆盖与状态 |
| --- | --- |
| 原始 `sh600000.day` 和 RAW staging | 1638 行；当前 DAY SHA、staging SHA 和完整 32 字节重编码 SHA 一致；单位及历史身份仍未认证 |
| 冻结九行 raw/hfq 缓存 | 2024-01-02 至 2024-01-12；读取原 cache metadata 固定代并通过哈希校验；当前观察不是当时 vintage |
| 暂停前取得的东方财富事件窗口响应 | raw 与 hfq 各 8 行，预先选定 2025-07-09 至 2025-07-18；保留原 HTTP JSON 字节、参数、获取时间和哈希；来源算法仍未认证 |
| 2025 年现金事件公告 | 已取得巨潮原始 PDF，123429 字节；本地核对日期表和正文；仅证明该次公告，不证明完整事件覆盖和修订历史 |
| TDX GBBQ、新浪因子旧归档 | 仍为未解码/仅因子观察；不能当作完整公司行为或已认证历史锚点 |

现金公告列明每普通股含税现金 0.41 元，登记日 2025-07-15，除息及派息日 2025-07-16。公告落款为 2025-07-09；巨潮归档路径日期为 2025-07-10。[巨潮原始公告](https://static.cninfo.com.cn/finalpage/2025-07-10/1224119803.PDF)
PDF 文件创建时间不能充当公告公开时间。精确发布时间、当时交易者实际取得时间及后续修订覆盖均为 UNKNOWN；本次取得时间记录为 UTC，历史类型仍为 `HISTORICALLY_RECONSTRUCTED`。

两份 HFQ 观察均源自东方财富：AKShare 包装和直接东方财富响应不能算两个独立上游。
它们相对于 TDX 可供跨来源检查，但尚不构成经过来源算法、锚点、舍入和时间复核的合格独立复权参考。

### 两种算法的独立对照状态

| 算法 | 软件 Golden | 真实 HFQ 计算 | 真实误差和最终资格 |
| --- | --- | --- | --- |
| `SOURCE_AFFINE_HFQ_V1` | 定向测试通过 | 未执行：缺已证明的历史仿射锚点、完整事件及来源合同 | 绝对/相对误差不可估计，UNVERIFIED |
| `SOURCE_RATIO_HFQ_V1` | 定向测试通过 | 未执行：缺已证明的历史比例锚点、完整事件及来源合同 | 绝对/相对误差不可估计，UNVERIFIED |

本地 `600000-independent-hfq-status.csv` 保留全部预选九行及事件窗口八行，共 17 个日期 × 4 个 OHLC 字段 × 2 种方法 = 136 条状态记录。
每条包含 TDX 候选原价、实际独立上游 HFQ 观察、参考 SHA/取得时间、UNKNOWN 锚点和事件覆盖；计算价与绝对/相对误差留空，最终资格为 UNVERIFIED。
没有从参考价格反拟合锚点，没有设乘数 1/偏移 0 假装来源锚点，没有把收盘比例套用于全部 OHLC，也没有混用两种算法。

因此本阶段**没有证券级真实复权证据闭环，没有发布合格 600000.SH 行情**。
真实资格包缺失，未构造或提交一份伪造的真实资格包；资格复核函数的拒绝、重放与合成边界由已执行定向测试覆盖。

## 6. 正式构建拒绝与剩余阻断

调用原 `build-dataset --config configs/research/csi500_5y.yaml`，在进程内明确禁止 socket 连接。
实际退出码为 1，网络尝试为 0，错误为：

```text
POINT-IN-TIME UNIVERSE REQUIRED: EFFECTIVE MEMBERSHIP SEMANTICS UNVERIFIED
```

正式 `dataset.parquet` 仍不存在。新运行收据为 `20261012T155551.323128Z-build-dataset-54222a54`，详情保存于本阶段 `formal-build-refusal.json` 和 `.log`。
原正式 YAML 字节 SHA 未变；未使用工作日补交易日历、当前成分回填、来源 verified 开关或合成数据强行放行。

正式五年研究仍缺：

1. 2021 年研究起点真实 500 成员基线、完整调样实际生效链和逐交易日 PIT 成员。
2. 历史 A 股身份、上市/退市/换码及逐日 ST、停复牌状态。
3. TDX 价格、成交量、成交额单位的覆盖认证，历史换手率或时点一致的分母。
4. 完整公司行为前史、后续更正、历史锚点、来源算法与舍入合同、独立 HFQ OHLC。
5. 独立实际交易日历及历史数据 vintage；当时可知信息不能由今天的重建时间替代。

跨公司行为的执行账本、权益到账、配股资金及执行价格边界仍需后续独立协议审查；本阶段未扩展执行协议或启用 Forward。

## 7. 完整性与证据哈希

起始收据固定 29073 份文件，包括研究代码/测试/配置、原 DAY、RAW staging、历史转换和性能/复权收据。
最终逐文件复核只允许两个明确代码修改，其余旧数据、Golden、配置和实验收据保持原 SHA；结果见 `final-integrity.json`。
补充定向测试开始和结束的研究 Python 源码 SHA 一致。全部当前产物另绑定文件哈希，未修改旧收据来适配新代码。

| 文件/资料 | SHA-256 |
| --- | --- |
| 起始完整性收据 | `d1d94b4c2407b1d8a3fbb1e72b24812611f70a1bcc688f6ff13f676f46fe5134` |
| 基础定向 JUnit | `f52e9f9ac4a611be9ef65af4cb905cdf73efef4860080b358be98a5604649043` |
| 补充定向 JUnit | `70012d81dce90a01fc3dabc078f813e3b853297eef3ba3e917ef93cc7996fe29` |
| 600000.SH 原 DAY | `f87cd9f50cd3039809a14b5fde9fcd8f5360f9b2cdf7db12b7bc2fd205f1e479` |
| 600000.SH RAW staging | `1d5a39f7963a9023e1a217857490f41436dc1025e8dca9463af986993174cbc8` |
| 原九行参考 Parquet | `d45a4179d3fdc497a295182fcb7a12aeb7f2e51f206d649b7bff3782af0b7cac` |
| 巨潮原始现金公告 PDF | `f2e8e0e2be70848a65debac6b4858c13cfd8da10031129ec9dc72d80bf8f8b5d` |
| 事件窗口 raw 响应 | `f59bcfd7122ef3ab24cf703345bb87fe5dbb65e9f10de10938bb39d72ae34581` |
| 事件窗口 hfq 响应 | `a409515327f1a7215e2be3f05de2d8dbaaff7d8eaa321886d8ab3b51eb879227` |
| 136 条复权资格状态 CSV | `9f2cc82789ea8d5c6cd2eb6d8fc7f6a08c140a3a915bed4e3231aa5fbf4d46ea` |
| 原正式五年 YAML | `a452a199eafaa968ff726ce449251bf366c4eff128a6f5bb57b5ac92bb00c9b8` |

哈希证明本次具体字节及本地完整性，不能证明历史公开时间、资料完整覆盖或第三方身份。

## 8. Git 提交与下一阶段条件

本阶段实现提交：

- `8240cd1489b888fee9b856669548d51034b16b45`：greetings YAML 转义修复。
- `9eb8258c176d6f5ad4cd5c14e8792c1973b3ea15`：两种 HFQ 方法的晚到事件扰动验收。

报告另作独立文档提交；最终报告提交 SHA 和分支状态由交付消息及本机 `completion.json` 记录，避免文档自引用。
全部提交保留在指定分支，未修改或合并 main，未 force push，暂停外部请求后未推送远端。

下一阶段按以下条件验收，不以增加功能数为目标：

1. 用户恢复外部取证后，补齐来源原文、完整事件/修订、历史锚点、来源算法/舍入、单位和 vintage；先冻结范围和容差，再运行两种来源合同各自的真实 HFQ 对照。
2. 对全部预选交易日输出真实计算价、独立参考、绝对/相对误差；没有资料的日期继续 UNKNOWN，不能拟合后筛选日期或提高容差。
3. 以完整真实资格包调用现有资格复核/生产接入，只有该范围合同全部满足才授予证券级行情资格；缺 PIT 或状态时五年构建继续拒绝。
4. 恢复完整工程验收时执行全量安全离线研究集、新提交云端 CI 和同环境配对性能测量；Golden、浮点容差及研究协议保持冻结。

当前允许交付的是工程增量和如实的证据缺口；真实复权认证及正式五年研究仍未完成。
