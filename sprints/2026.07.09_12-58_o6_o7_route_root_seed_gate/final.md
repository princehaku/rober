# O6/O7 Route Root Seed Gate Final

## sprint_type: epic

## 阶段收口

本 sprint 收口为完成。route-root seed 已从 `route_bag` gate 的硬依赖中解耦：显式 route root + replay 场景下，`route_bag` 缺失不再阻断 route-root seed local/mock smoke，O6/O7 可围绕同一 `task_id` 回读和展示 `trashbot.o6.route_root_seed_gate.v1` readiness。

证据边界：`software_proof_local_mock_route_root_seed_gate_only`。

## 实际改动

- Algorithm：更新 `onboard/scripts/field_route_evidence_manifest.py` 和 `docs/navigation/field_route_evidence_manifest.md`，让 route-root fixture 输出 `gate_pass=true`，并暴露 `route_root_seed_gate`、`route_bag_required=false`、`route_bag_present=false`、`frame_count=2`。
- O6：更新 `remote_cloud_relay.py`、`test_remote_cloud_relay.py` 和 `docs/interfaces/o6_cloud_archive_api.md`，新增 additive `trashbot.o6.route_root_seed_gate.v1` 摘要；缺 `route_bag` 时输出 `route_bag_missing_optional` / `route_bag_optional_evidence`，但 route.csv + manifest + derived replay 可用时 `route_root_seed_status=local_mock_route_root_seed_ready`。
- O7：更新 `o7ConsumerReadAdapter.ts`、`contracts.ts`、`O7FixturePreviewPanel.vue`、`catalog.test.ts`、`App.test.ts` 和 `docs/product/pc_tools_workstation.md`，请求并展示 O6 route-root seed gate 摘要，保留 dangerous true / unsafe refs / schema mismatch fail-closed。
- Product：创建 `tech-done.md`、`side2side_check.md`、`final.md`，并更新 `OKR.md`、`docs/process/okr_progress_log.md`。

## 验证结果

- Algorithm：py_compile 通过；route-root fixture 输出 `gate_pass=true`；`rg` 命中关键 token；`git diff --check` 通过。
- O6：py_compile 通过；`python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` 输出 `Ran 154 tests in 53.491s OK`；`rg` 命中关键 token；`git diff --check` 通过。
- O7：`cd pc-tools/workstation && npm run test && npm run build && npm run lint` 通过；Vitest `3 passed` / `475 passed`；build/lint 通过；`rg` 命中关键 token；`git diff --check` 通过。

## OKR 进展

- O7：约 44% -> 约 47%。上调理由是最低 active Objective 已新增 route-root seed readiness 消费和展示能力，且测试达到 `475 passed`；但仍只是 local/mock software proof，不归档 KR3/KR4。
- O6：约 45% -> 约 47%。上调理由是 O6 archive / consumer detail 新增 `trashbot.o6.route_root_seed_gate.v1` 并解除 `route_bag` 硬阻塞；但仍未接入真实生产云、真实 `route_bag` 或真实长期数据回灌。
- O1/O5/O2/O3/O4：本轮不调整。
- 方向判断：继续推进 O6/O7，但下一步必须消费真实或离线路线材料、真实 `route_bag`、真实媒体或生产链路证据，不能只叠加新的 local/mock wrapper。

## 安全旗标

safe_to_control: false
delivery_success: false
primary_actions_enabled: false
robot_control_executed: false

## 未完成事项和风险

- 不证明真实生产云、production DB/queue、OSS/CDN、TLS/4G、真实隧道或真实机器人数据。
- 不证明真实 `route_bag`、真实媒体可访问、真实 annotation API、真实 dataset export、真实 RTC/视频或真实 ASR/TTS。
- 不证明真实机器人运动、真实路线执行、wheel raw 非零、完整路线长期验收或 delivery success。
- O7 只展示只读 readiness 和 blocked reasons；不能据此打开控制面主动作或真实用户发车闭环。

## KR 历史归档判断

本轮不归档任何 O6/O7 KR。`trashbot.o6.route_root_seed_gate.v1` 和 O7 展示能力提升了 O6 KR2/KR6 与 O7 KR3/KR4 的软件侧证据，但缺少真实生产云、真实媒体、真实 route_bag、真实 annotation/export 和真实路线长期验收，不能标为完成。
