# O6 Cloud Archive Core API

## Scope

O6 cloud archive core 在 `cloud-relay` runtime 上新增 bearer-gated REST API，用于任务存档、事件存档、OSS `evidence_ref`、标注和推理记录。当前实现是本地/Docker software proof，持久层为单机 JSON 文件，证据边界固定为 `software_proof_o6_cloud_archive_core`。

该接口不替代 `trashbot.remote.v1` commands/status/ack，不暴露 `/cmd_vel`，不连接真实 OSS，不连接 production DB/queue，也不证明真实公网、4G、HIL 或送达成功。

## Schemas

- `trashbot.archive.v1`：任务、事件、任务详情和事件查询。
- `trashbot.annotation.v1`：PC/运营端提交和查询标注结果。
- `trashbot.inference.v1`：云端或外部推理结果记录，并同步写入事件时间线。
- `trashbot.o6.archive_health.v1`：O6 archive live health 只读探测结果。

所有响应必须包含：

- `source=software_proof`
- `proof_status=not_proven`
- `evidence_boundary=software_proof_o6_cloud_archive_core`
- `production_ready=false`
- `production_db_connected=false`
- `not_proven` 包含 `not_proven_production_db`

## Endpoints

```text
GET  /api/o6/archive/health

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

## Archive Live Health

`GET /api/o6/archive/health` 是 PC/手机/运维后续探测 O6 archive API 是否可用的稳定入口。它只读本地 proof store，不发送命令、不写 robot command store、不读取硬件、不执行 OSS upload 或模型推理。

响应固定包含：

- `schema=trashbot.o6.archive_health.v1`
- `capability=o6_archive_live_health`
- `archive_api_status=empty|ready|store_unavailable`
- `task_count`、`event_count`、`annotation_count`、`inference_count`
- `latest_task_ref`：仅包含 `robot_id`、`task_id`、`date`、`status`、`updated_at` 和 `evidence_ref_summary`
- `storage_backend=json_file_proof`
- `production_ready=false`
- `production_db_connected=false`
- `real_oss_upload=false`
- `real_inference_model_runtime=false`
- `safe_to_control=false`
- `sends_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `not_proven` 和 `next_required_evidence`

`latest_task_ref.evidence_ref_summary` 只输出 `present`、`kind`、`uri_scheme`、`source`、`proof_status`、`checksum_present`。它不得回显本地文件路径、完整 OSS key、token、Authorization、DB/queue URL 或 traceback。

如果 archive store JSON 损坏、schema 错误或不可读，health route 返回 HTTP 503，`archive_api_status=store_unavailable`，`error=archive_store_unavailable`，并保持 `redaction_status=passed`。503 payload 不包含 state path、异常类型、traceback 或本机目录。

### PC Workstation Aggregated Health Probe

PC workstation 侧的 `GET /api/o5-o6/cloud-relay-health` 只把 O5
`/api/o5/readiness/health` 和 O6 `/api/o6/archive/health` 汇总成一个本机
operator 视图。它从 query 或 `ROBER_CLOUD_RELAY_BASE_URL` 读取 private /
loopback base URL，bearer 只从 `TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN` 或
`ROBER_CLOUD_RELAY_BEARER_TOKEN` 环境变量读取，不从 URL、query 或浏览器输入读取
token。

该 PC endpoint 对 O6 的读取边界和上面的 Archive Live Health 一致：只 GET
`/api/o6/archive/health`，只展示 schema、capability、`archive_api_status`、
计数和 `next_required_evidence` 摘要，不读取任务详情、不写 archive store、不触发
annotation/inference、不上传 OSS、不连接 production DB/queue、不发送 robot command。
任何 O6 schema mismatch、HTTP 非 2xx、坏 JSON、敏感字段、`reads_hardware=true`、
`connects_cloud_production=true` 或控制/生产相关 true flag 都必须让聚合响应
fail closed，并保持 `production_ready=false`、`safe_to_control=false`、
`sends_commands=false`、`robot_control_executed=false` 和 `delivery_success=false`。

### External / Upper-Computer Live Probe

`pc-tools/workstation/scripts/o5-o6-external-live-probe.mjs` 是 O6 与 O5 共用的
外部/上位机只读证据入口。脚本输出
`schema=trashbot.o5_o6.external_live_probe.v1`，从外部主机视角同时验证：

- cloud-relay `GET /api/o5/readiness/health`；
- cloud-relay `GET /api/o6/archive/health`；
- PC workstation `GET /api/o5-o6/cloud-relay-health` 聚合视图。

O6 archive 侧仍只允许读取 health 摘要，不读取 task detail，不写 archive store，
不触发 annotation/inference，不上传 OSS，不连接 production DB/queue。脚本的 bearer
只来自环境变量，输出只记录 `token_status`；网络不通、HTTP 非 2xx、坏 JSON、schema
mismatch、敏感 marker、控制/生产 true flag 或 PC aggregate 不可达时统一落成
`probe_status=fail_closed` 和稳定 endpoint failure 分类。脚本固定
`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、
`reads_hardware=false`、`delivery_success=false`，因此只能作为 external live probe
入口和 fail-closed 证据，不证明真实云、真实 4G/SIM、production DB/queue、真实
OSS upload、真实推理 runtime、真实 phone/browser、上车数据或 delivery success。

`cloud-relay/scripts/o5_o6_external_live_probe.py` 是同一证据入口的 Python 3
stdlib runner，输出同一 schema 并额外标记 `runner=python_stdlib`。它只依赖
`argparse/json/urllib` 等标准库，适合 Orange Pi 上位机缺 Node.js 时通过 stdin 运行：

```bash
ssh -p 37878 root@192.168.1.11 'python3 -s - --once-json --output /safe/runtime/o5-o6-external-live-probe.json' < cloud-relay/scripts/o5_o6_external_live_probe.py
```

该 runner 仍只 GET O5 readiness、O6 archive 和可选 PC aggregate health；bearer
只从 `TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN` 或 `ROBER_CLOUD_RELAY_BEARER_TOKEN`
读取，输出只包含 `token_status`。缺 URL、网络不可达、HTTP 非 2xx、坏 JSON、
schema mismatch、敏感 marker、控制/生产 true flag 或 PC aggregate 不可达都会
落成 `probe_status=fail_closed`，并保持 `safe_to_control=false`、
`sends_commands=false`、`robot_control_executed=false`、`reads_hardware=false`、
`delivery_success=false`。它不读取 task detail，不写 archive store，不触发
annotation/inference，不上传 OSS，不连接 production DB/queue，不证明真实云、
真实 4G/SIM、真实 phone/browser、上车数据或 delivery success。

当 cloud base URL 使用 `https://` 时，Python stdlib runner 会额外输出
`tls_evidence`。该字段只用于 O5/O6 外部 HTTPS 观测材料捕获，不改变 archive
health 的只读边界，也不把探针升级为 production ready。字段包括：
`tls_status`、`scheme`、`hostname_redacted`、`host_status`、`port`、
`tls_observed`、`tls_version`、`cipher_status`、`cipher_bits`、
`certificate.not_before`、`certificate.not_after`、
`certificate.certificate_expiry_days`、issuer/subject 字段存在摘要、SAN DNS/IP
计数和 `verification_error` 分类。raw host、raw base URL、完整 issuer/subject
DN、SAN 域名列表、token、Authorization、traceback、私钥路径和 artifact path
不得进入输出。`http://` 时 `tls_status=not_applicable`；未配置 URL 时
`tls_status=not_configured`；URL 被拦截或 TLS/证书握手失败时
`tls_status=blocked`，整体 probe 继续 fail closed。

PC workstation 额外提供 `GET /api/o5-o6/external-probe-artifact`，用于运维读取
最近一次 external live probe artifact 的脱敏摘要。读取顺序是
`ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT` 指向的安全落盘文件，或
`.workstation-runtime/o5-o6-external-live-probe.json`。响应 schema 为
`trashbot.pc_tools_workstation.o5_o6_external_probe_artifact.v1`，只展示
`probe_status`、runner、`updated_at`、endpoint reachability、schema match
计数、blocked reasons、`tls_evidence`、`no_post` / `no_robot_control` /
`no_hardware_read` 和固定 false safety fields。PC API 只转发 TLS 观测摘要：
host 为 hash-only，issuer/subject 为字段计数，SAN 为数量统计，verification
error 为分类枚举；不展示 raw URL、raw host、证书 DN 原文、token、artifact path
或 traceback。该 API 不执行 probe、不发网络请求、不访问 `/robots/*`、不读取
硬件；缺文件、坏 JSON、schema mismatch 或 unsafe true field 均 fail closed。

`GET /api/real-material/acceptance` 会把同一份 O5/O6 artifact 转成 operator
queue，并在 `collection_runbook.collection_paths[]` 同时列出
`pc_node_npm` 与 `upper_computer_python_stdlib` 两条采集路径。两条路径输出同一
`trashbot.o5_o6.external_live_probe.v1` schema；上位机 Python 路径可通过
`--once-json` stdout 或 `--output` 文件落盘，再复制回 PC workstation runtime 或由
`ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT` 指向。该 queue 仍只读已有 artifact，不执行
probe、不 POST、不访问 `/robots/*`、不读取硬件。

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
