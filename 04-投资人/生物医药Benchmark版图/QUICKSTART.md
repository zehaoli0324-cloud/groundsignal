# 快速阅读入口

更新时间：2026-10-14

## 如果只有 5 分钟

先看：

1. `benchmark_investor_snapshot.csv`：45 个 benchmark 的一行式总览；
2. `ORGANIZATION_CLASSIFICATION.md`：国内外机构和大厂的文字版归类；
3. `benchmark_economic_value_evidence.csv`：买方、价值链、商业信号和潜在价值分数。

如果需要更窄的两种视图：

- `benchmark_quality_snapshot.csv`：只看质量、难度、SOTA 压力和公开采用；
- `benchmark_commercial_assessment.csv`：只看买方、价值链和商业证据。

## 如果想看投资机会

阅读顺序：

1. `ORGANIZATION_SUBCATEGORY_VALUE_PLAN.md`：先理解分类和经济价值口径；
2. `benchmark_investor_snapshot.csv`：按子领域、经济相关性和潜在价值筛选；
3. `benchmark_economic_value_evidence.csv`：检查买方、使用场景和证据等级；
4. `BENCHMARK_ASSESSMENT.md`：查看质量、难度、SOTA 压力和公开使用信号。

## 如果想核验来源

使用 `benchmark_registry.csv`，重点检查：

- `official_url`：官方主页或官方代码仓库；
- `paper_or_description_url`：论文或任务描述；
- `data_or_code_url`：数据或代码入口；
- `question_status`：数据是否可以直接下载；
- `license_status`：是否需要许可证复核。

## 如果想看题目级数据

- GeneBench-Pro 体系：`biology_taxonomy_mapping.csv`；
- 遗传学图谱之外的 CMB 题目：`data/normalized/parallel_biomedicine_taxonomy_summary.csv`；
- 逐题结果：`data/normalized/parallel_biomedicine_taxonomy.jsonl`；
- 题目级边界和人工复核说明：`QUESTION_TAXONOMY_STATUS.md`。
- 题目级阅读索引：`question_level_reading_index.csv`；
- 题目级过滤指南：`QUESTION_LEVEL_README.md`。

## 文件之间如何关联

```text
benchmark_id
  ├── benchmark_registry.csv
  ├── benchmark_assessment.csv
  ├── benchmark_organization.csv
  ├── benchmark_subcategory_mapping.csv
  ├── benchmark_economic_value_evidence.csv
  ├── benchmark_quality_snapshot.csv
  ├── benchmark_commercial_assessment.csv
  ├── controlled_vocabularies.csv
  ├── question_level_reading_index.csv
  └── benchmark_investor_snapshot.csv
```

`benchmark_id` 是唯一连接键。机构表通过 `organization_id` 连接经济价值证据表；子领域表通过 `subcategory_id` 连接经济价值证据表。

## 重要阅读提示

- `economic_potential_score` 是潜在价值优先级，不是收入、估值或市场规模；
- `evidence_grade` 为 `C/D/E` 的方向需要进一步做客户访谈或公开证据核验；
- benchmark 数量、题目数量、任务数量和评测案例数量不能直接横向相加；
- 通用医学题库的遗传学题量没有公开标签时，不应推断精确遗传学子集规模。
