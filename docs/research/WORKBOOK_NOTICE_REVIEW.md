# 临时调样工作簿的严格离线复核

## 本轮结论

2026-10-11（下列运行 ID 使用 UTC）真实取得3份已缓存公告明确链接的原 XLSX。
所有工作表通过 bundled artifact runtime 只读导入，原附件没有修改、重算或重导出。
其中两份已观察到的表格没有中证500条目；第三份有2条候选调整事件：

| 公告 ID / 正文出版日 | 工作表 | 数据行数 / 唯一指数代码数 | 本次已观察到的中证500内容 |
| --- | --- | --- | --- |
| 15546 / 2025-02-06 | Sheet1 | 175 / 165 | 无 `000905` 条目 |
| 1006022 / 2025-07-25 | Sheet1 | 173 / 173 | 无 `000905` 条目 |
| 3006227 / 2026-09-09 | 指数样本调整名单 | 166 / 166 | 第43行：调出601198.SH东兴证券，调入603083.SH剑桥科技 |

3份正文均没有“中证500”关键词。**正文未提中证500不等于附件没有相关调整**，
本次第三份附件已经提供了具体反例。原来源覆盖审计的15份正文关键词命中数，
不能解释成全部相关公告数。两份阴性结果只适用于本次读取的支持布局和当前附件，
不覆盖其他公告、历史附件版本或尚未取得的正文。

3006227 原正文规定“自东兴证券、信达证券退市日起”。这不是明确的交易日期，
解析结果为 `EFFECTIVE_DATE_REVIEW_REQUIRED`，没有按出版日或下载日执行变更。
原表 `E43:F43`、`I43:J43` 均为 `-,-`，表示额外空槽，不是未知股票的代填入口。
两个有效槽分别为 `C43:D43`（调出）和 `G43:H43`（调入）。

更重要的是，3006227 当前链接文件名为20261009131635，HTTP Last-Modified为
2026-10-09，晚于正文出版日和研究截止日2026-09-11。当前字节**不能证明**它们
在2026-09-09可获得，也不能直接用于该日的历史股票池或 Forward 证据。
因此本轮没有正式日级成员、dataset、横截面 RankIC 或真实 Forward 信号。
完整起点500成员、完整临时链、过渡期成员语义和逐日证券状态仍需补齐。

## 原始附件与日期语义

全部 URL 都来自已核验缓存正文的实际 metadata/href，不由文件名猜测：

- [15546 原附件](https://oss-ch.csindex.com.cn/notice/20250206175421-指数样本调整名单.xlsx)
- [1006022 原附件](https://oss-ch.csindex.com.cn/notice/20250722164043-指数样本调整名单.xlsx)
- [3006227 当前原附件](https://oss-ch.csindex.com.cn/notice/20261009131635-附件：指数样本调整名单.xlsx)

| 公告 ID | 原 XLSX SHA-256 | 字节数 | HTTP Last-Modified (UTC) |
| --- | --- | ---: | --- |
| 15546 | `e7b797f2b203dc8d9bdc93605b4b5def237785980230b0dc3895cb1abf3bb3c1` | 17548 | 2025-02-06 09:54:21 |
| 1006022 | `03219d87e44f9c9e7038e4741d4c22341c7037db70a9d51913e5f9f74dc9a9a5` | 18734 | 2025-07-22 08:40:43 |
| 3006227 | `8242a05e9e8b03e13cec867a3b9ea0ac77e7345d4ebd151d2cbc1f06adfd0933` | 18595 | 2026-10-09 05:16:35 |

1006022 文件名及修改日为7月22日，正文出版日为7月25日；不把它们合并成一种日期。
出版日、条件生效条款、附件修改日、抓取日分别保留。SHA证明本次具体字节身份，
不证明历史可得性、附件未曾修订或外部可信时间戳。

原缓存目录为 `data/research/diagnostics/official-temporary-attachments/20261011-three-generic/`。
只读提取 JSON 为 `data/research/diagnostics/official-temporary-inspection/20261011-three-generic/`。
实际使用的原只读导入脚本 SHA：
`50a82f001659b75453a8b5c94bb66f82041b50ae1c54f43c678588cada6b5cb4`。

## 新增接口与边界

`qbot/research/universe/notice_workbook.py` 是纯 Python 解释器，只接收已提取的
typed worksheet values，不导入 Excel SDK、不联网、不发布 universe。
合同 `csindex-csi500-paired-typed-values-v1` 仅支持实际观察到的6列和10列配对表：

- 两行表头必须逐格确认指数代码/简称、左调出右调入、证券代码/简称；
- 所有传入工作表都要检查，未知工作表、未知方向、未知行或空白指数代码报错；
- 指数代码必须保留六字符文本，目标只允许 `000905` 与 `中证500` 同时匹配；
- 不把其他“500”或中证500子指数当作目标，不补前导零或跨合并单元格填值；
- 目标证券标识保留六位ASCII数字；只允许显式 `-,-` 空槽，部分缺失/未解析代码报错；
- 目标调整代码重复、调入调出重叠、已声明数量不符或内嵌正文表不一致报错；
- 未声明数量时不伪造声明数量，未声明日期时不补日期；
- 保留 worksheet、一基行号及精确 security-slot range。

纯解析器不能证明调用者传入所有工作表或所有单元格；这个限制明确写入输出。
独立离线入口另核对原 XLSX 的 OOXML sheet inventory 与提取列表，绑定原文件、
提取脚本和 JSON 哈希，拒绝遗漏工作表、文件/脚本身份冲突及缓存损坏。
它没有第二套单元格提取器，不能把 sheet inventory 检查夸大成全部单元格独立复核。
原脚本的真实全表导入、人工表头/目标行检查和解析器回归是分别记录的证据。

## 实际执行的命令

```text
.venv-py39\python.exe -X utf8 -m examples.research.download_cached_notice_attachments --source-archive data/research/diagnostics/official-notices/20261010-csi-rebalance --attachment-root data/research/diagnostics/official-temporary-attachments/20261011-three-generic --notice-ids 15546 1006022 3006227 --timeout-seconds 10 --max-retries 0

.venv-py39\python.exe -X utf8 -m examples.research.review_cached_workbook_notices --source-archive data/research/diagnostics/official-notices/20261010-csi-rebalance --attachment-root data/research/diagnostics/official-temporary-attachments/20261011-three-generic --inspection-directory data/research/diagnostics/official-temporary-inspection/20261011-three-generic --inspector-script data/research/diagnostics/workbook-inspector/inspect.mjs --notice-ids 15546 1006022 3006227

.venv-py39\python.exe -m pytest -q --tb=short tests/research/test_notice_workbook.py tests/research/test_workbook_notice_example.py tests/research/test_cached_notice_attachments.py tests/research/test_official_sources.py --junitxml=results/runs/workbook-source-pipeline-20261011.xml
```

两个 Python 命令之间实际用 bundled Node 执行既有 `inspect.mjs`，逐份原附件导入全部
工作表并保存 `<notice_id>.inspection.json`。此步骤只读，不安装项目 Node 依赖，
不修改原文件。离线复核没有自动启动 Node 或未知提取脚本。

下载 run `20261010T165045.153256Z-download-cached-notice-attachments-78d053e4` success：
0正文HTTP、3附件HTTP、3正文缓存读取、3附件成功、0失败。全部正文先在缓存验证，
缺失不联网回退；服务器拒绝后不改身份继续请求。没有重开被403拒绝的正文流程。

复核 run `20261010T170654.786522Z-review-cached-workbook-notices-9208d9ff` success：
0 HTTP、6缓存读取、3工作簿、2候选事件、0失败。运行发生在 dirty 工作区，该事实
如实写入 manifest；原收据不改成 clean。每个新 run 独占输出，旧 run 不覆盖。
其 manifest SHA 为 `28bb1b82735231e0cfdb17cf7cddf3a593acc2761456db5159923609092ba4c6`。
`review.json` SHA 为 `4f71bdb3ef35d58511d1e59dfcc6fd6018f0c37991f208b33bf86f5cd078e054`；
`candidate_changes.csv` SHA 为 `48e08b328443bdc8359fb001c62bc11d470326adf7a7135233eabe5abdb592b5`。

定向回归实际151 passed，16.64秒；前一批127 passed，9.37秒。测试使用明确标记的
人工 HTTP/ZIP/cell fixtures，验证身份、日期条款、布局、空槽、缺失/损坏拒绝、
缓存离线行为、原始字节不变、重跑版本和结果哈希；人工数据不是历史成员证据。
完整回归见下文；提交后的缓存复跑另生成新清单，不修改这里记录的 dirty run。

## 起点检索与后续工作

此前6次限定公开检索的 MCP 原返回已保存为
`data/research/diagnostics/pit-baseline-discovery/20261011-bounded-search/search-responses.json`，
SHA为 `c19df963b532f3d09784e5905ad30cb9333f698fd62b5a32b649e24b16864b51`。
它们是搜索响应/摘要，不是原出版物字节；出现其他500指数、基金持仓和日期窗口外
资料，未取得合格完整起点名单。记录归档时间不冒充查询时刻，不宣称所有公开源无数据。

随后又执行2次交易所域名限定检索，并读取1份交易所披露的解析文本：
[东兴证券连续停牌提示公告](http://big5.sse.com.cn/site/cht/www.sse.com.cn/disclosure/listedinfo/announcement/c/new/2026-09-08/601198_20260908_RADI.pdf)。
该文签署日为2026-09-07、URL目录日为2026-09-08；披露计划最后交易日为9月14日，
9月15日开始连续停牌直至终止上市。它进一步说明不能把9月9日指数公告的出版日
当成退市日或替换日。停牌日不等于退市日，计划也不等于最终决定；本轮没有取到
该 PDF 原字节或最终退市决定，不据解析文本发布任何成员日期。

限定检索和解析文本返回分别保存在
`data/research/diagnostics/temporary-delisting-discovery/20261011-bounded/` 的
`search-responses.json`（SHA `2319af84c6fc631859ad05aa084051ec897bd0b9c85fba3842c3c3ed0afb0233`）和
`sse-disclosure-parsed-response.json`（SHA `9ea2fe0e280ec4ce383e000c22ee63471a5cff053b8e630ed40f641fcb5c81b6`）。
这些是 MCP 搜索摘要/已解析正文，不冒充本机获取的原 PDF 或当时的不可变快照。

下一步仍为独立验证完整成员基线、完整临时链及条件生效日期，而非直接累计事件数
形成500只股票池。尚未取得的168份正文不作无调整推断；正文403边界继续保持。
只有来源、逐日成员语义、状态和行情全链满足要求，才进入正式因子评价与五年实验。

## 本轮工程验收

Changed files 为本复核文档及 DATA、GETTING_STARTED、OFFICIAL_SOURCE_ARCHIVE 链接，
两个 example 入口、一个纯解析模块和三份测试文件；没有改 Legacy、LICENSE 或
原始数据消费门禁，没有新增核心依赖。LICENSE Git blob仍与官方基线相同：
`9fb99866c50772b1afadab1657cc45cc72cdc2d4`。

```text
.venv-py39\python.exe -m pytest -q --tb=short --junitxml=results/runs/workbook-review-full-20261011.xml
# 2135 passed, 2 deselected, 13 warnings in 473.47s

.venv-py39\python.exe -m qbot.research.cli audit --config configs/research/csi500_smoke.yaml
# exit 0；20261010T171140.639964Z-audit-5d7e1048

.venv-py39\python.exe -m qbot.research.cli build-dataset --config configs/research/csi500_5y.yaml
# exit 1；20261010T171143.172140Z-build-dataset-f58fd323
# POINT-IN-TIME UNIVERSE REQUIRED: EFFECTIVE MEMBERSHIP SEMANTICS UNVERIFIED

.venv-py39\python.exe -m py_compile qbot/research/universe/notice_workbook.py examples/research/review_cached_workbook_notices.py
.venv-py39\python.exe -m pip check
git diff --check
# 均通过；pip check: No broken requirements found
```

默认 deselected 为两项 network 用例，不计入通过数；本轮真实网络验收是3份附件
的实际下载，不把 mocked tests 或搜索摘要冒充真实横截面 smoke。13条警告来自
既有 Matplotlib/Pyparsing。正式 build 的 failed manifest 输出为空，正式
`data/research/processed/dataset.parquet` 仍不存在；本轮发现不是通过绕过门禁获得。
实际逐文件重新计算了离线复核18个输出 SHA，均与其 manifest 一致。
后续仍优先补正式 PIT/状态/行情输入，四模型实证与真实 Forward 不宣称已验收。
