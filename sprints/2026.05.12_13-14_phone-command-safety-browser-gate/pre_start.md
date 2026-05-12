# Sprint 2026.05.12_13-14 Phone Command Safety Browser Gate - Pre Start

## 状态

- 阶段：pre_start
- 启动时间：2026-05-12 13:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 建议证据边界：`software_proof_docker_phone_command_safety_browser_gate`
- 本轮限制：只在 Docker/local/browser/API 软件围栏内推进；本机没有真实硬件，不做 O1/HIL 主线。

## 启动依据

当前 `OKR.md` 快照显示 O5 手机体验约 38%，O6 4G 云中转 + OSS/CDN 约 38%，是所有 Objective 中最低完成度；O1/O2/O3/O4 均约 74%-76% 或更高。本轮应优先推进 O5/O6 的共同低位缺口，而不是在无真实硬件主机上继续消耗 O1/HIL。

上一轮 `sprints/2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate/final.md` 已完成 phone/API manifest consumption gate，把 O6 从约 36% 推到约 38%。剩余缺口仍包括真实 OSS upload、STS、CDN origin fetch、真实云、真实 4G/SIM、HTTPS/TLS 公网、生产 DB/queue、正式手机 app/真实手机浏览器验收。

本轮不把 `software_proof` 说成真实云、真实 4G、真实手机、真实送达或 HIL。ACK 只表示 command envelope 被处理，不代表垃圾送达成功、Nav2/fixed-route 成功、WAVE ROVER 运动或真实云交付成功。

## 用户价值和产品北极星

本轮价值是让普通手机用户在首屏就知道当前是否可以安全点击 Start、Confirm dropoff、Cancel、Diagnostics，并能理解为什么按钮被禁用或为什么 ACK 之后仍要继续看送达状态。用户不需要理解 raw JSON、ROS topic、`/cmd_vel`、串口、云密钥、OSS object key 或硬件参数。

北极星仍是：手机是普通用户唯一入口，4G 场景通过云中转完成命令、状态和诊断。当前 Docker/local 只能证明手机触点的安全交互形态，不能证明真实云/4G/硬件能力。

## OKR 映射

- O5 KR1：手机端最小流程必须把 Start、Confirm dropoff、Cancel、Diagnostics 约束到明确状态，而不是只显示可点击按钮。
- O5 KR5：普通用户失败时应知道下一步；按钮禁用和 ACK 后等待状态必须有中文优先 safe copy。
- O5 KR7：首屏可操作主路径需要在手机浏览器尺寸下完成最小可用验收，仍保持本地 HTML 为 fallback 调试入口。
- O6 KR1：命令/status/ack 契约保持云中转语义，不暴露 `/cmd_vel` 或 inbound 直连小车。
- O6 KR6：4G/云中断、ACK pending、status stale、auth failed、malformed response 等降级状态必须影响手机操作权限。

## 本轮核心抓手

把 phone readiness 从“状态摘要”推进到“命令安全 gate”：手机首屏的 Start、Confirm dropoff、Cancel、Diagnostics 操作必须由 local delivery state、remote readiness、pending ACK、status freshness、auth/degradation 和 diagnostic object readiness 共同约束。

最小 browser/API 围栏只证明用户触点可用：页面能渲染，按钮状态符合 readiness，用户 copy 解释 ACK != delivery success，API 状态不泄露敏感字段。

## 需要做什么

1. Full-stack 负责实现 phone command safety/browser gate：
   - 首屏 Start/Confirm/Cancel/Diagnostics 按钮状态从 `phone_readiness` 和 action permissions 派生。
   - `command_pending`、`status_stale`、`auth_failed`、`cloud_unreachable`、`malformed_response`、manifest `missing/invalid/stale` 必须阻断或降级相应操作。
   - ACK 后页面必须显示“命令已受理/处理中，但不等于送达成功”一类用户文案，并继续依赖 delivery status。
   - browser/API 围栏只扩展现有 targeted tests 或最小浏览器 smoke，不新增大批测试。
2. Robot 负责兼容性围栏：
   - 只验证 remote bridge command/status/ack/cursor 语义未退化。
   - 不改硬件、Nav2、WAVE ROVER、串口或 HIL 相关文件。
3. Product 负责阶段验收：
   - 核对 PRD P0、证据边界、redaction、ACK 语义和 sprint 留档。
   - 本轮 planning 不更新 `OKR.md`；实现收口后再决定是否小幅上调 O5/O6。

## 优先级和验收口径

- P0：Start/Confirm/Cancel/Diagnostics 操作状态受 phone readiness 和 action permissions 约束，并有用户可读解释。
- P0：ACK 明确不等于 delivery success；delivery 成功只看任务状态到 `completed` 等终态。
- P0：`status_stale`、`command_pending`、`auth_failed`、`cloud_unreachable`、`malformed_response` 不得让主路径呈现 green ready。
- P0：敏感字段 redaction 保持，不展示 token、Authorization、AK/SK、root password、serial、baudrate、ROS topic、`/cmd_vel`、WAVE ROVER 参数。
- P1：手机浏览器/窄屏尺寸下首屏按钮和提示不重叠，最小可点击区域保持可用。
- 非目标：真实云、真实 4G/SIM、真实 OSS upload、CDN origin fetch、生产账号、生产 DB/queue、正式手机 app、真实手机设备验收、Nav2/fixed-route 送达、WAVE ROVER/HIL。

## 责任 Engineer

- `full-stack-software-engineer`：主责 phone UI/API gate、browser smoke、targeted tests、产品文档同步、`tech-done.md`。
- `robot-software-engineer`：只做 remote bridge compatibility fence，确认 command/status/ack/cursor 语义未退化。
- `product-okr-owner`：本轮规划、验收口径、证据边界、side-by-side/final 收口和后续 OKR 更新建议。

## 风险、阻塞和证据链

- 当前主机没有真实硬件；本轮不可能产生 `hil_pass`、真实串口、WAVE ROVER feedback、Nav2/fixed-route 实跑或真实送达证据。
- Docker/local browser/API 只证明软件触点和安全 gate；不能证明真实云、HTTPS/TLS、公网入口、4G/SIM、OSS/CDN 实流量或生产可靠性。
- 如果 browser smoke 需要 dev server 或 localhost 端口，必须在 `tech-done.md` 写清启动命令、访问 URL、截图或最小日志证据。
- 如果现有 API 字段不足以准确约束按钮状态，由 Full-stack 在允许范围内补字段；Robot 只核对兼容，不扩大实现。

## 本轮需要创建或更新的 sprint 文档

- 已创建/待完成：`pre_start.md`
- 已创建/待完成：`prd.md`
- 已创建/待完成：`tech-plan.md`
- 实现后必须更新：`tech-done.md`
- 验收后必须更新：`side2side_check.md`
- 收口后必须更新：`final.md`
