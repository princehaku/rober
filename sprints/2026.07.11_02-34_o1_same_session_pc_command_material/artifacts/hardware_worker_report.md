# Hardware Worker Report

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

## 已证实的硬件结论

- `json_cmd.h` 定义 `T=1` 为左右轮速度命令、`T=130` 为底盘反馈请求、`T=1001` 为底盘基础反馈。
- `uart_ctrl.h` 表明 `CMD_SPEED_CTRL/CMD_BASE_FEEDBACK/CMD_ROS_CTRL` 都经 JSON `T` 分发；本轮只消费历史 artifact，不发送新命令。
- `ugv_rpi/base_ctrl.py` 明确上位机串口发包是 `json.dumps(data) + '\\n'` 的 UTF-8 JSON line。
- `config.yaml` 中 vendor `cmd_movition_ctrl=1`，与 `json_cmd.h` 的 `CMD_SPEED_CTRL=1` 一致。
- `02_pc_first_jog_samesession_timeoutfix.json` 可证明 historical same-session PC proxy 曾记录 motion-window 非零轮速材料；`03_base_status_after_pc_jog.json` 可证明 after-jog 的 latest `T=1001` readback 已回到 `L=0/R=0`。这两者都只是 material fact，不是 current live acceptance。

## 改动文件

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/tech-done.md`
- `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/artifacts/hardware_worker_report.md`

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py`
  - 结果：通过。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'`
  - 结果：`Ran 36 tests in 0.289s`，`OK`。
- `PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle`
  - 结果：exit `0`。
  - 关键输出：`status=motion_map_hil_material_bundle_ready_not_hil_pass`、`same_session_pc_command_material_present=true`、`same_session_pc_command_material_status=same_session_pc_command_material_ready_not_hil_pass`、`same_session_pc_command_motion_window_nonzero_frame_count=1`、`same_session_pc_command_after_jog_latest_pair.left_speed=0.0/right_speed=0.0`、`same_session_hil_acceptance_status=blocked_missing_current_live_acceptance`。
- `rg -n "same_session_pc_command|same_session_hil_acceptance|blocked_missing_current_live_acceptance" ...`
  - 结果：命中实现、测试、硬件文档和 sprint 留档锚点。
- `git diff --check -- ...`
  - 结果：通过。

## 当前 evidence boundary

- `software_proof_o1_motion_map_hil_material_bundle_only`
- historical same-session upper-computer software proof only
- 不证明 current live HIL
- 不证明 safe-to-control
- 不证明 delivery success
- 不证明 current live route execution success

## 风险与下一步

- 还缺 current live same-run external video、LiDAR motion delta、HIL acceptance record、Nav2 route execution success。
- 下一步应采 current live same-run `feedback_T1001.log`、motion command record、operator/external observation 和 HIL acceptance record，把 historical same-session material 过渡到 current live acceptance。
