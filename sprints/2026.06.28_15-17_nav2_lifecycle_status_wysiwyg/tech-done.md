# 2026.06.28 15:17 Nav2 Lifecycle Status WYSIWYG

## sprint_type

micro

## 实际改动

- 上车端 `onboard/scripts/upper_robot_api.py` 新增只读 `ROBER_NAV2_STATUS_COMMAND`，`/api/nav2/status` 现在读取 `o11_nav2_lifecycle.sh status` 并返回 `lifecycle_manager.running/state`、`lifecycle_running`、`lifecycle_state`。
- 上车端 `onboard/scripts/o11_nav2_lifecycle.sh` 修复 stale running：`ros2 launch` 退出后会写 `failed/stopped`，`status` 发现 pid 不存在时会覆盖旧 running 文件。
- PC summary `pc-tools/workstation/src/server/robotControlSummary.ts` 消费明确的 Nav2 lifecycle manager 状态；只有读到 `lifecycle_running=false` 时，才把普通首屏 blockers 首项标为 `nav2_stack_not_running`，并提示“先启动 Nav2 服务（不发车）”。
- Nav2 最近路线执行摘要新增 `goal_execution_base_feedback_latest_raw_left/right`，和底盘 `wheel_feedback_latest_raw_left/right` 同口径，便于排查 action succeeded 但 wheel raw L/R 仍为 `0/0` 的场景。
- 真车只读排查发现 `autonomous_nav2_stack_only.log` 原始失败为 `package 'nav2_bringup' not found`；已在车上安装 `ros-humble-navigation2` 与 `ros-humble-nav2-bringup`，并验证 `ros2 pkg prefix nav2_bringup`、`ros2 pkg prefix navigation2` 均指向 `/opt/ros/humble`。
- 同步更新 `pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/test/catalog.test.ts`、`onboard/tests/test_upper_robot_api.py`、`onboard/tests/test_o11_nav2_lifecycle_script.py` 和 `docs/product/pc_free_roam_mapping_design.md`。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_status_defaults_to_managed_lifecycle_commands onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_lifecycle_status_parse_failure_is_not_stopped onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_control_uses_default_managed_lifecycle_command` 通过。
- `bash -n onboard/scripts/o11_nav2_lifecycle.sh && python3 -m unittest onboard.tests.test_o11_nav2_lifecycle_script onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_lifecycle_status_parses_stdout_preview` 通过。
- `npm test -- test/catalog.test.ts -t 'stopped Nav2 stack|Nav2 IMU motion material|proxies Robot API readback endpoints'` 通过。
- `npm test` 通过，334 passed。
- `npm run lint` 通过。
- `npm run build` 通过。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py` 通过。
- `bash onboard/scripts/docker_humble_build.sh` 通过，Docker/Humble `colcon build --symlink-install` 输出 `Summary: 6 packages finished [43.4s]`。
- 本轮 SSH 只读确认：上车 ROS graph 当前只有 `/esp32_bridge`、`/free_roam_autonomy` 和静态 TF；`/planner_server`、`/controller_server`、`/bt_navigator`、`/map_server`、`/amcl` 未启动。摄像头 `/dev/video1` 无其他 holder，占用问题不成立，当前根因是 UVC 无首帧。
- 部署后 live 只读确认：`/api/nav2/status` 返回 `lifecycle_running=false/lifecycle_state=stopped`；PC `0.0.0.0:7001` summary 显示 `nav2_stack_not_running`，下一步为“先启动 Nav2 服务（不发车）”。摄像头仍为 `source_first_frame_failed/uvc_no_frame_not_exclusive`，自由移动 `free_roam_motion_start_ready=true`，建图验收仍缺 `camera_first_frame/lidar_fresh/mapping_active/fresh_map_preview`。
- 真车依赖验证：`ros2 pkg prefix nav2_bringup` 与 `ros2 pkg prefix navigation2` 均返回 `/opt/ros/humble`。

## 剩余风险

- 本轮未执行 Nav2 start、goal execute、free-roam start、manual 或 `/cmd_vel`，因此没有真实运动/HIL 通过结论；Nav2 依赖已补齐，但需要现场安全确认后再启动 stack 验证 planner/controller。
- 摄像头仍未输出首帧，根因不是页面独占；需要检查 USB/输入/供电或换 known-good UVC。
