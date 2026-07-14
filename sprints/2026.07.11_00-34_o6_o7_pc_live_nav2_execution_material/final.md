# O6/O7 PC Live Nav2 Execution Material Final

## 结果摘要

本轮 `sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/` 完成 `software_proof_pc_live_nav2_execution_material_only` 的产品收口：目标不是把 `2026-07-03` 的 PC live Nav2 执行材料包装成 current live rerun、delivery success 或 HIL pass，而是把这份既有 live material 以安全 additive section 形式贯通到 Algorithm -> O6 -> O7 的同一 `task_id` 证据链，并让 O7 operator 能直接看到 route execution 已走到哪一步、还差哪一层外部证明。

本轮选择逻辑保持与 `pre_start.md` 一致：O5 虽然仍是最低项，但最近 `cloud_production_cutover_readiness_packet` 已明确 `okr_credit_allowed=false`，当前环境没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser；O1 最近两轮则连续卡在 current same-run HIL、wheel L/R、external video、LiDAR motion delta 和 route execution blocker。相比继续消费相同 blocker，本轮转向 O6/O7，消费一类此前尚未进入同 task archive/readback/consumer 主路径的 prior live Nav2 execution material。

## 实际交付

- Algorithm 新增 `--pc-live-nav2-execution-material-json`，输出 `trashbot.pc_live_nav2_execution_material.v1`，写入 manifest 顶层与 `field_motion_evidence_packet.pc_live_nav2_execution_material`。
- O6 新增 `trashbot.o6.pc_live_nav2_execution_material.v1`，支持 archive detail、field evidence、artifact bundle、consumer detail 和 `include=pc_live_nav2_execution_material`。
- O7 默认 include/consume/display `pc_live_nav2_execution_material`，展示 `source_sprint`、`goal_accepted`、`goal_result_status`、`uses_base_uart`、`base_command_nonzero_observed`、`base_command_nonzero_count=733`、`base_feedback_sample_count=5941`、`base_feedback_lr_nonzero_proven=false`、`base_feedback_imu_attitude_delta_observed=true` 与 `next_required_evidence`。
- 集成验收补充了字段漂移复核，确保 `goal_accepted -> nav2_goal_accepted` 与 `goal_result_status -> result_status -> nav2_terminal_status -> terminal_status` 的 canonical/legacy 兼容顺序在三段链路内一致。

## 验证证据

- Algorithm：`python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py` 通过；`python3 -m unittest onboard.tests.test_field_route_evidence_manifest` 输出 `Ran 77 tests in 0.578s OK`；`git diff --check` 通过。
- O6：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 通过；`python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` 输出 `Ran 183 tests in 79.196s OK`；`git diff --check` 通过。
- O7：`cd pc-tools/workstation && npm run test && npm run build && npm run lint` 通过，关键输出为 `Tests 490 passed (490)`；build 仅保留既有 Vite chunk-size warning；`git diff --check` 通过。
- 集成验收：targeted Algorithm / O6 / O7 验收命令分别输出 `Ran 1 test in 0.008s OK`、`Ran 1 test in 0.789s OK`、`Tests 1 passed | 489 skipped (490)`。

## OKR 结论

- O6：从约 `~92%` 保守上调到约 `~93%`。原因是 O6 archive/readback 新消费了一类 prior live Nav2 execution material，并完成了真实 payload 字段漂移修平。
- O7：从约 `~92%` 保守上调到约 `~93%`。原因是 O7 operator 主路径现在默认展示这类同 task live execution material，用户可直接判断“Nav2/UART/base command/IMU 事实已到位，但轮速闭环、delivery、HIL 仍未证明”。
- O5：保持约 `~85%`。原因是本轮没有新增真实 production external evidence，仍不能靠 wrapper、readback、support-only packet 或 contract hardening 增分。
- O1：保持约 `~92%`。原因是本轮没有新增 current same-run HIL、wheel L/R nonzero、external video、LiDAR motion delta 或 Nav2 route execution live proof。

本轮不标完成、不归档任何 KR。

## 证据边界

本轮证据边界明确为 `software_proof_pc_live_nav2_execution_material_only`。它不证明：

- current live rerun；
- route execution success；
- delivery success；
- operator acceptance；
- WAVE ROVER wheel L/R nonzero feedback 已证明；
- HIL pass；
- production cloud / production DB/queue / OSS/CDN / phone/browser external proof。

## 风险与下一轮建议

- `base_feedback_lr_nonzero_proven=false` 仍是 O6/O7 继续上涨前最关键的 fail-closed 边界。只要这项仍未被 current same-run 材料证明，就不能把 base command nonzero 或 IMU attitude delta 当作 route execution success。
- 若下一轮继续做 O6/O7，必须接入 live route execution、delivery record、operator confirmation 或 production cloud readback 中至少一类新的同任务外部材料；否则又会落回 support-only lane。
- 若能拿到真实 production external evidence，优先回 O5；若能上车获取 current same-run HIL / wheel / motion / route 执行材料，优先回 O1。
