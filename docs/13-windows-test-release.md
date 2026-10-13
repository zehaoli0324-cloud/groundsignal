# Windows 用户测试版

本次交付为便携 ZIP：完整解压后双击 `GroundSignal.exe`，本地服务打开默认浏览器。
应用自带 Python 和依赖，无需测试者安装开发环境。界面采用原有浏览器 UI，尚未增加独立桌面窗口或安装向导。

## 测试者的流程

1. 安装 Obsidian 桌面版，创建或打开一个笔记库。
2. 解压应用，双击 EXE。
3. 点击“连接 Obsidian”，选择自动发现的笔记库，或使用“选择文件夹”。
4. 点击“连接并保存”，程序识别 `.obsidian` 并通过一个自动清理的临时文件验证写入权限。
5. 输入公司名称，搜索并保存；通过界面打开 Obsidian 或查看来源。

用户设置和搜索缓存保存在 `%LOCALAPPDATA%\GroundSignal`，笔记写入其自行选择的笔记库。
源码开发模式仍使用项目配置，两者互不覆盖。发行包不包含开发者的配置、缓存或笔记。

## 重新打包

在 Windows 的项目根目录执行：

```powershell
python -m venv .build-venv
.\.build-venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.\.build-venv\Scripts\python.exe scripts/build_windows.py
.\.build-venv\Scripts\python.exe scripts/smoke_windows_package.py
```

产物在 `release/`：ZIP、SHA-256 校验文件、`windows/GroundSignal/` 解压版。
附带用户说明和第三方许可；具体依赖版本在包内 `build-info.json`。
发布包由 PyInstaller 显式收集入口模块及单个 HTML 模板，不复制整个项目。

## 分发与测试边界

本版本针对 Windows x64，先提供给少量用户测试。请发送 ZIP 并提醒完整解压，不要只拷贝 EXE。
没有代码签名、自动更新或安装程序；组织的应用控制可能阻止未签名程序，需要由管理员审核。
本机测试可验证 EXE 在移除 Python PATH 后独立启动、连接笔记库和重启记忆；不能代替无开发环境的新电脑测试。
请至少在一台未安装 Python 的 Windows 10/11 x64 电脑验证首次运行、中文路径、目录权限、Obsidian 打开及搜索。
公开搜索服务的限流与事实核验边界不会因打包改变。

架构依据：[PyInstaller 运行时路径](https://pyinstaller.org/en/stable/runtime-information.html)、[Obsidian URI](https://obsidian.md/help/uri)。


批量更新公司资料
连接笔记库后，点击“更新全部公司”或“更新指定公司”。全部范围是 01-公司 文件夹下的公司笔记（不含子目录）。指定更新支持名称筛选、多选。更新会重新搜索并刷新自动采集区，保留手工内容与历史来源记录，不会自动把待核实信息变成已核实。
任务逐家处理，显示成功/失败结果；失败后可点击“重试失败项”。点击“停止剩余更新”后会先完成当前公司。请保持服务运行，队列不支持退出后恢复。搜索限速和冷却仍有效，失败时已有笔记不因搜索失败而删除。
