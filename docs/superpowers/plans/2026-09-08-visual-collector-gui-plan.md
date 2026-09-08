# 可扩展商品采集桌面工具实施计划

## 实施原则

- 保留现有命令行采集方式，GUI 只编排既有能力。
- 平台判断、进程执行、结果导出和界面分别放在独立模块中。
- 先用标准库 `unittest` 固化链接匹配、事件流和结果格式，再接入 Tkinter。
- 所有 Windows 批处理脚本统一使用 UTF-8 无 BOM 和 CRLF。

## 任务 1：平台适配层

新增 `collector/platforms/base.py`、`collector/platforms/registry.py` 和 `collector/platforms/alibaba1688.py`。

- 定义平台适配器接口和采集上下文。
- 实现安全的 URL 域名与路径匹配，拒绝伪造域名。
- 规范化 1688 链接并提取商品 ID。
- 通过注册中心选择适配器，未知平台返回明确错误。
- 添加 `tests/test_platform_registry.py`。

## 任务 2：可取消的采集服务

新增 `collector/process_runner.py` 和 `collector/service.py`。

- 使用当前 Python 解释器运行 `utils.auto_collector` 和 `main.py`。
- 实时合并并转发标准输出与错误输出。
- 把七个阶段转换为结构化事件并发送至线程安全队列。
- 保存当前子进程引用；取消时只终止该进程及其子进程。
- 失败后总是发出可恢复的终止事件。
- 添加 `tests/test_collection_service.py`，通过假执行器验证顺序、失败与取消，不访问网络。

## 任务 3：结构化结果导出

新增 `collector/exporter.py`。

- 使用现有 `HTMLParser` 读取保存的 HTML。
- 生成统一 `product.json`，包含公共字段、资源 URL、SKU、店铺、采集时间和下载文件清单。
- 统计主图、色卡图、详情图、视频的已落盘数量。
- 保留空字段，不制造页面数据。
- 添加 `tests/test_exporter.py`，使用最小 HTML fixture 验证格式与 UTF-8 中文。

## 任务 4：完善新版 1688 页面字段

完成 `utils/parsers/alibaba_parser.py` 的现有补丁。

- 合并 `window.context` 中的 `featureAttributes`。
- 解析 `currentPricesWithOnePiece` 的阶梯价和首档引用。
- 验证目标商品得到 18 个属性、3 档阶梯价和 12 个 SKU。

## 任务 5：桌面界面

新增 `gui/url_collector_app.py` 和 `collector_gui.pyw`。

- 实现链接输入、平台状态、开始按钮、阶段进度、实时日志、结果摘要和打开目录。
- 使用主线程 `after()` 消费服务事件，后台线程不得直接操作控件。
- 运行时禁用输入，失败或成功后恢复。
- 支持 Enter 开始、Ctrl+A/复制日志和清晰可见的键盘焦点。
- 关闭运行中窗口时确认；确认后调用服务取消。
- 使用系统字体、4/8 像素间距节奏、高对比文本和文本化状态。
- 将 UI 格式化逻辑放入可独立测试的纯函数，并添加 `tests/test_gui_presenter.py`。

## 任务 6：双击启动与编码

新增 `start_collector_gui.bat`。

- 优先使用 `.venv\Scripts\pythonw.exe` 启动 `collector_gui.pyw`。
- 虚拟环境不存在时显示中文安装提示并保留窗口。
- 写入 UTF-8 无 BOM、CRLF 和 `chcp 65001 >nul`。
- 扩展 `tests/test_batch_encoding.py` 覆盖仓库内全部 `.bat`。

## 任务 7：验证目标商品

- 运行全部单元测试和相关模块静态编译。
- 对指定 1688 商品执行一次真实端到端采集。
- 校验 HTML 不是登录或验证码页。
- 校验 `product.json`、属性页、重建脚本、图片和视频。
- 使用 Pillow 验证图片，用 MP4 `ftyp` 文件头验证视频。
- 无破坏性启动所有 `.bat` 的安全路径，确认中文无乱码。
- 打开桌面窗口进行一次启动、非法链接和成功摘要的人工检查。

## 提交顺序

1. `feat: add extensible platform adapters`
2. `feat: add collection service and JSON exporter`
3. `feat: add URL collector desktop GUI`
4. `test: cover collector workflow and batch encoding`
5. `docs: document GUI usage and collected output`
