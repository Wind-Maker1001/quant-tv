# 严格本地行情入口

本入口用于导入来自可核验数据源的静态历史文件，不负责提供数据、不认证来源权威性，也不替代历史股票池。当前用户没有此类文件，因此入口完成不代表真实端到端或五年实验已经完成。

## 输入合同

使用 `configs/research/csi500_local_smoke.yaml`，或复制配置后显式指定 `data.provider: local_parquet` 和 `paths.market_input_root`。股票池与证券状态可分别选择 `local` 或 `baostock`；三个来源都为本地时，整个数据与因子流水线无需网络或 AKShare/BaoStock 登录。

股票行情和基准行情各一份 CSV/Parquet，均必须包含且只包含以下列：

    date,symbol,open,high,low,close,volume,amount,turnover,adj_factor,
    raw_open,raw_high,raw_low,raw_close,adj_open,adj_high,adj_low,adj_close

日期为严格 `YYYY-MM-DD` 或无时区、零点的 datetime；symbol 已是 `600000.SH` 等 canonical 形式。价格单位为人民币元，量为股、金额为人民币元、换手为小数。股票 `adj_*` 必须由来源提供后复权价格，不能把原始价格复制进去冒充后复权；指数无复权，三组 OHLC 相同、`adj_factor=1`。系统不猜测缺失字段、单位或调整方式。

Schema 拒绝重复、非法 OHLC、负成交量/金额/换手、无穷大，以及不等于 `adj_close/raw_close` 的已提供复权因子（`rtol=1e-8, atol=1e-10`）。允许真实停牌日的缺失和零成交，缺失不向过去填充。`adj_factor` 只是收盘比例审计字段，不假设所有 OHLC 的后复权比例完全相同。

覆盖范围应包含配置要求的全部预热日与研究日。股票文件应覆盖 PIT 历史出现过的股票，不是当前成分股的历史价格合集。日历由基准推导：首尾必须严格存在，但仍需人工以独立来源核对是否遗漏中间交易日。

## 六命令流水线

下面的路径是用户真实导出文件的示例，不是仓库内置数据。相对输入路径与配置路径均相对仓库根目录解析。

    python -m qbot.research.cli import-market-data --config configs/research/csi500_local_smoke.yaml --stocks path/to/stocks.csv --benchmark path/to/csi500.csv --source "原始数据机构和导出方法" --source-version "可核验导出版本"
    python -m qbot.research.cli import-universe --config configs/research/csi500_local_smoke.yaml --input path/to/pit_members.csv
    python -m qbot.research.cli import-security-data --config configs/research/csi500_local_smoke.yaml --status path/to/status.csv --listings path/to/listings.csv
    python -m qbot.research.cli download-data --config configs/research/csi500_local_smoke.yaml
    python -m qbot.research.cli build-dataset --config configs/research/csi500_local_smoke.yaml
    python -m qbot.research.cli evaluate-factors --config configs/research/csi500_local_smoke.yaml

这里 `download-data` 表示通过统一 Provider 填充研究缓存；选择 `local_parquet` 时不下载网络数据。`import-universe` 在本地基准未缓存时先从本地行情 bundle 构建基准日历，随后验证逐日500个成员。缺失 PIT 或证券状态仍严格失败，不会自行补齐。ST/停牌和上市日期文件格式见 [DATA.md](DATA.md)。

示例配置保留真实 CSI500 的500成员要求、130日预热、120日上市阈值和最小横截面20。不能为跑出结果而减少这些要求；测试中的两股票人工数据仅验证软件。

## 不可变快照与版本

导入逐文件固定一次字节，同时用于哈希和解析；校验后写入不可变 `stocks.<generation>.parquet`、`benchmark.<generation>.parquet`，最后原子发布 `manifest.json`。旧代和失败发布的孤立文件不自动删除。清单记录来源声明、输入/输出 SHA-256、单位/复权合同、行数、范围与股票集。来源文字不是第三方认证。

Provider 第一次使用时固定一份清单并验证两份文件，随后固定这一代；切换清单不会使一次运行读入混合代。后续缓存来源合同与 `bundle_version` 绑定。同一内容重导入的文件名或时间变更不改变语义版本；内容或来源合同变更会改变版本。

若修正行情后重新导入，使用一个新的 `paths.data_root` 重新构建缓存、股票池、状态与数据集。旧缓存即使覆盖了全部日期，也因来源身份不一致被拒绝；程序不偷偷忽略修正、不重标旧缓存、不删除用户历史。静态快照不是可增量追加的实时数据源，更不能仅靠切换本地文件冒充真正的 Forward Test。

每个命令仍输出完整 RunManifest。导入清单绑定 bundle，数据集另外绑定原始缓存代、PIT 与状态版本。

## 软件复验

    python -m pytest -q tests/research/test_local_market_provider.py tests/research/test_config_local_provider.py tests/research/test_local_cli_pipeline.py

CLI 整链测试使用人工85日、两股票文件，禁止 HTTP 与 BaoStock 登录，实际运行全部六命令，检查40行数据集、28条成熟标签、14因子、有效 RankIC 和六份成功清单。这是离线工程证据，不是研究结果。

## 通达信原生 DAY 的独立入口

原生 DAY 必须先使用 [TDX_LOCAL_DATA.md](TDX_LOCAL_DATA.md) 的只读审计和 RAW staging
工具。该产物保留未知单位和未核验调整语义，没有 `adj_*` 或 `turnover`，不能直接导入
本 Provider。补充独立样本、证券历史身份、复权和状态证据后，另行组装上述精确生产
Schema，再经过原来源/PIT/状态门禁；本地文件的发现数或工程转换成功不代表研究合格。

## v2证据资格

`import-market-data`现支持可选`--qualification-manifest`，发布自包含、可复算的v2
证据包并绑定来源版本。旧v1可读，但明确TDX来源不得只靠v1声明升级RAW。
合成v2包永不通过正式行情加载；真实资料缺单位、身份、事件、独立参考、状态、
PIT或历史时间/覆盖证据也拒绝。协议未补齐的公司行为执行资格单独阻断。
模块、公式、精确证据合同和真实来源限制见
[DATA_ADJUSTMENT_FOUNDATION.md](DATA_ADJUSTMENT_FOUNDATION.md)。
