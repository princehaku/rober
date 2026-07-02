# 2026.07.03 06:55 WAVE ROVER main type 与命令链路诊断

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py`：按本地 vendor 资料增加 `T=900` 主机型配置，默认 `main=1,module=0`，启动配置顺序调整为 `T=900 -> T=143 -> T=142 -> T=131`。
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py`、`esp32_bridge_node.py`、`esp32_bridge.py`、`hardware_diagnostics_proof.py`：新增 `main_type/module_type` 参数、校验、诊断 proof 输出和启动配置 debug JSONL。
- `onboard/scripts/upper_robot_api.py`：汇总 `wave_rover_command_debug.jsonl`，在 `/api/base/status` 暴露命令链路、非零命令计数、最新命令和 WAVE ROVER main/module 启动配置状态。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、`pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：PC summary 和普通界面显示“命令已到 bridge/UART，但 wheel raw 仍未非零”的明确诊断，不把命令链路误写成 wheel 反馈成功。
- `docs/product/pc_tools_workstation.md`：同步记录本轮新边界和 vendor 资料来源。

## 验证结果

- `python3 -m py_compile onboard/scripts/upper_robot_api.py ... hardware_diagnostics_proof.py`：通过。
- `python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py onboard/src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py`：`Ran 39 tests ... OK`。
- `npm run build`：通过，Vite 仅保留既有 chunk size warning。
- `npm test -- --run test/App.test.ts test/robotControlSummary.test.ts test/catalog.test.ts`：`3 passed (3)`、`433 passed (433)`。
- `git diff --check`：通过。
- 已部署到上位机并重启 `esp32_bridge`：ROS 参数读回 `main_type=1`、`module_type=0`、`command_mode=pwm`、`pwm_min_abs=255`、`pwm_max_abs=255`。
- 上位机命令日志已观察到启动配置 `{"T":900,"main":1,"module":0}` 以及 PC 手控产生的 `T=11,L/R=255`、`T=11,L/R=-255` 和 stop `T=11,L/R=0`。
- 已重启 PC Node 到 `0.0.0.0:7001`，监听 PID `8406`；`GET http://127.0.0.1:7001/` 返回首页 HTML。
- 现场 PC summary 读回：`map_display_default_zoom_percent=45%`、`base_command_chain_observed=true`、`base_command_chain_nonzero_count=358`、`base_command_chain_startup_main_type_config_sent=true`、`base_command_chain_startup_main_type=1`、`base_command_chain_startup_module_type=0`、`wheel_raw_left=0`、`wheel_raw_right=0`、`wheel_feedback_lr_nonzero_proven=false`。

## 剩余风险

- 摄像头仍卡在 USB full-speed `12M` 且直接 V4L2 `STREAMON` 返回 `Input/output error`，不是 PC 多人预览独占问题；实时图传首帧未证明。
- WAVE ROVER 命令链路已到 bridge/UART，但 `T=1001 L/R` 仍为 `0/0`；剩余风险集中在电机使能、底盘模式、电源、轮子机械状态、固件反馈语义或下位机实际执行链路。
- 本轮未证明真实物理移动、wheel raw L/R 非零、完整 Nav2 自动驾驶移动闭环或 delivery success。
