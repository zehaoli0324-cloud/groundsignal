#!/usr/bin/env python3
"""Build normalized organization, subcategory, and economic-value tables."""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return value or "unknown"


DOMAIN_IDS = {
    "临床医学与医学知识": "clinical_medicine",
    "生物医学NLP与证据检索": "biomedical_nlp_evidence",
    "生物科研Agent与实验工作流": "biomedical_research_agents",
    "遗传学与基因组学": "genetics_genomics",
    "功能基因组学与单细胞": "functional_genomics_single_cell",
    "蛋白质与结构生物学": "protein_structural_biology",
    "药物发现与分子机器学习": "drug_discovery_molecular_ml",
    "医学影像与数字病理": "medical_imaging_digital_pathology",
    "临床时间序列与医疗Agent": "clinical_agents_time_series",
    "科学复现与一般科学推理": "scientific_reproduction_reasoning",
}


SUBCATEGORY_IDS = {
    "医学考试与临床知识": "medical_exam_clinical_knowledge",
    "文献问答与证据检索": "literature_qa_evidence_retrieval",
    "生物医学检索与问答": "biomedical_retrieval_qa",
    "多任务医学知识评测": "multitask_medical_knowledge",
    "开放式医疗对话与安全评分": "open_health_dialogue_safety",
    "专家级医学推理与多模态诊疗": "expert_medical_multimodal_reasoning",
    "中文医疗综合评测": "chinese_medical_evaluation",
    "医疗安全与开放式健康对话": "healthcare_safety_open_dialogue",
    "医学考试与知识覆盖": "medical_exam_knowledge_coverage",
    "中文医学考试": "chinese_medical_exam",
    "医学多模态与影像推理": "medical_multimodal_imaging_reasoning",
    "实验任务与科研工具使用": "lab_tasks_research_tools",
    "生物信息学 notebook 分析": "bioinformatics_notebook_analysis",
    "真实组学数据分析": "real_omics_analysis",
    "生命科学研究工作流": "life_science_research_workflows",
    "统计遗传学与数量遗传学": "statistical_quantitative_genetics",
    "综合遗传学与功能基因组学": "integrated_genomics_functional_genomics",
    "医疗 Agent 与工具调用": "medical_agents_tool_use",
    "生物医学数据分析 Agent": "biomedical_data_analysis_agents",
    "论文复现与科学计算": "paper_reproduction_scientific_computing",
    "连续诊断与病程决策": "sequential_diagnosis_course_decision",
    "中文医学诊断": "chinese_medical_diagnosis",
    "蛋白质基础模型评测": "protein_foundation_models",
    "蛋白质结构评测": "protein_structure_evaluation",
    "蛋白质设计": "protein_design",
    "泛科学高难度推理": "general_science_reasoning",
    "药物发现与药物反应": "drug_discovery_drug_response",
    "分子性质预测": "molecular_property_prediction",
    "虚拟筛选": "virtual_screening",
    "分子对接与结构质量": "molecular_docking_structure_quality",
    "虚拟筛选基准": "virtual_screening_benchmark",
    "蛋白突变效应": "protein_mutation_effects",
    "蛋白表示与工程": "protein_representation_engineering",
    "蛋白质结构预测": "protein_structure_prediction",
    "连续结构预测评测": "continuous_structure_evaluation",
    "单细胞分析开放问题": "single_cell_open_problems",
    "单细胞数据整合": "single_cell_data_integration",
    "基因扰动预测": "gene_perturbation_prediction",
    "标准化医学影像": "standardized_medical_imaging",
    "胸部影像与临床报告": "chest_imaging_clinical_reports",
    "胸部 X 光": "chest_xray",
    "数字病理": "digital_pathology",
    "分子生成": "molecular_generation",
    "分子生成评测": "molecular_generation_evaluation",
}


def subcategory_id(value: str) -> str:
    return SUBCATEGORY_IDS.get(value, slug(value))


def organization_class(row: dict[str, str]) -> str:
    value = row["organization_type"].lower()
    if "ai company" in value or "company" in value or "biotech" in value:
        return "AI公司/产业研究实验室"
    if "university" in value:
        return "高校/大学实验室"
    if "consortium" in value:
        return "挑战联盟/研究联盟"
    if "community" in value:
        return "社区/开放生态"
    if "research institute" in value or "platform" in value or "nonprofit" in value:
        return "研究机构/平台"
    return "其他/待核验"


SUBCATEGORIES = {
    "medqa": ("临床医学与医学知识", "医学考试与临床知识", "医学问答", "临床决策软件、医学教育、模型评测", "C", 3.4),
    "medmcqa": ("临床医学与医学知识", "医学考试与临床知识", "医学问答", "医学教育、模型评测", "C", 3.3),
    "pubmedqa": ("生物医学NLP与证据检索", "文献问答与证据检索", "文献问答", "科研检索、医学知识服务、药企情报", "C", 4.0),
    "bioasq": ("生物医学NLP与证据检索", "生物医学检索与问答", "检索、问答、语义索引", "药企情报、科研知识服务、医学搜索", "C", 4.2),
    "multimedqa": ("临床医学与医学知识", "多任务医学知识评测", "多数据集医学问答", "医疗模型验收、医学教育、企业评测", "C", 4.0),
    "healthbench": ("临床医学与医学知识", "医疗安全与开放式健康对话", "开放式医疗对话、安全评分", "医疗安全、模型发布、企业验收", "D", 4.6),
    "medxpertqa": ("临床医学与医学知识", "专家级医学推理与多模态诊疗", "医学推理、多模态问答", "医院、医疗模型、医学教育", "D", 4.5),
    "medbench": ("临床医学与医学知识", "中文医疗综合评测", "中文医学问答", "中文医疗模型验收与采购", "D", 4.4),
    "cblue": ("生物医学NLP与证据检索", "中文生物医学NLP", "信息抽取、关系识别、问答", "医疗 NLP、知识库、数据服务", "C", 4.0),
    "cmb": ("临床医学与医学知识", "医学考试与知识覆盖", "大规模选择题", "医学教育、中文医疗模型评测", "C", 3.5),
    "cmexam": ("临床医学与医学知识", "中文医学考试", "医学考试选择题", "医学教育、模型评测", "C", 3.5),
    "gmai_mmbench": ("医学影像与数字病理", "医学多模态与影像推理", "医学图像/文本多模态", "影像 AI、医院部署、模型验收", "D", 4.5),
    "lab_bench": ("生物科研Agent与实验工作流", "实验任务与科研工具使用", "实验 protocol、数据库、文献和序列任务", "药企研发、科研软件、实验自动化", "D", 4.7),
    "bixbench": ("生物科研Agent与实验工作流", "生物信息学 notebook 分析", "代码、数据分析、科研推理", "药企研发、科研软件、算力平台", "D", 4.7),
    "biomysterybench": ("生物科研Agent与实验工作流", "真实组学数据分析", "组学分析、科研判断", "药企研发、转化医学、科研服务", "D", 4.6),
    "lifescibench": ("生物科研Agent与实验工作流", "生命科学研究工作流", "生命科学推理与工具使用", "科研 Agent、药物研发、知识服务", "D", 4.6),
    "genebench": ("遗传学与基因组学", "统计遗传学与数量遗传学", "遗传分析、基因组推理", "遗传检测、科研软件、模型评测", "D", 4.2),
    "genebench_pro": ("遗传学与基因组学", "综合遗传学与功能基因组学", "遗传学科研任务", "遗传检测、药物研发、科研 Agent", "D", 4.6),
    "healthagentbench": ("临床时间序列与医疗Agent", "医疗 Agent 与工具调用", "临床工作流、工具调用", "医院工作流、医疗软件、模型验收", "D", 4.7),
    "biomnibench_da": ("生物科研Agent与实验工作流", "生物医学数据分析 Agent", "真实数据分析工作流", "药企研发、CRO、科研平台", "D", 4.7),
    "paperbenchx": ("科学复现与一般科学推理", "论文复现与科学计算", "科学复现、仿真、代码和证据", "科研软件、企业研发、科学计算平台", "D", 4.1),
    "sequential_diagnosis": ("临床时间序列与医疗Agent", "连续诊断与病程决策", "多轮诊断、时间序列决策", "医院辅助决策、医疗 Agent", "D", 4.7),
    "msdiagnosis": ("临床医学与医学知识", "中文医学诊断", "医学诊断问答", "中文医疗模型和医院应用", "D", 4.2),
    "proteinbench": ("蛋白质与结构生物学", "蛋白质基础模型评测", "蛋白表示、结构和功能", "药企、蛋白工程、模型厂商", "D", 4.6),
    "pxmeter": ("蛋白质与结构生物学", "蛋白质结构评测", "结构预测和结构质量", "结构生物学、药物研发、模型厂商", "D", 4.6),
    "pxdesignbench": ("蛋白质与结构生物学", "蛋白质设计", "蛋白设计和生成", "抗体、酶工程、合成生物学", "D", 4.8),
    "supergpqa": ("科学复现与一般科学推理", "泛科学高难度推理", "专家级科学问答", "通用模型验收和科学 AI", "D", 4.1),
    "tdc": ("药物发现与分子机器学习", "药物发现与药物反应", "药物性质、反应和发现任务", "药企、CRO、药物研发平台", "D", 4.8),
    "moleculenet": ("药物发现与分子机器学习", "分子性质预测", "分子机器学习任务", "药物研发软件、科研平台", "C", 4.1),
    "lit_pcba": ("药物发现与分子机器学习", "虚拟筛选", "配体-靶点活性预测", "药企、CRO、虚拟筛选平台", "C", 4.6),
    "posebusters": ("药物发现与分子机器学习", "分子对接与结构质量", "对接姿态验证", "结构药物发现、软件验收", "C", 4.4),
    "dude_e": ("药物发现与分子机器学习", "虚拟筛选基准", "分子筛选和排序", "药企、CRO、化学信息学", "C", 4.3),
    "protein_gym": ("蛋白质与结构生物学", "蛋白突变效应", "蛋白 fitness 和突变效应", "蛋白工程、酶工程、抗体研发", "D", 4.8),
    "flip": ("蛋白质与结构生物学", "蛋白表示与工程", "蛋白 fitness、表示学习", "蛋白工程、模型训练和评测", "D", 4.6),
    "casp": ("蛋白质与结构生物学", "蛋白质结构预测", "盲测结构预测", "结构生物学、药物研发、模型验收", "C", 4.6),
    "cameo": ("蛋白质与结构生物学", "连续结构预测评测", "持续结构预测", "结构生物学、模型监测", "C", 4.4),
    "openproblems": ("功能基因组学与单细胞", "单细胞分析开放问题", "单细胞整合、预测和分析", "生物制药、转化医学、科研软件", "C", 4.5),
    "scib": ("功能基因组学与单细胞", "单细胞数据整合", "批次校正、整合质量", "单细胞平台、药企研发、科研软件", "C", 4.5),
    "gears": ("功能基因组学与单细胞", "基因扰动预测", "CRISPR/扰动后的表达预测", "药物靶点发现、功能基因组学", "D", 4.7),
    "medmnist": ("医学影像与数字病理", "标准化医学影像", "医学图像分类", "医学影像模型开发和教育", "C", 3.9),
    "mimic_cxr": ("医学影像与数字病理", "胸部影像与临床报告", "X 光和报告建模", "医院影像、临床 AI、模型训练", "C", 4.6),
    "chexpert": ("医学影像与数字病理", "胸部 X 光", "影像分类和报告相关任务", "医院影像、模型验收", "C", 4.6),
    "camelyon": ("医学影像与数字病理", "数字病理", "病理切片转移灶检测", "病理 AI、医院和药企研发", "C", 4.6),
    "guacamol": ("药物发现与分子机器学习", "分子生成", "分子生成与优化", "药物研发、CRO、模型平台", "C", 4.5),
    "moses": ("药物发现与分子机器学习", "分子生成评测", "生成质量和多样性", "药物研发、生成模型评测", "C", 4.2),
}


def value_stage(domain: str) -> str:
    if domain in {"临床医学与医学知识", "临床时间序列与医疗Agent", "医学影像与数字病理"}:
        return "临床决策/医疗服务"
    if domain in {"药物发现与分子机器学习", "蛋白质与结构生物学", "遗传学与基因组学", "功能基因组学与单细胞"}:
        return "药物研发/生物技术研发"
    if domain in {"生物科研Agent与实验工作流", "生物医学NLP与证据检索"}:
        return "科研生产力/知识服务"
    return "模型研发/科学计算基础设施"


def modality_for(task_type: str, domain: str) -> str:
    task = task_type.lower()
    if "image" in task or "multimodal" in task or domain == "医学影像与数字病理":
        return "image_or_multimodal"
    if "structure" in task or "protein" in task or domain == "蛋白质与结构生物学":
        return "sequence_structure"
    if "code" in task or "agent" in task or "workflow" in task or domain == "生物科研Agent与实验工作流":
        return "data_code_workflow"
    if "molecular" in task or "drug" in task or domain == "药物发现与分子机器学习":
        return "molecule_or_structure"
    return "text_or_tabular"


def buyer_segment(domain: str) -> str:
    groups = {
        "临床医学与医学知识": "医院;医疗模型厂商;医学教育",
        "生物医学NLP与证据检索": "药企;科研机构;知识服务商",
        "生物科研Agent与实验工作流": "药企;CRO;科研软件公司",
        "遗传学与基因组学": "检测公司;药企;科研软件公司",
        "功能基因组学与单细胞": "药企;生物技术公司;科研平台",
        "蛋白质与结构生物学": "药企;抗体/酶工程公司;模型厂商",
        "药物发现与分子机器学习": "药企;CRO;药物研发平台",
        "医学影像与数字病理": "医院;医疗器械公司;影像 AI 厂商",
        "临床时间序列与医疗Agent": "医院;医疗软件公司;模型厂商",
        "科学复现与一般科学推理": "科研软件公司;企业研发;算力平台",
    }
    return groups.get(domain, "研究机构;模型厂商")


def main() -> int:
    registry = {r["benchmark_id"]: r for r in read_csv("benchmark_registry.csv")}
    organizations = read_csv("benchmark_organization.csv")
    assessments = {r["benchmark_id"]: r for r in read_csv("benchmark_assessment.csv")}

    entity_rows: dict[str, dict[str, str]] = {}
    for row in organizations:
        name = row["primary_organization"]
        organization_id = slug(name)
        entity_rows.setdefault(organization_id, {
            "organization_id": organization_id,
            "canonical_name": name,
            "aliases": name,
            "region": row["region"],
            "organization_class": organization_class(row),
            "subclass": row["organization_type"],
            "lab_or_division": "",
            "parent_organization": "",
            "role": "creator_or_maintainer",
            "ownership_mode": row["ownership_mode"],
            "commercial_status": "unknown",
            "evidence_url": registry[row["benchmark_id"]]["official_url"],
            "evidence_date": "2026-10-14",
            "confidence": row["affiliation_confidence"],
            "notes": row["organization_notes"],
        })

    out = ROOT / "organization_entity.csv"
    fields = list(next(iter(entity_rows.values())).keys())
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(entity_rows.values(), key=lambda x: x["canonical_name"].lower()))

    mapping_rows = []
    value_rows = []
    for benchmark_id, values in SUBCATEGORIES.items():
        registry_row = registry[benchmark_id]
        assessment = assessments[benchmark_id]
        domain, subcategory, task_type, buyers, grade, score = values
        mapping_rows.append({
            "benchmark_id": benchmark_id,
            "name": registry_row["name"],
            "primary_domain_id": DOMAIN_IDS[domain],
            "primary_domain": domain,
            "subcategory_id": subcategory_id(subcategory),
            "primary_subcategory": subcategory,
            "related_registry_domain": registry_row["domain"],
            "coverage_mode": "benchmark_level_primary_mapping",
            "task_type": registry_row["task_type"],
            "modality": modality_for(registry_row["task_type"], domain),
            "economic_relevance_existing": assessment["economic_relevance"],
            "confidence": "provisional",
        })
        value_rows.append({
            "benchmark_id": benchmark_id,
            "subcategory_id": subcategory_id(subcategory),
            "organization_id": slug(next(r["primary_organization"] for r in organizations if r["benchmark_id"] == benchmark_id)),
            "value_chain_stage": value_stage(domain),
            "buyer_segment": buyers,
            "use_case": task_type,
            "decision_affected": "研发优先级;模型验收;临床或科研工作流" if domain != "临床医学与医学知识" else "诊疗支持;医学教育;模型验收",
            "estimated_cost_saved": "待验证",
            "data_scarcity_score": "待核验",
            "adoption_signal": assessment["public_usage_signal"],
            "commercial_signal": assessment["purchase_or_contract_signal"],
            "commercial_signal_type": "公开交易证据未披露",
            "public_amount": "未披露",
            "public_volume": "未披露",
            "evidence_url": registry_row["official_url"],
            "evidence_date": "2026-10-14",
            "evidence_grade": grade,
            "economic_potential_score": f"{score:.1f}",
            "score_type": "heuristic_potential_priority",
            "record_status": "provisional",
            "analyst_note": "分数表示潜在价值优先级，不代表收入、估值或已实现商业化。",
        })

    mapping_fields = list(mapping_rows[0].keys())
    with (ROOT / "benchmark_subcategory_mapping.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=mapping_fields)
        writer.writeheader()
        writer.writerows(mapping_rows)

    value_fields = list(value_rows[0].keys())
    with (ROOT / "benchmark_economic_value_evidence.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=value_fields)
        writer.writeheader()
        writer.writerows(value_rows)

    organization_by_benchmark = {row["benchmark_id"]: row for row in organizations}
    organization_entities = {row["organization_id"]: row for row in entity_rows.values()}
    assessment_by_benchmark = assessments
    snapshot_rows = []
    for row in mapping_rows:
        benchmark_id = row["benchmark_id"]
        registry_row = registry[benchmark_id]
        assessment = assessment_by_benchmark[benchmark_id]
        value = next(value for value in value_rows if value["benchmark_id"] == benchmark_id)
        organization = organization_by_benchmark[benchmark_id]
        snapshot_rows.append({
            "benchmark_id": benchmark_id,
            "name": row["name"],
            "organization_class": organization_entities[slug(organization["primary_organization"])] ["organization_class"],
            "primary_organization": organization["primary_organization"],
            "region": organization["region"],
            "primary_domain": row["primary_domain"],
            "primary_subcategory": row["primary_subcategory"],
            "question_status": registry_row["question_status"],
            "item_or_task_count": assessment["item_or_task_count"],
            "quality_score_1_5": assessment["quality_score_1_5"],
            "difficulty": assessment["difficulty"],
            "ranking_value": assessment["ranking_value"],
            "economic_relevance": assessment["economic_relevance"],
            "evidence_grade": value["evidence_grade"],
            "economic_potential_score": value["economic_potential_score"],
            "official_url": registry_row["official_url"],
        })
    snapshot_fields = list(snapshot_rows[0].keys())
    with (ROOT / "benchmark_investor_snapshot.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=snapshot_fields)
        writer.writeheader()
        writer.writerows(snapshot_rows)

    quality_rows = []
    commercial_rows = []
    for row in snapshot_rows:
        benchmark_id = row["benchmark_id"]
        assessment = assessments[benchmark_id]
        value = next(value for value in value_rows if value["benchmark_id"] == benchmark_id)
        quality_rows.append({
            "benchmark_id": benchmark_id,
            "name": row["name"],
            "primary_domain": row["primary_domain"],
            "primary_subcategory": row["primary_subcategory"],
            "item_or_task_count": row["item_or_task_count"],
            "quality_score_1_5": row["quality_score_1_5"],
            "quality_summary": assessment["quality_summary"],
            "difficulty": row["difficulty"],
            "sota_stress": assessment["sota_stress"],
            "ranking_value": row["ranking_value"],
            "public_usage_signal": assessment["public_usage_signal"],
            "usage_count_publicly_reported": assessment["usage_count_publicly_reported"],
            "runs_or_tool_calls_publicly_reported": assessment["runs_or_tool_calls_publicly_reported"],
            "evidence_status": assessment["evidence_status"],
            "next_measurement": assessment["next_measurement"],
        })
        commercial_rows.append({
            "benchmark_id": benchmark_id,
            "name": row["name"],
            "primary_domain": row["primary_domain"],
            "primary_subcategory": row["primary_subcategory"],
            "primary_organization": row["primary_organization"],
            "value_chain_stage": value["value_chain_stage"],
            "buyer_segment": value["buyer_segment"],
            "use_case": value["use_case"],
            "decision_affected": value["decision_affected"],
            "economic_relevance": row["economic_relevance"],
            "economic_potential_score": value["economic_potential_score"],
            "evidence_grade": value["evidence_grade"],
            "commercial_signal": value["commercial_signal"],
            "commercial_signal_type": value["commercial_signal_type"],
            "public_amount": value["public_amount"],
            "public_volume": value["public_volume"],
            "estimated_cost_saved": value["estimated_cost_saved"],
            "record_status": value["record_status"],
            "evidence_url": value["evidence_url"],
            "analyst_note": value["analyst_note"],
        })

    for filename, rows in [("benchmark_quality_snapshot.csv", quality_rows), ("benchmark_commercial_assessment.csv", commercial_rows)]:
        fields = list(rows[0].keys())
        with (ROOT / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    controlled_rows = [
        {"field": "question_status", "code": "public-download", "meaning": "公开下载", "usage_note": "通常可以按许可证整理本地副本"},
        {"field": "question_status", "code": "public-gated", "meaning": "公开但受门槛限制", "usage_note": "需要注册、申请或接受使用条款"},
        {"field": "question_status", "code": "paper-or-leaderboard", "meaning": "有论文/榜单但未取得完整题目", "usage_note": "不能把任务数当成已落地题目数"},
        {"field": "question_status", "code": "not-question-based", "meaning": "不是传统问答题", "usage_note": "输入数据、结构或测试案例构成评测对象"},
        {"field": "evidence_grade", "code": "A", "meaning": "公开合同、采购、授权或价格", "usage_note": "已实现商业价值的强证据"},
        {"field": "evidence_grade", "code": "B", "meaning": "官方产品集成、企业服务或正式合作", "usage_note": "可验证产业使用价值"},
        {"field": "evidence_grade", "code": "C", "meaning": "长期榜单、标准或多机构重复采用", "usage_note": "标准层影响力，不等于付费"},
        {"field": "evidence_grade", "code": "D", "meaning": "基于数据稀缺、决策影响和替代成本推断", "usage_note": "潜在价值，不等于已商业化"},
        {"field": "evidence_grade", "code": "E", "meaning": "证据不足", "usage_note": "仅作候选方向"},
        {"field": "record_status", "code": "provisional", "meaning": "初步整理", "usage_note": "需要继续补充来源、访谈或人工审计"},
        {"field": "score_type", "code": "heuristic_potential_priority", "meaning": "启发式潜在价值优先级", "usage_note": "不是收入、估值或市场规模"},
    ]
    with (ROOT / "controlled_vocabularies.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = list(controlled_rows[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(controlled_rows)

    question_counts: dict[str, Counter[str]] = {}
    question_sources = {
        "cmb": "CMB 题目级分类",
        "lab_bench": "LAB-Bench 记录级分类",
        "paperbenchx": "PaperBenchX 任务级分类",
    }
    taxonomy_path = ROOT / "data" / "normalized" / "biological_question_taxonomy.jsonl"
    with taxonomy_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = __import__("json").loads(line)
            question_counts.setdefault(item["benchmark_id"], Counter())[item["directness"]] += 1
    question_rows = []
    for benchmark_id, counts in sorted(question_counts.items()):
        question_rows.append({
            "benchmark_id": benchmark_id,
            "source_description": question_sources.get(benchmark_id, "题目级分类"),
            "record_count": str(sum(counts.values())),
            "direct_count": str(counts.get("直接", 0)),
            "related_count": str(counts.get("相关", 0)),
            "out_of_taxonomy_count": str(counts.get("不适用", 0)),
            "review_count": str(counts.get("未确定", 0)),
            "summary_file": "data/normalized/biological_question_taxonomy_summary.csv",
            "detail_file": "data/normalized/biological_question_taxonomy.jsonl",
            "reading_note": "先看 summary，再按 benchmark_id 和 directness 过滤 JSONL",
        })
    with (ROOT / "question_level_reading_index.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = list(question_rows[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(question_rows)

    counts = Counter(row["primary_domain"] for row in mapping_rows)
    print(f"organizations={len(entity_rows)} benchmarks={len(mapping_rows)}")
    for domain, count in counts.most_common():
        print(f"{count}\t{domain}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
