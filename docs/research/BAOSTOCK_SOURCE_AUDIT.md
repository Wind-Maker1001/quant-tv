# 历史成员来源复核与可复现实测（2026-10-09）

## 结论与本次计划调整

当前没有经过独立核验的真实逐日中证500 PIT 股票池或 ST/停牌状态。因此没有正式研究 dataset、真实横截面 RankIC、五年四模型比较或真实 Forward 结果。用户确认没有可供导入的历史文件；程序不要求账号、API key，也不使用当前成分、每周快照插值或人工猜测来填补。

原计划假设 `query_zz500_stocks(date=...)` 逐日调用足以建立实际生效成员；此次公开来源复核不支持该假设。Firecrawl 帮助读取官方 API、版本说明和 publisher PyPI 数据，实际代码决策遵循“研究正确性优先”：保留来源诊断，但阻断正式发布与消费，而不是把可连接的接口等同于可验证的 PIT。

## Primary sources 与实际发现

| 证据 | 能说明什么 | 不能说明什么 |
| --- | --- | --- |
| [BaoStock 官方 CSI500 API](https://www.baostock.com/mainContent?file=pythonAPI.md#query_zz500_stocks) | 接口按周一更新；`date` 是查询日期，`updateDate` 是更新日期 | 查询日期不等于真实调样生效日；文档未承诺所有临时调整均按实际交易日追溯 |
| [官方数据/版本说明](https://www.baostock.com/mainContent?file=home.md) | 成分信息周一下午入库；0.9.1 支持多节点，0.9.4 于2026-09-21新增 VIP key 支持 | 新入口并不解决历史成员语义问题；匿名诊断不需要 VIP key |
| [publisher PyPI 0.9.4](https://pypi.org/project/baostock/0.9.4/) 与实际 wheel | 公共节点常量为 `public-api.baostock.com:10030`，VIP 为独立入口 | 不保证当前网络稳定，不证明成员生效日期或原生超时机制 |
| 已安装0.8.9代码 | 当前固定环境仍连接 `www.baostock.com:10030` | 端口超时不能单独区分服务器、路由、防火墙等原因 |

新 wheel 仅下载到 `data/research/diagnostics/baostock-sdk/`，没有安装、替换旧 SDK、修改常量或改系统代理。发行文件 SHA-256 已与 publisher 元数据核对：

    0bf71c6069ab5890ff3596632f9c3f8f1fbc6bfcac582c2f9d6a5c11ab2cfaf8

2026-10-09 07:09:52 UTC，旧入口单次 AF_INET 连接5秒超时，耗时5.016秒。07:15:59 UTC，新官方公共节点同样设置5秒上限，TCP成功，耗时0.046秒；清单为 `results/runs/20261009T071559.905135Z-diagnose-baostock-public-node-0b58d8f3/manifest.json`。这只是 TCP 证据，不能写成匿名登录或历史 API 已成功。

旧 SDK `ResultData.next()` 的空响应可能在错误码仍为0时返回 False。0.9.4 会在不足2000行的页面结束，而恰好2000行后的空响应仍不一定产生错误码。端到端诊断使用父进程总超时监督独立子进程，不假装 SDK 自带可靠全任务 deadline；不 monkeypatch 全局 socket。

## 代码门禁

- `collect_point_in_time_universe` 对 BaoStock Provider 及子类在请求、缓存访问、目录创建、发布之前拒绝。
- CLI 的正式股票池消费端拒绝旧 BaoStock schema 1/3 和 daily-v2 来源，避免历史缓存绕过。`download-data` 在股票池阶段拒绝，不启动500股任务；此前独立 benchmark 步骤可以成功或失败。
- 固定错误：`POINT-IN-TIME UNIVERSE REQUIRED: EFFECTIVE MEMBERSHIP SEMANTICS UNVERIFIED`。没有 `verified=true` 或手工布尔值放行入口。
- 诊断 `get_constituents` 保持三列输出，同时在 `attrs` 保留服务端查询日期与原始 `updateDate` 集合，明确标记未核验语义；这些信息不授权正式发布。
- 将配置改为 `local` 不会使 BaoStock 身份的旧 manifest 合法。真正的 local 导入必须以独立核验的真实生效日文件为前提；结构/哈希检查不是外部来源真实性证明。
- 软件级 CLI 测试改用实际 local importer 导入人工成员，而不是制造 BaoStock 已验证身份；人工数据仍不代表真实市场证据。

未来解除限制需要：研究起点的权威成员基线、研究区间全部定期和临时调整的实际生效日期、退出语义及证券代码历史，逐日与来源交叉验证后建立新的受审计来源合同。官方公告日、周更新日及调样生效日必须区分。仅查到官网、单份公告、ETF季度持仓或当前成分均不够。

## 可运行示例：真实单股因子与标签

    .venv-py39\python.exe -m examples.research.real_factor_label_smoke --config configs/research/csi500_smoke.yaml --start 2023-06-01 --end 2024-01-12 --symbol 600000.SH --retry-count 0 --timeout-seconds 5

默认独立缓存位于 `data/research/diagnostics/market-smoke/<provider>/`。脚本调用生产 Provider、Schema、Parquet Cache、benchmark 日历、14因子和 `t+1 open → t+6 open` 标签，不作价格填充。每次运行的四份 Parquet 产物均放入唯一 run 目录，并绑定同一次读取的缓存 metadata、内容/字节哈希及输出 SHA-256。参数窗口就是实际诊断窗口，没有隐式添加正式130日预热。

也可显式只读复跑已验证的真实缓存（不能自动补缺或改旧 cache）：

    .venv-py39\python.exe -m examples.research.real_factor_label_smoke --config configs/research/csi500_smoke.yaml --start 2023-06-01 --end 2024-01-12 --read-only-cache-root data/research/diagnostics/download-contract

`600000.SH` 只是连接性例子，绝不声称它在当日属于中证500。清单永久记录 `diagnostic_only=true`、未验证 PIT、未评价 RankIC；单股不能计算横截面 RankIC。原生5秒参数只覆盖个股连接/读操作，当前 AKShare 指数 SDK 没有该超时参数，不等于全任务5秒截止。

真实网络复跑07:21和07:22 UTC均在 benchmark 首次请求失败，完整失败清单分别为：

- `results/runs/20261009T072155.454429Z-real-factor-label-smoke-f1d3df0f/manifest.json`
- `results/runs/20261009T072239.952993Z-real-factor-label-smoke-cde7ccaa/manifest.json`

第二次只在 Python 诊断进程设置 `NO_PROXY=*`，没有修改系统代理。失败不可被缓存复跑成功覆盖；只读复跑必须另有 run_id，并明确 `data_access=existing-verified-cache-only`，不能报告为新 HTTP 下载。

07:30:35 UTC 实际执行上述只读命令成功：153个真实基准交易日、153个真实个股行，全部14因子都有有效观察、147个成熟 `EXCESS_RET5` 标签，最后6个标签缺失。新清单 `results/runs/20261009T073035.948434Z-real-factor-label-smoke-28e6a2a0/manifest.json`，四份隔离 Parquet 位于 `results/diagnostics/market-smoke/<run_id>/`；绑定先前实际网络下载的 source identity、metadata/hash，未重新取数或重写旧 cache。它是可复现实测，不是正式成员、证券状态或横截面排序能力的证据。

## 可运行示例：隔离 BaoStock 官方公共源

先取得已核对发行哈希的 wheel，不装入固定研究环境：

    .venv-py39\python.exe -m pip download --no-deps --only-binary=:all: --index-url https://pypi.org/simple baostock==0.9.4 --dest data/research/diagnostics/baostock-sdk
    .venv-py39\python.exe -m examples.research.baostock_source_probe --config configs/research/csi500_smoke.yaml

父进程先核验 publisher wheel 哈希与版本，再启动 wheel zipimport 的独立匿名子进程。诊断将 SDK运行版本与固定环境已安装版本分开记录。默认总截止20秒，SDK输出不混入结果 JSON，不保存凭据、网络包或 key。即使返回500个成员且查询日期正确，清单仍然 `point_in_time_universe_verified=false`；所有观察只进入独立诊断目录，不发布正式 universe。

07:36:02 UTC 实测匿名登录及三个查询合同成功，隔离执行0.9.4而固定环境仍为0.8.9。清单 `results/runs/20261009T073602.968748Z-baostock-source-probe-10e85834/manifest.json`，同目录保存带 SHA-256 的完整 `diagnostic.json`：

| 查询日/服务端日期 | 唯一成员数 | `updateDate` 分布 | 解释 |
| --- | --- | --- | --- |
| 2023-12-08 | 500 | 全部2023-12-04 | 服务端查询日期正确，但更新日不同 |
| 2023-12-11 | 500 | 全部2023-12-11 | 与上一查询相比增50、减50；不是全部生效史的证明 |
| 2024-01-02 | 500 | 全部2024-01-01 | 与2023-12-11成员哈希相同；更新日不一定是交易日 |

随后使用正式研究首末边界单独诊断：

    .venv-py39\python.exe -m examples.research.baostock_source_probe --config configs/research/csi500_smoke.yaml --date 2021-09-13 --date 2026-09-11 --timeout-seconds 20

07:38:11 UTC 该运行明确失败，而不是因登录/超时失败：2021-09-13 返回499个唯一成员、更新日2021-09-13；2026-09-11返回500、更新日2026-09-07，两者服务端错误码均为0。清单 `results/runs/20261009T073811.128186Z-baostock-source-probe-b94ce4ff/manifest.json` 保留完整观察及 `query_contract_verified=false`。这直接不满足本项目每日恰500的协议，但尚不能区分供应商缺项与指数当日真实特殊情况；未补一个当前股票、未降低成员数门槛，也未将源错误码0等同于正式数据合格。

## 验收范围与下一步

本次新增门禁测试覆盖实例/子类、完整500成员、服务端日期相同、更新日期过去/当日/未来、已有缓存及伪 verified 属性。真实单股示例测试覆盖来源/哈希、尾部六天缺标签、未来数据边界、失败清单、重复运行不覆盖、零网络 mock 和只读覆盖失败。源探针测试以离线 subprocess 模拟验证 deadline、哈希、响应结构与永不升级 PIT 的语义。

模块验收实际通过：门禁/Provider/原 Universe 三文件56项；真实示例44项；隔离源探针30项；CLI与门禁最终定向89项（排除一个长模型比较测试，保留JUnit `results/runs/pit-semantic-targeted-final.xml`）。首次 CLI 定向为57 passed/6 failed，原因是测试从旧BaoStock身份切换实际local importer后，五个旧 schema fixture仍混入generation字段、一个状态测试仍选BaoStock成员源。已修正fixture协议，并保留原有拒绝规则，未放宽生产校验。

首次全量1160 passed/5 failed/2 deselected，347.67秒，失败原XML保留为 `results/runs/pit-source-full-20261009.xml`。五项旧 generation/snapshot 写故障测试用同名假 BaoStock 身份，并期望正式 CLI 接受该产物，与新门禁冲突。现改为明确人工 `SyntheticSnapshotProvider`：保留原故障注入、全部尝试次数、查询次数、旧指针字节、不可变代、缓存复用等断言；另核验诊断 generation 的内容/字节哈希、日期覆盖和区间一致性，并明确正式入口拒绝。两个文件独立27 passed，3.62秒，没有回退生产门禁。

最终全量实际通过：**1165 passed、2 deselected、13 warnings，355.83秒**；JUnit 为 `results/runs/pit-source-full-final-20261009.xml`。两个 deselected 是默认排除的网络测试；13 warnings 是既有 Matplotlib/Pyparsing 警告。没有运行带联网、邮件或 GUI 副作用的 Legacy suite。真实调用是上述独立诊断，而不是将 mock 单测写成网络通过。

实际命令包括：

    .venv-py39\python.exe -m pytest -q --junitxml=results/runs/pit-source-full-final-20261009.xml
    .venv-py39\python.exe -m pytest -q tests/research/test_baostock_effective_semantics.py tests/research/test_baostock_status_provider.py tests/research/test_cli_reproducibility.py tests/research/test_cli_phase2.py -k "not walk_forward_and_compare_commands_are_offline_and_complete"
    .venv-py39\python.exe -m compileall -q qbot/research examples/research tests/research
    .venv-py39\python.exe -m qbot.research.cli audit --config configs/research/csi500_smoke.yaml
    git diff --check

另实际执行两例的 `--help`、一次真实行情只读复跑、两次真实行情新下载失败、两次真实匿名源探针（一次查询合同成功、一次499成员失败），并分别核验四份真实行情输出与两份源诊断 JSON 的实际文件 SHA-256。未启动500股任务；不存在需要隐藏的500股失败名单，源缺口与失败运行均单独保留。

### Changed files（21个，最小侵入）

- 核心门禁：`qbot/research/cli.py`、`qbot/research/universe/csi500.py`。
- 配置说明：`configs/research/csi500_5y.yaml`、`configs/research/csi500_smoke.yaml`；没有改研究参数或添加豁免开关。
- 新可运行示例：`examples/research/real_factor_label_smoke.py`、`examples/research/baostock_source_probe.py`。
- 新测试：`tests/research/test_real_factor_label_smoke.py`、`test_baostock_source_probe.py`、`test_baostock_effective_semantics.py`。
- 原测试合同迁移：`tests/research/test_baostock_status_provider.py`、`test_cli_phase2.py`、`test_cli_reproducibility.py`、`test_pit_generation_publication.py`、`test_pit_snapshot_failure.py`。
- 文档：本文件与 `docs/research/{ARCHITECTURE_AUDIT,DATA,GETTING_STARTED,PIT_SOURCE_AUDIT,RESEARCH_METHODOLOGY}.md`；旧候选源审计保留，仅增加新复核说明。
- `.gitignore`：只增加普通 `results/diagnostics/` 运行产物排除。

实际执行 `compileall` 与 `git diff --check` 通过；原始 LICENSE 与审计的上游提交内容相同。Legacy、研究环境固定依赖和系统网络均未改。普通诊断运行产物被 `.gitignore` 忽略，`results/forward` 没有增加统一忽略规则。

下一步是继续取得独立可核验历史调样资料，或在数据等待期间完善已有纯软件研究/Forward 评价路径。不能因复杂模型或回测代码已有而跳过 PIT 前置；不追求强行生成正收益，不事后补录2026-09-14真实 Forward 信号。

## 官方公告的有限复核（同日补充）

Firecrawl 的只读浏览确认[中证官方调样公告目录](https://www.csindex.com.cn/#/about/newsCenter?typelist=announcement&related_topics=index_rebalance)
可按标题查询。检索“沪深300”的实际结果显示129条记录，首页包括2023-11-24、
2023-05-26、2024-05-31等定期调整公告以及临时调整公告；未遍历全部页，也未取得
五年完整公告集合。仅看到目录标题和发布日期，不能写成读取了附件或验证了生效日。

实际浏览[2026-09-09临时调整公告](https://www.csindex.com.cn/#/about/newsDetail?id=3006227)
正文发现，其因股票换股吸收合并而调整相关指数，生效时点依赖被吸收证券退市日，
并非直接采用公告日期。已发现官方附件链接，但未下载解析附件，未判断中证500是否
实际受影响，也未取得交易所退市生效证据。该链接的上传路径含2026-10-09，不能用
文件路径日期证明它在公告当天已可获得，或决定指数生效日期。

历史公告正文的直接 scrape 只得到网页框架，另一请求超时；新的浏览请求也超时。
这些失败不是“官方没有历史资料”的证明。原只读交互会话已停止，未改站点状态、
未登录、未采集账号数据。有限官网观察只补充下一步溯源方向，不解除正式 PIT 门禁，
不把公告日、文件上传日、周更新日或临时调整依赖事件自动等同于真实成员生效日。
