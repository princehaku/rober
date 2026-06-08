# O6 Event Evidence Archive Tech Plan

## 计划状态

本文件完成后，设计阶段可转交 `full-stack-software-engineer` 做实现。当前只做文档化和验收口径，不写产品代码。

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前完成度最低的是 `O6：云端核心后端——数据存档、模型推理与打标平台`，进度为 0%。
2. 本 sprint 直接针对最低 Objective，推进 `O6-KR2` 与 `O6-KR3`。
3. 继续 O6 的理由：已有 `archive tasks / labeling / inference / tunnel status` 的 local/mock 软件证据，但缺少任务内增量事件和 evidence 引用查询。这个缺口会阻塞 O7 的路线回放、标注 seed、失败复盘和电梯 evidence timeline。

## 技术目标

在既有 O6 file-backed local/mock store 之上新增任务内增量写入与查询 API：

- `POST /api/o6/archive/events`
- `GET /api/o6/archive/events`
- `POST /api/o6/archive/evidence`
- `GET /api/o6/archive/evidence`

端点名称保持 `/api/o6/archive/*`，原因：

- 现有 O6 task、labeling、inference 都在 archive namespace 下；
- 本轮数据仍是 task archive 的子资源，不是独立控制面；
- 统一 namespace 便于 O7 后续只接一个 O6 archive contract。

## 执行 owner

- 主责实现：`full-stack-software-engineer`，单 owner 单线闭环。
- Product 验收：`product-okr-owner`。
- 不并行硬件/算法/ROS owner：本轮只改 cloud archive local/mock API 和相关文档，不涉及硬件、WAVE ROVER、Orange Pi 串口、Nav2、ROS launch 或真实 SSH 上车配置。

## 文件范围（后续实现建议）

后续工程实现允许建议改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/pc_tools_workstation.md`
- `cloud-relay/README.md`
- `sprints/2026.06.09_05-06_o6-event-evidence-archive/tech-done.md`
- `sprints/2026.06.09_05-06_o6-event-evidence-archive/side2side_check.md`
- `sprints/2026.06.09_05-06_o6-event-evidence-archive/final.md`

本设计阶段实际允许改动仅限：

- `sprints/2026.06.09_05-06_o6-event-evidence-archive/pre_start.md`
- `sprints/2026.06.09_05-06_o6-event-evidence-archive/prd.md`
- `sprints/2026.06.09_05-06_o6-event-evidence-archive/tech-plan.md`

明确禁止：

- 硬件配置、ROS launch、WAVE ROVER、UART、串口设备、真实 SSH 上车配置。
- 手机/PC UI 功能代码。
- `OKR.md` 和非本轮授权 sprint 文档。

## 数据存储与兼容策略

- 复用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 与既有 `FileBackedO6CloudArchiveStore` 风格。
- 建议在同一 store 中为每个 task 保留 `events[]` 与 `evidence_refs[]`，或新增 `event_archive` / `evidence_archive` section，但必须保持 `GET /api/o6/archive/tasks/<task_id>` 可继续读到兼容 task 详情。
- 写入只允许附着到已有 task；禁止 `POST events/evidence` 隐式创建 task。
- 重复写入采用幂等 upsert，不创建重复实体。
- 本地文件写入仍是 local/mock proof，不等于生产 DB 事务、跨实例并发或审计签名。

## API Contract

### A. `POST /api/o6/archive/events`

请求示例：

```json
{
  "robot_id": "trashbot-001",
  "task_id": "task-20260609-001",
  "events": [
    {
      "event_id": "evt-route-0001",
      "event_type": "route.pose",
      "occurred_at_ms": 1750000123000,
      "pose": {"x_m": 1.2, "y_m": 0.4, "yaw_rad": 0.1, "floor_id": "F1"},
      "summary": "route pose frame",
      "severity": "info",
      "evidence_refs": ["oss://mock/rober/trashbot-001/task-20260609-001/frame-0001.jpg"],
      "metadata": {"frame_index": 1}
    }
  ]
}
```

输入限制：

- `events[]` 上限 64。
- `event_id` 长度建议 1 到 128。
- `summary` 长度建议不超过 512。
- `metadata` 只允许小 object，深度不超过 3，序列化后建议不超过 8 KiB。
- `evidence_refs[]` 每条 event 最多 8 个引用。

事件白名单：

- `perception.detected_object`
- `route.frame`
- `route.pose`
- `elevator.door_state`
- `elevator.floor_evidence`
- `task.failure`
- `task.recovery`
- `operator.note`

成功响应固定字段：

- `schema=trashbot.o6.archive_events.v1`
- `schema_version=1`
- `source=local_mock_event_archive`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `real_cloud_db_connected=false`
- `real_oss_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `archive_event_written=true`

幂等键：`task_id + event_id`。

### B. `GET /api/o6/archive/events`

查询参数：

- `robot_id`
- `task_id`
- `event_type`
- `from_ms`
- `to_ms`
- `limit`，默认 50，上限 200

返回要求：

- 固定 `schema=trashbot.o6.archive_events.v1`、`source=local_mock_event_archive`、`proof_status=not_proven`。
- 返回 `query`、`events[]`、`event_summary`。
- `events[]` 只暴露白名单字段：`event_id/event_type/occurred_at_ms/source/pose/summary/severity/evidence_refs/metadata/created_at_ms/updated_at_ms`。
- 默认按 `occurred_at_ms` 升序，支持 route replay。

### C. `POST /api/o6/archive/evidence`

请求示例：

```json
{
  "robot_id": "trashbot-001",
  "task_id": "task-20260609-001",
  "evidence_refs": [
    {
      "evidence_id": "evd-frame-0001",
      "evidence_type": "camera_frame",
      "evidence_ref": "oss://mock/rober/trashbot-001/task-20260609-001/frame-0001.jpg",
      "captured_at_ms": 1750000123000,
      "event_id": "evt-route-0001",
      "content_type": "image/jpeg",
      "size_bytes": 123456,
      "checksum": "sha256:mock",
      "metadata": {"camera": "front"}
    }
  ]
}
```

输入限制：

- `evidence_refs[]` 上限 64。
- `evidence_id` 长度建议 1 到 128。
- `evidence_ref` 只允许对象引用或 mock ref，不允许带 credential 的 URL。
- `metadata` 只允许小 object，深度不超过 3，序列化后建议不超过 8 KiB。
- 不接受 base64 图片、视频、音频、完整日志或原始模型响应。

evidence 类型白名单：

- `camera_frame`
- `snapshot`
- `route_frame`
- `elevator_frame`
- `failure_snapshot`
- `audio_clip`
- `log_excerpt`

成功响应固定字段：

- `schema=trashbot.o6.archive_evidence.v1`
- `schema_version=1`
- `source=local_mock_evidence_archive`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `real_cloud_db_connected=false`
- `real_oss_connected=false`
- `real_oss_upload_success=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `archive_evidence_written=true`

幂等键：`task_id + evidence_id`。

### D. `GET /api/o6/archive/evidence`

查询参数：

- `robot_id`
- `task_id`
- `evidence_type`
- `event_id`
- `limit`，默认 50，上限 200

返回要求：

- 固定 `schema=trashbot.o6.archive_evidence.v1`、`source=local_mock_evidence_archive`、`proof_status=not_proven`。
- 返回 `query`、`evidence_refs[]`、`evidence_summary`。
- 只返回白名单字段：`evidence_id/evidence_type/evidence_ref/captured_at_ms/event_id/content_type/size_bytes/checksum/metadata/created_at_ms/updated_at_ms`。
- 不返回 credential URL、token、原始图片、原始音频、base64 内容或完整日志。

## Fail-Closed 规则

所有写入接口必须满足：

- bad JSON、非对象 JSON、空 body：拒绝。
- `events[]` / `evidence_refs[]` 非数组、为空或超过上限：拒绝。
- `unknown_task`：task 不存在时拒绝，不能隐式创建 task。
- `unauthorized_task`：`robot_id` 与 task 不一致时拒绝。
- 类型白名单不匹配：拒绝。
- `occurred_at_ms` / `captured_at_ms` 不在 task 时间窗内：拒绝。
- metadata 超长、超深、含非白名单字段或 unsafe content：拒绝。
- payload 含 `Authorization`、`Bearer`、`token`、`password`、`secret`、`private_key`、credential URL、`/cmd_vel`、串口路径、`baudrate`、`traceback`：拒绝。
- payload 声明真实能力：`production_ready=true`、`cloud_db_connected=true`、`oss_uploaded=true`、`robot_control_executed=true`、`delivery_success=true`：拒绝。

GET 查询接口必须满足：

- 非法 `limit`、未知 `event_type`、未知 `evidence_type`、非法时间窗：拒绝。
- 未命中 task 或 robot scope 不一致：返回 fail-closed，不泄露其他 task 数据。
- 返回数据必须先经过白名单裁剪。

## 真实能力 false 边界

所有成功响应必须固定：

- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `real_cloud_db_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`

events 响应还必须固定：

- `real_oss_connected=false`
- `archive_event_written=true`

evidence 响应还必须固定：

- `real_oss_connected=false`
- `real_oss_upload_success=false`
- `archive_evidence_written=true`

解释边界：

- `archive_event_written=true` 只表示 local/mock store 写入成功。
- `archive_evidence_written=true` 只表示 evidence ref 写入成功。
- `evidence_ref` 存在不证明 OSS 对象存在、上传成功、CDN 可读或真实现场采集成功。

## 测试计划

实现阶段必须新增或扩展 unittest，覆盖：

- events 成功写入、列表查询、按 `event_type` 查询、按时间窗查询。
- events 幂等更新与混合批次。
- evidence 成功写入、列表查询、按 `evidence_type` / `event_id` 查询。
- evidence 幂等更新与混合批次。
- `unknown_task`、`unauthorized_task`。
- bad JSON、非对象 JSON、缺字段、数组过大、非法 limit、非法类型。
- unsafe content 与真实能力声明 fail-closed。
- 写入后 task detail 仍能读到兼容 `events[]` / `evidence_refs[]`。

## 验收命令（实现阶段）

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
rg -n "trashbot\\.o6\\.archive_events\\.v1|trashbot\\.o6\\.archive_evidence\\.v1|POST /api/o6/archive/events|GET /api/o6/archive/events|POST /api/o6/archive/evidence|GET /api/o6/archive/evidence|local_mock_event_archive|local_mock_evidence_archive|real_oss_upload_success=false|archive_event_written|archive_evidence_written|unknown_task|unauthorized_task|fail-closed" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_05-06_o6-event-evidence-archive
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_05-06_o6-event-evidence-archive
```

## 验收命令（本设计阶段）

```bash
test -f sprints/2026.06.09_05-06_o6-event-evidence-archive/pre_start.md && test -f sprints/2026.06.09_05-06_o6-event-evidence-archive/prd.md && test -f sprints/2026.06.09_05-06_o6-event-evidence-archive/tech-plan.md
```

```bash
rg -n "sprint_type: epic|O6-KR2|O6-KR3|POST /api/o6/archive/events|GET /api/o6/archive/events|POST /api/o6/archive/evidence|GET /api/o6/archive/evidence|OKR 最低优先级核对|full-stack-software-engineer" sprints/2026.06.09_05-06_o6-event-evidence-archive
```

```bash
git diff --check -- sprints/2026.06.09_05-06_o6-event-evidence-archive
```

## 交付门槛

- 设计阶段：本目录三份文档通过存在性、关键字和 diff 健康检查。
- 实现阶段：代码、测试、接口文档、产品文档和 README 同步完成，并通过实现阶段四条验收命令。
- 收口阶段：补齐 `tech-done.md`、`side2side_check.md`、`final.md`，明确真实能力未证明的剩余风险。

## 剩余风险

- 本轮不更新 `OKR.md`，因为实现范围限定在 O6 event/evidence API、接口文档和 sprint 收口；O6 百分比建议留给后续 Product Owner 基于连续软件证据统一调整。
- 本轮不证明任何真实 OSS、真实 cloud DB、production cloud、4G、真实机器人控制或真实现场事件。
- 后续如果 O7 需要分页游标、事件订阅、WebSocket 或 audit log，需要另起 sprint。
