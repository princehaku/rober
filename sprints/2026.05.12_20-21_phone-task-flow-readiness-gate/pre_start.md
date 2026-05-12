# Sprint 2026.05.12_20-21 Phone Task Flow Readiness Gate - Pre Start

## 状态

- 阶段：pre_start
- 启动时间：2026-05-12 20:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 目标 Objective：Objective 5 手机体验与量产边界
- 目标 evidence boundary：`software_proof_docker_phone_task_flow_readiness_gate`

## 为什么选择 O5

本轮按 live `OKR.md` 重新排序。2026-05-12 晚间快照显示：

- O5 手机体验与量产边界约 46%，当前证据边界为 `software_proof_docker_phone_pwa_installability_gate`。
- O6 4G 云中转 + OSS/CDN 约 47%，当前证据边界为 `software_proof_docker_production_store_queue_gate`。
- O1/O2/O3/O4 约 75% 左右，下一步主要依赖真实硬件、Nav2/fixed-route、真实相机或 HIL。

因此 O5 是当前最低且 Docker/local 可继续推进的目标。本机没有真实硬件，只有 Docker；继续 O5 能把普通手机入口从“可安装壳层”推进到“普通用户任务流程 readiness gate”，不会伪造真实手机、真实云、真实 4G 或实机送达。

## 证据来源

- `OKR.md`：O5 约 46%，O6 约 47%，O1/O2/O3/O4 约 75% 左右；O5 剩余缺口包括正式手机 app、真实手机设备 Safari/Chrome install prompt、physical phone service worker runtime、普通用户实机验收。
- `sprints/2026.05.12_18-19_phone-pwa-installability-gate/final.md`：O5 已完成 manifest、service worker、offline shell、API bypass 等 local/Docker PWA installability software proof，但明确不是 production app、真实手机安装、真实云/4G 或真实送达。
- `sprints/2026.05.12_19-20_remote-production-store-queue-gate/final.md`：O6 已到约 47%，且下一步若继续 O6 需要真实生产 DB/queue 或真实云/公网/4G 证据，不适合当前 Docker-only 主机。
- `docs/product/mobile_user_flow.md`：手机端最小流程已经定义为连接入口、选择或确认垃圾站、放入垃圾、启动、查看状态、确认投放、异常人工接管；已有 phone_readiness、command_safety、PWA/installability 证据边界。

## 用户价值和产品北极星

北极星仍是：普通用户只用手机，把垃圾交给小车，小车完成送达或给出可理解的人工接管路径。

本轮用户价值不是继续增加工程诊断字段，而是把手机入口组织成普通用户能理解的任务步骤：

- 连接/就绪：用户知道当前是否可以继续。
- 选择或确认目的地：用户不用理解 route file、ROS topic 或 waypoint 内部字段。
- 确认已放入垃圾：用户清楚发车前需要完成的动作。
- 一键发车：Start 行为受 command safety gate 控制。
- 状态解释：用户看到任务进度、ACK 语义、等待、失败或人工接管原因。
- 失败/人工接管/诊断入口：Diagnostics 可用，但不把 raw ROS、topic、串口、JSON、token 或硬件参数暴露给普通用户。

## OKR 映射

- Objective 5 / KR7：手机端必须美观、可直接使用、不依赖命令行/SSH/ROS2 知识。本轮把首屏流程从 installable shell 推进到任务流程 readiness gate。
- Objective 5 / 普通用户入口：本轮要求所有步骤 phone-safe，展示用户语言和下一步动作，而不是工程内部对象。
- Objective 6：只作为远程 command/status/ack envelope 兼容性围栏；本轮不提升 O6，不声明真实云、4G、生产队列或公网入口。
- Objective 1/2/3：不提升，不声明 WAVE ROVER、Nav2/fixed-route、真实底盘或送达闭环。

## 本轮核心抓手

以 `operator_gateway` 本地手机页和 API 为中心，新增或整理 `trashbot.phone_task_flow_readiness.v1` 的展示/metadata 边界，使普通用户看到的是任务步骤和安全下一步，而不是 installability 壳层或 raw diagnostics。

## Owner 和边界

- Task A `full-stack-software-engineer`：实现 phone task-flow readiness gate、首屏/状态/diagnostics 展示和 `docs/product/mobile_user_flow.md` 同步。
- Task B `robot-software-engineer`：只做兼容性围栏，确认新增 task-flow metadata 不改变 remote command/status/ack envelope，不把 ACK 写成 delivery success，不触发额外 robot action，不推进 cursor。

## 阻塞和边界

- 当前环境没有真实硬件、真实手机设备、真实生产云、真实 4G/SIM、HTTPS/TLS 公网入口或生产账号。
- 本轮不证明 production app、真实 iPhone/Android install prompt、physical phone service worker runtime、Nav2/fixed-route、WAVE ROVER、HIL 或真实垃圾送达。
- 本轮不引入新的生产 DB/queue、OSS/CDN、云鉴权或远程部署能力。
- 本轮验证只做围栏：targeted unittest、`py_compile`、scoped `git diff --check`。

## 需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程完成后必须更新：`tech-done.md`。
- 验收或风险状态变化后必须更新：`side2side_check.md`、`final.md`。
- 若 Task A 改动手机流程或 UI 口径，必须同步更新 `docs/product/mobile_user_flow.md`。
