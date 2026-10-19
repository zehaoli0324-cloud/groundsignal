# 部署方案：从离线验证到小规模真实采集

适用范围：GroundSignal 搜索证据管线，2026-10-19。操作入口为 `scripts/research.py`，不是旧采集 UI。本方案先部署单机命令行任务，再考虑服务器；不需要先搭数据库、GPU 集群或训练模型。

当前实现仍在 [PR #5](https://github.com/zehaoli0324-cloud/groundsignal/pull/5)，依赖未合并的证据账本 PR #3。本文的新增命令在该 PR 分支上；只下载 main 可能找不到。真实来源许可、真实模型质量、无人值守运行尚未完成验收。

## 先选部署方式

| 方式 | 适用情况 | 本机负责什么 | 外部接收什么 |
|---|---|---|---|
| 仅采集、人工审核 | 首次试用；尚未选模型 | 搜索调度、正文保存、诊断 | 搜索 API 收到公司名、检索词；网站收到访问请求 |
| 本地小模型 | 数据不宜交给云模型；先测简单抽取 | 上述工作及 Qwen 推理 | 搜索服务仍会收到查询；正文不因本地推理而发给云模型 |
| 本地小模型 + 云端大模型 | 来源已允许第三方处理，需复杂关系复核 | 常规抽取、规则检查 | 被升级的正文片段、目标名称和提示词发送到配置的大模型端点 |
| 私有服务器 | 多人交接、集中保管；单机流程已通过 | 同上，另加运维与访问控制 | 取决于搜索和模型配置；“服务器在国内”不等于所有数据都不出境 |

推荐先用“仅采集”，再比较 9B + Flash 与 4B + Pro。4B、9B 是参数规模，不是可靠率；硬件是否够用应以实际量化版本、上下文长度及并发压测为准。初始并发固定为 1。公开模型的许可证、搜索 API 的商业条款也要分别检查。

## 步骤 1：取得正确代码并固定版本

**用途：** 确认使用 groundsignal，并让之后的结果能追溯到实际代码版本。

在装有 Git、Python 3.12 的终端中执行：

```bash
git clone --branch codex/search-evidence-pipeline-20261019 https://github.com/zehaoli0324-cloud/groundsignal.git
cd groundsignal
git status --short
git rev-parse HEAD
```

**产物与成功判据：** 目录包含 `scripts/research.py`、`requirements-search.txt`；`git status` 为空。把最后的 commit SHA 记入本次研究记录。已克隆的人先保存自己的修改，再切换或更新该分支；不要用强制重置覆盖工作。

**失败处理：** 找不到分支时查看 PR 是否已合并或改名；合并后可用 main 的明确提交。网络失败先处理 Git 访问，不要下载来源不明的同名仓库。

## 步骤 2：建立独立 Python 环境

**用途：** 隔离依赖，避免把采集工具安装进系统 Python。

以下主体命令适用于 macOS / Linux 的 Bash。Windows PowerShell 对应命令见本节末尾。

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-search.txt
python --version
```

**产物与成功判据：** Python 3.12；依赖安装无错误。默认安装 requests、HTML 解析、Schema 检查、pypdf；没有安装或启动 Qwen，也没有下载模型权重。

**失败处理：** 找不到 `python3.12` 时先安装 Python 3.12；不同系统的命令可能叫 `python3` 或 `py -3.12`，先核对版本。安装失败按 pip 的具体错误处理，不用管理员权限强装到系统环境。依赖目前是版本范围，跨时间安装可能不同；正式部署应另存 `python -m pip freeze`、操作系统和模型版本，后续补锁定文件。

Windows PowerShell 使用：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-search.txt
.\.venv\Scripts\python.exe scripts/research.py --help
```

不想调整 PowerShell 执行策略，可始终用 `.\.venv\Scripts\python.exe` 替换后文的 `python`；`cp` 改成 `Copy-Item`。Bash 的 `read/export/flock` 不适用于 PowerShell。

## 步骤 3：先跑不联网的工程演示

**用途：** 将安装错误与外部网站、API、模型问题分开定位。

```bash
python -m unittest discover -s tests -q
python scripts/research.py demo --out research-runs/install-demo-01
python scripts/research.py validate --run research-runs/install-demo-01/run.json
python scripts/research.py audit --run research-runs/install-demo-01/run.json --out research-runs/install-audit-01
```

**产物与成功判据：** 测试通过；演示为 `SYNTHETIC_ONLY`；完整性检查为 `CONTRACT_VALID`；审计为 `TECHNICAL_AUDIT_ONLY`，事实精度仍为 `UNASSESSED`。这些命令不调用真实搜索或模型。

**失败处理：** 输出目录必须不存在或为空；重复执行换 `-02`。完整性错误要回查文件或重新生成，不能删掉指纹字段绕过检查。合成演示成功只说明工程链路可运行。

## 步骤 4：建立目标与来源准入记录

**用途：** 在花搜索费、下载全文之前，明确研究对象、时间、范围和允许的数据流。

```bash
mkdir -p research-runs/setup-01
cp examples/search/target-nvidia.json research-runs/setup-01/target.json
cp docs/templates/research-review.md research-runs/setup-01/review.md
```

编辑 `target.json`：公司名称及别名、已核对的官网域名、九个研究维度、时间区间、允许抓取的 `seed_urls`。示例 NVIDIA 不是主体核验结果；替换目标时也要替换 ID、别名、域名和种子，不要只改中文名。

在 `review.md` 登记来源条款、自动访问许可、原文保存权、第三方模型处理权、公开分享权及保留期限；分别写“允许 / 禁止 / 待核实”和依据。规则见 [合规与质量方案](21-compliance-quality.md)。这里的表是人工门禁，程序尚未读取并强制执行它。

**产物与成功判据：** 能区分品牌与法人、母子公司；来源准入有责任人。未知权限的来源先不加入抓取名单；正文的云端处理权未知时保持大模型关闭。

**失败处理：** 同名公司、付费库、个人资料、授权范围有疑问时，缩小到明确许可的公司公开文件，必要时找数据提供方或法务确认。`official_domains` 仅控制来源偏好及可选浏览器范围，不是 HTTP 抓取的全局许可白名单。

## 步骤 5：生成一个有预算的工作会话

**用途：** 把搜索强度、提供商、模型选择落实为可审查配置，避免先启动再猜花费。

先只用一个已获准使用的搜索 API，例如 Brave：

```bash
python scripts/research.py prepare --target research-runs/setup-01/target.json --intensity quick --models none --providers brave --out research-runs/session-01
```

**产物与成功判据：** `session-01/` 有 `target.json`、`config.json`、`plan-preview.json`、`session.json`；状态 `PREPARED_OFFLINE`。此时无网络、无模型调用。检查查询是否指向正确公司，`unplanned_dimensions` 是否为空。

只抓人工已批准的种子，可把末尾写为 `--providers --out research-runs/session-01`，生成空提供商列表。必须确有 `seed_urls`。这是当前先逐源准入、再采集的可控方式；一般搜索运行会自动抓取命中，并没有逐条 URL 批准界面。

**失败处理：** 目标格式错误先修 JSON；查询过长先用准确短别名、缩小目标，不删掉主体约束。预算含义和三档差异见 [搜索与挖掘方案](20-search-mining-strategy.md)。调用上限不是货币限额，应同时在服务商控制台限制花费。

## 步骤 6：安全配置搜索密钥并检查环境

**用途：** 用真实身份访问获准的搜索 API，同时让密钥留在进程环境中。

Bash 中以隐藏输入方式设置，输入自己的服务商密钥：

```bash
read -r -s -p 'BRAVE_SEARCH_API_KEY: ' BRAVE_SEARCH_API_KEY
export BRAVE_SEARCH_API_KEY
python scripts/research.py doctor --config research-runs/session-01/config.json --target research-runs/session-01/target.json
```

`TAVILY_API_KEY / FIRECRAWL_API_KEY / DEEPSEEK_API_KEY` 同理，只设置选择的服务。程序不会自动加载 `.env`；不要把真实密钥放进 JSON、命令参数、截图、issue 或 Git。PowerShell 可通过操作系统密钥管理工具向当前进程注入环境变量，避免把明文写入历史。

**产物与成功判据：** 对应 `key_present=true`，依赖齐全，`collection_configuration_ready=true`。默认 doctor 完全离线，仅检查配置和环境变量是否存在；不证明密钥有效、余额足够或网站可访问。模型关闭时 `extraction_configuration_ready=false` 是预期。

**失败处理：** 先检查变量是否在同一个终端 / 服务进程中。doctor 退出码 0 只表示诊断完成，必须看字段。网络鉴权、余额及限流要在下一步的小批实跑中判断；不要打印密钥排查。

## 步骤 7：做一轮小批真实采集

**用途：** 验证查询、API、robots、正文下载和本地保存，先不把未知内容交给模型。

```bash
python scripts/research.py run --target research-runs/session-01/target.json --config research-runs/session-01/config.json --out research-runs/capture-01
python scripts/research.py audit --run research-runs/capture-01/run.json --out research-runs/capture-audit-01
```

**产物与成功判据：** 阅读 `report.md` 和 `audit.json`；至少有相关正文，能打开原 URL 并核对快照。模型关闭时 `COLLECTED_MODEL_NOT_COMPLETED` 是预期；它不是模型失败或已经核实。无正文 `NO_USABLE_DOCUMENTS` 返回 2，仍保存诊断。

**失败处理：** 依次区分 `NOT_CONFIGURED`、鉴权/余额、DNS、超时、429、robots、验证页、扫描 PDF。缺正文不能由模型补写。429 等待 Retry-After；拒绝访问、验证码、登录付费墙停止该来源。不要通过代理池、换账号或伪装身份绕过限制。

## 步骤 8：可选安装本地小模型，再显式开启大模型

**用途：** 在冻结原文上测结构化抽取；把常规工作交给小模型，困难样本才升级。

从 [Ollama 官方说明](https://docs.ollama.com/quickstart) 安装对应系统版本后：

```bash
ollama pull qwen3.5:9b
ollama serve
```

如果桌面应用或后台服务已经运行，不必启动第二个 `serve`。另一终端回到虚拟环境，在来源允许云处理后生成新配置：

```bash
python scripts/research.py prepare --target research-runs/session-01/target.json --intensity quick --models qwen9b-flash --providers brave --out research-runs/model-session-01
python scripts/research.py doctor --config research-runs/model-session-01/config.json --probe
```

`--probe` 仅向配置的 loopback 本地端点请求 `/models`，不发 prompt、不调用云 API；`MODEL_LISTED` 只表示服务列出这个名字。远端为 `REMOTE_NOT_PROBED`。如果本地服务列表使用其他模型 ID，应按真实 ID 修改配置。

只有确认相关来源可送给该供应商时，才用隐藏输入设置 `DEEPSEEK_API_KEY`；再执行：

```bash
python scripts/research.py extract --run research-runs/capture-01/run.json --config research-runs/model-session-01/config.json --out research-runs/extract-01
```

**产物与成功判据：** 有真实模型 attempt、请求/返回模型名、输入哈希、token 与耗时；候选仍为 `PENDING`。这一步是推理，不会训练或自动改善模型。

**失败处理：** 显存/内存不足降低模型规模或上下文，重新评测；不要直接把本地服务暴露到公网。云处理不允许时，将配置改为 `routing_mode=small_only`、`models.large.enabled=false`；不能一边保留 cascade 的云升级，一边称数据仅在本地处理。当前没有自动脱敏与脱敏后引文映射，不适宜外传的材料应全程本地处理或排除。

## 步骤 9：服务器部署与交接

**用途：** 在单机验证后获得稳定的文件保管和可重复运行环境，而不是直接扩大抓取量。

| 操作 | 用途与验收 | 失败处理 |
|---|---|---|
| 用独立普通用户完成步骤 1–8，固定代码 SHA | 不以 root 运行爬虫或模型；记录 Python、pip freeze、模型版本、配置 | 单机流程未通过时先不迁移 |
| 对运行目录使用 `umask 077`，文件系统启用受控访问与加密备份 | 原文、人物信息、研究结论仅授权人员可读；Git 忽略不等于加密 | 检查目录权限及备份恢复，不公开挂载整个仓库 |
| 用部署平台 secret store 向进程注入密钥 | 密钥不写服务文件、镜像和日志 | 泄露后撤销、轮换，检查历史和导出文件 |
| 本地模型只监听 loopback，外部网络用出站规则限制 | 防止公开推理接口；可选浏览器另用隔离环境控制子资源和私网访问 | 未能隔离时继续使用默认 HTTP 抓取 |
| 同一仓库运行任务串行；Linux 可用 `flock` 包住命令 | 本版缓存限流不是跨进程锁；避免重复抓取和额度竞争 | 并发需求先加任务队列，不能只开多个进程 |
| 每次用新运行目录，采集与抽取分开，保存日志和清单 | 失败能定位、原文能复用；中断不冒充完成 | 当前没有断点续跑；保留 search-progress，新任务换目录 |
| 演练恢复后才上线，首次仍为 quick | 能找回输入、输出、审核和授权记录；下线时停进程、撤销密钥、按保留策略处置数据 | 不直接部署自动定时或公开服务 |

Linux 串行执行示例，在仓库根目录且环境变量已注入时：

```bash
umask 077
flock -n .collector-run.lock .venv/bin/python scripts/research.py run --target research-runs/session-01/target.json --config research-runs/session-01/config.json --out research-runs/server-capture-01
```

已有任务时锁会拒绝运行；不要为了通过而删除正在使用的锁。`max_elapsed_seconds` 在工作单元边界检查，在途请求受单次 timeout 约束；需要硬截止应由作业平台终止进程。杀死进程可能只有部分进度，没有完整 run.json，不能套用完成运行的审计。

## 部署验收与后续生产化

| 门槛 | 需要的证据 | 当前状态 |
|---|---|---|
| 工程安装 | 离线测试、demo、完整性与审计命令 | 本分支可复验；本次记录见 22 号文档 |
| 外部连接 | 选定 API 的有效请求、允许站点的真实正文 | 必须在部署网络验证；当前环境没有成功的真实采集证明 |
| 模型运行 | 本地推理及获准的云调用记录 | 未在本环境下载权重或运行真实模型 |
| 质量与合规 | 人工金标、复审结果、来源权利与数据流登记 | 不能由测试通过或 doctor 代替 |
| 持续服务 | 锁定依赖、任务队列、逐源准入门禁、访问审计、备份恢复、故障告警 | 规划项；当前 CLI 不等于生产平台 |

下一步按 [日常使用方案](19-usage-guide.md) 做研究闭环。Ollama 的 [兼容 API](https://docs.ollama.com/api/openai-compatibility)、[模型列表](https://docs.ollama.com/api/tags)、[上下文与内存说明](https://docs.ollama.com/context-length) 用于部署核对；模型标签和服务价格都可能改变，使用时以供应商实际返回及条款为准。
