# Hardware Infra Owner Note: O10 Path Contract Safety Boundary

## sprint_type

sprint_type: epic

## 任务结论

本轮 Hardware Infra 只做安全边界复核和留档，不改产品代码、不改硬件配置、不发送真实串口命令。

结论：

- Robot Software 的 O10 map proof/path contract lock 目标仍应保持 no-motion：只锁定 map lifecycle proof latest JSON 的 canonical/readback 路径。
- 本轮 path contract lock 不应触碰 WAVE ROVER、base UART、`/api/base/manual`、`/cmd_vel`、`T=1`、`T=13`、`T=130`、`T=131` 或把 `T=1001` 写成 ACK/HIL。
- 当前没有现场看护、净空、急停/断电和 CEO/现场授权材料，stop-first HIL 判定为 `blocked_with_root_cause`。不得写 HIL pass。

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
  - WAVE ROVER upper/lower link 是 UART newline-delimited JSON。
  - vendor Raspberry Pi UART reference 是 `/dev/ttyAMA0 @115200`，Orange Pi 现场路径必须另行确认，不能凭 vendor path 硬编码。
  - WAVE ROVER 命令与反馈必须回到 `ugv_rpi/base_ctrl.py`、`json_cmd.h`、`uart_ctrl.h`、`movtion_module.h` 等本地资料。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `BaseController` 用 `serial.Serial(uart_dev_set, buad_set, timeout=1)` 打开串口。
  - `process_commands()` 写入 `(json.dumps(data) + '\n').encode("utf-8")`。
  - `base_speed_ctrl()` 发送 `{"T":1,"L":input_left,"R":input_right}`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `CMD_SPEED_CTRL=1`、`CMD_ROS_CTRL=13`、`CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`、`FEEDBACK_BASE_INFO=1001`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
  - `CMD_BASE_FEEDBACK` 调用 `baseInfoFeedback()`。
  - 串口 JSON 解析以换行形成完整命令。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
  - `baseInfoFeedback()` 输出 `T=FEEDBACK_BASE_INFO`，属于 vendor feedback material。

## O10 no-motion 复核

已复核 O10 `tech-plan.md`、`onboard/scripts/o3_map_lifecycle_proof.py` 和 `onboard/scripts/upper_robot_api.py` 当前 map lifecycle proof 相关边界：

- `o3_map_lifecycle_proof.py` 的 `safety_flags()` 固定 `safe_to_control=false`、`sends_base_motion_commands=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`delivery_success=false`、`hil_pass=false`。
- `upper_robot_api.py` 的 `run_map_lifecycle_proof_helper()` 注释说明 helper 只启动 LiDAR/SLAM，不接触底盘控制，并在成功、超时和异常分支都返回 `safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`。
- O10 path contract lock 若只调整 canonical latest path/readback 字段，不产生底盘运动风险；但任何新增实现必须继续保持上述安全字段和 forbidden command list。

硬件判断：

- `POST /api/map/proof/refresh` 和 `GET /api/map/proof/latest` 成功只能证明 no-motion map lifecycle/path contract material。
- 它不证明 WAVE ROVER stop、manual pulse、robot ACK、`T=1001` 同场反馈、PC WASD、AMCL/Nav2 真实消费或 delivery success。
- 若回包出现 `safe_to_control=true`、`hil_pass=true`、`robot_control_executed=true`、`sends_base_motion_commands=true`，或证据链出现 `T=1/T=13/T=130/T=131`，应视为安全口径漂移并阻断 O10 验收。

## stop-first HIL blocker

stop-first HIL 需要同场满足：

- 现场看护：操作员在场，能立即观察机器人并执行物理停机。
- 物理净空：机器人周围无人员、线缆、桌脚和易碰撞物，低速短 pulse 有缓冲距离。
- 急停/断电：现场已确认物理停机路径可用，不依赖软件 stop 单点成功。
- CEO/现场授权：明确允许进入真实底盘低速 pulse。

本轮未提供以上现场材料，所以 Hardware 只能写：

- `stop_first_hil_status=blocked_with_root_cause`
- `missing_prerequisites=["operator_present", "physical_clearance_confirmed", "emergency_stop_or_power_cut_ready", "ceo_or_field_authorization"]`
- `hil_pass=false`
- `safe_to_control=false`

## 验收记录

已执行命令：

```bash
sed -n '1,220p' docs/vendor/VENDOR_INDEX.md
python3 -m unittest onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
git diff --check -- docs/hardware/o1_pc_manual_lidar_hil_boundary.md sprints/2026.06.05_12-13_o10-delivery-readiness-path-contract-epic/owner_notes/robot-hardware-engineer.md
```

结果：

- `sed -n '1,220p' docs/vendor/VENDOR_INDEX.md`：通过，确认本轮使用的 WAVE ROVER UART/JSON、Orange Pi 路径确认和 LiDAR source-of-truth 入口。
- `python3 -m unittest onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py`：通过，`Ran 18 tests in 0.410s`，`OK`。
- `git diff --check -- ...`：通过，无 whitespace/error 输出。

## 剩余风险

- 未执行真实硬件 HIL，未打开 `/dev/ttyS5`，未发送 `T=1/T=13/T=130/T=131`。
- 未观察同场 `T=1001`，没有 robot ACK 或 stop-first operator report。
- 若 Software 后续改动 path contract 实现，Hardware 需要复核实际 diff 和回包字段是否仍保持 no-motion。
