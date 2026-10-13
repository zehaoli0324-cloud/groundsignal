# Benchmark 组织分类

更新时间：2026-10-12

## 分类原则

- `primary_organization`：最主要的创建者或维护者；
- `co_organizers_or_ecosystem`：联合机构、数据平台或使用生态；
- `organization_type`：公司、研究机构、大学实验室、社区或 challenge consortium；
- `ownership_mode`：创建/维护、联合创建、平台维护、外部采用或 legacy 社区维护；
- `affiliation_confidence`：对机构归属的置信度，不代表 benchmark 质量。

## 按组织看重点

### AI 公司/产业研究实验室

- **OpenAI**：HealthBench、LifeSciBench、GeneBench、GeneBench-Pro；偏医疗安全和生命科学科研工作流。
- **ByteDance Seed**：ProteinBench、PXMeter、PXDesignBench、SuperGPQA；偏蛋白质基础模型、结构/设计和泛科学推理。
- **Microsoft Research**：HealthAgentBench、Sequential Diagnosis Benchmark；偏医疗 Agent 和顺序诊断。
- **Anthropic**：BioMysteryBench；偏真实组学数据分析和生物科研判断。
- **Google Research**：MultiMedQA；偏医学知识与多数据集评测整合。
- **BenevolentAI**：GuacaMol；偏分子生成。
- **FreedomIntelligence**：CMB；偏中文医学知识和考试型评测。
- **xbench / Phylo / Humanlaya Data Lab**：BiomniBench-DA；偏过程级生物医学数据分析。
- **UniPat-AI**：PaperBenchX；偏论文复现和科学证据验证，其中一个公开任务是 CRISPRi 遗传互作分析。

### 大学和研究机构

- **清华 C3I + 上海 AI Lab**：MedXpertQA；专家级医学知识和多模态临床推理。
- **上海 AI Lab / OpenCompass**：MedBench；中文医疗大模型综合评测。
- **Harvard Zitnik Lab**：TDC；药物发现全流程机器学习任务。
- **Stanford**：MedQA、CheXpert、GEARS、FLIP 等相关项目。
- **MIT / PhysioNet**：MIMIC-CXR；临床影像和报告建模。
- **Stanford AIMI**：CheXpert；胸部 X 光分类和报告相关任务。
- **Shanghai Jiao Tong University**：MedMNIST；医学影像标准化数据集。
- **Theis Lab**：scIB；单细胞数据整合和批次效应评估。
- **Stanford SNAP**：GEARS；单细胞基因扰动预测。

### 社区和国际挑战组织

- **BioASQ**：生物医学信息检索和问答挑战。
- **CASP**：蛋白质结构预测盲测挑战。
- **CAMEO / SwissModel / SIB**：连续蛋白质结构预测评测。
- **Open Problems**：单细胞分析开放问题平台。
- **MoleculeNet / DeepChem**：分子机器学习社区基准。
- **CBLUE、GMAI-MMBench、MSDiagnosis**：国内学术和产业社区维护的中文医疗/医学多模态 benchmark。

## 机器可读文件

- `benchmark_organization.csv`：每个 benchmark 的组织归属；
- `organization_summary.csv`：按主组织汇总的数量和 benchmark ID。

