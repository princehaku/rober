# O6/O7 Route Root Seed Gate Tech Done

## sprint_type: epic

## 本轮核心抓手

本轮面向最低 active Objective O7，并由 O6 数据合同支撑，解决 route-root seed 对 `route_bag` gate 的硬依赖。产品判断是：local/mock route root 已具备 `route.csv`、manifest 和 derived replay 时，应允许形成可回读、可展示、可复验的 seed readiness 摘要；`route_bag` 继续作为增强证据和 next evidence，而不是阻断 `gate_pass=true`。

证据边界统一记录为 `software_proof_local_mock_route_root_seed_gate_only`。本轮不声明真实生产云、真实 `route_bag`、真实媒体、真实 annotation API、真实 dataset export、真实机器人运动或 delivery success。

## 实际改动

### robot-algorithm-engineer

- 修改 `onboard/scripts/field_route_evidence_manifest.py`。
- 修改 `docs/navigation/field_route_evidence_manifest.md`。
- route-root 输入在显式 route root + replay 场景下把 `rosbag/route_bag` 视为可选增强证据，不再阻断 `gate_pass=true`。
- manifest 暴露 `route_root_seed_gate`、`route_bag_required=false`、`route_bag_present=false`、`frame_count=2`，并保持所有安全旗标 false。

### robot-software-engineer

- 修改 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`。
- 修改 `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`。
- 修改 `docs/interfaces/o6_cloud_archive_api.md`。
- 新增 additive 摘要 `trashbot.o6.route_root_seed_gate.v1`，挂到 archive detail、field evidence consumer ingest、artifact bundle alias 和 O6 consumer detail。
- 缺 `route_bag` 时输出 `route_bag_required=false`、`route_bag_present=false`、`route_bag_missing_optional`、`route_bag_optional_evidence`，但 route.csv + manifest + derived replay 可用时 `route_root_seed_status=local_mock_route_root_seed_ready`。

### full-stack-software-engineer

- 修改 `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`。
- 修改 `pc-tools/workstation/src/shared/contracts.ts`。
- 修改 `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`。
- 修改 `pc-tools/workstation/test/catalog.test.ts`。
- 修改 `pc-tools/workstation/test/App.test.ts`。
- 修改 `docs/product/pc_tools_workstation.md`。
- O7 consumer detail 请求并展示 `trashbot.o6.route_root_seed_gate.v1`，显示 route-root seed status、`route_bag_required=false`、`route_bag_present=false`、counts、blocked reasons、next evidence 和 false safety fields。
- dangerous true、unsafe refs、schema mismatch 继续 fail-closed。

### product-okr-owner

- 创建本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`，将 O7/O6 保守上调到约 47%，并明确证据边界为 `software_proof_local_mock_route_root_seed_gate_only`。

## 验证结果

### Algorithm 验证

- `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py`：通过。
- route-root fixture smoke：输出 `gate_pass=true`。
- `rg` 关键 token 检查：命中 `route_root_seed_gate`、`route_bag_required=false`、`route_bag_present=false`。
- `git diff --check`：通过。

### O6 验证

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`：通过。
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`：`Ran 154 tests in 53.491s OK`。
- `rg` 关键 token 检查：命中 `trashbot.o6.route_root_seed_gate.v1`、`route_bag_missing_optional`、`route_bag_optional_evidence`、`local_mock_route_root_seed_ready`。
- `git diff --check`：通过。

### O7 验证

- `cd pc-tools/workstation && npm run test && npm run build && npm run lint`：通过。
- Vitest 输出覆盖 `3 passed` / `475 passed`。
- build：通过。
- lint：通过。
- `rg` 关键 token 检查：命中 `trashbot.o6.route_root_seed_gate.v1`、route-root seed status、`route_bag_required=false`、`route_bag_present=false` 和 fail-closed safety 字段。
- `git diff --check`：通过。

## 安全旗标

safe_to_control: false
delivery_success: false
primary_actions_enabled: false
robot_control_executed: false

## OKR 映射和方向判断

- 用户价值和产品北极星：O7 运营调试平台可以用本地/mock route root 稳定验证历史路线回放、标注和训练数据入口，不再因 `route_bag` 缺失停滞；这继续服务“可验证地可靠交付垃圾”的数据复盘链路。
- O7：从约 44% 保守上调到约 47%。理由是 O7 已消费 `trashbot.o6.route_root_seed_gate.v1` 并能展示 readiness、blocked reasons 和 false safety fields，测试达到 `475 passed`。
- O6：从约 45% 保守上调到约 47%。理由是 O6 archive / consumer detail 已新增 additive route-root seed gate 摘要，并在缺 `route_bag` 时保持 route-root seed ready。
- 方向判断：继续。下一步应把真实或离线 `route.csv`、keyframe、replay JSONL、真实 `route_bag` 或真实媒体逐步接入 allowlist root 与生产链路，而不是再堆叠新的只读 wrapper。
- KR 状态：不归档 O6/O7 KR。当前仍只是 local/mock software proof。

## 剩余风险

- `software_proof_local_mock_route_root_seed_gate_only` 不证明真实生产云、production DB/queue、OSS/CDN、TLS/4G 或真实长期数据回灌。
- 本轮不证明真实 `route_bag` 存在、可读或可回放；`route_bag` 只是可选增强证据，仍需后续补齐。
- 本轮不证明真实关键帧媒体、真实 annotation API、真实 dataset export、真实 RTC/视频或真实 ASR/TTS。
- 本轮不证明真实机器人运动、真实路线执行、wheel raw 非零、完整路线长期验收或 delivery success。
- 所有安全旗标保持 false，不允许据此开启控制面主动作或用户可执行发车闭环。
