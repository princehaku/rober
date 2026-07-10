# O6/O7 Route Bag Odometry Semantic Decoder Tech Done

## Sprint 类型

sprint_type: epic

收口时间：2026-07-09 23:27 CST。

## 实际改动

### Algorithm

- `onboard/scripts/field_route_evidence_manifest.py`
  - `nav_msgs/msg/Odometry` 纳入 `route_bag_semantic_replay` 白名单。
  - 新增 `decode_odometry_payload`，复用已有 Odometry CDR 位姿解析，只输出 frame pair 与平移安全摘要。
  - `route_bag_full_semantic_decode_matrix` 的 Odometry item 现在可输出 `status=decoded` 和 `decoder_name=decode_odometry_payload`。
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 增加 semantic replay 和 full semantic matrix 的 `/odom` fixture 覆盖。
  - 验证 Odometry decoded 后仍保持 false safety fields。
- `docs/navigation/field_route_evidence_manifest.md`
  - 记录 Odometry decoder、`odometry_summary` 与本地/离线 proof 边界。

### O6

- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 更新 O6 fixture，证明 `nav_msgs.msg.Odometry` 可在 semantic replay topic list 中安全回读。
  - 更新 full semantic matrix fixture，证明 Odometry decoded item 保留 `decoder=decode_odometry_payload`、counts、coverage ratio 与 false safety fields。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 记录 O6 对 Odometry semantic replay 与 matrix item 的安全归一和回读口径。
- `remote_cloud_relay.py` 未改动；现有 O6 归一逻辑已能安全透传该 matrix item，本轮补齐证明。

### O7

- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
  - 更新 consumer/UI fixture 和断言：`semantic_topic_types` 包含 `nav_msgs/msg/Odometry`，`/odom` matrix item 为 `decode_status=decoded`、`decoder_name=decode_odometry_payload`，`coverage_ratio=0.75`。
  - 验证不再出现 `route_bag_full_semantic_decode_matrix_failed_types_present`。
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 更新注释和页面提示口径：semantic replay / full semantic decode matrix 已包含 Odometry，但只表示 local/offline semantic coverage。
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
  - 同步 O7 product/docs 边界。

## 验证结果

- Algorithm：`python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
  - 结果：`Ran 48 tests in 0.275s`，`OK`
- O6：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - 结果：`Ran 163 tests in 60.247s`，`OK`
- O7：`cd pc-tools/workstation && npm run test && npm run build && npm run lint`
  - 结果：`Tests 482 passed (482)`，build 通过，lint 通过

## 偏差与修复

- Algorithm 首轮新增断言把 Odometry translation 预期写成非零；worker 复核后确认当前最小 fixture 可证明的是 decoder 成功和安全摘要接线，不证明真实平移精度，已把断言收紧到当前 decoder 可证明的安全输出。
- O6 首轮测试断言仍停留在 Odometry 接入前的旧 counts / coverage ratio；worker 更新 fixture 与断言后复验通过。
- O7 验收命令一次通过。

## 剩余风险

- 本轮只证明 Odometry semantic decoder 的 local/offline software proof 已被 Algorithm、O6、O7 消费。
- 不证明真实 production cloud、真实 4G/TLS、production DB/queue、真实 OSS/CDN 或生产级查询容量。
- 不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success 或完整路线长期验收。
- matrix 中仍有 unsupported topic type，raw ROS message payload 仍不是全量语义回放。
