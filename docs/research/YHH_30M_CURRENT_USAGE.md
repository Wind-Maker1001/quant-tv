# 分钟观察数据的当前工程入口

当前模块为 `qbot.engineering.yhh30m`，仅供工程验证和显式探索，NO LIVE MONEY。
原 69 个月分区、64,115,523 行数据的内容、Schema 和历史生产收据保持不变。

原 `qbot.research.data.yhh30m` 入口适用于生产提交 `129dbbd201fd640d58b0d787bd0089883c9dd402`。
原接入说明、交付报告及其已封存哈希保留历史含义；当前分支使用下面的新入口。
迁移原因是既有研究 CI 同时冻结测试集合和覆盖源码集合，工程扩展有独立的完整测试与覆盖门禁。
迁移没有减少转换、验证、筛选或审计功能，也没有把新实现从所有覆盖统计中排除。

```text
python -B -X utf8 -m qbot.engineering.yhh30m verify --dataset data/research/yhh30m/full-v1
python -B -X utf8 -m pytest tests/minute_data -q --cov=qbot.engineering.yhh30m
```

```python
from qbot.engineering.yhh30m import IntradayParquetProvider

provider = IntradayParquetProvider(
    "data/research/yhh30m/full-v1", purpose="exploratory"
)
for batch in provider.iter_batches(
    start="2026-09-30", end="2026-09-30",
    symbols=("000001.SZ",),
    columns=("symbol", "timestamp_local", "quality_flags"),
):
    # 带类型的供应商观察；不能据此认证交易区间、身份或单位。
    pass
```

当前 CLI 的 `convert` 参数与历史接口一致，但新的生产任务必须使用独立输出目录，
不能覆盖或改签原生产代。本轮不再重转全量数据。

原冻结研究套件继续由未修改的 `research-tests.yml` 执行；全部 42 项分钟及发布回归
由新增 `minute-data-evidence.yml` 单独执行。新门禁核对精确用例身份、九个运行源码文件、
源 SHA、完整可执行行清单和迁移前已命中的覆盖行，禁止漏测或跳过。
原失败 CI 和迁移前后的范围证明见
[CI 修复证据](evidence/yhh30m-independent-20261019-v1/ci-remediation.json)。

金融准入仍为 FAIL：时间标签与区间、时区、量额单位、复权方法、历史稳定身份、状态、
公司行为及 PIT 证据仍不足。`daily_bars` 直接拒绝请求；本组件不能接入正式研究或 Forward。
完整结论及 15:30、空因子和负量额调查见
[独立验收报告](YHH_30M_INDEPENDENT_ACCEPTANCE.md)。
