# FactorLab Forward Test

> **实现状态：Phase 4 核心流程已实现，但尚未正式激活。** 原定起点
> `2026-09-14` 已经过去，当日没有生成可信的实时信号，因此永久不得补写成
> `ON_TIME`。正式实验必须在配置中选定一个仍未到来的新日期，并在该日期前完成
> 激活收据和模型冻结。

## 1. 边界

Forward Test 只做 Paper Trading 信号记录：

- 不连接券商，不配置真实账户，不发送订单；
- `live_trading` 必须为 `false`；
- 模型、参数、因子、Top-K 与训练截止日必须在启用前冻结；
- 正式命令要求 Git 工作区干净；
- PIT 股票池、Schema 或数据版本不完整时直接失败。

历史 Walk-Forward 结果不能冒充 Forward Test。这里的目标是保留“预测在当时
确已生成”的可审计证据，而不是重放一段历史后挑选最好版本。

## 2. 三步启用

### 2.1 审核并提交配置

在 `configs/research/csi500_5y.yaml` 中设置：

```yaml
forward:
  enabled: true
  activation_date: 'YYYY-MM-DD'   # 必须仍在未来
  model_name: ridge               # 或预先选定的其他一个模型
  model_version: ridge-forward-v1
  training_asof: 'YYYY-MM-DD'     # 严格早于 activation_date
  parameter_candidate_index: 0    # 明确选择，不能再看最终 Test 调整
  timezone: Asia/Shanghai
  market_close_hour: 15
  market_close_minute: 30
  require_clean_worktree: true
```

冻结模型时，`data.end` 必须等于 `training_asof`。先审核配置并本地提交，确保
`git status` 干净。

### 2.2 注册未来激活收据

```powershell
python -m qbot.research.cli activate-forward `
  --date YYYY-MM-DD `
  --config configs/research/csi500_5y.yaml
```

命令只允许在激活日期之前运行。注册时间由模块内部读取，公共 API 不接受调用方传入
`registered_at`。收据还绑定 `qbot/research/**/*.py` 与
`dev/requirements-research.txt` 的确定性源码摘要，并在
`results/forward/activations/<activation_id>/` 原子创建不可覆盖的
`manifest.json` 与摘要。`--date` 必须与配置完全一致。创建后应把收据纳入本地
Git 提交，再继续下一步；否则“干净工作区”保护会阻止模型冻结。

### 2.3 构建训练数据并冻结模型

```powershell
python -m qbot.research.cli download-data `
  --config configs/research/csi500_5y.yaml
python -m qbot.research.cli build-dataset `
  --config configs/research/csi500_5y.yaml
python -m qbot.research.cli freeze-forward-model `
  --config configs/research/csi500_5y.yaml
```

冻结命令只能在 activation date 之前运行，并在耗时拟合结束、正式发布前再次检查
上海日期、Git 状态和源码摘要。冻结逻辑只纳入 `date <= training_asof` 且
`exit_date <= training_asof` 的有限
标签；因此标签窗口尚未成熟的尾部样本不会进入 imputer、scaler 或模型。模型参数
来自配置指定的单一候选，不读取 Historical Test 进行自动选优。

训练日期只接受 canonical `YYYY-MM-DD`、`date` 或 tz-naive 午夜时间戳；整数日期、
带时区时间戳和带时分秒值一律失败，避免 UTC 转换或纳秒解析把未来标签移到 cutoff
之前。`FinalModelFit` 还以模型序列化摘要绑定训练行数、cutoff、标签退出日、特征、
参数与 seed，替换审计字段后无法保存。

产物位于：

```text
results/forward/models/<model_name>/<model_version>/
├── metadata.json
└── model.pkl
```

加载时先验证文件集合及 SHA-256，再反序列化本项目生成的本地可信 pickle，并复核
模型类型、参数、seed、特征顺序、冻结时刻、数据集哈希、源码哈希、股票池哈希和
研究契约哈希。不要加载
来源不可信的 pickle。冻结后同样应提交该 bundle，使首个信号日前工作区恢复干净。

## 3. 每日收盘后信号

```powershell
python -m qbot.research.cli forward-signal `
  --date YYYY-MM-DD `
  --config configs/research/csi500_5y.yaml
```

命令会在内存中把本次 `data.end` 精确固定为 `--date`；研究契约有意排除这个每日
滚动字段，因此无需每天修改配置文件。随后自动执行：

```text
取得全流程独占锁
  -> 验证激活收据、源码摘要、干净工作区和激活日前冻结的模型
  -> 增量更新截至 signal_date 的数据与 PIT 股票池
  -> 任一股票行情或证券状态下载失败即停止
  -> 以独立 build-dataset 子运行重建并验证数据集
  -> 确认 signal_date 是中证500交易日且 data_asof 恰好到该日
  -> 当日合格横截面必须达到 expected_member_count × min_valid_ohlcv_ratio
  -> 只用当日横截面计算模型 score
  -> 任一入选横截面特征非有限即停止，不允许模型侧插补掩盖缺数
  -> 按 score 降序、symbol 升序打破并列
  -> 生成 Top-K 等权 Paper Portfolio
  -> 原子追加一个新版本
```

正式配置把收盘安全边界固定为 `15:30 Asia/Shanghai`，不能改成盘前时刻。当日信号
只允许在该时刻之后生成。网络或构建阶段跨过午夜时，
系统会用实际发布时刻重新检查，不能继续把它标记为 `ON_TIME`。

## 4. 迟到重发，不是历史补录

信号日已经过去时必须显式提供原因：

```powershell
python -m qbot.research.cli forward-signal `
  --date YYYY-MM-DD `
  --reissue-reason "approved upstream data correction" `
  --config configs/research/csi500_5y.yaml
```

该版本固定标记为 `LATE_REISSUE`。下列操作一律失败：

- 生成激活日前的信号；
- 把旧日期称为 `ON_TIME`；
- 对旧日期省略重发原因；
- 生成未来日期或当日收盘前信号；
- 覆盖已经存在的版本目录。

同一日期默认依次写入 `v000001`、`v000002`……。日期级独占锁在锁内分配版本，
staging 目录完整写入后再原子发布；并发进程不会选到同一个版本。已有版本不会因
重跑被修改。

## 5. 信号字段与目录

```text
results/forward/signals/YYYY-MM-DD/vNNNNNN/
├── completion/
│   ├── receipt.json
│   ├── receipt.sha256
│   └── run_manifest.json
├── signals.csv
├── manifest.json
└── manifest.sha256
```

每行至少包含：

| 字段 | 语义 |
| --- | --- |
| `signal_date` / `data_asof` | 信号交易日与输入数据截至日 |
| `generated_at` | 上海时区的实际生成时刻 |
| `model_name` / `model_version` | 冻结模型身份 |
| `model_bundle_sha256` / `dataset_sha256` | 精确模型 bundle 与当日数据集内容摘要 |
| `git_commit` / `run_id` | 代码版本与运行清单 |
| `universe_version` | 当日 PIT 股票池版本 |
| `activation_id` | 预先注册的激活收据 |
| `activation_manifest_sha256` | 激活收据摘要 |
| `research_contract_sha256` | 冻结研究合同摘要 |
| `source_sha256` | 激活、模型和信号共同绑定的 FactorLab 源码摘要 |
| `timeliness` / `reissue_reason` | `ON_TIME` 或有原因的迟到重发 |
| `symbol` / `score` / `rank` | canonical 股票代码、分数与名次 |
| `target_weight` | Paper Portfolio 目标权重 |

Manifest 记录行数、列顺序、CSV 字节数和 SHA-256，自身摘要由 sidecar 保存。信号
数据先原子发布，只有 producer run 成功落盘后才原子追加 `completion/`；该目录保存
成功运行清单的不可变副本及摘要。进程在两步之间崩溃只会留下不能被正式读取器接受
的 orphan version，重跑必须分配新版本，不能覆盖 orphan。下游读取器会同时复核
目录文件集合、完成收据、成功运行快照、manifest、CSV 摘要和 canonical 序列化。对应
`results/runs/<run_id>/manifest.json` 还记录当日数据集、模型 bundle、股票池、环境、
配置和子运行来源。

## 6. 证据保存规则

`results/forward/` 没有被 `.gitignore` 整体忽略，目的是让激活收据、冻结模型和每日
信号能按顺序进入本地提交。建议流程是：

1. 配置提交；
2. 激活收据提交；
3. 冻结模型提交；
4. 每日信号生成后尽快提交；
5. 不 force-push、不改写这些提交。

本地 SHA-256、文件时间和系统时钟并不是第三方可信时间戳，也无法阻止拥有文件系统
权限的人删除整个目录或同时重写文件与本地摘要。源码摘要、manifest 摘要和完成收据
提供的是一致性证据，不是独立可信时间戳。若课程要求更强证明，应把提交推送到受保护远端或使用外部
时间戳/WORM 存储。本项目只声称可检测普通修改并保留可审计链路，不声称提供法律级
防篡改证明。

## 7. 当前真实状态

- `2026-09-14` 至今没有可被追认为当时生成的正式信号；
- 正式 YAML 仍保持 `forward.enabled: false`，没有擅自替用户选择新起点；
- 当前公开数据下载仍受 BaoStock 网络连接失败阻塞，因此没有生成真实五年数据集或
  正式冻结模型；
- 测试产生的临时目录和 synthetic 数据只验证工程链路，不构成实证或 Forward Test
  结果。

新的真实启用日必须由研究者在日期到来前明确批准并按上述流程注册。
