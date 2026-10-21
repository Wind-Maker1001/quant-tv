Public derivative of historical report. Original SHA256: 797ffee4dd8524cb82cc700015698c93b4a4d0631f7f45f11d7b3dd3dd11ed45. Local references are redacted; historical conclusions are retained. This is not the original file or current execution evidence.

# CSMAR原生字段及单位合同

2026-10-21。NO LIVE MONEY。原件DES精确SHA允许清单见profiles.py；未知版本拒绝，不能凭字段名或Excel显示格式推断。原生列、说明行、单位行保留；实际CSMAR声明的A列dimension不代表真实列数，读取实际cell坐标。

|原生表/字段|原生单位与语义依据|候选字段/单位|转换|
|---|---|---|---|
|TRDNEW_Dalyr.Stkcd|DES：交易所证券代码|symbol|严格六位字符串；不补前导零|
|Markettype|DES：1/32上证A，4/16深证A|SH/SZ后缀、CNY|Decimal精确整数枚举；其他市场或币种拒绝|
|Trddt|DES：YYYY-MM-DD|date|严格实际日期，无日偏移，不接受Excel序列日期|
|Opnprc/Hiprc/Loprc/Clsprc|单位行元/股，DES确认A股人民币|open/high/low/close，CNY/share|Decimal乘1，再转float64；原始词法值另存|
|Dnshrtrd|股|volume，shares|乘1，非负整数且float64可精确表达|
|Dnvaltrd|元，DES确认A股人民币|amount，CNY|乘1，不填缺失|
|Filling|DES：0真实未填充，1/2供应商填充|原生观察及RAW隔离|1/2对应四价NaN，原生价格仍保留|
|Trdsta|DES：1—16交易/ST等状态|原生观察|不能映射成0/1停复牌资格|
|Dsmvosd等市值|千元及多个口径|仅原生列|不生成合格换手率或历史股本|
|IDX_Idxtrd.Indexcd/Idxtrd09|交易所指数代码/中文简称|000905.SH|必须同时000905和中证500；无替代指数|
|Idxtrd01|YYYY-MM-DD|date|严格原日|
|Idxtrd02—05|没有单位，DES为指数点位|OHLC，index_points|乘1；不冒充股票CNY/share|
|Idxtrd06|万股|volume，shares|Decimal乘10000|
|Idxtrd07|万元，DES人民币|amount，CNY|Decimal乘10000|
|Idxtrd08|%|原生观察|不混入比例；本轮未规范投影收益率|
|TRD_AdjustFactor.TradingDate/Symbol|原生日期/代码|原生列及行定位|日期无平移；代码不推断交易所或稳定身份|
|FwardFactor/BwardFactor|DES价格比公式|原生正有限数值观察|不推造事件、锚点、HFQ或available_at|
|CumulateFwardFactor/CumulateBwardFactor|DES累计乘积|原生正有限数值观察|基准、历史算法资格保持UNKNOWN|
|TRDNEW_Co|公司及代码上市等原生资料|全部原生列|不生成完整IdentitySnapshot或历史知识端点|
|TRDNEW_Cptl|分配类型、公告/除权/到账、每股比率|全部原生列|Amount元/股依事件类型，不自动进入CorporateAction|
|TRDNEW_Capchg|股本变动日期、类型、股数|全部原生列|不认证历史股本可得性|
|IDX_Chgsmp|供应商变更日、公告日、成员、动作|全部原生列|不把供应商日期当真实生效/知识时间|
|IDX_Smprat|原生指数、截止日、成员、权重(%)|全部原生列|不把000906换成000905，不签发PIT|

缺日期/代码/必需单位、非法数值、重复或缺失主键、公式单元格、未知状态、非正交易价、不合理OHLC、未填充零成交均拒绝相关规范投影。空值、-9666等不能默认为0或1；未获得明确语义的扩展字段留在原生表，不进入正式投影。原生日数值字符串按Decimal精确缩放，float64是当前规范数值表示，词法精度保留在native.parquet及行摘要，不宣称二进制浮点无表示误差。

主键逐表写在profiles.PRIMARY_KEYS，所有选中记录跨sheet检查。完整原件和成员字节重算、预期sheet行数检查不等同全部供应商分卷齐全。稀疏说明/单位行允许尾部空格列缺失并显式补None；数据空行、额外未声明列或缺失三行元数据拒绝。
