# 开源对照与采集评测验证（2026-10-19）

## 本轮完成

- 在 GitHub 搜索并固定 14 个相关仓库的默认分支 SHA、维护 / 归档状态、API 许可证识别；阅读 README 和关键 skill、证据模型、LICENSE。记录见 [开源快照](research/open-source-snapshot-20261019.json)，比较和推断见 [23 号文档](23-open-source-comparison-value.md)。
- 新增评测器 `scripts/evaluate_research.py`、分层评分模块，以及 benchmark / reviews / policy 三种 Schema；使用见 [24 号文档](24-collection-evaluation.md)。
- Python 3.12：137 项测试通过，原 114 + 本轮 23。新增测试检查漏采分母、转载去重、语义方向错误、未知判断、版本 / scope / 审核绑定、标注独立性约束、草稿、空金标、无模型、人工分歧、模型不充当人类、权限声明、时间记录、CLI 退出码及 fixture 标记晋级拦截。
- 9 次 CLI 检查覆盖 demo、init-benchmark、review-template、score、草稿默认拒绝 / 显式预览、冻结模型三路比较、采集评分比较和重复输入拒绝。命令及预期退出码见 [JSON](25-collection-eval-validation-20261019.json)。
- 相对文档链接与 `git diff --check` 验证；CI 增加采集评测合成演示。

## 合成负例揭示了什么

| 路由（模拟输出） | 去重后精确率 | 已取得标注正文召回 | 端到端参考召回 |
|---|---:|---:|---:|
| small_only | 1.00 | 2/3 | 0.50 |
| large_only | 1.00 | 1.00 | 0.75 |
| cascade | 1.00 | 1.00 | 0.75 |

三个配置使用相同冻结正文和预算，包含一个同源转载、一个故意缺失的参考主张。small_only 的错误阶段输出被拒绝，留下的候选依然可以有很高精确率；漏采和漏抽只有在端到端分母中显现。

上述数据是预设的虚构 fixture，用于验证评分公式和工程状态，不是 Qwen / DeepSeek 的运行成绩或真实性能排序。所有结果 SYNTHETIC_ONLY、NOT_READY、NO_AUTOMATIC_WINNER。没有人类审核、真实授权、真实 token 用量或货币成本。

可直接阅读 [单次完整评分](../samples/search/collection-evaluation.synthetic.json)、[评分门槛摘要](../samples/search/collection-evaluation.synthetic.md)、[三路比较](../samples/search/collection-comparison.synthetic.json)。单次文件中的字节 SHA 绑定生成它的具体运行，重新执行会产生新的运行 ID / 时间和 SHA。

## 尚未证明

- 外部 14 个项目仅做文档审阅，未安装、未调用、未重跑榜单；特别记录 Open Deep Research 已归档，DRB 的 README badge 与 LICENSE 标识存在差异。
- 没有 Firecrawl / Tavily skill、GPT Researcher 与 GroundSignal 的同条件实跑结果；原生轨迹转换器待做。
- 没有 5 家公司、100–200 条真实人类金标；真实检索、模型质量、人工工时改善与费用均未知。
- 评分器不认证审核身份、不验证授权文件真假、不阻止违法或越权采集、不自动发布事实。门槛达到也只进入 REQUIRES_HUMAN_RELEASE。
- 本轮新增的是测量工具和价值假设，不是已建立生产优势、行业覆盖或商业收入的证据。
