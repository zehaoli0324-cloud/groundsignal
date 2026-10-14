# 数据字典与可读性说明

更新时间：2026-10-14

## 1. 推荐阅读层级

| 层级 | 文件 | 用途 |
|---|---|---|
| 快速总览 | `benchmark_investor_snapshot.csv` | 一行看完一个 benchmark，适合筛选和排序 |
| 来源登记 | `benchmark_registry.csv` | 找官网、论文、代码、数据和许可证 |
| 质量评估 | `benchmark_assessment.csv` | 看质量、难度、SOTA 压力、榜单价值 |
| 质量窄表 | `benchmark_quality_snapshot.csv` | 只保留质量和公开采用相关字段 |
| 机构归属 | `organization_entity.csv` | 看机构实体、地区、类型和角色 |
| 子领域映射 | `benchmark_subcategory_mapping.csv` | 看一级领域、二级子分类和映射置信度 |
| 经济价值 | `benchmark_economic_value_evidence.csv` | 看买方、价值链、商业信号和证据等级 |
| 商业窄表 | `benchmark_commercial_assessment.csv` | 只保留商业化判断相关字段 |
| 受控词表 | `controlled_vocabularies.csv` | 统一状态、证据和分数编码 |
| 题目级数据 | `data/normalized/*.jsonl` | 看单题/单任务分类，不与 benchmark 数量混用 |
| 题目索引 | `question_level_reading_index.csv` | 先看每个题目级数据集的规模和分类状态 |

## 2. 关键字段

### Benchmark 标识

- `benchmark_id`：稳定的内部唯一 ID，跨表连接键；
- `name`：benchmark 的展示名称；
- `version`：当前项目尚未对所有项目统一版本化，后续应增加版本字段；
- `item_or_task_count`：原始资料中的题目、任务或案例数量，可能是近似值。

### 机构字段

- `organization_id`：归一化机构实体 ID；
- `canonical_name`：标准名称；
- `organization_class`：AI 公司、大学实验室、研究机构/平台、挑战联盟或社区；
- `role`：创建者、维护者、托管方、数据提供方、采用者或商业用户；
- `affiliation_confidence` / `confidence`：归属判断的可信度，不代表 benchmark 质量。

### 子领域字段

- `primary_domain_id`：一级领域的稳定英文 ID；
- `primary_domain`：一级领域中文名称；
- `subcategory_id`：二级子分类的稳定英文 ID；
- `primary_subcategory`：二级子分类中文名称；
- `coverage_mode`：当前为 benchmark 级主分类，不代表每道题都属于该类别；
- `confidence`：当前映射是 provisional，题目级任务需要另外核验。

### 经济价值字段

- `value_chain_stage`：价值发生在科研生产力、药物研发、临床服务或模型基础设施的哪个环节；
- `buyer_segment`：潜在买方，不等于已付费客户；
- `decision_affected`：可能受到影响的决策；
- `data_scarcity_score`：数据稀缺性，目前统一标记为“待核验”，不把未调查内容伪装成量化结果；
- `adoption_signal`：公开论文、排行榜、挑战赛或模型报告中的采用信号；
- `commercial_signal`：公开交易、合作或付费信号，目前多数为 `not_publicly_disclosed`；
- `evidence_grade`：A/B 为可核验商业证据，C 为标准/重复采用，D 为合理推断，E 为证据不足；
- `economic_potential_score`：内部优先级分数，不是市场规模或收入预测。
- `score_type`：说明分数是启发式潜在价值优先级，不是交易金额或市场估值；
- `record_status`：`provisional` 表示需要补充来源、访谈或逐项审计。

## 3. 当前已知的可读性边界

- `benchmark_assessment.csv` 里的 `quality_score_1_5` 仍是初步人工评分，数值前有 `provisional-` 时不能理解为客观测量；
- `runs_or_tool_calls_publicly_reported` 只记录公开披露，不代表实际没有运行；
- `purchase_or_contract_signal` 为空或未披露，不代表没有商业使用；
- `organization_type` 是原始归属表字段，跨机构比较时优先使用 `organization_entity.csv` 的 `organization_class`；
- `biology_taxonomy_mapping.csv` 是 GeneBench-Pro 图谱映射，不能与平行医学分类表的一级领域直接合并统计。
