# Final - O6/O7 Same-Task Replay Packet Readback

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback/`
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Final status: accepted
- Closeout time: 2026-07-13 06:59 CST
- Proof boundary: `software_proof_o6_o7_same_task_replay_packet_readback_only`

## 用户价值和产品北极星

北极星仍是固定路线送垃圾任务的可验证闭环。本轮没有发车、没有执行路线、没有送达；本轮价值是把 05:02 已接受的 28-pose same-task replay packet 安全接入 O6 local/mock archive/readback 与 O7 PC consumer detail，让后续现场 route execution / delivery / HIL 材料能沿同一 `task_id`、`packet_id` 和 `route_intent_id` 继续补证。

## Product 验收结论

Product 接受本轮为 O6/O7 local/mock readback + PC consumer detail 增量。验收事实：

- O6 新增 dedicated schema `trashbot.o6.same_task_replay_packet_readback.v1`。
- O6 consumer detail 支持 `include=same_task_replay_packet_readback`。
- O7 新增 `trashbot.pc_tools_workstation.o7_same_task_replay_packet_readback.v1` 并默认消费/展示。
- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `path_structured_pose_count=28`
- `same_task_identity_verified=true`
- `same_task_replay_packet_ready=true`

保守拒绝：本轮不是 route execution、delivery、HIL、safe-to-control、NavigateToPose/controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、O5 production/external evidence 或 production cloud readiness。

## OKR 映射和方向判断

- O6：继续约 `93%`。新增 readback section 是有效 local/mock 消费增量，但不证明真实 production cloud、真实机器人数据、当前 live route execution、delivery record 或 operator acceptance。
- O7：继续约 `93%`。PC consumer detail 新增默认展示和 fail-closed 摘要，但不证明真实 RTC/视频、真实回放/标注数据流、当前 live route execution 或 delivery success。
- O5：继续约 `85%`。没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：继续约 `94%`。没有新增 current live HIL、safe-to-control、wheel direction、IMU/battery calibration、Nav2 route execution success 或现场 acceptance。
- 方向判断：继续 O6/O7 read-only evidence consumption；暂停 O5 support-only wrapper；KR `不归档`；主百分比不调整。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。原因：

- `same_task_replay_packet_readback` 只证明同一 packet 可被 O6/O7 安全读回和展示，不证明车跑过。
- 固定 false 字段全部保持 false：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`、`primary_actions_enabled=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`connects_cloud_production=false`。
- O5 仍缺真实 external production evidence；O1 仍缺 current live HIL / route execution / delivery acceptance。

历史记录位置：本轮证据写入本 `final.md`、`side2side_check.md`、`artifacts/product_acceptance_same_task_replay_packet_readback.json`、`OKR.md` 4.1 snapshot / O6 / O7 记录，以及 `docs/process/okr_progress_log.md` 的 2026-07-13 06:05 记录。

## 实际改动

Product closeout 新增或更新：

- `sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback/side2side_check.md`
- `sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback/final.md`
- `sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback/artifacts/product_acceptance_same_task_replay_packet_readback.json`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Implementation 已由 `full-stack-software-engineer` 完成并记录在 `tech-done.md`；Product 本轮没有修改实现代码、测试代码或接口文档。

## 验证结果

Full-stack implementation 验证证据来自 `tech-done.md`：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
Ran 185 tests in 81.295s
OK
```

```text
cd pc-tools/workstation && npm run test && npm run build && npm run lint
Test Files  3 passed (3)
Tests  491 passed (491)
vite v7.3.3 building client environment for production...
built in 1.92s
eslint .
```

Product closeout required commands passed:

```text
python3 -m json.tool .../product_acceptance_same_task_replay_packet_readback.json
# exit 0

structured assertions
product_same_task_replay_packet_readback_acceptance_ok

rg -n "2026-07-13 06:05|same-task replay packet readback|same_task_replay_packet_readback|packet_o3_28_pose_same_task_replay|route_csv_row_count=28|replay_jsonl_event_count=28|path_structured_pose_count=28|route_execution_success=false|delivery_success=false|hil_pass=false|safe_to_control=false|不归档|O6|O7" ...
# anchors found

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback
# exit 0
```

## 失败定位

Product closeout 未发现需返工的问题。Full-stack 在实现阶段已定位并修复两个偏差：

- O6 全局 unsafe gate 一度把安全 false 字段误判为危险字段，后改为 dedicated section 白名单摘要。
- O7 fixture 的 task id/source schema 一度不一致，后用专门断言覆盖 exact identity、28/28/28 counts、basename refs、sha256 prefix 和 fixed false fields。

## 剩余风险和下一步

剩余风险：

- 当前证明边界固定为 `software_proof_o6_o7_same_task_replay_packet_readback_only`。
- 本轮不证明 route execution、delivery、HIL、safe-to-control、NavigateToPose/controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART 或 O5 production/external evidence。
- O6/O7 后续要提升 OKR credit，必须消费新的 same-task route execution / delivery / HIL / production evidence。

下一步 owner/action：

- `robot-algorithm-engineer`：在安全准入明确后，用同一 `packet_id` / `route_intent_id` 收集受控 route execution record。
- `full-stack-software-engineer`：只有拿到新的 route execution / delivery / HIL / production evidence 时才继续扩展 O6/O7 consumption；不要重复 readback-only 包装。
