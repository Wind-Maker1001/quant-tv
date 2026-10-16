# TDX 审计聚合证据与复现

2026-10-16（Asia/Shanghai），NO LIVE MONEY。真实本地资产审计，正式金融准入仍为 false。

本目录只发布聚合计数、SHA、状态与覆盖图。冻结十股只发布计数；不发布全量证券标识、
证券级范围/缺失日、行情价格/量额序列、原响应、GBBQ 载荷、原公告全文或本机私有路径。
公开 checkout 无法凭本目录重建真实私有行情；缺资产时应报告 UNKNOWN。

## 本轮实际运行

| 收据 | 记录内容 |
| --- | --- |
| `summary.json` | 9,374 原件、9,371 完整 Parquet 回编码、原资产 SHA、冻结样本与零改写结果 |
| `publication-receipt.json` | 主审计六份公开聚合产物 SHA/字节数、主程序运行源码 SHA |
| `review.json` | 独立进程复核全部原件 SHA/逐条 struct、全部 Parquet SHA、9,371 份完整合同/身份摘要及原转换源码绑定、54 条独立编码抽样、九条 GBBQ 标量核对 |
| `supplement-receipt.json` | 原50名单覆盖、量额候选、公告/旧GBBQ归档绑定及 Matplotlib 图 SHA |
| `supplement-independent-review.json` | 从 DAY 原字节用 struct/Decimal 独立复算全部10,024个量额候选比较、原50输入SHA及覆盖；同一操作者 |
| `delivery.json` | 最终定向/完整离线回归、静态检查、发布与冻结检查摘要 |
| `delivery-files.json` | 本目录和本次交付源码/报告/notebook 的逐文件 SHA；不包含自身以避免循环 |

独立实现复核为同一操作者使用另一进程/实现，不是已完成的外部人工金融认证。
PR 留待人工审查，不自动合并。原有三份失败文件和全部历史收据保持原位。
两个早期 Git 子模块/悬空链接冻结预检失败目录、一次 Matplotlib 兼容性修复前的补充输出及旧/当前转换源码版本诊断中间输出均留在私有目录，
未覆盖或当作最终成功收据；最终有效运行分别为 `asset-audit-r3`、`separate-review-r3`、`aggregate-supplement-r2`。
主审计只读运行耗时约 633 秒；全任务准备阶段另取得过一份固定提交的开源 reader 源码，未下载行情。

覆盖 CSV 中 `expected_grid` 是所有本地候选文件数乘原生基准月度观察日数。
不按缺失原因、上市日或成员资格缩小分母；缺失仍为 UNKNOWN。
原 `anomalies.csv` 的 `records` 列沿用诊断计数：日历缺口类为受影响**文件数**，其他为记录数。
`frozen-comparison.csv` 的 EXACT_MATCH/DIFFERENT 是候选固定尺度零容差数值计数，
SOURCE_UNIT_UNVERIFIED 是来源资格，两者不能合并当作金融认证。

## 离线复现命令

使用已有 Python 3.9 研究环境及 `dev/requirements-research-ci.txt`。以下所有根目录必须指向实际已有资产，
各输出目录必须全新；原始行情保持在原私有位置。不要复制原行情到 Git 或改写旧收据。

```powershell
$private = '<EXISTING_PRIVATE_CHECKOUT>'
$python = '<EXISTING_PY39_RESEARCH_PYTHON>'
$audit = "$private/results/diagnostics/tdx-data-quality-audit/<NEW_RUN>/asset-audit"
$pilot = "$private/data/research/five-year-pilot/20261015-native-calendar-v1/runs/20261015T111701027971Z-d51bb4d1/manifest.json"
$decoder = '<EXISTING_ARCHIVED_SHA_PINNED_GBBQ_READER>'
& $python -B -X utf8 -m examples.research.audit_tdx_quality --private-root $private --output $audit --pilot-manifest $pilot --decoder-reference $decoder
& $python -B -X utf8 -m examples.research.review_tdx_quality --private-root $private --audit $audit --output "$private/results/diagnostics/tdx-data-quality-audit/<NEW_RUN>/separate-review" --decoder-reference $decoder
& $python -B -X utf8 -m examples.research.summarize_tdx_quality --private-root $private --audit $audit --output "$private/results/diagnostics/tdx-data-quality-audit/<NEW_RUN>/aggregate-supplement"
& $python -B -m pytest tests/research/test_tdx_quality_audit.py tests/research/test_tdx_day.py tests/research/test_tdx_staging.py tests/research/test_tdx_reference.py tests/research/test_five_year_pilot.py tests/research/test_real_hfq_evidence_pilot.py -q
$pytestTmp = '<NEW_SAME_DRIVE_DIRECTORY_OUTSIDE_THIS_REPOSITORY>'
& $python -B -m pytest tests/research -q -m 'not network' --basetemp $pytestTmp --junitxml=<NEW_JUNIT_PATH> --cov=qbot.research --cov-report=xml:<NEW_COVERAGE_PATH>
& $python -B .github/scripts/ci/research_checks.py
```

`audit_tdx_quality` 退出 0 只表示工程完整性核对完成，原 OHLC 失败仍如实保留，金融准入 false。
它只读既有生成代，不调用转换发布或供应商 acquisition。固定 decoder 的 SHA/提交见 GBBQ 报告，
没有匹配源文件则停止，不能换成虚构事件。

Windows 完整回归的临时目录需与仓库同盘且在仓库之外，供既有跨 cwd 相对路径用例构造 `..`。
必须验证目标为本任务新目录且尚不存在，避免 pytest 清理既有目录。
本轮默认 C 盘临时目录的首次完整回归为 3,122 passed、2 failed、2 network deselected，
两项均在跨 C/D 盘的 `os.path.relpath` 处失败；仓库内同盘预检又揭示一个原有 `..` 断言。
改用同盘外部新目录后，两项定向复核全部通过；原始失败/中断日志保留，未修改测试断言或应用代码。
最终完整重跑的结果与独立覆盖文件见 `delivery.json`。

聚合 notebook 使用已有 Anaconda Python 3.12 的 nbformat/nbclient/ipykernel 执行，未向研究环境安装依赖。
它默认只验证已发布聚合和展示覆盖 PNG；实际私有审计需要明确启用并提供环境变量。
已从头执行全部六个代码单元，无错误；覆盖图经实际图像检查。运行时的 ZMQ/调试器兼容警告不构成金融证据。

正式金融结果：PIT_UNVERIFIED / HFQ_UNVERIFIED / FORMAL_ADMISSION_BLOCKED。
合成测试只用于软件边界，真实原件/原生响应检验与软件回归分别保留。
