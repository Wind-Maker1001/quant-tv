# 四模型软件就绪诊断

SYNTHETIC SOFTWARE ACCEPTANCE ONLY / NO LIVE MONEY / 非五年中证500研究结果

本场景软件验收：NOT_RUN；金融数据资格：Formal / Forward 均为 BLOCKED。

| 维度 | 检查 | 状态 | 原因 |
|---|---|---|---|
| 功能 | dataset_labels | PASS | 既有14因子Dataset；独立验证t+1/t+6标签数值及未成熟尾部 |
| 功能 | fold_isolation | PASS | 9个Fold；purge/embargo为0时实际标签exit边界仍隔离 |
| 功能 | pipeline/factor_score | PASS | 真实fit/predict实参隔离、Validation选参、Test单次预测及两级回测通过 |
| 功能 | pipeline/ridge | PASS | 真实fit/predict实参隔离、Validation选参、Test单次预测及两级回测通过 |
| 功能 | pipeline/lightgbm | PASS | 真实fit/predict实参隔离、Validation选参、Test单次预测及两级回测通过 |
| 功能 | pipeline/xgboost | PASS | 真实fit/predict实参隔离、Validation选参、Test单次预测及两级回测通过 |
| 功能 | four_model_cohort | PASS | 四模型共享日期、证券、Fold、标签身份、Train来源及运行身份 |
| 功能 | future_causality | NOT_RUN | 尚未执行 |
| 性能 | resources | PASS | 阶段耗时、原生RSS采样峰值与OS累计峰值已记录；无性能SLA |
| 性能 | scale_run | PASS | 500证券×1200交易日，显式执行 |
| 性能 | formal_parameter_stress | NOT_RUN | 诊断使用小候选配置；未执行正式YAML完整候选资源验收 |
| 可复现性 | input_identity | PASS | 七类输入内容、源代码、依赖、参数和线程设置均绑定SHA或版本 |
| 可复现性 | repeat_predictions | NOT_RUN | 尚未执行 |
| 统计合同 | historical_inference | PASS | 调用既有配对RankIC/HAC/MBB/固定三项Holm；可用性状态单独保留，不评选模型 |
| 统计合同 | statistical_counterexamples | PASS | 缺日/低coverage/不足60日/常数/序列相关/溢出及固定Holm反例通过 |
| 统计合同 | comparison_counterexamples | NOT_RUN | 尚未执行 |
| 数据资格 | Formal | BLOCKED | 仅合成输入；未提供本实验可验收的五年PIT/HFQ/状态证据及Forward激活证据 |
| 数据资格 | Forward | BLOCKED | 仅合成输入；未提供本实验可验收的五年PIT/HFQ/状态证据及Forward激活证据 |

资源数据见 resources.csv；嵌套阶段耗时包含子调用，不能相加。
sampled_peak_rss_bytes 为10ms采样的原生RSS峰值下界；process_high_watermark_bytes 为OS进程累计峰值。
events.jsonl 每阶段START/END落盘；硬终止时最后未结束的START提供失败位置。
