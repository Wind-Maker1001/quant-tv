# 正式行情统一准入边界

NO LIVE MONEY。软件修复不构成金融数据认证；正式五年研究仍然 BLOCKED。

## PR #14 的 P1 复核修正

请求价格行来自已重放 `required_keys` 在请求日历和证券内的子集，不再构造日期乘证券的
笛卡尔积。中途上市或换入指数不需要伪造上市前价格/状态。仍检查所有请求 PIT 键、真实
价格和状态行；缺行、变值以及资格范围外的上市前行必须拒绝。合成换股夹具只能证明
RAW/ADJUSTMENT/STATUS/PIT 软件合同，最终仍被 SOFTWARE_ONLY 金融门禁拒绝。

修订校验器不再直接导入。现有 CI 控制器先核对独立固定摘要，再编译同一份已核验字节。
`trust-anchor.json` 固定校验器和外层控制器，摘要由 `.github/workflows/market-admission.yml`
独立固定，并在导入仓库代码前用标准库复核。控制器、校验器、信任锚和此工作流不能进入
校验器自身的授权列表；不能通过同时重封装校验器、收据或候选信任锚自行获准。
顶层工作流是独立评审的信任根；此机制不声称能阻止有权同时重写整个 CI 与测试的操作者。

## 原因与修复范围

基线 `657486f8ca928c1e66b430f471cfe5ce96a613ab` 的 `_load_bar_inputs` 和
Walk-Forward 执行准入只对 LocalParquetProvider 调用资格断言。AKShare 缓存即使
没有资格包，仍能进入正式 Dataset 消费。修复前复用了现有离线夹具，实际接受
3900 行合成 Dataset，资格包数量为零。这个结果是软件反例，不是真实市场研究。

新 `data.admission.assert_formal_market_admission` 是共同边界。Provider 的
`get_research_qualification` 只交付候选证据，不交付授权。默认没有证据，必须拒绝；
名称、旧断言方法、verified/PASS/布尔值、正确 Schema 和文件 SHA 都不能授予资格。

证据包含固定清单 SHA、来源版本和资格包重放的完整股票/基准表。共同边界重新读取
源文件及表、调用现有资格引擎，核对研究范围、独立日历、有效 PIT、证券、精确价格、
基准和实际状态/上市输入。RAW/ADJUSTMENT/STATUS/PIT/SOURCE_BINDING/FORMAL
必须全部 PASS，issues 必须为空，synthetic_only 必须为 false；回测和 Forward
还要求 execution_admission。旧资格引擎的金融语义及未绑定来源角色保持不变。

资格收据绑定请求表摘要、成员摘要、时间范围、日历及来源版本。收据不能授权之后的
输入；即便调用者提供已固定的行情元组，Dataset 消费仍重新检查。

## 消费入口

- build-dataset：写特征、Dataset 或成功清单前检查，并绑定实际状态和上市数据。
- evaluate、walk-forward：Dataset 消费重新检查；Walk-Forward 另外要求执行资格。
- compare-models：不能以历史成功报告代替当前金融资格；重新检查当前 Dataset 身份。
- freeze-forward-model、forward-signal：沿共同 Dataset 边界检查，包括不刷新缓存的信号路径。
- evaluate-forward：实际收益标签的缓存覆盖检查后，另行验证金融资格及 PIT/状态。

PIT、生效语义、历史身份、复权、来源追溯、预注册、训练截止、时钟、Git 状态、
纸面 Forward 和发布锁等独立约束继续存在。激活元数据的登记本身不代表行情准入。

## 探索及合成软件测试

工程读取、独立 exploratory、DatasetBuilder 数学接口、WalkForwardRunner 以及
model_readiness 的合成计算仍可使用。它们不能签发正式资格。

四个既有 CLI 编排测试模块显式使用 `synthetic_cli_admission` 测试夹具。这是只存在于
tests 的边界替身，标记 SOFTWARE_ONLY、formal_admission=false、execution_admission=false，
并阻断网络；不伪造金融正向认证。原数值、时间、版本和失败断言保留。
`tests/market_admission` 不使用该替身，始终检验真实门禁。

目前没有真正合格的非 Local 金融证据，因此不添加虚假的金融准入正向样本。
新增反例覆盖无包、空包、不完整/错配/篡改包、重新封装 PASS、供应商名称、合成包、
输入绑定、已有缓存及模型/Forward 消费和拒绝后产物。Local 的工程可读与正式拒绝分开验证。

## 冻结验收与证据

历史 frozen-baseline、3144 项收集清单、平台跳过身份、Golden、14 因子、模型参数及
旧证据不重写。本次授权安全修复使用独立 security-revision.json，固定基线、精确路径、
Git 前后像和四个变动源码的可执行行清单。CI 固定该收据摘要；额外修改、扩展范围或
改写收据都必须失败，不自动将当前工作区认作新的可信基线。

原执行结果、失败传播、跳过原因和未修改源码覆盖清单的检查保持原样。新独立 CI 作业
运行实际金融拒绝反例、四模型合成就绪套件及市场结构兼容性；所有运行均只产生软件证据。

PIT 归档的校验器、清单和原断言不变。测试先验证当前安全修订的全部精确后像，再将
三个已授权变动文件的固定基线 Git 前像提供给历史文本校验；其他文件继续读取当前文本。
这同时区分历史归档完整性与当前代码完整性。未登记的当前变动仍拒绝，不将旧证据改写成
当前代码的证明。CI 显式获取资格基线及四模型原始源码固定 Git 对象，缺失对象必须失败。

覆盖率按源码目录收集，避免 coverage 对带有依赖导入的子模块预探测和清理造成 NumPy
扩展重复初始化。该修正不改变依赖版本、模型代码、测试断言或资格判定。

## 尚未解决的金融资格

真实完整 PIT、历史身份/ST/停复牌、单位、原始来源解释、独立 HFQ 及事件/锚点、历史
可知时点等证据仍不齐全。默认五年配置继续被 BaoStock PIT 生效语义门禁阻断；新的
统一行情门禁构成另一独立阻断。不得据本修复宣称 Alpha、五年实证或真实 Forward 已获准。
