# Sprint 2026.05.12_07-08 Remote Cloud Production Preflight - Final

## 状态

- 阶段：final
- 时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 最终结论：DONE_WITH_CONCERNS
- 证据边界：`software_proof_docker_preflight_gate`

## 用户价值和产品北极星

本轮把 O6 的核心风险从“Docker relay 能跑，但上线前缺口分散”收敛为一个可执行 production preflight gate。它对普通手机用户的价值是间接但必要的：后续真实云上线前，系统能先用 phone-safe 语言暴露凭证、TLS/公网、OSS/CDN、state store 和敏感输出问题，避免把配置问题误报成机器人故障。

产品北极星仍是普通用户只用手机，通过 4G 云中转让小车完成 trash delivery。本轮没有交付真实手机 UI，也没有交付真实云或真实机器人运行，只完成上线前置 gate 的软件证据。

## OKR 映射

| Objective/KR | 最终状态 |
| --- | --- |
| O6 KR1 commands/status/ack | 保持兼容；preflight 是旁路 gate。 |
| O6 KR2 云服务端基线 | TLS/public ingress 缺口可被 gate 阻断。 |
| O6 KR3 OSS 写入策略 | OSS/CDN 目标配置可检查，但真实链路未验证。 |
| O6 KR4 CDN 入口 | CDN base URL 口径可检查，但无实流量。 |
| O6 KR5 凭证管理 | missing/placeholder credential 和输出脱敏已纳入 gate。 |
| O6 KR6 graceful degradation | blocked/warning/pass、`safe_summary`、`retry_hint` 可支撑后续手机提示。 |
| O5 手机体验 | 只有 phone-safe readiness 支撑，不提升完成度。 |
| O1/O2/O3/O4 | 本轮无新增真实硬件、任务、导航或感知证据，不提升。 |

## KR 拆解或更新

- O6：从约 27% 小幅更新为约 30%，新增证据是 `software_proof_docker_preflight_gate`。
- O5：保持约 33%，本轮没有正式手机 UI、普通用户实机验收或真实远程手机流程。
- O1：保持约 75%，无真实 WAVE ROVER、串口、HIL、`/odom`、`/imu/data` 或 `/battery` 新证据。
- O2：保持约 74%，无真实任务送达、Nav2/fixed-route 或任务恢复实跑证据。
- O3：保持约 76%，无真实路线采集、Nav2 waypoint/fixed-route 实跑或 keyframe 实景证据。
- O4：保持约 75%，无真实相机、楼层识别、门状态识别或上车视觉证据。

## 本轮核心抓手

本轮核心抓手是 `production preflight gate`：

- `/preflightz` endpoint。
- `python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight` CLI。
- `PREFLIGHT_EVIDENCE_BOUNDARY=software_proof_docker_preflight_gate`。
- credential provisioning、TLS/public ingress、OSS/CDN、state store、phone-safe output checks。
- Docker smoke 中的 preflight blocked 和 command/status/ack 主路径 smoke。
- Robot compatibility fence 确认 gate 不改变 remote bridge 主路径。

## 做什么 / 不做什么

已做：

- 接受 Docker/local production preflight gate 为 O6 软件侧小幅进展。
- 将 blocked preflight 归类为云端生产配置缺口。
- 更新当前 sprint `side2side_check.md` / `final.md` 和 `OKR.md` 进度快照。

未做且不声明：

- 没有真实云部署。
- 没有真实 4G/SIM。
- 没有 HTTPS/TLS 公网实证。
- 没有 OSS/CDN 实流量。
- 没有生产 DB/queue。
- 没有 Nav2/fixed-route 实跑。
- 没有 WAVE ROVER、真实串口或 HIL。
- 没有正式手机 UI 或普通用户实机验收。

## 优先级和验收口径

| 优先级 | 验收口径 | 最终判断 |
| --- | --- | --- |
| P0 | Gate 可在 Docker/local 环境执行 | 满足 |
| P0 | Gate blocked 能说明缺生产配置而非伪装 pass | 满足 |
| P0 | 输出包含 `software_proof_docker_preflight_gate` 边界 | 满足 |
| P0 | 敏感字段不进入 phone-safe 输出 | 满足 |
| P0 | command/status/ack robot compatibility 不退化 | 满足 |
| P0 | OKR 只小幅提升 O6，不提升 O5/O1/O2/O3/O4 | 满足 |

## 对应责任 Engineer

- `full-stack-software-engineer` 完成 gate、checks、Docker smoke 和 docs/product 同步。
- `robot-software-engineer` 完成 remote bridge compatibility fence。
- `product-okr-owner` 完成本轮验收收口、`OKR.md` 保守快照和 sprint final。

## 验证证据摘要

来自 `tech-done.md` 的工程验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 12 tests in 4.714s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
exit 0
```

```text
production preflight endpoint:
"evidence_boundary": "software_proof_docker_preflight_gate"
"production_ready": false
"overall_status": "blocked"
"missing_or_placeholder_credential"
"https_public_ingress_missing"
"oss_cdn_not_production_ready"
"file_backed_store_only"
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py src/ros2_trashbot_behavior/test/test_remote_bridge.py
Ran 31 tests in 15.218s
OK
```

Product 收口验证将在本文件落地后执行：

```bash
git diff --check -- OKR.md sprints/2026.05.12_07-08_remote-cloud-production-preflight/side2side_check.md sprints/2026.05.12_07-08_remote-cloud-production-preflight/final.md sprints/2026.05.12_07-08_remote-cloud-production-preflight/tech-done.md
ls -la sprints/2026.05.12_07-08_remote-cloud-production-preflight
```

## 风险、阻塞和需要补齐的证据链

- 生产云证据仍缺：云主机、域名、HTTPS/TLS、公网入口、防火墙、生产环境变量和运维边界。
- 真实网络证据仍缺：4G/SIM、弱网/断网恢复、公网链路稳定性。
- OSS/CDN 证据仍缺：STS/受限 AK、真实上传、CDN 回源、生命周期、权限和实流量。
- 生产状态证据仍缺：DB/queue、多实例一致性、备份、灾备、rotate。
- 机器人实证仍缺：Nav2/fixed-route、WAVE ROVER、真实串口、HIL、真实送达和同一 `evidence_ref` 复盘。
- 手机体验证据仍缺：正式 UI、美观验收、主流手机尺寸验收和普通用户实机流程。

## 后续建议

下一轮 O6 应优先补真实云最小 staging 环境：HTTPS public ingress、生产 secret provisioning、受限 state backend 和 preflight 从 blocked 到部分 pass 的真实证据。仍需保持保守边界：没有真实 4G/SIM、OSS/CDN 实流量和生产 DB/queue 前，不把 O6 写成生产完成。
