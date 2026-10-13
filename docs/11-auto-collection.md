# 自动搜索并写入 Obsidian

原来的 `ask.py` 只读取本地 Markdown，静态 HTML 中的搜索框没有采集后端。
现在 `scripts/collect.py` 负责联网检索、抓取网页和写入笔记。不需要手工准备 YAML 或 API key。

## 使用

Windows 图形界面：双击项目根目录 `启动采集界面.vbs`，即可在浏览器里搜索、查看进度和记录、打开 Obsidian 笔记。界面默认仅监听本机 `127.0.0.1:8765`，复用现有仓库配置。页面底部可退出采集服务。

在项目根目录安装依赖：`python -m pip install -r requirements.txt`。
在 `collector-config.json` 设置 vault（也可直接在界面选择笔记库）。

```powershell
python scripts/collect.py "瑞芯微" "杭州临芯"
# 任意其他公司，流程相同：
python scripts/collect.py "公司名称"
# 联网预演，不写入：
python scripts/collect.py "公司名称" --dry-run
# 指定其他仓库：
python scripts/collect.py "公司名称" --vault "D:\Vault"
```

也可以运行 `./collect-company.ps1` 后输入公司名称。
需要看板时使用原查询工具的新参数（此模式只接受公司名，不接受问题句式）：

```powershell
python scripts/ask.py "D:\Obsidian\产业情报" "公司名称" --collect -o board.html
```

## 输出与边界

- `01-公司/公司名.md`：新实体生成待核实笔记；已有笔记只替换自动采集标记区，保留人工正文、属性和关系。
- `09-采集记录/公司名-内容摘要.md`：来源 URL、搜索摘要、网页摘录、抓取时间和失败原因。
- 同名 JSON 保留结构化采集结果；相同内容复用记录，改变的内容保留新版本。
- 搜索仅按名称筛选，不自动确认法律主体；简称可能匹配多个主体，需核实。
- 搜索默认依次使用搜狗、360 的公开结果页。一个搜索源受限、无匹配或网络失败时尝试下一个，不绕过验证码。仍要求结果包含公司名称，不把不相关结果作为成功。
- 同一名称和来源数量的搜索结果缓存 6 小时；原始搜索时间与本次网页采集时间分开记录。缓存仅覆盖搜索结果，原网页仍会重新读取。
- 同一搜索源请求间隔至少 5 秒；验证码、HTTP 403/429 会暂停该源至少 30 分钟。暂停状态与缓存保存在项目 `.collector-cache/`，重启也保留。`Retry-After` 秒数更长时按更长时间暂停。
- 界面显示实际搜索来源；全部失败时列出各源的原因，区分验证限制、无名称匹配、网络故障和页面结构变化。
- 可选正式搜索 API：在启动程序的环境中设置 `BRAVE_SEARCH_API_KEY` 后优先使用 Brave Search API。密钥只放在 HTTP 请求头，不写入笔记或前端。需要自行申请有效凭据，可能产生服务费用；本次默认流程未使用付费 API。[官方认证文档](https://api-dashboard.search.brave.com/documentation/guides/authentication)
- 来源登录限制或动态页面可能无法获取正文，只保存搜索线索并标注失败；未绕过访问限制。
- 不把搜索摘要变成已验证事实，不自动推断投资、客户或供应关系。
- 这是手动触发的自动采集入口，没有配置后台定时任务；旧 HTML 搜索框仍是静态表单，不会触发联网采集。

运行验证：`python -m unittest discover -s tests -v`。
