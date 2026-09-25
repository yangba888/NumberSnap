# NumberSnap Agent Guide

## 项目简介

NumberSnap 是一个仅支持 Windows 的本地截图数字 OCR 工具。用户框选屏幕区域后，
程序提取数字、根据 Bounding Box 恢复表格行列，并将 TSV 纯文本复制到剪贴板。

## 技术栈

- Python 3.12+
- PySide6 Essentials
- RapidOCR + ONNX Runtime
- NumPy
- PyInstaller
- pytest + Ruff

禁止引入云端 OCR、Web 服务、数据库、账号系统或不必要的大型依赖。

## 目录职责

- `numbersnap/app.py`：应用流程编排、快捷键、截图和 OCR 调度。
- `numbersnap/config/`：本地设置。
- `numbersnap/core/`：截图、OCR、过滤、排版、剪贴板和系统功能。
- `numbersnap/ui/`：主窗口、标题栏、托盘、截图遮罩和通知。
- `tests/`：无需真实截图的单元测试。
- `NumberSnap.spec`：PyInstaller 配置。

保持职责分离，不要把功能集中到 `main.py`。

## 现有产品行为

- 截图快捷键默认 `Ctrl+Shift+X`，可编辑。
- 显示/隐藏窗口快捷键默认 `Ctrl+Shift+Z`，可编辑。
- 右上角关闭按钮隐藏到后台；右下角“关闭”彻底退出。
- 截图时左键拖选，右键或 `Esc` 取消。
- 支持跟随系统、浅色和深色主题。
- 剪贴板只能写入 `text/plain` / `CF_UNICODETEXT`，禁止添加 HTML 或 RTF。
- OCR、NumPy 和工作线程延迟加载；不要破坏现有轻量化策略。
- OCR 忙碌时不得继续堆积截图任务。

## 开发原则

- 遵守 KISS、单一职责和关注点分离。
- 保持现有 UI、功能和操作逻辑，除非任务明确要求改变。
- OCR 文本始终按字符串处理，必须保留 `00123` 等前导零。
- 排版必须使用 Bounding Box 坐标，不能依赖 OCR 返回顺序。
- 阈值应根据字符高度和间距动态计算，禁止硬编码固定像素值。
- 不在 GUI 主线程执行 OCR。
- 不用频繁 `gc.collect()` 掩盖资源生命周期问题。
- 新增长期线程、定时器或大型常驻对象前，先评估内存影响。

## 隐私与安全

- 截图只允许保存在内存中，不得上传或默认写入磁盘。
- 不提交用户截图、日志、配置、密钥、Token、证书或个人路径。
- 不打印或记录剪贴板内容、认证凭据和完整截图数据。
- 提交前检查 `.gitignore`，确保 `.tools/`、`build/`、`dist-*/`、
  `debug-captures/`、`.env*` 和压缩包未被跟踪。
- GitHub 仓库保持私有，除非用户明确要求公开。

## 修改与验证

修改代码后至少运行：

```powershell
.\.tools\python312\python.exe -m ruff check numbersnap tests scripts
.\.tools\python312\python.exe -m pytest -p no:cacheprovider
```

涉及 OCR、线程、快捷键、剪贴板或 UI 时，还应运行对应冒烟测试。发布前执行：

```powershell
.\build.ps1
```

不要为了通过测试而删除断言或降低测试覆盖。修复缺陷时应增加回归测试。

## 版本与发布

- 同步更新 `numbersnap/__init__.py`、`numbersnap/main.py` 和 `pyproject.toml`。
- 在 `CHANGELOG.md` 记录用户可见变化。
- 构建产物不得提交 Git，只提交源码、测试和文档。
- 推送前运行隐私扫描并确认 `git status` 中没有个人文件。
- 不使用破坏性 Git 命令，不覆盖用户未提交的修改。
