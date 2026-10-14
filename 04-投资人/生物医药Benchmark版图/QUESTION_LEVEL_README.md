# 题目级数据阅读指南

更新时间：2026-10-14

## 推荐顺序

1. 先看 `question_level_reading_index.csv`，确认每个 benchmark 的记录量和分类状态；
2. 再看 `data/normalized/biological_question_taxonomy_summary.csv`，按领域和 directness 看汇总；
3. 最后用 `data/normalized/biological_question_taxonomy.jsonl` 做逐条筛选。

## directness 的含义

| 值 | 含义 | 阅读方式 |
|---|---|---|
| `直接` | 题目/任务目标明确属于 GeneBench-Pro 图谱 | 可以作为直接覆盖样本，但仍需检查版本和标签质量 |
| `相关` | 使用相近数据、方法或对象，但不是完整遗传学研究问题 | 作为邻近任务，不要直接计入核心题数 |
| `不适用` | 不属于图片中的遗传学/计算生物学图谱 | 转到平行医学或其他科学分类 |
| `未确定` | 规则无法可靠判断 | 进入人工复核队列 |

## 当前题目级范围

- `CMB`：280,839 条，其中 272,674 条转入平行医学分类；
- `LAB-Bench`：1,967 条公开记录，主要是相关或待复核任务；
- `PaperBenchX`：12 个任务，其中 1 个功能基因组学任务，11 个为其他科学任务。

JSONL 适合程序处理，不建议直接用文本编辑器打开全部文件。人工抽样时优先按 `benchmark_id`、`directness`、一级领域和 `source_file` 过滤。
