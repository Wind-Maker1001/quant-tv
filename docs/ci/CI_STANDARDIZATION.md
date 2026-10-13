# FactorLab CI 分层与恢复条件

2026-10-13，Python 3.9，NO LIVE MONEY。CI 修改不授予金融数据资格。

## 核心研究验收

`research-tests.yml` 保留原 `Python 3.9 offline suite` 检查名、隔离依赖、完整
`tests/research`、Golden、防泄漏测试、`not network` 策略及配置/架构审计。
覆盖率在同一次 pytest 执行中测量 `qbot/research`，不另开一套重复研究环境。
`dev/requirements-research-ci.txt` 引用未改动的 `requirements-research.txt`，再固定
兼容 Python 3.9 的覆盖率和静态工具。没有合并 Legacy GUI/交易依赖。

输出真实 `coverage.xml` 和 JUnit，验证有效源码、执行数量和失败状态后上传 artifact；
失败运行也保留已有报告。没有覆盖率百分比阈值，报告用于观察，不能当金融认证。
源码覆盖率不等于行为正确性；子进程覆盖只反映工具实际捕获的范围。
核心测试失败仍使 job 失败，artifact 的 `always()` 不改变测试结果。
超时从 20 分钟增加至 30 分钟，为覆盖率插桩预留时间，不删除或跳过研究断言。

核心检查建议作为合并必需项。分支保护或 ruleset 需要管理员在具备权限/计划时配置；
本任务不改变仓库保护设置。

## 可选、可执行的质量检查

| 工作流 | 实际范围 | 合并必需建议 |
| --- | --- | --- |
| FactorLab static checks，文件名 `pylint.yml` | Python 3.9 编译；研究/测试/examples/CI Python 的 Flake8 E9,F63,F7,F82；变更空白；仅 CI Python 的 Black；CI 合同单元测试 | 远端执行通过后可设为必需；不是完整 Pylint |
| FactorLab workflow validation | actionlint 1.7.12 检查全部活动 workflow 和可选 CodeQL 模板；Linux 使用可用的 shellcheck | 远端执行通过后可设为必需；不冒充 Legacy 业务兼容验收 |
| Coverage | 已迁移到核心研究 job 的真实 XML/控制台报告及 artifact | 暂不设百分比门槛，先积累测量 |
| Add label automatically | 路径标签；不执行 PR 代码，不是质量/金融认证 | 不应作为研究合并必需检查 |
| CodeQL | 仅提供升级到 v4 的非激活模板 | 取得服务资格并完成真实上传后再决定 |
| SonarCloud | 当前没有本仓库项目/授权的证明，旧上游流程退出 | 有真实绑定及成功扫描后再决定 |

静态比较使用 PR 的 `base.sha`、push 的 `before` SHA 或首次推送时的
`origin/main` merge-base；检出完整历史，缺失/非法基准明确失败。
不使用 `HEAD~1`，不运行上游 GTest/C++/Bazel 格式脚本，也不修改被检查源码。
Git 空白规则承认 CRLF 为行尾，同时仍拒绝真实行尾空格；冻结参考字节不重写。

## 标签与写权限安全

标签规则为 research、tests、documentation、ci、data；不会删除或覆盖无关用户标签。
`sync-labels=false`。标签预先创建，所以 job 只需要 `contents: read` 和
`pull-requests: write`，不需要 `issues: write`。

自动事件使用 `pull_request_target` 的可信 base SHA，通过 GitHub API 读取 `.github/labeler.yml`；
没有检出 PR head、运行仓库脚本、安装 PR 依赖或执行 PR 配置中的代码。
手动 dispatch 仅供有仓库写权限的维护者选择已审查 ref，并指定本仓库 PR 编号。
标签流程不检出仓库；其余检查只在 Git fetch 进程环境传入只读凭据，不写入 Git 配置。
Actions 都固定完整 commit SHA。

**当前 PR 的部署限制：** `pull_request_target` 执行目标分支上的工作流。
在 PR #1 尚未人工合并时，`main` 的旧 labeler 和缺失配置仍可能被执行。
这不是新实现扫描通过的证据，也不能通过修改 main 或伪造状态消除。
使用指定分支的手动 dispatch 核验新实现；若 GitHub 不允许该 dispatch，则记录阻塞，
在人工审查/合并后用后续真实 PR 验证自动事件。具体平台规则见
[官方 labeler 文档](https://github.com/actions/labeler)。

## 六项旧失败的处理与恢复

原始配置仍由 Git 基线
`b26ca0c211a22bb561f5bc2f8156348742bd4379` 保留；没有改写历史。

| 原工作流 | 原始失败及用途 | 当前处理 | 恢复或完善条件 |
| --- | --- | --- | --- |
| Add label automatically | v4 缺少 `.github/labeler.yml`，自动添加 PR 标签 | v7 固定 SHA，新增当前项目路径规则和可信 base/手动读取 | 新配置人工合入 main 后验证后续自动 PR；标签属于元数据，非质量门禁 |
| Coverage | 占位 `path/to/coverage.xml`；运行无项目的 `.NET dotnet test` | 删除错误 workflow，覆盖率并入完整 Python 研究执行 | 不恢复 .NET 示例；以后确有 .NET 项目时另建专用合同 |
| Pylint | 浅检出下读取 `HEAD~1`，且调用上游多语言格式器 | 改为完整历史和独立只读研究检查；名称准确反映内容 | 全面 Pylint/Black 覆盖业务源码需另行评估既有风格，不在本轮重排业务代码 |
| Python application | Legacy `matplotlib==3.2.2` FreeType 构建失败；Qlib/mypy/nbqa 示例与研究环境混用 | 从自动 workflows 中删除，保留 Legacy requirements 和业务文件 | 明确 Legacy GUI/交易维护需求、隔离环境和有效输入后，先手动验收再恢复专用 workflow |
| Analyze with SonarCloud | 上游 UFund / ufund-me，远端 Not authorized | 删除上游 workflow；不声明本仓库扫描通过 | 本仓库自己的 organization/project key；管理员设置合法 SONAR_TOKEN；固定维护中的 Action；真实覆盖率输入和首次成功扫描 |
| CodeQL | v2 旧 Action；Code Scanning 未启用，SARIF 上传被拒绝 | 删除不具备条件的自动流程；`docs/ci/optional-workflows/codeql-analysis.yml` 为固定 v4 的非激活模板 | 管理员确认许可证/所有者/私有仓库资格及 Code Scanning；将审查后的模板移入 active workflows，再验证真实远端上传 |

现状为个人账户下的 PRIVATE 仓库，Code Scanning API 返回 403，仓库安全配置字段
未提供可用资格证明。GitHub 官方说明的常规私有库 Code Security 条件涉及具备
相应服务的组织计划；不能假设个人私有仓库或仅升级 Pro 就自动取得 CodeQL 服务。
参见 [GitHub Code Security 的适用条件](https://docs.github.com/en/code-security/getting-started/quickstart-for-securing-your-repository)。
分支保护 API 也返回计划相关 403；是否升级计划、迁移组织或改变可见性由用户决定。
本任务不改变可见性、Secrets、许可证、组织身份或服务授权，不无限重试扫描上传。

SONAR_TOKEN 元数据和 SONAR_ORGANIZATION/SONAR_PROJECT_KEY 仓库变量检查没有发现
本仓库绑定。真实 SonarCloud 项目状态为 UNKNOWN，不以公开查询不存在来断言没有私有项目。
不得继续使用上游身份，也不得创建、输出或硬编码令牌。

## 其余 Legacy workflow 的审计与退出

只读阶段的全目录 actionlint 明确失败：旧 Runner/Action、无效 needs 引用及废弃输出命令。
后续核对显示没有仓库 Secrets、Pages 未配置、统计入口路径错误、发布模板缺少部分输入。
根据本任务允许清理不适用流程的范围，以下文件从本分支的活动 workflow 目录退出。
原文件和既有业务功能保留在基线 Git 历史/业务目录，没有修改策略、GUI、依赖或发布版本。
这不是把失败 job 改成忽略错误，亦不声称旧 GUI/交易系统兼容新环境。

| 文件 | 原用途与实际输入/检查问题 | 退出理由及未来恢复条件 |
| --- | --- | --- |
| auto-trade.yml | cron 调用 Legacy 策略/GUI 与 SMS；所需 Secrets 未配置 | 与离线研究和 NO LIVE MONEY 隔离边界不一致；恢复需用户明确批准测试范围、隔离环境及通知，不自动恢复实盘/交易调度 |
| ci-release.yml | master / v 标签发布；退役 macOS Runner、旧 Actions、缺失 investool/release-lock 输入 | 上游多项目发布模板不完整；恢复需明确目标分支、有效制品/输入、固定版本和最小发布权限 |
| qbot-release.yml | main / v 标签 GUI/多语言发布；退役 Runner、旧 artifact Action、无效 needs.release、缺失 investool | 不是有效当前研究发布协议；恢复需先单独验收各 Legacy 包与真实发布需求 |
| greetings.yml | 上游促销欢迎语、占位 LGTM 图片及移动 main Action；PR/issue 写评论 | 社交模板不证明质量，没有当前项目有效内容；恢复需明确用户需求、真实内容及固定维护中的 Actions |
| html-static.yml | 上传整个仓库到 Pages；Pages API 404、旧 Pages Actions | 没有已配置的站点和经确认发布边界；恢复需用户确认私有库资格、站点来源、允许发布内容与权限 |
| repo-clone-stats.yml | cron 创建 gist、修改 Secrets、执行下载的移动分支脚本；缺少 PAT/GIST 配置 | 无有效授权，外部代码/写权限边界不明确；恢复需明确统计需求、最小凭据和固定审查脚本，不自动创建 Secrets |
| repo-stats.yml | cron 写统计；scripts/update_repo_stats.py 不存在、SECRET_TOKEN 未配置、旧 setup Action | 当前入口错误且未配置授权；恢复需专用读取权限、真实入口、隔离产物及受控写入 |
| tagging.yml | dev PR closed 自动改版本、强制标签；旧 checkout Action | 不属于当前 main/研究发布合同；恢复需经批准的版本协议，不能沿用强制标签更新 |

基线历史仍保留这些旧版本，活动目录不再执行未固定第三方 Action。
本轮的“完整 SHA 固定、最小权限”结论适用于当前活动研究/标签流程和可选 CodeQL 模板，
不是对 Git 历史中全部工具或业务源码的安全认证。
活动目录的删除在本分支生效；默认分支上的 cron、pull_request_target 和部署配置只有在
用户人工审查合并或手动停用后才改变。代理不修改 main、不擅自修改仓库 workflow 启用状态。

## 本地复核

使用 Python 3.9 的独立 CI 环境安装 `dev/requirements-research-ci.txt`，不升级现有 Legacy
或研究工作环境。检查命令：

```powershell
python -m unittest discover -s .github/scripts/ci -p 'test_*.py' -v
python .github/scripts/ci/research_checks.py
python -m black --check --diff .github/scripts/ci
python -m pip check
python -m pytest tests/research -q -m "not network" --cov=qbot.research --cov-report=xml:<new-output>/coverage.xml --junitxml=<new-output>/research.xml
python .github/scripts/ci/validate_reports.py <new-output>/coverage.xml <new-output>/research.xml
```

actionlint 1.7.12 使用官方 release 的 SHA-256 固定下载；本地 Windows 验证 YAML/表达式，
Linux workflow 使用可用的 shellcheck。覆盖率执行方式变更需要一次实测，不能用单元
测试中的人工 XML 作为实际覆盖率 artifact。完整测试结果和远端运行状态见本轮验收报告。

2026-10-13 本地实测：Python 3.9.25 / Windows，完整覆盖率研究测试仅执行一次，
2666 passed、0 failures、0 errors、0 skipped、2 deselected、88 warnings；pytest
耗时 975.02 秒，包装进程耗时 977.268 秒。真实覆盖率 XML 为 13019 / 15004 行，
line-rate=0.8677，无百分比门槛。最终 19 项 CI 合同测试、221 份 Python 编译、上述
Flake8 规则、3 份 CI 脚本 Black、pip check、全部活动 YAML 的 actionlint 通过。

一次报告校验失败暴露了 coverage 将仓库根目录写入 source、研究路径写入 filename
的实际输出格式。已改为校验规范化后的完整来源路径，增加对应正例及无关路径、
相似目录、路径回退反例；直接重新验证原 XML，没有重跑研究测试或修改报告。
271 份受保护研究/Golden/配置/依赖/历史脚本的 SHA-256 与任务开始时一致。
本轮原始命令、日志、JUnit、覆盖率和哈希收据保存在新的本地目录
`results/diagnostics/ci-standardization/20261013-v1/`；历史验收目录没有改写。
此处记录本地事实；远端 CI 结果以 PR #1 checks 及最终交付报告中的运行链接为准。

首次远端运行在 checkout v7 的凭据清理阶段失败：基线存在缺少 `.gitmodules` 定义的
`pyfunds/funds` 和 `utils/thsauto` gitlink。稀疏检出的本地复现仍失败，故不以此冒充修复。
没有修改这些 Legacy 记录、创建假子模块来源或忽略错误。研究/静态/workflow 检查
改用相同的原生 Git 检出命令：获取完整历史及事件指定 SHA，不初始化子模块，
凭据仅存在于单次 fetch 进程环境中，派生授权头用 GitHub 日志掩码保护。
检出后核对精确 HEAD；研究文件、测试、Golden 和配置范围全部保留。
标签配置直接通过固定版本 github-script 调用 API 读取可信 base SHA 或经授权手动 ref。
新增 CI 合同断言检查三组检出一致、完整历史、事件 SHA 和不保存凭据。
这些修复只需定向验证；首次失败均未开始研究测试，不重复本地完整研究验收。

原生 fetch 已在远端成功；之后发现 Runner 的 Git LFS 全局过滤器试图下载 Legacy
wxPython Linux wheel，而临时 fetch 凭据已结束。已显式设置检出进程的
`GIT_LFS_SKIP_SMUDGE=1`，延续原 checkout 默认不下载 LFS 的研究边界。
当前 `git lfs ls-files` 仅列出 3 个 `dev/wxPython*.whl`，没有研究源码、Golden 或
研究数据文件。没有更改 `.gitattributes`、LFS 记录、二进制或任何来源资格。
