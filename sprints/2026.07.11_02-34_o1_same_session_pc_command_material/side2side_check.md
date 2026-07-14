# O1 Same-Session PC Command Material Side2Side Check

## 对照结论

本轮验收通过。实际交付与 `tech-plan.md` 一致：Hardware owner 只扩展 O1 hardware bundle additive fields，没有改 ROS topic、service、launch 参数、WAVE ROVER command 行为或硬件配置。

## 计划 vs 实际

| 项目 | 计划口径 | 实际结果 | 结论 |
| --- | --- | --- | --- |
| 输入 artifact | 消费 `02_pc_first_jog_samesession_timeoutfix.json` 和 `03_base_status_after_pc_jog.json` | 已加入默认路径并由 CLI 默认消费 | 通过 |
| 输出前缀 | 只输出 `same_session_pc_command_*` | 关键字段均带前缀；未输出顶层 `wheel_feedback_lr_nonzero_proven=true` | 通过 |
| 安全字段 | 顶层 success/control/HIL 固定 false | `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`robot_control_executed=false`、`nav2_route_execution_success=false` | 通过 |
| 双向事实 | motion-window L/R 非零和 after-jog L/R 零速同时保留 | 输出 L/R `20.0/20.0` 与 after-jog `0.0/0.0` | 通过 |
| 泄露围栏 | 不回显 URL、endpoint、`/root/`、`/dev/tty*`、baudrate、raw frames、secret | positive leakage test 保持通过，新增 after-jog negative test | 通过 |

## 主节点验收

主节点只读复核了 diff、`tech-done.md` 和 `hardware_worker_report.md`。新增 parser 只消费 allowlisted 字段，并把 `remote_motion_key_values.wheel_feedback_lr_nonzero_proven=true` 限制在 `same_session_pc_command_wheel_feedback_lr_nonzero_material_present=true` 语义内；after-jog readback 仍明确 `left_speed=0.0/right_speed=0.0`。

## 证据边界

Proof boundary：`software_proof_o1_motion_map_hil_material_bundle_only`。

本轮不证明 current live HIL、safe-to-control、delivery success、wheel direction、IMU/battery calibration、current live Nav2 route execution success 或 production cloud。
