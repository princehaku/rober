# Free Roam Param Timeout Diagnostic

## sprint_type

micro

## 实际改动

- 修改 `onboard/scripts/upper_robot_api.py`：free-roam start/stop 写 `/free_roam_autonomy` ROS 参数时使用 `FREE_ROAM_PARAM_SET_TIMEOUT_S=2.0` 专用短超时，避免 ROS graph 或参数服务卡住时 PC 操作长时间无响应。
- 修改 `onboard/tests/test_upper_robot_api.py`：锁定 free-roam 参数序列使用短超时，并覆盖首个参数失败后停止后续参数写入，避免半启动。
- 更新 `docs/product/pc_free_roam_mapping_design.md`：校正 HTTP start/stop 的真实边界，start 只通过固定状态机参数打开运动发布双锁，不直接发布 `/cmd_vel`，且 `cmd_vel_topic` 仍不可由 PC 改写。

## 真实上位机定位

- 已部署前一轮上位机代码后，`trashbot-local-webrtc-camera.service` 与 `trashbot-upper-robot-api.service` 均恢复 `active`，8088/8787 均由 systemd 管理进程监听。
- `ros2 node list` 显示当前 ROS graph 存在重复 `learn.launch.py` 残留，`/map_recorder`、`/slam_toolbox`、`/static_laser_tf` 等节点重复。
- `ros2 param list /free_roam_autonomy` 在 6 秒内超时，`POST /api/free-roam/autonomy/start` 也会在参数写入阶段超时；这解释了“自动驾驶没法动”的一个当前软件阻塞点。
- 部署短超时修正并重启 `trashbot-upper-robot-api.service` 后，`POST /api/free-roam/autonomy/start`
  在 `2.693s` 返回 HTTP 400 结构化失败：首个参数 `operator_confirmed=true` 写入超时，
  `blocked_parameters_not_touched=["motion_hil_unlocked","enable_cmd_vel_publish","cmd_vel_topic"]`。
  因此 PC 不再长时间卡死，也不会半启动运动发布双锁。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api`：通过，`Ran 55 tests in 0.113s`，`OK`。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py`：通过。
- `git diff --check`：通过。

## 剩余风险

- 本轮修复 PC/API 卡死诊断，不等于真实自由移动已经可动；仍需清理重复 ROS runtime，恢复 `/free_roam_autonomy` 参数服务响应，再做低速 HIL。
- 当前真实上位机 `free_roam_autonomy_node` 仍以 `enable_cmd_vel_publish=false`、`motion_hil_unlocked=false` 启动；start 成功写参数后才会进入可发布状态。
