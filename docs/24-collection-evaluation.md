# 数据采集评测系统：设计、运行与验收

入口：`scripts/evaluate_research.py`。默认完全离线，不调用搜索、模型或 LLM judge。它读取已有 `search-run.v1`，检查原文完整性，与明确范围的人工参考集比较，再输出 JSON、CSV、Markdown。它与 `research.py audit` 的区别是：audit 查运行，evaluate 加入参考来源、主张金标、人工裁决及声明权限；已有 `research.py compare` 仍用于启动模型三路对照。

本版能评估内部采集结果、模型重跑和同契约提交。Firecrawl / Tavily skill、GPT Researcher 等原生轨迹转换器尚未实现；本轮没有它们的真实性能分数。

## 1. 评测问题与分层指标

| 层 | 指标与分母 | 用处及限制 |
|---|---|---|
| 检索 | 参考源组 recall@k；已判断结果上的 precision；判断覆盖率；reference reciprocal rank；条件满足时 nDCG@k | 判断是否找到已知关键来源。排名按 `run.hits` 的采集管线融合顺序，先合并 URL、再合并人工来源组；不是单条查询的搜索引擎原生榜单 |
| 获取 | FETCHED / 所有尝试文档；已取得相关参考源组 / 已知相关组；缺失 required 来源；重复正文数 | 区分找到了 URL 和拿到了正文。下载成功不代表内容支持结论；IRRELEVANT 不计成功正文 |
| 抽取 | TP / FP / FN；精确率；已取得标注正文的召回；包含漏搜 / 漏抓的端到端参考召回 | 严格比较来源组 + 文本 SHA + 七个原子字段，不用模型自报置信度 |
| 分项质量 | 按谓词、商业阶段、肯定 / 否定拆开计数与精度 / 端到端召回 | 防止总体高分掩盖投资、实控、否认和量产错误；仍需真实代表性样本 |
| 人工审核 | 覆盖率、全体审核一致正确比例、分歧、未定、严重错误、风险候选复审率 | 只认声明为 HUMAN 的审查，MODEL 不充当人类；身份未做签名认证 |
| 声明权限 | 缺少采集许可、声明禁止却已采集、禁止 / 未知云处理却出现外发尝试 | 事后核对提交的声明；不阻止调用，也不证明授权真实或法律合规 |
| 资源与时效 | 调用、预算超限、耗时、输入截断、完整报告时的 token、已知发布时间到首次观察的滞后 | 金额未知保持 null；未知发布时间不伪造发现延迟；首次观察不是事件发生或全行业最早发现时间 |

**最重要的区分：** 已抓到 3 条正确主张、另有 1 条已知主张完全没采到，正文内召回可以是 100%，端到端只能是 75%。同一通稿的十个转载也不能把一条已知事实变成十条独立成功。

这里的 recall 全部限于已定义的参考池，不能叫全行业或全网召回率。`retrieval_by_provider` 是按运行记录顺序聚合各提供商命中后的组级指标，也不是单查询平均指标；比较 API 时要固定查询与预算单独实跑。

## 2. 三个输入契约

| 文件 | 契约 / 核心内容 | 防止的问题 |
|---|---|---|
| benchmark.json | `schemas/research-benchmark.v1.schema.json`；研究范围、截止时间、目标 SHA、split、标注者、来源组和正文金标 | 换目标、换原文、用转载凑分、混合真实与合成、把模型答案当金标 |
| reviews.json（可选） | `schemas/research-review.v1.schema.json`；run / benchmark 文件字节 SHA、文档权限、人类 / 模型逐候选裁决、可选 effort_minutes | 旧审核套新运行、重复同一审核人冒充双审、模型意见冒充人类审核、无依据模板直接批准 |
| policy.json | `schemas/research-eval-policy.v1.schema.json`；默认 `config/research-eval.default.json` | 临时改验收口径、只看点估计、不写样本与覆盖门槛 |

原子字段为 `subject, predicate, object, product, stage, polarity, event_time`。同名 / 别名不会由 evaluator 猜测归一；需在研究前确定主体口径。字段错误通常产生一个 FP 和一个 FN，这是严格关系匹配的预期。

来源组是人工核定的原始来源 / 同源转载组，不是域名数，也不天然保证独立性。每组有 URL 别名、0–3 相关性、维度、required 和可为空的发布时间。0 表示已判断无关，null 表示未判断，不能互换。每个规范化 URL 只能属于一组；组内不同正文版本都需要各自标注 SHA，不能把原文金标静默套给改写转载。

`annotation_complete=true` 代表这版正文已完整标注：`claims=[]` 才能作为无关系负例。未读完、尚未标注用 false，不能拿空数组当“没有事实”。金标主张可以属于本轮未采到的参考正文，从而计入端到端 FN；不能只标注系统已经找到的材料。

## 3. 第一步：运行合成演示，确认评分器工作

**用途：** 在无密钥、无权重情况下验证分母、去重和失败状态。

```bash
python scripts/evaluate_research.py demo --out research-runs/eval-demo-01
```

**产物：** `run/` 保存合成运行，`evaluation/` 有 evaluation.json、metrics.csv、report.md。命令退出 0 只说明合成工程演示执行成功。

**应看到：** SYNTHETIC_ONLY、NOT_READY；参考源召回 0.75；取得正文上的抽取召回 1.0；端到端 0.75；缺少 missing_capacity；1 篇重复内容；没有人工审核、许可声明或真实 token / 费用成绩。可直接查看仓库的 [合成评分样例](../samples/search/collection-evaluation.synthetic.json)。

**失败处理：** 目录重复换编号；Schema / SHA 错误回查输入，不删掉字段绕过。该样例所有公司、产品和遗漏参考均为虚构工程材料。

## 4. 第二步：为真实采集创建标注草稿

**用途：** 获得可编辑的引用和版本清单，而不把模型候选变成标准答案。

```bash
python scripts/evaluate_research.py init-benchmark --run research-runs/capture-01/run.json --out research-runs/gold-draft-01
```

**产物：** 草稿 benchmark.json；来源相关性 null、claims 空、正文未完整标注、groups_reviewed=false。程序不会复制 run.candidates，也不会凭正文哈希自动声称来源独立。

**人工必须补的内容：** 写准问题 / 时间 / 研究用途，核定来源分组与相关性；从独立来源发现系统没找到的材料；由两位人类读正文标注、裁决分歧，保留无关材料、空主张、否定、历史关系、同名、表格和阶段负例。只用生成草稿就评分会被拒绝；`--allow-draft` 仅用于预览，结果仍不达正式标注门槛。

**成功判据：** ADJUDICATED 至少两个不同标注者、裁决者、已核对来源组，所有登记的正文标注完整且来源相关性已判断。状态字段只是提交者声明，不能替代真实人工工作；人工改成 ADJUDICATED 不会让数据自动正确。

**失败处理：** 无法获得相关原件或判定关系，就不强造金标。按公司、原件 / 转载组、时间划分开发与留出；先小批试标，再建立 100–200 条真实样本，不能只对系统最容易的样本验收。

## 5. 第三步：创建绑定输入版本的人工审核表

**用途：** 在冻结的候选与来源上记录人类判断和实际权利依据，避免旧审批漂移。

benchmark 定稿后执行：

```bash
python scripts/evaluate_research.py review-template --run research-runs/extract-01/run.json --benchmark research-runs/gold-draft-01/benchmark.json --out research-runs/reviews-01
```

**产物：** reviews.json。文档权限默认 UNKNOWN、候选审核为空，不能直接当审批。

文档行分别填写 capture_permission、cloud_permission（ALLOWED / DENIED / UNKNOWN）、basis、reviewer、reviewed_at。basis 指向真实条款 / 合同 / 准入记录；模板 NOT_REVIEWED / UNASSIGNED 不能与肯定或否定权限决定共存。

逐候选行示例，仅说明格式，不能原样当真实审核：

```json
{
  "candidate_id": "从本次 run 复制实际 candidate_id",
  "reviewer": "实际审核人的稳定标识",
  "reviewer_type": "HUMAN",
  "verdict": "INCORRECT",
  "error_types": ["REVERSED_RELATION"],
  "reason": "说明原文哪个主体给谁供货，为什么候选方向错误",
  "reviewed_at": "2026-10-19T01:00:00Z",
  "effort_minutes": 4
}
```

CORRECT、INCORRECT、UNCERTAIN 分开；严重错误包括主体、方向、阶段越级、极性、无支持。TIME_ERROR 与 OTHER 也单独记录。CORRECT 不能同时带错误类型。同一候选同一审核人只能有一条最终记录，修订要另存有版本的审核文件，不能用重复记录充人数。

**成功判据：** 文件中的 run / benchmark 字节 SHA 与输入一致。当前风险规则覆盖股权 / 控制 / 投资 / 竞争、非肯定主张及订单 / 出货 / 量产，默认要求两位人类一致正确；这只是启发式，未覆盖所有合同、财务或独家性风险。所有拟正式采用的候选仍应人工核对。

**失败处理：** 更改 run 或 benchmark 后旧审核将报 binding_mismatch；重新核对新版并生成绑定，不能只复制旧签名。没有实际分钟记录保持 null；模型复核记录不得填 HUMAN。程序不验证审核者真实身份或独立性。

## 6. 第四步：评分并理解退出码

**用途：** 生成可追溯的质量诊断，明确哪些条件不足。

```bash
python scripts/evaluate_research.py score --run research-runs/extract-01/run.json --benchmark research-runs/gold-draft-01/benchmark.json --reviews research-runs/reviews-01/reviews.json --out research-runs/eval-01
```

可以省略 reviews，技术与金标指标仍能算；人工和权限门槛会显示不足，不会推测已审。若只预览草稿，显式加 `--allow-draft`。

| 退出码 | 含义 | 应做什么 |
|---:|---|---|
| 0（score / compare） | 已满足配置门槛，仍为 REQUIRES_HUMAN_RELEASE | 人类核对报告、权利、真实使用范围，再决定是否发布；代码不会发布 |
| 3 | 报告生成成功，但 NOT_READY | 读 FAILED / UNASSESSED 及分母，补具体缺口；不要当作程序崩溃或质量 PASS |
| 2 | 输入、契约、指纹或文件错误 | 修输入 / 版本，重新执行 |
| 0（demo / init / review-template） | 演示或草稿生成成功 | 只验证工程 / 生成材料，相应状态仍为合成、草稿或待审 |

**默认门槛：** 至少 3 个相关参考源组、100 条金标；参考检索召回 ≥0.8，有正参考的维度也逐项达到此门槛；抽取精确率 ≥0.95、端到端参考召回 ≥0.8、排名判断覆盖 ≥0.8；候选标注和人类审核覆盖均 100%；风险候选双人一致；无人类严重错误、分歧或与金标不一致的审核结论；required 来源无缺失；调用 / 文档 / 查询预算无超限；声明权限完整且无禁止行为；输入为真实运行、金标已裁决。可版本化修改 policy，必须报告 policy SHA，不跨门槛混排。没有参考材料的维度仍未知，不能由其余维度代为证明覆盖。

真实模型是否执行单独记录，不以“用了 LLM”作为质量奖励或验收前提；固定代码抽取也应按证据和金标判断。当前无模型的采集运行没有候选，其抽取精度仍未评估。模型尝试与原文的真实 / 合成标记必须一致，不能只改运行标签就把 fixture 晋级为实测；这些元数据检查仍不等于防篡改执行证明。

不存在一个加权总分来补偿严重错误：overall_score 始终 null。合成运行始终 NOT_READY，即使数值漂亮也不获得真实验收；缺数据是 UNASSESSED 或明确失败，不算通过。

精确率带 Wilson 95% 区间，默认门槛使用点估计，不使用置信区间下界自动放行。主张可能按公司 / 来源聚集，Wilson 的独立二项近似不能代替按公司分组的不确定性分析；小样本表现与生产可靠性要分开。

门槛目前按单次 run 计算。因此 5 家合计 100–200 条的起始标注集，可能不足以让任何一家公司达到默认 100 条门槛；它仍可以用于流程验证和错误分析。跨公司总体验收需另做分组汇总，不能把多次小样本相加后声称本评分器已完成总体统计。

## 7. 第五步：同条件比较采集策略

**用途：** 比较真实来源覆盖或冻结输入上的模型差异，避免混淆实验因素。

先生成一个完全离线、仅验证评分系统的三路样例：

```bash
python scripts/research.py compare --run research-runs/eval-demo-01/run/run.json --fixture examples/search/synthetic.json --out research-runs/eval-routes-01
python scripts/evaluate_research.py compare --runs research-runs/eval-routes-01/small_only/run.json research-runs/eval-routes-01/large_only/run.json research-runs/eval-routes-01/cascade/run.json --benchmark examples/search/eval-benchmark.synthetic.json --out research-runs/eval-compare-01
```

第二条命令应返回 3，生成 NO_AUTOMATIC_WINNER。合成 small_only 的不合格“量产”被过滤，因此剩余候选精确率仍可为 1，但端到端召回低于大模型 / 级联样例；这仅证明评测没有被高精确率迷惑，不能解释为真实 Qwen 弱于 DeepSeek。可看 [合成比较样例](../samples/search/collection-comparison.synthetic.json)。

真实比较换成真实 run、经人类裁决的 benchmark 和同顺序 `--reviews file1 file2 ...`。比较器禁止混合目标 / 真实合成模式、重复 run ID 和重复文件；共享同一 benchmark 与 policy，并报告 same_budget、same_frozen_input。它不自动挑赢家，也不因共享 benchmark 就保证外部服务调用公平。

**实验设计：** 采集端到端比较要相同问题、时间窗、允许来源、总预算与重试口径，并交错运行时间降低网页变化影响；模型比较要相同冻结原文；解析器比较要相同原始文件。外部 agent 只有最终报告时，不能伪造 search-run 补齐缺失过程。

## 8. 输出如何用于改进

| 现象 | 优先排查 | 不应得出的结论 |
|---|---|---|
| reference_recall 低 | 查询、语言、官方 seeds、预算、API 连通 | 行业里没有该关系 |
| 找到来源却 capture_recall 低 | robots、网络、解析、扫描 PDF、文档预算 | 大模型能力不够 |
| 正文召回高但端到端低 | 漏搜 / 漏抓的金标与覆盖范围 | 抽取器已解决整个研究任务 |
| 精度高、候选很少 | 漏抽、规则误拒、输入截断 | 系统整体可靠 |
| 高风险复审不足 / 有分歧 | 人工队列、实体、阶段、反证 | 再加一个模型即可代替人类 |
| 权限未知 / 禁止外发尝试 | 准入流程、批次隔离、模型配置 | 评分器证明合规或能撤回已外发内容 |
| token / 费用为空 | 服务未执行、用量缺失、账单未接入 | 使用成本为零 |

人工时间仅在所有 HUMAN 审核行都有 effort_minutes 时合计，未覆盖的采集准备、查证、建金标、等待等时间不在内。比较方案价值时另记完整研究人时；不能把本字段叫全部劳动成本。没有账单与价格输入，金额和每条正确主张的货币成本仍是 null。

## 9. 当前覆盖与下一阶段

已实现：契约、输入 / 审核绑定、来源组去重、范围内检索 / 获取 / 抽取 / 审核评分、预算与声明权限检查、未知处理、区间、分项报告、比较命令、合成负例及回归测试。

尚未实现：真实参考集、外部系统轨迹转换、表格单元格评分、实体语义归一、审核身份认证、实际账单、报告论证质量 judge、跨公司宏平均 / bootstrap、变化告警的匹配与漏报统计。下一步先补真实留出集和一个外部基线转换器，再考虑 LLM judge；judge 不能代替原文、金标与权限依据。
