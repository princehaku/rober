# O1 Same-Session PC Command Material Final

## 复盘结论

本轮 `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/` 完成 O1 historical same-session PC command material 收口。Hardware owner 已把 `02_pc_first_jog_samesession_timeoutfix.json` 与 `03_base_status_after_pc_jog.json` 安全接入 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，形成 `same_session_pc_command_material` additive section。

Product 判断：O1 从约 `~92%` 保守上调到约 `~93%`。原因是本轮消费了此前未进入 composite bundle 的两个同会话 PC/上位机 artifact delta；但它仍是 historical same-session software proof，不是 current live rerun 或 HIL acceptance。本轮不归档任何 KR。

## 实际改动

Hardware owner 改动：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/tech-done.md`
- `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/artifacts/hardware_worker_report.md`

Product / 主节点收口改动：

- `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/side2side_check.md`
- `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/final.md`
- `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/artifacts/product_worker_report.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 核心输出

- `same_session_pc_command_material_present=true`
- `same_session_pc_command_material_status=same_session_pc_command_material_ready_not_hil_pass`
- `same_session_pc_command_latest_nonzero_pair.left_speed=20.0`
- `same_session_pc_command_latest_nonzero_pair.right_speed=20.0`
- `same_session_pc_command_after_jog_latest_pair.left_speed=0.0`
- `same_session_pc_command_after_jog_latest_pair.right_speed=0.0`
- `same_session_hil_acceptance_status=blocked_missing_current_live_acceptance`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `nav2_route_execution_success=false`

## 验证结果

Hardware owner 记录的最终验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py
通过
```

```text
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'
Ran 36 tests in 0.289s
OK
```

```text
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
exit 0
status=motion_map_hil_material_bundle_ready_not_hil_pass
same_session_pc_command_material_present=true
```

```text
git diff --check -- scoped files
通过
```

主节点只读验收确认：改动集中在允许范围；PC motion-window L/R 非零只作为 prefix material fact；after-jog L/R zero readback 保留；最终 summary 不输出顶层 `wheel_feedback_lr_nonzero_proven=true`。

## OKR 结论

- O5：保持约 `~85%`。仍缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实 phone/browser evidence；继续做 O5 support-only readiness 不计分。
- O1：从约 `~92%` 保守上调到约 `~93%`。本轮新增消费两个 historical same-session PC/上位机 artifact delta，但不归档 KR。
- O6/O7：保持约 `~93%`。本轮未改 O6/O7 消费链路。

## 证据边界

Proof boundary：`software_proof_o1_motion_map_hil_material_bundle_only` / historical same-session upper-computer software proof only。

本轮不证明：

- current live HIL pass；
- safe-to-control；
- delivery success；
- wheel direction；
- IMU/battery calibration；
- current live Nav2 path generation success；
- current live Nav2 route execution success；
- production cloud。

## 下一轮建议

优先采 O1 current live same-run HIL artifact：`feedback_T1001.log`、motion command record、operator/external observation、external video、LiDAR motion delta 和 HIL acceptance record。若 CEO 能提供 O5 production external evidence，则切回 O5；否则不要继续把 historical same-session material 包装成 current live HIL。
