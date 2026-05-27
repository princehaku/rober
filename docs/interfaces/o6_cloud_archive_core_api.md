# O6 Cloud Archive Core API

## Scope

O6 cloud archive core 在 `cloud-relay` runtime 上新增 bearer-gated REST API，用于任务存档、事件存档、OSS `evidence_ref`、标注和推理记录。当前实现是本地/Docker software proof，持久层为单机 JSON 文件，证据边界固定为 `software_proof_o6_cloud_archive_core`。

该接口不替代 `trashbot.remote.v1` commands/status/ack，不暴露 `/cmd_vel`，不连接真实 OSS，不连接 production DB/queue，也不证明真实公网、4G、HIL 或送达成功。

## Schemas

- `trashbot.archive.v1`：任务、事件、任务详情和事件查询。
- `trashbot.annotation.v1`：PC/运营端提交和查询标注结果。
- `trashbot.inference.v1`：云端或外部推理结果记录，并同步写入事件时间线。

所有响应必须包含：

- `source=software_proof`
- `proof_status=not_proven`
- `evidence_boundary=software_proof_o6_cloud_archive_core`
- `production_ready=false`
- `production_db_connected=false`
- `not_proven` 包含 `not_proven_production_db`

## Endpoints

```text
POST /api/o6/archive/tasks
GET  /api/o6/archive/tasks?robot_id=<id>&task_id=<id>&date=<yyyy-mm-dd>&status=<status>
GET  /api/o6/archive/tasks/{task_id}?robot_id=<id>

POST /api/o6/archive/events
GET  /api/o6/archive/events?robot_id=<id>&task_id=<id>&event_type=<type>

POST /api/o6/annotations
GET  /api/o6/annotations?robot_id=<id>&task_id=<id>&annotation_status=<status>

POST /api/o6/inference
GET  /api/o6/inference?robot_id=<id>&task_id=<id>&inference_status=<status>
```

所有 `/api/o6/*` 路由复用 cloud-relay bearer gate。未授权返回 401；坏 JSON 或缺少必填字段返回 400；缺失任务详情返回 404。

## Required Fields

任务记录最小字段：

- `robot_id`
- `task_id`
- `created_at`
- `date`
- `status`
- `source`
- `proof_status`
- `evidence_ref`

事件记录最小字段：

- `robot_id`
- `task_id`
- `event_id`
- `event_type`
- `created_at`
- `source`
- `proof_status`
- `evidence_ref`
- `payload`

标注记录最小字段：

- `annotation_id`
- `robot_id`
- `task_id`
- `item_id`
- `label_type`
- `label_value`
- `annotation_status`
- `evidence_ref`

推理记录最小字段：

- `inference_id`
- `robot_id`
- `task_id`
- `inference_type`
- `inference_status`
- `model_ref`
- `result`
- `evidence_ref`

## evidence_ref

`evidence_ref` 只保存对象引用，不保存图片、视频或大日志正文。推荐形状：

```json
{
  "kind": "oss_object_ref",
  "uri": "oss://bytegallop/rober/<robot_id>/<date>/<task_id>/frame-001.jpg",
  "checksum": "",
  "source": "software_proof",
  "proof_status": "not_proven"
}
```

当前只验证字段形状，不证明真实 OSS 上传、STS 签发、CDN 回源或生命周期策略。

## Offline Algorithm Evidence Feed

`ros2_trashbot_nav.algorithm_evidence_feed` can generate a local `trashbot.archive.v1` bundle for O6/O7 software proof. The bundle includes one task, route-frame events, a keyframe event, elevator/floor/obstacle evidence events, ASR/TTS stub events, safe-command stub events, draft annotations, and inference-stub records.

Required safety boundary for this feed:

- `source=software_proof`
- `proof_status=not_proven`
- `evidence_boundary=software_proof_o6_o7_algorithm_evidence_feed`
- `mock_feed=true`
- `offline_only=true`
- `real_cloud_archive_connected=false`
- `real_realtime_api_connected=false`

The feed is a generator for schema and UI consumption checks only. It does not prove real route execution, real elevator door state, real floor recognition, real obstacle detection, real model robustness, real ASR/TTS runtime, real TTS playback, real safe-command API, real robot ACK, real OSS upload, production DB persistence, or O7 playback/submit/dispatch readiness.

## Storage Boundary

默认 state 路径优先由 `TRASHBOT_O6_ARCHIVE_STATE` 指定，Task C 验收建议显式指向 `/tmp` 或测试临时目录。未指定时使用 `TRASHBOT_REMOTE_CLOUD_STATE` 同目录下的 `*.o6_archive.json`；如果两者都为空，runtime fallback 为系统临时目录下的 `/tmp/o6_cloud_archive_state.json` 等价路径，不允许在仓库根目录生成 `o6_cloud_archive_state.json`。

这是单机 software proof store，不是 production DB。真实生产前至少需要补：

- production DB/queue 连接和迁移证据；
- 多实例一致性、备份恢复和灾备证据；
- 真实 OSS upload / STS / CDN live traffic 证据；
- 外部或 CPU 推理 runtime 证据。

## Objective 6 Mock 90 Evidence

`2026.05.28_00-04_mock-okr-90-acceptance` Task C 的可复验证据覆盖：

- cloud archive core 可在单命令 unittest 中写入和查询 task/event/annotation/inference；
- 机器人侧 `archive_event_publisher` 生成的 board event envelope 可被 `ArchiveStore.create_event()` 接收；
- `ros2_trashbot_nav.algorithm_evidence_feed` 生成的 offline/mock `trashbot.archive.v1` bundle 可和机器人侧事件共用同一 `robot_id/task_id` 存档，并可被 O7 PC adapter 派生为路线回放、标注、推理摘要、ASR/TTS stub 和手控/寻路 stub 的只读摘要；
- `TRASHBOT_O6_ARCHIVE_STATE` 或 fallback `/tmp` state fence 防止 `o6_cloud_archive_state.json` 落到仓库根目录。

该证据可支持 Objective 6 `90%+ mock/software completion` 判断，但真实安全隧道、production DB/queue、真实 OSS upload、真实推理 runtime 和 live O6 API 仍为 `not_proven`。
