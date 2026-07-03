# 2026.07.03 23:58 PC Command Raw Motion Evidence

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `command_raw_motion_summary*`，把本次 `T=1/T=11 L/R`、`T=13 X/Z` 命令 raw 非零与 vendor `T=1001 L/R` feedback 分开。
  - `/api/base/manual` 新增 `command_raw_*`、`motion_evidence_complete`、`motion_evidence_source` 字段；`wheel_feedback_lr_nonzero_proven` 仍只由同窗口 T1001 L/R 非零决定。
  - `/api/base/status` 从 fresh `wave_rover_command_debug.jsonl` 派生最近 sent nonzero command raw L/R，供 PC summary 显示控制链事实。
- `pc-tools/workstation/src/server/index.ts`
  - PC manual proxy 透传并顶层暴露 `command_raw_*` 与 `motion_evidence_*`。
  - 键盘本地 evidence cache 支持 command raw + motion evidence，保留 vendor feedback 单独字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、`src/shared/contracts.ts`
  - Summary 增加 `keyboard_command_raw_lr_nonzero`、`keyboard_motion_evidence_complete`、`keyboard_wheel_feedback_lr_nonzero`。
  - Action card/base readback 合同同步 command raw 与 motion evidence 字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 键盘状态新增“命令已动”中间态：command raw + IMU 已动可完成手控动作目标，但页面仍显示 vendor feedback L/R=0/0 未非零。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 command raw + IMU 回归，防止以后把 feedback L/R=0/0 假报成非零。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步 PC 手控证据分层口径与 WAVE ROVER vendor 资料来源。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过，`tsc` + `vite build` + server `tsc` 均成功。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "keyboard wheel readback|wheel raw goal|continuous hand|command raw"`：通过，3 passed。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts`：通过，241 passed。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py`：通过。
- `python3 -m unittest onboard.src.ros2_trashbot_bringup.test.test_launch_contract_static`：通过，23 tests OK。
- `git diff --check`：通过。
- 上车部署：已 `scp` 到 `root@192.168.1.11:7878:/root/rober/onboard/scripts/upper_robot_api.py`，`python3 -m py_compile` 通过，`trashbot-upper-robot-api.service` 重启后 `active`。
- PC Node：已重启为 `HOST=0.0.0.0 PORT=7001 ROBER_ROBOT_API_BASE_URL=http://192.168.1.11:8787 npm run api`，监听 `*:7001`；最终 summary 可读。
- Live smoke：
  - 500ms ROS/T=13 手控：`proxy_status=command_forwarded`、80 帧 T1001、`command_raw_twist_nonzero_proven=true`、`wheel_feedback_lr_nonzero_proven=false`、`L/R=0/0`。
  - 800ms 手控：`command_raw_nonzero_proven=true`、`command_raw_lr_nonzero_proven=true`、`command_raw_latest_left/right=255/255`、`imu_attitude_delta_observed=true`、`motion_evidence_complete=true`、`motion_evidence_source=command_raw_lr_plus_motion_signal`、`wheel_feedback_lr_nonzero_proven=false`、`wheel_feedback_latest_raw_left/right=0/0`。
  - stop 兜底：`proxy_status=command_forwarded`。
  - stop 后 summary：`keyboard_wheel_lr_nonzero=true`、`keyboard_command_raw_lr_nonzero=true`、`keyboard_wheel_feedback_lr_nonzero=false`、`base_command_raw_lr=true`、`base_command_raw_latest_left/right=255/255`、`base_feedback_lr=false`、`base_feedback_left/right=0/0`。
  - 最终 7001 summary：`status=needs_wysiwyg`、`robot_api=readable`、`keyboard_wheel_lr_nonzero=true`、`keyboard_command_raw_lr_nonzero=true`、`keyboard_wheel_feedback_lr_nonzero=false`、`base_command_raw_lr=true`、`base_feedback_lr=false`。

## 剩余风险

- vendor T1001 feedback L/R 仍为 0/0；本轮没有假报为反馈非零，后续仍需继续查 WAVE ROVER feedback/编码器/固件或模式原因。
- 800ms smoke 能证明低速手控动作和 command raw 链路，但不等于完整 Nav2 路线成功或 delivery success。
- 相机首帧仍是独立硬件/输入信号缺口，不在本轮修复范围。
