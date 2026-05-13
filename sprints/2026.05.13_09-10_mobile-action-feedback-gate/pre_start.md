# Sprint 2026.05.13_09-10 Mobile Action Feedback Gate - Pre Start

## Sprint Type

- `sprint_type: epic`
- 本轮是 Objective 4 手机用户体验与低成本量产边界的跨 owner Epic sprint planning。
- 当前阶段只创建 planning docs：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 本阶段不改产品代码、测试代码、`OKR.md`、`docs/process/` 或产品正文；后续实现、验证和收口必须由对应子 agent 执行。

## 启动依据

- `OKR.md` 4.1 当前快照更新时间：2026-05-13 08:19 Asia/Shanghai。
- 当前完成度：Objective 4 手机用户体验与低成本量产边界约 60%，Objective 5 云中转 + OSS/CDN 数据通路产品化约 61%。
- Objective 1/2/3 分别约 75%/77%/77%，主要缺真实 WAVE ROVER、真实串口、`T=1001` feedback、真实 Nav2/fixed-route 实跑、同一 `evidence_ref` 任务复盘、HIL 和真实送达。
- 当前主机没有真实硬件，只有 Docker；本轮不得声明真实手机设备/browser、真实云/4G、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- 最新 sprint `sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/final.md` 只提升 Objective 5，不调整 Objective 4，并继续声明没有真实手机设备/browser、真实云/4G、HIL 或真实送达。
- 最近提交 `cb29f53 Add mobile operation log gate` 已完成只读操作日志，强调 operation log 不启用 Start/Confirm/Cancel，不发送 ACK，不推进 cursor，不声明 delivery success。
- 最近提交 `aa3490f Add cloud public ingress TLS gate` 继续强调 ACK 不是 delivery success，metadata-only 响应不触发机器人动作、不 POST ACK、不推进或持久化 cursor。
- `mobile/README.md` roadmap 写明下一步是真实手机浏览器/设备验收、安装提示和弱网体验；但当前 Docker-only 无真实手机，所以本轮先推进 local/static 可验证的 `mobile action feedback gate`。
- `docs/product/mobile_user_flow.md` 当前已定义 Start 的 mobile task-start confirmation payload、operation log 只读边界、ACK 只代表 accepted/processing evidence，不代表 delivery success。

## 上轮未完成项

- Objective 4 仍缺 production app、真实手机浏览器/设备验收、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、TTS/喇叭实放、Nav2/fixed-route、WAVE ROVER、HIL、真实送达与量产实物验收。
- `mobile/web/` 已能显示 readiness、command safety、task flow、offline/resume、support handoff 和只读 operation log，但用户点击 Start/Confirm/Cancel 后还缺一块 phone-safe 的动作回执/失败提示/ACK 语义面板。
- Start 已有 `trashbot.mobile_task_start_confirmation.v1` body；Confirm Dropoff 和 Cancel 仍需要 generic mobile action confirmation payload，避免 body-less 控制请求无法被手机端解释和追溯。
- Robot 侧仍需 compatibility fence，证明 `mobile_action_confirmation`、`mobile_action_receipt`、`phone_action_feedback` 等 metadata-only 响应不会进入 backend action path。

## 本轮目标

建立 `software_proof_docker_mobile_action_feedback_gate`：

- 手机首屏在 Start/Confirm/Cancel 提交后显示 phone-safe 动作回执、失败提示、恢复建议和 ACK 语义。
- Confirm Dropoff 和 Cancel 也带 generic mobile action confirmation payload，字段只包含 phone-safe body、动作类型、用户确认、client reference、evidence boundary 和 ACK 语义。
- 手机端文案明确：提交成功或 ACK 只代表命令 accepted/processing evidence，不代表送达成功、投放完成、取消已落地、机器人运动或硬件执行。
- Robot compatibility fence 证明相关 mobile action feedback metadata-only 响应不触发 backend action、不 POST ACK、不推进或持久化 cursor。
- 只做 local/static fixture、targeted unittest、`py_compile` 和 scoped diff check；不新增大测试堆，不做真实手机或真实云验证。

## 用户价值和产品北极星

用户价值：普通手机用户点击发车、确认投放或取消后，需要立刻看到"我刚才点了什么、系统是否接收、下一步该等还是重试、失败该怎么办"。这比只显示按钮状态更接近真实可用的手机体验，同时不会把 ACK 或提交成功误写成真实送达完成。

产品北极星：rober 的手机入口必须让不会电脑和硬件的用户完成核心任务，并能理解失败与恢复路径；所有动作反馈都要 phone-safe、可解释、可审计，并严格区分用户提交、云/机器人 ACK、机器人执行、任务送达成功这几层证据。

## OKR 映射

- Objective 4 KR1：补齐手机端最小流程中的动作提交后反馈，覆盖一键发车、确认投放和取消。
- Objective 4 KR4：把动作回执、失败原因、恢复建议和 client reference 纳入远程诊断最小数据包的 phone-safe 语义。
- Objective 4 KR5：让普通用户无需命令行、ROS2 或硬件知识，也能知道动作是否被接收、是否仍在处理、何时需要重试或人工接管。
- Objective 4 KR7：提升手机首屏主路径可用性；本轮仍是 local/static software proof，不是 production app 或真实手机验收。
- Objective 5 KR1/KR6：通过 robot-side compatibility fence 保护云中转 command/status/ack 语义，确保 metadata-only feedback 不变成真实机器人动作或 delivery success。

## 范围边界

后续工程允许范围建议：

- Task A full-stack-software-engineer：
  - `mobile/web/index.html`
  - `mobile/web/app.js`
  - `mobile/web/styles.css`（如需要）
  - `mobile/test_mobile_web_entrypoint.py`
  - `mobile/fixtures/mobile_web_status.fixture.json`
  - `mobile/README.md`
  - `docs/product/mobile_user_flow.md`
- Task B robot-software-engineer：
  - `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - `docs/interfaces/ros_contracts.md`
- Task C product-okr-owner：
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
  - `sprints/2026.05.13_09-10_mobile-action-feedback-gate/tech-done.md`
  - `sprints/2026.05.13_09-10_mobile-action-feedback-gate/side2side_check.md`
  - `sprints/2026.05.13_09-10_mobile-action-feedback-gate/final.md`

本 planning 阶段只允许创建：

- `sprints/2026.05.13_09-10_mobile-action-feedback-gate/pre_start.md`
- `sprints/2026.05.13_09-10_mobile-action-feedback-gate/prd.md`
- `sprints/2026.05.13_09-10_mobile-action-feedback-gate/tech-plan.md`

## 阻塞与风险

- 无真实手机设备/browser：本轮不能证明 iPhone/Android 真实点击、安装提示、弱网行为或移动浏览器兼容性。
- 无真实云/4G：本轮不能证明 cloud-to-robot 真实链路，只能做 local/static 和 robot protocol compatibility proof。
- 无真实硬件、Nav2/fixed-route 或 HIL：任何 ACK、receipt 或 feedback 都不能写成机器人已运动、已到站、已投放或已取消成功。
- 如果动作回执文案过绿，用户会把 accepted/processing 误解为 delivery success；本轮必须 fail closed。
- 如果 generic confirmation payload 暴露 raw JSON、ROS topic、`/cmd_vel`、串口、WAVE ROVER 参数、token、路径或完整 artifact，必须视为验收失败。

## 需要创建或更新的 sprint 文档

- 已创建/待填写：`pre_start.md`
- 已创建/待填写：`prd.md`
- 已创建/待填写：`tech-plan.md`
- 后续执行后必须补齐：`tech-done.md`
- 后续验收后必须补齐：`side2side_check.md`
- 后续收口后必须补齐：`final.md`
