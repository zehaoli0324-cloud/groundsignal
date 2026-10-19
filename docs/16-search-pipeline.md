# 搜索与证据采集：部署、操作和模型选择

对应 [Issue #4](https://github.com/zehaoli0324-cloud/groundsignal/issues/4)；设计依据见 [proposal](15-search-evidence-proposal.md)。本入口为 `scripts/research.py`，原 `collect.py` 和 Windows 采集界面仍使用原来的流程。

首次使用按 [部署手册](18-deployment-guide.md) 和 [使用手册](19-usage-guide.md) 操作；搜索预算与六轮角度见 [挖掘方案](20-search-mining-strategy.md)，来源权限、个人信息和验收见 [合规与质量](21-compliance-quality.md)。本页为原始接口参考。新增 `prepare` 离线生成三档会话，`doctor` 检查配置（仅 `--probe` 请求本地模型元数据），`audit` 报告技术缺口，不代表事实正确或法律授权。

## 1. 现在可以做什么

输入公司研究目标，生成覆盖九类关系/变化的搜索计划；通过 Brave、Tavily、Firecrawl、DeepSeek 的 REST 适配器或显式选择的旧搜索源取得线索；保存原始网页或 PDF、解析文本及内容指纹；抽取带精确引文的关系候选；按失败/风险/抽样规则调用大模型；生成待审队列和 PR #3 的证据 ledger。

这是一条有限步骤、可检查的管线。它没有任意执行网页指令的工具，也不会让模型自动批准正式事实。`PENDING` 候选与 ledger 的 `EARLY_SIGNAL` 是正常产物，不能写成已确认供应关系。

## 2. 安装与首次运行

需要 Python 3.10+；本轮验证使用 Python 3.12。先进入仓库根目录。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-search.txt
python scripts/research.py demo --out research-runs/demo-01
python scripts/research.py validate --run research-runs/demo-01/run.json
```

Windows PowerShell 中，创建环境使用 `py -m venv .venv`，激活使用 `.\.venv\Scripts\Activate.ps1`；也可以直接用 `.\.venv\Scripts\python.exe` 执行上述 Python 命令。

`demo` 不联网、不调用真实模型。它使用虚构企业和预先写好的模型返回值，验证阶段越级、否定、所有权、转载和交接逻辑。所有产物标记 `SYNTHETIC_ONLY`，不能把其中的分数解释为 Qwen/DeepSeek 成绩。

输出目录必须不存在或为空，以保护先前的采集时间和证据版本。更改命令中的目录名即可开展新一轮。`research-runs/` 和缓存不提交 Git；真实网页全文、模型运行材料和密钥不进入公开提交。

## 3. 编辑研究目标

从 `examples/search/target-nvidia.json` 复制一份目标配置。里面的 `id` 是研究记录 ID，`identity_status=UNCONFIRMED` 不代表已完成工商主体确认。

- `name / aliases`：中文名、完整名称、英文别名。英文短名按词边界匹配。
- `official_domains`：你已核对的官网主机名。用于搜索优先级和浏览器抓取范围，不代表官网每句话都已核实。
- `dimensions`：供应商、客户、竞争、投资方、被投资方、人物、产品、产能、反证。
- `time_range.after / before`：ISO 日期或 null。是搜索提示，不能保证每家搜索引擎都完全执行，也不替代事件时间审核。
- `seed_urls`：明确的一手页面地址。不知道 URL 时可留空；知道官方公告地址时，固定入口可以补足搜索排名遗漏。

```bash
python scripts/research.py plan --target examples/search/target-nvidia.json --out research-runs/nvidia-plan-01
```

这一步只写搜索计划，不发请求。先为各维度分配任务，再增加英文别名和官方来源查询。查询预算不足时，`unplanned_dimensions` 明确列出缺口。

## 4. 真实搜索与正文获取

默认配置的模型关闭；搜索服务仅在对应环境变量存在时执行：

| 提供商 | 环境变量 | 适配器依据 |
|---|---|---|
| Brave | BRAVE_SEARCH_API_KEY | Web Search API |
| Tavily | TAVILY_API_KEY | POST /search |
| DeepSeek | DEEPSEEK_API_KEY | POST /v1/tools/search |
| Firecrawl | FIRECRAWL_API_KEY | POST /v2/search；在 providers 中显式选择 |

在本地终端或部署环境中设置所选服务的密钥；不写进配置或 Git。本程序只读取进程环境，不自动加载 `.env`。

```bash
python scripts/research.py run --target examples/search/target-nvidia.json --config config/search.default.json --out research-runs/nvidia-capture-01
```

未设置密钥时返回 `NOT_CONFIGURED`，不会偷偷换成模型编造的搜索结果。没有任何可用正文时总体为 `NO_USABLE_DOCUMENTS`，CLI 返回 2，并保存诊断。查询得到空数组是 `NO_RESULTS`；格式变化、网络错误、验证页、超额和缺配置分别记录。

需要测试已知网页时可使用 `examples/search/target-nvidia.seeded.json`。其中是已通过官方页面发现的 2024 年报道，只用于抓取 smoke，不是近期行业动态的样本。若只想抓取种子 URL，在自己的配置中将 `providers` 设为空数组。

旧的搜狗/360 网页解析器可在自己的配置中显式选择 `sogou/so360`，用于对照或补充；不作为稳定服务的承诺。验证页被识别后停止，不自动解决验证。

URL 规范化只移除明确的跟踪参数，保留文章 ID 等查询参数。相同 URL 合并搜索命中，跨域完全相同正文记录 `duplicate_content_of`，但不自动认定不同内容属于独立来源。来源注册表的 `tier_hint` 只用于检索优先级；ledger 仍为 UNKNOWN，等待审核。

HTTP 抓取检查 robots、响应类型、正文长度和目标别名；保存 bytes 与解析文本。PDF 默认用 pypdf，保留页码和字符区间；扫描版没有文本时明确提示可能需要 OCR，不生成正文。

## 5. 小模型与大模型分别在哪一步出现

第一步搜索和网页下载不依赖大语言模型。取得并保存原文后，小模型开始工作：它按 `prompts/search/extract.md` 与 JSON Schema 抽取候选。

目前给出两套可实际选择的配置，均是待验证的初始方案：

| 配置 | 常规执行 | 大模型升级 | 适用试验 |
|---|---|---|---|
| search.qwen9b-flash.json | 本地 qwen3.5:9b | deepseek-flash | 推荐起始对照，先测常规抽取与升级率 |
| search.qwen4b-pro.json | 本地 qwen3.5:4b | deepseek-v4-pro | 本地资源较少，测更小执行器是否造成过多升级 |

本地 Qwen 使用 Ollama 的兼容端点 `http://127.0.0.1:11434/v1`。如果使用 vLLM、LM Studio 或其他服务，把 `base_url / model` 改为服务真实提供的值；不要假定不同服务的模型名字相同。

已安装 Ollama 时，可以先运行：

```bash
ollama pull qwen3.5:9b
ollama serve
```

如果 Ollama 应用已在运行，就不用再启动第二个服务。下载和运行模型需要本机实际的磁盘与内存资源；本工程没有在当前环境下载或运行这些权重。

配置好本地模型服务和 `DEEPSEEK_API_KEY` 后，使用已保存原文进行抽取：

```bash
python scripts/research.py extract --run research-runs/nvidia-capture-01/run.json --config config/search.qwen9b-flash.json --out research-runs/nvidia-extract-01
```

`extract` 不重新搜索或下载网页，保留首次观察和抓取时间。它会新建模型运行记录和交接记录，避免把旧证据重跑误写成“刚发现”。

程序自动检查：Schema、引文在模型输入和原文中的位置、主体/客体是否出现在引文中、产品、日期精度，以及明确的量产阶段越级。不能通过的输出进入 rejected 队列。原文定位正确仍可能语义错误，因此所有通过程序检查的候选仍是 PENDING。

以下情况升级大模型：小模型不可用/格式失败、引文或字段失败、所有权/实控/竞争、否定/传闻、空抽取，以及对普通样本的确定性抽样。大模型与小模型不一致时保留分歧；大模型不可用时显示升级未完成。角色关闭/缺密钥/调用超额不会被显示成审核通过。

请求记录包括请求与返回模型名、提示词哈希、输入哈希、配置哈希、token 用量和耗时。服务别名不保证模型版本永久不变；没有供应商不可变版本 ID 时，不能宣称完全复现同一权重。

## 6. 怎样公平比较与选型

```bash
python scripts/research.py compare --run research-runs/nvidia-capture-01/run.json --config config/search.qwen9b-flash.json --out research-runs/nvidia-compare-01
```

比较 `small_only / large_only / cascade`，每组使用完全相同的冻结原文。每组有自己的模型预算，因此整个命令最多是单组预算的三倍；不会自动反复优化到满意为止。

没有人工标签时，比较只记录运行、调用次数和 token，质量为 `UNASSESSED`；模型根本未执行时为 `MODEL_NOT_RUN`。没有供应商实际价格或账单时，金额成本保持 null，不用过时价格制造精确数字。

带人工标签时使用 `--gold`。格式示例为 `examples/search/synthetic-gold.json`，其中的虚构标签只能用于合成输入。真实标签应有每份正文的 document_id、text_sha256 和人工确认的原子关系；程序拒绝正文版本不匹配的标签。评测按标注子集计算严格字段匹配的 precision/recall，不等于全行业召回率，也不能代替实体归一和最终人工科学/商业判断。

选型顺序：

1. 先检查精确引文、关系方向、商业阶段、否定与时间错误。
2. 在达到真实留出集质量门槛的配置中比较成本、时延和升级比例。
3. 按公司、来源类别、语言和关系类型拆开看，不能只用一个总体分数。
4. 9B 若已能可靠处理简单材料，就让大模型集中处理困难样本；4B 只有在节约的本地成本没有被升级调用抵消时才值得选。
5. 固定测试集，不让测试答案进入 prompt/skill 优化。模型训练和自动技能进化留到有足够失败样本后。

合成对照可运行：

```bash
python scripts/research.py compare --run research-runs/demo-01/run.json --fixture examples/search/synthetic.json --gold examples/search/synthetic-gold.json --out research-runs/synthetic-comparison-01
```

这个命令的结果必须标记 SYNTHETIC_ONLY，没有真实模型优胜者。

## 7. 输出、审核和账本

| 文件 | 用途 |
|---|---|
| plan.json | 搜索计划与未覆盖维度 |
| search-progress.json | 已执行搜索的命中和诊断；进程中断时保留 |
| sources/ | 原始 bytes/渲染 HTML，保存在本地运行目录 |
| documents/ | 每份正文、获取时间、指纹和解析状态 |
| run.json | 完整冻结输入、抽取尝试、成本计数与缺口 |
| review-queue.json | 待审候选与被程序拒绝的输出 |
| report.md | 人可阅读的来源、引文、阶段和运行结果 |
| ledger/manifest.json | PR #3 格式的未审核原文交接 |

当前账本以文档为 `UNCLASSIFIED_LEAD` 接入，候选 ID 保存在 lineage 中；还没有把未归一的客体自动创建成正式公司关系。来源品质提示不写为审核结论；未知发布时间、来源独立性及主体身份保持未知。

人工应按候选返回完整原文，确认实体、关系、阶段、时间和反证，再使用 `evidence_demo.py review` 的显式审核流程。不能只批准整篇新闻后把所有候选都默认认作事实。专门的逐条候选裁决/实体归一界面属于下一阶段。

```bash
python scripts/evidence_demo.py review --help
python scripts/evidence_demo.py report --input research-runs/nvidia-extract-01/ledger/manifest.json --out research-runs/nvidia-extract-01/ledger.html
```

## 8. 预算、依赖和已知边界

配置独立约束查询、搜索请求、命中、正文、抓取 HTTP 请求/浏览器调用、模型调用、大模型调用、输入字符、输出 token、单次超时与总时长。总时长在工作单元边界检查，在途请求仍由单次超时约束；不是操作系统级硬截止。

搜索缓存和供应商暂停状态在 `.collector-cache/research/` 保存；HTTP 429 的 Retry-After 受到尊重。此版命令按顺序执行；跨进程并发限流、断点自动恢复和任务调度仍需后续队列支持。

动态页可选安装 Crawl4AI，并在配置中选择 `fetcher=crawl4ai`；它仅用于目标配置明确列出的官方域名。浏览器渲染会请求子资源，预算计渲染调用而非每条子资源，部署环境应另设网络边界。PDF 的 `pdf_parser=docling` 可使用已安装的 Docling；本适配器的 Markdown 暂无可靠页码映射，不能宣称保留了表格单元格或原 PDF 页码证据。两种重型适配器本轮没有真实执行。

原先的单公司采集 UI、`ingest.py` 与来源域名打标器没有被替换；新流程用独立入口隔离未审核候选。后续接 UI 和旧导入入口时必须保留相同门禁。

本分支复用未合并的 PR #3；它没有替用户合并 main。审阅新 PR 时请先检查依赖。运行状态及本轮验证记录见 [验证说明](17-search-validation-20261019.md)。
