# 输入 generation 与行情证据验收

日期：2026-10-05。分支：`factorlab/phase-1`。本次完成缓存/PIT 的可靠发布和研究输入绑定，不代表真实五年实验或 Forward Test 已完成。

## Changed files

| 范围 | 文件 | 行为 |
| --- | --- | --- |
| 行情缓存 | `qbot/research/data/cache.py`、`data/__init__.py` | metadata v3 不可变文件、清单最后切换、同一字节快照校验/解析、OS writer lock、严格 v2 迁移 |
| 行情证据 | `qbot/research/data/provenance.py` | benchmark 与完整 PIT symbol 并集的 receipts；missing slot；独立于存储代次的语义版本 |
| PIT | `qbot/research/universe/csi500.py` | schema 3 不可变 daily/intervals、字节及语义哈希、manifest commit 后 best-effort aliases；每日缓存落盘成功才记成功覆盖 |
| CLI | `qbot/research/cli.py` | 固定 PIT 清单；dataset schema 4/producer/current input 校验；Walk-Forward 固定股票及基准输入；四模型固定报告字节和行情版本 |
| 配置 | `config/models.py`、`configs/research/csi500_5y.yaml`、`csi500_smoke.yaml` | `cache.lock_timeout_seconds: 10`，非负有限数值严格验证 |
| 新测试 | `test_cache_generation_publication.py`、`test_pit_generation_publication.py`、`test_pit_snapshot_failure.py`、`test_bar_data_provenance.py`、`test_comparison_snapshot.py` | 写入/指针失败、迁移、路径、篡改、并发、进程退出、快照一致性与报告 TOCTOU |
| 更新测试/文档 | `test_config.py`、`test_data_cache.py`、`test_universe_phase1.py`、`test_cli_phase2.py`、`test_phase1_file_pipeline.py`、`DATA.md`、`GETTING_STARTED.md` | 真实缓存文件 fixture、输入变化拒绝、迁移和故障恢复说明 |

Legacy、许可证、GUI 和实盘接口均未修改。

## Tests passed 与 Commands executed

独立环境为 `.venv-py39`，Python 3.9.25。实际执行：

```text
.venv-py39\python.exe -m pytest -q
# 最终：532 passed, 2 deselected, 13 warnings, 239.60s

.venv-py39\python.exe -m pytest -q tests/research/test_data_cache.py tests/research/test_config.py
# 49 passed

.venv-py39\python.exe -m pytest -q tests/research/test_cli_reproducibility.py tests/research/test_pit_generation_publication.py tests/research/test_phase1_file_pipeline.py
# 40 passed

.venv-py39\python.exe -m compileall -q qbot/research
git diff --check
# 均通过
```

增量还分别执行了缓存 generation（28 passed）、独立行情证据（54 passed）、PIT 每日落盘故障（6 passed）、比较快照（9 passed）的定向 pytest。第一次全量回归为 530 passed / 2 failed：失败位于旧 CLI mock 与产物登记边界，已修复 PIT 清单的重复读取并重新执行完整 suite。最终无失败；没有隐藏或移除失败测试。2 deselected 是默认排除的 network tests，13 warnings 来自既有 Matplotlib/Pyparsing。

文件级整链测试实际调用 `import-universe`、`import-security-data`、`build-dataset`、`evaluate-factors`，使用 65 个预热日、20 个研究日、2 只人工股票及全部 14 因子。生成 40 行数据集、28 个非空标签、有效 RankIC、CSV/PNG/Markdown 和四份 success run manifest，并验证 build/evaluate 的行情、PIT、证券状态与 dataset 版本连续绑定。此处的“真实文件”指生产 CSV/Parquet/CLI 路径，不是真实市场数据。

## 已验证的边界

- 首次写入失败不形成虚假覆盖；更新失败保留旧指针和旧 generation。未提交孤立文件不会成为可消费输入。
- metadata 和 Parquet 各读一次；清单在读取期间切换，旧快照仍指向旧代。哈希与解析不重新打开同一路径。
- 同股并发更新在 OS 锁内重读并合并，两个日期均保留；超时明确报错，异常或子进程终止后释放 OS 锁。
- 严格 v2 迁移不会提前覆写旧文件。来源不一致、篡改、缺失、路径逃逸、代次碰撞均拒绝。
- PIT daily/intervals/manifest 更新失败不破坏旧代。alias 不影响 verified consumer；每日缓存 Parquet/JSON 写失败不能被误报为已成功下载。
- 股票行情更正、缺行补齐、缺失股票缓存补齐、来源变化、甚至窗口外追加，都会保守地使旧 dataset 失效。
- 相同字节及来源合同在新 generation 重发布不改变语义行情版本；完整 producer receipts 仍必须与 dataset 清单精确一致。
- 模型训练期间行情缓存更新，Fast/Execution 回测仍使用训练前固定的输入。四模型行情版本不一致时拒绝比较。
- 模型比较从验证后的 CSV/Parquet 内存快照读取，不会消费校验后替换或新加入的文件。模型二进制等只流式校验，不全量保存在内存中。

## Migration 与 Known limitations

1. 来源、哈希及覆盖完整的行情 metadata v2 可直接读取，下次成功更新写 v3；v1/来源冲突须先归档或换 `data_root`。不要修改哈希来绕过校验。
2. 严格旧 PIT local v1/v2、BaoStock schema 1 保持只读。新发布为 schema 3。
3. dataset schema 3 不再用于正式评价/训练，必须在本次代码/环境下重新 `build-dataset`，并保留成功 producer manifest。
4. 缓存完整字节哈希是保守证据；窗口外增量也需重建。旧 generation 和孤立未提交文件暂不自动清理。OS 行情锁文件可长期存在；PIT 锁机制不同，异常中断后的恢复见 `DATA.md`。
5. 原子切换保证进程中断时不混读，不能证明供应商从未事后修订，也不承诺抵御所有断电或磁盘损坏。

本轮没有重试已经失败的真实网络端点。2026-10-05 最近实际测试仍是 AKShare `600000.SH` 请求 `RemoteDisconnected`、BaoStock 登录 `WinError 10057`，均在四次尝试后失败。只有 benchmark 曾成功，真实个股/PIT/状态烟雾链路仍不完整；没有形成 500 股完整失败清单、五年数据集、四模型实证报告或真实 forward signals。详见 `PHASE1_INTEGRITY_VERIFICATION.md` 的网络记录。

## Next step

优先取得可验证的真实历史行情、逐日 PIT 成分及证券状态（恢复公开端点，或使用严格本地导入路径），再执行真实小样本四步 CLI 验收。完整数据到位后才进入正式五年 Baseline/四模型实验；绝不以当前成分股或人工数据替代真实历史研究。

本次只创建本地逻辑提交，不 push、不改历史。缓存发布提交为 `2b41a0a`；其后的输入证据提交与最终工作区状态可通过 `git log` 和最新 `audit` run manifest 检查。

## 提交后 CLI 审计记录

输入证据提交为 `d605671`。实际执行 `.venv-py39\python.exe -m qbot.research.cli audit --config configs/research/csi500_smoke.yaml`：

- 首次 run `20261005T074740.289708Z-audit-ef1749fa` 因 Windows `WinError 5`（替换 run manifest 临时文件时访问被拒绝）返回 1，failed manifest 和残留临时文件保留；未删除或覆盖这次失败记录。
- 同命令重试 run `20261005T074820.258563Z-audit-00f9c95c` 返回 0；manifest 为 `status=success`、`git_dirty=false`，绑定 `d605671ed145bc80afa710e7dab72b3a0fff56bf` 与 Python 3.9.25。

该访问拒绝尚未确定原因；单次重试恢复不等于根因已修复。运行清单写入仍应关注 Windows 短暂访问拒绝，后续可在不掩盖持久权限错误的前提下补专门的有界重试与临时文件恢复测试。本项不会把首次失败伪装为成功。
