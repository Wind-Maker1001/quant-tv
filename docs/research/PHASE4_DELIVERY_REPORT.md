# Qbot FactorLab Phase 4 交付与验收

验收日期：2026-09-24（Asia/Shanghai）

2026-10-09 补充：CLI 已扩展完整横截面预测存档与 schema 3 成功收据，旧 schema 2
仍为 Top-K-only，禁止补评分。后续回归及实际 synthetic 示例见
[FORWARD_PREDICTION_AUDIT.md](FORWARD_PREDICTION_AUDIT.md)。这不补造任何真实信号；
成熟 Forward 关联评价仍未实现。下面2026-09-24的测试与网络记录为原阶段证据，不能
当成当前数据源状态，当前 PIT 限制见 [BAOSTOCK_SOURCE_AUDIT.md](BAOSTOCK_SOURCE_AUDIT.md)。

## 结论

Phase 4 的核心软件链路已经实现并通过离线回归：

- 研究者必须预先审核一个尚未到来的 activation date；
- 激活收据、最终模型 bundle 和每日信号均采用不可覆盖的新目录发布；
- 激活、模型与信号共同绑定确定性的 FactorLab 源码摘要；
- 最终模型只使用在 `training_asof` 前已经成熟的标签；
- 每日命令自动更新数据、重建验证数据集并在收盘后生成 Top-K Paper Signal；
- 旧日期只能发布带原因的 `LATE_REISSUE`，不能冒充 `ON_TIME`；
- 全流程保持 `live_trading=false`，没有券商连接或真实订单路径。

“软件完成”不等于“真实 Forward Test 已开始”。正式 YAML 仍关闭该能力，没有擅自
选择新起点、没有创建正式激活收据，也没有生成任何真实 forward signal。已经过去的
`2026-09-14` 永久留空。

## 新增能力

### 研究合同与激活

- `forward/contract.py` 对因子、标签、预处理、市场状态、验证、Top-K、费用、执行
  假设、模型、候选索引、训练截止日和收盘策略生成 canonical SHA-256；仅每日滚动
  的 `data.end` 被排除。
- `forward/activation.py` 要求在上海本地日期到达 activation date 之前注册；注册
  时刻只能由内部时钟获取，不能由调用方回填；收据
  使用独占锁、staging、原子目录发布和 manifest 摘要，重注册或篡改会失败。
- 正式命令要求已提交的干净 Git 工作区，并在真正发布前再次检查 commit/worktree，
  防止长时间下载期间代码身份改变。
- `forward/integrity.py` 拒绝证据路径中的 symlink/Windows reparse point，以稳定顺序
  摘要 `qbot/research/**/*.py` 和研究依赖文件，并为完整日跑提供不自动破锁的独占锁。

### 冻结模型

- 支持 FactorScore、Ridge、LightGBM 和 XGBoost，但调用方只能提供一个显式模型和
  一个显式参数映射，没有读取 Test 选优的入口。
- 训练行同时满足 `date <= training_asof`、`exit_date <= training_asof` 和有限标签；
  imputer、scaler 与 estimator 均只看到这些行。
- bundle 精确绑定模型类型、参数、seed、特征顺序、训练行数、最大标签退出日、
  冻结时刻、数据集/PIT/研究合同/源码/Git 哈希；加载时在反序列化可信本地 pickle
  前先验证文件摘要。
- 日期输入拒绝整数、时区时间戳与非午夜值；内部授权摘要防止调用者替换训练 cutoff、
  行数或最大标签退出日后保存。
- 冻结在 activation date 当天或之后必然失败；耗时拟合后、bundle 发布前再次检查
  时钟、工作区和源码摘要。
- 同一 model version 不可覆盖。

### 日终 Paper Signal

- `forward/policy.py` 统一使用 `Asia/Shanghai` 判定当日收盘、未来日期与迟到重发。
- `forward-signal` 在内存中把 `data.end` 固定为 `--date`，再分别建立真实的
  `download-data` 和 `build-dataset` 子运行清单。
- 信号日前必须有完整 benchmark 交易日、PIT 股票池、数据集和冻结模型；任一行情或
  状态下载失败、任一信号日特征非有限、任何来源哈希不一致均停止。
- 当日分数按降序排列，canonical symbol 升序打破并列，输出配置化 Top-K 等权组合。
- 日期级 `O_EXCL` 锁在锁内分配 `vNNNNNN`，完整 staging 后原子发布；并发写入不会
  获得同一版本，已有版本不会被修改。
- 另一个全流程锁覆盖刷新、构建、读取、评分和发布；Parquet 以同一份内存字节完成
  hash 与解析，消除共享路径替换造成的 TOCTOU。
- 每行和 manifest 直接绑定 activation、研究合同、模型 bundle、当日数据集、PIT、
  源码、Git 和 run_id。`manifest.sha256` 与严格读取器能发现 CSV/manifest/目录清单修改。
- producer run 成功后才追加原子的 `completion/` 收据，其中包含成功运行清单快照；
  两步之间崩溃的 orphan version 不会被正式读取器接受。

## CLI

新增：

```text
python -m qbot.research.cli activate-forward --date YYYY-MM-DD --config ...
python -m qbot.research.cli freeze-forward-model --config ...
python -m qbot.research.cli forward-signal --date YYYY-MM-DD --config ...
```

旧日期重发必须增加：

```text
--reissue-reason "approved reason"
```

完整的审核、提交顺序和证据局限见 `docs/research/FORWARD_TEST.md`。

## 测试与命令证据

实际执行：

```text
.\.venv-py39\python.exe -m pytest -q
292 passed, 2 deselected, 13 warnings in 109.75s

.\.venv-py39\python.exe -m compileall -q qbot/research examples/research tests/research

.\.venv-py39\python.exe -m qbot.research.cli --help
# 已列出 activate-forward / freeze-forward-model / forward-signal

.\.venv-py39\python.exe -m qbot.research.cli audit --config configs/research/csi500_smoke.yaml
# success on clean commit 528c39f: 20260923T165306.531462Z-audit-61c9c053

.\.venv-py39\python.exe -m examples.research.phase4_synthetic_demo --output results/examples/phase4_synthetic_acceptance_20260924_final
# success: 2099 年 synthetic activation，Ridge bundle，ON_TIME v000001，LATE_REISSUE v000002
# 两个版本均有 completion receipt；明确标记 SYNTHETIC SOFTWARE DEMO ONLY

.\.venv-py39\python.exe -m qbot.research.cli download-data --config configs/research/csi500_smoke.yaml
# failed safely at BaoStock login after 4 attempts on clean commit 47f1564:
# 20260923T165405.262372Z-download-data-9af5efa1
```

`pytest` 默认按 `pytest.ini` 排除两个 network marker。13 条 warning 均来自当前
Matplotlib/PyParsing 兼容层，不是测试失败。

Phase 4 新测试覆盖：

- disabled-by-default 和严格配置合同；
- activation advance-only、并发、不可覆盖和篡改；
- 注册时钟不可由调用者传入、源码摘要与 symlink/reparse 拒绝；
- 滚动 `data.end` 不改变研究合同；
- 训练标签成熟边界与单一候选参数；
- 整数/带时区/非午夜日期拒绝，以及 FinalModelFit 审计字段防替换；
- bundle 文件、类型、参数、特征顺序和哈希校验；
- 上海收盘、未来日期、迟到原因与跨时区日期；
- signal symbol/rank/weight、并发版本、失败 staging 和不可覆盖；
- manifest/CSV/额外文件篡改检测；
- 下载部分失败、信号特征缺失、全流程并发锁与 producer completion 收据；
- 激活 → 冻结 → ON_TIME → LATE_REISSUE 的离线 CLI 生命周期。

## Changed files

核心：

- `qbot/research/forward/{activation,contract,integrity,model_bundle,policy,signal_recorder}.py`
- `qbot/research/forward/__init__.py`
- `qbot/research/cli.py`
- `qbot/research/config/models.py` 与 `config/__init__.py`
- `configs/research/csi500_5y.yaml`
- `configs/research/csi500_smoke.yaml`

测试：

- `tests/research/test_forward_*_phase4.py`
- `tests/research/test_cli_phase4.py`
- `tests/research/test_config.py`
- `examples/research/phase4_synthetic_demo.py` 与对应回归测试

文档：

- `README.md`
- `docs/research/{ARCHITECTURE_AUDIT,GETTING_STARTED,FORWARD_TEST,VALIDATION,RESEARCH_METHODOLOGY,KNOWN_LEGACY_ISSUES}.md`
- 本报告

## 真实数据与真实信号状态

本阶段没有用 synthetic 或历史重跑冒充真实结果。2026-09-24 再次执行真实 smoke
下载，run 为 `20260923T165405.262372Z-download-data-9af5efa1`：benchmark 缓存可读，
确认 88 个研究交易日和 130 个精确预热交易日，但 BaoStock 登录连续四次网络接收
错误后以 `failed` 结束。因此 PIT 股票池、个股数据、真实数据集、正式模型和真实
RankIC/NAV 仍不存在。安全失败没有退化为当前成分股。

由于正式训练数据前置未满足，本次没有注册未来 activation，也没有冻结正式模型。
即便代码允许 `LATE_REISSUE`，它也不能越过 activation boundary，更不能把
`2026-09-14` 写成 `ON_TIME`。

## 已知限制

- 本地 SHA-256 和本机时钟不是第三方可信时间戳；应把配置、激活收据、模型和每日
  信号依次提交到不可改写历史，必要时使用受保护远端或外部 WORM/时间戳服务。
- 拥有文件系统权限的恶意操作者仍可删除整个目录；本实现保证正常 API 与并发调用
  不覆盖，并检测普通内容篡改，不声称法律级不可篡改。
- 模型使用 pickle，只能加载本项目生成且来源可信的本地产物。
- realized-return 关联评价需等 `t+6` 开盘数据实际成熟后生成；原始 signal 文件不应
  为此修改。
- Optional Streamlit Dashboard 未实现，不影响 CLI 核心。
- 真实数据源网络阻塞尚未解决，无法诚实给出五年实验或真实 forward 性能。

## 下一步

1. 在 BaoStock/AKShare 可用或导入经验证的 PIT 数据后完成正式五年数据与四模型实验；
2. 由研究者审核模型与 Validation 证据，明确批准一个仍在未来的新 activation date；
3. 按 `FORWARD_TEST.md` 依次提交配置、激活收据、冻结模型和每日信号；
4. 标签成熟后新增只追加的 realized-return 关联与 Forward IC/RankIC 报告，不修改原始信号。
