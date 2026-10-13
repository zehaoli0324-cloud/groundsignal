# Benchmark 组织、子领域与经济价值整理方案

更新时间：2026-10-13

## 1. 建议的整理顺序

不要直接把 benchmark 按“哪个公司做的”或“看起来值钱”排序。建议拆成四层，并保持四层可以通过 `benchmark_id` 关联：

1. **机构实体层**：谁创建、维护、发布、托管或商业化使用；
2. **benchmark 层**：项目的版本、任务、数据形态、公开程度和许可证；
3. **子领域层**：benchmark 覆盖什么生物医药问题，允许一个 benchmark 映射到多个子领域；
4. **价值证据层**：谁可能购买或使用、解决什么高成本问题、是否存在公开的商业化信号。

这比把“研究机构分类”和“生物学分类”放在同一张表里更稳定，也能避免一个 benchmark 因为主办方不同而被误判为不同领域。

## 2. 国内外机构的第一层分类

### 2.1 AI 公司和产业研究实验室

重点看：是否把 benchmark 用于模型训练、模型发布、企业客户评测、数据服务或安全合规。

**国内候选组**：字节跳动 Seed、阿里通义/千问、百度、腾讯、智谱、华为诺亚/盘古等。当前项目中已经有 ByteDance Seed 相关 benchmark；阿里、百度、腾讯、智谱和华为应先补充官方来源与 benchmark 证据，再纳入正式统计，不能仅因公司做了生物模型就归入。

**国际候选组**：OpenAI、Anthropic、Google Research、Microsoft Research、NVIDIA、BenevolentAI、FutureHouse/Edison Scientific 等。

### 2.2 高校和大学实验室

按“学校—实验室/课题组—benchmark”三级记录，而不是只记录学校名称。例如：清华 C3I、上海 AI Lab、Stanford AIMI、Stanford SNAP、Harvard Zitnik Lab、MIT/PhysioNet、Theis Lab、上海交通大学等。

### 2.3 研究机构、平台和评测组织

例如 OpenCompass、FlagEval、PhysioNet、FutureHouse、xbench、BioASQ consortium、CASP、CAMEO、Open Problems、DeepChem 等。这里需要区分：

- **创建者**：提出任务和数据集；
- **维护者**：负责版本、网站、代码和排行榜；
- **托管平台**：提供提交、算力或数据分发；
- **采用者**：论文或企业使用，但不拥有 benchmark。

### 2.4 社区和挑战赛联盟

适合单独统计 recurring challenge、社区数据集和长期评测，例如 CASP、CAMEO、BioASQ、MoleculeNet、Open Problems 等。它们的价值通常不来自一次性销售，而来自标准制定、数据积累、竞赛生态和科研基础设施地位。

## 3. 机构表的推荐字段

在现有 `benchmark_organization.csv` 之外，建议增加机构实体表：

```text
organization_id,canonical_name,aliases,region,organization_class,
subclass,lab_or_division,parent_organization,role,ownership_mode,
commercial_status,evidence_url,evidence_date,confidence,notes
```

关键字段说明：

- `organization_class`：AI 公司、高校、研究机构、医院、数据平台、挑战联盟、社区；
- `subclass`：国内/国外、公司/大学/非营利、基础研究/产业研究/平台型；
- `role`：creator、maintainer、host、data_provider、adopter、commercial_user；
- `commercial_status`：research-only、open-infrastructure、enterprise-facing、commercial-product、unknown；
- `confidence`：confirmed、probable、needs-review。

## 4. Benchmark 子领域的第二层分类

子领域必须与机构分类解耦。建议先使用以下 12 个一级类别，再用二级类别描述任务：

| 一级类别 | 建议二级子领域 |
| --- | --- |
| 临床医学与医学知识 | 临床问答、医学考试、临床决策、诊断、治疗建议、医学安全 |
| 生物医学 NLP 与证据检索 | 文献问答、证据检索、关系抽取、医学知识库、摘要与引用验证 |
| 生物科研 Agent 与实验工作流 | notebook 分析、实验规划、protocol、数据库查询、科研工具调用 |
| 遗传学与基因组学 | 统计遗传学、群体遗传学、数量遗传学、调控组学、临床遗传学、癌症基因组学 |
| 功能基因组学与单细胞 | CRISPR/扰动、遗传互作、单细胞整合、空间组学、细胞状态预测 |
| 蛋白质与结构生物学 | 结构预测、蛋白设计、突变效应、蛋白工程、蛋白质组学 |
| 药物发现与分子机器学习 | 分子性质、虚拟筛选、对接、生成、ADMET、药物反应 |
| 医学影像与数字病理 | X 光、CT、MRI、超声、病理切片、报告生成、多模态影像 |
| 临床时间序列与医疗 Agent | 连续诊断、病程预测、EHR、医疗工具使用、长期决策 |
| 科学复现与一般科学推理 | 论文复现、科学计算、仿真、科学代码和跨学科推理 |
| 公共卫生与健康服务 | 流行病学、风险预测、健康管理、卫生政策和人群干预 |
| 数据质量、安全与评测基础设施 | 污染检测、鲁棒性、公平性、幻觉、安全、排行榜和评测协议 |

### 子领域映射原则

- 一个 benchmark 可以有一个 `primary_subcategory` 和多个 `secondary_subcategory`；
- 只有当题目、输入数据或官方任务说明明确覆盖时，才标记为 `direct`；
- 只因论文中提到“可用于某领域”而产生的映射标记为 `adjacent`；
- 通用医学题库需要逐题抽样或逐题标注后，才能计算某个遗传学、肿瘤学或药物基因组学子集的真实题量；
- 非问答 benchmark 用 `task_instance_count`、`dataset_size`、`evaluation_case_count` 区别“题目数”。

推荐的多对多映射表：

```text
benchmark_id,version,primary_domain,primary_subcategory,
secondary_subcategories,coverage_mode,item_or_task_count,
public_item_access,license_status,task_type,modality,confidence,notes
```

## 5. 经济价值如何体现

不要把“引用多”直接等同于“经济价值高”，也不要把“没有公开购买记录”写成“没有商业价值”。建议拆成三个结果：

### 5.1 已实现商业价值

只记录可以被外部证据支持的事实：

- 公开采购、合同、授权、API、企业订阅或付费数据服务；
- 纳入商业模型发布门槛、企业客户验收或合规评测；
- 被数据服务商、模型厂商、药企、医疗机构或 CRO 明确采用；
- 公开披露价格、合同金额、客户数量、调用量或付费版本。

### 5.2 可验证的产业使用价值

即使没有金额，也可以记录：

- 是否进入模型训练、微调、模型卡或发布报告；
- 是否成为行业标准、挑战赛长期基准或监管/临床验证的一部分；
- 是否能替代高成本人工工作，如专家阅片、文献筛选、变异解读、实验设计、药物筛选；
- 是否具有稀缺数据、专家标注、真实世界数据或合规壁垒。

### 5.3 潜在经济价值

这是推断项，必须与已实现价值分开。建议每个 benchmark/子领域填写以下 0–5 分维度：

| 维度 | 0–5 分含义 |
| --- | --- |
| buyer_demand | 是否存在明确买方和持续需求 |
| decision_impact | 模型结果是否会影响诊疗、研发、采购或合规决策 |
| data_scarcity | 数据是否难获取、难标注或具有隐私/合规壁垒 |
| replacement_cost | 能否替代专家、实验、筛选或计算资源 |
| adoption | 是否有论文、排行榜、产品或机构重复使用 |
| monetization | 是否有授权、API、采购、服务或企业集成信号 |
| regulatory_leverage | 是否与临床验证、药品研发、医疗器械或监管要求相关 |

内部优先级分数可以定义为：

```text
economic_potential_score =
  0.20 * buyer_demand
  + 0.20 * decision_impact
  + 0.15 * data_scarcity
  + 0.15 * replacement_cost
  + 0.10 * adoption
  + 0.10 * monetization
  + 0.10 * regulatory_leverage
```

这个分数只能表示“项目优先研究/商业验证价值”，不能当作市场规模、估值或收入预测。

## 6. 经济价值证据表

建议新增一张证据表，而不是把所有判断塞进 `benchmark_assessment.csv`：

```text
benchmark_id,subcategory_id,organization_id,value_chain_stage,
buyer_segment,use_case,decision_affected,estimated_cost_saved,
data_scarcity_score,adoption_signal,commercial_signal,
commercial_signal_type,public_amount,public_volume,evidence_url,
evidence_date,evidence_grade,economic_potential_score,analyst_note
```

`evidence_grade` 建议使用：

- **A**：公开合同、采购、价格、授权或企业客户证据；
- **B**：官方产品集成、企业服务、付费 API、模型发布门槛或正式合作；
- **C**：多机构重复使用、长期排行榜、竞赛标准或广泛论文采用；
- **D**：基于数据稀缺、决策影响和替代成本的合理推断；
- **E**：目前没有足够证据，仅作候选方向。

## 7. 子领域经济价值的写法示例

### 临床变异解读/临床遗传学

- 买方：医院、遗传咨询机构、检测公司、药企和临床决策软件厂商；
- 高成本问题：专家审阅、变异分级、家族风险解释、报告生成；
- 数据壁垒：病例隐私、专家标注、临床证据链和版本追踪；
- 价值证据：临床产品集成、检测服务、合规验证和专家工作流采购；
- 不应直接写成：某 benchmark 已经产生了多少收入，除非有公开证据。

### 蛋白质设计/突变效应

- 买方：药企、抗体公司、酶工程公司、合成生物学公司和模型厂商；
- 高成本问题：实验筛选、定向进化轮次、候选蛋白优先级排序；
- 数据壁垒：实验测量、专利序列、活性/稳定性/表达标签；
- 价值证据：实验轮次减少、候选命中率提高、企业合作、商业平台集成。

### 药物发现与分子生成

- 买方：药企、CRO、药物发现平台、化学信息学软件公司；
- 高成本问题：虚拟筛选、合成可行性、ADMET 过滤、候选化合物排序；
- 数据壁垒：真实实验活性、失败实验、专利和内部筛选数据；
- 价值证据：项目进入 lead optimization、合作研发、软件订阅或服务合同。

### 生物科研 Agent 与实验工作流

- 买方：生命科学研究机构、药企研发部门、科研软件公司和算力平台；
- 高成本问题：文献检索、数据库查询、分析脚本、实验计划和结果解释；
- 数据壁垒：真实 notebook、实验 protocol、工具执行轨迹和专家评分；
- 价值证据：工作流节省时间、工具调用成功率、企业部署和按量计费服务。

## 8. 下一阶段的实际执行顺序

1. 先把 45 个 benchmark 的机构名称归一化，形成机构实体表；
2. 将国内外 AI 大厂、研究机构、高校实验室、平台和挑战联盟分组；
3. 为 45 个 benchmark 建立一级领域和二级子领域的多对多映射；
4. 对有完整题目的 benchmark 做题目级子领域标签；
5. 对每个子领域建立买方、使用场景、数据壁垒和证据等级；
6. 优先研究 `A/B/C` 证据级别的方向，再对 `D/E` 方向做产业访谈或公开资料检索；
7. 最终输出三张核心表：机构表、子领域映射表、经济价值证据表。

