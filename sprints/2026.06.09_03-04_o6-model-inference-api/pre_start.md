# O6 Model Inference API Epic Pre-Start

## sprint_type

sprint_type: epic

## 用户价值与产品北极星

产品北极星是让普通用户把垃圾交给小车后，机器人任务全程可观测、可复盘、可被 PC/手机继续消费。O6 是这个北极星的数据底座：不是只把状态显示出来，而是把任务、轨迹、感知事件、标注结果和推理结果沉淀成统一的云端核心后端契约。

最近两轮已经完成 O6 local/mock archive task API 与 local/mock labeling API 的软件证据。本轮继续补 O6-KR5：把电梯门开/关、楼层识别等模型推理结果定义成可写入 archive task 事件存档的 local/mock contract，让后续 PC 端电梯状态、历史回放、标注队列和手机状态页能消费同一份 O6-shaped 数据。

本轮价值不在于证明真实模型已经可用，而在于先冻结推理请求、推理结果、事件落库和 fail-closed 边界，避免后续 UI、云端和算法各自发明不兼容字段。

## OKR 映射与方向判断

- 当前最低 Objective：`O6：云端核心后端——数据存档、模型推理与打标平台`。
- `OKR.md` 4.1 快照中 O6 当前仍为 `0%`，是当前最低完成度 Objective。
- 本轮方向判断：**继续（continue）O6**。
- 本轮目标 KR：`O6-KR5：模型推理接口（电梯门开/关、楼层识别）可在云端调用，推理结果写入事件存档，不要求 GPU 上线即可用`。
- 方向依据：
  - `sprints/2026.06.09_01-02_o6-cloud-archive-api/final.md` 已完成 local/mock archive task API，但明确未覆盖模型推理。
  - `sprints/2026.06.09_02-03_o6-labeling-api/final.md` 已完成 local/mock labeling API，但仍未接真实标注平台、训练导出或模型反馈闭环。
  - `docs/interfaces/o6_cloud_archive_api.md` 已有 `tasks` 与 `labels` 契约，本轮应把 inference 作为 archive task 的事件来源扩展，而不是另建孤立数据岛。

## KR 拆解、更新与历史归档

### 本轮推进 KR

- `O6-KR5-A`：定义 `POST /api/o6/archive/inference` local/mock 请求契约，支持以 `robot_id + task_id + frame_id/evidence_ref` 提交推理输入摘要。
- `O6-KR5-B`：定义推理输出结构，至少覆盖 `elevator_door_state` 与 `floor_recognition` 两类结果。
- `O6-KR5-C`：推理结果必须写入既有 O6 archive task 的 `events[]` 或等价事件存档，不允许创建孤儿推理记录。
- `O6-KR5-D`：固定 `local/mock`、`not_proven`、`fail-closed` 边界，不证明真实 GPU、外部模型、生产云、真实 OSS、机器人控制或真实电梯识别成功。
- `O6-KR5-E`：同步更新接口文档、PC 触点文档与 cloud-relay README，使 PC/手机后续消费方能明确只读边界。

### 已有 KR 证据

- `O6-KR2 / O6-KR3 / O6-KR6` 的 local/mock archive task 软件证据：
  - `sprints/2026.06.09_01-02_o6-cloud-archive-api/tech-done.md`
  - `sprints/2026.06.09_01-02_o6-cloud-archive-api/side2side_check.md`
  - `sprints/2026.06.09_01-02_o6-cloud-archive-api/final.md`
- `O6-KR4` 的 local/mock labeling 软件证据：
  - `sprints/2026.06.09_02-03_o6-labeling-api/tech-done.md`
  - `sprints/2026.06.09_02-03_o6-labeling-api/side2side_check.md`
  - `sprints/2026.06.09_02-03_o6-labeling-api/final.md`

这些 KR 目前只进入软件证据区，不移动到“真实生产完成”历史区；因为它们仍未证明真实 DB、OSS、生产云、4G/SIM、真实 PC/手机消费或现场机器人数据。

### 本轮不覆盖 KR

- `O6-KR1`：Orange Pi 隧道接入、公网在线/离线感知与自动重连。
- 真实 GPU、真实外部模型 API、真实生产云 DB/queue、真实 OSS、真实 CDN。
- 真实机器人控制、真实电梯现场识别、真实楼层到达判定、HIL 或送达成功。

## 本轮核心抓手

本轮先完成设计文档，不写产品代码。设计必须让下一步 `full-stack-software-engineer` 能单线闭环实现：

- `POST /api/o6/archive/inference`：提交 local/mock 推理请求并写入事件存档。
- `GET /api/o6/archive/tasks/<task_id>`：通过既有 task detail 读到推理事件。
- 固定事件类型：
  - `model_inference.elevator_door_state`
  - `model_inference.floor_recognition`
- 固定边界字段：
  - `schema=trashbot.o6.model_inference.v1`
  - `source=local_mock_inference`
  - `proof_status=not_proven`
  - `safe_to_control=false`
  - `connects_cloud_production=false`
  - `robot_control_executed=false`
  - `real_gpu_model_connected=false`
  - `real_external_model_api_connected=false`

## 优先级和验收口径

P0：先冻结请求/响应、事件存档、fail-closed 和 `not_proven` 字段，满足后才允许进入代码实现。

P1：工程实现必须复用已有 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` local/mock store，并只附着到已存在 task。

P2：文档同步必须覆盖 `docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md`、`cloud-relay/README.md`，但本设计阶段不修改这些文件。

## 责任 Engineer

- Product / OKR Owner：本轮只负责设计文档、范围边界和验收口径。
- 实现 owner：`full-stack-software-engineer` 单线闭环。
- 咨询角色：默认不需要硬件、ROS2 或算法并行；真实模型或真实电梯数据进入后再由 `robot-algorithm-engineer` 补事实。

## 风险、阻塞和证据链缺口

- 当前只证明 local/mock inference contract，不证明真实 GPU/外部模型/生产云/机器人控制。
- 推理结果必须附着在已有 archive task，否则 PC/手机会出现无法追溯的孤儿感知事件。
- `floor_recognition` 不能被 UI 解释成真实楼层到达；必须保留 `not_proven` 和 confidence/evidence_ref。
- 本轮不涉及硬件真实集成，不读取 vendor 引脚、电压、UART 或 WAVE ROVER 资料。

## 需要创建或更新的 sprint 文档

- `sprints/2026.06.09_03-04_o6-model-inference-api/pre_start.md`
- `sprints/2026.06.09_03-04_o6-model-inference-api/prd.md`
- `sprints/2026.06.09_03-04_o6-model-inference-api/tech-plan.md`
