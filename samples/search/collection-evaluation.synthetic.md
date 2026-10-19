# GroundSignal 采集评测

- 状态：SYNTHETIC_ONLY
- 决策：NOT_READY
- run SHA：fa52609d8dfb25e1c7107a4c0e444bbac653cde3bef20089d5ce63aaaf93db65
- benchmark SHA：0218c8ecb4f30e4d933386cda94cbc4ce3935d9ca4d1fd0c552f49ad04c7fcdb

指标限于明确定义的参考集；未知项保持 null。合成数据不证明真实模型效果。

| 门槛 | 状态 | 实际值 | 阈值 |
|---|---|---:|---:|
| reference_sample_size | MET | 4 | 3 |
| gold_claim_sample_size | FAILED | 4 | 100 |
| retrieval_recall | FAILED | 0.75 | 0.8 |
| rank_judgment_coverage | MET | 1.0 | 0.8 |
| extraction_precision | MET | 1.0 | 0.95 |
| end_to_end_recall | FAILED | 0.75 | 0.8 |
| candidate_label_coverage | MET | 1.0 | 1 |
| human_review_coverage | FAILED | 0.0 | 1 |
| retrieval_recall:downstream | MET | 1.0 | 0.8 |
| retrieval_recall:investors | MET | 1.0 | 0.8 |
| retrieval_recall:products | MET | 1.0 | 0.8 |
| retrieval_recall:capacity | FAILED | 0.0 | 0.8 |
| retrieval_recall:counterevidence | MET | 1.0 | 0.8 |
| high_risk_review_coverage | FAILED | 0.0 | 1 |
| critical_error_reviews | UNASSESSED | None | 0 |
| unanimous_human_correctness | UNASSESSED | None | 1 |
| human_gold_disagreements | UNASSESSED | None | 0 |
| budget_breaches | MET | 0 | 0 |
| missing_required_reference_groups | FAILED | 1 | 0 |
| declared_permission_violations | MET | 0 | 0 |
| permission_declaration_completeness | FAILED | 0 | 1 |
| live_run | FAILED | 0 | 1 |
| adjudicated_reference | MET | 1 | 1 |

分层指标、分母与已知缺口见 evaluation.json / metrics.csv。
权限检查仅核对声明，不阻止访问或证明合法性；审核身份未进行签名认证。
