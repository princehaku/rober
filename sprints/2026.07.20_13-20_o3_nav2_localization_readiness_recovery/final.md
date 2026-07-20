# O3 Nav2 Localization Readiness Recovery - Final

## Sprint metadata

- `sprint_type: epic`
- Product owner：`product-okr-owner`
- Engineer owners：`robot-software-engineer`、`robot-algorithm-engineer`
- Final status：`accepted_engineering_owned_stop_clean_planner_only_no_go_no_okr_credit`
- proof boundary：`strict_no_motion_persistent_lifecycle_fresh_pose_planner_only_path_readiness`
- `PLANNER_ONLY_NO_GO`
- `OWNED_STOP_CLEAN=yes`
- `PRODUCT_CLOSEOUT_COMPLETE=yes`

## Product final decision

Product 接受跨 owner 代码、测试、navigation 文档、strict-no-motion start 合同、fresh current partial artifact 与 owned cleanup；拒绝 current localization/path readiness、motion、HIL、route、delivery、Mission 和 OKR credit。

用户获得的是一个真实生效且 fail-closed 的安全 lifecycle API：远端 API/helper SHA 均与本地对齐；final-window `start/refresh/stop=1/1/1`、proof latest GET=1、`retries=0`；effective `base_enabled=false/lidar_enabled=false`，new-open=`0/0`。`initialpose/goal/cmd_vel/UART=0/0/0/0`，command log delta=0，无物理运动。

Final stop semantic success，cleanup scope=`o11_owned_pid_process_group_only`；PID `684474` 与 owned PID file 已移除，最终 lifecycle stopped，因此 `OWNED_STOP_CLEAN=yes`。`readiness_assertion.json` 是 pre-stop snapshot；其中 stop pending 不能覆盖 `lifecycle_safety_manifest.json.final_stop` 和 stop response 的最终 cleanup 事实。

## 实际改动与验证证据

- Robot Software 完成 strict start/stop semantic contract、fail-closed compatibility migration、API tests 与 field-route preflight 文档。
- Algorithm 完成 current persisted pose planner-only gate、helper tests 与 fixed-route 文档。
- Robot：`py_compile` exit 0；`114 tests OK (skipped=1 aiohttp)`；中文注释比例 `20.2%`。
- Algorithm：`py_compile` exit 0；`167 tests OK`；中文注释比例 `20.946%`。
- 双方 diff 与静态断言均绿；8 个 JSON 可解析，Product 的 artifacts 交叉核对通过。
- Product 没有重跑工程 tests/build/SSH/ROS/Nav2/control，只执行 read-only 文档与 artifact 验收。

## Current PLANNER_ONLY_NO_GO

Helper `elapsed_ms=80444`，超过 API `process_timeout_s=80`；partial artifact 被保留，last successful phase=`tf_probe`，timeout command=`ros2 pkg list`。精确根因包括：

- `helper_process_timeout_after_partial_artifact`
- `sigint_before_final_artifact`
- `current_amcl_pose_sample_timestamp_and_freshness_not_proven`
- `persisted_pose_audit_and_final_tf_freshness_gate_not_reached`
- `planner_and_controller_lifecycle_active_not_proven_before_timeout`

Partial current evidence 只证明 map_server/amcl active、dynamic `map->odom` observed 且 unique AMCL attribution、`map->base_link=true`、initialpose publish attempts=0。它不证明 fresh `/amcl_pose`、persisted pose final gate、formal TF freshness、planner/controller active 或 path。

Path requested=true，但 attempted/succeeded/generated=false，count=0。因此最终裁决保持 `PLANNER_ONLY_NO_GO`；代码合同与 no-go 均不得转算为 OKR 提升。

## OKR、Mission、delta 与 KR

- O5：约 `85%`，provider/runtime blocker `2/2`，flat。
- O6/O7：各约 `93%`，flat。
- O1：约 `94%`，flat。
- O3：不新增 Mission credit；主百分比不调整。
- `current_run_artifact_delta=true`：仅表示 fresh no-motion current artifact、strict contract 和 clean stop。
- `external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false`。
- `robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`delivery_success=false`、`safe_to_control=false`、`okr_credit=false`。
- KR：`不归档`；历史区无新增。

Mission Objective 0 不是 pending authorization：CEO 已授权 motion，但本 sprint 未消费。正确状态仍为 `blocked_before_attempt_on_current_localization_readiness`，没有 mission attempt 或 success。

## 方向调整与剩余风险

本轮修复了 start body 被忽略、`auto` 可能新开 serial、HTTP 200 被误判成功和 persisted-pose planner-only gate 的代码合同；当前剩余风险已收敛到 O10 helper runtime path 与 80s API budget 不相容，以及 Upper API graceful shutdown 的既有 `stop-sigterm` 风险。

暂停重复 strict-start wrapper/live refresh。`next_offline_runtime_budget_fix`：下一轮由 `robot-software-engineer` 与 `robot-algorithm-engineer` 先在本地/离线剖析并修复 helper 在 `ros2 pkg list` / TF probe 后超出 80s budget 的 runtime path、probe order 与 final artifact 时序；只有新测试证明能在预算内自然完成，才开新的 no-motion current proof。

若新 proof 仍无 persisted pose，Product/CEO 必须明确 localization input gate，禁止隐式 `/initialpose`。运动授权仍未被本 sprint 消费；未来 motion 必须重新满足 current readiness、operator、路线和 obstacle gate。
