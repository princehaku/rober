# Sprint 2026.05.12_08-09 Remote Cloud SQLite State Proof - Final

## 状态

- 阶段：final
- 时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 最终结论：DONE_WITH_CONCERNS
- 证据边界：`software_proof_docker_sqlite_state_store`

## 用户价值和产品北极星

本轮把 O6 从上一轮 Docker preflight 仍指出的 file-backed/state-store 缺口推进到 SQLite-backed state store software proof。用户价值是为未来普通手机用户的云端控制面提供更可靠的恢复语义：relay 或 store 重启后，命令、状态和 ACK 轨迹可以继续被读取，而不是停留在更弱的 file-backed/preflight 证明。

产品北极星保持不变：普通手机用户通过 4G 云中转控制小车完成 trash delivery。本轮没有把 SQLite proof 包装成真实云部署、真实 4G、生产 DB/queue、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL 完成。

## OKR 映射

| Objective/KR | 最终状态 |
| --- | --- |
| O6 KR1 commands/status/ack | SQLite backend 下 command/status/ack recovery proof 通过，HTTP shape 不变。 |
| O6 KR2 云服务端基线 | 单实例 SQLite state proof 通过，但生产 DB/queue、多实例、备份和灾备仍未证明。 |
| O6 KR5 凭证管理 | preflight/error output 继续过滤 bearer、Authorization、OSS secret、root password 和硬件/ROS 底层细节。 |
| O6 KR6 graceful degradation | SQLite path 缺失、不可写或初始化失败有 phone-safe reason；blocked/warning 不伪装 production pass。 |
| O5 手机体验 | 仅有 phone-safe readiness/retry hint 支撑，没有正式手机 UI 或普通用户验收，不提升。 |
| O1/O2/O3/O4 | 无真实硬件、任务、路线、相机或 HIL 新证据，不提升。 |

## KR 拆解或更新

- O6：从约 30% 保守小幅更新为约 32%，新增证据是 `software_proof_docker_sqlite_state_store`。
- O5：保持约 33%，本轮没有正式手机 UI、美观验收、真实远程手机流程或普通用户实机验收。
- O1：保持约 75%，本轮没有 WAVE ROVER、串口、底盘反馈、`/odom`、`/imu/data`、`/battery` 或 HIL 新证据。
- O2：保持约 74%，本轮没有真实 Nav2/fixed-route 送达、任务恢复实跑或真实垃圾投递证据。
- O3：保持约 76%，本轮没有真实路线采集、keyframe/live frame、Nav2 waypoint 或 fixed-route 实跑证据。
- O4：保持约 75%，本轮没有真实相机采集、门状态识别、楼层识别或上车视觉证据。

## 本轮核心抓手

- `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` SQLite backend。
- command/status/ack 跨 store reopen 或 relay/container restart 恢复。
- `/preflightz` / `--preflight` 输出 `evidence_boundary=software_proof_docker_sqlite_state_store`。
- production DB/queue、多实例一致性、backup/restore、disaster recovery 缺口持续阻断。
- remote bridge compatibility acceptance 确认 robot side 主路径和 cursor/ACK 保守语义未退化。

## 做什么 / 不做什么

已做：

- 接受 Task A SQLite-backed state store proof。
- 接受 Task B remote bridge compatibility acceptance。
- 更新 `OKR.md` 当前进度快照，O6 保守提升到约 32%。
- 创建 `side2side_check.md` 和 `final.md`，并在 `tech-done.md` 补 Product acceptance 摘要。

未做且不声明：

- 没有真实云部署、域名、公网 HTTPS/TLS 或防火墙。
- 没有真实 4G/SIM、弱网/断网恢复。
- 没有 OSS/CDN 上传、CDN 回源、生命周期、权限或实流量。
- 没有生产 DB/queue、多实例一致性、备份、灾备或生产运维。
- 没有正式手机 UI、美观验收或普通用户实机验收。
- 没有 Nav2/fixed-route、WAVE ROVER、真实串口、HIL 或真实送达。

## 优先级和验收口径

| 优先级 | 验收口径 | 最终判断 |
| --- | --- | --- |
| P0 | SQLite backend 可显式启用 | 满足 |
| P0 | Command/status/ack 可跨 reopen/restart 恢复 | 满足 |
| P0 | Remote bridge compatibility 不退化 | 满足 |
| P0 | ACK/cursor 不被写成 delivery result | 满足 |
| P0 | Preflight 记录 `software_proof_docker_sqlite_state_store` | 满足 |
| P0 | Production DB/queue、多实例、backup/DR 缺口清晰 | 满足 |
| P0 | O6 小幅提升，其他 Objective 不提升 | 满足 |

## 对应责任 Engineer

- `full-stack-software-engineer`：完成 SQLite store proof、preflight boundary、Docker smoke、targeted tests 和相关 docs/product 同步。
- `robot-software-engineer`：完成 remote bridge compatibility acceptance，确认 robot polling、status、ACK 和 cursor 语义未退化。
- `product-okr-owner`：完成 OKR 保守更新、side-by-side acceptance 和 final closure。

## 验证证据摘要

来自 Task A：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 16 tests in 5.803s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
exit 0
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

来自 Task B：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py src/ros2_trashbot_behavior/test/test_remote_bridge.py
Ran 31 tests in 15.221s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
exit 0
```

Product 收口验证：

```text
git diff --check -- OKR.md sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/tech-done.md sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/side2side_check.md sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/final.md
```

```text
ls -la sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof
```

## 风险、阻塞和需要补齐的证据链

- 生产云证据仍缺：云主机、域名、HTTPS/TLS、公网入口、防火墙、生产 secret provisioning 和运维边界。
- 真实网络证据仍缺：4G/SIM、弱网/断网恢复和公网链路稳定性。
- OSS/CDN 证据仍缺：STS/受限 AK、真实上传、CDN 回源、生命周期、权限和实流量。
- 生产状态证据仍缺：DB/queue、多实例一致性、备份、灾备和 rotate。
- 机器人实证仍缺：Nav2/fixed-route、WAVE ROVER、真实串口、HIL、真实送达和同一 `evidence_ref` 复盘。
- 手机体验证据仍缺：正式 UI、美观验收、主流手机尺寸验收和普通用户实机流程。

## 后续建议

1. 基于上一轮 preflight 仍暴露 TLS/public ingress、credential provisioning 和 OSS/CDN 缺口，下一轮 O6 优先推进真实云最小 staging 入口。
2. 基于 Task A SQLite proof 只证明 Docker/local 单实例恢复，下一轮需要选择受限生产 state backend 或 staging DB/queue，并明确迁移、备份、灾备和多实例边界。
3. 基于 Task B remote bridge compatibility 已通过，下一轮继续保持 robot side contract 稳定，除非真实云 staging 暴露协议问题。
4. 基于 O6 仍缺真实 4G/SIM、OSS/CDN 实流量和生产鉴权 rotate，不应提升 O5/O1/O2/O3/O4。
