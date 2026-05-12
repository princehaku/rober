# Sprint 2026.05.12_15-16 Phone Browser Acceptance Gate - Pre Start

## 状态

- 阶段：pre_start
- 启动时间：2026-05-12 15:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性咨询：`robot-software-engineer`，仅在 API/command contract 退化风险出现时介入
- 目标证据边界：`software_proof_docker_phone_browser_acceptance_gate`
- 本轮限制：本机无真实手机设备、无真实硬件、无真实云/4G、无 HIL；只做 Docker/local browser software proof

## 背景证据

Live `OKR.md` 显示 Objective 5 约 40%、Objective 6 约 41%，O1-O4 约 74-76%。当前最低且可在 Docker/local 主机推进的是 O5 手机体验，不是 O1 HIL 或 O6 真实云。

最近证据链：

- `sprints/2026.05.12_13-14_phone-command-safety-browser-gate/final.md` 已完成按钮级 `command_safety` API/HTML handler proof，但明确没有真实浏览器/手机设备截图。
- `sprints/2026.05.12_14-15_remote-network-recovery-drill/final.md` 只给 O5 增加 phone-safe network recovery 摘要支撑，不提升 O5。
- `docs/product/mobile_user_flow.md` 已定义本地 operator gateway 是 phone-first fallback HTML，ACK 只代表 command accepted/processing evidence，不等于送达成功。

## 用户价值和产品北极星

用户价值：普通 operator 用手机浏览器打开本地页面时，首屏必须能看懂当前能不能操作、为什么不能操作、ACK 代表什么，以及 diagnostics 入口能进入但不代表主操作可用。

产品北极星：手机是普通用户唯一入口。当前本地 fallback HTML 必须先具备真实浏览器可用性证据，才能继续向正式手机 app、真实云/4G 和普通用户验收推进。

## OKR 映射

- O5 KR1：手机端最小流程从 API/handler proof 推进到真实浏览器渲染 proof。
- O5 KR5：普通用户不接触命令行，也能从首屏理解状态、阻断原因和失败恢复提示。
- O5 KR7：覆盖响应式布局、主流窄屏宽度、最小可点击区域 >= 44pt、首屏可读、不重叠。
- O6 KR1/KR6：仅作为 command safety 和 network recovery 摘要的消费背景，不作为本轮主提升目标。

## 本轮核心抓手

把上一轮 `command_safety` 从 API/HTML handler proof 推到本地真实浏览器 acceptance gate：

- 用真实浏览器自动化打开 operator 首屏，而不是只检查 HTML 字符串。
- 覆盖手机窄屏和桌面窄窗口至少两个 viewport。
- 检查 Start、Confirm dropoff、Cancel、Diagnostics 的 hit area 不小于 44 CSS px。
- 检查首屏关键文案可见且不重叠：`command_safety` 阻断文案、ACK 语义、status/recovery copy。
- 检查 Diagnostics 可进入，但其可进入状态不能让 Start/Confirm/Cancel 误显示为可用。

## 需要做什么

1. Full-stack 启动本地 operator HTTP surface 或等价 test server。
2. Full-stack 编写最小 browser acceptance 围栏，产出可复查日志或截图路径。
3. Full-stack 修正 operator HTML/CSS/JS 中导致移动端不可读、重叠或 hit area 不足的问题。
4. Full-stack 同步 `docs/product/mobile_user_flow.md` 或接口文档，写清 browser acceptance gate 和证据边界。
5. Full-stack 更新本 sprint `tech-done.md`，记录实际改动、截图/日志、验证命令和剩余风险。
6. Product 收口阶段再更新 `side2side_check.md`、`final.md` 和 `OKR.md`。本计划阶段不得改 `OKR.md`。

## 优先级和验收口径

P0 必须满足：

- 真实浏览器自动化能打开本地 operator 页面并完成截图或结构化 layout 检查。
- 手机窄屏首屏不出现关键文案重叠；Start/Confirm/Cancel/Diagnostics hit area 均 >= 44 CSS px。
- command safety 文案和 ACK 不等于 delivery success 的文案在首屏可见。
- Diagnostics 可点击或可进入，但 Start/Confirm/Cancel 在阻断状态保持 disabled。
- 验收输出必须明确 `software_proof_docker_phone_browser_acceptance_gate`。

P1 可选：

- 增加 Android-like 与 iPhone-like 两个 viewport。
- 保存 PNG 截图到 sprint evidence 子目录。
- 对 network recovery 摘要做一次可见性检查，但不把它作为 O5 提升必要条件。

## 对应责任 Engineer

- `full-stack-software-engineer`：主责本轮实现、browser acceptance、targeted tests、产品文档同步和 `tech-done.md`。
- `robot-software-engineer`：只在 Full-stack 发现 command/status/ack API shape 退化风险时做兼容性咨询或最小围栏，不主动扩大范围。
- `product-okr-owner`：负责本轮计划、验收口径、阶段收口和 OKR 更新建议。

## 风险、阻塞和证据链缺口

- Docker/local browser proof 不等于真实手机设备验收；真实 iPhone/Android 设备仍缺。
- 本地 operator gateway 不是正式 app，不含账号、生产登录、真实 4G、真实云入口。
- ACK 仍不是送达成功；不能用 ACK proof 宣称 Nav2/fixed-route、WAVE ROVER motion、HIL 或真实垃圾送达。
- 如果当前环境缺浏览器二进制或 Playwright 依赖，Full-stack 必须记录阻塞并给出可复现安装/替代命令；不能回退成只做 handler proof 后宣称 P0 完成。

## 需要创建或更新的 sprint 文档

本阶段创建：

- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/pre_start.md`
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/prd.md`
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/tech-plan.md`

后续工程阶段必须更新：

- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/tech-done.md`

收口阶段必须更新：

- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/side2side_check.md`
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/final.md`
- `OKR.md`
