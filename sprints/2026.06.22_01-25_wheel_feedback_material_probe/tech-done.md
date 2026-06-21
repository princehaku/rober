# 2026.06.22 01:25 Wheel Feedback Material Probe

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`：`/api/base/feedback-samples` 现在保留精简 `t1001_feedback_frames`，并按同一 `T=1001` 帧内 `L/R` 都有限非零的规则生成 `wheel_feedback_summary`、`wheel_feedback_lr_nonzero_proven` 和 `wheel_feedback_nonzero_observed`。
- `pc-tools/workstation`：PC feedback samples proxy、manual/first-jog evidence capture 和 Robot Control summary 增加 wheel material 短字段；字段只用于材料诊断，不提升 `safe_to_control`、`hil_pass` 或 `delivery_success`。
- `onboard/tests/test_upper_robot_api.py` 与 `pc-tools/workstation/test/catalog.test.ts`：增加 T1001 L/R 非零聚合和 PC 透传回归测试。
- 文档同步更新 `OKR.md`、`docs/hardware/board_sensor_stack_smoke.md`、`docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`。

## 验证结果

- 上位机部署：已备份旧脚本到 `/root/rober/onboard/scripts/backup_20260622_012522/upper_robot_api.py`，新脚本通过远端 `python3 -m py_compile`，`trashbot-upper-robot-api.service` 重启后 active，PID `17608`。
- 静止真实采样：`01_upper_feedback_samples_after_deploy.json` 返回 `t1001_feedback_frames`，L/R 都为 `0`，`wheel_feedback_lr_nonzero_proven=false`。
- 点动期间并发采样：`04_upper_feedback_samples_during_manual.json` 返回 `t1001_observed_count=4`，但 4 帧 L/R 仍为 `0`，所以 wheel raw nonzero 仍未证明。
- PC proxy：`06_pc_feedback_samples_proxy_after_fields.json` 返回 `samples_forwarded`、`remote_http_status=200`、`wheel_feedback_lr_nonzero_proven=false`、`wheel_feedback_latest_left_speed=0`、`wheel_feedback_latest_right_speed=0`。
- PC summary：`10_pc_summary_retry_after_timing.json` 返回 `robot_api_connection.status=readable`、`loaded_count=13`、`failed_count=0`、`first_jog_readiness_summary.status=ready_for_first_jog`。
- PC first-jog：`15_pc_first_jog_ui_body_after_wheel_fields.json` 返回 `proxy_status=command_forwarded`、`remote_http_status=200`、`clamped_speed_mps=0.08`、`clamped_duration_ms=500`；随后 `16_pc_stop_after_first_jog_ui_body.json` 返回 `proxy_status=command_forwarded`。

## 软件验证

- `python3 -m py_compile onboard/scripts/upper_robot_api.py`：通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api`：通过，33 tests。
- `cd pc-tools/workstation && npm run test -- --run test/catalog.test.ts`：通过，80 tests。
- `cd pc-tools/workstation && npm run test`：通过，2 个测试文件、99 tests。
- `cd pc-tools/workstation && npm run build`：通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `bash onboard/scripts/docker_humble_build.sh`：通过，`Summary: 6 packages finished [47.7s]`；证据边界为 `software_proof_docker_only`。

## 剩余风险

- 当前真实 WAVE ROVER `T=1001` 已能透传 L/R，但点动期间仍观测为 `0/0`，不能证明 wheel raw nonzero；需要继续查固件反馈语义、反馈时序或更长/更合适的采样窗口。
- 本轮没有改变运动安全 gate，也没有证明完整 HIL、Nav2 route execution、真实手控/寻路或 delivery success。
