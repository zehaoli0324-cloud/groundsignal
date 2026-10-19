# 相关 skill、开源方案与 GroundSignal 的价值判断

核对日期：2026-10-19。方法：GitHub 仓库搜索、仓库 API、固定 commit 的 README，以及关键 skill / 证据模型 / LICENSE 文件阅读。完整的 14 个仓库 SHA、归档状态、更新时间和 API 许可证识别见 [检索快照](research/open-source-snapshot-20261019.json)。没有安装运行这些外部系统，也没有取得同条件性能、费用或中文行业准确率成绩。

**结论：GroundSignal 的通用搜索和爬取部分差异化有限，继续自建整套爬虫的收益不高。值得保留和验证的是半导体领域的关系定义、原文证据、商业阶段、时间变化、反证和审核记录。它目前是有潜力的研究工作流原型，尚未证明比成熟开源组合更准确、更便宜或更省人工。**

## 1. 最相关的 skill：基础能力已经相当完整

| 项目与本次阅读位置 | 已有能力及与我们的重叠 | 对 GroundSignal 的建议 | 边界与维护成本 |
|---|---|---|---|
| [Firecrawl skills](https://github.com/firecrawl/skills/blob/2b8f29eae6c6faa30f357b184dc1603419e16228/README.md)，重点 [competitive-intel](https://github.com/firecrawl/skills/blob/2b8f29eae6c6faa30f357b184dc1603419e16228/skills/workflows/firecrawl-competitive-intel/SKILL.md) 与 [deep-research](https://github.com/firecrawl/skills/blob/2b8f29eae6c6faa30f357b184dc1603419e16228/skills/workflows/firecrawl-deep-research/SKILL.md) | 搜索、抓取、浏览、竞争变化和多角度研究 SOP；竞争 skill 保存来源和再次运行参数，深度研究区分力度 | 直接作为“通用 agent + skill”的强基线；参考操作 SOP，保留自身证据契约 | skill 为 ISC；目录是镜像，改动应回源。开源 skill 不包含免费云服务或上游内容权利；竞争 skill 重点是价格、功能、变更，不是直接交付我们的供应链事实账本 |
| [Tavily skills](https://github.com/tavily-ai/skills/blob/778122e5f9c680f541eeceda5a5b36405eb7980c/README.md)，重点 [search](https://github.com/tavily-ai/skills/blob/778122e5f9c680f541eeceda5a5b36405eb7980c/skills/tavily-search/SKILL.md) 与 [research](https://github.com/tavily-ai/skills/blob/778122e5f9c680f541eeceda5a5b36405eb7980c/skills/tavily-research/SKILL.md) | 搜索、提取、站点发现、爬取、研究，支持深度、时间 / 域名过滤和结构化报告 | 用作搜索 / 研究服务基线；先比来源覆盖，不仅比最终报告观感 | 仓库 MIT；当前 CLI 文档有受限 keyless 搜索 / 提取，研究要求鉴权。我们 REST 适配器目前要求密钥，未复用其 CLI keyless 模式。供应商变化需要持续适配 |

上述 skill 是让通用 agent 使用工具的工作说明；不是被严格执行的数据质量保证。GroundSignal 当前的 prompt + Schema + 固定代码同样不能仅凭“有 skill”证明行业事实正确。要比较的是同一问题下取得了哪些原件、哪些关键关系正确、漏了多少以及花了多少人工。

## 2. 爬取、解析和抽取：优先复用成熟部件

| 方案 | 文档中的强项 | 我们当前的实际差距 | 采用判断 |
|---|---|---|---|
| [Crawl4AI](https://github.com/unclecode/crawl4ai/blob/94b67888ca8b335ff2121423a50e06dd27661922/README.md) | 浏览器、Markdown、CSS / XPath / LLM 抽取、分块、深爬与恢复 | 我们只有可选调用接口，没有完整深爬编排、恢复或浏览器子资源预算 | 动态站点候选；静态页继续轻量 HTTP。Apache-2.0 API 识别，另核对仓库归属说明、依赖及实际使用条款 |
| [Crawlee Python](https://github.com/apify/crawlee-python/blob/508f544f7f0260b4f26b806d50e84592538f8db6/README.md) | 持久 URL 队列、状态恢复、请求路由、存储、重试 | 我们顺序执行、跨任务预算和断点恢复不完整 | 需要持续采集时优先评估队列层，不应自己继续堆重试循环。Apache-2.0；仅启用获准的访问方式 |
| [LangExtract](https://github.com/google/langextract/blob/3a68580f0aede0e96a2e1e03daa2a5f4011e4fcd/README.md) | 结构化抽取、来源字符定位、长文分块 / 多遍、可视化，本地 Ollama 支持 | 我们精确逐字检查较简单，长文只选有限片段，缺逐条可视化审核 | 最值得优先做抽取对照的组件。Apache-2.0；它不是 Google 正式支持的产品；定位机制仍不等于语义核验 |
| [Docling](https://github.com/docling-project/docling/blob/0e54294231b69bc2cf7a39873235495788f76b57/README.md) | PDF 布局、表格、OCR、本地处理与结构化中间格式 | 我们的 Docling 接口只取 Markdown，丢失了它可以提供的部分结构 / 定位价值 | 年报、股权表格与扫描 PDF 的重点候选；先做页码和单元格定位适配。代码 MIT，模型各自许可需另查 |

这些项目在通用采集 / 解析上比我们更完整，这是能力覆盖判断，不是实测速度排名。当前不应把“我们也有网页快照、JSON、字符区间”当成新的技术壁垒。基础层保留窄接口和测试，将创新投入到关系口径、证据维护及审核效率。

## 3. 研究 agent：报告与受控问答的强基线

| 方案 | 适合比较什么 | 对我们的意义与限制 |
|---|---|---|
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/README.md) | 规划 / 执行、网页和本地研究、递归深搜、引用报告、skill 接入 | 活跃的通用研究基线；可以覆盖我们大量报告需求。报告引用不是逐条关系裁决、当前有效性和许可登记的替代；需适配采集轨迹才能公平评测。Apache-2.0 |
| [Jina node-DeepResearch](https://github.com/jina-ai/node-DeepResearch/blob/fd323b521a51264d497bec333bfb997da1bf3210/README.md) | 搜索—阅读—推理循环、问题缺口与 token 预算 | 适合比较定向深搜、答案精简和收敛；不应强行按长报告长度评价。Apache-2.0；本次固定提交在 2026-05，不能只依据项目名假定最新维护状态 |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/README.md) | 可配置模型、搜索 / MCP、LangGraph 研究与历史评测实现 | **API 显示 archived=true**，最新默认分支提交在 2026-08；保留架构与实验参考，不作为本轮新生产依赖首选。MIT；旧 README 的模型和榜单不能当当前结论 |
| [Tongyi DeepResearch](https://github.com/Alibaba-NLP/DeepResearch/blob/f72f75d8c3eb842f2bbbab096a12206ff66e270f/README.md) | 专门的长程检索模型、ReAct / Heavy 推理范式、搜索 benchmark | 后续规划 / 检索策略基线。README 说明总参数约 30.5B、每 token 激活约 3.3B，不能把激活量当作 3B 稠密模型的部署成本。仓库 Apache-2.0，权重、工具服务和运行成本分别核对；当前不应为了“更强 agent”先承担整套部署 |

本次只确认功能、接口和维护状态，未重跑上述项目的榜单，不据各自 README 的性能宣传给我们或它们排质量名次。

## 4. DisMech / mechmaker：最值得借鉴的知识维护方式

[DisMech](https://github.com/monarch-initiative/dismech/blob/9e83460b89fc61be2879e4794e9e14a4ee5dc35a/README.md) 把结构化知识、引用和 agent 维护结合，通过 PR 让人审阅。[证据模型](https://github.com/monarch-initiative/dismech/blob/9e83460b89fc61be2879e4794e9e14a4ee5dc35a/docs/explanation/evidence-model.md) 区分证据支持 / 反驳方向、直接性和引文在原文中的角色；引用真实、引文匹配与科学含义正确是不同层次。[mechmaker](https://github.com/monarch-initiative/mechmaker/blob/4ea572526d9801856b175412ee457959ddfd9141/README.md) 进一步提供创建此类知识库的流程、模型、检查和 agent 说明。两者仓库代码 API 识别为 BSD-3-Clause，具体内容许可仍要逐项核对。

对我们的价值主要是方法：让机器提出变更、让证据和审核决定是否采纳，而非让最强模型直接拥有事实写入权。半导体不需要照搬疾病本体，却需要自己的法人、产品代际、商业阶段、股权与时效定义。当前 GroundSignal 的逐候选裁决入图、实体归一与有效期还没有完成，不能宣称已经复现了一个成熟的行业 DisMech。

## 5. 评测方案：借鉴分层，避免被“报告好看”带偏

| 开源评测 | 可借鉴内容 | 为什么不能直接作为采集验收 |
|---|---|---|
| [DeepResearch Bench](https://github.com/Ayanami0730/deep_research_bench/blob/f2735b5c3636759c22f9e936c0232de8bf545b67/README.md) | RACE 报告评价与 FACT 引用核对分开；记录 evaluator 配置 | 通用报告质量不是公司关系精确率；引用抓取和 judge 版本都会影响结果。README badge 写 MIT，但本次 [LICENSE](https://github.com/Ayanami0730/deep_research_bench/blob/f2735b5c3636759c22f9e936c0232de8bf545b67/LICENSE) 及 API 为 Apache-2.0，复用以实际文件及所用数据许可核对 |
| [DeepResearch Bench II](https://github.com/imlrz/DeepResearch-Bench-II/blob/b38f360603db9531b102aef8c166cedb8509b6f6/README.md) | 从专家报告拆细粒度可核对条目，分信息召回、分析、呈现 | 适合后续公司研究报告 rubric，不替代来源获取、方向 / 阶段 / 时间与审核质量；代码 Apache-2.0，数据逐条许可而非统一覆盖 |

本轮的 [采集评测系统](24-collection-evaluation.md) 先做不依赖付费 judge 的、参考集限定的确定性评测，保留人工语义裁决。没有直接复制上述项目代码、论文题目或专家答案；也没有安装外部 skill 或更改用户全局 agent 设置。

## 6. 我们现在有什么价值，缺什么证据

| 层次 | 当前已做 | 价值判断 | 还需证明 |
|---|---|---|---|
| 搜索 / 抓取 | 多 API、固定来源、快照、预算、错误诊断 | 必要工程基础，差异化低 | 真实中文行业覆盖、故障恢复与成本 |
| 行业主张 | 九维、方向、产品、阶段、否定、有限时间字段 | 有领域适配价值；未形成完整本体 | 金额 / 比例 / 法人链、跨文件与表格处理 |
| 证据维护 | 精确引文、冻结输入、未审交接、保留分歧 | 可支持透明审核；这种方法已有成熟先例 | 逐候选审核、当前有效性、实体归一、独立来源链 |
| 模型分工 | 小模型常规抽取、大模型按需升级 | 可能省钱，但未证明 | 同等质量下的升级率、实际账单、延迟和人工时间 |
| 评测 | 本轮加入参考源召回、获取、关系与人工审核分层评测 | 为后续选择提供工具，不是质量优势本身 | 真实金标、独立留出、与外部基线的同条件实验 |
| 产品与数据资产 | 手册、模板、版本化运行 | 让研究能交接；尚无持续信息优势 | 是否持续发现重要关系、减少误报、节省决策时间及客户需求 |

**投入建议：继续，但缩小自建范围。** 复用搜索服务和成熟解析器；自己的主要工作放在半导体关系、证据变化、人工审核与测量。若项目最终只是把网页摘要汇总成带链接的公司报告，直接组合现有 skill 的替代性很高；若能持续维护经审核的产品—供应商—客户—股权关系和失效 / 反证记录，才更可能形成有用数据资产。这是基于能力对照的判断，商业价值仍需真实使用验证。

## 7. 用什么实验验证这项判断

1. **固定任务与参考集。** 选 5 家不同环节公司，覆盖九维；由两位人类审核 100–200 条原子主张及无关 / 无关系正文，按公司与原始来源组划分开发和留出。用途：避免只选我们熟悉或容易的材料。
2. **设三个端到端基线。** A：通用 agent + Firecrawl / Tavily skill；B：GPT Researcher；C：GroundSignal。使用相同问题、时间窗口、允许来源、运行上限，记录真实费用与人工分钟。用途：看自建流程是否超出通用工具组合。
3. **另做组件消融。** 相同冻结正文上比较当前抽取器与 LangExtract、small_only / large_only / cascade；固定文件集比较 pypdf 与 Docling。用途：把检索、解析与模型效果分开；不能用不同检索输入宣称小模型更强。
4. **按三种成本比较。** 以“每条正确、可追溯、已审核主张”的 API 成本、总耗时、人工分钟分别报告；包含失败运行与复审修正，不用模型 token 代替总成本。用途：验证级联是否真的有收益。
5. **独立做变化试点。** 在获准来源上连续两周保留新增、终止、更正、过期与漏报。用途：验证持续维护的价值；一次静态报告无法证明提前发现或长期有效性。
6. **预先确定去留条件。** 先达到同一质量底线，再判断覆盖、成本或人工时间是否优于基线；若没有优势，优先保留审核 / 数据层，把通用研究执行交给成熟方案。用途：避免因为已写代码就持续扩大自建。

当前评测器直接读取本仓库 `search-run.v1`，外部 skill / agent 的原生轨迹转换器尚未实现。因此本轮交付是文档能力对照和可运行的内部评测框架，不是已经完成 A / B / C 的胜负实验。后续转换必须保存真实来源、正文、指纹、时间、请求与错误；仅有最终报告时，缺失的采集层指标保持未评估，不能补造轨迹。
