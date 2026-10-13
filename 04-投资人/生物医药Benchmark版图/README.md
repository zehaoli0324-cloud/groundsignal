# 生物医药 Benchmark 版图

**连接机构、评测任务与产业需求，理解 AI 在生物医药中已经被评测了什么，以及哪些能力值得进一步验证。**

这是 [GroundSignal](../../README.md) 的生物医药 AI 评测研究专题。项目从公开 Benchmark 出发，整理其创建与维护机构、领域覆盖、任务形式、质量初评和价值证据，为投资研究、模型评测和科研任务设计提供一个可追溯的入口。

**当前交付：45 条 Benchmark 登记记录、39 条机构实体记录、六张关联数据表及专题分析文档。** 当前阶段为研究型版图库；持续更新、交互查询与模型实跑评测是下一步建设方向。

[快速概览 PDF](biomedical_benchmark_investor_memo_7p.pdf) · [Benchmark 总表](benchmark_registry.csv) · [领域映射](benchmark_subcategory_mapping.csv) · [整理方法](ORGANIZATION_SUBCATEGORY_VALUE_PLAN.md)

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
