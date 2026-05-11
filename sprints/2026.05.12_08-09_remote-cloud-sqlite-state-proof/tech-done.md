# Sprint 2026.05.12_08-09 Remote Cloud SQLite State Proof - Tech Done

## 状态

- 阶段：tech-done
- 执行时间：2026-05-12 Asia/Shanghai
- Owner：`full-stack-software-engineer`
- 任务：Task A - SQLite-backed state store proof
- 证据边界：`software_proof_docker_sqlite_state_store`

## 用户旅程变化

- 手机/云端入口的 command/status/ack API shape 继续保持 `trashbot.remote.v1`，普通用户和 robot remote bridge 不需要改调用方式。
- independent relay 可通过 `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` 使用 SQLite proof store；command 入队、robot status、terminal ACK 可跨 store reopen 或 relay restart 恢复。
- `/preflightz` 与 `--preflight` 能识别 SQLite backend，并把它解释为 Docker/local 单机恢复 proof，而不是生产 DB/queue 或真实云 ready。
- SQLite path 缺失、不可写或初始化失败时只输出 phone-safe `state_store_not_writable` / `not_ready` 类原因，不回显 bearer token、Authorization、OSS secret、root password、ROS topic、串口、baudrate、WAVE ROVER 参数或 `/cmd_vel`。

## 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `SQLiteRelayStore`，使用 SQLite 保存 commands/status/acks，保留现有 normalize 与 response envelope。
  - 新增 `build_relay_store()` 与 `--state-backend` / `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND` backend 选择。
  - preflight 对 `sqlite` 输出 `software_proof_docker_sqlite_state_store`，并明确 production DB/queue、多实例一致性、backup/restore、disaster recovery 未证明。
  - SQLite 连接封装为显式关闭 session，避免 ResourceWarning 污染验证证据。
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 增加 SQLite store reopen、HTTP relay restart 后 status/ack/cursor 恢复、unwritable path phone-safe、SQLite preflight boundary 与敏感输出过滤测试。
- `scripts/remote_cloud_relay_docker_smoke.sh`
  - 默认启用 SQLite backend smoke，覆盖 compose 启动、preflight、command/status/ack、container restart 后恢复和敏感输出过滤。
- `.env.example`
  - 增加 SQLite proof backend 示例，占位说明不等于生产 DB/queue、多实例、备份或灾备。
- `docker-compose.remote-cloud-relay.yml`
  - 增加 backend 选择说明，默认仍保留 file 以兼容既有 compose 使用。
- `docs/product/cloud_4g_infrastructure.md`
  - 同步 SQLite state proof 边界、env、preflight、持久化和未完成生产缺口。
- `docs/product/remote_4g_mvp.md`
  - 同步 independent relay 的 file/SQLite proof store、preflight boundary、restart 语义和 phone-safe 失败口径。

## 接口影响

- HTTP API shape 未变：
  - `POST /robots/{robot_id}/commands`
  - `GET /robots/{robot_id}/commands/next?last_ack_id=<id>`
  - `POST /robots/{robot_id}/status`
  - `GET /robots/{robot_id}/status`
  - `POST /robots/{robot_id}/commands/{command_id}/ack`
  - `GET /robots/{robot_id}/commands/{command_id}/ack`
- 新增内部/部署配置：
  - `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=file|sqlite`
  - CLI `--state-backend file|sqlite`
- ACK 仍只代表 command envelope terminal state，不代表真实送达、Nav2/fixed-route、WAVE ROVER 运动或 HIL。

## 验证结果

### Unit fence

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

关键输出：

```text
Ran 16 tests in 5.803s
OK
```

### Compile fence

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

结果：通过，无输出。

### SQLite state store smoke

```bash
PYTHONDONTWRITEBYTECODE=1 scripts/remote_cloud_relay_docker_smoke.sh
```

覆盖点：

- `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite`
- `/readyz` state store writable pass
- `/preflightz` 输出 `evidence_boundary=software_proof_docker_sqlite_state_store`
- command/status/ack 写入 SQLite backend
- Docker container restart 后读取同一 ack/status
- `last_ack_id=cmd-docker-smoke-1` 后 `command=null`，terminal ACK cursor 语义未改变
- preflight 输出包含 production DB/queue、多实例一致性、backup/restore、disaster recovery 未证明
- preflight 和错误输出过滤 Authorization、Bearer、`/cmd_vel`、ttyUSB、baudrate、WAVE ROVER 等敏感标记

关键输出片段：

```text
"evidence_boundary": "software_proof_docker_sqlite_state_store"
"code": "sqlite_state_store_proof_only"
"production_db_or_queue"
"multi_instance_consistency"
"backup_restore"
"disaster_recovery"
{"ok": true, "ack": {"command_id": "cmd-docker-smoke-1", ... "state": "acked"}}
{"ok": true, "status": {... "state": "idle", ...}}
{"ok": true, "command": null}
```

### Diff fence

```bash
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py scripts/remote_cloud_relay_docker_smoke.sh .env.example docker-compose.remote-cloud-relay.yml docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/tech-done.md
```

结果：通过，无输出。

## 失败定位与修复

- 第一轮 unit fence 失败于新增测试缩进错误：`IndentationError: unexpected indent`，已修正 `test_preflight_blocks_unwritable_state_store` 的断言缩进。
- 第二轮 unit fence 功能通过但出现 SQLite connection `ResourceWarning`，原因是 sqlite3 connection context manager 只 commit/rollback 不 close；已改为 `_session()` 显式关闭连接后重跑通过。

## 剩余风险

- 本轮仍是 Docker/local 软件 proof，不等于真实云、真实 4G/SIM、HTTPS/TLS 公网入口、OSS/CDN 实流量、生产 DB/queue、多实例一致性、备份、灾备、Nav2/fixed-route、WAVE ROVER 或 HIL。
- SQLite backend 只适合单实例 proof；生产需要明确数据库/队列、迁移、并发、备份恢复和灾备演练。
- Robot Platform Engineer 仍需执行 Task B compatibility acceptance，确认 remote_bridge status-command-ack 主路径和 cursor 保守语义未被 relay backend 选择影响。

---

## Task B - Remote Bridge Compatibility Acceptance

### 状态

- 阶段：tech-done / Task B acceptance
- 执行时间：2026-05-12 06:19 Asia/Shanghai
- Owner：`robot-software-engineer`
- 任务：Remote bridge compatibility acceptance
- 证据边界：`software_proof_docker_sqlite_state_store`

### 验收结论

- 未修改 robot bridge 产品代码或测试代码；当前 `remote_bridge_protocol.py` / `remote_bridge.py` 与既有 targeted tests 已覆盖本轮兼容性要求。
- SQLite backend 和 preflight 仍属于 independent relay 旁路/后端选择；robot polling 主路径继续只面向 `trashbot.remote.v1` 的 status-command-ack HTTP shape。
- ACK 仍只代表 command envelope terminal state，不代表真实送达、Nav2/fixed-route、WAVE ROVER 运动、4G 实网或 HIL。
- `auth_failed`、`cloud_unreachable`、`malformed_response` 和 ACK 提交失败场景保持保守语义：不推进 `last_ack_id` / cursor，不落盘 terminal cursor，不触发新的本地 action。

### 覆盖到的关键测试口径

- `test_client_round_trips_status_command_and_ack_with_independent_relay`：确认 independent relay 下 status -> command -> ack -> cursor 后无新 command 的主路径 shape 未变。
- `test_bearer_auth_failure_maps_to_phone_safe_cloud_error`：确认 bearer auth 失败映射为 `auth_failed` / `check_auth`，不泄露 Authorization/Bearer。
- `test_status_cloud_outage_does_not_poll_command_or_advance_cursor`：status 提交失败时不拉取 command、不触发本地 action、不推进 cursor。
- `test_auth_failed_get_posts_phone_safe_status_without_cursor_advance`：command poll 鉴权失败时不触发本地 action、不 ACK、不推进 cursor，并回写 phone-safe degraded status。
- `test_malformed_cloud_response_does_not_start_action_or_advance_cursor`：malformed cloud response 不解析 payload、不触发本地 action、不推进 cursor。
- `test_ack_failure_does_not_persist_cursor_state`：ACK 失败时不写 `remote_cursor.json`，`last_ack_id` 保持不变。
- `test_ack_failure_does_not_overwrite_successful_command_result`：本地 action 已提交但 ACK 失败时只缓存 command result，重试 ACK 不重复提交本地 action。

### 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

关键输出：

```text
Ran 31 tests in 15.221s
OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
```

结果：通过，无输出。

### 失败定位

- 本轮 Task B acceptance 未发现 robot-side compatibility 失败。
- 未执行真实 ROS2 graph、Nav2/fixed-route、WAVE ROVER、串口、4G/SIM、真实云或 HIL 验证；这些不在本轮 Docker-only robot compatibility fence 内。

### 剩余风险

- 证据仍是 Docker/local Python targeted fence；不等于真实云、真实 4G/SIM、HTTPS/TLS、公网入口、生产 DB/queue、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER 或 HIL。
- SQLite backend 的 production DB/queue、多实例一致性、备份和灾备缺口仍由 relay/preflight 侧继续阻断；robot bridge 只确认 HTTP shape 和 cursor/ACK 保守语义未退化。
- Product 仍需在 Task C 收口时保守更新 `OKR.md` / `side2side_check.md` / `final.md`，并明确 O6 只可小幅提升，O1/O2/O3/O4/O5 不因此提升。

---

## Task C - Product Acceptance and OKR Closure

### 状态

- 阶段：tech-done / Task C product acceptance
- 执行时间：2026-05-12 Asia/Shanghai
- Owner：`product-okr-owner`
- 任务：Product acceptance and OKR closure
- 证据边界：`software_proof_docker_sqlite_state_store`

### 产品收口结论

- 接受 Task A SQLite-backed state store proof：`TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` 下 command/status/ack 可跨 store reopen 或 relay/container restart 恢复。
- 接受 Task B remote bridge compatibility acceptance：remote bridge targeted tests `Ran 31 tests in 15.221s OK`，robot polling/status/ack/cursor 保守语义未退化。
- `OKR.md` 只将 O6 从约 30% 保守小幅更新为约 32%；O5/O1/O2/O3/O4 不提升。
- `side2side_check.md` 与 `final.md` 明确 SQLite proof 不是 production ready，不等于真实云、真实 4G/SIM、HTTPS/TLS 公网、OSS/CDN 实流量、生产 DB/queue、多实例、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL。

### 实际改动

- `OKR.md`
  - 更新 2026-05-12 09:00 进度快照。
  - 新增 `2026.05.12_08-09_remote-cloud-sqlite-state-proof` 证据。
  - O6 更新为约 32%，其他 Objective 保持不变。
- `sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/side2side_check.md`
  - 新增 side-by-side 产品验收、OKR 映射、边界和下一步建议。
- `sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/final.md`
  - 新增 sprint final、最终结论、验证证据摘要和剩余风险。
- `sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/tech-done.md`
  - 补充 Task C 产品收口摘要。

### 剩余风险

- SQLite backend 只证明 Docker/local 单实例恢复语义；生产 DB/queue、多实例一致性、备份、灾备和 rotate 仍缺。
- 本机 Docker-only，无真实云、真实 4G/SIM、HTTPS/TLS 公网、OSS/CDN 实流量、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL 证据。
- 下一轮 O6 应优先补真实云最小 staging 入口和受限 state backend，而不是继续扩大 Docker-only 证明范围。
