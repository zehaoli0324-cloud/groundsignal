# GroundSignal

### Evidence-Grounded Continuous Enterprise Intelligence

> **From public signals to decision intelligence.**

**把分散的公开信息变成可追溯、可比较、可持续更新的企业与供应链情报。**

> 软件是生产机器，数据是资产，**Intelligence 才是商品**。
> 商业路径：Service first → Subscription second → Data/API third。

GroundSignal 不是一个"搜索公司信息"的 Agent，也不是一个静态知识图谱。它尝试建立一条完整的企业情报链路：

```text
公开信息
→ Evidence
→ Claim / Relation / Event
→ Temporal Intelligence Graph
→ Cross-Entity Analysis
→ Change Detection
→ Decision-oriented Output
→ Evaluation
```

目标不是回答"NVIDIA 的供应商有哪些？"，而是继续回答：

> 这条供应关系由什么证据支持？它是什么时候成立的？现在还成立吗？
> 新加入一家寒武纪后，它和已有 NVIDIA / 华为 / 海光信息有什么竞争或供应链交集？
> 一个 HBM、CoWoS 或客户变化出现后，哪些已有判断可能需要更新？
> 系统漏掉了多少重要事件？发现得够不够快？误报多不多？

---

## Why this exists

企业情报真正困难的部分通常不是"找到一篇新闻"，而是把长期分散的信息连接起来。

```text
NVIDIA → makes → H200 → uses → HBM3E → supplied by → SK hynix → packaging dependency → CoWoS → manufactured by → TSMC
```

某一天出现"TSMC expands CoWoS capacity"，真正有价值的问题不是"台积电扩产了"，而是：

> 这是否影响 NVIDIA GPU 的供给约束？哪些 HBM、服务器 ODM、PCB 或光模块公司与这个变化有关？哪些已有 watchlist 公司应该被重新检查？

**核心思想：新信息不是被存入数据库，而是被放进已有知识网络中重新解释。**

---

## System Logic

```text
1. Research Target (Company/Product/Industry/Watchlist)
        ↓
2. Multi-source Retrieval (API/filings/annual reports/websites/media/search)
        ↓
3. Evidence Extraction (source URL · publication time · retrieved_at · source tier)
        ↓
4. Structured Intelligence (Entity·Product·Facility·Relation·Claim·Evidence·Event)
        ↓
5. Intelligence Graph (company ↔ product ↔ supplier ↔ facility, investor ↔ company, event ↔ affected)
        ↓
   Cross-Entity Scan              Change Detection
   (overlap/competition/          (event stream/capacity/
    shared customer/supplier)      product & supplier changes)
        ↓
6. Intelligence Output (Company Card · Panorama · Discovery Report · Watchlist · Evidence Audit)
        ↓
7. Evaluation (Precision · Recall · Evidence Coverage · Detection Latency · False Alert Rate)
```

---

## What happens when a new company enters the system?

这是系统目前最重要的一条运行逻辑。加入"寒武纪"，系统不会只创建 `寒武纪.md`，而是执行一次 **Cross-Entity Intelligence Scan**：

```text
寒武纪 → 读取产品/客户/供应商/投资人/行业/已知关系
      → 与已有实体逐一比较 → neighbors(new) ∩ neighbors(existing)
      → 识别共享节点和直接关系 → 分类
```

当前 prototype 支持发现：`DIRECT_COMPETITOR / PRODUCT_OVERLAP / SHARED_CUSTOMER / SHARED_SUPPLIER / SHARED_INVESTOR / SUPPLY_CHAIN_LINK / COMMON_ECOSYSTEM`

发现分成三层，避免把"有共同客户"直接写成"一定是竞争对手"：

```text
OBSERVED    已有直接关系或证据支持的事实
DERIVED     由共享客户/产品/供应链结构计算出的分析
HYPOTHESIS  只有行业或生态重叠，需要进一步检索验证
```

```bash
python3 scripts/cross-entity-scan.py ai-compute 寒武纪 --report
# → 08-智能发现/2026-08-27-寒武纪-交叉关系发现.md
```

---

## From search to evidence

| Tier | Source | Typical use |
|------|--------|-------------|
| Tier 1 | 交易所公告、年报、招股书、政府文件、采购/招投标公告 | 事实验证 |
| Tier 2 | 公司官网、Reuters/Bloomberg/Nikkei/主流财经与专业行业媒体 | 强支持证据 |
| Tier 3 | 搜索结果、公众号、雪球、财富号、论坛、行业讨论 | 线索发现 |

实际使用/设计支持的数据来源：东方财富行情/F10 API、巨潮/上交所/深交所公告、公司年报与公告、公司官网、互动易/e互动、招投标公告（Structured/first-party）；主流财经媒体、半导体行业媒体、360/搜狗搜索、行业分析（Discovery）；雪球、财富号、公众号、论坛（Lead-only）。

核心原则：**一手优先、多源交叉、事实与预期分离、量化数字必须溯源、弱来源只作为 lead。**

系统保存的不只是"富瀚微 → 海康威视"，而是 claim + evidence：

```yaml
claim:
  subject: 富瀚微
  predicate: SUPPLIES
  object: 海康威视
  status: SUPPORTED
  valid_from: 2023
  last_verified_at: 2026-08-25
evidence:
  source_type: annual_report
  source_url: ...
  publication_date: ...
  retrieved_at: ...
```

---

## Data Model

V2 intelligence model 七类核心对象：ENTITY / PRODUCT / FACILITY / RELATION / CLAIM / EVIDENCE / EVENT

- **ENTITY**：谁？（NVIDIA / TSMC / SK hynix / 寒武纪）
- **PRODUCT**：具体什么产品？（H100 / H200 / B200 / HBM3E / 昇腾 910C）
- **FACILITY**：哪个制造/产能节点？（Fab / CoWoS 封装厂 / HBM 产线 / 服务器工厂）
- **RELATION**：两个对象理论上什么关系？（SUPPLIES / CUSTOMER_OF / MANUFACTURED_BY / PACKAGED_BY / INVESTED_IN / COMPETES_WITH）
- **CLAIM**：系统认为某个关系成立到什么程度？（VERIFIED / SUPPORTED / INFERRED / DISPUTED / STALE / SUPERSEDED / REJECTED / UNKNOWN）
- **EVIDENCE**：为什么相信？（annual report / announcement / disclosure / industry media / discussion）
- **EVENT**：什么变了？（NEW_CUSTOMER / SUPPLIER_CHANGED / CAPACITY_EXPANSION / NEW_PRODUCT / FUNDING / TENDER / REGULATION / PRICE_CHANGE）

---

## Information Integration（多层信息整合）

### 1. Single-Entity Intelligence

```bash
python3 scripts/ask.py demo "富瀚微的客户是谁" -o board.html
```
聚合公司画像 + 供应商 + 客户 + 产品 + 投资人 + 证据 + 关联实体 → 单实体 Intelligence Card。

### 2. Pairwise Intelligence

```bash
python3 scripts/panorama.py demo 富瀚微 全志科技 -o panorama.html
```
比较 A-only / B-only / shared nodes / common ecosystem / potential overlap，理解两个公司的关系结构。

### 3. Cross-Entity Intelligence

```bash
python3 scripts/cross-entity-scan.py <vault> <new-company> --report
```
新公司进入数据库后自动与已有知识比较，发现可能的竞争/供应链交互 → Discovery Report。这是系统从 database 走向 intelligence system 的关键能力。

### 4. Temporal / Event Intelligence

```bash
python3 scripts/watchlist.py ai-compute --watch NVIDIA,SK海力士,台积电 -o watchlist.html
```
变化记录为 Event 而非覆盖旧事实；目标是 **Change Detection，而不是 News Aggregation**。

---

## Evidence Layer

每条重要事实都应该回答：来源？何时采集？证据强度？是否过期？

```bash
python3 scripts/evidence-audit.py <vault>   # 节点级分级 VERIFIED/SUPPORTED/INFERRED/UNKNOWN
```

长期设计区分两个概念：`source_quality ≠ evidence_strength`（Reuters 是高质量来源，但"据悉可能进入供应链"对"已经成为供应商"的支撑强度仍然很低）。

---

## Evaluation

### Eval v1 — Is what we stored correct?
Relation Precision / Evidence quality / Entity Resolution / Temporal Validity / Abstention。已完成 50 条关系分层抽样 gold set：**Relation Precision 50/50**，并诚实暴露早期问题（关系级 evidence 覆盖不足、时间信息不完整、弱证据混入），作为 backlog 追踪。

### Eval v2 — Is the system useful?
| Metric | Question |
|--------|----------|
| Relation Recall | 应该知道的关系覆盖了多少？ |
| Event Recall | 重要事件抓到了多少？（当前 AI Compute 窄域 **8/12 = 67%**） |
| Detection Latency | 事件发生多久后系统知道？（live 待 cron 运行数据验证） |
| False Alert Rate | 推送中有多少没有商业意义？（待运行数据） |
| Evidence Coverage | 多少 claim 能追溯到来源？（当前 98%） |

诚实结论：**precision 较高，但 coverage 有限；live latency 与 false-alert 仍待证明。**

---

## Commercial Value

1. **Supply-chain intelligence**：谁供谁、供什么、哪个产品依赖哪个组件、哪个设施是瓶颈
2. **Competitive intelligence**：新公司加入自动发现 product overlap / shared customers / shared suppliers / shared investors / direct competition（VC/PE、券商研究、战略、BD、采购）
3. **Continuous monitoring**：用户定义 watchlist，系统持续回答"从上次检查之后，什么真正变了？"
4. **Evidence-backed research**：每个结论保留 source/timestamp/confidence/evidence state，可 review/audit/correct/update/export

---

## What is implemented vs. what is next

### Implemented / runnable
- Markdown/Obsidian intelligence graph
- structured entity + relation ingestion（ingest.py）
- single-entity intelligence board（ask.py）
- pairwise panorama（panorama.py）
- evidence source grading + audit report（evidence-audit.py）
- event/watchlist rendering（watchlist.py）
- product/facility/event V2 data objects
- **cross-entity scan prototype + Discovery Report**
- Eval v1 + Eval v2 metric framework

### Prototype / early validation
- cross-entity relationship scoring（heuristic，待校准）
- event recall measurement（67%，待提升）
- continuous monitoring orchestration（cron 已注册，live 待证明）
- temporal state tracking / capacity intelligence

### Next（未实现，不冒充）
- **Event → Impact Propagation**（event → affected company → first-order → second-order supply-chain impact）
- **Event Significance**（Novelty × Commercial Impact × Supply Criticality × Evidence Strength × Watchlist Relevance，只推送真正改变判断的变化）
- **Continuous Evaluation**（Recall / latency / false alerts / coverage 滚动测量）
- **User Validation**（是否有人持续使用并付费）

---

## Example Intelligence Domains

- `demo/`：Company–Company 关系图（半导体公司/供应商/客户/投资人/股东/竞争者），验证关系图谱 + 证据打标 + 单/双实体查询。159 节点 / 715 关系 / 0 断裂。
- `ai-compute/`：V2 intelligence model（Company/Product/Facility/Event/Capacity/Evidence/Cross-Entity Discovery），聚焦 AI Compute Supply Chain（AI accelerator / HBM / advanced packaging / foundry / PCB / optical module / server ODM）。47 实体节点 / 8 事件 / 2 产能追踪（另有自动生成的 Discovery Report）。

---

## Repository

```text
demo/            Company-centric intelligence graph
ai-compute/      V2 AI Compute intelligence graph
scripts/         ingest · ask · panorama · cross-entity-scan · watchlist · evidence-audit · import-helper
docs/            architecture · source methodology · schema · evaluation · user validation · commercial validation
```

## Documentation

- **行业搜索与证据采集（Issue #4）**：运行 `python scripts/research.py demo --out research-runs/demo-01` 查看合成闭环。支持九维度搜索计划、Brave/Tavily/Firecrawl/DeepSeek 适配器、原文快照、小/大模型级联、冻结原文对照与待审核账本交接。部署和边界见 [`docs/16-search-pipeline.md`](docs/16-search-pipeline.md)，方案见 [`docs/15-search-evidence-proposal.md`](docs/15-search-evidence-proposal.md)。真实模型质量尚未实测；新入口不替换原采集 UI。
- **逐步操作手册**：[部署与环境检查](docs/18-deployment-guide.md) · [研究使用闭环](docs/19-usage-guide.md) · [搜索与挖掘力度](docs/20-search-mining-strategy.md) · [合规与质量验收](docs/21-compliance-quality.md) · [人工审核模板](docs/templates/research-review.md)。每步说明用途、操作、验收与失败处理；`prepare / doctor / audit` 分别生成有界配置、检查环境、审计运行，均不自动批准事实或来源权限。
- **Issue #1 最小 Demo**：直接打开 [`samples/ground-evidence/demo.html`](samples/ground-evidence/demo.html)，或运行 `python scripts/evidence_demo.py`。支持独立证据计数、状态变化、按时间回放与 CSV/JSONL 导出；8 条真实仓库回填与虚构流程分开展示，详见 [`docs/14-ground-evidence-demo.md`](docs/14-ground-evidence-demo.md)。尚未证明真实提前发现。
- **图形界面**：双击 `启动采集界面.vbs`，输入公司名称并点击“搜索并保存”。详见 `界面使用说明.md`。
- `docs/11-auto-collection.md` — 自动联网搜索公司并写入 Obsidian（`python scripts/collect.py "公司名称"`；仓库路径见 `collector-config.json`）
- `docs/02-企业情报数据库-架构与Proposal.md` — architecture
- `docs/04-search-methods.md` — data sources & retrieval methodology
- `docs/06-eval-report.md` — Eval v1
- `docs/07-schema-v2.md` — intelligence schema
- `docs/08-eval-v2.md` — recall / latency / false-alert evaluation
- `docs/09-user-validation.md` — user validation
- `docs/10-commercial-validation.md` — commercial roadmap

---

## Design Principle

> 只保存会改变我们对公司、产品、供应链或事件判断的信息，并让每个判断可以被验证、比较和更新。

```text
Search finds information.
A database stores information.
Enterprise Intelligence connects information, tracks how it changes,
tests whether it is reliable, and determines why the change matters.
```

---

## Status

**Current stage: sellable / testable intelligence MVP, not yet a validated commercial intelligence platform.**

已证明：structured intelligence can be built / evidence provenance can be preserved / cross-entity relationships can be discovered / events can be represented and surfaced / system quality can be evaluated

尚待证明：high recall / low detection latency / low false-alert rate / impact propagation quality / repeated real-user usage / willingness to pay
