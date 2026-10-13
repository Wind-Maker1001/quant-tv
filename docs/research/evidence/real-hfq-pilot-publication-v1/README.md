# HFQ试点发布索引

**BLOCKED / UNVERIFIED，HFQ正式认证0日。**

- `source-index.json`记录11项已有来源的SHA、字节数、类型、上游及取得日期，不附原始行情。
- `claims-summary.json`只发布已有局部一致性及算法约束的派生汇总，不包含原始OHLC。
- `verification-summary.json`绑定原真实27项测试、原Windows2732项测试及发布版源码。

原本地提交和全部原证据保留私有，没有进入可推送分支祖先链。
未取得再分发授权的DAY、缓存、行情/因子原响应、机器路径、日志及临时文件均不上传。
公开SHA是索引及完整性线索，不能让缺原字节的远端checkout自行认证真实数据。
测试中的虚构数据始终SYNTHETIC_TEST_ONLY；不会升为真实参考或金融资格。
