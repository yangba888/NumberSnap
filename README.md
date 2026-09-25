# NumberSnap

NumberSnap 是一个仅在本机运行的 Windows 数字表格截图 OCR 工具。按下
`Ctrl + Shift + X`，框选数字区域后，程序会恢复行列并将 TSV 写入剪贴板，
可直接粘贴到 Excel、WPS 或 Google Sheets。仅识别数字这一项特别适用于工作中报计划。

## 功能

- `Ctrl + Shift + X` 全局快捷键启动多屏截图框选，`Esc` 取消。
- `Ctrl + Shift + Z` 显示或隐藏后台主窗口；两组快捷键均可编辑并持久保存。
- RapidOCR 在后台线程进行本地识别，界面不会因 OCR 阻塞。
- 默认仅保留数字、正负号、小数点、千位分隔符、百分号及 `¥/$/€`。
- 原始 OCR 文本、置信度、四点 Bounding Box 与归一化文本分别保留。
- 按动态字符高度聚类行，按 X 坐标检测列，并为缺失单元格输出空 TSV 字段。
- 自动复制到系统剪贴板，托盘通知识别数量及表格尺寸。
- 右上角关闭隐藏到后台，右下角“关闭”按钮彻底退出程序。
- 支持跟随系统、浅色和深色主题；顶栏使用轻量半透明渐变和细分割线。
- 可选开机自启，登录后静默进入托盘；重复启动会唤醒已有窗口。
- OCR、NumPy 与工作线程按需加载，并限制原生线程池以降低空闲内存。

## 技术选择

- **PySide6 Essentials**：窗口、截图遮罩、托盘、通知与剪贴板统一由 Qt 提供；不安装
  本项目未使用的 PySide6 Addons，以减少开发环境和发布内容。
- **RapidOCR + ONNX Runtime**：完全本地 OCR，模型随 Python 包安装并在首次识别时初始化，
  不调用云 API。OCR 引擎在 Worker Thread 中复用，避免每次重新加载模型。
- **Qt 屏幕捕获替代 mss**：Qt 能在多显示器和 Windows DPI 缩放环境中让截图坐标与
  遮罩窗口保持同一坐标系，也减少一个运行时依赖。
- **Windows `RegisterHotKey` API**：全局快捷键不额外引入键盘钩子依赖。
- **纯 Python 布局算法**：便于使用模拟 Bounding Box 做快速、确定性的单元测试。

程序默认不保存截图。只有未来显式启用 Debug 截图选项时才允许保存；当前版本即使
开启 debug 日志也只记录 OCR 文本、置信度、坐标和布局过程。

## 开发环境

需要 Windows 10/11 和 Python 3.12 或更新版本。推荐使用项目内虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m numbersnap
```

运行测试：

```powershell
python -m pytest
python -m ruff check numbersnap tests scripts
python scripts\ocr_smoke.py
```

构建发布版：

```powershell
.\build.ps1
```

输出位于 `dist\NumberSnap\NumberSnap.exe`。

`build.ps1` 会先运行测试，测试成功后才调用 `NumberSnap.spec`。Spec 会收集 RapidOCR
模型数据及 ONNX Runtime 动态库，输出为目录模式，启动速度优于单文件自解压模式。

## 使用

1. 启动 `python -m numbersnap` 或打包后的 `NumberSnap.exe`。
2. 按 `Ctrl + Shift + X`，按住鼠标左键框选数字表格，松开确认；右键或 `Esc` 取消。
3. 收到“已识别 … · 已复制”通知后，在表格应用中按 `Ctrl + V`。
4. 修改快捷键后点击对应的“保存”，新快捷键立即生效。
5. 右上角关闭隐藏到后台；右下角“关闭”按钮直接结束程序。

若快捷键已被其他程序占用，NumberSnap 会显示托盘错误通知，仍可使用窗口或托盘中的
“截图识别”。首次识别需要加载 OCR 模型，后续识别会复用已加载实例。

开机自启使用当前用户的 Windows `Run` 启动项，不需要管理员权限。如果用户在
Windows“启动应用”中禁用 NumberSnap，程序不会自动重新开启。发布包移动后，
仅在用户原本已开启自启时修复路径。
快捷键等个人设置以 JSON 保存在 `%LOCALAPPDATA%\NumberSnap\settings.json`，更新发布包不会覆盖。

便携版卸载前可运行 `NumberSnap.exe --uninstall-cleanup` 清理启动项并保留个人设置；
如用户同时选择删除个人设置，使用 `--uninstall-cleanup --remove-user-data`。

## 项目结构

```text
numbersnap/
  main.py                 # 程序入口
  app.py                  # UI 工作流编排
  config/settings.py      # 本地 JSON 设置
  core/
    capture.py            # 多屏内存截图
    ocr_engine.py         # RapidOCR 适配与原始结果保留
    worker.py             # OCR 后台线程任务
    normalization.py      # 保守 OCR 字符纠正
    number_filter.py      # 数字提取
    layout_detector.py    # 动态行列恢复
    formatter.py          # TSV 格式化
    clipboard.py          # Qt 剪贴板
    hotkey.py             # Windows RegisterHotKey
  ui/
    main_window.py
    screenshot_overlay.py
    tray.py
    notification.py
tests/                    # 不依赖真实截图的核心算法测试
scripts/ocr_smoke.py      # 内存生成图像的 OCR 集成烟测
NumberSnap.spec
build.ps1
```

## 算法说明

OCR 单元始终以字符串保存，因此 `00123` 不会丢失前导零。归一化只在整个 OCR token
呈现明确数字上下文时将 `O/o` 改为 `0`、`I/l` 改为 `1`；普通单词不会被修改。

布局检测先以 Bounding Box 中心 Y 与动态中位高度阈值聚类行。列数由信息最完整的行
初始化，再以所有行的中心 X 中位数迭代校正。稀疏行通过保持从左到右顺序的动态规划
映射到列，所以中间缺失值能输出为空字段。该实现没有固定像素阈值，模块可独立替换。

第一版的列检测假设至少有一行包含全部列；若截图中每一行都缺少不同列，无法从视觉
位置唯一推断完整表格宽度。复杂合并单元格、旋转文本和手写数字不在第一版范围内。

## 日志

默认记录启动、快捷键和耗时摘要。将配置文件中的 `debug` 设为 `true` 后，会额外记录
OCR 原文、归一化文本、置信度、Bounding Box、行列聚类及最终二维数组。即使 Debug
开启也不会保存截图。配置文件位于 Qt 返回的 Windows `AppConfigLocation` 下。

## 隐私

截图仅保留在内存中用于当前 OCR，不上传、不写数据库、不需要账号。应用日志不会
记录截图像素。

仓库的 `.gitignore` 会排除虚拟环境、构建产物、压缩包、调试截图、日志、编辑器配置、
环境变量文件以及常见密钥/证书文件。提交代码前仍应避免把个人截图、账号配置或密钥
复制进源码目录。

## 开源许可

NumberSnap 使用 [MIT License](LICENSE) 开源，可在保留许可证与版权声明的前提下使用、
修改和分发。
