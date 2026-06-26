# 2026-06-27 22:40 base command mode speed default

## sprint_type: micro

本轮针对 CEO 反馈“自动驾驶没法动、小车动不动不应依赖雷达”做底盘命令入口收敛。设计结论先于代码：雷达只影响建图/避障/验收，不应决定 `/cmd_vel` 是否能进入底盘；底盘默认命令模式必须和硬件 bridge 纯默认、vendor 主路径一致，PWM 只能作为显式 HIL/诊断 override。

采用的本地资料来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

## 实际改动

- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
  - `command_mode` 默认从 `pwm` 改回 `speed`。
  - 描述改为 `speed uses vendor T=1 default; pwm uses explicit T=11 diagnostic override; ros uses T=13`。
- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
  - 同步把 `command_mode` 默认从 `pwm` 改回 `speed`。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 新增静态契约测试，锁定 bringup/autonomous 默认 `speed`，并确认 `pwm_min_abs/pwm_max_abs` 仍作为显式 override 参数传入 `esp32_bridge`。
- `docs/hardware/wave_rover_json_bridge.md`
  - 更新 command mode 说明：`speed/T=1` 是默认，`pwm/T=11` 是显式诊断，不再写成默认成功路径。
- `docs/interfaces/ros_contracts.md`
  - 更新 `esp32_bridge.command_mode` 合约，说明 driver/bringup/autonomous 默认一致为 `speed`。
- `docs/interfaces/ros_runtime_contracts.md`
  - 更新 O11/Nav2 运行边界：PWM 可显式选择，但非零 PWM JSON 不等于 wheel raw L/R 证明。
- `docs/product/pc_free_roam_mapping_design.md`
  - 更新自由移动/建图口径：相机或雷达不 ready 仍可安全试动，但不能按可验收建图收口；底盘默认控制面回到 `speed/T=1`。
- `docs/product/pc_tools_workstation.md`
  - 把之前 PWM 默认说明收紧为历史诊断证据，明确当前默认与剩余运动材料缺口。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 通过，`Ran 18 tests in 0.032s`，`OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py onboard/src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py`
  - 通过，`Ran 35 tests in 0.014s`，`OK`。
- `rg -n "bringup/autonomous 默认 `command_mode=pwm`|default_value='pwm'|默认走该模式|默认使用该模式" docs onboard/src/ros2_trashbot_bringup -g '!**/node_modules/**'`
  - 无匹配，确认当前默认口径未残留旧文档。

## 剩余风险

- 本轮是代码契约和文档收敛，不是真实 HIL。还没有证明 WAVE ROVER 真实轮速非零、外部视频位移、LiDAR delta 或 delivery success。
- PC manual 的 `base_command_mode=pwm` 历史诊断路径没有在本轮改掉，因为它已有单独测试和历史材料；后续如果要统一 PC manual 默认，也必须重新做真实低速安全 HIL。
- 自动驾驶当前已经不应再被雷达 gate 判定为“不能发底盘命令”，但“发命令后真实动起来”仍需下一轮现场复测电机使能、底盘模式、供电、PWM/速度执行链和安全空间。
