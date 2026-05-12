# Sprint 2026.05.12_15-16 Phone Browser Acceptance Gate - PRD

## 状态

- 阶段：prd
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 产品目标：O5 phone browser acceptance gate
- 证据边界：`software_proof_docker_phone_browser_acceptance_gate`

## 用户价值和产品北极星

普通用户只应通过手机入口理解机器人能不能开始任务、为什么不能操作、什么时候需要等待或联系支持。上一轮已经证明按钮安全 gate 的 API/HTML handler wiring，本轮要证明页面在真实浏览器中可读、可点、不会把 diagnostics 的可进入误导成主操作可用。

北极星保持不变：手机是普通用户唯一入口；本地 operator HTML 是 fallback 调试入口，但也必须满足基本手机浏览器可用性，不能停留在 API contract。

## 问题定义

当前 O5 最大可行动缺口不是再新增一个 readiness 字段，而是缺真实浏览器层证据：

- handler/unit test 能证明 HTML 字符串包含控件，但不能证明移动 viewport 下布局不重叠。
- API payload 能证明 `command_safety.actions.*.enabled` 正确，但不能证明按钮 hit area >= 44pt。
- ACK 文案写入 contract 后，还需要在首屏真实可见。
- Diagnostics 可进入是支持入口，不应让用户误以为 Start/Confirm/Cancel 可以执行。

## OKR 映射

- O5 KR1：用户最小流程中的首屏状态查看、一键发车、确认投放和取消操作进入浏览器验收。
- O5 KR5：普通用户不用命令行，也能从首屏看到下一步和失败/阻断原因。
- O5 KR7：手机端 UI 美观且能直接使用，本轮至少证明本地 fallback 页面满足响应式、44pt hit area 和首屏可读。
- O6 KR6：弱网恢复摘要可作为首屏文案素材，但本轮不以 O6 进度为主目标。

## KR 拆解或更新

本轮完成后，O5 可考虑从约 40% 保守上调到约 42%，前提是 P0 browser acceptance 证据全部满足。

不允许上调的情况：

- 只新增文档，没有真实浏览器运行证据。
- 只跑 API/handler/unit test，没有 viewport、hit area 或重叠检查。
- 页面截图显示关键文案不可见、遮挡、按钮过小或 diagnostics 与主操作状态混淆。
- 证据没有明确 `software_proof_docker_phone_browser_acceptance_gate` 边界。

## 本轮核心抓手

核心抓手是一个最小但真实的 browser acceptance gate：

- viewport：至少覆盖 phone narrow 和 desktop/narrow web 两类；建议 `390x844` 与 `768x900`。
- 首屏：不滚动或少量滚动内能看到 readiness/command safety、主操作按钮、ACK 语义和 diagnostics 入口。
- hit area：Start Delivery、Confirm Dropoff、Cancel、Diagnostics 可点击区域均 >= 44 CSS px 高和宽。
- safety copy：展示阻断原因、recovery hint、ACK 语义；不展示 raw JSON、ROS topic、serial、token 或硬件参数。
- diagnostics：可以进入或打开，但不会让 blocked primary actions 变成 enabled。

## 范围

In scope：

- 本地 operator gateway HTML/CSS/JS 的移动浏览器可用性。
- `/api/status.phone_readiness.command_safety` 的 UI 消费验证。
- 浏览器自动化脚本、targeted tests 或最小 smoke。
- `docs/product/mobile_user_flow.md` 和本 sprint `tech-done.md` 的同步更新。

Out of scope：

- 正式 native app 或生产账号系统。
- 真实手机设备验收、真机 Safari/Chrome 手动验收。
- 真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM。
- 真实 OSS upload、CDN origin fetch、STS、生产 DB/queue。
- Nav2/fixed-route 送达、WAVE ROVER motion、真实 HIL 或垃圾送达。

## 优先级和验收口径

P0 验收：

- Full-stack 给出 browser acceptance 命令，能在本地/Docker 环境打开 operator 页面。
- 命令输出包含 viewport、hit area、visible text、primary action enabled/disabled、diagnostics access 和 screenshot/evidence 路径。
- 至少一个阻断状态证明 Start/Confirm/Cancel disabled，Diagnostics accessible。
- ACK copy 在首屏可见，且文案明确 ACK 只代表 command accepted/processing evidence。
- `git diff --check` scoped 到实际改动文件通过。

P1 验收：

- 两个手机尺寸截图。
- network recovery summary 首屏或 diagnostics 入口可见性检查。
- 结构化 JSON evidence 便于后续 `side2side_check.md` 引用。

## 对应责任 Engineer

- 主责：`full-stack-software-engineer`。
- 可咨询：`robot-software-engineer`，只处理 command/status/ack contract 兼容性。
- Product 收口：`product-okr-owner`。

## 风险和阻塞

- 如果 CI/Docker 缺浏览器依赖，本轮可用本地浏览器或 Playwright install 方式解决，但必须记录命令和环境；不能降级为上一轮同类 handler proof。
- 如果页面需要启动 ROS2 node 才能提供状态，Full-stack 应用 lightweight HTTP test server 或 fixture 注入，避免扩大到硬件/HIL。
- 如果修 UI 触碰 API shape，必须保持旧客户端可忽略新增字段。

## 需要更新的文档

- 本轮实施时必须更新 `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/tech-done.md`。
- UI/验收口径变化必须同步 `docs/product/mobile_user_flow.md`。
- 若接口 contract 改动，必须同步 `docs/interfaces/ros_contracts.md`。
- 收口时 Product 更新 `side2side_check.md`、`final.md` 和 `OKR.md`。
