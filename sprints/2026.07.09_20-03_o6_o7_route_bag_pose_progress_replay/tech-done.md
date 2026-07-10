# O6/O7 Route Bag Pose Progress Replay Tech Done

## Sprint 类型

sprint_type: epic

收口时间：2026-07-09 20:52 CST。

## 实际改动

Algorithm：

- `onboard/scripts/field_route_evidence_manifest.py` 新增 `trashbot.route_bag_pose_progress_replay.v1` 与 `software_proof_route_bag_pose_progress_replay_only`。
- `onboard/tests/test_field_route_evidence_manifest.py` 补 ready、missing、decode failure、unsafe topic/text 和 nested packet 测试。
- `docs/navigation/field_route_evidence_manifest.md` 同步描述 route bag pose progress replay 合同。

O6：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 新增 `trashbot.o6.route_bag_pose_progress_replay.v1` sanitizer/readback/include 链路。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` 覆盖 field evidence、artifact bundle、consumer detail、explicit include 和 unsafe fail-closed。
- `docs/interfaces/o6_cloud_archive_api.md` 同步 O6 archive/readback 合同。

O7：

- `pc-tools/workstation/src/shared/contracts.ts` 新增 `O7ConsumerRouteBagPoseProgressReplaySummary`。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts` 增加多入口归一化与 fail-closed。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 增加只读 pose progress 区块。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts` 更新 include、blocked summary 和 UI 断言。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md` 同步 O7 consumer 说明。

Product 收口：

- `OKR.md`、`docs/process/okr_progress_log.md` 更新 O6/O7 进度和证据边界。

## 验证结果

Algorithm owner：

```text
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
Ran 41 tests in 0.192s
OK
```

O6 owner：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
Ran 161 tests in 57.594s
OK
```

O7 owner：

```text
cd pc-tools/workstation && npm run test && npm run build && npm run lint
479 tests passed
build passed
lint passed
```

O7 build 仅保留既有 Vite chunk size warning，不影响本轮验收。

## 偏差和修复

- Algorithm 首轮 ready case 位移为 0，根因是 TF/Odometry fixture 的 CDR 对齐缺 8 字节补齐；worker 已修复并复验通过。
- O6 首轮 HTTP 回包裁掉 `pose_topic_types`，根因是通用 `safe_value()` 把含 `topic` 字段名误判为敏感；worker 已加入安全例外并复验通过。
- O7 首轮遇到 include 列表、blocked summary 和 TypeScript 类型/重复字段问题；worker 已修复并完成 test/build/lint。

## 剩余风险

- 本轮只证明 `software_proof_route_bag_pose_progress_replay_only`，不证明真实 production cloud、真实 4G/TLS、production DB/queue、真实 OSS/CDN、真实机器人数据或生产级查询容量。
- 不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success 或完整路线长期验收。
- 不证明 raw ROS message payload 全量语义解析；当前 Algorithm 只覆盖 TFMessage 与 Odometry 的安全摘要，其他消息类型 fail closed。
