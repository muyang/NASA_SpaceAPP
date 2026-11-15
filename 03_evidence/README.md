# 依据导航｜按汇报主张查证

|编号|支持的主张|最终结果表|原始依据／复现位置|
|---|---|---|---|
|E1|Marsden 两年／三年系统观测差值|`contrast_summary.csv`、`marsden_annual_contrasts.csv`、`contrast_backtest_metrics.csv`|`../04_reproduce/case-study/public-field-validation/`；相邻 boone-v2 产量输入与冻结协议|
|E2|黑麦真实农场结果及缺口|`pfi_2022_farm_summary.csv`|public-field-validation 原报告、转录、sources.json；不得重造原始条带|
|E3|最新田块诊断误差与准入门槛|`field_replay_evaluation.json`、`admission_gates.json`|`../04_reproduce/case-study/field-admission-v2/`，原始土壤／日志、协议、逐次输出、代码与散列|
|E4|六县迁移、实际轮作与用途差异|`county_evidence_cards.csv`、`review_metrics.csv`、`review_process_diagnostics.csv`、`rotation_transition_summary.csv`|`Brief_Crop_Rotation_Six_Counties.md`；完整县域输入与历史模型实验在 `../../repo`，本包未重复全部候选模拟|
|E5|时间留出与偏差迁移|`historical_validation_series.csv`、`historical_bias_transfer.csv`|技能按原表读取；这是历史诊断，不是前瞻性验证|
|E6|历史财务点估计与价格敏感性|`historical_financial_point_order.csv`、`historical_stress_order_counts.csv`|field-admission-v2 中的论文原件、转录和经济分析代码；不能视为完整 CBA|
|E7|全国相似性数据来源覆盖|`conus_county_screening.csv`|本表标签计数为 POWER 885／IDW 2216／锚点 6；只作为扩展范围说明，不作预测或推荐地图|

`Field_Admission_Validation_Report_CN.md` 是详细方法附件；`Farmer_Usability_Test_Protocol_CN.md` 是尚待执行的测试方案。`REFERENCES.md` 列主要论文和来源，`RIGHTS.md` 保留第三方权利边界。整个 `repo2` 的文件追溯见 `manifest.json`。

本包没有复制 6,000 多条自动提取 URL、所有候选校准输出或多个历史版本。若同行需要县域全流程审计，转到完整档案 `../../repo`；不要把本包的最小复现范围说成已覆盖所有早期实验。
