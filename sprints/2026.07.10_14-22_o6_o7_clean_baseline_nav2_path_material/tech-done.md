# O6/O7 Clean Baseline Nav2 Path Material Tech Done

## sprint_type

epic

## 实际改动

本轮主节点只做拆解、派单、验收和收口；产品代码、测试和实现验证由三个 owner worker 完成。

- Algorithm 侧新增 `trashbot.clean_baseline_nav2_path_material.v1`：
  - 新增 CLI 输入 `--clean-baseline-nav2-path-json`。
  - 支持从 `nav2_refresh_summary.json`、`nav2_retry_summary.json`、`nav2_latest_after_success.json`、`nav2_status_after_success.json`、`nav2_success_readback_summary.txt` 中安全读取 clean-baseline Nav2 no-motion path 材料。
  - 输出写入 manifest 顶层与 `field_motion_evidence_packet.clean_baseline_nav2_path_material`。
  - 固定 `proof_scope=evidence_boundary=software_proof_clean_baseline_nav2_path_material_only` 和所有 delivery/control/HIL/production flags 为 false。
- O6 侧新增 `trashbot.o6.clean_baseline_nav2_path_material.v1`：
  - 支持 field evidence、artifact bundle、archive detail、consumer detail、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest` 和 `include=clean_baseline_nav2_path_material` 回读。
  - 对 bad schema、proof scope mismatch、task mismatch、危险 true、unsafe text/raw/base64、绝对路径、URL/token、traceback/response body 做 section-local fail-closed。
- O7 侧新增 `trashbot.pc_tools_workstation.o7_clean_baseline_nav2_path_material.v1`：
  - 默认 consumer detail include 新增 `clean_baseline_nav2_path_material`。
  - adapter 从 top-level、field evidence、field motion packet、field/artifact ingest、artifact bundle 和 readiness 来源读取并 fail-closed 归一化。
  - UI 新增只读面板，展示 first failure、retry success、`path_point_count`、cleanup、blocked reasons、next required evidence 和 false flags。

## 验证结果

- Algorithm worker：
  - `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py`
  - `python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
  - `git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material/artifacts/algorithm_worker_report.md`
  - 结果：通过，`Ran 71 tests in 0.523s OK`

- O6 worker：
  - `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material/artifacts/o6_worker_report.md`
  - 结果：通过，`Ran 175 tests in 72.238s OK`

- O7 worker：
  - `cd pc-tools/workstation && npm run test && npm run build && npm run lint`
  - `git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material/artifacts/o7_worker_report.md`
  - 结果：通过，`Tests 486 passed (486)`，build 通过且仅保留既有 Vite chunk-size warning，lint 通过

- 主节点只读合同复核：
  - `rg -n "clean_baseline_nav2_path_material|software_proof_clean_baseline_nav2_path_material_only|include=clean_baseline_nav2_path_material" onboard docs pc-tools sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material`
  - 结果：命中 Algorithm、O6、O7、接口文档、产品文档和本 sprint 留档中的新增合同。

## 偏差与修复

- 角色专属子 agent 首次启动失败，错误为 `spawn_agent could not resolve the child model for service tier validation`；已按既有 SOP 改用通用 `worker` 并显式写入角色 System Prompt 后成功派发。
- 本轮没有执行新的真实上车命令；所消费材料来自既有 `2026.06.11_11-15_clean_baseline_nav2_path_refresh` sprint artifacts。

## 剩余风险

- 证据边界仍是 `software_proof_clean_baseline_nav2_path_material_only`。
- 本轮不证明真实 `NavigateToPose`、`FollowPath`、controller/BT 执行、真实 robot motion、真实 route execution、delivery record、operator confirmation、delivery success、production cloud、production DB/queue 或 WAVE ROVER HIL。
- cleanup readback 的 ready 判定依赖现有日志标记形状；若上位机 cleanup log 模板变化，需要同步扩充 parser 白名单。
