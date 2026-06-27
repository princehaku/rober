# Free Move Start 与建图 Gate 分层

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - free-roam start 改为优先判断 `free_move_ready`，避免旧形态里 `ready=false` 被误解释成自由移动不可启动。
  - start 回包新增 `free_move_start_ready`、`free_move_blocked_reasons`、`mapping_readiness_ready`、`mapping_blocked_reasons`。
  - 相机 readiness 注释改为建图验收语义，明确相机首帧不是自由移动硬门禁。
- `onboard/tests/test_upper_robot_api.py`
  - 旧“camera not ready 阻止 start”测试改为“camera not ready 只降级 mapping_active，自由移动仍启动”。
- `onboard/scripts/test_upper_robot_api_free_roam.py`
  - 新增旧调用兼容测试：`ready=false` 但 `free_move_ready=true` 时仍必须启动自由移动。
- `pc-tools/workstation/src/server/index.ts`
  - PC free-roam start 代理透传上车端自由移动/建图验收分层短字段。
- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlFreeRoamAutonomyResponse` 增加分层短字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - free-roam fallback 响应补齐分层字段。
- `pc-tools/workstation/test/catalog.test.ts`
  - 固定默认小车 free-roam start 代理测试覆盖 `free_move_start_ready=true`、`mapping_readiness_ready=false` 和建图缺口透传。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录自由移动 start 与建图验收 gate 的产品合同。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api onboard.scripts.test_upper_robot_api_free_roam`
  - 通过：72 tests。
- `npm test -- --testNamePattern "fixed POST proxies|free-roam|Free Roam" --maxWorkers=1 --no-fileParallelism`
  - 通过：33 passed, 297 skipped。
- `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 通过：330 passed。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；仍有既有 Vite chunk size warning。
- `git diff --check`
  - 通过。
- `HOST=0.0.0.0 PORT=7001 npm run api:public`
  - 已重新启动，`node` 监听 `*:7001`。
- `curl -sS --max-time 5 http://127.0.0.1:7001/api/robot-control/summary`
  - 只读复验通过：`safe_command_boundary.free_roam_autonomy=start_ready`。
  - 只读复验通过：`free_roam_autonomy_start_ready=true`、`free_roam_motion_start_ready=true`。
  - 只读复验通过：`free_roam_mapping_ready=false`，缺口为 `camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`。
  - 只读复验通过：runtime 当前仍为 `decision_state=stopping`、`artifact_only=true`、`cmd_vel_publish_enabled=false`，说明尚未现场点击 start。

## 剩余风险

- 本轮不发真实 start/stop/manual/Nav2/free-roam 或 `/cmd_vel`，只验证软件合同。
- 真实车是否移动仍取决于现场点击 start 后 ROS 参数服务是否成功写入，以及上车 `free_roam_autonomy_node` 是否运行。
- 当前摄像头首帧和雷达状态仍可能阻止“可验收建图”收口，但不应阻止低速自由移动入口。
