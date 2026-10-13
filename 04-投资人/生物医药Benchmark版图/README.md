# 生物医药 Benchmark 版图

**把“谁在做评测、评测什么、如何评测、对谁有价值”连接起来，形成可追溯的生物医药 AI 研究与产业分析入口。**

本项目是 [GroundSignal](../../README.md) 的生物医药 Benchmark 专题，面向投资研究、模型评测和科研任务设计，将分散的公开基准整理为可关联的机构、任务、子领域与价值证据。

它围绕四个问题展开：

- **机构版图**：哪些公司、高校、实验室和社区在创建或维护 Benchmark？
- **能力版图**：现有评测覆盖哪些临床与科研任务，采用什么数据和评测形式？
- **评测价值**：一个 Benchmark 能否区分模型能力，质量、难度和复现条件如何？
- **产业价值**：任务对应哪些买方和工作流，价值判断有哪些公开证据支持？

**当前阶段：研究型版图库与初步分析材料。** 现有成果为 CSV 数据表、分类说明和投资人概览；自动更新、交互看板和模型执行评测属于后续建设方向。

[投资人概览 PDF](biomedical_benchmark_investor_memo_7p.pdf) · [Benchmark 总表](benchmark_registry.csv) · [子领域映射](benchmark_subcategory_mapping.csv) · [经济价值证据](benchmark_economic_value_evidence.csv)

## 当前收录

数据快照：**2026-10-13**。统计以本目录 CSV 为准。

| 项目 | 当前规模 | 统计口径 |
| --- | ---: | --- |
| Benchmark 登记记录 | 45 | 按 `benchmark_id` 去重 |
| 机构实体记录 | 39 | 按 `organization_id` 去重，包含实验室、联盟和社区记录 |
| 已覆盖一级领域 | 10 | 按子领域映射表中的 `primary_domain` 统计 |
| 机构归属、子领域映射、质量初评、价值证据 | 各 45 条 | 当前各表均覆盖全部登记记录 |
| 经济价值证据等级 | C 级 22 条、D 级 23 条 | 表内初步标注，仍需逐项核验 |
| Benchmark 级公开交易金额 | 45 条均标注“未披露” | 不能据此判断实际收入或不存在商业价值 |

45 条记录包含问答题库、任务集合、数据集、评测工具、预测任务和持续挑战赛。它们的评测单位不同，不能简单相加为“总题量”，也不能按题量直接排名。

### 覆盖领域

下表使用当前主领域标签，每条记录计入一个主领域；代表项目仅用于导航。

| 一级领域 | 记录数 | 代表项目 |
| --- | ---: | --- |
| 临床医学与医学知识 | 9 | MedQA、HealthBench、MedXpertQA、CMB |
| 生物医学 NLP 与证据检索 | 3 | PubMedQA、BioASQ、CBLUE |
| 医学影像与数字病理 | 5 | GMAI-MMBench、MedMNIST、MIMIC-CXR、CAMELYON |
| 生物科研 Agent 与实验工作流 | 5 | LAB-Bench、BixBench、BioMysteryBench、BiomniBench-DA |
| 遗传学与基因组学 | 2 | GeneBench、GeneBench-Pro |
| 临床时间序列与医疗 Agent | 2 | HealthAgentBench、Sequential Diagnosis Benchmark |
| 科学复现与一般科学推理 | 2 | PaperBenchX、SuperGPQA |
| 蛋白质与结构生物学 | 7 | ProteinBench、PXMeter、PXDesignBench、ProteinGym、CASP |
| 药物发现与分子机器学习 | 7 | TDC、MoleculeNet、LIT-PCBA、PoseBusters、GuacaMol |
| 功能基因组学与单细胞 | 3 | Open Problems、scIB、GEARS |
| **合计** | **45** | |

完整分类方案提出了 12 个一级类别，当前数据覆盖其中 10 类。“公共卫生与健康服务”和“数据质量、安全与评测基础设施”尚无项目作为主领域归入。广义科学基准中只有部分任务属于生物医药，相关范围需要结合任务说明确认。

## 如何使用

### 投资与产业研究

先读 [投资人概览](biomedical_benchmark_investor_memo_7p.pdf)，再通过 [机构实体表](organization_entity.csv) 和 [机构归属表](benchmark_organization.csv) 找到相关组织，最后查看 [经济价值证据表](benchmark_economic_value_evidence.csv)。

研究时沿着“**子领域 → 工作流 → 潜在买方 → 采用或交易证据**”展开。例如，蛋白质设计任务可进一步研究候选筛选和实验验证场景，科研 Agent 任务可进一步研究分析工作流和专家时间成本。买方与节省成本的描述需要实际采用、测量或交易证据支持。

### 模型评测与能力分析

先在 [子领域映射表](benchmark_subcategory_mapping.csv) 中筛选任务，再从 [登记表](benchmark_registry.csv) 进入官网、论文、代码和数据入口，结合 [初评表](benchmark_assessment.csv) 检查题量口径、质量、难度、SOTA 压力及待补证据。

正式比较模型前，应固定 Benchmark 版本、数据划分、评分方法、工具权限和运行预算。知识问答、数据分析和多步 Agent 任务应分别比较。

### 科研任务与出题种子发现

用领域和任务类型定位候选来源，再检查数据可获取性、许可证、评分规则和复现环境。涉及遗传学以外医学题目时，可参考 [平行生物医药分类说明](PARALLEL_BIOMEDICINE_CLASSIFICATION.md)。

这个目录提供来源发现与初筛依据。将某条来源纳入正式题包，还需要完成任务级科学审查、数据授权核验、参考解验证和实际运行测试。

## 数据结构与文件导航

项目将机构、Benchmark、领域和价值证据分开记录，便于分别更新并关联查询。

| 文件 | 内容 | 关联字段 |
| --- | --- | --- |
| [benchmark_registry.csv](benchmark_registry.csv) | 名称、任务类型、官网、论文、代码或数据入口、公开状态与许可状态 | `benchmark_id` |
| [benchmark_organization.csv](benchmark_organization.csv) | 主组织、联合组织或生态、组织类型、地区、归属方式和置信度 | `benchmark_id` |
| [organization_entity.csv](organization_entity.csv) | 机构规范名称、别名、类别、实验室或部门、角色及来源 | `organization_id` |
| [benchmark_subcategory_mapping.csv](benchmark_subcategory_mapping.csv) | 主领域、主子领域、次级分类、覆盖方式、任务类型与模态 | `benchmark_id` |
| [benchmark_assessment.csv](benchmark_assessment.csv) | 规模、使用信号、质量初评、难度、SOTA 压力和下一步测量 | `benchmark_id` |
| [benchmark_economic_value_evidence.csv](benchmark_economic_value_evidence.csv) | 价值链、潜在买方、使用场景、商业信号、来源、证据等级与潜在价值分数 | `benchmark_id`、`organization_id` |

以 `benchmark_registry.csv` 为入口，使用 `benchmark_id` 关联其他 Benchmark 表，再通过价值证据表中的 `organization_id` 关联机构实体表。当前这些关联键均能在相应主表中找到。

目前子领域映射表每个 Benchmark 只有一行，次级分类保存在字段中；机构归属表使用组织名称描述归属。正式的子领域实体表、多对多映射和完整机构角色关系表仍需补齐。

| 文档 | 阅读目的 |
| --- | --- |
| [biomedical_benchmark_investor_memo_7p.pdf](biomedical_benchmark_investor_memo_7p.pdf) | 快速浏览投资人版概览 |
| [ORGANIZATION_SUBCATEGORY_VALUE_PLAN.md](ORGANIZATION_SUBCATEGORY_VALUE_PLAN.md) | 理解四层整理方法、分类方案、价值维度与执行顺序 |
| [ORGANIZATION_CLASSIFICATION.md](ORGANIZATION_CLASSIFICATION.md) | 浏览公司、高校、研究机构及挑战社区的组织分类 |
| [PARALLEL_BIOMEDICINE_CLASSIFICATION.md](PARALLEL_BIOMEDICINE_CLASSIFICATION.md) | 理解遗传学图谱之外的医学题目分类与统计口径 |

分类说明中提到的逐题 JSONL、汇总表、分类脚本及 `organization_summary.csv` 均未包含在当前仓库快照中。本目录保留分类说明和汇总口径；逐题分析需先补齐数据与脚本。本目录也不包含原始大题库和中间压缩包。

### 本地查询示例

克隆仓库后，可以用 Python 标准库查看某个领域的项目与来源：

```bash
git clone https://github.com/zehaoli0324-cloud/groundsignal.git
cd groundsignal
python - <<'PY'
import csv
from pathlib import Path

base = Path("04-投资人/生物医药Benchmark版图")

def read_csv(filename):
    with (base / filename).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

registry = {row["benchmark_id"]: row
            for row in read_csv("benchmark_registry.csv")}

for row in read_csv("benchmark_subcategory_mapping.csv"):
    if row["primary_domain"] == "功能基因组学与单细胞":
        project = registry[row["benchmark_id"]]
        print(project["name"], project["official_url"])
PY
```

这段示例用于目录查询。具体评测运行方式需要进入相应项目，按其官方说明准备数据和环境。

## 如何理解质量与价值

### 质量、难度与机构归属

`benchmark_assessment.csv` 的质量分数目前均带有 `provisional-` 前缀，是待审查的初评。正式质量判断需要补充来源、重复与污染检查、标注可靠性、评分可复现性和版本化运行证据。

机构归属的置信度只描述“谁创建或维护”的确定程度。创建者、维护者、托管平台和采用者应分别核验，机构名称本身不能证明任务质量。

### 经济价值证据等级

| 等级 | 方法口径 | 当前记录数 |
| --- | --- | ---: |
| A | 公开合同、采购、价格、授权或企业客户证据 | 0 |
| B | 官方产品集成、企业服务、付费 API、模型发布门槛或正式合作 | 0 |
| C | 多机构重复使用、长期排行榜、竞赛标准或广泛论文采用 | 22 |
| D | 基于数据稀缺、决策影响和替代成本的合理推断 | 23 |
| E | 证据不足，保留为候选方向 | 0 |

等级是当前表内标注，阅读时需要回到 `evidence_url` 核验相应主张。项目官网可以支持项目身份，但采购、采用或节省成本等主张需要各自对应的证据。

`economic_potential_score` 表示优先研究和商业验证的潜在价值。整理方案提出了买方需求、决策影响、数据稀缺、替代成本、采用程度、变现信号和监管关联七个维度；当前表尚未提供全部维度的逐项分值，暂不能完整复算总分。

**潜在价值分数不能解释为收入、估值、市场规模或投资回报预测。**

### 分类与来源的边界

- 当前子领域标签均为初步分类，`coverage_mode` 使用 `direct_or_adjacent`，尚未明确拆开直接覆盖与邻近相关。
- 价值证据表的 `subcategory_id` 仍存在 `unknown` 等粗粒度标签，需要统一为稳定分类 ID。
- 39 条机构记录包含不同层级的实验室、社区和生态描述，仍需继续处理别名、上下级和可能重叠的实体。
- 多项许可状态仍为 `license-review` 或 `terms-review`；公开可下载不自动意味着允许再分发或商业使用。
- `evidence_date` 应结合来源理解，不能直接视为论文发表日、交易发生日或最近一次联网复核时间。
- 平行医学分类文档描述的是另一组题目级分类统计，其题量不属于本目录 45 条登记记录的统一规模指标。

## 与 GroundSignal 的关系

GroundSignal 的目标是将公开信号转化为可追溯、可比较和可更新的情报。本专题为生物医药评测方向提供了一个结构化起点：

| GroundSignal 对象 | 本专题可提供的内容 | 后续接入工作 |
| --- | --- | --- |
| Entity | 机构与 Benchmark 登记记录 | 稳定实体 ID、别名与角色归一化 |
| Claim / Relation | 创建维护关系、领域归属、采用与价值判断 | 拆成独立主张并绑定来源 |
| Evidence | 官网、论文、代码和价值证据链接 | 补充证据摘录、采集时间与核验状态 |
| Event | 待建设 | 记录新版本、任务变化、排行榜及采用变化 |

当前文件已支持人工阅读和表格关联。持续监测、变化检测和自动情报生成需要进一步实现并验证。

## 更新与贡献

欢迎通过 [Issue](https://github.com/zehaoli0324-cloud/groundsignal/issues) 或 Pull Request 补充项目、修正归属、核验许可和提供采用证据。

建议按照以下顺序新增或更新记录：

1. **登记来源**：优先采用官方项目、论文或维护仓库，记录版本、任务范围、访问与许可条件。
2. **核验机构**：区分创建、维护、托管和采用，复用已有机构 ID，并保留归属证据与置信度。
3. **标注领域**：依据实际任务说明分类，区分直接覆盖和邻近相关，说明评测单位。
4. **完成初评**：将公开事实、分析判断和待验证项分开，缺失信息明确标注。
5. **补充价值证据**：分别记录科研采用、产品集成、实际交易和潜在需求，避免用同一个链接支持不同主张。
6. **检查关联与变更**：检查 ID 唯一性、关联完整性、来源链接和统计口径，更新日期及修改原因。

提交修订时，请提供来源链接、适用版本、核验日期、拟修改字段和理由。修改现有项目时保持 `benchmark_id` 稳定，并同步相关表。只有得到新证据支持时，才提高归属置信度、质量结论或商业证据等级。

## 下一步

| 优先级 | 工作 | 完成标准 |
| --- | --- | --- |
| P0 | 核验官方来源、版本、许可与机构归属 | 每条记录具备来源和明确核验状态 |
| P0 | 统一机构和子领域 ID，拆分覆盖方式 | 名称重叠可解释，分类关系可关联 |
| P1 | 将采用与商业判断拆成逐条证据记录 | 每个重要主张绑定来源、时间与状态 |
| P1 | 补充版本化评测与任务级质量审查 | 难度与质量判断有可检查的运行或审查依据 |
| P2 | 增加筛选看板与定期更新机制 | 可按机构、领域、任务和证据等级查询，并追踪变化 |

项目的长期价值在于持续回答：**哪些生物医药任务值得评测，现有评测能证明什么，以及这些能力与真实科研和产业决策之间还缺哪些证据。**
