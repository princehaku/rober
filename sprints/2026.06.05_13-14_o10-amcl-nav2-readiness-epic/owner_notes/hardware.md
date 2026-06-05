# Hardware Owner Note: Stop-first HIL Gate Acceptance

## sprint_type

sprint_type: epic

## 任务

- Owner：`robot-hardware-engineer`
- KR：`KR-O10-Stop-First-HIL-Gate`
- 时间：2026-06-05 13-14 CST
- 结论：`blocked_with_root_cause`
- blocker_root_cause：`missing_same-session_site_safety_authorization`
- evidence_type：`blocked_with_root_cause`

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 已证实的硬件结论

- WAVE ROVER 上下位机链路按本地 vendor 资料是 UART、UTF-8、newline-delimited JSON。
- `base_ctrl.py` 通过 `json.dumps(data) + '\n'` 写串口；`base_speed_ctrl()` 会发送 `{"T":1,"L":...,"R":...}`。
- `json_cmd.h` 定义 `CMD_SPEED_CTRL=1`、`CMD_PWM_INPUT=11`、`CMD_ROS_CTRL=13`、`CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`、`FEEDBACK_BASE_INFO=1001`。
- `uart_ctrl.h` 中 `T=1/T=11/T=13` 进入底盘控制路径；`movtion_module.h` 的 `rosCtrl()` 会把 `X/Z` 转成左右轮目标速度。
- `ugv_advance.h` 的 `baseInfoFeedback()` 输出 `T=1001`、`L/R/r/p/y/v` 等字段；该反馈只能作为 vendor feedback material，不能单独写成 robot ACK 或 HIL pass。
- vendor Raspberry Pi 默认 `/dev/ttyAMA0 @115200` 不能外推为 Orange Pi 默认；当前现场材料使用 `/dev/ttyS5 @115200` 也必须在真实 HIL 同场复核。

## 本轮安全判定

- `/cmd_vel_sent=false`
- `base_manual_called=false`
- `sends_base_motion_commands=false`
- `robot_control_executed=false`
- `wave_rover_motion_executed=false`
- `safe_to_control=false`
- `hil_pass=false`
- `field_hil_material=not_proven`

缺少同场现场看护、物理净空、急停/断电路径和 CEO/现场授权时，本轮只能保持 no-motion。即使上位机可 SSH 或 API 可达，也不得发送 `/api/base/manual`、base manual、WASD、pulse、`T=1`、`T=11`、`T=13` 或 ROS `/cmd_vel`。

## 实际改动

- 新增本 owner note，承接本轮 Hardware owner 对 stop-first HIL gate 的验收结论。
- 在 `tech-done.md` Hardware 相关段落补充机器可读安全字段和 grep 验收结果。
- 未修改底盘驱动、launch、串口参数、vendor 文件或 factory firmware。

## 验证结果

已执行并通过：

```bash
sed -n '1,220p' docs/vendor/VENDOR_INDEX.md
grep -R "safe_to_control=false\|sends_base_motion_commands=false\|robot_control_executed=false\|hil_pass=false\|missing_same-session_site_safety_authorization\|not_proven" docs/hardware/o1_pc_manual_lidar_hil_boundary.md sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/owner_notes/hardware.md sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/tech-done.md
git diff --check -- docs/hardware/o1_pc_manual_lidar_hil_boundary.md sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/owner_notes/hardware.md sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/tech-done.md
```

关键结果：

- vendor index 入口确认了 WAVE ROVER UART newline-delimited JSON、Raspberry Pi 串口路径不能外推到 Orange Pi、`T=1/T=11/T=13/T=130/T=131` 和 LiDAR 串口隔离边界。
- grep 覆盖了 `safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`、`missing_same-session_site_safety_authorization` 和 `not_proven`。
- `git diff --check` 无 whitespace error。

## 失败定位

无命令失败。当前阻塞不是软件异常，而是现场 HIL 安全授权材料缺失：`missing_same-session_site_safety_authorization`。

## 剩余风险

- 未执行 SSH、`/api/base/manual`、base manual、WASD、pulse、`T=1/T=11/T=13`、WAVE ROVER motion 或 ROS `/cmd_vel`。
- 未形成真实 stop、低速 pulse、post-status、operator report、同场 `T=1001` 或视频/现场记录。
- `T=1001` 后续即使出现，也必须和同一 `evidence_ref` 的 pre-stop、manual response、auto stop、post-status 和 operator review 绑定，才能进入 Product/OKR 收口。
- 本轮不得把 `not_proven`、`blocked_with_root_cause` 或 no-motion 材料写成 HIL pass、robot ACK、`field_hil_material` 或 `safe_to_control=true`。
