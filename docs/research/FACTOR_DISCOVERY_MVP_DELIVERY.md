# 受约束自动因子发现 MVP 交付说明

**软件状态：SOFTWARE_MVP_SUCCESS。NO LIVE MONEY。这不是可交易 Alpha 的发现或正式金融验证。**

从核验的 main `48ea4dd8c1876c1515f3172c9bb2e812f20ebe82` 创建独立分支 `codex/automated-factor-discovery-mvp`。最终实际运行的源码提交为 `49e7901269495c43ece227e11a7deebbd9bd63b5`；随后仅提交这些公开报告和验证摘要。PR 最新 HEAD、研究/静态 CI 和 Codex 审查状态以 PR 正文最终记录为准，本地报告不预先宣称远程检查通过。

## 实际交付与运行

新增独立 `qbot/research/exploratory/factor_discovery/`，实现白名单 AST、量纲与价格基准检查、显式日历逐股票执行、有限模板生成、缓存与 Windows 预算、结构去重、逐日数值冗余、FactorLab 通用数学适配和独立收据。没有修改旧14因子、Golden、历史报告、资格门禁、Forward 或交易实现。

两个数据模式各实际运行两次。每次生成40条候选记录，39个结构唯一且成功计算，1条交换乘法操作数的审计重复，0计算失败、0语义拒绝。有限全集49条、按冻结顺序截断9条，覆盖趋势动量、收益波动、交易活跃和价量交互4类经济意义；拒绝与失败分支另有反例测试。

|证据|合成模式|私有历史50股模式|
|---|---|---|
|软件状态|SOFTWARE_MVP_SUCCESS|SOFTWARE_MVP_SUCCESS|
|真实数据状态|NOT_RUN；合成结果不能替代真实证据|SUCCESS；冻结授权与哈希核验后只读执行|
|开发窗口|2023-07-03—2023-12-15|2025-09-12—2026-06-30|
|39候选原始有效率范围|93.562500%—99.687500%|98.793651%—99.851852%|
|每候选最少有效RankIC日期|114|183|
|候选与旧14规范AST重复|0|0|
|候选之间数值冗余|{"NON_REDUNDANT": 716, "HIGHLY_REDUNDANT": 25}|{"NON_REDUNDANT": 717, "HIGHLY_REDUNDANT": 24}|
|候选与旧14数值冗余|{"NON_REDUNDANT": 541, "HIGHLY_REDUNDANT": 5}|{"NON_REDUNDANT": 542, "HIGHLY_REDUNDANT": 4}|
|两次完整运行耗时（秒）|12.616 / 19.655|34.203 / 27.159|
|表达式缓存峰值（字节）|7040000|12636800|

四次完整运行所在单个 Windows Python 进程的操作系统工作集峰值为 `409423872` 字节（包含导入、旧14计算、评价和诊断）。缓存峰值不是进程总内存。收据的 total_elapsed_seconds 包括最终写入；生成报告中的时间测量较早，不能混作同一测量点。

两次同模式运行的规范表达式集合、开发因子数值、逐日IC、五分位和评价摘要哈希全部相同。两模式表达式集合 SHA-256 均为 `56ec334218a0b5b81e6763caa78ebdf231434fd180f7e9aacbe67c2709a2df91`；合成开发因子哈希 `6fd87de90853cd095b6518be1903deec2036251d6f17abaf924d54f54c582d47`，私有开发因子哈希 `9d4458ac6fe6547fb71af560030866dcab9d45aca50860cb1fca6658ffef4621`。计时、运行身份与资源观测不参与数值确定性哈希。

## 全部表达式与描述性结果

[合成完整中文报告](evidence/factor-discovery-synthetic-v1/summary.md)及[私有完整中文报告](evidence/factor-discovery-private-v1/summary.md)分别列出40条记录（39个实际可执行表达式）的经济语义、原表达式、量纲、RAW/HFQ来源、完整规范AST、SHA、深度/节点/滚动复杂度、回看长度、计算状态，以及每候选有效率、缺失率、MAD异常率、处理后覆盖、IC和RankIC。每候选的耗时、静态操作量、缺失/除零原因计数在各 `candidates.csv` 中。

各目录另有 `daily_ic.csv`、`evaluation_summary.csv`、`factor_quality.csv`、`quantile_returns.csv`、`label_sensitivity.csv`、`redundancy_summary.csv`、冻结配置和独立 `receipt.json`。五分位按信号日因子可用性形成；未来标签仅在准确的t+1进入、t+6退出且全在开发期内成熟后聚合。完整标签子样本重分组只作为单独的选择敏感性诊断。

冗余按同日横截面再跨日汇总，不拼接不同日期；阈值事前固定为至少20证券、60天、80%平均配对覆盖、0.98平均绝对相关。EXACT_DUPLICATE、NUMERIC_DUPLICATE、HIGHLY_REDUNDANT、NON_REDUNDANT、UNDETERMINED 分开，实际高度冗余记录保留，未选优、翻转方向或写入注册表。

## 验证范围与快照

[机器可检查的验证摘要](evidence/factor-discovery-validation-v1/validation.json)保存各实际JUnit/coverage哈希、范围、快照与重复运行资源数据。原日志留在本地忽略目录，不发布可能含路径或输入诊断的完整日志。

|本次实际执行|结果|范围与限制|
|---|---|---|
|最终新模块pytest|85通过、0失败|最终源码 `49e7901269495c43ece227e11a7deebbd9bd63b5`；engine、generator、integration、公开包校验|
|原14与通用评价Golden|350通过、0失败|本次重新执行；旧公式与Golden后续无修改|
|完整离线tests/research|2975通过、0失败、2网络用例排除|源码快照065fabd；历史2895 + 当时新模块80；后续5个回归已纳入最终85项定向测试，最新PR全量CI再次覆盖最终源码|
|完整研究覆盖|85.37%，15189/17791行|上述完整离线实际报告；没有虚构门槛或最终HEAD覆盖率|
|静态与CI合同|PASS|264 Python文件；flake8 E9/F63/F7/F82；维护的3个CI脚本black检查；19个CI合同unittest|
|产物和公开边界|PASS|两份独立收据及每项字节SHA；严格文件/CSV列白名单；自重算收据也无法公开证券或分组成员列|
|旧数据/代码保护|PASS|原manifest与批准v2收据运行前后字节SHA不变；旧公式、Golden、资格配置、Forward/交易、历史产物Git差异为空|

第一次全量执行遇到两个历史测试的Windows跨盘路径假设（C:临时目录与D:仓库无法relpath）。没有修改历史测试；将pytest basetemp设为同一D:盘、仓库外的独立目录后，完整套件通过。初次失败不记作通过。

必须的15项要求均有定向覆盖：

1. 所有39候选的未来行情不变性。
2. 两证券Lag/Rolling人工预期与股票隔离。
3. RAW/HFQ及现金/股数推导价格、倒数和归一化后的来源约束。
4. 显式日历缺口不压缩、不填价。
5. 除零、非有限、非法日期/代码、未知节点与循环AST拒绝。
6. 交换律有限规范化、结构重复、哈希与真实数值重复运行。
7. 类型不兼容、动态/负滞后及隐藏标签节点拒绝。
8. 候选/深度/节点/滚动/回看/面板/操作/缓存/诊断/单调时钟预算。
9. 生成器无数据、标签、分区或文件输入接口，禁读测试。
10. 开发期之后价格及标签变化不改变开发输出。
11. 全部39×14逐日相关对用独立NumPy配对公式复算。
12. 缺私有数据NOT_RUN、篡改或计算失败BLOCKED、合成不能冒充真实SUCCESS。
13. 实际正式资格、正式配置、Forward模型/信号读取入口拒绝新Schema。
14. 原14、Golden、历史产物和资格/交易文件保持原字节及Git身份。
15. Windows/Python3.9.25四次真实闭环与最终定向测试。

独立审查已修复三项P1：推导RAW价格丢失来源、冻结标签缺少独立可信哈希锚点、近常数Pearson消减误差造成伪高相关；反例回归通过。源码与最终公开证据按独立提交封存，远程审查若新增P0/P1须修复并补受影响检查。

## 复现

使用独立Python3.9研究环境与 `dev/requirements-research-ci.txt`，从仓库根目录运行：

```powershell
.venv-py39/python.exe -m qbot.research.exploratory.factor_discovery --mode synthetic
.venv-py39/python.exe -m qbot.research.exploratory.factor_discovery --verify docs/research/evidence/factor-discovery-synthetic-v1/receipt.json
.venv-py39/python.exe -m qbot.research.exploratory.factor_discovery --verify docs/research/evidence/factor-discovery-private-v1/receipt.json
.venv-py39/python.exe -m pytest tests/research/test_factor_discovery_engine.py tests/research/test_factor_discovery_generator.py tests/research/test_factor_discovery_integration.py tests/research/test_factor_discovery_delivery.py -q
```

私有模式只在已有原授权冻结文件时，显式传 `--mode private --manifest <manifest路径> --frozen-receipt <已批准v2收据路径> --development-start 2025-09-12 --development-end 2026-06-30`。软件不会下载缺失数据；manifest字节、4输入与410源哈希、v2收据锚点、冻结标签锚点必须全部匹配。见[复用与来源审计](FACTOR_DISCOVERY_REUSE_AUDIT.md)。输出按独立run_version/attempt目录新增，不覆盖旧产物。

## 尚存限制与后续判断

P2工程限制：预算用静态操作/内存上限及有界算子间的Windows单调时钟检查，不能抢占单个底层NumPy/Pandas调用；精确浮点哈希保证限于同一源码字节、Python和依赖环境；合成业务日日历不是交易所日历。没有以跨平台逐位相同或硬实时中断作保证。

真实50股一年样本已被先前研究观察，是EXPLORATORY / UNVERIFIED / NON_PIT_CONVENIENCE；非PIT成分、幸存偏差、短样本、供应商HFQ未正式资格及事后多候选选择使本结果不能证明可靠Alpha。不存在独立未观察测试集或正式金融准入结论。

更长历史须独立授权/冻结来源、稳定证券身份与实际交易日历、PIT成分/状态、可重放合格HFQ、冻结成熟标签及真正隔离的验证/测试区间。优先完成这些数据条件与跨环境复现，再考虑遗传编程或LLM辅助更大搜索空间；当前有限模板足以验收软件闭环，扩大搜索会增加多重筛选负担，尚无必要。

公开Git仅含表达式、聚合指标、必要来源/收据哈希和非敏感报告。原行情、证券级因子/标签、供应商完整响应、私有分位成员及其可枚举摘要不入Git。正式14因子库与金融门禁保持原状，不启用Forward、实盘或下单。
