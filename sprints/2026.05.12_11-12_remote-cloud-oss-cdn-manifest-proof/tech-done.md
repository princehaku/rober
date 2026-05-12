# Sprint 2026.05.12_11-12 Remote Cloud OSS/CDN Manifest Proof - Tech Done

## 状态

- 阶段：tech-done
- 更新时间：2026-05-12 12:28 Asia/Shanghai
- 主责 Engineer：`full-stack-software-engineer`
- Evidence boundary：`software_proof_docker_oss_cdn_manifest`

## 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 OSS/CDN manifest proof 常量、生成、校验和摘要 helper。
  - 新增 CLI：`--write-oss-cdn-manifest`、`--manifest-robot-id`、`--manifest-task-id`、`--manifest-date`。
  - 新增 preflight 输入：`TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT` 和 `--oss-cdn-manifest-artifact`。
  - `production_preflight_payload` 新增 `oss_cdn_manifest` check：有效 artifact 为 pass，缺失为 warning，无效为 blocked。
  - 有效 manifest artifact 会把 preflight evidence boundary 提升到 `software_proof_docker_oss_cdn_manifest`。
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 覆盖 manifest artifact 生成、字段 contract、checksum 校验、CDN URL 规则、无效 artifact fail-closed、preflight pass/warning/blocked 三类路径和脱敏断言。
- `docs/product/cloud_4g_infrastructure.md`
  - 同步 O6 manifest proof 的生成、preflight 消费、字段规则、环境变量和未证明边界。
- `docs/product/remote_4g_mvp.md`
  - 同步手机/云端远程 MVP 中 OSS/CDN manifest proof 的用户可见边界和 CLI 示例。

## 用户旅程变化

- 手机/云端后续展示诊断大对象时，不需要临时拼 bucket、prefix 或 CDN URL；本轮先固定可校验的对象引用 artifact。
- 预检可以区分三种用户可读状态：manifest 缺失是 warning，manifest 损坏或不合规是 blocked，manifest 合规则进入本地 software proof。
- 手机侧仍不会看到 bearer token、Authorization header、OSS secret、AK/SK、root password、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

## 接口影响

- command/status/ack HTTP API 未改变。
- 新增的 manifest artifact 是 local/Docker proof artifact，不是正式手机端 API。
- `/preflightz` 和 `--preflight` 会新增 `oss_cdn_manifest` check；这是 preflight JSON 的扩展，不改变 relay 主控制面协议。
- ACK 语义未改变：ACK 仍只表示 robot bridge 已处理 command envelope，不代表真实送达成功。

## 联调结果

- 本轮只做 Docker/local Python software proof。
- 未接入真实 OSS、STS、CDN、生产云、4G/SIM、HTTPS/TLS 公网入口、生产 DB/queue、Nav2/fixed-route、WAVE ROVER 或 HIL。
- ROS2 command/status/ack 主路径通过既有 relay unit fence 间接覆盖，manifest 逻辑没有修改 HTTP route、store、command normalize、status normalize 或 ACK normalize。

## 验证结果

已执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

结果：

```text
Ran 23 tests in 6.388s
OK
```

已执行：

```bash
PYTHONPATH=src/ros2_trashbot_behavior PYTHONDONTWRITEBYTECODE=1 python3 -m ros2_trashbot_behavior.remote_cloud_relay --write-oss-cdn-manifest "$tmp_manifest" --manifest-robot-id robot-local-proof --manifest-task-id task-local-proof --manifest-date 2026-05-12
PYTHONPATH=src/ros2_trashbot_behavior PYTHONDONTWRITEBYTECODE=1 ... python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight --oss-cdn-manifest-artifact "$tmp_manifest"
```

结果：

```text
manifest generate: ok=True, evidence_boundary=software_proof_docker_oss_cdn_manifest
preflight consume: ok=False, evidence_boundary=software_proof_docker_oss_cdn_manifest, overall_status=blocked, oss_cdn_manifest=pass
```

说明：preflight 仍 blocked 是预期结果，因为生产 DB/queue、backup/restore、真实上传/云/4G 等仍未证明。

已执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

结果：通过，无输出。

已执行：

```bash
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py scripts/remote_cloud_relay_docker_smoke.sh docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.05.12_11-12_remote-cloud-oss-cdn-manifest-proof/tech-done.md
```

结果：通过，无输出。

## 偏差和失败定位

- 第一轮 unit test 失败在 preflight 顶层 `not_proven` 仍使用旧 `external_tls/public_ingress` 命名，未包含 PRD 要求的 `https_tls_public_ingress`。
- 已修复为本轮 manifest proof 指定术语，重跑 unit test 通过。

## 剩余风险

- `software_proof_docker_oss_cdn_manifest` 只证明 schema、prefix、CDN URL 组合、checksum 和脱敏边界。
- 真实 OSS upload、STS issuance、CDN origin fetch、lifecycle policy、production account、real cloud、real 4G/SIM、HTTPS/TLS public ingress、production DB/queue、Nav2/fixed-route、WAVE ROVER/HIL 仍未证明。
- 正式手机 UI 尚未消费 manifest；后续需要定义 artifact 过期、刷新、权限和私有对象引用策略。
