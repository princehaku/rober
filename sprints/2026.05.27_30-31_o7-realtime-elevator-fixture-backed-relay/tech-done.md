# O7 Realtime/Elevator Fixture-Backed Relay

## sprint_type

micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `TRASHBOT_O7_REALTIME_ELEVATOR_SNAPSHOT_JSON` runtime env。
  - `GET /api/o7/realtime-elevator/snapshot` 只读取 env 指向的本机 `trashbot.o7.realtime_elevator_fixture.v1` fixture，不接受 query 任意路径。
  - 安全 fixture 可生成 `map_ref`、`map_frame`、`robot_pose`、`pose_freshness`、`route_membership`、`elevator_state_chain.samples`、`current_floor_evidence`、`human_takeover` 只读摘要。
  - 坏 JSON、unsupported schema、凭证/`/cmd_vel`/串口/traceback、success/control、真实 realtime API、真实 `/tf`、latency/elevator/floor/takeover proven 或 route membership true 声明均 fail closed。
  - 所有真实实时、`/tf`、电梯、楼层、接管、控制和成功字段继续固定 false。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 覆盖未配置仍空、safe fixture 非空但危险字段 false、不安全 fixture blocked、坏数值安全降级。
- `docs/interfaces/o7_realtime_operator_console.md`、`pc-tools/README.md`、`cloud-relay/README.md`
  - 更新 env fixture-backed realtime/elevator relay contract 的使用边界和 fail-closed 风险。

## 验证结果

- `cd onboard && python3 -m pytest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k "o7_realtime_elevator"`
  - 结果：通过，`4 passed, 108 deselected in 2.38s`。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o7_realtime_operator_console.md pc-tools/README.md cloud-relay/README.md sprints/2026.05.27_30-31_o7-realtime-elevator-fixture-backed-relay`
  - 结果：通过，无输出。
- `python3 -m compileall -q onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 结果：通过，无输出。

## 剩余风险

- 本轮只推进 cloud relay runtime 上的本机 fixture 摘要，不打通真实 RTC/视频、真实 ROS2 `/tf`、真实电梯设备、真实楼层识别、真实手控/寻路、机器人 ACK 或硬件 HIL。
- `cloud_runtime_fixture_connected=true` 只表示 relay 读取到安全 fixture 并生成摘要，不表示真实 realtime API connected。
