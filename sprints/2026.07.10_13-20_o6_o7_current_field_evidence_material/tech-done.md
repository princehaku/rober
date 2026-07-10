# O6/O7 Current Field Evidence Material Tech Done

## sprint_type

epic

## 实际改动

本轮没有直接改产品代码；由工程 worker 完成的可验收成果如下：

- Algorithm 侧新增 `trashbot.current_field_evidence_material.v1` 安全摘要，固定 `proof_scope=software_proof_current_field_evidence_material_only`，并把同一摘要写入 manifest 顶层与 `field_motion_evidence_packet.current_field_evidence_material`。
- O6 侧新增 `trashbot.o6.current_field_evidence_material.v1` 读回链路，支持 field evidence、artifact bundle、archive detail、consumer detail 和 `include=current_field_evidence_material`，同时保留 fixed false safety fields。
- O7 侧新增只读 consumer contract `trashbot.pc_tools_workstation.o7_current_field_evidence_material.v1`，可在 workstation 里展示 current field evidence material 的 status、present materials、blocked reasons 和 next required evidence。
- 文档与测试合同已随 worker 一并更新，且各自验证通过；O6 修复了 current-field 的 unsafe 扫描误判和 canonical status 兼容问题，O7 修复了 `catalog.test.ts` 的旧 include 断言。

## 验证结果

- Algorithm worker：
  - `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py`
  - `python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
  - `git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/artifacts/algorithm_worker_report.md`
  - 结果：通过，`Ran 48 tests in 0.236s OK`

- O6 repair worker：
  - `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/artifacts/o6_repair_worker_report.md`
  - 结果：通过，`Ran 173 tests in 70.467s OK`

- O7 test repair worker：
  - `cd pc-tools/workstation && npm run test`
  - `cd pc-tools/workstation && npm run build`
  - `cd pc-tools/workstation && npm run lint`
  - `git diff --check -- pc-tools/workstation/test/catalog.test.ts sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/artifacts/o7_test_repair_worker_report.md`
  - 结果：通过，`Tests 486 passed (486)`，build 与 lint 通过

- 本轮产品 closeout 复核：
  - `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material`
  - `rg -n "current_field_evidence_material|software_proof_current_field_evidence_material_only|2026.07.10_13-20_o6_o7_current_field_evidence_material" OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material`

## 剩余风险

- 这轮证据边界仍然只是 `software_proof_current_field_evidence_material_only`，不是真实 route execution、delivery success、HIL、production cloud 或 production DB/queue。
- O5 仍缺真实 production cloud、production DB/queue、4G/TLS 和 live endpoint evidence，不能因本轮 O6/O7 收口而上调。
- O1 仍缺真实 WAVE ROVER nonzero L/R、轮速方向、同 run HIL 准入和真实上车材料，不能因本轮 software proof 推进而上调。
- O6/O7 当前只证明 current field evidence material 的软件侧消费和回读闭环，下一轮若要继续增量，必须切到真实或准现场 route execution / delivery / production evidence。

