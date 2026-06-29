# Free Roam Start Runtime Wait

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - `POST /api/free-roam/autonomy/start` 在真实 `ros2 param load` 成功后，会短等 `free_roam_autonomy_latest` artifact 刷新到运行态。
  - 新增 `start_runtime_wait` 回包，记录是否等待、是否看到 `running/avoiding/turning_for_coverage`、是否看到 `cmd_vel_publish_enabled=true`。
  - mock/fake 响应不会等待，避免测试和非真实路径被拖慢。
- `pc-tools/workstation/src/server/index.ts`
  - PC free-roam start 代理透传 `start_runtime_wait` 和 `latest_cmd_vel_publish_enabled`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏自由移动状态机写入提示会显示“运行态已看到/运行态还未回读”。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 free-roam start 代理合同字段。
- `onboard/scripts/test_upper_robot_api_free_roam.py`
  - 新增单测覆盖真实 param load 成功后等待 runtime artifact 的行为。

## 验证结果

- 本地：`python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api_free_roam.py` 通过。
- 本地：`python3 -m unittest onboard.scripts.test_upper_robot_api_free_roam`，4 tests OK。
- 本地：`python3 -m unittest onboard.tests.test_upper_robot_api`，88 tests OK，1 skipped。
- 本地：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.tests.test_camera_first_frame_probe`，45 tests OK。
- PC：`npm run build` 通过。
- PC：`npm test -- --run`，386 tests OK。
- 真实上位机：已同步 `/root/rober/onboard/scripts/upper_robot_api.py` 并重启 8787，`0.0.0.0:8787` 由新 `upper_robot_api.py` 监听。
- 真实只读验证：`GET /api/free-roam/autonomy/latest` 返回 `decision_state=stopping`、`cmd_vel_publish_enabled=false`、`free_move_start_ready=true`、`motion_without_radar_allowed=true`、`robot_control_executed=false`。
- PC 只读验证：`GET /api/robot-control/summary` 返回 `free_roam_status=start_ready`、`decision_state=stopping`、`cmd_vel_publish_enabled=false`、`free_move_start_ready=true`。

## 剩余风险

- 本轮没有触发 `POST /api/free-roam/autonomy/start`，没有发送 manual、keyboard、Nav2 goal、delivery、stop 或 `/cmd_vel`，因此未证明真实轮子已开始自由移动。
- 新 `start_runtime_wait` 只有在现场勾选安全确认并真正点击自由移动 start 后才会产生运行态结果；若 ROS 节点 tick、param load 或 runtime artifact 仍异常，PC 会显示“运行态还未回读”。
- 建图仍被相机首帧阻塞；自由移动不受相机/雷达阻塞。
