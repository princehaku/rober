# Sprint 2026.05.12_11-12 Remote Cloud OSS/CDN Manifest Proof - Tech Plan

## 状态

- 阶段：tech-plan
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 计划结论：进入实现阶段，单主责 owner 执行，Robot 只做兼容性围栏。

## 技术方案

在现有 `ros2_trashbot_behavior.remote_cloud_relay` 的 preflight/backup artifact 口径上，增加 OSS/CDN manifest artifact proof。实现应复用现有 phone-safe 输出、preflight check、checksum 和 local/Docker proof 思路，不新增真实云依赖。

建议实现形态：

- 新增或扩展一个 manifest helper，负责生成和校验 JSON artifact。
- artifact schema 使用显式 `schema` 和 `schema_version`，避免后续真实上传接入时破坏兼容。
- checksum 使用稳定 JSON payload 计算，校验时排除 checksum 字段自身。
- preflight 支持通过环境变量或 CLI 参数读取 manifest artifact，例如 `TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT`。
- artifact valid 时新增 manifest check，输出 `passed`，并将 evidence boundary 提升到 `software_proof_docker_oss_cdn_manifest` 或等价清晰边界。
- artifact invalid/missing 时保持 blocked 或 warning，错误必须 phone-safe。
- manifest proof 不改变 relay command/status/ack HTTP API。

## Artifact contract

P0 字段：

```json
{
  "schema": "trashbot.oss_cdn_manifest",
  "schema_version": 1,
  "evidence_boundary": "software_proof_docker_oss_cdn_manifest",
  "created_at": "2026-05-12T11:20:00+08:00",
  "robot_id": "robot-local-proof",
  "task_id": "task-local-proof",
  "date": "2026-05-12",
  "bucket": "bytegallop",
  "region": "oss-cn-hangzhou",
  "prefix": "rober/robot-local-proof/2026-05-12/task-local-proof/",
  "cdn_base_url": "https://cdn.bytegallop.com/rober/",
  "objects": [
    {
      "name": "diagnostic_snapshot",
      "object_key": "rober/robot-local-proof/2026-05-12/task-local-proof/diagnostic_snapshot.json",
      "cdn_url": "https://cdn.bytegallop.com/rober/robot-local-proof/2026-05-12/task-local-proof/diagnostic_snapshot.json",
      "content_type": "application/json",
      "sha256": "placeholder-or-local-proof-hash",
      "bytes": 0,
      "redaction": "phone_safe"
    }
  ],
  "not_proven": [
    "real_oss_upload",
    "sts_issuance",
    "cdn_origin_fetch",
    "lifecycle_policy",
    "production_account",
    "real_cloud",
    "real_4g_sim",
    "https_tls_public_ingress",
    "production_db_or_queue",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil"
  ],
  "checksum": "<stable-payload-sha256>"
}
```

校验规则：

- `bucket` 必须是 `bytegallop`。
- `region` 必须是 `oss-cn-hangzhou`。
- `prefix` 必须匹配 `rober/<robot_id>/<date>/<task_id>/`。
- `cdn_base_url` 必须是 `https://cdn.bytegallop.com/rober/`。
- 每个 `object_key` 必须以 `prefix` 开头。
- 每个 `cdn_url` 必须等于 `cdn_base_url` + 去掉 `rober/` 前缀后的对象相对路径，或采用实现中明确且文档同步的等价规则。
- checksum 必须可复算。
- artifact 与 preflight 输出不得包含敏感字段或底层机器人控制字段。

## 文件范围

Full-stack 主责允许范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `scripts/remote_cloud_relay_docker_smoke.sh`（仅当需要把 manifest proof 纳入 smoke）
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.05.12_11-12_remote-cloud-oss-cdn-manifest-proof/tech-done.md`

Robot compatibility 允许范围：

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `sprints/2026.05.12_11-12_remote-cloud-oss-cdn-manifest-proof/tech-done.md`

禁止范围：

- 不修改 `OKR.md`。
- 不修改硬件/vendor 资料。
- 不修改 Nav2/fixed-route、WAVE ROVER、串口、launch 硬件参数。
- 不新增真实密钥、`.env` 或生产账号配置。

## 接口影响

- Cloud relay API 的 command/status/ack 路径必须保持兼容。
- Preflight JSON 可新增 manifest check 和 evidence boundary，但既有字段 `production_ready`、`overall_status`、`safe_summary`、`retry_hint`、per-check records 不应破坏。
- Manifest artifact 是新的 local proof artifact，不是手机端正式 API。
- ACK 语义不变：ACK 不等于 delivery success。

## 验收命令

Full-stack 实现围栏：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

如实现接入 Docker smoke，则运行：

```bash
TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT=18088 \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token \
scripts/remote_cloud_relay_docker_smoke.sh
```

Robot compatibility fence：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

文档和范围检查：

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  scripts/remote_cloud_relay_docker_smoke.sh \
  docs/product/cloud_4g_infrastructure.md \
  docs/product/remote_4g_mvp.md \
  sprints/2026.05.12_11-12_remote-cloud-oss-cdn-manifest-proof/tech-done.md
```

本计划文档自身验收：

```bash
ls -la sprints/2026.05.12_11-12_remote-cloud-oss-cdn-manifest-proof
```

```bash
git diff --check -- \
  sprints/2026.05.12_11-12_remote-cloud-oss-cdn-manifest-proof/pre_start.md \
  sprints/2026.05.12_11-12_remote-cloud-oss-cdn-manifest-proof/prd.md \
  sprints/2026.05.12_11-12_remote-cloud-oss-cdn-manifest-proof/tech-plan.md
```

## Team 执行方式

当前 sprint 进入 implementation 时：

- 派 1 个 `full-stack-software-engineer` worker 单线负责实现、targeted tests、文档同步和 `tech-done.md`。
- 派 1 个 `robot-software-engineer` worker 执行 remote bridge compatibility fence；若无代码问题，只回填验证结果，不扩大实现。
- 两个 worker 不应同时改同一产品代码文件；`tech-done.md` 可由主责 Full-stack 汇总，Robot 只提供验证片段。

## 风险边界

- `software_proof_docker_oss_cdn_manifest` 只能证明 manifest shape 和本地校验，不证明真实 OSS/CDN。
- Docker/local preflight 即使 passed，也不能声明 production ready。
- 如果 Docker smoke 因本机 Docker 环境失败，需要记录为环境阻塞，并保留 unit/preflight proof；不能把 smoke 失败写成产品逻辑失败，除非日志指向实现缺陷。
- 本轮不读取 vendor 硬件资料，因为不涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 底盘协议、速度映射、反馈协议、引脚、电压、固件或机械尺寸。

## 完成后收口要求

- `tech-done.md` 必须写清实际改动、验证结果、偏差和未证明事项。
- `side2side_check.md` 必须对照 PRD P0 验收 manifest proof，不允许用 happy path 代替 redaction/negative case。
- `final.md` 必须明确是否建议 O6 从约 34% 保守上调，以及上调依据；没有实现证据时不得更新 OKR 进度。
