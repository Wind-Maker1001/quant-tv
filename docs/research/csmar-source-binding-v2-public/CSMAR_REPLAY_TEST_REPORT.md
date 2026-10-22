Public derivative of historical report. Original SHA256: 46f6898e65523c516742dbfed204e0416ad57088449acb6deb0adcc2e8de662d. Local references are redacted; historical conclusions are retained. This is not the original file or current execution evidence.

# CSMAR原件重放与回归报告

2026-10-21。NO LIVE MONEY。

最终实现指纹：`6f8162caa5fa722133fc6b1292f20dd81b4ce49f0db98b90ecb2a657ae31cd6d`。环境：Python 3.9.25 / pandas 2.2.3 / PyArrow 17.0.0。

|真实表|完整扫描记录|选中记录|独立重放|
|---|---:|---:|---|
|TRDNEW_Dalyr|1000000|5|三表精确一致|
|IDX_Idxtrd|1000000|5|三表精确一致|
|TRD_AdjustFactor|62523|9|三表精确一致|
|TRDNEW_Co|6025|1|三表精确一致|
|TRDNEW_Cptl|72305|9|三表精确一致|
|TRDNEW_Capchg|144074|6|三表精确一致|
|IDX_Chgsmp|610|408|三表精确一致|
|IDX_Smprat|1000000|4000|三表精确一致|

日线及000905指数选区为2021-09-13至2021-09-17、分别000001和000905；其他选区及全部原件、成员、字典和规范/native/lineage哈希见evidence/validation-summary.json。IDX_Smprat保留000906原生标识，不能作为中证500成员。所有三表独立重放精确哈希一致，由此得到规范数值差异0；没有对比候选表与自身自哈希。

使用真实不完整QualificationInputs经原publish_qualification发布并再加载；RAW=PASS，其余五阶段INCOMPLETE，synthetic_only=false，formal_admission=false，execution_admission=false。包大小28068字节；未复制大型ZIP，只复制引用与局部小表。原件、解析版本或引用变化使重放拒绝。

最终相关回归：464 passed、0 failed、0 errors、0 skipped，191.46秒。包含新增62项适配器测试、来源重放、Local Provider、金融资格、PIT、复权及统一准入边界。

广义回归：3854 passed、19 failed、3 errors、0 skipped，2333.33秒；另外2个network用例由原pytest配置排除。该轮覆盖research、market_admission、model_readiness、market_structure、minute_data、evidence。它在开发中版本启动；最终版本另行完成上述464项及全部真实重放，不能把这轮称为最终HEAD全量通过。

实际失败列表及错误消息保存在validation-summary.json和regression-junit.xml。旧冻结/历史发布保全未登记新的market_qualification.py代码版本，会拒绝本轮修改；CSMAR_SOURCE_CHANGE_REVIEW.json只提交精确待审字节，不自行授权。没有改历史收据、旧测试或控制pin。当前不能宣称CI全绿。

广义回归中的3个readiness初始化错误，是新增源码尚未提交到HEAD所致。代码提交后单独重跑readiness与source_identity：24 passed、0 failed、0 errors，84.64秒；原3项已通过，不更改原失败JUnit。

基线相关测试162 passed、0 failed；首次相关回归453 passed、0 failed。另有历史发布诊断17 failed/91 passed及冻结诊断1 failed。各轮有重叠，不相加作为唯一测试总量。最终静态检查：323个Python文件编译及flake8 E9/F63/F7/F82通过；git diff --check通过。远端最终分支CI未执行，本任务未推送。

既有审计13份输入中9份与旧DELIVERY_MANIFEST字节哈希一致；其余4份在该旧清单无独立哈希条目，本轮仅新固定其实际哈希，状态NOT_BOUND_IN_DELIVERY，不冒充旧认证。47份原件大小/mtime前后相同，8份实际使用ZIP在重放中完整重算SHA；未重做全库1亿行审计。

私有原始行、引用、来源授权登记、失败轮次日志及完整命令收据位于任务独立临时根，不进入Git。完整64字符哈希、环境版本、各轮命令及后续可复现CLI见清单和实施说明。
