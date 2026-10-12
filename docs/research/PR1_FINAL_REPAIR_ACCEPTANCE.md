# PR #1 合并前修复与验收边界

2026-10-13（Asia/Shanghai）。基线 `b9fa6484c4a2d57ae970b0fcad9d7cf323ca7585`，
现有分支 `codex/factor-evaluation-performance`。Python 3.9，**NO LIVE MONEY**。

## P1-1：原文与规范化事实的绑定

旧代码会读取来源原文并验证哈希，但随后使用调用者提供的 RAW、成员、状态、
身份、单位、公司行为与参考表；这些事实没有从原文重解析。重新组装股票表、
重算参考哈希及补齐本地 review JSON 可绕过旧准入。文件哈希只能证明本地字节
未变，不能证明另一份表来自这些字节，也不能认证审查者或历史可知时间。

现在复用现有 TDX DAY 解码器：`SourceArtifact.read()` 先验证原文字节哈希和长度，
`TDX_DAY_BYTES_V1` 选择固定候选格式，从这份字节解码后与 RAW 的全部输入列、
全部行及顺序严格对照，不容差、不排序修补、不截断补齐。打包重放读取自包含原文，
不重新打开原 locator；locator 只提供原文件名的代码假设。解析源码也加入实现摘要。
该候选解析不证明证券身份、价格尺度或金融单位。

| 来源角色 | 当前可核验解析绑定 | 正式准入边界 |
| --- | --- | --- |
| RAW | TDX DAY 候选字节重放；其他格式未建立合同 | 未支持、混合未知来源、篡改/缺行/乱序/额外事实列均拒绝；TDX 成功本身也不授予金融资格 |
| PIT | 现有 CSV/Parquet 导入验证规范化结构，不等于上游历史成员生效链解析 | `SOURCE_BINDING/PIT` 不完整，拒绝真实认证 |
| 证券状态 | 无上游停牌/ST历史原文到状态表的完整解析合同 | `SOURCE_BINDING/STATUS` 不完整 |
| 交易日历 | 原文字节与独立日历仍缺固定来源解析合同 | `SOURCE_BINDING/CALENDAR` 不完整 |
| 历史身份 | 来源哈希关联不证明代码/实体/上市区间由原文导出 | `SOURCE_BINDING/IDENTITY` 不完整 |
| 单位 | 手工 UnitContract 及 artifact 不证明真实物理单位 | `SOURCE_BINDING/UNITS` 不完整 |
| 公司行为 | 本地规范化 generation 是自报事实；PDF 尚无条款/覆盖解析合同；Sina 因子只是观察 | `SOURCE_BINDING/ADJUSTMENT` 不完整 |
| 独立参考 | 参考表哈希与独立原文之间缺解析合同 | `SOURCE_BINDING/REFERENCE` 不完整 |
| 基准/换手/上市资料/锚点 | 同样不能用调用者表或声明补齐 | 分别以 `BENCHMARK`、`TURNOVER`、`LISTINGS`、`ANCHOR` 拒绝 |

新增 `SOURCE_BINDING` 阶段。真实来源当前一律 `INCOMPLETE`；合成软件测试为
`SOFTWARE_ONLY`，永远 `formal_admission=false`、`execution_admission=false`。
其他阶段的工程 PASS 不替代这一准入条件。完整本地 review 声明、改名来源、重算
自报哈希或更改 synthetic 标志都不能取得正式资格。不提供可注册任意解析函数或
人工 verified/PASS 的后门。

**P1-1 的可绕过风险已通过重放和明确 fail-closed 边界消除；真实金融资料的全部
解析合同尚未完成，不能宣称全源金融认证已实现。** 后续按来源单独建立版本化原文
解析、字段/覆盖映射、历史可知证据及独立审查者可信边界，再逐项替换代码中的拒绝
条件；本轮不建大型供应商框架，不重新取证。

## P1-2：冻结研究范围与预热

`QualificationInputs.research_start/research_end` 为独立研究日期声明，须由冻结研究
配置或独立协议填写。二者缺失、倒置或不在独立交易日历中，PIT 阶段失败；不从
membership、RAW 或 required_keys 的首尾日期推断。每个声明区间内的交易日必须有
完整成员，正式真实 CSI500 只能要求 500 名。预热日可以进入 RAW、状态与 required_keys，
但不进入正式 PIT 窗口；把预热成员混入正式成员表会作为额外日期拒绝。不会用当前
成分、工作日历或合成成员补齐真实资料。

新日期字段由 qualification recipe 序列化保存；来源解析代码摘要与报告一起重放。
旧包若没有独立研究范围或实现摘要已过期，必须重新资格评估，不能重写历史收据
使其通过。保留旧包原文用于追溯。

## 回归证据

先增加 17 个用例再修复生产代码，基线执行结果为 **15 failed / 2 passed**。
其中九类来源篡改反例会被旧代码错误正式放行；TDX 原文不变但 RAW/组装产物同步
修改仍被当作 RAW PASS；PIT 起点、终点及预热后正式边界缺日未被发现。内部缺日
本来可拒绝，正确预热窗口本来可通过，二者作为控制组。

修复后首次原用例与既有 qualification 测试 **49 passed**。新增严格行/列/顺序、
混合/重复来源、坏日期/截断/重复记录、自包含重放、独立日历边界、预热越界、
500 成员及缺一成员场景后，定向执行 **374 passed**。测试中的来源与 review JSON
均明确标记 SYNTHETIC REGRESSION ONLY，不是新金融取证或真实审查凭据。

完整安全离线研究套件只执行一次：**2700 passed，0 failures，0 errors，0 skipped，
2 network deselected**，1022.66 秒，88 个既有依赖弃用警告。实际覆盖 13110 / 15055
行，XML line-rate=0.8708（87.08%），无百分比阈值；同次运行的 Coverage/JUnit 已经
由原 CI 报告校验器验证。222 份 Python 3.9 编译、选定 Flake8、19 项 CI 合同、
CI Black、pip check、变更空白与全部活动 workflow/可选 CodeQL 模板 actionlint 通过。

本轮原始红/绿日志、JUnit、完整离线覆盖率与只读范围收据写入新的本地目录
`results/diagnostics/pr1-final-20261013/`；最终完整套件和远端状态以
[PR #1](https://github.com/Wind-Maker1001/quant-tv/pull/1) 最新验收记录为准。

范围核验：1235 个受保护 Git 对象相对基线无变更，包含 Golden、14 因子、四模型、
复权核与时间边界、冻结配置、Forward、Legacy 和活动 workflows。研究源码没有
Legacy 交易/GUI/经纪 SDK 导入；正式 PIT 门禁实际返回
`POINT-IN-TIME UNIVERSE REQUIRED: EFFECTIVE MEMBERSHIP SEMANTICS UNVERIFIED`，
Forward 实际返回 disabled。没有创建正式五年结果或真正 Forward 信号。

正式配置的 `build-dataset` 命令也实际以退出码 1 报上述 PIT 错误。仅新建失败收据
`20261012T185619.584096Z-build-dataset-b620fb0f`，其 status=failed、outputs={}；
没有修改先前实验收据，也没有构建正式数据集。

研究配置关闭不等于旧 main 的仓库调度已经停用：GitHub API 仍列出旧 AutoTrade
与 release 工作流为 active，开发分支删除尚未通过人工合并部署。本轮不恢复、
触发或修改其启停设置，合入后需核验默认分支。不能声称全仓实盘已有 Kill Switch。

长期平台目标、资产清单和未来安全替代流程见
[PLATFORM_EVOLUTION_AND_LIVE_BOUNDARY.md](PLATFORM_EVOLUTION_AND_LIVE_BOUNDARY.md)。
工程合并需核心研究、静态和工作流检查通过后由人审查；不自动合并 main、
不 force push，也不把工程合并视为研究或实盘授权。
