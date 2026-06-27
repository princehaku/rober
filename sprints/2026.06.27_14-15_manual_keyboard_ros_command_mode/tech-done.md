# 2026-06-27 14:15 普通手控/键盘默认 ROS 命令模式

## sprint_type: micro

本轮目标是把普通手控、PC 键盘连续控制和 first-jog 从旧 PWM 默认切到 ROS/T=13 默认，避免普通用户路径继续撞上“上一轮 PWM 命令非零但 wheel raw L/R 仍为 0/0”的问题。PWM 和 speed 仍保留为显式诊断 override。

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - `DEFAULT_BASE_COMMAND_MODE` 从 `pwm` 改为 `ros`。
  - `ALLOWED_BASE_COMMAND_MODES` 加入 `ros`。
  - 新增 `ros_command_for_direction()`，把 forward/back/left/right/stop 映射到 WAVE ROVER vendor `T=13` 的 `X/Z` 控制。
  - `stop_commands_for_mode("ros")` 优先发送 `T=13 X=0 Z=0`，再兜底 `T=11` 和 `T=1` 停车。
  - `base_status` 的 wheel raw L/R 当前证明只接受本次 readback 或 fresh feedback artifact，stale 历史非零不再置顶为当前证明。
- `pc-tools/workstation/src/server/index.ts`
  - `POST /api/robot-control/base/manual` 和 `POST /api/robot-control/base/first-jog` 转发上车 `/api/base/manual` 时显式带 `command_mode=ros`。
- `onboard/tests/test_upper_robot_api.py`
  - 更新默认 manual/键盘 pulse 期望为 ROS/T=13。
  - 新增显式 `command_mode=pwm` 诊断 override 回归。
  - 新增 stale feedback artifact 不污染当前 base status 轮速证明回归。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 PC manual/first-jog proxy 的转发 body 期望，锁住 `command_mode=ros`。
- `docs/product/pc_tools_workstation.md`
  - 记录普通用户路径与高级诊断 override 的底盘模式边界。

## 验证结果

- `python3 -m unittest ...manual_control...`：通过，4 tests OK。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts -t "base manual proxy|first-jog proxy"`：通过，`6 passed | 120 skipped`。
- `python3 -m unittest onboard.tests.test_upper_robot_api`：首次失败 1 个旧断言，修正后通过，`Ran 64 tests ... OK`。
- `cd pc-tools/workstation && npm test`：通过两次，最终 `2 passed`，`291 passed`。
- `cd pc-tools/workstation && npm run build`：通过，Vite 仅提示 chunk size warning。
- `bash onboard/scripts/docker_humble_build.sh`：通过两次，最终 `Summary: 6 packages finished [43.4s]`。
- 上车部署验证：
  - 已同步 `onboard/scripts/upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`。
  - 远端 `python3 -m py_compile /root/rober/onboard/scripts/upper_robot_api.py` 通过。
  - 发现旧孤儿 PID `242019` 占用 `0.0.0.0:8787`，已只清理该旧 API 进程并由 systemd 接管。
  - 最终 systemd PID `247569` 监听 `0.0.0.0:8787`。
  - 只读 `/api/base/status` 已确认 `control_policy.base_command_mode=ros`、`nav2_base_command_mode=ros`、stop 顺序为 `T=13 -> T=11 -> T=1`。
  - 同一只读状态确认当前 `T=130` readback 的 `L/R=0/0` 且 `wheel_feedback_lr_nonzero_proven=false`；stale artifact 的历史非零不再污染当前证明。
  - 重启本机 PC Node 后确认 `*:7001` 监听。
- `GET http://127.0.0.1:7001/api/robot-control/summary`：
  - base 当前 `wheel_feedback_latest_left_speed=0`、`wheel_feedback_latest_right_speed=0`、`wheel_feedback_lr_nonzero_proven=false`。
  - 历史非零仍只显示在 `wheel_feedback_latest_nonzero_left_speed/right_speed=164/164`，不再当作当前证明。
  - Nav2 仍显示 `goal_succeeded_wheel_feedback_not_proven`，下一次执行模式为 `ros`。

## 剩余风险

- 本轮不主动触发真实 manual、keyboard、Nav2 或 free-roam 运动；wheel raw L/R 非零仍需要现场勾选安全确认后用 ROS 模式复验。
- ROS/T=13 的方向映射依据本地 vendor 资料和现有 ROS bridge 约定；真实运动方向仍需低速现场确认。
- 部署期间只重启上车 API 并清理旧 API 孤儿进程；没有停止雷达 lifecycle、camera service 或发送任何运动命令。
