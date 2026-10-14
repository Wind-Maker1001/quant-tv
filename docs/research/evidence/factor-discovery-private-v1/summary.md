# 受约束自动因子发现 MVP：描述性探索报告

**NO LIVE MONEY。软件执行成功不代表发现可靠或可交易 Alpha。**

数据：EXPLORATORY / UNVERIFIED / NON_PIT_CONVENIENCE。开发区间：2025-09-12 至 2026-06-30，之前历史只用于预热。

实际候选记录 40；结构唯一 39；成功计算 39；计算失败 0；语义拒绝 0；结构重复 1。

软件状态：SOFTWARE_MVP_SUCCESS；真实数据状态：SUCCESS（all frozen private hashes/contracts verified）。

总耗时 32.888 秒；因子计算耗时 0.139 秒；密集网格 17950 行；缓存峰值 12636800 字节；子表达式缓存命中 73 次。

## 评价合同

生成器只接收冻结配置，先有限经济模板枚举，再规范化和结构去重，无遗传优化、实时 LLM 或标签输入。Add/Mul 仅交换两个操作数；不使用浮点结合律改写。最终候选为无物理量纲，保留 RAW/HFQ 来源和收益/换手语义。

时序按证券与显式交易日历计算。Lag/Delta 仅正滞后；RollingStd 使用 ddof=1 且完整窗口；缺日保持缺失。零分母、非有限值保持缺失，原因计数见 candidates.csv。

复用 FactorLab 逐日 MAD/Z-score 及 evaluate_factors 的 IC、RankIC 和五分位数学。未来标签仅在进入与退出交易日都落入开发窗口且成熟时参与描述性评价；信号分组在因子可用时形成。quantile_returns.csv 为实际信号分组；label_sensitivity.csv 仅披露完整标签子样本重选分组的选择敏感性。末尾未成熟标签不会重新决定信号分组。

冗余使用逐日横截面 Pearson，分别报告平均有符号与平均绝对相关，禁止跨日期拼接后得出单一结论。至少 20 证券、60 有效日期、平均配对覆盖 80%；高冗余阈值 0.98。数值相同还要求每个开发日已知值及缺失掩码完全一致。证据不足为 UNDETERMINED。

结构重复跳过计算；数值冗余候选保留全部审计记录，不自动筛除或翻转方向。旧 14 因子只读调用；AMIHU20 不可表示为首版 AST，其特殊量纲只参与数值比较。

## 每个候选的开发期质量与指标

|候选|语义类别|计算状态|有效率|缺失率|异常值率|处理后覆盖|IC均值|RankIC均值|旧14结构匹配|
|---|---|---|---|---|---|---|---|---|---|
|FD_001|TREND_MOMENTUM|SUCCESS|0.998519|0.00148148|0.0227513|0.998519|0.0287526|0.0353531||
|FD_002|TREND_MOMENTUM|SUCCESS|0.997989|0.00201058|0.015873|0.997989|0.0285735|0.0357959||
|FD_003|TREND_MOMENTUM|SUCCESS|0.996825|0.0031746|0.0167196|0.996825|-0.00123607|0.0114836||
|FD_004|TREND_MOMENTUM|SUCCESS|0.98836|0.0116402|0.0186243|0.98836|-0.0279716|-0.0196006||
|FD_005|RETURN_VOLATILITY|SUCCESS|0.998413|0.0015873|0.00402116|0.998413|0.0288036|0.0212016||
|FD_006|RETURN_VOLATILITY|SUCCESS|0.997884|0.0021164|0.000952381|0.997884|0.0155524|0.011008||
|FD_007|RETURN_VOLATILITY|SUCCESS|0.996614|0.00338624|0.00010582|0.996614|0.000958461|0.00284169||
|FD_008|RETURN_VOLATILITY|SUCCESS|0.988148|0.0118519|0.00021164|0.988148|-0.00426248|-0.0250314||
|FD_009|ACTIVITY_DYNAMICS|SUCCESS|0.998519|0.00148148|0.0100529|0.998519|0.00085893|-0.00329262||
|FD_010|ACTIVITY_DYNAMICS|SUCCESS|0.997989|0.00201058|0.013545|0.997989|0.00558462|0.00196655||
|FD_011|ACTIVITY_DYNAMICS|SUCCESS|0.996825|0.0031746|0.0169312|0.996825|-0.00955869|-0.0107618||
|FD_012|ACTIVITY_DYNAMICS|SUCCESS|0.98836|0.0116402|0.0240212|0.98836|0.00169363|0.000828102||
|FD_013|ACTIVITY_DYNAMICS|SUCCESS|0.998519|0.00148148|0.0102646|0.998519|0.00267333|-0.00110338||
|FD_014|ACTIVITY_DYNAMICS|SUCCESS|0.997989|0.00201058|0.0141799|0.997989|0.00780414|0.0043875||
|FD_015|ACTIVITY_DYNAMICS|SUCCESS|0.996825|0.0031746|0.0187302|0.996825|-0.00926675|-0.00898044||
|FD_016|ACTIVITY_DYNAMICS|SUCCESS|0.98836|0.0116402|0.0263492|0.98836|0.00113801|-0.00289421||
|FD_017|ACTIVITY_DYNAMICS|SUCCESS|0.998519|0.00148148|0.00973545|0.998519|0.00184763|-0.00171295||
|FD_018|ACTIVITY_DYNAMICS|SUCCESS|0.997989|0.00201058|0.0133333|0.997989|0.00718996|0.00451521||
|FD_019|ACTIVITY_DYNAMICS|SUCCESS|0.996825|0.0031746|0.0162963|0.996825|-0.00819699|-0.00936775||
|FD_020|ACTIVITY_DYNAMICS|SUCCESS|0.98836|0.0116402|0.0242328|0.98836|0.00219426|0.00104336||
|FD_021|PRICE_VOLUME_INTERACTION|SUCCESS|0.998519|0.00148148|0.0107937|0.998519|0.00163216|-0.00255481||
|FD_022|PRICE_VOLUME_INTERACTION|SUCCESS|0.997989|0.00201058|0.0149206|0.997989|0.00665663|0.0038728||
|FD_023|PRICE_VOLUME_INTERACTION|SUCCESS|0.996825|0.0031746|0.02|0.996825|-0.0100085|-0.00875416||
|FD_024|PRICE_VOLUME_INTERACTION|SUCCESS|0.98836|0.0116402|0.0269841|0.98836|-0.000518922|-0.00440079||
|FD_025|PRICE_VOLUME_INTERACTION|EXACT_DUPLICATE|—|—|—|—|—|—||
|FD_026|TREND_MOMENTUM|SUCCESS|0.998413|0.0015873|0.0178836|0.998413|0.0241336|0.0242478||
|FD_027|TREND_MOMENTUM|SUCCESS|0.997884|0.0021164|0.0172487|0.997884|0.00727881|0.0178402||
|FD_028|TREND_MOMENTUM|SUCCESS|0.997672|0.00232804|0.015873|0.997672|-0.0263261|-0.0102422||
|FD_029|TREND_MOMENTUM|SUCCESS|0.99746|0.00253968|0.0220106|0.99746|-0.0282993|-0.0334096||
|FD_030|RETURN_VOLATILITY|SUCCESS|0.998307|0.00169312|0.0404233|0.998307|0.0210393|0.0178658||
|FD_031|RETURN_VOLATILITY|SUCCESS|0.997778|0.00222222|0.0497354|0.997778|0.0257628|0.0220764||
|FD_032|RETURN_VOLATILITY|SUCCESS|0.996402|0.00359788|0.057672|0.996402|0.0234677|0.0191014||
|FD_033|RETURN_VOLATILITY|SUCCESS|0.987937|0.0120635|0.0722751|0.987937|0.0173964|0.0174768||
|FD_034|ACTIVITY_DYNAMICS|SUCCESS|0.998413|0.0015873|0.0175661|0.998413|0.000345525|0.00400753||
|FD_035|ACTIVITY_DYNAMICS|SUCCESS|0.997884|0.0021164|0.0192593|0.997884|-0.00178756|0.000663449||
|FD_036|ACTIVITY_DYNAMICS|SUCCESS|0.997672|0.00232804|0.0214815|0.997672|-0.00754044|0.00299615||
|FD_037|ACTIVITY_DYNAMICS|SUCCESS|0.99746|0.00253968|0.0286772|0.99746|-0.0300147|-0.0235248||
|FD_038|PRICE_VOLUME_INTERACTION|SUCCESS|0.998413|0.0015873|0.0297354|0.998413|0.0232665|0.0246954||
|FD_039|PRICE_VOLUME_INTERACTION|SUCCESS|0.997884|0.0021164|0.0286772|0.997884|0.0151192|0.0171078||
|FD_040|PRICE_VOLUME_INTERACTION|SUCCESS|0.996614|0.00338624|0.0298413|0.996614|-0.0139524|-0.0050983||

## 原 14 因子及候选之间的冗余

CANDIDATE：{"NON_REDUNDANT": 717, "HIGHLY_REDUNDANT": 24}。完整配对结论、有效日期与覆盖见 redundancy_summary.csv。

ORIGINAL14：{"NON_REDUNDANT": 542, "HIGHLY_REDUNDANT": 4}。完整配对结论、有效日期与覆盖见 redundancy_summary.csv。

- FD_001 与旧14最接近：REV5，平均绝对相关 0.819267，NON_REDUNDANT，有效 189 日，配对覆盖 0.998413。
- FD_002 与旧14最接近：REV5，平均绝对相关 0.925777，NON_REDUNDANT，有效 189 日，配对覆盖 0.997989。
- FD_003 与旧14最接近：PRICE_MA20，平均绝对相关 1，HIGHLY_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_004 与旧14最接近：MOM20，平均绝对相关 0.837084，NON_REDUNDANT，有效 189 日，配对覆盖 0.98836。
- FD_005 与旧14最接近：REV5，平均绝对相关 0.745764，NON_REDUNDANT，有效 189 日，配对覆盖 0.998413。
- FD_006 与旧14最接近：PRICE_MA20，平均绝对相关 0.749435，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_007 与旧14最接近：MOM20，平均绝对相关 0.829939，NON_REDUNDANT，有效 189 日，配对覆盖 0.996614。
- FD_008 与旧14最接近：MOM60，平均绝对相关 0.852876，NON_REDUNDANT，有效 189 日，配对覆盖 0.988148。
- FD_009 与旧14最接近：REV1，平均绝对相关 0.333275，NON_REDUNDANT，有效 189 日，配对覆盖 0.998519。
- FD_010 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.38067，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_011 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.636809，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_012 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.605347，NON_REDUNDANT，有效 189 日，配对覆盖 0.98836。
- FD_013 与旧14最接近：REV1，平均绝对相关 0.360028，NON_REDUNDANT，有效 189 日，配对覆盖 0.998519。
- FD_014 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.400024，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_015 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.650123，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_016 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.59276，NON_REDUNDANT，有效 189 日，配对覆盖 0.98836。
- FD_017 与旧14最接近：REV1，平均绝对相关 0.333195，NON_REDUNDANT，有效 189 日，配对覆盖 0.998519。
- FD_018 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.380343，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_019 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.636421，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_020 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.605351，NON_REDUNDANT，有效 189 日，配对覆盖 0.98836。
- FD_021 与旧14最接近：REV1，平均绝对相关 0.36702，NON_REDUNDANT，有效 189 日，配对覆盖 0.998519。
- FD_022 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.400555，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_023 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.649655，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_024 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.590043，NON_REDUNDANT，有效 189 日，配对覆盖 0.98836。
- FD_026 与旧14最接近：REV5，平均绝对相关 1，HIGHLY_REDUNDANT，有效 189 日，配对覆盖 0.998413。
- FD_027 与旧14最接近：PRICE_MA20，平均绝对相关 0.919536，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_028 与旧14最接近：MOM20，平均绝对相关 1，HIGHLY_REDUNDANT，有效 189 日，配对覆盖 0.997672。
- FD_029 与旧14最接近：MOM60，平均绝对相关 1，HIGHLY_REDUNDANT，有效 189 日，配对覆盖 0.99746。
- FD_030 与旧14最接近：REV1，平均绝对相关 0.286565，NON_REDUNDANT，有效 189 日，配对覆盖 0.998307。
- FD_031 与旧14最接近：REV1，平均绝对相关 0.301815，NON_REDUNDANT，有效 189 日，配对覆盖 0.997778。
- FD_032 与旧14最接近：REV1，平均绝对相关 0.308769，NON_REDUNDANT，有效 189 日，配对覆盖 0.996402。
- FD_033 与旧14最接近：REV1，平均绝对相关 0.316746，NON_REDUNDANT，有效 189 日，配对覆盖 0.987937。
- FD_034 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.433566，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_035 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.628314，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_036 与旧14最接近：VOLUME_RATIO，平均绝对相关 0.575015，NON_REDUNDANT，有效 189 日，配对覆盖 0.996614。
- FD_037 与旧14最接近：TURN5，平均绝对相关 0.428061，NON_REDUNDANT，有效 189 日，配对覆盖 0.997037。
- FD_038 与旧14最接近：REV5，平均绝对相关 0.959718，NON_REDUNDANT，有效 189 日，配对覆盖 0.998413。
- FD_039 与旧14最接近：PRICE_MA20，平均绝对相关 0.890102，NON_REDUNDANT，有效 189 日，配对覆盖 0.996825。
- FD_040 与旧14最接近：MOM20，平均绝对相关 0.931203，NON_REDUNDANT，有效 189 日，配对覆盖 0.996614。

## 表达式、量纲、规范形式与复杂度

### FD_001

TREND_MOMENTUM：复权收盘价相对过去5个交易日均价，描述价格趋势位置。

表达式：`SafeDiv(adj_close,RollingMean(adj_close,5))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 4 交易日。

SHA-256：`8c50b376e148a618bee30565b56b6c0fa2d24e29d4dcec4af54f181a6d924b2c`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"adj_close"},{"args":[{"op":"Field","value":"adj_close"}],"op":"RollingMean","param":5}],"op":"SafeDiv"}
```

### FD_002

TREND_MOMENTUM：复权收盘价相对过去10个交易日均价，描述价格趋势位置。

表达式：`SafeDiv(adj_close,RollingMean(adj_close,10))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 9 交易日。

SHA-256：`3a0d1bf29ea3f3394be7377caeb4bf14d99aa9fb0fa554cfeb73964ab4a45fc5`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"adj_close"},{"args":[{"op":"Field","value":"adj_close"}],"op":"RollingMean","param":10}],"op":"SafeDiv"}
```

### FD_003

TREND_MOMENTUM：复权收盘价相对过去20个交易日均价，描述价格趋势位置。

表达式：`SafeDiv(adj_close,RollingMean(adj_close,20))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 19 交易日。

SHA-256：`0f9ca71a4ab82b98848b52be0557e38e6da010a2d4aa7ce4b864c931f78bfd26`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"adj_close"},{"args":[{"op":"Field","value":"adj_close"}],"op":"RollingMean","param":20}],"op":"SafeDiv"}
```

### FD_004

TREND_MOMENTUM：复权收盘价相对过去60个交易日均价，描述价格趋势位置。

表达式：`SafeDiv(adj_close,RollingMean(adj_close,60))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 59 交易日。

SHA-256：`15f2832dcafb7cb9708a1222964c488fa16bed7ecdbc1726349ec86d718d4115`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"adj_close"},{"args":[{"op":"Field","value":"adj_close"}],"op":"RollingMean","param":60}],"op":"SafeDiv"}
```

### FD_005

RETURN_VOLATILITY：过去5个交易日平均单日收益除以同期收益标准差，描述收益与风险的关系。

表达式：`SafeDiv(RollingMean(RET1,5),RollingStd(RET1,5))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 5, "rolling_operators": 2}`；有效回看 5 交易日。

SHA-256：`de23e12b3ac3396122cbf806b563ca921fbc04fdc7d622d5974338dbd7d4c204`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"RET1"}],"op":"RollingMean","param":5},{"args":[{"op":"Field","value":"RET1"}],"op":"RollingStd","param":5}],"op":"SafeDiv"}
```

### FD_006

RETURN_VOLATILITY：过去10个交易日平均单日收益除以同期收益标准差，描述收益与风险的关系。

表达式：`SafeDiv(RollingMean(RET1,10),RollingStd(RET1,10))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 5, "rolling_operators": 2}`；有效回看 10 交易日。

SHA-256：`bbc72617b56833c781097e35b246c9d6d1cdaa80b2ab605b28d9f25525452c70`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"RET1"}],"op":"RollingMean","param":10},{"args":[{"op":"Field","value":"RET1"}],"op":"RollingStd","param":10}],"op":"SafeDiv"}
```

### FD_007

RETURN_VOLATILITY：过去20个交易日平均单日收益除以同期收益标准差，描述收益与风险的关系。

表达式：`SafeDiv(RollingMean(RET1,20),RollingStd(RET1,20))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 5, "rolling_operators": 2}`；有效回看 20 交易日。

SHA-256：`7b6e4bb8583ecfc7021e6702016e6973fea8034afd7d7819be3c5b71d7778178`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"RET1"}],"op":"RollingMean","param":20},{"args":[{"op":"Field","value":"RET1"}],"op":"RollingStd","param":20}],"op":"SafeDiv"}
```

### FD_008

RETURN_VOLATILITY：过去60个交易日平均单日收益除以同期收益标准差，描述收益与风险的关系。

表达式：`SafeDiv(RollingMean(RET1,60),RollingStd(RET1,60))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 5, "rolling_operators": 2}`；有效回看 60 交易日。

SHA-256：`a5774b3370a816c00ef9ac306dae7b3696f9c61d9dd0cb1849032df27f1a1f08`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"RET1"}],"op":"RollingMean","param":60},{"args":[{"op":"Field","value":"RET1"}],"op":"RollingStd","param":60}],"op":"SafeDiv"}
```

### FD_009

ACTIVITY_DYNAMICS：当日成交股数相对过去5个交易日均值，描述成交活跃程度。

表达式：`SafeDiv(volume,RollingMean(volume,5))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 4 交易日。

SHA-256：`9209b3158f56d1ba05858db6d260a2e1d6ec396196bb1780469b7d26e688e5ab`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"volume"},{"args":[{"op":"Field","value":"volume"}],"op":"RollingMean","param":5}],"op":"SafeDiv"}
```

### FD_010

ACTIVITY_DYNAMICS：当日成交股数相对过去10个交易日均值，描述成交活跃程度。

表达式：`SafeDiv(volume,RollingMean(volume,10))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 9 交易日。

SHA-256：`4e4d47d6e4045163e2255c83c1e59d92e7a287d53e98b3b8e527654965490013`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"volume"},{"args":[{"op":"Field","value":"volume"}],"op":"RollingMean","param":10}],"op":"SafeDiv"}
```

### FD_011

ACTIVITY_DYNAMICS：当日成交股数相对过去20个交易日均值，描述成交活跃程度。

表达式：`SafeDiv(volume,RollingMean(volume,20))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 19 交易日。

SHA-256：`d2dfd1fadc0baff14054d4dea26f778e3671e8f0ef26fade4193c8e014eb7dfd`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"volume"},{"args":[{"op":"Field","value":"volume"}],"op":"RollingMean","param":20}],"op":"SafeDiv"}
```

### FD_012

ACTIVITY_DYNAMICS：当日成交股数相对过去60个交易日均值，描述成交活跃程度。

表达式：`SafeDiv(volume,RollingMean(volume,60))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 59 交易日。

SHA-256：`ae2c0918fa2e9e400cfbbcecab350da1901fcb5d3a708d31680d861ef5d4acd0`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"volume"},{"args":[{"op":"Field","value":"volume"}],"op":"RollingMean","param":60}],"op":"SafeDiv"}
```

### FD_013

ACTIVITY_DYNAMICS：当日成交金额相对过去5个交易日均值，描述资金成交活跃程度。

表达式：`SafeDiv(amount,RollingMean(amount,5))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 4 交易日。

SHA-256：`b39cd57b5d41fbb866f14a267e89ba4d686a1f58fef259a55b79e3e11482ad00`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"amount"},{"args":[{"op":"Field","value":"amount"}],"op":"RollingMean","param":5}],"op":"SafeDiv"}
```

### FD_014

ACTIVITY_DYNAMICS：当日成交金额相对过去10个交易日均值，描述资金成交活跃程度。

表达式：`SafeDiv(amount,RollingMean(amount,10))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 9 交易日。

SHA-256：`247efa806262f9add62d9d88fe7084cce3359d1d02ab02b0a84f486c65f1116b`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"amount"},{"args":[{"op":"Field","value":"amount"}],"op":"RollingMean","param":10}],"op":"SafeDiv"}
```

### FD_015

ACTIVITY_DYNAMICS：当日成交金额相对过去20个交易日均值，描述资金成交活跃程度。

表达式：`SafeDiv(amount,RollingMean(amount,20))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 19 交易日。

SHA-256：`146a8d2c80f4d8e032002e21c64d41656eada59a3a200cbc8b855fd7ad97a7d5`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"amount"},{"args":[{"op":"Field","value":"amount"}],"op":"RollingMean","param":20}],"op":"SafeDiv"}
```

### FD_016

ACTIVITY_DYNAMICS：当日成交金额相对过去60个交易日均值，描述资金成交活跃程度。

表达式：`SafeDiv(amount,RollingMean(amount,60))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 59 交易日。

SHA-256：`1c6f75986288b4eff34f6566aa592dbb74fd1b2174cf8bead03f76e0a0237811`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"amount"},{"args":[{"op":"Field","value":"amount"}],"op":"RollingMean","param":60}],"op":"SafeDiv"}
```

### FD_017

ACTIVITY_DYNAMICS：当日比例换手率相对过去5个交易日均值，描述换手活跃程度。

表达式：`SafeDiv(turnover,RollingMean(turnover,5))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 4 交易日。

SHA-256：`17eb56531d7d50cec5ab40838f78852a3adf9972bf8906b35a786732b976f868`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"turnover"},{"args":[{"op":"Field","value":"turnover"}],"op":"RollingMean","param":5}],"op":"SafeDiv"}
```

### FD_018

ACTIVITY_DYNAMICS：当日比例换手率相对过去10个交易日均值，描述换手活跃程度。

表达式：`SafeDiv(turnover,RollingMean(turnover,10))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 9 交易日。

SHA-256：`4795afc0bca80a174f07a66512f22b1aabddc937d1d67448041dc9748ac7ed39`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"turnover"},{"args":[{"op":"Field","value":"turnover"}],"op":"RollingMean","param":10}],"op":"SafeDiv"}
```

### FD_019

ACTIVITY_DYNAMICS：当日比例换手率相对过去20个交易日均值，描述换手活跃程度。

表达式：`SafeDiv(turnover,RollingMean(turnover,20))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 19 交易日。

SHA-256：`db0fab1d6092bdc99f4a6d54673d4b3470ab43b2276a31020c794a95b5a1a39d`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"turnover"},{"args":[{"op":"Field","value":"turnover"}],"op":"RollingMean","param":20}],"op":"SafeDiv"}
```

### FD_020

ACTIVITY_DYNAMICS：当日比例换手率相对过去60个交易日均值，描述换手活跃程度。

表达式：`SafeDiv(turnover,RollingMean(turnover,60))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 4, "rolling_operators": 1}`；有效回看 59 交易日。

SHA-256：`1b81904983d4f239d58b0cda2b441fb1fd520aa4c45654ba75f785c2a28cbdb7`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"op":"Field","value":"turnover"},{"args":[{"op":"Field","value":"turnover"}],"op":"RollingMean","param":60}],"op":"SafeDiv"}
```

### FD_021

PRICE_VOLUME_INTERACTION：价格相对5日均价与成交量相对5日均量的乘积，描述价量共同偏离。

表达式：`Mul(SafeDiv(adj_close,RollingMean(adj_close,5)),SafeDiv(volume,RollingMean(volume,5)))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 4, "nodes": 9, "rolling_operators": 2}`；有效回看 4 交易日。

SHA-256：`9b76c7cc7ee11def6e9e6c98b0e7b462cc303d28e77b6aa8e0d77862dc329fee`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"adj_close"},{"args":[{"op":"Field","value":"adj_close"}],"op":"RollingMean","param":5}],"op":"SafeDiv"},{"args":[{"op":"Field","value":"volume"},{"args":[{"op":"Field","value":"volume"}],"op":"RollingMean","param":5}],"op":"SafeDiv"}],"op":"Mul"}
```

### FD_022

PRICE_VOLUME_INTERACTION：价格相对10日均价与成交量相对10日均量的乘积，描述价量共同偏离。

表达式：`Mul(SafeDiv(adj_close,RollingMean(adj_close,10)),SafeDiv(volume,RollingMean(volume,10)))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 4, "nodes": 9, "rolling_operators": 2}`；有效回看 9 交易日。

SHA-256：`3c665febc16453edc8f5d0eef88644578f28abefe8ba6d8c56b7b0763f4e5894`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"adj_close"},{"args":[{"op":"Field","value":"adj_close"}],"op":"RollingMean","param":10}],"op":"SafeDiv"},{"args":[{"op":"Field","value":"volume"},{"args":[{"op":"Field","value":"volume"}],"op":"RollingMean","param":10}],"op":"SafeDiv"}],"op":"Mul"}
```

### FD_023

PRICE_VOLUME_INTERACTION：价格相对20日均价与成交量相对20日均量的乘积，描述价量共同偏离。

表达式：`Mul(SafeDiv(adj_close,RollingMean(adj_close,20)),SafeDiv(volume,RollingMean(volume,20)))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 4, "nodes": 9, "rolling_operators": 2}`；有效回看 19 交易日。

SHA-256：`fa3b5f7edd2638076b98d611280b7b6b07299dd01478210e3195b5d36cb04c38`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"adj_close"},{"args":[{"op":"Field","value":"adj_close"}],"op":"RollingMean","param":20}],"op":"SafeDiv"},{"args":[{"op":"Field","value":"volume"},{"args":[{"op":"Field","value":"volume"}],"op":"RollingMean","param":20}],"op":"SafeDiv"}],"op":"Mul"}
```

### FD_024

PRICE_VOLUME_INTERACTION：价格相对60日均价与成交量相对60日均量的乘积，描述价量共同偏离。

表达式：`Mul(SafeDiv(adj_close,RollingMean(adj_close,60)),SafeDiv(volume,RollingMean(volume,60)))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 4, "nodes": 9, "rolling_operators": 2}`；有效回看 59 交易日。

SHA-256：`5eb305a3877a2868c76ec1c675aa69f158a4abbab1c236137b0959cccd96ab0e`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"adj_close"},{"args":[{"op":"Field","value":"adj_close"}],"op":"RollingMean","param":60}],"op":"SafeDiv"},{"args":[{"op":"Field","value":"volume"},{"args":[{"op":"Field","value":"volume"}],"op":"RollingMean","param":60}],"op":"SafeDiv"}],"op":"Mul"}
```

### FD_025

PRICE_VOLUME_INTERACTION：同一5日价量共同偏离表达式交换乘法操作数，仅用于结构重复审计。

表达式：`Mul(SafeDiv(volume,RollingMean(volume,5)),SafeDiv(adj_close,RollingMean(adj_close,5)))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 4, "nodes": 9, "rolling_operators": 2}`；有效回看 4 交易日。

SHA-256：`9b76c7cc7ee11def6e9e6c98b0e7b462cc303d28e77b6aa8e0d77862dc329fee`。状态 EXACT_DUPLICATE；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"adj_close"},{"args":[{"op":"Field","value":"adj_close"}],"op":"RollingMean","param":5}],"op":"SafeDiv"},{"args":[{"op":"Field","value":"volume"},{"args":[{"op":"Field","value":"volume"}],"op":"RollingMean","param":5}],"op":"SafeDiv"}],"op":"Mul"}
```

### FD_026

TREND_MOMENTUM：复权收盘价过去5个交易日的变化除以当时价格，描述区间价格动量。

表达式：`SafeDiv(Delta(adj_close,5),Lag(adj_close,5))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 5, "rolling_operators": 0}`；有效回看 5 交易日。

SHA-256：`4f19281a32016ab0cf22a552a253d7e55460adcd2630882d98cb253634d58836`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"adj_close"}],"op":"Delta","param":5},{"args":[{"op":"Field","value":"adj_close"}],"op":"Lag","param":5}],"op":"SafeDiv"}
```

### FD_027

TREND_MOMENTUM：复权收盘价过去10个交易日的变化除以当时价格，描述区间价格动量。

表达式：`SafeDiv(Delta(adj_close,10),Lag(adj_close,10))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 5, "rolling_operators": 0}`；有效回看 10 交易日。

SHA-256：`cf7357bdf58434784b16707b7293f3b8519a45d25bd9a877bc7337f949113f2c`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"adj_close"}],"op":"Delta","param":10},{"args":[{"op":"Field","value":"adj_close"}],"op":"Lag","param":10}],"op":"SafeDiv"}
```

### FD_028

TREND_MOMENTUM：复权收盘价过去20个交易日的变化除以当时价格，描述区间价格动量。

表达式：`SafeDiv(Delta(adj_close,20),Lag(adj_close,20))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 5, "rolling_operators": 0}`；有效回看 20 交易日。

SHA-256：`089725b7c49ec62e37b90f38fb137a031ecfd94680648fb12303e48be1643d70`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"adj_close"}],"op":"Delta","param":20},{"args":[{"op":"Field","value":"adj_close"}],"op":"Lag","param":20}],"op":"SafeDiv"}
```

### FD_029

TREND_MOMENTUM：复权收盘价过去60个交易日的变化除以当时价格，描述区间价格动量。

表达式：`SafeDiv(Delta(adj_close,60),Lag(adj_close,60))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 5, "rolling_operators": 0}`；有效回看 60 交易日。

SHA-256：`c118ee7d937e2c07fc837c0e63450c29ab23972872e772a2daa37ad300c2d51b`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"adj_close"}],"op":"Delta","param":60},{"args":[{"op":"Field","value":"adj_close"}],"op":"Lag","param":60}],"op":"SafeDiv"}
```

### FD_030

RETURN_VOLATILITY：5日收益波动率相对上一交易日同窗口波动率，描述风险扩张或收缩。

表达式：`SafeDiv(RollingStd(RET1,5),Lag(RollingStd(RET1,5),1))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 4, "nodes": 6, "rolling_operators": 2}`；有效回看 6 交易日。

SHA-256：`f14075f303de76a3174a8b19d4b0b0544439e85f1fcd787fdc3ad7ed8634103d`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"RET1"}],"op":"RollingStd","param":5},{"args":[{"args":[{"op":"Field","value":"RET1"}],"op":"RollingStd","param":5}],"op":"Lag","param":1}],"op":"SafeDiv"}
```

### FD_031

RETURN_VOLATILITY：10日收益波动率相对上一交易日同窗口波动率，描述风险扩张或收缩。

表达式：`SafeDiv(RollingStd(RET1,10),Lag(RollingStd(RET1,10),1))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 4, "nodes": 6, "rolling_operators": 2}`；有效回看 11 交易日。

SHA-256：`fb258e3a8d94d83a70edaf38787261a6db629ec13bf06eb7431cbcabc87606ab`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"RET1"}],"op":"RollingStd","param":10},{"args":[{"args":[{"op":"Field","value":"RET1"}],"op":"RollingStd","param":10}],"op":"Lag","param":1}],"op":"SafeDiv"}
```

### FD_032

RETURN_VOLATILITY：20日收益波动率相对上一交易日同窗口波动率，描述风险扩张或收缩。

表达式：`SafeDiv(RollingStd(RET1,20),Lag(RollingStd(RET1,20),1))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 4, "nodes": 6, "rolling_operators": 2}`；有效回看 21 交易日。

SHA-256：`3d12dda62191a7ef7c5e0f9c0cc8eecc943c970c2d7ab2dfd8dbecbea907e7ee`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"RET1"}],"op":"RollingStd","param":20},{"args":[{"args":[{"op":"Field","value":"RET1"}],"op":"RollingStd","param":20}],"op":"Lag","param":1}],"op":"SafeDiv"}
```

### FD_033

RETURN_VOLATILITY：60日收益波动率相对上一交易日同窗口波动率，描述风险扩张或收缩。

表达式：`SafeDiv(RollingStd(RET1,60),Lag(RollingStd(RET1,60),1))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 4, "nodes": 6, "rolling_operators": 2}`；有效回看 61 交易日。

SHA-256：`bb039833a2d7278870c7a27207f32300b62a1d703a933e9388496a73a291be16`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"RET1"}],"op":"RollingStd","param":60},{"args":[{"args":[{"op":"Field","value":"RET1"}],"op":"RollingStd","param":60}],"op":"Lag","param":1}],"op":"SafeDiv"}
```

### FD_034

ACTIVITY_DYNAMICS：成交股数相对5个交易日前的比例变化，描述交易活动变化。

表达式：`SafeDiv(Delta(volume,5),Lag(volume,5))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 5, "rolling_operators": 0}`；有效回看 5 交易日。

SHA-256：`53da8efbb190688597da6410110dbe6208da0f57f9400fedcc0ada6ff0a29e85`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"volume"}],"op":"Delta","param":5},{"args":[{"op":"Field","value":"volume"}],"op":"Lag","param":5}],"op":"SafeDiv"}
```

### FD_035

ACTIVITY_DYNAMICS：成交股数相对10个交易日前的比例变化，描述交易活动变化。

表达式：`SafeDiv(Delta(volume,10),Lag(volume,10))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 5, "rolling_operators": 0}`；有效回看 10 交易日。

SHA-256：`34033ccd95584d8d52420edb20774ccb7016f40267b3ab6308d8b85bfa51b440`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"volume"}],"op":"Delta","param":10},{"args":[{"op":"Field","value":"volume"}],"op":"Lag","param":10}],"op":"SafeDiv"}
```

### FD_036

ACTIVITY_DYNAMICS：成交股数相对20个交易日前的比例变化，描述交易活动变化。

表达式：`SafeDiv(Delta(volume,20),Lag(volume,20))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 5, "rolling_operators": 0}`；有效回看 20 交易日。

SHA-256：`4f3d1c00b39d2a3d99c45f91a94f9e17a6af5b9bfca0e2e6ff4a5ac6586294ba`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"volume"}],"op":"Delta","param":20},{"args":[{"op":"Field","value":"volume"}],"op":"Lag","param":20}],"op":"SafeDiv"}
```

### FD_037

ACTIVITY_DYNAMICS：成交股数相对60个交易日前的比例变化，描述交易活动变化。

表达式：`SafeDiv(Delta(volume,60),Lag(volume,60))`

量纲：`{"is_dimensionless": true, "price_basis": null, "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 3, "nodes": 5, "rolling_operators": 0}`；有效回看 60 交易日。

SHA-256：`ad70b132370f5019a7febf3a92716d26d563642ba8ef28e4369e526169c6fae8`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"op":"Field","value":"volume"}],"op":"Delta","param":60},{"args":[{"op":"Field","value":"volume"}],"op":"Lag","param":60}],"op":"SafeDiv"}
```

### FD_038

PRICE_VOLUME_INTERACTION：5日价格动量与成交量相对5日均量的乘积，描述成交活动下的动量。

表达式：`Mul(SafeDiv(Delta(adj_close,5),Lag(adj_close,5)),SafeDiv(volume,RollingMean(volume,5)))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 4, "nodes": 10, "rolling_operators": 1}`；有效回看 5 交易日。

SHA-256：`80eea8937e7f5b7d167f4a7fb7ba0ad5e9ed5269670b33fe095f022ced413488`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"args":[{"op":"Field","value":"adj_close"}],"op":"Delta","param":5},{"args":[{"op":"Field","value":"adj_close"}],"op":"Lag","param":5}],"op":"SafeDiv"},{"args":[{"op":"Field","value":"volume"},{"args":[{"op":"Field","value":"volume"}],"op":"RollingMean","param":5}],"op":"SafeDiv"}],"op":"Mul"}
```

### FD_039

PRICE_VOLUME_INTERACTION：10日价格动量与成交量相对10日均量的乘积，描述成交活动下的动量。

表达式：`Mul(SafeDiv(Delta(adj_close,10),Lag(adj_close,10)),SafeDiv(volume,RollingMean(volume,10)))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 4, "nodes": 10, "rolling_operators": 1}`；有效回看 10 交易日。

SHA-256：`fc7234fc12790f5bfeb9de0ebb3a102cd16a96fd17d0eb79cee89b00b2bc0dea`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"args":[{"op":"Field","value":"adj_close"}],"op":"Delta","param":10},{"args":[{"op":"Field","value":"adj_close"}],"op":"Lag","param":10}],"op":"SafeDiv"},{"args":[{"op":"Field","value":"volume"},{"args":[{"op":"Field","value":"volume"}],"op":"RollingMean","param":10}],"op":"SafeDiv"}],"op":"Mul"}
```

### FD_040

PRICE_VOLUME_INTERACTION：20日价格动量与成交量相对20日均量的乘积，描述成交活动下的动量。

表达式：`Mul(SafeDiv(Delta(adj_close,20),Lag(adj_close,20)),SafeDiv(volume,RollingMean(volume,20)))`

量纲：`{"is_dimensionless": true, "price_basis": "HFQ", "units": {"adjusted_currency": 0, "raw_currency": 0, "shares": 0}, "value_type": "dimensionless"}`；复杂度：`{"depth": 4, "nodes": 10, "rolling_operators": 1}`；有效回看 20 交易日。

SHA-256：`cb2e70fb58c7bcc6d663544ef8d075a795c39813629704754830440b397e160d`。状态 SUCCESS；拒绝/失败原因 ``。

```json
{"args":[{"args":[{"args":[{"op":"Field","value":"adj_close"}],"op":"Delta","param":20},{"args":[{"op":"Field","value":"adj_close"}],"op":"Lag","param":20}],"op":"SafeDiv"},{"args":[{"op":"Field","value":"volume"},{"args":[{"op":"Field","value":"volume"}],"op":"RollingMean","param":20}],"op":"SafeDiv"}],"op":"Mul"}
```

## 数据状态、统计局限与后续前提

SYNTHETIC_TEST_ONLY 使用确定性模拟行情和业务日日历，含多证券、预热、缺日、零成交与极端值；不能解释为金融实证。私有真实数据只有本地原授权 manifest 字节 SHA、冻结版本、410 源哈希、旧收据及冻结历史标签全部通过才可读入；无下载、补价、换股或改写旧产物。

历史50股一年便利样本已参加以前研究，有幸存偏差、非 PIT 成分、HFQ 来源未正式核验、样本短与多候选事后筛选风险。它不是独立未观察测试集。这里不输出选优 p 值，不因最大 RankIC 宣称 Alpha。

接入更长历史数据须新增独立授权和冻结来源合同、明确证券身份与实际日历、无前视的 PIT 成分及状态、独立可重放 HFQ 资格与成熟标签；另设未参与生成/去重/阈值调整的验证与测试窗口。当前软件不更改任何正式金融门禁。

首版不需要遗传编程或实时 LLM 搜索：有限模板已验证软件闭环，而当前历史样本无法支持更大搜索空间的金融结论。下一步先增加独立合格数据与跨环境复现证据，再决定是否需要更大候选空间及多重筛选控制。

工程限制：P2——预算为预估操作/缓存上限与每个有界向量算子之间的单调时钟检查，不能抢占底层单个 NumPy/Pandas 调用；有界面板与 AST 防止无界执行，未依赖 Unix 信号。P2——浮点完全相同保证限于同一冻结 Python/依赖与源码字节环境；不同平台可发生舍入差异。P2——合成日历不是实际交易所日历。金融正式资格仍未取得，属于数据前提，不能由软件通过替代。

收据记录输入 SHA、开发区间、模板版本/种子/白名单/所有预算、表达式集合、源码逐文件哈希/Git身份、Python/依赖版本与完成原因；证券级因子、未来收益及供应商响应不会写入公开产物。
