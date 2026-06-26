# Free Roam Param Timeout Diagnostic

## sprint_type

micro

## 实际改动

- 修改 `onboard/scripts/upper_robot_api.py`：free-roam start/stop 写 `/free_roam_autonomy` ROS 参数时改为一次固定 `ros2 param load` 临时 YAML，使用 `FREE_ROAM_PARAM_LOAD_TIMEOUT_S=10.0` 专用超时，避免 5-6 个 `ros2 param set` CLI 串行启动拖慢 PC 操作。
- 修改 `onboard/tests/test_upper_robot_api.py`：锁定 free-roam 参数序列只启动一次固定 `ros2 param load`，并覆盖参数 load 失败时不声明任何参数已写入，避免半启动。
- 更新 `docs/product/pc_free_roam_mapping_design.md`：校正 HTTP start/stop 的真实边界，start 只通过固定状态机参数打开运动发布双锁，不直接发布 `/cmd_vel`，且 `cmd_vel_topic` 仍不可由 PC 改写。

## 真实上位机定位

- 已部署前一轮上位机代码后，`trashbot-local-webrtc-camera.service` 与 `trashbot-upper-robot-api.service` 均恢复 `active`，8088/8787 均由 systemd 管理进程监听。
- `ros2 node list` 显示当前 ROS graph 存在重复 `learn.launch.py` 残留，`/map_recorder`、`/slam_toolbox`、`/static_laser_tf` 等节点重复。
- `ros2 param list /free_roam_autonomy` 在 6 秒内超时，`POST /api/free-roam/autonomy/start` 也会在参数写入阶段超时；这解释了“自动驾驶没法动”的一个当前软件阻塞点。
- 第一版 2 秒短超时部署并重启 `trashbot-upper-robot-api.service` 后，`POST /api/free-roam/autonomy/start`
  在 `2.693s` 返回 HTTP 400 结构化失败：首个参数 `operator_confirmed=true` 写入超时，
  `blocked_parameters_not_touched=["motion_hil_unlocked","enable_cmd_vel_publish","cmd_vel_topic"]`。
  因此 PC 不再长时间卡死，也不会半启动运动发布双锁。
- 随后直接在上位机 shell 执行 `ros2 param get/set /free_roam_autonomy enable_cmd_vel_publish` 均成功，
  说明节点参数服务可恢复；单次 `ros2 param set` 约需 7 秒，不适合 start/stop 串行写 5-6 个参数。
- 已在上位机验证临时 YAML `ros2 param load /free_roam_autonomy <file>` 可一次写入 stop 的 5 个参数，
  输出 5 行 `Set parameter ... successful`，耗时约 `real 0m3.438s`。最终方案因此改为一次 `param load`。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api`：通过，`Ran 55 tests in 0.103s`，`OK`。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py`：通过。
- `git diff --check`：通过。
- 部署最终 `param load` 版本到真实上位机并重启 `trashbot-upper-robot-api.service` 后，
  `POST /api/free-roam/autonomy/stop` 返回 HTTP 200，`TOTAL_TIME=4.888967s`；
  `command_result.results[0].write_strategy=ros2_param_load`，stdout 显示
  `enable_cmd_vel_publish/motion_hil_unlocked/external_stop_requested/mapping_active/operator_confirmed`
  5 个参数均 `Set parameter ... successful`，`blocked_parameters_not_touched=["cmd_vel_topic"]`。

## 剩余风险

- 本轮修复 PC/API start/stop 参数写入链路和 stop 收口验证，不等于已经远程发 start 让车真实自由移动；start 会打开运动发布双锁，仍需现场人员确认周边安全后做低速 HIL。
- 当前真实上位机仍有重复 `learn.launch.py`/`map_recorder`/`slam_toolbox` 残留，后续应做 runtime 清理，避免 ROS graph 再次抖动。
