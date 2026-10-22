Public derivative of historical report. Original SHA256: 93c549791da5cd79c03cfc917f4df7a8a080f49e481381730fee3ca061dcf5b7. Local references are redacted; historical conclusions are retained. This is not the original file or current execution evidence.

# CSMAR来源角色差距矩阵

实施前冻结，2026-10-21。NO LIVE MONEY。基线 cc13795d144592b360e560a9b979e183d6b01907。

|来源角色|现有代码能力|现有CSMAR证据|可实现范围|缺失事实|
|---|---|---|---|---|
|RAW|TDX_DAY_BYTES_V1重放|TRDNEW_Dalyr原件、字段字典、Filling|原件确定性重放及行定位|历史可得版本不由本地哈希证明|
|UNITS|UnitContract和知识时间检查|日线元/股、股、元；指数万股、万元|转换合同逐值验证；不解除生产UNITS|历史单位证据及available_at|
|REFERENCE|要求独立原始参考|CSMAR/TDX对照审计|不签发独立参考资格|独立完整四价和版本|
|CALENDAR|独立日历合同|IDX_Idxtrd观测日|候选观测日读取|独立交易所完整性及版本|
|BENCHMARK|独立字节来源要求|000905指数行情|候选原生数值与单位转换|独立身份及历史版本|
|IDENTITY|历史稳定身份与区间|TRDNEW_Co及历史别名材料|原生观察读取|稳定身份、端点、available_at|
|STATUS|逐日状态与上市合同|Trdsta和Filling|保留观察；填充价格隔离|完整独立历史状态及知识时间|
|PIT|逐日精确500和独立窗口|IDX_Chgsmp、IDX_Smprat|候选原生读取|起点完整500、实际生效和历史版本|
|ADJUSTMENT|事件重算及独立校验|TRD_AdjustFactor、Cptl、Capchg|原生因子及行为观察读取|实施/更正/前史、算法、独立锚点|
|TURNOVER|严格显式输入|量、市值、股本观察|保留原生字段；不推造换手率|合格历史分母和口径|
|LISTINGS|独立上市及身份资格|TRDNEW_Co|候选原生读取|历史身份和版本|
|ANCHOR|历史锚点合同|部分参考|不签发锚点资格|独立完整锚点及可得版本|

计划仅扩展RAW的特定代码拥有解析路径。其他角色维持fail-closed。此表是实施边界，最终实测见重放报告和清单，不是金融PASS。

最终实测：8类原件均完成声明范围的独立重放，既有真实资格引擎RAW阶段为PASS。UNITS等11个金融角色仍未绑定，SOURCE_BINDING与FORMAL仍为INCOMPLETE。旧冻结/发布保全拒绝新的资格代码版本，须独立评审登记，未修改历史控制条件。
