# O6 Worker Report

## 改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`

## 实际实现内容

- 为 O6 新增 `pc_live_nav2_execution_material` additive section，支持 `field_evidence_manifest`、`artifact_bundle` 和 `field_motion_evidence_packet` 三个入口位置。
- 新增 O6 回读 schema `trashbot.o6.pc_live_nav2_execution_material.v1`，支持 archive detail、field evidence、artifact bundle、consumer detail 和 `include=pc_live_nav2_execution_material`。
- 新增 fail-closed 安全收敛：
  - bad schema / bad proof scope / task mismatch 只降级该 section。
  - unsafe text（路径、URL、token、traceback、raw body）只降级该 section。
  - `base_feedback_lr_nonzero_proven=true` 会把该 section 降级为 `blocked_not_proven`。
- 测试新增正反两组回归，覆盖 field/bundle/detail/include 主路径，以及 missing、schema mismatch、proof scope mismatch、task mismatch、unsafe text、wheel L/R 非零宣称等 fail-closed 场景。
- 文档补充 `pc_live_nav2_execution_material` 的 schema、proof scope、include 行为和 fail-closed 规则。

## 验证命令与结果

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

- 结果：通过，无输出。

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

- 结果：

```text
.......................................................................................
----------------------------------------------------------------------
Ran 183 tests in 79.136s

OK
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material
```

- 结果：通过，无输出。

## 失败定位

- 本轮验收命令未复现失败。

## 剩余风险

- 当前 O6 只消费安全摘要，未证明真实 live Nav2 route execution success、真实 wheel L/R 非零反馈、真实 delivery record、真实 operator acceptance 或 production cloud。
- 我按 2026-07-03 现场验证记录形状固定了 O6 兼容字段；如果 Algorithm 最终 producer 追加新的安全字段，O6 当前会忽略它们而不是透传。
- 当前 contract 明确把 `base_feedback_lr_nonzero_proven=true` 视为 fail-closed；如果后续产品口径允许把该字段作为“来源事实但不等于 success proof”，需要再同步 O6/O7/Algorithm 合同。

## 协同需求

- 需要 Algorithm 与本字段名保持一致，尤其是 `source_sprint`、`goal_accepted`、`uses_base_uart`、`base_command_nonzero_observed`、`base_feedback_sample_count`、`base_feedback_lr_nonzero_proven`、`base_feedback_imu_attitude_delta_observed`、`result_status`。
- 需要 O7 按同一字段名消费并展示该 section。

## 返工记录

- 验收发现 O6 之前只输出 `result_status`，没有输出 canonical `goal_result_status`，且读取优先级没有覆盖 Algorithm 的 legacy `nav2_goal_accepted` / `nav2_terminal_status`。
- 本次返工已修复：
  - 读取 `goal_accepted` 时优先 canonical `goal_accepted`，fallback `nav2_goal_accepted`。
  - 读取结果状态时优先 canonical `goal_result_status`，fallback `result_status`、`nav2_terminal_status`、`terminal_status`。
  - O6 输出新增 canonical `goal_result_status`，同时保留 `result_status` alias。
  - 测试新增 canonical payload 与 legacy payload 兼容读回覆盖，确保 archive detail / consumer detail / include 都保持 ready。
- 返工后协同重点变为：O7 应优先消费 `goal_result_status`，`result_status` 只保留兼容用途。
