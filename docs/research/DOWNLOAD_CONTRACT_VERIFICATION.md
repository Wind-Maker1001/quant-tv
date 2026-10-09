# 下载合同与严重错误阻断验收（2026-10-09）

本轮修复上轮明确记录的研究红线：个股下载原先捕获所有异常后继续，可能把严重 Schema 错误当成普通网络缺失并让下游过滤掉该股票。没有改变因子、标签、模型、股票池要求、交易参数或 Legacy 模块。

## Changed files

- `qbot/research/errors.py`、`data/providers/akshare.py`：明确的 `ProviderNetworkError`、保守网络重试分类和 SDK 输出的结构/数值校验。
- `qbot/research/data/download_status.py`：严格、不可变 fatal/resolution 收据与 SHA-256 链、原生跨进程锁、损坏/中断时 fail closed。
- `qbot/research/cli.py`：严重错误立即停止、网络失败列表、强制重新取数、共享守卫及公开研究命令阻断。
- 扩展 AKShare 旧测试，新增 Provider 失败合同、收据和 CLI 回归；更新数据规范和快速开始。
- `tests/research/test_download_repair_concurrency.py`：正常并发 writer 的确定性时序回归，不靠 sleep 猜调度。

原始 LICENSE、GUI、Qlib、easyquant、实盘接口、根依赖未修改。只创建本地逻辑提交，不 push 或改写历史。

## 合同与恢复

只有明确的 transport 错误或可辨识的 HTTP 408/425/429/5xx 才重试并最终成为 `ProviderNetworkError`。其他 HTTP、JSON、权限/磁盘、参数/代码错误，以及非 DataFrame、重复日期、非法数字/OHLC、缺字段或 raw/hfq 日期不一致都不能伪装成可跳过网络错误。验证 SDK 输出，不声称能够恢复 SDK 已经 coercion 掉的原始输入或未暴露的 HTTP 状态。

个股网络失败继续扫描其他股票；`failed_symbols.json` 是本轮股票失败列表，Benchmark 的错误另记在运行清单和严重收据中。Benchmark、PIT 和证券状态仍是强制输入。Schema 或缓存错误立即停止，已成功写入的股票 generation 保留，不回滚或删除用户数据。

专用守卫目录为 `data_root/raw/download_status/`，不按 Provider 隔离。每次事件独占创建 `receipt.<id>.json`，最后发布 `current.json`；历史 receipt 从不覆盖，resolution 引用此前全部未解决 fatal 的 ID，并绑定实际校验的缓存 metadata SHA-256。RunManifest 记录原始错误、收据/目录输出、解除 ID 和仍未解决的 ID。

重跑 `download-data` 对有 fatal 的股票绕过 covered-range 跳过逻辑，实际请求当前范围与所有旧失败窗口的并集。空响应、只读旧缓存、换 Provider、缩短研究日期或网络失败都不能解除。原始响应经过 Schema 和缓存发布/快照校验后才追加 resolution；Benchmark 的实际新响应必须满足配置首末日期及预热数量。来源合同与旧缓存冲突仍严格报错，需要明确的新数据根目录和重新验证流程，不能给旧 metadata 重贴标签。

解除还绑定实际取数开始前观察到的同 symbol 收据 ID 集合。在取数、缓存发布和解除之间，另一个正常 writer 若记录新的同 symbol fatal，本次旧请求不能顺便解除它；必须保留阻断并再取数。其他 symbol 的新错误只阻断其自身解除及下游整体研究，不妨碍当前 symbol 的合法修复。另一修复已合法解除旧集合时不重复编造 resolution。

完全缺失的守卫历史对此前的缓存保持读取兼容，不代表它能认证旧版本的下载过程。存在但无提交历史、缺指针/receipt、未知文件、哈希链错误、符号链接或发布遗留都会严格拒绝。父目录永久 OS 锁覆盖第一次初始化和后续发布；锁不能删除来“解锁”，进程退出后 OS 自动释放。

普通 provider 错误应先修复源数据，再重跑实际请求。收据本身发布失败或被部分破坏时，不自动吸收孤立文件、重置指针或删除历史；先保留整个目录、相关 RunManifest 和缓存，人工核对文件字节、完整哈希链及事件上下文后再恢复提交指针。无法验证的原目录继续封存，不能宣称已被合法解除。代码没有提供自动 ledger 修复工具。

入口守卫阻止构建/评价/Walk-Forward/比较/激活/冻结/Forward 命令，不是运行全程监控。命令已固定的合法输入快照不会因为另一进程稍后的新事件自动终止。网络扫描可以为 success，但存在历史 fatal 时会输出 WARNING 与未解决 ID，后续研究仍失败。

## Tests passed / Commands executed

使用 Python 3.9.25 实际执行：

    .venv-py39\python.exe -m pytest -q --junitxml=results/runs/download-contract-full-20261009.xml
    .venv-py39\python.exe -m pytest -q tests/research/test_download_status.py tests/research/test_cli_download_contract.py tests/research/test_download_repair_concurrency.py tests/research/test_local_cli_pipeline.py --junitxml=results/runs/download-contract-targeted.xml
    .venv-py39\python.exe -m pytest -q tests/research/test_akshare_provider.py tests/research/test_akshare_failure_contract.py tests/research/test_cli_download_contract.py -k 'not public_local_file'
    .venv-py39\python.exe -m compileall -q qbot/research tests/research
    .venv-py39\python.exe -m qbot.research.cli audit --config configs/research/csi500_smoke.yaml
    git diff --check

最终全量 **1073 passed、2 deselected、13 warnings，280.18秒**；JUnit 为 `results/runs/download-contract-full-20261009.xml`。源码/测试/文档在此测试运行期间冻结，未以跳过公共整链或放松来源校验换取通过。

守卫/CLI/本地整链组合 **111 passed，59.35秒**；JUnit 为 `results/runs/download-contract-targeted.xml`。并发修复前的 Provider/CLI 定向178 passed、1 deselected（只暂排公共长链，最终全量未排它）、11.53秒；最终收据独立78 passed、9.06秒，确定性 CLI 并发3 passed、2.97秒。compileall、diff --check 均通过（Git 仅提示既有 CRLF 规则）；audit 返回0，清单 `20261009T065449.736099Z-audit-a5a10c41`，仅证明配置/审计入口可运行。

2 deselected 是明确标注的真实联网测试，不是泄漏或并发测试；13 warnings 来自既有 Matplotlib/Pyparsing 依赖。未执行带外部副作的 Legacy suite。

公开人工文件流程实际执行 `import-market-data → import-universe → import-security-data → download-data → build-dataset → evaluate-factors`。网络被禁止，使用生产 Provider、缓存和校验逻辑。先注入 Schema 故障，下载立即停止，旧行情 generation 保留；build/evaluate 均被收据阻止。修复后实际重抓完整85个交易日，再生成40行 dataset、28个成熟标签、有效 RankIC、CSV/PNG/Markdown。9份运行清单为3 failed、6 success，fatal 历史保留并新增 resolution。两只人工股票不属于真实 CSI500 历史证据。

第一次全量执行的工具句柄已失效，检查时 Python 进程也不存在，但没有保存最终摘要，因此不计为通过。随后独立代码复审发现上面的并发收据窗口，已补充17个直接 API 回归和3个生产缓存/CLI 时序回归；最终全量用 JUnit XML 保存可重查的证据。早先组合测试曾出现一次人工 CLI 长链失败，原因是其他文件在长链运行中改动，引发合法的 `git_diff_sha256` 来源拒绝；冻结后重跑通过，未放松该检查。另一次误用不存在的 `test_cli_phase1.py` 导致没有收集测试，不计为通过。

真实诊断也已执行：Python 3.9.25，`600000.SH`，2024-01-02至2024-01-12，零重试、原生 timeout 5秒，仅在该 Python 进程设置 `NO_PROXY=*`。本次再次失败，异常链为 `ProviderNetworkError → requests.ConnectionError → RemoteDisconnected`（后者位于连接异常内容中）；运行清单为 `results/runs/20261008T165241.720802Z-diagnose-akshare-contract-8f4bdcae/manifest.json`。没有新真实行数、没有覆盖旧缓存、没有500股票失败任务。它证实此真实断连被明确分类为网络错误，不代表所有端点可用或原始行情已经完成。

2026-10-09 下午的后续真实重试得到局部恢复，不覆盖前述失败证据：

- 14:48（北京时间），同一9交易日请求成功：`20261009T064852.532218Z-diagnose-akshare-contract-7c1719b6`。
- 14:50，扩大为2023-06-01至2024-01-12，取得153个真实交易日，raw/hfq 对齐、单位与 Schema 校验、缓存写入和快照校验通过：`20261009T065031.160154Z-diagnose-akshare-long-contract-af5e6cfa`。
- 14:52，实际请求中证500同区间的官方基准行情，也取得153个交易日；不消费此前 metadata v1 的正式目录旧缓存，而是在独立诊断目录生成当前合同的新缓存。股票按该实际 benchmark 日历重新索引，缺失价格不填充。生产 Factor Engine 生成14个因子，每个都有有效值；`MOM60/VOL60` 各93个，全部公式有效计数记录于清单。生产 Label Engine 生成147个成熟 `EXCESS_RET5`，尾部6天仍缺失：`20261009T065233.642286Z-diagnose-real-factor-label-0f6d47e6`。产物仅在 `data/research/diagnostics/download-contract/real-stock-factor-label.parquet`，不是正式 `processed/dataset.parquet`。
- 14:51，独立 BaoStock TCP 探测仍在5.032秒超时：`20261009T065116.954792Z-diagnose-baostock-tcp-518be2d9`。没有登录成功或历史成分快照；不能据此确定远端服务、本地防火墙或路径故障的根因。

上述 run_id 的完整清单均在 `results/runs/<run_id>/manifest.json`。153行诊断不证明该股票是当时 CSI500 成员，不含证券状态过滤、横截面预处理或真实 RankIC。股票池/状态未通过，绝不以人工成员表补齐它，亦不启动声称完成500股票的任务。官方 benchmark 日历也仍需正式验收时独立核对中间交易日完整性。

## Known limitations / Next phase

用户确认没有外部历史文件。当前未取得完整真实逐日 PIT 与证券状态；已完成单股真实因子/标签诊断，但尚未完成真实横截面数据集/RankIC 整链、正式五年四模型实验或真实 Forward 结果。人工行情与故障注入仅用于验证软件，不用于研究收益、模型优劣或股票池真实性结论。

本地 append-only 加哈希链用于检测误损和不完整发布，不是有外部锚定的防篡改公证。完全不可写的存储无法保证任何日志被保存；有权限删除整个 ledger、备份和所有引用的人仍能抹去其存在。正式研究须另行保存/备份清单与收据，不能宣称本机制对恶意管理员不可绕过。

AKShare 个股原生 timeout 不是任务总时限，部分指数端点没有原生 timeout；未修改全局代理、requests 或 socket 设置。上市/ST/停牌/PIT 缺失不静默退化。9行历史局部行情成功不能证明整个五年来源恢复；此前真实请求及失败记录见 [LOCAL_DATA_VERIFICATION.md](LOCAL_DATA_VERIFICATION.md)。

下一步仍是取得并验证真实行情、逐日 PIT、状态和交易日序列，完成小规模真实 CLI，再进行正式历史研究。已实现的模型和 Forward 代码不等于实证已完成；不得回填已经过去的日期作为真实样本外信号。Forward 成熟收益与 IC/RankIC 关联仍是后续开发项。
