# 隔离真实 A 股探索性因子研究

**EXPLORATORY · UNVERIFIED · HISTORICALLY_RECONSTRUCTED · NO LIVE MONEY · NOT FORMAL CSI500 EVIDENCE**

本入口接受已声明供应商提供的真实未复权和后复权日线，进行描述性因子评价；不签发正式金融数据资格。真实数据不足时输出 BLOCKED，不能使用合成行情替代实证。此次交付的实际状态、规模、结果与缺口以 [研究报告](evidence/exploratory-factor-v1/summary.md) 为准。

## 基线和复用审计

PR #2 于北京时间 2026-10-14 合并。最新 main 是 `9c96afe06d19b6cde92070dc5fa6f43bf37ec034`；开始实现前核对该合并提交的 [研究 CI](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38454437891) 和 [静态检查](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38454437986) 均为 completed / success。独立分支为 `codex/exploratory-factor-research`。

| 现有组件 | 适用条件及本次复用方式 |
| --- | --- |
| data/schema.py、providers/akshare.py | 明确 RAW 四价、HFQ 四价和原始量额换手；同一股票供应商，手转股、百分数转比例。独立探索合同先检查显式字段，禁止 canonicalize 的缺字段别名推导掩盖数据缺口。|
| data/cache.py、provenance.py | 正式缓存及旧收据不改写；既有真实基准缓存复用时需重新验 SHA、声明原版本和获取时间。探索数据使用自己的语义版本和逐文件 SHA，不冒充正式缓存资格。|
| factors/registry.py、preprocess.py | 复用原 14 因子；最长因子 lookback 61；当日 MAD×5、1.4826 尺度及 ddof=0 Z-score，最低横截面 20。实际历史预热至少 130 个完整交易日。|
| labels/forward_return.py | t 收盘后信号，t+1 后复权开盘进入，t+6 开盘退出；减中证500同期开盘收益。实际日历完整面板，不填补缺价；末尾六个信号日可能缺标签。|
| market/regime.py | 中证500价格指数 close、MA20、MA60 的 BULL / BEAR / SIDEWAYS 固定规则，使用截至 t 的数据，未按评价结果修改。指数价是未经股票复权的价格指数，adj_* 只是同一指数观察值的显式别名。|
| metrics/factor.py | 复用日度 Pearson / Spearman、样本数、等权日均及标准差、正值比例、相关、自相关和单边最高五分位换手。最低 20 不放宽。|
| reports/generator.py | 复用现有 CSV 导出；在独立目录生成中文披露与五项标识的 PNG。|
| Golden、金融准入、HFQ、PIT、Forward、交易入口 | 不改数学定义、参考、正式守卫、生产算法或安全开关。新增测试调用原正式/Forward reader 验证探索包不能被其 schema 接收。|

## 五分位合同差异

现有正式 Golden 要求分位边界只取决于当期有效因子；缺失未来标签仍占据分位。此次用户明确要求缺失标签不参与探索评价边界。因此新增适配器只在分位评价调用时过滤缺失 `EXCESS_RET5` 的行，再调用同一 `evaluate_factors`。原核心统计及 Golden 不改，因子、IC、相关、自相关和换手仍使用原完整面板。

这种分位是事后可观察标签子样本的描述性收益，含标签可取得性选择偏差，不能解释为可交易的组合收益。报告同时披露五日标签重叠、多重比较、非 PIT 便利名单、生存者偏差、缺少历史 ST/停复牌/退市及涨跌停可执行状态。

## 独立入口和复现

Windows / Python 3.9，使用隔离研究环境和 `dev/requirements-research.txt`。下面所有真实输入都保留在 gitignored 私有目录；若原始来源未授权再分发，不上传仓库。

```powershell
.\.venv-py39\python.exe -m qbot.research.exploratory.acquire --output data/research/exploratory/a-share-50-20261014-v1
.\.venv-py39\python.exe -m qbot.research.exploratory run --manifest data/research/exploratory/a-share-50-20261014-v1/manifest.json --output results/exploratory
.\.venv-py39\python.exe -m qbot.research.exploratory verify --receipt <private-run-directory>/receipt.json
.\.venv-py39\python.exe -m qbot.research.exploratory.publication --verify docs/research/evidence/exploratory-factor-v1/receipt.json
```

股票名单必须在获取研究窗口行情前冻结，选择日期和方法写入 sample.json。当前固定名单是 `NON_PIT_CONVENIENCE`，`pit=False`；它不是中证500历史成员名单。只按研究起点之前完整预热数据判断资格，不根据未来收益、未来状态或评价表现换股。完整日历×合格冻结证券构造因子面板，滚动窗口遇缺失不跨停牌日期偷位。

探索清单绑定源版本、取得时间、真实原响应哈希、RAW/HFQ角色、转换单位、冻结名单和覆盖范围。上游历史 vintage 未获认证，供应商可能修订历史。内部版本及 SHA 一致不等于独立认证来源、当年可见性或后复权算法。

输入不足、重复、错单位、字段误用、日历错位、预热不足或哈希不一致均明确失败。数据合同只在显式 `allow_synthetic=True` 的离线软件测试中接受标明 `SYNTHETIC_TEST_ONLY` 的夹具；真实报告 CLI 没有该开关。

运行收据使用 `EXPLORATORY_RUN_V1`；公开派生收据使用 `EXPLORATORY_PUBLICATION_V1`。两者均为 `formal_admission=False`、`qualification=UNVERIFIED`、`forward_allowed=False`、`live_allowed=False`。这些 schema 不能充当正式资格、模型 bundle 或 Forward signal 完成收据。公开包只允许指定派生 CSV、Markdown、PNG、质量摘要与来源哈希索引；供应商响应、原价表和逐证券因子标签 Parquet 不发布。

代码哈希采用实际文件字节，包括换行。公开 checkout 若发生 CRLF/LF 转换会产生新的运行版本；这不是伪造原收据。数学参考保持既有 Golden。相同私有输入、代码字节和环境重跑落到同一运行目录并验原收据；旧产物不能静默覆盖。

## 检查与下一阶段

先运行新增离线定向测试，再运行完整 `tests/research -m "not network"`、coverage/JUnit 验收、静态检查及正式 smoke audit。软件回归中的合成夹具只证明软件行为，不是金融结果。最终分支推送并创建 PR，等待该 HEAD 的 CI 和 Codex 审查，不自行合并 main。

一年便利样本即使得到 SUCCESS，也不足以批准五年四模型正式中证500研究。先补同源长期行情、可复核后复权合同、历史 PIT 成员与逐日证券状态、标签尾部价格和足够市场状态样本，再按冻结时间分割评价模型。RankIC 是否为正不决定本轮成功，也不决定正式准入。
