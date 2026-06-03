# O1 Base Turn Smoke Micro Sprint Tech Done

## sprint_type

micro

## 本轮目标

用户反馈左右转还不行。本轮按 vendor 资料复核 WAVE ROVER UART `T=1` 左右轮速度映射，以及 `T=130/T=1001` feedback 语义；判断当前 onboard manual `left/right` 是否需要修复。范围内不改 PC UI。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/templates/control.js`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 已证实的硬件结论

- vendor `base_ctrl.py` 的 `base_speed_ctrl()` 发送 `{"T":1,"L":input_left,"R":input_right}`。
- vendor 固件 `uart_ctrl.h` 收到 `T=1` 后调用 `setGoalSpeed(L,R)`。
- vendor 固件 `movtion_module.h` 写明 `A-left, B-right`，`setGoalSpeed()` 将左输入映射到左侧控制，将右输入映射到右侧控制。
- vendor Web 控制 `templates/control.js` 对纯左转使用 `L=-max_speed,R=+max_speed`，对纯右转使用 `L=+max_speed,R=-max_speed`。
- 当前 onboard `wheel_command_for_direction()` 的 `left/right` 映射与 vendor 官方 Web 控制和差速转向常识一致，因此本轮不修改 `onboard/scripts/upper_robot_api.py`、不修改配套测试、不修改 PC UI。
- `T=130` 是非运动 base feedback request；`T=1001` 是 `baseInfoFeedback()` 输出的 vendor feedback，含 `L/R/r/p/y/v`。它不是项目 robot ACK、HIL pass、`safe_to_control=true` 或 ROS feedback topic 证明。

## 实际改动

- 新增 `docs/hardware/o1_base_manual_turn_smoke.md`
  - 记录 vendor 来源、左右转映射结论、现场点动建议、判定标准和证据边界。
- 更新 `docs/interfaces/o7_upper_robot_api.md`
  - 补充 `/api/base/manual` 的 `left/right` vendor 映射说明，以及 `T=130/T=1001` feedback 语义边界。
- 新增 `sprints/2026.06.03_24-25_o1-base-turn-smoke/tech-done.md`
  - 记录本轮 micro sprint 结论、验证结果和剩余风险。

## 验证结果

已运行：

- `python3 -m unittest onboard/scripts/test_upper_robot_api.py`
  - 结果：`Ran 16 tests in 1.341s`，`OK`。
- `python3 -m compileall -q onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py`
  - 结果：exit 0，无输出。
- `git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/interfaces/o7_upper_robot_api.md docs/hardware/o1_base_manual_turn_smoke.md sprints/2026.06.03_24-25_o1-base-turn-smoke/tech-done.md`
  - 结果：exit 0，无输出。

## 失败定位

当前未发现 onboard `left/right` 映射错误。现场“左右转还不行”更可能来自 pulse 太短/速度太低、地面摩擦、负载卡滞、观察视角、电机线序/安装方向、底盘模式或反馈材料未同场采集；这些必须用现场视频、左右轮观察、manual response 和 `T=1001` 回读材料继续定位。

## 剩余风险和下一步履约动作

- 本轮没有真实上车执行 `/api/base/manual`，没有发送运动命令，不能宣称左右转现场已恢复。
- 下一次现场建议在净空、急停、操作员看护条件下，用 `speed=0.08`、`duration_ms=350` 分别点动 `left/right`。
- 每次点动后必须额外 `POST /api/base/stop`，并保存 `manual` 响应、`stop` 响应、`feedback-request` 或 `feedback-samples` 的 `T=1001` 材料。
- 若观察到 left/right 轮向与 vendor 映射相反，先按硬件安装、电机线序、固件 `SET_MOTOR_DIR/mainType` 复核升级，不直接反改 onboard 方向表。
