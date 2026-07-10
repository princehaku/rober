# Algorithm Worker Report

## 变更

- 更新 [`/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py`](</Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py>)，新增 `trashbot.route_bag_pose_progress_replay.v1` 和 `software_proof_route_bag_pose_progress_replay_only`。
- 新增只读 DB3 位姿进度摘要链路，优先支持 `tf2_msgs/msg/TFMessage` 的 transform translation，低风险兼容 `nav_msgs/msg/Odometry`。
- 顶层 manifest 与 `field_motion_evidence_packet.route_bag_pose_progress_replay` 同步写入，保留 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`live_nav2_run_proven=false`、`route_execution_success=false`。
- 更新 [`/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py`](</Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py>)，补齐 ready、missing input、decode failure、unsafe topic fail-closed 和 nested packet 断言。
- 更新 [`/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md`](</Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md>)，补充新 contract、输出字段和 gate 语义说明。

## 验证

执行命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

结果：

- `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py` 通过。
- `python3 -m unittest onboard.tests.test_field_route_evidence_manifest` 通过，`Ran 41 tests in 0.192s`，`OK`。

## 失败定位

- 首轮 ready case 失败在 pose progress 位移被算成 0。
- 根因是测试 fixture 的 TF/Odometry CDR 打包没有按字符串后的整体 8 字节边界补齐，导致解码读偏。
- 已修正为在 `child_frame_id` 后按当前 payload 长度补齐到 8 字节边界，再重新验证通过。

## 剩余风险

- 这条链路仍然只证明 software proof，不证明真实 live Nav2、真实底盘运动、真实 delivery success。
- 目前只覆盖 `TFMessage` 和 `Odometry` 的安全摘要，其他 ROS 消息类型仍会被 fail closed。
- `route_bag_pose_progress_replay` 现在可稳定回读，但仍需要后续 O6/O7 消费端把这个 section 接到可视化和归档链路里。
