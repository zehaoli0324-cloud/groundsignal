# 生物医药 Benchmark 投资版图

更新时间：2026-10-14

本文件夹整理国内外生物医药 benchmark 的机构归属、子领域分类、题目级入口和经济价值证据，服务于 GroundSignal 的企业、产业链和投资研究。

## 推荐阅读

- `QUICKSTART.md`：按投资人、研究者和来源核验三种目的选择入口。
- `biomedical_benchmark_investor_memo_7p.pdf`：7 页投资人版概览。
- `benchmark_investor_snapshot.csv`：45 个 benchmark 的一行式总览。
- `benchmark_quality_snapshot.csv`：质量、难度、SOTA 压力和公开采用。
- `benchmark_commercial_assessment.csv`：买方、价值链、商业信号和潜在价值。
- `DATA_DICTIONARY.md`：字段解释、表之间的连接关系和可比性边界。

## 机构和子领域

- `organization_entity.csv`：39 个归一化机构实体；
- `benchmark_organization.csv`：benchmark 原始组织归属；
- `ORGANIZATION_CLASSIFICATION.md`：机构文字版归类；
- `benchmark_subcategory_mapping.csv`：45 个 benchmark 的一级领域和二级子分类；
- `ORGANIZATION_SUBCATEGORY_VALUE_PLAN.md`：分类和经济价值方法。

## 经济价值和来源

- `benchmark_economic_value_evidence.csv`：详细经济价值证据表；
- `benchmark_commercial_assessment.csv`：商业判断窄表；
- `controlled_vocabularies.csv`：状态、证据等级和分数编码；
- `benchmark_registry.csv`：官网、论文、代码、数据和许可证入口；
- `benchmark_assessment.csv`：质量、难度、SOTA 压力和产业相关性初评。

## 题目级资料

- `question_level_reading_index.csv`：题目级数据规模和阅读入口；
- `QUESTION_LEVEL_README.md`：题目级数据过滤方法；
- `PARALLEL_BIOMEDICINE_CLASSIFICATION.md`：遗传学图谱之外的医学题目分类说明。

## 口径

- 经济价值分数是潜在价值优先级，不是收入、估值或市场规模；
- 当前公开资料中没有系统披露 benchmark 级采购金额、客户数量或授权收入；
- `evidence_grade` 为 A/B 的项目才有较强的公开商业证据，C/D/E 需要继续核验；
- 原始大体量题库和中间压缩包不放入本目录，避免把不必要的大文件写入企业情报仓库。

## 可重复生成

`build_investor_tables.py` 可从项目内的 registry、organization 和 assessment 表重新生成窄表与索引。
