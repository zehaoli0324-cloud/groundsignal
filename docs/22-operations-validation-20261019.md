# 部署与使用方案的验证记录（2026-10-19）

对应本次 18–21 号手册及 `prepare / doctor / audit` 增量。机器可读命令记录见 [JSON](22-operations-validation-20261019.json)；原管线真实网络失败及限制见 [首轮验证](17-search-validation-20261019.md)。这不是用户设备的部署记录，也不是行业数据质量成绩。

## 本地完成的验证

- Python 3.12 虚拟环境，按 `requirements-search.txt` 安装依赖。
- `python -m unittest discover -s tests -q`：114 项通过，原 103 + 新 11；无真实搜索和模型调用。
- 12 次 CLI 检查通过：quick / standard / deep 三档 prepare、两套模型配置 prepare、空 providers 的种子模式 prepare、离线 doctor、plan、demo、validate、audit、合成 compare。
- 九维计划实际生成 9 / 27 / 54 条；六轮按维度覆盖后再展开，短英文名和官网入口进入相应轮次；减少维度不会重复凑满额度。
- 默认 doctor 与 prepare 不访问网络；mock 检查 `--probe` 仅请求 loopback 元数据、不跟随重定向、不请求远端模型、不调用生成接口；缺少模型 / 密钥不会伪造已执行。
- 以测试密钥验证诊断不包含密钥值。没有真实密钥写入文件。
- audit 对合成材料始终报告事实质量 UNASSESSED、法律合规 NOT_ASSESSED；模型预算耗尽的正文被列为未完成处理，不被计为无事实。
- Markdown 相对文件链接有效；`git diff --check` 通过。人工核对四份手册的用途、操作、验收、失败处理和当前能力边界。

## 没有完成或不由本轮证明的部分

| 项目 | 状态 / 原因 |
|---|---|
| 有效付费搜索 API 请求 | NOT_RUN；没有本轮真实服务鉴权与额度证据 |
| 成功真实原文采集 | 本轮未重跑；首轮是 DNS / timeout 失败，不能写为通过 |
| Qwen 权重下载与本地推理 | NOT_RUN；doctor 的服务名单检查也不等于推理测试 |
| DeepSeek 真实推理、模型质量与费用 | NOT_RUN；合成 compare 不存在真实赢家 |
| Crawl4AI / Docling 实际运行 | NOT_RUN；重型依赖未安装执行 |
| 真实金标、≥95% 主张精度、高风险双人复审 | 未完成；手册中的数值是建议门槛 |
| 来源许可、个人信息与跨境逐批审查 | 未由程序验证；手册及模板供实际部署负责人执行 |
| 用户机器 / 服务器部署、无人值守调度 | 未执行；提供方案与可复验命令 |
| 自动多跳挖掘、实体归一、逐候选审核入图 | 未实现；保持 PENDING / UNCONFIRMED |

合规引用已按官方法律文本和 RFC 核对，仍需结合实际来源条款、数据类型、供应商与用途判断。代码 SHA、模型版本、输入与配置应随真实试点保存。

## 复验命令

激活虚拟环境后，在仓库根目录执行；目录名重复则换新编号：

```bash
python -m unittest discover -s tests -q
python scripts/research.py prepare --target examples/search/target-nvidia.json --intensity deep --models none --providers brave --out research-runs/recheck-session-01
python scripts/research.py doctor --config research-runs/recheck-session-01/config.json --target research-runs/recheck-session-01/target.json
python scripts/research.py demo --out research-runs/recheck-demo-01
python scripts/research.py validate --run research-runs/recheck-demo-01/run.json
python scripts/research.py audit --run research-runs/recheck-demo-01/run.json --out research-runs/recheck-audit-01
python scripts/research.py compare --run research-runs/recheck-demo-01/run.json --fixture examples/search/synthetic.json --gold examples/search/synthetic-gold.json --out research-runs/recheck-compare-01
```

依次用于测试工程约束、生成计划、查看环境、演示闭环、检查完整性、查看技术缺口与验证冻结对照；均不能替代真实采集和人工事实审核。GitHub Actions 的同类离线检查随 PR 运行，具体结果查看 PR checks。
