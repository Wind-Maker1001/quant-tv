# 官方调样 PDF 的严格离线候选复核

## 当前结论

2026-10-11（运行时间戳为 UTC 2026-10-10）已补齐公告14796和15044的原始 PDF，
核验各50条调入和50条调出。200是**调整事件数**，不是完整成员数。
各25条备选名单只作独立证据，合计50条不进入调整事件输出。

这解除“两份2023年定期附件尚未取得/解析”的特定缺口，**不解除正式 PIT 门禁**。
当前仍缺合格的完整500成员基线、全部临时调整覆盖、过渡期成员语义及逐日证券状态。
78/246份已核验正文的覆盖统计未改变，不能据此声称其余168份没有中证500调整。
没有生成正式 dataset、真实横截面 RankIC、五年实证或真正 Forward 信号。

## 可运行入口与依赖边界

研究环境仍是独立 Python 3.9。PDF 读取是可选来源复核工具，不是因子、模型、
回测或普通研究 CLI 的强制依赖。安装可选读取器：

```text
.venv-py39\python.exe -m pip install --no-deps -r dev/requirements-source-review.txt
```

`pypdf==6.13.3` 的实际发行元数据要求 Python >=3.9。本机已安装此固定版本，
`pip check` 无依赖冲突。研究核心 `notice_pdf.py` 只接收有序整页字符串，
不导入 PDF 库、不联网、不调用 GUI/Qlib/Backtrader。

使用已保存的真实正文容器和 SHA 核验过的附件缓存：

```text
.venv-py39\python.exe -X utf8 -m examples.research.review_pdf_notices --input-directory data/research/diagnostics/official-browser-subsets/20261010-missing-pdfs --archive-root data/research/diagnostics/official-browser-attachments/20261010-2023-regular-recheck
```

该入口**只有离线模式**。缓存缺失或损坏返回失败/partial，不提供 HTTP fallback。
每份正文必须恰有一个明确 PDF 链接；多版本不自动选新文件。原附件、原收据和原
正文不修改，每次运行创建独占输入快照、新 CSV/JSON 和 manifest。
用户也可把自己的合规来源提取成整页文本后调用纯函数；提取文本本身不证明来源。

## 解析合同

`csindex-csi500-paired-page-text-v1` 只支持实际观察到的配对行布局：

- 精确的“中证500指数样本调整名单”标题，不把子指数或备选标题当成调样表；
- 表头必须确认左侧调出、右侧调入及两组代码/名称，禁止假定列顺序；
- 按整页顺序保留跨页状态，续页如重发表头须重新验证方向；
- 下一指数或备选名单标题在其数据行之前结束目标表；
- ASCII 六位代码必须完整，缺码、`-`、重复/交叉代码、未知活动区行、数量不符报错；
- 公告正文明确更换数量必须与两侧分别一致，不能从表长反推数量；
- 保留原提取简称（含空格、ST标记）、一基页号/行号和逐页行数；
- 若正文也有内嵌表，动作/代码/去空格后的名称必须一致，不能由 PDF 静默覆盖正文。

输出状态只能是 `PARSED_SOURCE_CANDIDATE_NOT_PIT` 或需要日期进一步核验的候选。
明确“收市后”日期按源声明保留，不自动映射成下一个交易日；出版日、附件修改日、
获取日均不当成成员生效日期。无 `get_members` 或正式发布股票池的接口。
纯文本解析器不宣称已做视觉检查；视觉证据与自动提取结果分开保存。

## 两份真实附件与核验范围

附件获取 run：`20261010T152825.173110Z-review-browser-notices-c54d2996`，success，
2次实际 HTTP 请求、2份原 PDF、0失败。此前超时收据保留，未改写成成功记录。
没有重开被403拒绝的公告正文流程。

| 公告 | 原 PDF SHA-256 | 字节数 | 正文声明收市后日期 | 第1/2页配对行数 |
| --- | --- | ---: | --- | --- |
| 14796 | `5b6b0487112108e6bf6c962add3092e149683c2f7e7b3bbf72c404ec7f017354` | 773545 | 2023-06-09 | 22 / 28 |
| 15044 | `1ccc9012bcb5e539c662232dd26cd7cc17c98923621e2a1970ef4d5bb1fa6ded` | 181980 | 2023-12-08 | 17 / 33 |

原始 URL 从保存的官方正文链接读取，而非猜测文件名：

- [14796官方附件](https://oss-ch.csindex.com.cn/notice/20230526172747-附件：部分指数样本调整名单.pdf)
- [15044官方附件](https://oss-ch.csindex.com.cn/notice/20231124170025-附件：部分指数样本调整名单.pdf)

两份均5页。各第1、2页的中证500目标表和第5页备选表实际用 Poppler 渲染、
查看；不存在只看第一页就假定50行齐全的核验。目标表在第2页中证1000标题前结束。
原 `Last-Modified` 均为2024-11-30，这不证明附件字节在2023年发布时已相同。

独立比较使用 bundled Python 3.12 的 `pdfplumber==0.11.9`，按已视觉确认且绑定
原 PDF SHA 的页/表位置重新提取。动作、canonical symbol、去空格简称、所在页
200项逐一一致；第5页各25个备选代码和1..25排序独立验证，未并入目标表。
这不把不同提取器的一致性当作完整 PIT 或历史可用性证明。

## 实际产物与可审计性

第一次真实离线解析 run：`20261010T160113.413702Z-review-pdf-notices-7a9ad7b7`：

- success；0 HTTP、2次已验证附件缓存读取；2份正文、2份 PDF、200候选事件；
- manifest SHA `f24c406b62a9e79df582aeb5180ebd8fdd5edbb64ee43d524f4a5f900b36c8b4`；
- 候选 CSV SHA `12335d97c6b11ae0656c1054297e7bf577f2bb526a9e5d83cae352320c135af0`；
- review JSON SHA `28e1c00e26a79b4d7b0710fd534c185161919f0ddeea9966611b8253501181fd`；
- 记录实际 Python/包版本、Git提交及未提交工作区、原收据字节、PDF/正文快照、
  各页文本 SHA、脚本/解析模块 SHA 和所有输出 SHA。

这次是在新增代码尚未提交时运行，manifest 如实标为 `git_dirty=true`，不冒充
clean commit 的运行。后续提交后的复验另保留新的 run，旧产物不覆盖。

独立比较：
`data/research/diagnostics/official-pdf-inspection/20261010-2023-regular-crosscheck/comparison.json`，
SHA `3980ac9512a09d812a281d769510b40315868da51f74385c86a2066b3aafad8c`。
它绑定 producer manifest、全部输出、原PDF、比较脚本和6张实际查看的 PNG；
其中脚本自身仍诚实记录“未由脚本做视觉检查”。
同目录另追加 `visual-review.json`，单独绑定6张实际查看的 PNG，并记录模型已查看
左右方向、跨页续表、下一指数边界和备选表。未修改比较器原来的视觉状态字段。

另用新纯解析器对原5份2024～2026定期 PDF 做真实只读复查：公告15267、15471、
15690、3006000、3006137各100候选事件，与原500条 CSV 的动作/代码/名称全部一致。
均在中证1000标题处停止；0 HTTP、10次已验证缓存读取，未覆盖旧提取结果。
这只增加解析复查，未声称这5份的所有页本轮都做了视觉核验。

## 测试及运行问题

实际模块/文件入口/原正文合同联合回归：

```text
.venv-py39\python.exe -m pytest -q tests/research/test_notice_pdf.py tests/research/test_pdf_notice_example.py tests/research/test_notice_review.py tests/research/test_browser_notice_observations.py --tb=short --junitxml=results/runs/pdf-review-targeted-fixed-20261010.xml
```

结果 **192 passed，17.91秒**。人工页字符串/PDF字节仅测试软件合同，不构成市场数据。
测试覆盖跨页、方向、列头、缺码、备选/其他指数隔离、重复/交叉代码、数量不符、
空白扫描页、条件生效、正文冲突、坏/缺缓存、零网络、不可变快照、哈希和逐文件失败。

首次测试中，未给超大字节参数指定短 pytest id，导致 Windows 环境变量长度超限。
191项通过、2个 setup/teardown 错误；修复为短 id 后复验通过。异常栈意外包含
环境中的凭据，本轮生成的原失败 JUnit 已移除，仅保留
`results/runs/pdf-review-targeted-20261010-failure-sanitized.json`。用户已获告知需轮换
被输出的凭据；工具输出无法撤回。不删除其他失败来源收据或历史研究证据。

首次尝试 bundled Python 运行入口因该环境缺 SciPy 而失败，未形成成功研究收据。
正式入口改用研究 Python 3.9并安装单个可选读取器后真实成功；bundled运行时只承担
独立只读表格比较和渲染，不升级研究环境或 Legacy 依赖。

全量研究回归随后实际完成：

```text
.venv-py39\python.exe -m pytest -q --tb=short --junitxml=results/runs/pdf-review-full-20261010.xml
```

**2061 passed、2 deselected、13 warnings，595.69秒**。2项网络测试默认排除，
Legacy副作用测试未运行；13条为既有 Matplotlib/Pyparsing 弃用提示。
本轮新增69个人工合同/入口用例，真实来源复核是上述独立运行，不混淆二者。
`pip check` 无破损依赖，4个新增 Python 文件的 `py_compile` 通过。
原 LICENSE 与审计基线的 Git对象哈希均为
`9fb99866c50772b1afadab1657cc45cc72cdc2d4`，未修改许可证或 Legacy 模块。
