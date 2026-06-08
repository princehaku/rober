# O6 Labeling API PRD

## 需求概述

本轮在 `remote_cloud_relay.py` 的 existing O6 local/mock 架构上，增加 `O6 archive labels` API：

- `POST /api/o6/archive/labels`：提交或更新标注结果，支持 idempotent upsert。
- `GET /api/o6/archive/labels`：返回待标注/已标注任务的安全摘要。
- `GET /api/o6/archive/labels/<task_id>`：返回单任务标注详情。

设计边界：本轮只做本地 mock 接口，不连接真实云 DB、真实 OSS、真实训练集导出、模型训练链路和机器人控制。

## 目标用户

- O7 标注开发/运营用户：要有稳定接口读取待标注清单并提交打标结果。
- PC O7 工程与 QA：要能基于固定 schema 和 fail-closed 行为写验收测试。

## 用户价值

1. 让 PC 标注队列从“页面想象数据”进入“可写入、可查询、可复现的 API 证据”。
2. 把 O6 与 O7 边界清晰化，避免把 local/mock 写成生产标注平台。
3. 形成可复用的安全摘要，让“待标注”与“已标注”分工更可观测。

## 范围内功能

### P0：标注提交（idempotent upsert）

- 接口：`POST /api/o6/archive/labels`
- 必填：
  - `task_id`
  - `robot_id`
  - `labels`（数组）
- 单条 label 必填：
  - `item_id`
  - `item_type`
  - `label_type`
  - `value`
- 单条 label 可选：
  - `confidence`
  - `annotator_id`
  - `evidence_ref`
  - `notes`
- upsert 语义：同一 `task_id + item_id + label_type` 重复提交按幂等更新返回 `write_status="updated"`。

### P0：按任务查询详情

- 接口：`GET /api/o6/archive/labels/<task_id>`
- 查询成功：返回 task 的所有 label 与 `task_status`。
- 未找到：返回明确 fail-closed，不回显敏感/未知输入。

### P0：安全摘要查询

- 接口：`GET /api/o6/archive/labels`
- 支持 query（可选）：
  - `status=pending|labeled|all`（默认 `all`）
  - `limit`（正整数，默认 50）
  - `robot_id`（可选筛选）
- 返回：`task_count`、`pending_task_count`、`labeled_task_count`、`sample`。

### P0：固定响应与边界字段

以下字段必须每个成功响应都能判断到位：

- `schema="trashbot.o6.archive_labeling.v1"`
- `schema_version=1`
- `source="local_mock_labeling"`
- `proof_status="not_proven"`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `submit_enabled=false`
- `rollback_enabled=false`
- `dataset_export_available=false`
- `real_annotation_api_connected=false`
- `real_dataset_export_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `not_proven` 必须显式包含：
  - `real_annotation_submit_success`
  - `real_annotation_review_api`
  - `real_dataset_export`
  - `real_o7_labeling_production`

### P0：fail-closed（必须 fail）

- 坏 JSON（不合法 JSON）
- 缺字段：`task_id`/`robot_id`/`labels`
- `labels` 不是数组
- 数组过大：`labels` 元素上限、`label` 注释字段长度上限、`notes` 长度上限
- unsafe 内容：`Authorization`、`Bearer`、`token`、`/cmd_vel`、串口路径、`baudrate`、`traceback`、带凭证 URL
- unknown task_id
- 越权 task_id（`robot_id` 与现有 archive task 不匹配）

## 范围外功能

- 真实云/OSS/DB/queue
- `dataset_export` 的真实产出（只返回 boundary 状态）
- 机器人控制命令下发与任何 navigation/ASR/TTS 的真实闭环
- 真实生产认证与 TLS/公网接入

## KR 拆解

- `KR4-A`：设计固定 endpoint 及 payload-schema，支持 labeling upsert。
- `KR4-B`：GET list/detail 以安全摘要与 `task_status` 形式查询。
- `KR4-C`：实现 `idempotent upsert` + `bad input fail closed` + `unknown/unauthorized task_id`。
- `KR4-D`：response fixed boundary 字段（`not_proven`/`proof_status`）在文档与实现中一致。
- `KR4-E`：`docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md` 与 `cloud-relay/README.md` 对齐本轮边界。

## 优先级与验收口径

P0 满足后才可进入实现：

- `POST /api/o6/archive/labels` 可在已存在的 `task_id` 上创建/更新标注。
- `GET /api/o6/archive/labels` 可输出 pending / labeled 的安全摘要。
- `GET /api/o6/archive/labels/<task_id>` 可读回该 task 的标注明细。
- 所有成功响应含固定 schema/source/not_proven 字段，不出现真实生产声明。
- 失败场景不回显危险字符串。

P1 完成后才可收口：

- `tech-done.md` 记录实际改动、验证、失败定位、剩余风险。
- 只提交在文档/验收通过后执行。

## 责任 Engineer

- `full-stack-software-engineer`（单线闭环）

## 风险与阻塞

- 未接真实 O6 云标注服务，所有 `real_annotation_*` 均为 fail-safe false。
- 标注 schema 与 O7 UI/路由可用性存在后续协作窗口，超出本轮范围的真实 UI 交互可能先用 local mock payload 兼容。
- 未知或越权 task 需要工程层明确 fail-closed，否则 O7 会出现跨任务污染风险。
