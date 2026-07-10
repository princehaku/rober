# O6/O7 Route Root Seed Gate Side-by-Side Check

## sprint_type: epic

## 验收结论

通过产品收口。实现结果满足 PRD/tech-plan 的核心目标：route-root seed local/mock smoke 不再强依赖 `route_bag` gate；在显式 route root + replay 场景下，缺少 `route_bag` 只产生 optional evidence / next evidence，而不阻断 `gate_pass=true` 或 O6/O7 consumer readiness。

证据边界为 `software_proof_local_mock_route_root_seed_gate_only`。本轮不声明真实生产云、真实 `route_bag`、真实媒体、真实 annotation API、真实 dataset export、真实机器人运动或 delivery success。

## PRD 对照

| 验收点 | 结果 | 证据 |
| --- | --- | --- |
| route-root seed local/mock smoke 不再强依赖 `route_bag` gate | 通过 | route-root fixture 输出 `gate_pass=true`，并暴露 `route_root_seed_gate` |
| 缺少 `route_bag` 时不阻断 seed smoke | 通过 | `route_bag_required=false`、`route_bag_present=false`、`route_bag_missing_optional`、`route_bag_optional_evidence` |
| O6 输出可回读 additive 摘要 | 通过 | `trashbot.o6.route_root_seed_gate.v1` 挂到 archive detail、field evidence consumer ingest、artifact bundle alias 和 O6 consumer detail |
| O7 consumer detail 展示 readiness | 通过 | UI/adapter 展示 route-root seed status、counts、blocked reasons、next evidence 和 false safety fields |
| dangerous true / unsafe refs / schema mismatch fail-closed | 通过 | O7 worker 测试覆盖，O6/O7 验证通过 |
| 安全旗标 false | 通过 | `safe_to_control: false`、`delivery_success: false`、`primary_actions_enabled: false`、`robot_control_executed: false` |

## 验证证据对照

- Algorithm：`python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py` 通过；route-root fixture 输出 `gate_pass=true`；`rg` 命中 `route_root_seed_gate`、`route_bag_required=false`、`route_bag_present=false`；`git diff --check` 通过。
- O6：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 通过；`python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` 输出 `Ran 154 tests in 53.491s OK`；`rg` 命中 `trashbot.o6.route_root_seed_gate.v1`；`git diff --check` 通过。
- O7：`cd pc-tools/workstation && npm run test && npm run build && npm run lint` 通过；Vitest 输出 `3 passed` / `475 passed`；build/lint 通过；`rg` 命中 `trashbot.o6.route_root_seed_gate.v1`；`git diff --check` 通过。

## OKR 对照

- O7 是本轮最低 active Objective，原约 44%。本轮把 O7 consumer detail 主路径推进到 route-root seed gate readiness，可展示 route-root seed status、optional `route_bag` evidence、blocked reasons、next evidence 和 false safety fields，因此保守上调到约 47%。
- O6 是 O7 的数据底座，原约 45%。本轮新增 `trashbot.o6.route_root_seed_gate.v1` 并让 O6 archive / consumer detail 可回读，因此保守上调到约 47%。
- 本轮不归档 KR，因为证据仍限于 local/mock software proof。

## 产品方向判断

方向继续。route-root seed gate 已解除 `route_bag` 硬阻塞，下一步应优先把真实或离线路线材料放进 allowlist root，补真实 `route_bag`、真实关键帧媒体、真实 annotation/export 和生产链路证据，避免继续堆叠新的只读 surface。

## 安全旗标

safe_to_control: false
delivery_success: false
primary_actions_enabled: false
robot_control_executed: false

## 剩余风险

- `software_proof_local_mock_route_root_seed_gate_only` 不证明真实 production cloud、真实 OSS/CDN、真实 TLS/4G、真实生产 DB/queue 或真实机器人数据。
- 不证明真实 `route_bag`、真实媒体可访问、真实 annotation API、真实 dataset export、真实 RTC/视频或真实 ASR/TTS。
- 不证明真实机器人运动、真实路线执行、wheel raw 非零、完整路线长期验收或 delivery success。
- O7 展示保持只读 readiness，不得据此开启 `primary_actions_enabled` 或任何真实控制闭环。
