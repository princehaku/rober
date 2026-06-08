# O6 Model Inference API PRD

## 需求概述

本轮设计 O6 local/mock 模型推理接口，让电梯门开/关、楼层识别等推理结果能写入 O6 archive task 的事件存档，并被 PC/手机后续消费。

目标接口：

- `POST /api/o6/archive/inference`：提交一组 local/mock 推理请求，返回推理结果摘要，并把结果写入已有 archive task 的事件存档。
- `GET /api/o6/archive/tasks/<task_id>`：通过既有 task detail 查询到推理事件，不新增独立只读孤岛。

本轮只完成设计，不写产品代码。本轮只证明 `local/mock` inference contract，不证明真实 GPU、外部模型、生产云、真实 OSS、真实电梯识别、机器人控制或真实送达。

## 目标用户

- PC 运营/调试用户：在历史任务、路线回放、电梯状态和标注界面中看到可追溯的推理事件。
- 手机用户体验链路：后续可以通过 O6/O7 数据源看到“电梯门状态/楼层证据”的安全摘要，但不能误读为真实自动驾驶完成。
- 工程与 QA：基于固定 schema、固定 boundary 字段和 fail-closed 行为编写本地测试与消费端契约。

## 用户价值

1. 把“模型推理”从临时日志或 UI 假数据变成可复盘的任务事件。
2. 让 PC/手机消费同一份 O6 archive task 数据，降低字段漂移和重复实现。
3. 在真实模型和生产云未就绪前，先建立可测试的 API 合同与安全边界。

## 范围内功能

### P0：local/mock 推理提交

接口：`POST /api/o6/archive/inference`

必填字段：

- `robot_id`
- `task_id`
- `inference_id`
- `model_family`
- `requested_outputs[]`
- `inputs[]`

`requested_outputs[]` 首批只允许：

- `elevator_door_state`
- `floor_recognition`

`inputs[]` 单项建议字段：

- `input_id`
- `input_type`：`image_ref | frame_ref | snapshot_ref | metadata_only`
- `evidence_ref`
- `captured_at_ms`
- `metadata`

约束：

- `task_id` 必须已存在于 O6 archive store。
- `robot_id` 必须与目标 archive task 一致。
- `inputs[]` 与 `requested_outputs[]` 必须是小数组。
- local/mock 模式可以按 deterministic stub 生成结果，禁止声明真实模型成功。

### P0：推理结果写入事件存档

成功提交后必须把推理结果作为 archive task 事件追加或幂等更新。

建议事件字段：

- `event_id`
- `event_type`
- `occurred_at_ms`
- `source=local_mock_inference`
- `inference_id`
- `model_family`
- `result_type`
- `result_value`
- `confidence`
- `evidence_ref`
- `not_proven[]`

首批事件类型：

- `model_inference.elevator_door_state`
- `model_inference.floor_recognition`

幂等语义：

- `task_id + inference_id + input_id + result_type` 作为结果幂等键。
- 重复提交同一键更新既有推理事件，返回 `write_status=updated` 与 `duplicate=true`。
- 全新键返回 `write_status=created` 与 `duplicate=false`。

### P0：固定响应与边界字段

所有成功响应必须包含：

- `schema=trashbot.o6.model_inference.v1`
- `schema_version=1`
- `source=local_mock_inference`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `real_gpu_model_connected=false`
- `real_external_model_api_connected=false`
- `real_model_inference_success=false`
- `real_floor_recognition_proven=false`
- `real_elevator_door_state_proven=false`
- `archive_event_written=true`（仅表示 local/mock store 写入成功）
- `not_proven` 至少包含：
  - `real_gpu_model`
  - `real_external_model_api`
  - `real_cloud_production`
  - `real_oss_evidence_object`
  - `real_elevator_door_state`
  - `real_floor_recognition`
  - `robot_control`

### P0：fail-closed

必须 fail closed 的输入：

- 坏 JSON / 非对象 JSON / 空 body。
- 缺少 `robot_id`、`task_id`、`inference_id`、`model_family`、`requested_outputs[]`、`inputs[]`。
- `task_id` 不存在：`unknown_task`。
- `robot_id` 与 archive task 不一致：`unauthorized_task`。
- `requested_outputs[]` 含未知输出类型。
- `inputs[]` 或 `requested_outputs[]` 过大。
- `captured_at_ms` 不在 task 起止时间窗口内，或时间字段倒序。
- unsafe 内容：`Authorization`、`Bearer`、`token`、`/cmd_vel`、串口路径、`baudrate`、`traceback`、带凭证 URL。
- 任何请求中出现 `success=true`、`production_ready=true`、`gpu_connected=true`、`floor_recognition_proven=true`、`robot_control_executed=true` 等真实能力声明。

失败响应不得回显危险字符串，不得创建 archive task，不得写孤儿 inference record。

## 范围外功能

- 真实 GPU、真实 CPU 模型、真实外部模型 API 或真实模型服务。
- 真实生产云 DB/queue、真实 OSS/CDN、TLS/公网/4G/SIM。
- 真实 PC/手机 UI 改造。
- 真实机器人控制、Nav2、WAVE ROVER、串口、HIL 或真实电梯现场识别。
- 模型训练、标注审核、数据集导出、模型版本管理。

## OKR 映射和方向判断

- 对应 Objective：`O6：云端核心后端——数据存档、模型推理与打标平台`。
- 对应 KR：`O6-KR5`。
- 方向判断：继续推进 O6。O6 仍是当前最低 Objective，本轮补齐 archive 与 labeling 之后的模型推理 contract。

## KR 拆解

- `KR5-A`：定义推理请求与 response schema。
- `KR5-B`：定义电梯门状态与楼层识别两类结果。
- `KR5-C`：推理结果写入既有 archive task events。
- `KR5-D`：实现 unknown/unauthorized/unsafe/oversized/unsupported output fail-closed。
- `KR5-E`：文档同步到接口文档、PC 触点边界和 cloud-relay README。

## 优先级和验收口径

进入实现前必须满足：

- `pre_start.md`、`prd.md`、`tech-plan.md` 已明确 `sprint_type: epic`、O6-KR5、local/mock、not_proven、fail-closed 与 owner。
- `tech-plan.md` 已明确任务分工、允许改动文件范围、接口影响、验收命令、风险边界、OKR 最低优先级核对。

实现收口时必须满足：

- `POST /api/o6/archive/inference` 能在已有 archive task 上写入推理事件。
- 通过 `GET /api/o6/archive/tasks/<task_id>` 能读回推理事件。
- unknown task、unauthorized task、unsupported output、unsafe content 和过大数组均 fail-closed。
- 所有成功响应固定 `local_mock_inference`、`not_proven` 和真实能力 false 字段。
- 更新 `docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md`、`cloud-relay/README.md`。
- 验证输出写入本 sprint `tech-done.md`，验收对照写入 `side2side_check.md`，收口写入 `final.md`。

## 对应责任 Engineer

- 实现 owner：`full-stack-software-engineer` 单线闭环。
- Product owner 只负责本轮设计、验收口径和 sprint 留档，不写产品代码。

## 风险、阻塞和证据链

- 本轮没有真实模型或真实电梯数据，所有推理结果只能是 deterministic local/mock。
- `archive_event_written=true` 只能表示本地 mock store 写入成功，不能解释为生产云持久化或真实识别成功。
- PC/手机后续消费必须显示 `not_proven` 边界，不能把楼层识别当成真实到站依据。
- 真实 GPU、外部模型 API、生产云和机器人控制需要后续 sprint 独立验收。

## 已完成 KR 历史记录位置

- O6 archive task API 软件证据：`sprints/2026.06.09_01-02_o6-cloud-archive-api/final.md`。
- O6 labeling API 软件证据：`sprints/2026.06.09_02-03_o6-labeling-api/final.md`。
- 本轮完成后只应记录为 O6-KR5 local/mock software proof，不应移动到真实生产完成历史区。

## 需要创建或更新的 sprint 文档

- 设计阶段：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现阶段：`tech-done.md`、`side2side_check.md`、`final.md`。
