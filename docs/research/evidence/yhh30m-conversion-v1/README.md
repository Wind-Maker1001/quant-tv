# 余哈哈分钟转换派生证据

NO LIVE MONEY。本目录仅保存聚合统计、分区定位和软件验收摘要，不含原始行情或抽样价格。

- `summary.json`：全量行数、覆盖、异常/缺失、来源审计绑定、实现 SHA、小样本验收及资源实测。
- `parquet-inventory.csv`：69 个分区相对于数据集根目录的路径、记录数、字节数、Parquet 与收据 SHA。
- `verification.json`：完整套件、Windows 临时目录环境失败与未改断言的复测记录；保留原运行 SHA 及逐用例最终通过状态。
- `completion-audit.json`：逐项交付与验收证据索引。

数据集根目录为本工作树忽略目录 `data/research/yhh30m/full-v1/`。
其中 `dataset.json` 绑定月收据；月收据绑定来源 CSV 内容 SHA、软件/契约与输出 SHA，
并含原始数值随机样本。原始 ZIP/CSV 保留于用户提供的外部目录，未复制到本证据目录。

旧审计 JSON 的公开脱敏映射依据
`../pit-publication-20261018-v1/manifest.json`。旧私有原件的哈希、公开副本的哈希及本次来源容器/成员哈希
分别保留原义；不重写旧收据或将历史 PASS 当成本次金融认证。

方法、字段映射和资格缺口见 [接入说明](../../YHH_30M_DATA.md)，
实际运行与交付见 [交付报告](../../YHH_30M_CONVERSION_DELIVERY.md)。
Parquet 工程验收成功不等于金融数据合格；正式准入继续为 false。
