# Sprint 2026.05.12_09-10 Remote Cloud Backup Restore Drill - Tech Done

## 状态

- 阶段：tech-done
- 更新时间：2026-05-12 07:15:29 CST
- 本轮主责：`full-stack-software-engineer`
- 当前完成项：Task A - Backup/restore drill implementation
- 证据边界：`software_proof_docker_backup_restore_drill`

## 实际改动

### Relay backup/restore drill

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 SQLite backup artifact 格式：`trashbot.remote_cloud_relay_backup.v1`、version、metadata、`sha256` checksum 和 `evidence_boundary=software_proof_docker_backup_restore_drill`。
  - 新增 SQLite export/import helper，artifact 只保存已脱敏的 command/status/ack envelope，不保存 raw SQLite page、bearer token、Authorization header、OSS secret、root password、raw state path、ROS topic、串口、baudrate、WAVE ROVER 参数或 `/cmd_vel`。
  - 新增 CLI：
    - `--backup-state-to <artifact.json>`：从 SQLite state 生成 backup artifact。
    - `--restore-backup-from <artifact.json> --restore-state-path <state.sqlite>`：恢复 artifact 到新的 SQLite state。
    - `--backup-restore-drill --backup-state-to <artifact.json> --restore-state-path <state.sqlite>`：执行 backup -> restore -> command/status/ack shape 和 ACK cursor 保守语义验证。
    - `--overwrite-restore-state`：只用于临时 drill path，重跑时清理 restore proof state。
  - 扩展 preflight：新增 `backup_restore_drill` check。未提供 artifact 时保持 warning；artifact schema/version/evidence/checksum 不匹配时 blocked；artifact 有效时输出 `local_backup_restore_drill_artifact_valid`，但仍保持生产备份策略、真实 DR、生产 DB/queue、多实例一致性未证明。

### Tests and smoke

- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 新增 backup -> restore -> restored HTTP shape 测试，覆盖 restored status、ACK、pending command 和 `last_ack_id` cursor 保守语义。
  - 新增 checksum mismatch fail-closed 测试。
  - 新增 preflight 识别本地 backup artifact 且不声明生产 DR 的测试。
- `scripts/remote_cloud_relay_docker_smoke.sh`
  - 在 Docker SQLite relay 中通过 HTTP 填充 status、acked command、pending command。
  - 容器内执行 backup/restore drill，验证 artifact checksum、restored command/status/ack shape、cursor 保守语义和 phone-safe output。
  - 使用 `TRASHBOT_REMOTE_CLOUD_BACKUP_ARTIFACT` 运行 preflight CLI，验证本地 drill artifact 被识别，同时生产 DB/queue、生产备份策略、真实 DR 仍未证明。

### Docs and env placeholders

- `docs/product/cloud_4g_infrastructure.md`
  - 增加 backup/restore drill 边界、CLI 示例、preflight artifact env 和不得宣称事项。
- `docs/product/remote_4g_mvp.md`
  - 增加 SQLite backup artifact、restore fail-closed、ACK 不等于 delivery result、phone-safe output 字段说明。
- `.env.example`
  - 增加可选 `TRASHBOT_REMOTE_CLOUD_BACKUP_ARTIFACT` 占位说明，仅用于本地 preflight artifact 验证。

## 用户旅程变化和触点收益

- 未来 phone/operator 触点可以区分三类状态：
  - `backup_restore_drill_not_run`：还没有本地恢复演练证据。
  - `backup_restore_drill_artifact_invalid`：artifact 缺失、schema/version/evidence/checksum 不可信。
  - `local_backup_restore_drill_artifact_valid`：Docker/local SQLite backup artifact 可校验，但生产备份策略和真实 DR 仍未完成。
- 恢复后仍沿用 `trashbot.remote.v1` command/status/ack shape；手机端不需要理解 SQLite、路径、ROS topic 或串口细节。
- ACK 仍只表示 command envelope 处理状态，不被解释成真实送达结果；手机端仍应继续读 status。

## 验证结果

### Unit fence

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

关键输出：

```text
Ran 19 tests in 6.374s

OK
```

### Compile fence

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

结果：通过，无输出。

### Docker backup/restore smoke

```bash
PYTHONDONTWRITEBYTECODE=1 scripts/remote_cloud_relay_docker_smoke.sh
```

关键输出：

```text
== sqlite backup restore drill ==
{"backup_status": "passed", "checks": {"artifact_checksum": true, "cursor_ack_conservative": true, "phone_safe_output": true, "restored_ack_http_shape": true, "restored_command_http_shape": true, "restored_status_http_shape": true}, "counts": {"ack_count": 1, "command_count": 2, "source_backend": "sqlite", "status_count": 1, "target_backend": "sqlite"}, "drill_status": "passed", "evidence_boundary": "software_proof_docker_backup_restore_drill", ...}

== production preflight CLI recognizes local backup artifact without production DR claim ==
{"evidence_boundary": "software_proof_docker_backup_restore_drill", "checks": [... {"code": "local_backup_restore_drill_artifact_valid", ... "status": "pass"} ...], "not_proven": ["real_cloud", "real_4g", "external_tls", "public_ingress", "oss_upload", "cdn_origin", "production_db_or_queue", "multi_instance_consistency", "production_backup_policy", "real_disaster_recovery", "nav2_or_fixed_route", "wave_rover_hil"], ...}
```

结果：通过。Docker/local preflight 仍返回 non-zero/blocked 是预期结果，因为真实生产云、TLS、公网、OSS/CDN、生产 DB/queue、生产备份策略和真实 DR 没有证明。

## 失败定位

- 本轮 Task A 验证未出现需要修复的测试或 smoke 失败。
- Docker smoke 中 readiness 等待期间出现过一次 transient `curl: (56) Recv failure: Connection reset by peer`，脚本重试后 `/readyz` 正常返回 `ok=true`，不影响最终 smoke 结果。

## 剩余风险和需要配合事项

- 当前证据只支持 `software_proof_docker_backup_restore_drill`。
- 仍未证明：真实云、真实 4G/SIM、HTTPS/TLS 公网入口、OSS/CDN 实流量、生产 DB/queue、多实例一致性、生产备份策略、真实灾备、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL。
- 后续 `robot-software-engineer` 需要继续做 remote bridge compatibility acceptance，确认 robot polling、status、ACK 和 cursor 语义未退化。

---

## Task B - Remote Bridge Compatibility Acceptance

### 状态

- 执行时间：2026-05-12 07:18:18 CST
- 执行角色：`robot-software-engineer`
- 结论：通过。
- 证据边界：`software_proof_docker_backup_restore_drill` 的 robot-side compatibility acceptance；不等于真实云、真实 4G、真实送达、Nav2/fixed-route、WAVE ROVER 或 HIL。

### 实际改动

- 未改动 `remote_bridge_protocol.py` 或 `remote_bridge.py`。
- 未改动 remote bridge 测试文件；现有 targeted fence 已覆盖 `trashbot.remote.v1` status-command-ack 主路径、auth/cloud/malformed 降级不触发本地 action、不推进 cursor、ACK 失败不落盘 cursor，以及 ACK 只作为 command envelope terminal state 的语义。
- 仅更新本文件记录 Task B 验收证据。

### Compatibility Acceptance 结果

- `status -> command -> ack` HTTP shape 保持兼容：`RemoteCloudClient` 仍按 `/robots/<robot_id>/status`、`/commands/next?last_ack_id=...`、`/commands/<command_id>/ack` 与 independent relay round trip。
- Backup/restore/preflight 变化没有进入 robot polling 主路径；robot bridge 仍只消费 `command` envelope，并通过 status/ACK API 与云端交互。
- `auth_failed`、cloud unreachable、malformed response 均保持保守语义：不触发 `start_collection` / `confirm_dropoff` / `cancel_collection`，不发送 terminal ACK，不推进 `last_ack_id`。
- ACK 失败时仍不写 `cursor_state_path`，因此 restore/preflight blocked 或 warning 这类非 terminal delivery evidence 不能被误当作 command 完成游标。
- ACK 仍是 command envelope terminal state；真实 delivery result 仍必须继续看 status/task record，不能由 ACK 代表送达成功。

### 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

关键输出：

```text
Ran 31 tests in 15.219s

OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
```

结果：通过，无输出。

### 失败定位

- Task B 验收未发现 remote bridge compatibility regression。
- 未发现需要改动产品代码或补救 Task A backup/restore drill 的 robot-side gap。

### 剩余风险和协同事项

- 当前只验证 local Python/HTTP mock 与 independent relay compatibility，不覆盖真实云、真实 4G/SIM、生产 TLS、公网入口、生产 DB/queue、多实例、OSS/CDN、Nav2/fixed-route、WAVE ROVER 或 HIL。
- 不需要 Product 或 Full-stack 在 Task B 上返工；Product 后续可基于 Task A/B 结果执行 Task C 收口，但必须保持 `software_proof_docker_backup_restore_drill` 边界。

---

## Task C - Product Acceptance and OKR Closure

### 状态

- 执行时间：2026-05-12 09:10 Asia/Shanghai
- 执行角色：`product-okr-owner`
- 结论：通过，按软件证据边界收口。
- 证据边界：`software_proof_docker_backup_restore_drill`

### 用户价值和产品北极星

本轮让 O6 从 SQLite 单实例恢复能力推进到“可备份、可恢复、可演练”的 Docker/local 软件闭环。对普通手机用户的价值是未来云中转节点出现容器重建、本地 state 损坏或人工迁移时，系统已有可审计的恢复路径，并能用 phone-safe 状态说明恢复演练是否可信。

产品北极星保持不变：普通用户只用手机，通过 4G 云中转完成 trash delivery。本轮不把 backup/restore drill 包装成真实云灾备、真实 4G、正式手机 UI、真实送达或 HIL。

### OKR 映射和 KR 拆解

- O6 KR1：restore 后 `trashbot.remote.v1` command/status/ack shape 保持兼容，Robot compatibility acceptance 通过。
- O6 KR2：Docker/local 单实例 backup/restore drill 为后续 staging/production 提供软件证据，但不等于生产云 ready。
- O6 KR5：artifact、preflight 和 drill output 不应泄露 bearer token、Authorization header、OSS secret、root password、raw state path、ROS topic、串口、baudrate、WAVE ROVER 参数或 `/cmd_vel`。
- O6 KR6：backup/restore/preflight 对缺 artifact、checksum/schema mismatch 和生产灾备缺口保持 phone-safe blocked/warning。
- O5：仅获得 future phone-safe restore/readiness 文案素材，不提升正式手机 UI 或普通用户验收进度。

### 做什么 / 不做什么

已做：

- 接受 Task A 的 SQLite backup artifact、checksum、restore、CLI drill 和 preflight drill check。
- 接受 Task B 的 robot compatibility 结论：backup/restore/preflight 未改变 robot polling、status、ACK 和 cursor 保守语义。
- 将 O6 从约 32% 保守更新到约 34%，并保持 O5/O1/O2/O3/O4 不变。
- 创建 `side2side_check.md` 和 `final.md`，记录 evidence boundary、验证命令、缺口和不得宣称事项。

不做：

- 不声明真实云、真实 4G/SIM、HTTPS/TLS 公网入口、OSS/CDN 实流量、生产 DB/queue、多实例一致性、生产备份策略、真实灾备、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL。
- 不把 ACK 写成真实 delivery success；ACK 仍只代表 command envelope terminal evidence。
- 不修改代码、测试或 `docs/product/`，Task C 只做产品验收和 sprint/OKR 收口。

### 优先级和验收口径

- P0 backup artifact：Task A 已证明 artifact/checksum 可用。
- P0 restore drill：Task A Docker smoke 已输出 `backup_status=passed`、`restore_status=passed`、`drill_status=passed`。
- P0 robot compatibility：Task B remote bridge fence 输出 `Ran 31 tests in 15.219s OK`。
- P0 evidence boundary：所有收口文件保持 `software_proof_docker_backup_restore_drill`，并明确 production DR 和真实云缺口。
- P1 OKR closure：只更新 O6 到约 34%，其他 Objective 不变。

### Product 收口验证结果

```bash
ls -la sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill
```

关键输出：

```text
final.md
prd.md
pre_start.md
side2side_check.md
tech-done.md
tech-plan.md
```

```bash
git diff --check -- OKR.md sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/tech-done.md sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/side2side_check.md sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/final.md
```

结果：通过，无输出。

### 风险、阻塞和证据链缺口

- 当前是 Docker/local 单实例软件演练，不是生产备份策略、生产 DB/queue、多实例一致性或真实灾备。
- 当前没有真实云主机、HTTPS/TLS 公网入口、真实 4G/SIM、OSS/CDN 实流量、生产账号、弱网/断网恢复或 rotate 证据。
- 当前没有正式手机 UI、美观验收、普通用户实机验收、Nav2/fixed-route、WAVE ROVER 或 HIL 证据。
- 后续若进入 O6 下一轮，优先补真实 staging 云 HTTPS/public ingress 或生产级 state backend/backup policy，不应继续把本地 proof 包装成生产完成。
