# O6 Event Evidence Archive Epic Pre-Start

## sprint_type

sprint_type: epic

## 背景

本轮开始时间：2026-06-09 05-06。

CEO 明确要求：“设计好才能开始写功能点，功能点不完善不允许开始写代码，代码不完美不允许提交”。因此本 sprint 当前只做 Epic 设计文档，不写功能代码，不改测试代码，不触碰硬件、ROS launch 或真实 SSH 上车配置。

O6 最近几轮已经形成 local/mock 软件证据：

- `sprints/2026.06.09_01-02_o6-cloud-archive-api/final.md`：`POST/GET /api/o6/archive/tasks`，证明最小 task archive local/mock contract。
- `sprints/2026.06.09_02-03_o6-labeling-api/final.md`：`POST/GET /api/o6/archive/labels`，证明标注 local/mock contract。
- `sprints/2026.06.09_03-04_o6-model-inference-api/final.md`：`POST /api/o6/archive/inference`，证明推理结果可写入 task `events[]` 的 local/mock contract。
- `sprints/2026.06.09_04-05_o6-tunnel-online-status/final.md`：`POST/GET /api/o6/tunnel/*`，证明隧道在线态 local/mock contract。

现有缺口是：任务创建之后，还缺通用的“增量事件写入/查询”和“证据引用写入/查询”能力。后续 Orange Pi、O7 PC 回放/标注、失败复盘和电梯链路都需要在 task 生命周期内追加感知事件、路线帧事件、电梯事件、失败事件和 OSS `evidence_ref` 引用，而不是每次覆盖整份 task archive。

## 用户价值和产品北极星

产品北极星：让 rober 的每次送垃圾任务都可追溯、可回放、可复盘。

本轮价值是补齐 O6 的“任务内时间线”：机器人或后续 O7 在任务开始后，可以持续追加事件与证据引用；运营端能按 `robot_id / task_id / event_type` 查询，不再只能看一次性 task 摘要。这样失败复盘、路线回放、电梯证据和模型/标注闭环可以共享同一数据底座。

## OKR 映射和方向判断

- 当前最低 Objective：`O6：云端核心后端——数据存档、模型推理与打标平台`（`OKR.md` 4.1 当前仍为 0%）。
- 本轮方向判断：**继续 O6**。
- 直接映射：
  - `O6-KR2`：任务记录和感知事件持久化存档，支持按 `robot_id / task_id / date` 查询。本轮聚焦 task 内事件增量写入与查询。
  - `O6-KR3`：摄像头帧/快照等大对象通过 OSS 存档，云端数据库只保留 `evidence_ref`。本轮只存 local/mock evidence reference，不上传真实 OSS。
- 继续 O6 的原因：O6 是 O7 的数据前提；前几轮已经有 task、labeling、inference、tunnel 的 local/mock 形状，本轮补事件和 evidence 引用后，PC 回放/标注/失败复盘才有统一 timeline。

## KR 拆解、更新或历史归档

### 本轮推进 KR

- `O6-KR2-A`：定义并冻结 `POST /api/o6/archive/events`，支持对已有 task 增量追加事件。
- `O6-KR2-B`：定义并冻结 `GET /api/o6/archive/events`，支持按 `robot_id / task_id / event_type / time window` 查询。
- `O6-KR3-A`：定义并冻结 `POST /api/o6/archive/evidence`，支持写入 OSS-shaped `evidence_ref` 引用。
- `O6-KR3-B`：定义并冻结 `GET /api/o6/archive/evidence`，支持按 `robot_id / task_id / evidence_type` 查询。

### 已完成 KR 的历史记录位置

- O6 archive task local/mock 证据：
  - `sprints/2026.06.09_01-02_o6-cloud-archive-api/tech-done.md`
  - `sprints/2026.06.09_01-02_o6-cloud-archive-api/final.md`
  - 剩余风险：真实 cloud DB、真实 OSS、production cloud、4G/公网均未证明。
- O6 labeling local/mock 证据：
  - `sprints/2026.06.09_02-03_o6-labeling-api/tech-done.md`
  - `sprints/2026.06.09_02-03_o6-labeling-api/final.md`
  - 剩余风险：真实 annotation API、review API、dataset export 未证明。
- O6 model inference local/mock 证据：
  - `sprints/2026.06.09_03-04_o6-model-inference-api/tech-done.md`
  - `sprints/2026.06.09_03-04_o6-model-inference-api/final.md`
  - 剩余风险：真实 GPU/外部模型、真实楼层识别、真实电梯门状态未证明。
- O6 tunnel online status local/mock 证据：
  - `sprints/2026.06.09_04-05_o6-tunnel-online-status/tech-done.md`
  - `sprints/2026.06.09_04-05_o6-tunnel-online-status/final.md`
  - 剩余风险：真实隧道、真实 4G、真实生产云未证明。

## 本轮核心抓手

P0 功能点必须完整覆盖：

1. `POST /api/o6/archive/events`
   - 只允许对已有 archive task 追加事件。
   - 支持事件类型白名单：`perception.detected_object`、`route.frame`、`route.pose`、`elevator.door_state`、`elevator.floor_evidence`、`task.failure`、`task.recovery`、`operator.note`。
   - 支持幂等键：`task_id + event_id`。
2. `GET /api/o6/archive/events`
   - 支持 `robot_id`、`task_id`、`event_type`、`from_ms`、`to_ms`、`limit` 查询。
   - 默认按 `occurred_at_ms` 升序返回，便于回放；如实现选择倒序，必须在 `tech-done.md` 说明理由。
3. `POST /api/o6/archive/evidence`
   - 只保存 `evidence_ref` 引用，不保存图片/视频/音频原始内容。
   - 支持 evidence 类型白名单：`camera_frame`、`snapshot`、`route_frame`、`elevator_frame`、`failure_snapshot`、`audio_clip`、`log_excerpt`。
   - 支持幂等键：`task_id + evidence_id`。
4. `GET /api/o6/archive/evidence`
   - 支持 `robot_id`、`task_id`、`evidence_type`、`event_id`、`limit` 查询。
   - 返回白名单摘要，不能回显凭据 URL 或大对象原始内容。

## 优先级和验收口径

P0 设计验收：

- 三份 Epic 文档存在：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 文档明确 `O6-KR2`、`O6-KR3`、四个 endpoint、owner、字段、fail-closed、幂等、白名单、上限、真实能力 false 边界。
- 文档明确实现阶段主责为 `full-stack-software-engineer`，且禁止触碰硬件、ROS launch 或真实 SSH 上车配置。

P1 实现验收（后续工程 sprint）：

- py_compile、unittest、rg 关键字、git diff --check 全部通过。
- 单测覆盖成功写入/查询、重复写入、未知 task、越权 task、非法 payload、unsafe content、限制上限。
- 文档同步更新到 `docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md`、`cloud-relay/README.md`。

## 对应责任 Engineer

- 产品设计与验收口径：`product-okr-owner`。
- 后续实现主责：`full-stack-software-engineer` 单线闭环。
- 不并行启动硬件、算法或 ROS owner：本轮是 cloud archive local/mock API，不涉及 WAVE ROVER、串口、Orange Pi 硬件配置、Nav2 或 ROS launch。

## 风险、阻塞和需要补齐的证据链

- 本轮只做设计，不证明代码实现完成。
- 后续实现仍是 local/mock file-backed proof，不证明真实 cloud DB、真实 OSS 上传、真实 CDN 可读、真实公网、真实 4G、真实机器人控制。
- 需要补齐的证据链：实现阶段 `tech-done.md`、`side2side_check.md`、`final.md`；接口文档同步；测试日志；真实能力 false 字段回归证据。

## 需要创建或更新的 sprint 文档

本轮创建：

- `sprints/2026.06.09_05-06_o6-event-evidence-archive/pre_start.md`
- `sprints/2026.06.09_05-06_o6-event-evidence-archive/prd.md`
- `sprints/2026.06.09_05-06_o6-event-evidence-archive/tech-plan.md`

后续实现完成后必须补齐：

- `sprints/2026.06.09_05-06_o6-event-evidence-archive/tech-done.md`
- `sprints/2026.06.09_05-06_o6-event-evidence-archive/side2side_check.md`
- `sprints/2026.06.09_05-06_o6-event-evidence-archive/final.md`
