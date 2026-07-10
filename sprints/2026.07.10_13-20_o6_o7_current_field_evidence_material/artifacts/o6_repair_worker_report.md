# O6 Repair Worker Report

run_time: 2026-07-10 13:54 CST

## 实际改动

- 修复 [`/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py) 中 `current_field_evidence_material` 的安全扫描逻辑，避免把 `nav2_no_motion_path_generated` 这类合法字段名误判成危险路径。
- 将 O6 回读 status 统一收敛为 canonical `current_field_evidence_ready_not_route_execution_proof`，同时保留旧输入 `current_field_evidence_material_ready_not_route_execution_proof` 作为 ready 兼容输入。
- 补强 [`/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py)：
  - ready fixture 断言改为 canonical O6 输出；
  - 新增 legacy ready 输入回归；
  - 保留 unsafe / dangerous true 的 fail-closed 断言。
- 同步更新 [`/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`](/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md)，明确 current-field 旧输入兼容但 O6 回读只输出 canonical status。

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 结果：通过
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - 结果：`Ran 173 tests in 70.467s OK`
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/artifacts/o6_repair_worker_report.md`
  - 结果：通过

## 失败定位

- 根因是 current-field 专用 unsafe 扫描复用了过宽的 key 规则，把 `nav2_no_motion_path_generated` 里的 `path` 误当成危险路径，导致 ready fixture 被压成 `blocked_not_proven`。
- 另一个问题是测试仍按旧 status 名断言，和 canonical O6 输出不一致。

## 剩余风险

- 这次只修了 O6 current-field 合同和本地单测，没有扩大到 O7。
- 仍然不证明真实 route execution、control success、HIL 或生产云连通；该 packet 继续按 fail-closed 语义处理。
