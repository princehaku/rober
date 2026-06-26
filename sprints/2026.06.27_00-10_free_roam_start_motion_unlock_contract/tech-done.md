# 自动扫图 start 运动双锁合同修正

## Sprint 类型

sprint_type: micro

## 实际改动

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`：
  - `free_roam_autonomy_start()` 在 `confirm_operator_safety=true` 且参数服务成功时，同时设置 `enable_cmd_vel_publish=true` 与 `motion_hil_unlocked=true`。
  - `free_roam_autonomy_stop()` 收回 `enable_cmd_vel_publish=false` 与 `motion_hil_unlocked=false`，并设置 `external_stop_requested=true`。
  - 回包按成功/失败区分 `motion_unlock_requested` 和 `blocked_parameters_not_touched`，避免 PC 误判是否真的打开过上车状态机运动双锁。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py` 与 `test_operator_gateway_static.py`：
  - 锁定 HTTP fake gateway 与真实源码合同一致：start 成功请求运动解锁，但不直接发布 `/cmd_vel`，也不允许改 `cmd_vel_topic`。
- 新增 `onboard/scripts/test_upper_robot_api_free_roam.py`：
  - 锁定 8787 实际入口的 free-roam 合同：相机/雷达不 ready 时仍请求低速自由移动双锁，`mapping_active_applied=false` 表示本轮不能按可验收建图收口。
- 更新 `docs/product/pc_free_roam_mapping_design.md`：
  - 明确 launch 默认 artifact-only，PC start 在安全确认后临时打开双锁，stop 收回双锁；相机/雷达 readiness 只影响建图验收，不阻止自由移动。

## 验证结果

- `python3 onboard/scripts/test_upper_robot_api_free_roam.py`：通过，1 test。
- `python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`：通过，60 tests。
- `python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`：通过，11 tests。
- `python3 onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py && python3 onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy_node.py`：通过，10 + 5 tests。
- `cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "free-roam|free roam|autonomy|自动扫图"`：通过，5 tests。
- `cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "free-roam|free roam|自动扫图|扫图"`：通过，19 tests。
- `cd pc-tools/workstation && npm run build`：通过，保留既有 Vite chunk size warning。
- `bash onboard/scripts/docker_humble_build.sh`：通过，`Summary: 6 packages finished [42.9s]`。
- live 只读/安全 smoke：SSH 到 `192.168.1.11:37878` 成功；`POST /api/free-roam/autonomy/start` 在 `confirm_operator_safety=false` 时返回 `blocked_missing_confirmation`，未写运动参数、未发运动。

## 剩余风险

- 本轮没有在真车上发送 `confirm_operator_safety=true` 的自动扫图 start，因此没有实际发布非零 `/cmd_vel` 或证明 wheel raw L/R 非零。
- live 8787 当前由 `onboard/scripts/upper_robot_api.py` 提供；该脚本已具备安全确认后打开 free-roam 双锁的路径。ROS `operator_gateway.py` 的合同漂移已修，但现场服务若切换到该节点仍需重新部署/重启后才生效。
- 摄像头 `/dev/video1` 仍是首帧不可读；雷达 lifecycle 当前 stopped。两者不阻止自由移动，但仍阻止“可验收建图”结论。
