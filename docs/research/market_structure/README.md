# 市场结构特征研究软件基础

NO LIVE MONEY。来源仅 SYNTHETIC_TEST_ONLY。真实研究状态为 REAL_RESEARCH_BLOCKED。

实现 32 个候选合同中的 14 个，提供 5/15/30 分钟合成聚合、历史可知快照、资金分类完整性和原生粒度诊断。完整验收状态、被测提交和哈希见 `evidence/v1/acceptance.json` 与 `delivery-manifest.json`。演示收据不会单独声称完整软件验收成功。

- [设计、复用审计及时间合同](DESIGN.md)
- [32 项候选目录](CANDIDATES.md)
- [结构交换 Schema](SCHEMA.json)
- [未来真实来源需求矩阵](REAL_DATA_REQUIREMENTS.md)
- [合成诊断报告](evidence/v1/synthetic/summary.md)
- [全部合同状态](evidence/v1/synthetic/contract_status.csv)
- [资金未分类金额及覆盖](evidence/v1/synthetic/flow_classification.csv)
- [独立验收结论](evidence/v1/acceptance.json)
- [逐文件覆盖率源码清单](evidence/v1/coverage-source-inventory.json)
- [打包限制](evidence/v1/packaging-audit.json)

## 源码运行

在本独立 worktree 根目录使用 Python 3.9 和原锁定研究依赖，输出必须为新目录。不要覆盖历史证据。

```powershell
python -m qbot.research.exploratory.market_structure --help
python -m qbot.research.exploratory.market_structure --output D:/Code/quant-tv-market-structure-artifacts-20261018/reproduce --frequencies 5 15 30
```

默认 24 个虚构证券、6 个合成交易日；日频上下文使用额外 80 个合成预热日。合成工作日不是经过验证的交易所日历。每次历史模拟显式提供窗口、as_of 和 decision_time，禁止用事后版本替换旧时点。

## 显式验收

根 pytest.ini 不会默认收集新测试。必须独立执行，覆盖率数据文件也应独立，避免覆盖正式 CI 的测量。以下输出目录须先建立。

```powershell
$env:COVERAGE_FILE = 'D:/Code/quant-tv-market-structure-artifacts-20261018/recheck/.coverage'
python -m pytest tests/market_structure -q --junitxml=D:/Code/quant-tv-market-structure-artifacts-20261018/recheck/new-tests.xml --cov=qbot/research/exploratory/market_structure --cov-branch --cov-report=xml:D:/Code/quant-tv-market-structure-artifacts-20261018/recheck/coverage.xml --cov-report=json:D:/Code/quant-tv-market-structure-artifacts-20261018/recheck/coverage.json
python -m flake8 --select=E9,F63,F7,F82 qbot/research/exploratory/market_structure tests/market_structure
Remove-Item Env:COVERAGE_FILE
```

独立静态验收还逐文件使用 Python 3.9 compile 验证语法，并执行 git diff --check。正式冻结回归单独使用原 benchmark.py 与 production-complete 校验器，不修改收集清单或覆盖率源清单。新功能验收不能由正式 CI 绿色替代。

Windows 原回归含跨目录相对路径测试，原控制器须通过 `--base-temp` 指定与仓库同盘且尚不存在的临时目录。检出时须防止 core.autocrlf 把 pytest.ini 从基线 LF 转成 CRLF；门禁按原始字节校验，文件必须与基线 Git blob 一致，不能改冻结哈希或事后改写报告。本次检出环境修正记录见 evidence/v1/environment-notes.json。

没有拒绝记录时，拒绝台账仍保留 CSV 表头，便于独立工具读取。原冻结回归的被测提交见 frozen-validation.json；新增模块最终被测提交见 synthetic/receipt.json。原冻结回归完成后，仅修正新增模块对未闭合窗口的静态计数输出，并重新执行独立验收；两次提交间原冻结源码、测试、正式配置和门禁均无改动。这两个执行主体分别记录，不将早先回归伪称为最终提交的执行。

任务目录内的 .gitattributes 固定新增 Python 源码为 LF、证据为原始字节，避免跨平台检出改变源码及产物哈希；未修改根属性文件或正式门禁。

市场状态完全复用原判定；当日尚未完成/发布/实际可用的基准日频记录不进入分钟快照。窗口结束也不意味着一分钟资金或价格已经发布。未分类资金不能解释为零净主动额。

## 资格和安装边界

SOFTWARE_MVP_SUCCESS 仅表示合成软件合同、反例和工程证据通过。REAL_RESEARCH_BLOCKED 表示真实来源、历史可知证据和预测能力均未验证。未训练模型、未生成收益标签或可交易 Alpha，不自动接纳候选到正式研究。

命名空间不含 __init__.py，原 find_packages 可能遗漏它。本轮只验证 Python 3.9 源码入口；wheel、安装包及安装后入口均 NOT_VALIDATED。
