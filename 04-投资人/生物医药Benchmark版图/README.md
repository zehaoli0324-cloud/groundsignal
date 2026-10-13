# 生物医药 Benchmark 版图

**连接机构、评测任务与产业需求，理解 AI 在生物医药中已经被评测了什么，以及哪些能力值得进一步验证。**

这是 [GroundSignal](../../README.md) 的生物医药 AI 评测研究专题。项目从公开 Benchmark 出发，整理其创建与维护机构、领域覆盖、任务形式、质量初评和价值证据，为投资研究、模型评测和科研任务设计提供一个可追溯的入口。

**当前交付：45 条 Benchmark 登记记录、39 条机构实体记录、六张关联数据表及专题分析文档。** 当前阶段为研究型版图库；持续更新、交互查询与模型实跑评测是下一步建设方向。

[快速概览 PDF](biomedical_benchmark_investor_memo_7p.pdf) · [Benchmark 总表](benchmark_registry.csv) · [领域映射](benchmark_subcategory_mapping.csv) · [整理方法](ORGANIZATION_SUBCATEGORY_VALUE_PLAN.md) · [新调查报告 PDF](生物医药Benchmark_机构版图与实用价值调查报告_2026-10-13.pdf)

## 为什么做这份版图

生物医药 AI 的评测对象跨度很大：医学知识问答、开放式健康对话、组学数据分析、基因扰动预测、蛋白质设计和分子筛选，都可能被称为“生物医药 Benchmark”，但它们检验的能力、需要的证据和对应的工作流不同。

要判断一个方向是否值得投入，需要把几个问题连起来：

| 问题 | 本项目整理的内容 | 支持的判断 |
| --- | --- | --- |
| 谁在做？ | 创建者、维护者、联合机构、平台和社区 | 研究布局与机构生态 |
| 测什么？ | 主领域、子领域、任务类型和数据入口 | 能力覆盖与候选来源 |
| 测得怎么样？ | 规模口径、质量初评、难度、区分能力和复现需求 | 是否适合进一步审查或评测 |
| 对谁有用？ | 潜在买方、工作流、决策影响和采用证据 | 产业验证与研究优先级 |

项目希望将“一个 Benchmark 的名字”展开为一条可检查的研究线索：**来源是谁、任务是什么、结果能证明什么、与实际使用之间还需要补什么证据。**

## 当前版图

以下为 **2026-10-13 数据快照**，统计来自本目录 CSV。数字表示登记记录数，包含题库、数据集、任务套件、评测工具和持续挑战赛，不能相加为统一“总题量”。

| 主领域 | 记录数 | 当前登记项目 |
| --- | ---: | --- |
| 临床医学与医学知识 | 9 | MedQA-USMLE、MedMCQA、MultiMedQA、HealthBench、MedXpertQA、MedBench、CMB、CMExam、MSDiagnosis |
| 生物医学 NLP 与证据检索 | 3 | PubMedQA、BioASQ、CBLUE |
| 生物科研 Agent 与实验工作流 | 5 | LAB-Bench、BixBench、BioMysteryBench、LifeSciBench、BiomniBench-DA |
| 遗传学与基因组学 | 2 | GeneBench、GeneBench-Pro |
| 功能基因组学与单细胞 | 3 | Open Problems in Single-Cell Analysis、scIB、GEARS |
| 蛋白质与结构生物学 | 7 | ProteinBench、PXMeter、PXDesignBench、ProteinGym、FLIP/FLIP2、CASP、CAMEO |
| 药物发现与分子机器学习 | 7 | Therapeutics Data Commons、MoleculeNet、LIT-PCBA、PoseBusters、DUD-E、GuacaMol、MOSES |
| 医学影像与数字病理 | 5 | GMAI-MMBench、MedMNIST、MIMIC-CXR、CheXpert、CAMELYON |
| 临床时间序列与医疗 Agent | 2 | HealthAgentBench、Sequential Diagnosis Benchmark |
| 科学复现与一般科学推理 | 2 | PaperBenchX、SuperGPQA |
| **合计** | **45** | **每条记录按一个主领域计数** |

[分类方案](ORGANIZATION_SUBCATEGORY_VALUE_PLAN.md) 定义了 12 个一级类别，目前登记数据覆盖其中 10 类；“公共卫生与健康服务”和“数据质量、安全与评测基础设施”尚无项目作为主领域归入。次级领域保存在映射表中；广义科学项目的生物医药覆盖范围需按具体任务确认。

机构层同时收录公司研究团队、高校实验室、研究平台、挑战联盟和开放社区。39 条记录是当前机构实体表的规模，其中包含不同层级的组织描述；创建、维护、托管和采用关系应结合来源分别核验。

## 按机构浏览

机构分类与学科分类是两条独立索引：前者帮助理解研究布局和维护生态，后者帮助寻找实际任务。下表汇总当前登记项目，并用本次查阅的代表性官方来源补充角色说明。长尾归属仍有待核验项，完整作者与合作单位应以适用版本的论文和仓库为准。

### 公司、科研组织与产业团队

| 机构类别 | 机构 / 团队 | 登记项目 | 角色与重点 |
| --- | --- | --- | --- |
| 国内 AI 公司及产业团队 | ByteDance Research / Seed | ProteinBench、PXMeter、PXDesignBench、SuperGPQA | 模型团队发布评测与工具；蛋白预测、设计和一般科学推理。 |
| 国际 AI 公司及研究团队 | OpenAI | HealthBench、LifeSciBench、GeneBench、GeneBench-Pro | 健康安全、研究工作流和计算生物学；应按任务和发布版本分别记录。 |
| 国际 AI 公司及研究团队 | Anthropic | BioMysteryBench | 生物数据分析的客观结果评测；正式跑分需固定题集版本。 |
| 国际 AI 公司及研究团队 | Microsoft | HealthAgentBench、Sequential Diagnosis Benchmark | 分别为医疗 Agent 环境与逐步诊断；团队归属不能一概合并为同一实验室。 |
| 国际 AI 公司及研究团队 | Google Research | MultiMedQA | 评测套件汇编者；组件数据集仍有各自创建和维护机构。 |
| 科研组织与联合团队 | FutureHouse / 合作团队 | LAB-Bench、BixBench | 研究能力与开放式分析。BixBench 官方仓库署名 FutureHouse 与 ScienceMachine 合作。 |
| 评测研究与产业团队 | FreedomIntelligence、xbench 相关合作方、UniPat AI | CMB、BiomniBench-DA、PaperBenchX | 中文医学、过程分析与科学复现；具体合作角色按论文和官方说明核验。 |
| 生物技术及开放生态 | BenevolentAI、Molecular Sets 社区 | GuacaMol、MOSES | 登记表中的分子生成方向；企业起源不等于当前评测收费。 |

### 高校、研究平台与挑战社区

| 机构类别 | 机构 / 团队 | 登记项目 | 定位与核验重点 |
| --- | --- | --- | --- |
| 高校与研究机构联合 | 清华大学 / 上海 AI Lab；上海 AI Lab / OpenCompass | MedXpertQA；MedBench | 前者是联合学术项目；后者是版本化中文医疗评测平台。 |
| 高校实验室 | Harvard Zitnik Lab | Therapeutics Data Commons | 治疗相关任务平台；具体子任务的数据来源和许可需分别核验。 |
| 高校相关团队 | Stanford AIMI、SNAP 及相关学术合作 | CheXpert、GEARS、MedQA、FLIP/FLIP2 | AIMI 与 SNAP 是不同团队；MedQA 与 FLIP 的完整归属需按论文复核。 |
| 高校与数据平台 | MIT / PhysioNet / 临床合作方 | MIMIC-CXR | 数据创建、临床来源、托管与访问治理是不同角色。 |
| 高校与研究团队 | Theis Lab；上海交通大学相关团队；AIIMS；CUHK AIM | scIB；MedMNIST；MedMCQA；CMExam | 登记归属导航；未将所有来源逐项升级为已核验事实。 |
| 多机构学术合作 | Marks Lab / OATML 及合作者 | ProteinGym | 实验突变与临床变异评测，应区分测量性质与任务版本。 |
| 挑战联盟与持续评测 | BioASQ；CASP；CAMEO / SwissModel / SIB | BioASQ；CASP；CAMEO | 周期挑战与持续评测，适合研究标准、盲测和新版本比较。 |
| 开放社区与挑战生态 | Open Problems；DeepChem；国际病理合作社区 | Open Problems、MoleculeNet、CAMELYON | 提供社区方法比较和数据入口；托管平台与创建者不应混记。 |
| 尚需细化的归属 | 学术团队、结构/对接社区、国内医学社区 | PubMedQA、LIT-PCBA、PoseBusters、DUD-E、CBLUE、GMAI-MMBench、MSDiagnosis | 现有表包含笼统社区标签；应补全作者、单位和版本，不能直接统计成独立公司。 |

**机构归属更新说明：** [BixBench 官方仓库](https://github.com/Future-House/BixBench)明确署名 FutureHouse 与 ScienceMachine 合作，与当前 CSV 中的“FutureHouse / Edison Scientific”存在差异。本次更新在 README 与调查报告中记录差异，CSV 的逐项归一化需另行核验。Google 是 [MultiMedQA 的套件汇编者](https://research.google/pubs/large-language-models-encode-clinical-knowledge/)，组件数据集各有自己的创建与维护机构。Microsoft 两项评测的具体团队应分别核验。

进一步阅读：[OpenAI](https://openai.com/index/healthbench/) · [Anthropic](https://www.anthropic.com/research/Evaluating-Claude-For-Bioinformatics-With-BioMysteryBench) · [ByteDance ProteinBench](https://proteinbench.github.io/) · [清华 / 上海 AI Lab MedXpertQA](https://medxpertqa.github.io/) · [MedBench 平台更新](https://www.shlab.org.cn/news/5444287)。更多项目来源见[调查报告](生物医药Benchmark调查报告_2026-10-13.md)。

## 各大类 Benchmark 的实用意义

下面按“实际工作 → 影响什么决策 → 如何验证”解释用途。买方与收益描述是研究分析，是否改善实际工作需要相应用户数据、实验或受控试点验证。

| 大类 | 实际工作 | 能帮助做的决策 | 重点验证 |
| --- | --- | --- | --- |
| 临床医学与医学知识 | 医疗问答、医学教育、患者沟通与诊疗信息辅助。 | 选择基础模型、决定哪些问题交给人工、检查版本升级是否增加危险回答；先按人群和场景分层，再看总体平均分。 | 知识题正确率之外，报告严重错误率、遗漏关键建议的比例、专家一致性与置信度校准。HealthBench 的医生量表提供开放式评分实例。 |
| 生物医学 NLP 与证据检索 | 检索论文、抽取疾病与药物关系、回答证据问题、为综述和研发判断整理引用。 | 选检索系统和模型、决定某条关系是否进入知识库、识别哪些结论需要进一步检索；更适合支撑证据工作流的局部决策。 | 联合检查检索召回、证据与主张的对应性、引用定位、答案忠实度、时间有效性和无法回答时的弃答行为。 |
| 生物科研 Agent 与实验工作流 | 读取组学文件、检索数据库、编写分析脚本、执行工具、解释结果与形成可交接的研究材料。 | 选择哪些分析环节可以委托 AI，确定需要专家介入的位置，比较模型与工具配置，而不是只比较聊天回答。 | 同时记录科学结果、关键假设、数据质控、干净环境重跑、错误恢复与成本。BioMysteryBench 的客观元数据任务可用于验证结果 |
| 遗传学与基因组学 | 遗传关联、数量遗传学、组学统计与转化研究中的多阶段分析。 | 数据是否支持当前问题、该采用哪个模型、是否需要修改目标估计量、结论是否足以进入后续验证。 | 检查样本与批次结构、模型假设、效应估计、置信区间、多重检验和敏感性分析 |
| 功能基因组学与单细胞 | 单细胞整合、批次校正、标签迁移与扰动后的表达预测。 | 选整合方法、判断哪些候选扰动值得进入实验、筛查模型是否在新基因或新组合上失效；GEARS 提供扰动预测入口。[R17] | 以生物重复和条件为单位划分数据，比较无变化、均值和单扰动基线 |
| 蛋白质与结构生物学 | 结构预测、复合物评估、骨架与序列设计、突变效应排序。 | 选结构模型、筛除不合理设计、确定突变和候选的实验优先级。各子任务应独立比较，结构分数与功能分数不可直接合并。 | 结构误差、界面质量、物理合理性、序列多样性和实验功能分别报告 |
| 药物发现与分子机器学习 | 性质与 ADMET 预测、虚拟筛选、对接、分子生成和候选排序。 | 采用哪种排序或过滤方法、把有限实验预算分给哪些候选、如何设置弃答或适用域。 | 使用骨架、靶点或时间留出 |
| 医学影像与数字病理 | 胸片分类、图像与报告建模、病理切片识别及多模态问答。 | 选择适合目标设备、医院和病例分布的模型，决定哪些结果交由医生复核。小型标准化集适合工程初测，不能承担全部部署验收。 | 按患者与医院划分，检查关键病变灵敏度、特异度、校准、漏报和图文矛盾 |
| 临床时间序列与医疗 Agent | 逐步诊断中的问询、检查选择与假设更新，以及医疗数据和工具环境中的多步任务。 | 何时追问、何时停止检查、何时升级人工，哪些工具或数据操作可交给 AI。 | 结合最终结果、检查次数与成本、信息利用、时间泄漏、权限操作和安全升级 |
| 科学复现与一般科学推理 | 专家级问题求解，或将论文说明变成可重跑的代码、环境和结果。 | 选择适合论文复现和工具操作的模型，定位失败来自科学建模、软件运行还是结果验证。 | 固定数据与环境后清理旧输出，再从头执行 |
| 公共卫生与健康服务（待补） | 人群风险、资源配置与健康管理。 | 选择干预对象和配置有限资源；当前无独立主领域记录。 | 时间与地区留出、校准、干预对照和资源成本。 |
| 数据质量、安全与评测基础设施（待补） | 污染检测、评分审计、鲁棒性和版本回归。 | 判断不同分数是否可比较、是否能作为发布或研究依据。 | 正反例、等价解、数据隔离与干净环境重跑。 |

知识题、预测任务和工作流任务应分别解释：医学知识分数支持基础筛查；组学、蛋白与分子任务可支持方法选择和候选排序；Agent 与科学复现任务检验完整工作流程的执行与证据。结构置信度、对接合理性和离线准确率都需要进一步实验或场景验证，才能支持更下游的判断。

以“功能基因组学与单细胞”为例，评测的实用意义是判断整合方法是否保留生物差异，或扰动预测是否在未见条件上提供实验前排序增益。正式题目应加入无变化与均值基线、生物重复、批次诊断和留出条件，而不只报告整体表达相关性。

[完整调查报告 PDF](生物医药Benchmark_机构版图与实用价值调查报告_2026-10-13.pdf)详细展开十个已收录大类的使用者、决策、验收、价值与边界，并讨论两个待补类别、市场需求、竞争格局与最小试点。

## 从哪里开始

### 做投资或产业研究

先读 [投资人概览 PDF](biomedical_benchmark_investor_memo_7p.pdf)，再沿着“**领域 → 任务 → 工作流 → 买方 → 价值证据**”追查。

例如，研究蛋白质设计方向时，可以从 PXDesignBench 定位任务与官方入口，从机构表了解相关团队，再检查价值证据表中的候选筛选、实验验证和潜在买方描述。随后需要寻找具体的采用、实验效果或交易证据，确认这些潜在需求是否形成了实际价值。

建议的阅读顺序：

1. [领域映射表](benchmark_subcategory_mapping.csv)：选择关注的方向和任务。
2. [机构归属表](benchmark_organization.csv)与[机构实体表](organization_entity.csv)：理解相关组织与生态。
3. [价值证据表](benchmark_economic_value_evidence.csv)：检查买方、场景、证据等级和待验证判断。

### 选模型评测或科研出题来源

先筛领域和任务类型，再从 [Benchmark 总表](benchmark_registry.csv)进入官网、论文与代码，结合 [初评表](benchmark_assessment.csv)检查任务是否适合当前目标。

- **知识与对话任务**：关注数据污染、专家评分、安全边界与真实问题覆盖。
- **预测与设计任务**：关注数据划分、分布外泛化、指标含义与实验验证。
- **数据分析与 Agent 任务**：关注可执行环境、工具权限、预算、过程证据与结果复现。

纳入正式评测或题包前，需要固定版本、核验许可、审查评分方法并验证参考解。目录中的初评可用于候选筛选，正式结论需要任务级审查与运行证据。

### 看医学题库的细分类

[平行生物医药分类说明](PARALLEL_BIOMEDICINE_CLASSIFICATION.md)讨论遗传学图谱之外的医学题目分类，包括药学、护理、临床专科和公共卫生等。

该文档的题目级统计有独立范围。当前仓库快照未包含其中引用的逐题数据和分类脚本，因此这些题量应按原文口径理解，不能与本目录 45 条登记记录合并计算。

## 数据如何组织

数据拆为机构、Benchmark、领域和价值证据四层，以便分别维护事实、分类与分析判断。

| 文件 | 主要内容 | 查询与关联方式 |
| --- | --- | --- |
| [benchmark_registry.csv](benchmark_registry.csv) | 名称、维护者、任务类型、官网、论文、代码或数据入口、公开与许可状态 | 登记主表，主键为 `benchmark_id` |
| [benchmark_organization.csv](benchmark_organization.csv) | 主组织、联合机构或生态、组织类型、地区、归属方式与置信度 | 按 `benchmark_id` 关联；机构以名称描述 |
| [organization_entity.csv](organization_entity.csv) | 机构 ID、规范名称、别名、类别、部门、角色与来源 | 机构主表，主键为 `organization_id` |
| [benchmark_subcategory_mapping.csv](benchmark_subcategory_mapping.csv) | 主领域、主子领域、次级分类、覆盖方式与任务类型 | 按 `benchmark_id` 关联 |
| [benchmark_assessment.csv](benchmark_assessment.csv) | 规模、使用信号、质量初评、难度、SOTA 压力与待补测量 | 按 `benchmark_id` 关联 |
| [benchmark_economic_value_evidence.csv](benchmark_economic_value_evidence.csv) | 价值链、买方、场景、商业信号、证据链接、等级与潜在价值分数 | 按 `benchmark_id` 关联任务，按 `organization_id` 关联机构 |

当前五张 Benchmark 相关表各有 45 条记录，`benchmark_id` 集合一致；价值证据表中的机构 ID 均能关联到机构实体表。

当前领域映射每个 Benchmark 一行，次级分类存于字段中。稳定的子领域实体、多对多关系以及逐条机构角色证据，属于后续数据结构完善工作。

### 本地查看示例

克隆仓库并进入根目录后，运行以下标准库 Python 示例，无需额外依赖：

```bash
git clone https://github.com/zehaoli0324-cloud/groundsignal.git
cd groundsignal
```

```python
import csv
from pathlib import Path

root = Path("04-投资人/生物医药Benchmark版图")

def read_table(name):
    with (root / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

registry = {
    row["benchmark_id"]: row
    for row in read_table("benchmark_registry.csv")
}

for row in read_table("benchmark_subcategory_mapping.csv"):
    if row["primary_domain"] == "功能基因组学与单细胞":
        source = registry[row["benchmark_id"]]
        print(source["name"], row["primary_subcategory"],
              source["data_or_code_url"])
```

这个查询可用于定位单细胞与扰动方向的登记来源。它读取的是版图数据，候选任务能否复现需要进入各项目继续检查。

## 如何读质量与经济价值

### 质量判断

`benchmark_assessment.csv` 中的质量分数均带有 `provisional-` 前缀，表示研究初评。难度、SOTA 压力和排序价值也需要结合具体版本、数据划分、模型结果和运行条件核验。

机构归属置信度回答“创建或维护关系有多确定”；质量分数回答“评测本身是否可靠”。两者应分别判断。

### 价值判断

项目分别关注三个层次：

- **已实现商业价值**：合同、采购、授权、付费服务或其他交易证据。
- **可验证的使用价值**：科研采用、产品集成、模型验收或可测量的工作流收益。
- **潜在经济价值**：根据买方需求、决策影响、数据稀缺和替代成本提出的研究假设。

价值证据等级采用以下方法口径：

| 等级 | 需要支持的主张 | 当前表内条数 |
| --- | --- | ---: |
| A | 公开合同、采购、价格、授权或企业客户证据 | 0 |
| B | 官方产品集成、企业服务、付费 API、模型发布门槛或正式合作 | 0 |
| C | 多机构重复使用、长期排行榜、竞赛标准或广泛论文采用 | 22 |
| D | 基于数据稀缺、决策影响和替代成本的合理推断 | 23 |
| E | 证据不足，保留为候选方向 | 0 |

上述条数是当前表内标注的统计。核验时应检查来源是否直接支持相应主张：项目官网可支持项目身份，采用程度、商业合同和成本节省需要各自的证据。

当前 45 条记录的商业信号均为 `not_publicly_disclosed`，公开金额和使用量均标为“未披露”，成本节省均为“待验证”。

`economic_potential_score` 用于排列后续研究与商业验证的优先级。方法文档提出七个评分维度，但当前数据尚未提供全部维度的逐项分值，无法完整复算总分。**该分数不能解释为收入、估值、市场规模或投资回报。**

## 当前完成度与下一步

| 层次 | 已有内容 | 下一步要完成的工作 |
| --- | --- | --- |
| 来源登记 | 45 条记录及官网、论文、代码或数据入口 | 逐条固定版本，核验项目身份、访问与许可条件 |
| 机构整理 | 45 条归属记录、39 条机构实体记录 | 统一别名和上下级关系，拆开创建、维护、托管与采用角色 |
| 领域分类 | 10 个主领域及子领域描述 | 将 `direct_or_adjacent` 拆为明确覆盖关系，建立稳定分类 ID |
| 质量研究 | 规模、难度、质量和区分能力初评 | 增加任务级审查、参考解和版本化运行结果 |
| 价值研究 | 买方、场景、来源链接和潜在价值初评 | 将采用和商业主张拆成逐条证据，补充实际效果与交易来源 |
| 持续情报 | 可人工阅读与关联的 CSV 快照 | 接入变化记录、定期核验与筛选看板 |

其中，价值证据表有 40 条 `subcategory_id=unknown`，其余标签也尚未形成统一分类体系；领域映射的置信度均为 `provisional`。这些字段需要在下一阶段优先归一化。

实际复用数据时，还应逐条检查 `license_status`。公开可访问与允许再分发或商业使用是不同条件。`evidence_date` 的含义也需结合来源确认，不能直接作为发表日、交易日或最近一次联网核验时间。

## 与 GroundSignal 的关系

GroundSignal 面向可追溯、可比较和可持续更新的情报。本专题为生物医药评测方向提供基础数据：

| GroundSignal 对象 | 本专题的对应内容 | 接入重点 |
| --- | --- | --- |
| Entity | 机构与 Benchmark | 实体 ID、别名和角色归一化 |
| Claim / Relation | 机构归属、领域覆盖、采用及价值判断 | 拆成独立主张，绑定来源与核验状态 |
| Evidence | 官方入口、论文、代码和价值来源 | 补充主张对应的证据、采集时间和适用版本 |
| Event | 后续建设 | 追踪新版本、任务变化、评测结果及采用变化 |

长期目标是持续回答：**哪个方向出现了新评测、新能力或新采用证据，这些变化是否足以改变原有判断。**

## 文档导航与更新规则

| 文档 | 用途 |
| --- | --- |
| [机构版图与实用价值调查报告 PDF](生物医药Benchmark_机构版图与实用价值调查报告_2026-10-13.pdf) / [Markdown](生物医药Benchmark调查报告_2026-10-13.md) | 新调查报告：机构分类、各类用途、需求与商业验证、试点和实施路线 |
| [投资人概览 PDF](biomedical_benchmark_investor_memo_7p.pdf) | 快速阅读当前专题概览 |
| [组织、子领域与经济价值整理方案](ORGANIZATION_SUBCATEGORY_VALUE_PLAN.md) | 四层结构、12 类领域、价值评分与证据方法 |
| [Benchmark 组织分类](ORGANIZATION_CLASSIFICATION.md) | 按公司、研究机构、高校和挑战社区浏览 |
| [平行生物医药分类](PARALLEL_BIOMEDICINE_CLASSIFICATION.md) | 查看遗传学图谱之外的医学题目分类口径 |

部分文档引用了 `organization_summary.csv` 或题目级分类文件，这些文件未包含在当前仓库快照中；使用时以实际文件与各文档范围说明为准。

欢迎通过 [Issue](https://github.com/zehaoli0324-cloud/groundsignal/issues) 或 Pull Request 补充来源、修正归属和提供采用证据。

新增或修订记录时，请提供**官方来源、适用版本、核验日期、拟修改字段与理由**，并遵循以下顺序：

1. 登记项目和任务范围，核验访问及许可条件。
2. 复用机构 ID，分别记录组织角色与归属依据。
3. 按实际任务分类，明确评测单位和直接或邻近覆盖。
4. 将公开事实、分析判断和缺失信息分开标注。
5. 为采用、成本节省或商业化主张提供对应证据。
6. 检查 ID 唯一性、表间关联和统计口径，记录更新原因。

修改现有项目时保持 `benchmark_id` 稳定，并同步相关表。新增来源应先完成核验，再进入正式统计；质量结论和证据等级应随新增证据更新。

---

**让每一项生物医药 AI 能力判断，都能追溯到任务、数据、评测条件与实际使用证据。**
