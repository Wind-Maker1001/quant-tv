# 本地行情入口与数据边界验收（2026-10-08至09）

本轮有实际代码、测试和真实请求进展，但尚未满足真实 CSI500 端到端、正式五年实验或真实 Forward Test 的验收条件。用户确认没有可供导入的历史文件；以下人工数据测试不能替代它们。

## Changed files

- `qbot/research/data/providers/local.py`：严格静态 CSV/Parquet 行情导入、不可变 bundle、同字节哈希/解析、线程安全 pin-once、来源与单位/复权合同。
- `qbot/research/cli.py`、`config/{models,loader}.py`、`data/{__init__,providers/__init__}.py`：公开 `import-market-data`，本地 Provider 路由、独立缓存路径、三种导入共用仓库相对路径解析。
- `data/schema.py`：拒绝所有数值列的无穷大、错误复权因子及 canonical/raw 缺失位置不一致；合法 NaN/零成交仍保留。
- `data/providers/akshare.py`：原始与后复权个股请求都传递配置的原生连接/读取超时，保留旧位置参数 API。
- `reproducibility.py`：仅对 Windows 5/32/33 替换错误重试同一个临时文件，最多4次，间隔0.025/0.05/0.1秒；一次序列化、flush、fsync，持久故障保留原错误与旧清单，只清理本次拥有的临时文件。
- `data/cache.py`：无缓冲打开永久锁文件，先取得原生 OS 锁再初始化；初始化失败释放锁，解锁二级错误不遮蔽原异常，成功 body 若解锁失败则明确报错。仍是跨进程锁，不用全局内存 mutex 替代、不删除锁文件。
- 新增5个测试文件并扩展 AKShare、CLI 路径和缓存锁测试；新增 `csi500_local_smoke.yaml`、`LOCAL_MARKET_DATA.md`，更新数据规范及快速开始。

Legacy GUI、Qlib、easyquant、实盘接口、根依赖与原始 LICENSE 未修改。不 push、不修改 Git 历史。

## Tests passed / Commands executed

实际执行使用 Python 3.9.25：

    .venv-py39\python.exe -m pytest -q
    .venv-py39\python.exe -m pytest -q tests/research/test_schema_phase1.py tests/research/test_schema_ohlc_relationship.py tests/research/test_schema_numeric_integrity.py tests/research/test_local_market_provider.py tests/research/test_config_local_provider.py tests/research/test_local_cli_pipeline.py
    .venv-py39\python.exe -m pytest -q tests/research/test_config_local_provider.py tests/research/test_local_cli_pipeline.py
    .venv-py39\python.exe -m compileall -q qbot/research tests/research
    git diff --check
    .venv-py39\python.exe -m qbot.research.cli audit --config configs/research/csi500_local_smoke.yaml

最终全量：841 passed、2 deselected、13 warnings，279.86秒。第一次全量：820 passed，255.65秒。路径统一修复后的定向测试：28 passed，23.59秒。Schema/本地数据相关集成测试：258 passed，25.46秒；本地 Provider 独立测试：139 passed，10.84秒。compileall 与 diff --check 均通过（Git 仅提示既有 CRLF 规则）。

第二次全量为823 passed、2 failed：两个旧 CLI mock 测试仍断言导入器接收未经解析的相对路径。已将它们更新为明确的 `config.repo_root / filename` 绝对路径，并让 fake receipt 使用实际传入路径，未删除测试或放松路径检查。随后 CLI 相关定向回归46 passed，25.02秒；异 cwd 的真实文件整链同时通过。

第三次全量为824 passed、1 failed（271.99秒）：两个独立行情缓存实例并发首次更新，在 Windows 锁文件初始化的 `handle.flush()` 出现 PermissionError。栈证实初始化发生在获取 OS 锁之前，存在未保护的并发写窗口。一次独立的 buffered append 模拟没有重现原错误，因此不宣称已经证明 Windows 内部偏移/缓冲的完整因果链。这是需要修复的锁生命周期边界，不能跳过测试或仅增大超时；修复与最终并发/全量结果在下文补记。

实际 Windows 原生诊断证明可以先锁空文件 EOF 外的 byte0；随后第二句柄竞争失败、owner 初始化成功、释放/关闭后另一句柄可锁。实现据此改为先锁再初始化，并使用无缓冲句柄。缓存两个测试文件57 passed（14.76秒）；锁专项再次17 passed（7.10秒）。新增16项回归，强制两个句柄先打开空文件并断言 write/flush 只能发生在成功加锁之后；覆盖初始化四类故障、open故障、原异常/解锁异常、5轮四线程和2轮四独立进程并发合并，原超时/强制终止释放测试也通过。这证明新的操作次序和释放语义，而不是声称已确定旧 CRT 内部竞争时序。

并发 spy 的断言最终按每个句柄自身 acquire/write/flush/release 的顺序检查，不强制原生解锁后的额外 Python 调度顺序；最终缓存定向复跑57 passed（14.27秒）。没有以放松锁语义换取稳定，也没有删除旧故障记录。

2 deselected 是默认排除的两个网络测试；13 warnings 是既有 Matplotlib/Pyparsing 警告。未运行有外部副作的 Legacy suite。曾误用不存在的 `test_schema.py` 路径导致一次 pytest 没有收集测试；随后用真实文件名成功执行，没有把那次当作通过。

公开入口整链测试不 mock Provider、因子、标签、数据集或证据校验。实际执行：

    import-market-data → import-universe → import-security-data
    → download-data → build-dataset → evaluate-factors

输入为65个预热日加20个研究日、两只人工股票、14因子，生成40行 dataset、28个成熟标签、有效 RankIC、CSV/PNG/Markdown 和六份 success RunManifest。禁止 HTTP 与 BaoStock 登录；另从其他工作目录以相对配置和输入路径重复整链，验证来源绝对路径与哈希。更换股票价格快照后，已有 benchmark cache 即使覆盖日期也被严格拒绝，旧 dataset 不被覆盖。

本地 `audit` 实跑返回0，run 为 `20261008T154006.982009Z-audit-fa323f54`。它只验证配置和审计入口，不证明数据已到位。

## 真实数据覆盖与失败

2026-10-08 的个股诊断没有改动系统代理；仅在该 Python 进程使用 `NO_PROXY=*`，请求超时5秒。

- `600000.SH`，2024-01-02至2024-01-12：取得9个真实交易日，raw/hfq 对齐，单位与 Schema 校验通过，写入 `data/research/diagnostics/akshare/daily` 的行情缓存。成功清单 `results/runs/20261008T153013.852948Z-diagnose-akshare-5aa5633e/manifest.json`，无失败股票。该股票是连接诊断标的，不代表它属于当时 CSI500。
- 将区间扩为2023-06-01至2024-01-12时，请求再次 `RemoteDisconnected`。默认3次重试共4次尝试均失败；失败清单 `results/runs/20261008T154920.466733Z-diagnose-real-factors-3bb606a6/manifest.json` 保留 `ProviderError → ConnectionError` 异常链。更早的零重试失败清单也保留。没有得到这个较长区间的14因子真实验证结果。
- `www.baostock.com:10030` 的一次独立 TCP 连接探测在5.03秒超时。这里只能证明当时的短时连接未完成，不能区分本地防火墙、网络路径或远端服务故障；没有据此发起500股票任务，也没有把先前 SDK 的10057二级错误当作确定根因。
- 第一次个股诊断因调用端误用 `max_retries` 参数，在网络请求之前失败；对应清单 `20261008T152421.078720Z-diagnose-akshare-84360bcb` 已明确记录 setup failure，未冒充下载成功。

因此本轮没有500股票正式失败清单、完整 PIT/状态、真实 dataset/RankIC、五年模型结果或真实 forward 信号。9行局部行情成功不等于整个网络已恢复。原始数据目录和普通运行产物按既有规则忽略，不提交市场大数据。

## Known limitations / Next phase

- **下一步优先修复的正式研究红线：** 独立复审发现 `command_download` 的单股 `except Exception` 仍会把 incoming SchemaError 或其 CacheError 包装当作普通下载失败；若该股票尚无缓存，随后 `build-dataset` 的缺股过滤可能生成缩小样本。这不满足“严重 Schema fail-fast”的最终验收。后续须区分可恢复网络错误与致命数据合同错误，并用未解决 fatal 收据阻止正式数据集生成。841项通过只证明当前覆盖的行为，不证明此未覆盖缺口已解决；在修复/新增回归前不发布正式研究结果。
- 本地来源是用户声明，不是第三方认证；显式 raw/hfq 与单位是合同，不能仅凭价格数值证明来源诚实。
- 本地行情是静态历史快照，修正后需新缓存根目录重建；旧 generation/孤立文件没有自动清理策略，不删除用户历史。
- 个股 `timeout_seconds` 是原生连接/读取超时，不是整个任务最大耗时。现有指数/当前成分 SDK 端点没有原生 timeout 参数，未通过全局 monkeypatch 或假线程超时伪装已解决。
- 中证500完整历史成分仍是正式研究硬门槛；没有用户文件，也没有验证可用的新 PIT 来源。绝不用2026年的当前成分回测2021年。
- 上述 fatal 边界修复后，恢复/取得真实行情、逐日 PIT 与证券状态，完成真实小样本 CLI；再执行正式五年 Baseline 与四模型实验。已实现的第二至第四阶段代码不等于这些实证验收已通过；不得回填已经错过的2026-09-14作为真正样本外证据。Forward 成熟收益关联/IC/RankIC 也仍是后续实现项，而非已经交付的实证。

后续补记（2026-10-09 下午）：上述 fatal 边界及正常并发修复窗口现已补齐，最终全量1073项通过；真实诊断也取得单股/基准153交易日、14因子和147个成熟标签。但 BaoStock 短时连接仍超时，未完成正式 PIT/状态或真实 RankIC。完整的新证据见 [DOWNLOAD_CONTRACT_VERIFICATION.md](DOWNLOAD_CONTRACT_VERIFICATION.md)，本页旧测试与失败记录保留，不据后续进展改写历史。
