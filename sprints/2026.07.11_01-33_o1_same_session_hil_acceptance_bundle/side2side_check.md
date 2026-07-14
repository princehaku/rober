# O1 Same-Session HIL Acceptance Bundle Side2Side Check

## 验收结论

Product / 主节点只读验收通过。Hardware owner 已按 `tech-plan.md` 将 historical same-session wheel feedback material 接入 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，并保持 HIL / safety / delivery / route success 结论 fail-closed。

## 对照检查

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 只消费 allowlisted same-session material | 通过 | `same_session_wheel_feedback_material_present=true` |
| L/R 非零材料带前缀输出 | 通过 | `same_session_wheel_feedback_latest_nonzero_pair.left_speed=61.0`、`right_speed=61.0`、`sign_pattern=both_positive` |
| 不输出顶层成功轮速字段 | 通过 | 测试断言 `wheel_feedback_lr_nonzero_proven` 不在顶层 summary |
| current live rerun 边界明确 | 通过 | `same_session_wheel_feedback_current_live_rerun=false` |
| HIL acceptance 仍 blocked | 通过 | `same_session_hil_acceptance_status=blocked_missing_current_live_acceptance` |
| 安全字段固定 false | 通过 | `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false` |
| 泄露边界 | 通过 | 单测覆盖 `/dev/tty`、`115200`、URL、endpoint、raw frames 不出现在最终 summary |

## 验证证据

Hardware `tech-done.md` 记录：

```text
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py
exit 0
```

```text
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'
Ran 35 tests in 0.261s
OK
```

```text
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
exit 0
status=motion_map_hil_material_bundle_ready_not_hil_pass
same_session_wheel_feedback_material_status=same_session_wheel_feedback_material_ready_not_hil_pass
same_session_hil_acceptance_status=blocked_missing_current_live_acceptance
```

## OKR 判断

O1 保持约 `~92%`，不因本轮上调。理由：本轮接入的是已经在 `2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake` 消费过的 historical same-session material 的 composite bundle view，不是新 current live HIL rerun、external video、LiDAR motion delta、acceptance record 或 route execution proof。

O5 保持约 `~85%`。O5 仍是最低项，但没有真实 external production evidence；继续做 local/mock readiness/readback 仍是 support-only。

## 剩余风险

- 仍缺 current live same-run `feedback_T1001.log`。
- 仍缺 current live motion command record、operator/external observation、external video 和 LiDAR motion delta。
- 仍缺 HIL acceptance record、wheel direction confirmation、IMU/battery calibration record。
- 仍缺 current live Nav2 path generation success 和 route execution success。
