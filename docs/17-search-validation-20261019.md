# 搜索管线首轮验证记录

日期：2026-10-19（Asia/Shanghai）；关联 Issue #4，依赖草稿 PR #3。

## 工程验证

安装 `requirements-search.txt` 对应轻量依赖后，本地运行：

```bash
python -m unittest discover -s tests -q
```

结果：**103 项通过**，包括原有 61 项及新增 42 项。新增检查涉及九维度覆盖、查询预算、精确 URL/域名匹配、别名词边界、缺密钥、HTTP 429 持久暂停、缓存时间、四个 REST 提供商的模拟返回、验证页、私网目的地址与重定向、PDF 页码、模型格式、引文、阶段越级、调用预算、分歧、合成隔离、冻结重跑、原文和原始快照篡改、未审核账本交接及无标签拒绝评分。

提供商与模型 HTTP 单元测试使用模拟传输，不构成真实 API 连通性或真实模型质量测试。

另已执行 CLI 的 plan、demo、validate、compare：

- 默认目标生成 18 个查询，九个维度均至少有一条。
- 合成演示产生 4 份虚构正文、4 条待审核候选；真实搜索、抓取、模型请求均为 0。
- 合成的三种路由使用相同的冻结原文哈希，标记 SYNTHETIC_ONLY，`selection_status=NO_AUTOMATIC_WINNER`。
- Ledger 无审核记录，来源层级为 UNKNOWN；所有文档交接为 UNCLASSIFIED_LEAD / EARLY_SIGNAL。
- 原始来源和解析正文的指纹均可核验；CONTRACT_VALID 只代表契约与保存文本校验。

可检查的合成样例见 `samples/search/`，重跑命令见操作文档。

## 真实网络尝试：未通过

| 尝试 | 实际结果 | 可以得出的结论 |
|---|---|---|
| 2 个已从 NVIDIA 官方页面发现的种子 URL | 两个均 dns_unavailable；HTTP 抓取请求数 0 | 当前执行环境不能解析该站域名；没有取得原文 |
| 360 搜索，查询富瀚微供应关系 | 1 次有预算的调用，ReadTimeout；后续因预算停止 | 没有取得搜索结果；没有证明该搜索源连通或可靠 |
| 付费搜索 API | 无对应环境密钥，NOT_CONFIGURED | 适配器仅完成离线传输测试 |
| Qwen3.5-9B / 4B | 未下载权重、未启动本地服务 | MODEL_NOT_RUN |
| DeepSeek Flash / Pro | 无模型密钥 | MODEL_NOT_RUN |
| Crawl4AI / Docling 可选适配器 | 未安装和执行 | NOT_RUN；不计入已验证能力 |

真实尝试总体为 NO_USABLE_DOCUMENTS，没有生成候选或已确认关系。机器可读记录见 `docs/search-validation-20261019.json`。公开提交只保存状态、URL、哈希及计数，不提交第三方网页全文或运行密钥。

## 当前选型结论

建议以 Qwen3.5-9B + DeepSeek Flash 作为真实试点的起始配置，同时以 4B + Pro 和 large_only 作对照。这是工程上的初始选择，**没有真实测量支持“当前最强”或“级联已经优于单大模型”的结论**。

下一步在可访问目标站点的本地/服务器环境，配置一个搜索服务和模型服务，先取 5 家公司、三类来源的冻结原文；建立人工留出标签后再选择最终组合。两个星期的持续监控、真实召回/误报/时延及质量门槛均未完成，不关闭 proposal 中的后续工作。

已加入 GitHub Actions 的离线检查工作流；本地验证不能代替远端 CI 的实际运行状态。
