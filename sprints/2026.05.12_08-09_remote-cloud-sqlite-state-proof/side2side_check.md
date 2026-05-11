# Sprint 2026.05.12_08-09 Remote Cloud SQLite State Proof - Side-by-Side Check

## 状态

- 阶段：side2side_check
- 时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 工程证据来源：Task A `full-stack-software-engineer`、Task B `robot-software-engineer`
- 验收结论：PASS_WITH_BOUNDARY
- 证据边界：`software_proof_docker_sqlite_state_store`

## 用户价值和产品北极星

本轮验收确认 O6 从上一轮 file-backed/preflight proof 推进到 SQLite-backed state store proof。对普通手机用户的间接价值是：未来云中转重启后，command/status/ack 控制面状态不应因为单个 relay 进程重启而无声丢失。

产品北极星仍是普通手机用户通过 4G 云中转使用小车完成 trash delivery。本轮只接受 Docker/local SQLite 单实例恢复证明，不接受真实云、真实 4G、生产 DB/queue、OSS/CDN、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL 完成。

## Side-by-Side 对照

| 验收项 | 07-08 preflight 证据 | 08-09 SQLite 证据 | Product 判断 |
| --- | --- | --- | --- |
| State store 边界 | preflight 可识别 `file_backed_store_only`，仍是 file-backed proof | `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` 可启用 SQLite backend，command/status/ack 可跨 reopen/restart 恢复 | O6 可保守提升 |
| Command/status/ack API shape | Docker relay 主路径和 robot compatibility 已通过 | Task B remote bridge tests `Ran 31 tests in 15.221s OK`，未改 remote bridge 产品代码 | 兼容性可接受 |
| ACK/cursor 语义 | ACK 只代表 command envelope terminal state | auth/cloud/malformed/ACK failure 仍不推进 cursor、不伪造 local action 或 delivery result | 语义边界准确 |
| Phone-safe 输出 | preflight 输出 `safe_summary` / `retry_hint`，不泄露敏感字段 | SQLite unwritable/init/preflight 输出继续过滤 Authorization、Bearer、OSS secret、root password、ROS topic、串口、baudrate、WAVE ROVER 和 `/cmd_vel` | 可作为未来 O5 支撑，不提升 O5 |
| Production readiness | `production_ready=false`，blocked | SQLite pass 仍阻断 production DB/queue、多实例、backup/restore、disaster recovery | 不能写成 production ready |

## OKR 映射

| Objective/KR | 验收结果 |
| --- | --- |
| O6 KR1 commands/status/ack | 通过 SQLite backend recovery proof 小幅推进；HTTP contract 不变。 |
| O6 KR2 云服务端基线 | 从 file-backed proof 推进到单实例 SQLite proof，但未达到生产 DB/queue。 |
| O6 KR5 凭证管理 | Task A 证据显示 preflight/error output 持续过滤敏感字段。 |
| O6 KR6 graceful degradation | SQLite path 缺失、不可写或初始化失败输出 phone-safe blocked/not-ready reason。 |
| O5 | 只获得 phone-safe readiness/retry hint 支撑；没有正式手机 UI 或普通用户实机验收，不提升。 |
| O1/O2/O3/O4 | 没有真实硬件、真实任务、真实路线、真实相机或 HIL 新证据，不提升。 |

## KR 拆解或更新

- O6 从约 30% 保守小幅更新为约 32%。
- O5 保持约 33%，因为本轮没有正式手机 UI、美观验收、主流手机尺寸验收或普通用户远程流程。
- O1 保持约 75%，没有 WAVE ROVER、串口、`/odom`、`/imu/data`、`/battery` 或 HIL 新证据。
- O2 保持约 74%，没有真实 Nav2/fixed-route 送达或任务恢复实跑证据。
- O3 保持约 76%，没有真实路线采集、keyframe/live frame 或 fixed-route 实跑证据。
- O4 保持约 75%，没有真实相机、门状态、楼层识别或上车视觉证据。

## 本轮核心抓手

- SQLite-backed state store proof。
- command/status/ack reopen/restart recovery。
- `software_proof_docker_sqlite_state_store` preflight boundary。
- remote bridge compatibility acceptance。
- Product OKR conservative closure。

## 做什么 / 不做什么

已接受：

- SQLite backend 可作为 Docker/local 单实例 state recovery proof。
- command/status/ack 主路径和 remote bridge compatibility 未退化。
- O6 可按证据从约 30% 保守提升到约 32%。

不接受为完成：

- 真实云部署、域名、公网 HTTPS/TLS、防火墙。
- 真实 4G/SIM、弱网/断网恢复。
- OSS/CDN 上传、回源、生命周期、权限和实流量。
- 生产 DB/queue、多实例一致性、备份、灾备或生产运维。
- 正式手机 UI、普通用户实机验收。
- Nav2/fixed-route、WAVE ROVER、真实串口、HIL 或真实送达。

## 优先级和验收口径

| 优先级 | 验收口径 | 判断 |
| --- | --- | --- |
| P0 | SQLite backend 显式启用并可读写 state | 满足 |
| P0 | Command/status/ack 可跨 reopen/restart 恢复 | 满足 |
| P0 | Remote bridge status-command-ack shape 不变 | 满足 |
| P0 | ACK/cursor 不被解释成 delivery result | 满足 |
| P0 | Preflight 输出 `software_proof_docker_sqlite_state_store` | 满足 |
| P0 | Production DB/queue、多实例、backup/DR 缺口被明确阻断 | 满足 |
| P0 | OKR 只提升 O6，其他 Objective 不提升 | 满足 |

## 对应责任 Engineer

- `full-stack-software-engineer`：已完成 Task A SQLite store proof、preflight boundary、smoke 和相关 docs/product 同步。
- `robot-software-engineer`：已完成 Task B remote bridge compatibility acceptance。
- `product-okr-owner`：已完成 Task C Product acceptance、OKR 保守更新和 sprint 收口。

## 验证证据摘要

Task A：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 16 tests in 5.803s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 scripts/remote_cloud_relay_docker_smoke.sh
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

Task B：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py src/ros2_trashbot_behavior/test/test_remote_bridge.py
Ran 31 tests in 15.221s
OK
```

Product validation：

```text
git diff --check -- OKR.md sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/tech-done.md sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/side2side_check.md sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/final.md
```

```text
ls -la sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof
```

## 风险、阻塞和需要补齐的证据链

- 生产云证据仍缺：真实云主机、域名、HTTPS/TLS、公网入口、防火墙、生产 secret provisioning 和运维边界。
- 真实网络证据仍缺：4G/SIM、弱网/断网恢复和公网链路稳定性。
- OSS/CDN 证据仍缺：STS/受限 AK、真实上传、CDN 回源、生命周期、权限和实流量。
- 生产状态证据仍缺：DB/queue、多实例一致性、备份、灾备和 rotate。
- 机器人实证仍缺：Nav2/fixed-route、WAVE ROVER、真实串口、HIL、真实送达和同一 `evidence_ref` 复盘。
- 手机体验证据仍缺：正式 UI、美观验收、主流手机尺寸验收和普通用户实机流程。

## 下一步建议

1. 基于 07-08 preflight 仍暴露的 TLS/public ingress、credential provisioning 和 OSS/CDN 缺口，下一轮 O6 优先补真实云最小 staging 入口。
2. 基于 08-09 SQLite proof 已证明单实例恢复，但仍缺 production DB/queue，多实例和备份灾备应作为 staging 前后的明确 gate。
3. 基于 Task B remote bridge compatibility 已保持 robot 主路径，下一轮不要扩大 robot side 范围，除非真实云 staging 暴露协议兼容问题。
4. 基于 O6 仍缺真实 4G/SIM、OSS/CDN 实流量和生产鉴权 rotate，继续把后续证据写成 O6 云链路 proof，不要提升 O5/O1/O2/O3/O4。
