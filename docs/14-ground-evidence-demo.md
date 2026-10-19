# Issue #1：Ground Evidence 最小可运行 Demo

对应 [Issue #1](https://github.com/zehaoli0324-cloud/groundsignal/issues/1)。本版验证四件事：证据可单独追溯、同源转载不重复计数、事件状态可随审核变化、历史快照不使用未来来源或审核。

## 立即查看

直接用浏览器打开 `samples/ground-evidence/demo.html`。页面自包含，不需要启动服务、Obsidian、模型密钥或网络连接。

需要重新生成时，在项目根目录运行：

```bash
python -m pip install -r requirements.txt
python scripts/evidence_demo.py
```

这会复用已保存的回填 manifest，保持首次观察时间不变；不会反复把旧时间改成“刚发现”。离线数据量很小，生成器为每个证据或审核边界预先计算一个 Python 快照；展示和导出使用同一份结果。

## 两组数据的含义

| 数据 | 来源与作用 | 能证明什么 |
|---|---|---|
| 现有 AI Compute 事件 | 固定提交 `5506f8f` 的 8 个 Markdown 笔记；逐条迁移为 GroundEvidence | 真实笔记可以迁移、保留出处和原日期精度、按本次入库时间回放 |
| 模拟供应关系 | 虚构公司、凭证、原始来源组、审核和时间 | 状态计算、转载去重、反证、替代、过期和回放逻辑可执行 |

**8 条回填记录均为 `EARLY_SIGNAL`。**其中 6 条原笔记提供了外部引用网址，2 条缺少外部网址。迁移保存的是仓库记录，而非这些网址的原始文章；本次没有重新抓取或核验原文。旧置信度与 `SUPPORTED` 标签不继承为当前确认状态。

这些记录的 `first_seen_at / retrieved_at / processed_at` 使用迁移时刻。旧 `fetched_at / last_verified_at` 只保留在 lineage 中。未知 `published_at` 保持 null；年或月精度的 `event_time` 不伪造为具体日期。来源法律审核和再分发许可保持未知。实体 ID 对固定笔记标签稳定，但不是工商主体确认。

## 演示顺序

选择“模拟供应关系”，依次点击：

1. **资格线索**：1 条审核支持，状态为 `WATCH`。
2. **两个独立来源**：2 个审核确认的独立来源组，状态为 `SUPPORTED`。
3. **新增转载**：证据记录从 2 增到 3，独立来源仍为 2。
4. **客户确认**：一手确认经过明确审核，状态为 `VERIFIED`，显示约 41 天的**模拟**提前量。
5. **出现反证**：状态为 `DISPUTED`，停止显示提前量。
6. **反证复核**：后续审核拒绝不适用的反证，恢复 `VERIFIED`；回看上一步仍是 `DISPUTED`。
7. **旧版本替代**：V2 获确认后，V1 被显式标为 `SUPERSEDED`；此前快照不出现替代信息。

也可手动输入截止时间。页面统一用 UTC；“客户确认”前的快照不包含该确认来源、确认时间或提前量。超过 45 天未复核的支持状态变为 `STALE`，不表示关系已终止。

页面可导出当前截止时间的完整快照 JSON、事件 JSONL 和 CSV。导出的事件包含状态、可用的证据 ID、来源 URL、独立支持数、确认时间与提前量边界。

## CLI 回放

```bash
python scripts/evidence_demo.py snapshot --input examples/ground-evidence/synthetic.json --as-of 2026-04-11T08:15:00Z --out evidence-runs/pre-confirmation
python scripts/evidence_demo.py snapshot --input examples/ground-evidence/synthetic.json --as-of 2026-05-21T08:15:00Z --out evidence-runs/confirmed
```

两个输出目录均包含 `snapshot.json / events.jsonl / events.csv`。早期目录不包含后续确认和反证。`evidence-runs/` 不提交到 Git。

## 接入已有采集器

`import-collection` 接受今天新增的 `collect.py` 保存的 JSON：

```powershell
python scripts/collect.py "台积电" --vault ai-compute
$record = Get-ChildItem 'ai-compute/09-采集记录/台积电-*.json' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$runDir = 'evidence-runs/tsmc-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
python scripts/evidence_demo.py import-collection $record.FullName --out $runDir
python scripts/evidence_demo.py report --input "$runDir/manifest.json" --out "$runDir/demo.html"
```

导入按 URL 去重，保留采集文件指纹及声明时间；导入时的观察时间不回填成声明的旧时间。每个结果进入独立的 `UNCLASSIFIED_LEAD`，不根据关键词猜测关系或将不同事件错误合并。公司主体、事件归并与语义抽取仍需后续模块。

`review` 可以追加当前时刻的审核；必填审核人、原因与支持原文。独立来源组由审核人明确指定，不从域名数量推导。同一原文指纹即使被赋予不同组也合并。来源组未知不会计作独立支持。`CONFIRM` 还要求记录声明原始来源已经核对、且为 T1。当前采集导入默认 UNKNOWN，不能直接确认。

```bash
python scripts/evidence_demo.py review --help
python scripts/evidence_demo.py report --help
```

审核不提供 `--at` 回填时间参数。修改审核结论需追加新记录；旧审核继续保留。CLI 不实施全文理解或自动判断证据是否支持，审核决定仍是人的责任。结构、引用、时间顺序、原文定位、确认条件与替代条件由确定性校验器把关。

## 文件与接口

- `scripts/ground_evidence.py`：数据校验、独立来源归并、状态、快照与导出。
- `scripts/evidence_demo.py`：迁移、采集接入、追加审核、报告生成。
- `schemas/ground-evidence.v1.schema.json`：ledger、manifest、Evidence 的结构契约；跨记录与时间语义由 Python 校验。
- `ai-compute/09-ground-evidence/manifest.json`：真实回填 manifest；每条 Evidence 单独保存于 `capacity/` 或 `disclosure/`。
- `examples/ground-evidence/repository-source-fingerprints.json`：固定源版本的文本指纹，阻止变更笔记继续引用旧提交出处。
- `examples/ground-evidence/synthetic.json`：与真实数据隔离的模拟 ledger。
- `templates/evidence-demo.html`：无外部依赖的展示模板。
- `samples/ground-evidence/`：可直接打开的报告及两组导出样例。

版本分别为 `groundsignal.ground-evidence.v1`、`groundsignal.event-snapshot.v1` 和 `groundsignal.event-feed.v1`。不输出未经校准的 confidence、materiality、signal_strength 或投资收益。

## 验证与边界

```bash
python -m unittest discover -s tests -v
```

测试覆盖未来证据和审核不可见、独立来源与转载、同内容伪装多源、反证与后续更正、替代条件、过期、真实回填缺失时间、采集接入、损坏数据拒绝、来源指纹变化、CSV 公式文本与 HTML 文本安全；原采集器测试一并运行。

离线 HTML 包含完整演示时间线，因此不能用作对秘密未来数据的访问控制。Python 快照和导出截断当时可见记录，但本版不对输入 JSON 中的时间真实性做第三方认证；真正线上数据还需要可信采集日志和持久、不可改写的存储。固定回填指纹也不能替代对原始商业凭证的核验。

本版尚未证明真实出货/招投标凭证覆盖、自动语义抽取、一阶或二阶影响传播、实时监测、正提前量、量化回测或付费价值。下一步应接入一类真实招投标/采购或资格来源，在本 ledger 上积累实际采集与独立审核记录，再计算实际表现。
