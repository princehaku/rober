# Sprint 2026.05.12_20-21 Phone Task Flow Readiness Gate - PRD

## 状态

- 阶段：prd
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 目标 evidence boundary：`software_proof_docker_phone_task_flow_readiness_gate`

## 用户价值和产品北极星

普通用户只应通过手机完成送垃圾任务的发起、理解和求助，不需要知道 SSH、ROS2、topic、串口、JSON、ACK envelope、底盘协议或云队列内部细节。

本轮把本地/Docker 手机入口从“PWA/installable shell”推进到“任务流程 readiness gate”。用户进入首屏后，应能按任务步骤判断自己能不能继续、下一步做什么、机器人现在处于什么状态、失败时找哪里求助。

## OKR 映射

- Objective 5：推进手机体验与量产边界，从约 46% 的 installability software proof 进入 task-flow readiness software proof。
- KR7 手机端美观可用：首屏必须围绕普通用户任务步骤，而不是工程字段。
- Objective 6：保持 command/status/ack envelope 兼容；本轮只消费或展示 phone-safe 状态，不提升 O6。
- Objective 1/2/3/4：本轮不声明硬件、真实送达、Nav2/fixed-route 或真实视觉进展。

## KR 拆解或更新

本轮不新增顶层 Objective，只细化 O5 的下一层 KR：

- KR5-A：手机首屏能显示连接/就绪、目的地、装载确认、发车、任务状态、失败/人工接管/诊断入口。
- KR5-B：每一步都有 phone-safe 文案和机器可测 metadata，不展示 raw ROS/topic/串口/JSON/token/硬件参数。
- KR5-C：Start/Confirm/Cancel 继续受 command safety gate 约束；Diagnostics 可访问但不能让主任务按钮误显为 ready。
- KR5-D：ACK 只解释为 command accepted/processed evidence，不能写成 delivery success。
- KR5-E：本轮证据边界必须写入 API、UI 或 docs 的用户可理解口径：`software_proof_docker_phone_task_flow_readiness_gate`。

## 本轮核心抓手

围绕 `operator_gateway` 本地手机页形成任务流程 readiness gate：

1. 连接/就绪：首屏显示当前能否继续、本地/远程状态是否阻塞、下一步提示。
2. 选择或确认目的地：展示用户可理解的目标/站点状态；缺目标时阻止发车并给出恢复提示。
3. 确认已放入垃圾：发车前要求用户明确装载确认，不把“自动检测已装载”作为本轮前提。
4. 一键发车：主按钮受 readiness + command safety 共同约束。
5. 状态解释：展示 delivering、arrived、returning、completed、failed、needs_human_help 等用户状态；保留 elevator assist phone-safe 文案。
6. 失败/人工接管/诊断入口：支持普通用户进入诊断或人工接管路径，但 raw diagnostics 默认不成为首屏体验。

## 需要做什么

### Task A：Phone task-flow readiness gate

Owner：`full-stack-software-engineer`

需要实现：

- 在本地 phone/operator surface 中引入 task-flow readiness gate 或等价 metadata。
- 首屏/状态/diagnostics 展示覆盖连接/就绪、目的地、装载确认、一键发车、状态解释、失败/人工接管/诊断入口。
- 所有用户可见 copy phone-safe，不出现 raw ROS topic、串口、baudrate、JSON payload、token、Authorization header、cloud secret、WAVE ROVER 参数或硬件配置。
- Start/Confirm/Cancel 仍受 command safety 和状态权限约束；Diagnostics 可访问。
- 同步更新 `docs/product/mobile_user_flow.md`，写清 evidence boundary 和未证明范围。

目标 evidence boundary：`software_proof_docker_phone_task_flow_readiness_gate`。

### Task B：Robot compatibility fence

Owner：`robot-software-engineer`

需要确认：

- 新增 phone task-flow metadata 不改变 remote command/status/ack envelope。
- ACK 仍只是 command envelope evidence，不等于 delivery success。
- 新 UI/metadata 不触发额外 robot action。
- 新 UI/metadata 不推进 remote cursor。
- remote bridge 既有 command/status/ack targeted unittest 仍通过。

## 优先级和验收口径

优先级：

- P0：phone-safe task-flow metadata 和首屏步骤正确，不暴露 raw ROS/topic/串口/JSON/secret。
- P0：Start/Confirm/Cancel 安全 gate 不回退，ACK 语义不变。
- P1：Diagnostics/人工接管入口可被普通用户找到，且 copy 解释阻塞原因。
- P1：`docs/product/mobile_user_flow.md` 同步本轮证据边界和未证明范围。

验收口径：

- Full-stack targeted unittest 覆盖 operator gateway HTTP/static/diagnostics 相关路径。
- Robot targeted unittest 覆盖 remote bridge command/status/ack compatibility。
- `py_compile` 通过相关 Python 文件。
- scoped `git diff --check` 通过。
- 不运行 broad regression，不把测试扩展成大套证明。

## 对应责任 Engineer

- `full-stack-software-engineer`：Task A，负责用户触点实现、展示、API metadata、产品文档同步和 full-stack 验证。
- `robot-software-engineer`：Task B，负责 remote bridge 兼容性围栏和 robot 验证。
- `product-okr-owner`：阶段验收、OKR 口径、sprint 留档和最终 OKR 更新。

## 风险、阻塞和证据链缺口

- 无真实手机设备：不能证明 Safari/Chrome 真实 install prompt、physical service worker runtime 或真实手势体验。
- 无真实硬件：不能证明 WAVE ROVER 运动、真实串口、Nav2/fixed-route、HIL 或垃圾送达。
- 无生产云/4G：不能证明真实 HTTPS/TLS、公网入口、SIM/4G、生产账号、生产 DB/queue 或 OSS/CDN 实流量。
- UI 只能证明 local/Docker phone task-flow readiness，不得提升为真实 production app 或真实用户验收。
- 若出现 raw engineering detail 泄露，必须由 Task A 修复后再验收。
- 若 remote envelope、ACK 语义或 cursor 行为变化，必须由 Task B 阻断并修复。

## 需要创建或更新的 sprint 文档

- 已创建或本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程完成后更新：`tech-done.md`。
- Product 验收后更新：`side2side_check.md`、`final.md`。
- 最终收口时按证据更新 `OKR.md`，不得把 local/Docker software proof 写成真实手机、真实云、真实 4G、HIL 或送达成功。
