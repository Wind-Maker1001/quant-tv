# 独立模型就绪证据（仅合成软件验收）

NO LIVE MONEY。Formal / Forward 均 BLOCKED。本目录不是五年中证500研究产物。

- `small/`：默认完整离线入口，小规模软件验收PASS；包括未来扰动、重复预测及61项比较反例。
- `scale/`：显式500证券×1200研究日、9个Fold的规模测量，执行的检查全部PASS；省略的扰动、
  重跑和比较反例为NOT_RUN，因此完整软件验收汇总仍为NOT_RUN。
- `resources-summary.csv`：两场景逐阶段汇总；原始调用收据及CSV在各场景目录。嵌套耗时不可相加。
- `final-tests.xml`：68个独立测试全部通过，网络连接在整个测试session被禁止。
- `coverage.xml`：独立Windows覆盖率87%；CLI默认入口另行实测通过，没有合并到该覆盖率数字。
- `index.json`：基线、代码内容SHA、测试文件SHA、硬件标识及证据文件内容SHA。

目录内`.gitattributes`保留收据原始字节，避免Git自动换行转换导致索引中的文件SHA失效。

软件入口、具体命令、测量方法、限制及完整就绪矩阵见[中文审计报告](../../MODEL_RESEARCH_READINESS_AUDIT.md)。
原始合成预测Parquet位于本地 `results/diagnostics/model-readiness/` 对应运行目录，预测内容SHA
已在readiness.json记录；不将大体积可重建输入与预测加入PR。
