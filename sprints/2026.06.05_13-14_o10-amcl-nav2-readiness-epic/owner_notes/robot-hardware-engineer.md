# Robot Hardware Engineer Owner Note

## sprint_type

sprint_type: epic

## 任务

- Owner：`robot-hardware-engineer`
- KR：`KR-O10-Stop-First-HIL-Gate`
- 时间：2026-06-05 13-14 CST
- 结论：`blocked_with_root_cause`
- evidence_type：`blocked_with_root_cause`

## 已读 vendor 来源

- `AGENTS.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 硬件结论

- WAVE ROVER 上下位机链路按 vendor 资料是 UART、UTF-8、newline-delimited JSON。
- `T=1`、`T=11`、`T=13` 分别进入速度、PWM 和 ROS velocity 底盘控制路径，本轮 no-motion/path contract 不允许触碰这些命令。
- `T=130`、`T=131`、`T=142`、`T=143` 是反馈/echo/间隔相关命令；它们不等于 motion HIL，也不能替代 stop-first 现场授权。
- `T=1001` 来自 vendor `baseInfoFeedback()`，只能作为 vendor feedback material；缺 stop、post-status、operator report 和同场安全观察时，不能写 robot ACK、HIL pass 或 `safe_to_control=true`。
- 上位机可 SSH 不等于可运动。缺现场看护、净空、急停/断电路径和 CEO/现场授权时，必须保持 no-motion。

## 实际改动

- 更新 `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`，新增 Stop-first HIL Gate CEO blocker 模板。
- 新增本 owner note，记录硬件决策门的 vendor 来源、阻塞根因、验证结果和剩余风险。

## 验证结果

已运行：

```bash
sed -n '1,220p' docs/vendor/VENDOR_INDEX.md
python3 -m compileall -q onboard/scripts onboard/src
python3 -m unittest onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
git diff --check -- docs/hardware/o1_pc_manual_lidar_hil_boundary.md sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/owner_notes/robot-hardware-engineer.md
```

关键结果：

- `sed -n '1,220p' docs/vendor/VENDOR_INDEX.md`：已确认 WAVE ROVER UART newline-delimited JSON、vendor Raspberry Pi `/dev/ttyAMA0 @115200` 仅为参考、Orange Pi 串口需现场确认、`T=1/T=11/T=13/T=130/T=131/T=142/T=143` 的本地 vendor 口径。
- `python3 -m compileall -q onboard/scripts onboard/src`：通过，无输出。
- `python3 -m unittest onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py`：通过，`Ran 18 tests in 0.454s`，`OK`。
- `git diff --check -- ...`：通过，无输出。

## 是否执行运动

否。

未执行：

- `ssh root@192.168.1.11 -p 37878`
- `/api/base/manual`
- pulse/base manual/WASD
- `T=1`、`T=11`、`T=13`
- ROS `/cmd_vel`

原因：当前对话没有提供同场 operator、物理净空、急停/断电路径、CEO/现场授权四项材料，按 stop-first HIL gate 必须 fail-closed。

## blocker_root_cause

`missing_same-session_site_safety_authorization`

CEO/现场需要提供：

- operator 姓名或角色，确认人在现场看护。
- 低速短 pulse 区域净空确认。
- 可立即急停或断电的路径确认。
- CEO/现场负责人明确授权本次 stop-first 单方向低速短 pulse。
- 统一 `evidence_ref`，绑定 preflight、stop、pulse、post-status、`T=1001` 和 operator review。

## 剩余风险

- 未做真实串口、真实 WAVE ROVER feedback、真实 stop、真实 pulse、真实 post-status 或 operator review。
- `python` 单测只能证明 no-motion runner 护栏，不证明硬件可控。
- `T=1001` 即使后续出现，也必须和同一 evidence_ref 的 stop/operator 材料绑定后才能进入 Product/OKR 收口。
- 本轮不得提升 O10 HIL 完成度，只能作为 CEO blocker 和 no-motion gate 材料。
