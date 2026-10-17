# 中证500外部历史PIT数据接入前最小验收规范 v1

项目：`Wind-Maker1001/quant-tv`。日期：2026-10-18（Asia/Shanghai）。**NO LIVE MONEY**。

**本规范与测试方案已建立；真实PIT仍为 `PIT_UNVERIFIED / FORMAL_ADMISSION_BLOCKED`。** 本轮没有取得新的成员原件、生成成员数据或运行正式导入。2021-09-13完整基线、13888实际生效日期、完整历史调整链及合格历史身份仍未认证。规范中的字段名是本地接入设计名，不声称是Wind接口字段；Wind原生字段、接口及历史版本能力必须随交付另行验证。

适用范围是外部材料进入隔离证据区之前的验收设计。小样本合格只覆盖明确列出的文件、日期和事实，不能证明五年数据合格。研究窗口固定为2021-09-13至2026-09-11，每个研究交易日500个唯一指数成员；`live_trading:false`、Formal和Forward合同保持原样。

## 1. 已读取依据与验收边界

| 依据 | 本规范继承的约束 |
| --- | --- |
| [第一阶段PIT报告](PIT_PHASE1_EVIDENCE_2026-10-18.md)、[证据登记](evidence/pit-phase1-20261018-v1/evidence-register.json)、[候选事件](evidence/pit-phase1-20261018-v1/candidate-events.json) | 14条只是候选；实际成员生效日及当时可知时刻仍UNKNOWN；当前附件版本不能自动回溯 |
| [独立数据复核](../../INDEPENDENT_DATA_REVIEW_2026-10-17.md) | 价格可读不等于历史指数资格；本轮复用摘要，不重扫行情 |
| [PIT来源审计](PIT_SOURCE_AUDIT.md)、[五年PIT证据](FIVE_YEAR_PIT_EVIDENCE.md)、[官方缓存合同](OFFICIAL_SOURCE_ARCHIVE.md)、[条件事件](CONDITIONAL_EVENT_EVIDENCE.md) | 拒绝当前成分回填、含义不明的退出日及基金持仓替代；原件、工具表示与缓存收据分开 |
| [PIT代码](../../qbot/research/universe/csi500.py)、[身份代码](../../qbot/research/universe/identity.py) | 精确交易日快照或显式闭区间；唯一历史代码、稳定身份及知识时间 |
| [SourceArtifact](../../qbot/research/data/evidence.py)、[资格代码](../../qbot/research/data/market_qualification.py)、[本地正式入口](../../qbot/research/data/providers/local.py) | 字节重放、来源绑定、独立审查及正式入口复算；人工PASS不能替代代码拥有的解析合同 |
| [五年配置](../../configs/research/csi500_5y.yaml)、[Forward合同](../../qbot/research/forward/contract.py) | 独立冻结窗口、500要求、身份/状态/复权等并列门禁及Forward独立时序约束 |

采用三种处理结果：`RETAIN_AS_EVIDENCE_ONLY`（可留存但不合格）、`REJECT_FOR_ADMISSION`（拒绝准入并列出具体缺口）、`EVIDENCE_ACCEPTED_FOR_DECLARED_SCOPE`（仅指定证据范围通过）。这些是**拟议验收用语**，不是仓库既有资格状态或正式通行标志。任何必需事实UNKNOWN、冲突未解决或检查未执行，均不得给第三种结果。

当前真实来源的 `_unbound_real_roles()` 仍列出PIT、IDENTITY、STATUS、CALENDAR、UNITS、ADJUSTMENT、REFERENCE、BENCHMARK、TURNOVER、LISTINGS、ANCHOR等角色；RAW是否绑定另行判断。即使本规范全部小样通过，当前实现仍不存在完整真实准入路径。不得删除这些阻断角色、手写 `formal_admission=true`、提交手工COMPLETE声明或以synthetic结果放行。

## 2. 外部交付的最小结构

每批交付使用新的不可变目录，分为原件、采集收据、原生字典/版本、事实登记、规范投影及检查结果。以下是设计结构，本轮不创建成员投影文件。原件按字节留存，不改列名、不改编码、不覆盖旧版本；CSV/Excel的前导零、空值、公式及原生代码均保留。解析后的文本或表格另存并绑定父原件哈希。

官方路线：中证指数发布者原文件及发布记录、日期语义、完整性和版本链。供应商路线：如Wind的授权原生导出/响应、可重放请求参数与完整响应、原生字典、历史版本/修订记录及可核验上游血缘。**来源品牌、付费、查询参数写了历史日期，均不单独证明历史PIT。** 不要求伪造官方文件没有的供应商ID；允许可证明的NOT_APPLICABLE，但其他必需事实不能因此豁免。

### 2.1 工件与原生版本字段

| 设计字段 | 类型与最低要求 | 原生字段保留/拒绝条件 |
| --- | --- | --- |
| `package_id, schema_version, source_namespace` | 非空字符串；命名空间区分发布者、Wind产品及其他供应商 | 本地批次版本不得冒充供应商版本 |
| `source_id, publisher, upstream_origin` | 明确原作者、交付方与事实血缘 | 域名托管方不必等于作者；来源不明拒绝 |
| `source_url, locator` | 已观察到的原始URL/授权导出定位及接口操作标识 | 非公开交付可记录NOT_APPLICABLE及原因，但必须有可审计导出定位；不公开凭证 |
| `request_artifact_ref, response_artifact_ref` | 请求参数/字段选择/日期/版本/筛选/分页及响应工件引用 | 官方静态文件请求项可有依据地NOT_APPLICABLE；API分页缺页、截断或失败响应拒绝 |
| `path, sha256, bytes, acquired_at` | 本地原件路径、64位小写SHA-256、字节数、带时区实际获取时间 | 哈希和字节数必须重算匹配；采集收据也单独绑定；不得改写旧获取时间 |
| `representation_kind, parent_artifact_sha256` | ORIGINAL_BYTES、BROWSER_CONTAINER、RESPONSE_TEXT、DERIVED_TABLE等；派生项必须有父引用 | 容器/文本哈希不能冒充原响应哈希；缺原件只能保留线索 |
| `native_fields, native_values, native_row_locator` | 原始列名、值、类型及行/页/单元格/响应记录坐标 | 与规范字段并存；不得用新代码覆盖原生历史值 |
| `native_schema_version, field_dictionary_ref` | 交付时原生字段字典及版本原件引用，含日期、状态、交易所、ID含义 | 不猜Wind字段名；无原生版本号时保留UNKNOWN，须有可验证的原生schema快照及其哈希版本替代依据，否则拒绝 |
| `native_dataset_version, native_record_revision, supersedes_ref` | 数据原生版本、逐条修订、被替代版本引用/完整更正链 | 官方无版本号时保留原值UNKNOWN，以有证据的发布记录+原件哈希标识该版本；哈希只能区分字节，不能证明历史可得性。首版/无修订须有依据，不用默认值冒充 |
| `provider_updated_at, native_generated_at` | 供应商更新时间、文件生成时间分别存储；记录精度和证据 | 无此原生字段时可UNKNOWN；不得代替发布日期、实际生效或known_at |
| `usage_evidence_ref` | 此次本地研究、原件留存和审查引用的使用范围依据 | 沿用已有授权审查要求；本轮不采购或联系第三方 |
| `adapter_version, parser_implementation_sha256, transformation_log_ref` | 后续实现时记录适配器、实现字节及每步字段/值转换 | 本轮仅设计；没有适配器不能宣称已实现来源绑定 |

### 2.2 每个事实的证据字段

所有成员状态、事件动作、日期和身份关系均按事实绑定，而非只给整表一个“可信”标签。

| 设计字段 | 要求 |
| --- | --- |
| `fact_id, subject_id, field_name, value, value_status` | 稳定事实键、对象、字段和值；状态为VERIFIED/UNKNOWN/CONFLICT/NOT_APPLICABLE，NOT_APPLICABLE需明确理由 |
| `evidence_refs[]` | 每项含原件SHA、原生字段/单元格/页码坐标、必要原文及解析/视觉核验定位；不能只指向搜索结果 |
| `validation_basis, reviewer, reviewed_at` | 说明验证的是“文件陈述”“实际实施”“版本历史”还是“当时可得”，以及审查者和本次审查时刻 |
| `confidence_by_dimension` | 分开记录字节一致、作者/血缘、语义、实际实施、历史版本与可知时间的置信度及理由；HIGH不得覆盖UNKNOWN |
| `conflict_refs, resolution_ref` | 所有冲突版本和解决依据；未解决冲突拒绝；不以“最新覆盖旧版”消除历史 |

必需字段缺失时，在隔离事实登记中保持 `value=UNKNOWN, value_status=UNKNOWN`；不得把字符串UNKNOWN、空字符串、0、默认日期或当前时间投影到正式合同。可选的供应商更新时间未知不自动否定已有独立历史时间证据；成员、实际日期、必需身份或历史可得性未知则拒绝。

### 2.3 成员快照、事件和身份字段

| 记录 | 必需设计字段 | 规则 |
| --- | --- | --- |
| 快照头 | `snapshot_id, index_id_raw, index_id_canonical, membership_effective_date, effective_phase, timezone, source_version_ref, completeness_evidence_ref, reported_member_count` | 000905/中证500的原生与规范别名须有字典依据；快照日期明确对应哪一交易时段；数量及完整性须来自原件/交付说明 |
| 快照成员 | `snapshot_id, native_member_key, native_security_code, native_exchange, historical_symbol, security_id, membership_status_raw, membership_status_canonical, fact_refs` | 保留供应商标识/原名（有则逐字保留）；500个ACTIVE指数成员、500个唯一历史symbol和500个唯一稳定身份；不因名称相同合并 |
| 区间（若交付） | `historical_symbol, entry_date, exit_date, endpoint_semantics, fact_refs` | 原生端点及开闭区间原样保留；仅在端点有效交易日和转换语义均已证实时投影到显式首尾包含区间。无法证明退出边界则不投影 |
| 调整事件 | `event_id_raw, index_id, action, affected_security_id, historical_symbol, announcement_ref, action_ref, time_fact_refs, condition_ref, cancellation_revision_refs, coverage_scope` | ADD/REMOVE/RESERVE分开；条件、撤销、改期及补充公告必须单独核验；14条候选不是完整历史目录 |
| 历史身份 | `supplier_namespace, supplier_security_id_raw, stable_id_namespace, security_id, historical_symbol, start, end, listing_date, delisting_date, relationship, security_type, available_at, fact_refs` | 无原生稳定ID时保留UNKNOWN，可由独立身份材料证明的受治理本地ID替代，但须明确命名空间与分配依据；不得冒充ISIN或交易所ID |
| 供应商别名边 | `supplier_namespace, supplier_security_id_raw, security_id, alias_start, alias_end, alias_time_semantics, version_ref, fact_refs` | 别名适用时间与交易所代码时间是两回事；供应商将新代码回溯作内部标识，须有明确历史别名合同，不修改原文件 |

`delisting_date`仅当证券确有退市且与区间相关时必填；未退市须有对应状态依据，可按既有合同投影为空字符串。身份的start/end/listing_date/available_at/security_type不能UNKNOWN。当前缺完整历史端点时，先保留转换事件；不得为了填满 `IdentitySnapshot` 凭日历生成端点。有限范围身份区间也须明确为经证实的覆盖区间，而非伪称证券全生命周期。

## 3. 五类时间及版本必须分开

每个时间事实同时记录原值、时区、精度（DATE/TIMESTAMP/SESSION_PHASE）、语义、证据引用及状态。时间戳须有时区；日期保留YYYY-MM-DD，不能伪装成已知的00:00时刻。

| 时间 | 设计字段 | 禁止替代 |
| --- | --- | --- |
| 公告首次发布 | `announcement_publish_date, announcement_publish_time` | 落款、URL目录日、HTTP Last-Modified或供应商抓取日不能替代首次公开 |
| 计划实施 | `planned_implementation_date, planned_phase, planned_condition` | “周五收盘后”“自上市日起”只能是计划/条件，不能直接写实际成员日 |
| 实际生效 | `actual_effective_member_date, actual_effective_phase, actual_effective_at` | 必须有已实施证据及交易时段语义；精确时刻不详可UNKNOWN，前提是已证实日级实际边界足以支持所验收的日级用途；盘中边界不明则拒绝日级投影 |
| 历史可知 | `historical_known_at, known_at_precision, known_to, historical_vintage_ref` | 绑定**这个版本、这个事实**当时对公开市场或所声明授权用户可得的时间；公告公开不代表其后来附件版本同时公开 |
| 实际获取 | `acquired_at` | 本机2026年下载可与有证据的2021年版本共存；获取时间不能回填为历史known_at，也不能单独认证历史版本 |

原生生成、供应商入库、供应商修订、本轮审查时间另列，不合并到上述五类。更正后发现的事实保留其新知识时间，不能用后来的正确值覆盖早期信号时可见版本。已有历史known_at不得因本轮复查而改写。

若有独立证据仅能证明**同一事实及版本**在某个日期已可得，可保留该日期和DATE精度，沿用 `evidence.timestamp()` 的上海该日终了上界；这是保守比较规则，不是补出的精确发布时间。只允许在此上界不晚于原合同 `signal_as_of` 的范围内使用，日内更早信号拒绝。该规则不使13888后来附件的历史可得性变为已知。身份 `available_at` 须覆盖其所有必需事实的已证实知识上界；任何依赖UNKNOWN则不能生成。

实际有效日期与历史known_at不要求大小关系固定：计划可以事前公开，实施确认也可能事后取得。若确认仅在事后可得，只能作事后核验材料；不能自动成为早期信号的PIT输入。

## 4. 2021-09-13完整基线验收

以下B01—B08必须全部通过。通过只证明该日该时段基线，不证明后续五年链条。

| 检查 | 最低可接受证据与断言 | 拒绝条件 |
| --- | --- | --- |
| B01 原件与版本 | 发布者原件或有可核验血缘的授权历史交付；原字节/收据/字典及历史版本绑定完整 | 只有搜索摘要、截图节选、当前名单、合成表或无法重放的查询结果 |
| B02 指数与时段 | 明确000905中证500、2021-09-13开盘/该日有效成员及时区；供应商“日期”含义有原件定义 | 只有“2021-09-13”标签，无法判断观察日、次日有效或生成日 |
| B03 完整性 | 完整文件/分页收齐，源声明数量与解析ACTIVE数量相符；恰好500个唯一symbol和稳定身份 | 499、501、重复、截断、缺页；原件原样留存，不能补一只或删重复凑500 |
| B04 身份 | 每行证券类型、市场、稳定身份及当日历史代码均有唯一证据映射；无歧义/碰撞 | 当前代码覆盖旧代码；未上市证券填入；同一身份重复计数 |
| B05 指数资格与状态 | 正式成员、备选、待纳入、停牌/ST、过渡条目语义明确 | 用ETF持仓/PCF替代；删除停牌/ST后再补股票；无法分类的占位条目 |
| B06 历史知识 | 快照版本和必需身份事实的known_at已证实且满足相应信号边界；修订可追溯 | 本次导出时间、发布日期或字段名“PIT”代替历史版本证据 |
| B07 起点特殊边界 | 官方/合格供应商材料明确13716及13420对起点的实际处理，并与基线集合对照 | 13716一调入一调出被当作全表；从中国能建后来上市倒推起点；499补601868 |
| B08 日历与投影 | 独立日历证明目标日，逐行原件→规范行可重放；严格date-only和SH/SZ代码 | 通过宽松日期归一化掩盖盘中/时区问题；以成员数据自身定义日历 |

500是指数成员总数，先于研究中ST、停牌、上市天数等可交易筛选；不要求筛选后交易股票池仍有500只。成员原件若有停牌公司必须保留其指数资格；独立状态合同仍须后续满足。状态UNKNOWN不能被解释成正常交易。

起点最小材料包：2021-09-13目标有效名单原件；2021-09-10处理前后及起点过渡说明；13716实际处理与13420相关过渡条目证明；同版本历史字典/身份/知识时间和完整性证明。若直接权威基线已完整明确覆盖相关过渡处理，可引用该证据，不重复开发重建器。不存在合格基线时停止正式投影；不得把后续调样反推成已认证起点。

## 5. 13888集合差验收案例

当前证据只支持：正文所载发布日期2021-11-26、计划2021-12-10收盘后调整，当前附件有50 ADD、50 REMOVE及25个应排除的备选。**实际成员生效日期、历史known_at和当时附件版本仍UNKNOWN。** 不把2021-12-13计算成已验证实际日。

原附件：[中证指数调入调出名单.xlsx](https://oss-ch.csindex.com.cn/notice/20211130195824-中证指数调入调出名单.xlsx)，SHA-256 `f6b9d596f3fa6072258aa1eb2c036517bf20cc74c7879eaad1069cb8e1747909`；ADD坐标`调入!A1034:D1083`，REMOVE坐标`调出!A838:D887`。附件元数据createAt=2021-11-30，Last-Modified=2024-11-30，均不能证明2021-11-26已有这些字节。正文浏览器容器、response.text及原响应缺失状态见[候选证据](evidence/pit-phase1-20261018-v1/candidate-events.json)，不得互换哈希。

下一次只索取该边界前后完整名单、实施/修订链及时间语义。2021-12-10处理前后和2021-12-13开盘是**请求核验的候选快照**；其日期标签不能代替实施证据。定义：

- `B0`：已证实实际边界之前的完整500成员集合。
- `B1`：已证实实际边界之后的完整500成员集合，来自另一个原生有效快照，不能由本地套用ADD/REMOVE生成。
- `A/R`：经原件、身份、版本和实际实施核验的13888调入/调出集合。现在只有候选A/R。

先确认边界间没有另一个调整/更正/条件事件；名称变化与代码变化通过合格稳定身份对齐，不能当作指数调样。对稳定身份集合检查，历史symbol另按各自日期核对：

```text
|B0| = |B1| = 500
|A| = |R| = 50; A ∩ R = ∅
R ⊆ B0; A ∩ B0 = ∅
B0 \ B1 = R; B1 \ B0 = A
B1 = (B0 \ R) ∪ A; |B0 ∩ B1| = 450
```

所有等式须比较实际集合，不能只检查计数。输出未解释的额外调入、额外调出、遗漏动作和身份歧义列表，并绑定原始行坐标。若另有已证实事件，应索取中间快照隔离13888，或另设有完整顺序证据的组合案例；本案例先拒绝，不能删除差异以凑50/50。不能把工作表同行理解成经济上的逐一替换关系。

周五交易时段与周五收盘后是两个时段。若资料只能证明计划收盘后实施，不能把新成员放入周五盘中，也不能自动平移到下一交易日。没有边界证据、独立B0/B1或历史版本，则集合差用例状态为NOT_RUN，正式准入拒绝。本轮未取得B0/B1，未计算真实前后差，也未构造虚假500名单。

## 6. 300114/302132小样本验收

采用供应商原始标识→稳定身份→当日交易所代码三层边，指数成员资格另接证据。沿用[既有映射草案](evidence/pit-phase1-20261018-v1/identity-mapping-proposal.json)。原交付将302132用于早期历史的观察仅复用旧摘要，不读取行情。

现有发行人2025-028与后来中信证券督导材料一致支持“自2025-02-17开市由300114变为302132”的来源陈述。完整身份主表、交易所实际操作时点、旧区间端点、上市日和历史available_at仍未资格化；后来的督导意见不能回填2025年的知识时间。两原件SHA分别为 `dd68049c48df826848f361fd9e7b23dd20b6805144a2e5bc36e54db638611488`、`9234be47b07dcfa6e4ef070f099d6b19ce927864897bd6e827eca31830dd6779`，位置及URL见第一阶段登记。

| 小样本 | 待取得材料及断言 | 目前处理 |
| --- | --- | --- |
| I01 变更前有效时段 | 取2025-02-14候选样本的交易所历史主表/源快照及独立日历，核验当日300114.SZ、证券类型、稳定身份、上市日和known_at | 候选采样日，不据此生成旧区间末日；缺证拒绝 |
| I02 变更时段 | 取2025-02-17开市生效记录及当日主表，核验302132.SZ与已证实的同一上市证券关系 | 已有来源陈述/事后齐证；完整IdentitySnapshot仍拒绝 |
| I03 变更后有效时段 | 取2025-02-18候选样本及该日历史版本，检查稳定身份连续、旧代码不再有效且无重叠 | 候选日期须经独立日历验证，未取证不运行 |
| I04 供应商回溯别名 | 仅索取一条2021-09-13候选映射样本的原生标识/记录定位、供应商历史别名定义及对应主表 | 可以保留供应商原值302132，不能把它认成当年的交易所代码；别名证据缺失拒绝 |
| I05 不可知/冲突 | 同一身份同时映射两代码、同一代码映射两身份、2026材料作为2025 available_at、前日由日历补出 | 全部拒绝，不修原始数据 |

样本仅主表/别名/元数据记录，无须价格行。I01—I03只有取得各自证据才有预期代码；日期选择不等于认证，不能从三个点推定整段连续覆盖。身份关系须证明为SAME_SECURITY；吸收合并、重新上市或不同证券份额不按名称/主体相同自动合并。不得将`LOCAL-PROPOSED-AVIC-LISTING-001`冒充已认证ID，也不得自动拼接000780/001289或600068/601868。

## 7. 与现有合同的字段映射

富证据记录与窄表投影分开保存，不能将供应商字段直接塞入现有导入CSV；原始字段和版本留在旁证工件中。下表是下一阶段设计映射，尚未实现适配器。

| 本规范字段/工件 | 现有合同 | 转换与限制 |
| --- | --- | --- |
| 原件`path,sha256,bytes,source_id,acquired_at,locator` | `data.evidence.SourceArtifact`同名6字段 | `read()`重算字节与长度；不证明作者、事实正确或历史时间。勿与`universe.official_sources.SourceArtifact`混用 |
| 明确有效日、历史symbol、ACTIVE状态 | daily `date,symbol,is_member` | 日期只传YYYY-MM-DD，is_member显式True；源状态映射必须有证据。当前函数缺is_member可默认True，本规范不依赖这个默认值 |
| 已证明的首末有效交易日 | interval `symbol,entry_date,exit_date`，可选`is_member,interval` | 首尾包含；不能直接接`opt-in/opt-out`或无穷终点；混合布局/未知列拒绝 |
| 原生版本、富元数据 | 导入manifest的`source_file_sha256,daily_sha256,intervals_sha256,source_version`及外部旁证 | 原件→解析→规范投影逐层哈希。现有local-import source_file只绑定投影文件，**不自动绑定上游供应商原件**；`user-pit-import-v2`不是供应商版本 |
| `security_id,historical_symbol,start,end,listing_date,available_at,source_sha256,delisting_date,relationship,security_type` | `SecurityIdentity`对应字段，其中historical_symbol→`symbol` | `relationship=SAME_SECURITY`，`security_type=A_SHARE`，源SHA在artifacts中；区间首尾包含，symbol或security_id不得重叠 |
| 身份区间及全部原件 | `IdentitySnapshot(intervals,artifacts,synthetic_only)` | 真证据不得标synthetic冒充通过；resolve对每个date/symbol须唯一，且available_at不晚于signal_as_of；别名边不等同该合同，不改写原始行情 |
| 合格成员、日历、原始来源 | `QualificationInputs.membership,pit_source,calendar_reference,calendar_source,benchmark_source` | 完整研究窗口由独立`research_start/end`规定；日历与benchmark精确一致，不能从已有成员裁剪窗口；pit_source单一引用须有可重放多原件血缘，不能只是自写汇总 |
| 原生交付/适配器版本 | `QualificationInputs.source_version`及旁证manifest | 各版本独立命名并绑定，不能一个本地字符串抹掉供应商修订 |
| 五类时间、完整性、原件血缘审查 | `source_reviews: Tuple[SourceArtifact,...]` | 见下方精确审查schema；很多时间/版本字段在窄表中无原生位置，必须保留旁证并由将来的代码解析合同验证 |
| 本规范证据范围结果 | **无自动映射到**`QualificationReport.formal_admission/execution_admission` | 只能走原资格复算和本地正式入口；SOURCE_BINDING阻断保持不动；Forward仍独立验收 |

现有独立审查JSON必须使用schema `FACTORLAB_INDEPENDENT_SOURCE_REVIEW_V1`，且字段**恰好**为：

```text
schema, role, reviewer, reviewed_at, bound_sha256, upstream_origin,
time_basis, coverage_basis, effective_date_basis, history_kind, scope_start, scope_end
```

`history_kind`须为CONTEMPORANEOUS；相关角色原件SHA须全部覆盖；reviewed_at不能晚于该审查工件acquired_at；范围需覆盖实际资格价格范围（包含所声称的预热行）。PIT、IDENTITY小样本审查不足以满足RAW、CALENDAR、STATUS、UNITS、ADJUSTMENT、REFERENCE、BENCHMARK等其余审查角色。不能加入本规范富字段破坏该schema；额外说明另存绑定。该JSON不认证审查者或时间真伪，也不消除未完成的SOURCE_BINDING解析合同。

现有 `validate_daily_membership` 会归一化日期/代码并可默认成员标志；严格导入入口另用 `strict_import_date`。后续适配器须在归一化之前验原生语义，保留转换日志并使用严格入口的日期规则。不能把宽松函数的成功当作原始日期已认证。

## 8. 最小样本检查与失败用例

完整执行顺序、必需材料、预期通过范围与拒绝场景见[验收测试方案](EXTERNAL_PIT_ACCEPTANCE_TEST_PLAN_2026-10-18.md)。本轮只核对规范与当前合同/候选证据的一致性；用例设计不记为真实样本已通过。

必须包括：完整500但无历史版本、499名单补股票、重复身份凑500、缺实际日期、用公告日/计划日代替实际、附件晚于公告、套用动作自造B1、只对计数不对集合、额外临时调整、备选混入、同日收盘后错投到盘中、当前代码倒灌、身份端点/available_at未知、手工来源绑定PASS，以及小样本外推全五年。任何必需字段缺失均拒绝正式准入，不能先导入后补证。

## 9. 下一阶段最小实施顺序

| 优先级 | 最小工作 | 停止/完成条件 |
| --- | --- | --- |
| P0-1 | 先获取一个2021-09-13权威完整名单与字段/时段/版本/起点过渡证据 | B01—B08全通过才认定该时段基线；缺项原样留存并拒绝，不扩大无关下载 |
| P0-2 | 获取13888独立前后快照、实际实施与修订链；复用现有缓存和公告解析器 | 实际边界及版本已证实，再运行完整集合差；否则NOT_RUN，不自动平移日期 |
| P0-3 | 取得300114/302132三个边界样本及一条供应商别名样本所需主表/知识时间 | 每条事实唯一绑定，不能从小样本制造全生命周期或全部PIT |
| P1-1 | 在独立实现轮次增加最小外部隔离适配器：原件→原生字典→事实/版本→严格窄表，输出逐条拒绝收据 | 复用`archive_bytes/SourceArtifact`、`OfficialNoticeSource(cache_only=True)`、`read_browser_notice`及`review_csi500_notice/workbook_values/pdf_pages`；13888分块布局沿用第一阶段已核验坐标；不重写通用抓取/解析框架 |
| P1-2 | 将测试方案落成隔离夹具与负例回归，先小样；再独立审查代码拥有的原件解析/绑定合同 | 本轮不实现、不解除任何角色；将来证明特定角色绑定也不代表其他角色通过 |
| P2 | 样本证据成立后再取覆盖全窗口的完整历史目录、临时/条件/紧急/更正链和逐日成员材料 | 不能默认14条完整；每日500/身份/时间/日历均须成立，再经现有资格与正式入口复算 |

状态、上市、单位、公司行为、复权、参考价格、基准及其来源绑定继续独立补证；本规范不改变模型、因子、研究窗口或Forward。索取材料只形成最小需求，本轮没有向外发送消息或执行采购。

## 10. 本轮可复现交付检查

新增工件位于[evidence/external-pit-acceptance-20261018-v1/](evidence/external-pit-acceptance-20261018-v1/)。`preservation-before.json`绑定写入前580份既有研究代码、测试、配置、文档及审计报告；`delivery-manifest.json`绑定新增规范/测试方案/检查器和复核输入；`verification.json`记录本轮检查结果。收据自身只证明可复现一致性，不是金融数据认证。

```powershell
.venv-py39\python.exe -B -X utf8 docs/research/evidence/external-pit-acceptance-20261018-v1/verify_spec.py
```

检查器只读：核对上述文件哈希、合同字段与仍阻断的来源角色、13888候选动作及UNKNOWN、旧证据引用绑定和git tracked差异；不联网、不解析行情记录、不导入研究流水线，不生成成员或正式资格。保全哈希包括既有52,416字节试点DAY及小型测试夹具，仅比较字节，不重放行情审计或扫描历史价格目录。检查成功不等于基线、实际日期或身份已获证。测试方案中的未来用例未执行项保持NOT_RUN。
