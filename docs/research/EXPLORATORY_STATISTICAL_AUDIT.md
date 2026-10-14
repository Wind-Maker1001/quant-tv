# 冻结真实A股探索统计审计

**EXPLORATORY · UNVERIFIED · HISTORICALLY_RECONSTRUCTED · NON_PIT_CONVENIENCE · NO LIVE MONEY · NOT FORMAL CSI500 EVIDENCE**

本入口仅复用PR #3封存的50股、2025-09-12至2026-09-11真实数据，原语义版本 `2f145d173f5ddc79d303f580bc4485241023ae3971d3b40a2e8fa6e3de2e3f5f`。main基线 `64c72ab0aee49bba59dbf7449f2c8235c61fca2c` 的[完整研究CI](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38530507226)和[静态CI](https://github.com/Wind-Maker1001/quant-tv/actions/runs/38530507234)通过后，建立 `codex/exploratory-statistical-audit`。

[中文报告](evidence/exploratory-statistical-audit-v2/report.md)、[公开收据](evidence/exploratory-statistical-audit-v2/receipt.json)、[输入核验](evidence/exploratory-statistical-audit-v2/input_audit.json)与同目录10张CSV及4张PNG提供完整复核材料。旧探索v1/v2与其收据原样保留。实际证券分位成员仅保留在忽略的私有审计运行目录，不随PR上传。

## 计算合同

- 原始236日RankIC均值、ddof=1标准差、正值比例；保留全部242实际信号日期和末尾六日缺失。
- HAC/Newey-West lag5/20，Bartlett权重，n/(n-k)修正与正态近似；20日非循环重叠Moving Block Bootstrap，2000次，seed20261014，14因子/状态/缺失位置联合抽日期元组；百分位95%区间和中心化双侧Monte Carlo p。
- 均值14项、状态差42项分别为事后探索检验族；各方法分别Holm，不跨方法挑p、不宣称全局同时推断。状态完整轴指示变量回归，差异含协方差，Bootstrap不压缩同状态日。
- SIDEWAYS45日、8个短区间不足；BULL128日/6区间、BEAR63有效日/3区间也无法替代独立周期验证。
- 五分位A先过滤可观察标签再分桶；B按t日全部合格有限因子分桶后统计可观察标签。A必须复现冻结原分位；数量、可观察成员变化、Q1–Q5收益、Q5–Q1、缺失率及月分布全部独立输出。无标签保留NA，正式`evaluate_factors`与Golden不修改。

## 离线复现

Windows / Python3.9隔离研究环境。必须持有原经授权的私有输入与匹配的v2私有运行；本入口没有下载或合成选项。哈希包括源文件换行字节；不同checkout换行/计算实现产生不匹配时应BLOCKED，不能放宽冻结版本。

```powershell
.\.venv-py39\python.exe -m qbot.research.exploratory.statistical_audit `
  --manifest data/research/exploratory/a-share-50-20261014-v1/manifest.json `
  --private-run results/exploratory/2f145d173f5ddc79/89e5d6e2ac7858a8 `
  --publication docs/research/evidence/exploratory-factor-v2 `
  --output results/exploratory

.\.venv-py39\python.exe -m qbot.research.exploratory.statistical_audit `
  --verify docs/research/evidence/exploratory-statistical-audit-v2/receipt.json --public
```

公开产物可单独核验其收据，不需要把私有行情下载到CI。真实重算须重新验源哈希、原计算代码、证券级因子/标签/状态、日度IC/覆盖和原A分位；聚合CSV不能用来反推成员。缺输入、版本变化、代码证据失败、统计合同失败返回退出码2，产生独立BLOCKED报告和收据；不伪造实证。

私有schema为`EXPLORATORY_STATISTICAL_AUDIT_PRIVATE_V1`，公开schema为`EXPLORATORY_STATISTICAL_AUDIT_PUBLIC_V1`；公开收据绑定私有审计收据SHA。发布只能新建目录，文件与CSV列均有白名单；正式金融准入、Forward、模型、交易及Golden守卫不变。

## 验证与适用边界

定向测试验证时间依赖、HAC独立计算、缺失日期、实际区块邻接、状态切换及协方差、样本不足、标签缺失/未成熟、固定检验族、哈希及冻结来源不一致、代码版本失败BLOCKED、私有成员不发布、CSV行情字段拒绝与正式/Forward拒绝；Golden原参考回归通过。最终完整CI和PR审查见交付说明。

本轮没有均值或状态差经Holm得到统计支持。值得扩大到独立五年历史周期的隔离探索，解决方向稳定性、状态重复、长依赖及选择偏差的问题；扩大年份本身不补齐历史PIT、HFQ合同、vintage和执行资格，也不批准正式五年四模型研究。
