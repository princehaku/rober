# O5/O6 Cloud Terminal Result Delivery Bridge Tech Plan

## Sprint 类型

sprint_type: epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 active Objective：O5、O6、O7，并列约 80%。
2. 本 sprint 是否针对最低 Objective：是。主抓 O5 cloud command terminal result，同时把结果接入 O6/O7 delivery result evidence 读模型。
3. 选择理由：最近两轮 O6/O7 都完成但都提醒下一轮转向 production cloud 或 delivery record/operator confirmation。本轮不继续做 decoder/wrapper，而是把已有 O5 robot-facing terminal result 主路径作为 O6/O7 delivery result evidence 来源。

## 最近两轮 final 核对

- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/final.md`：完成，未 blocked；下一轮建议不要继续只补 decoder。
- `sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/final.md`：完成，未 blocked；下一轮建议优先 production cloud、live route execution 或 delivery record/operator confirmation。

结论：本轮不重复消费同一 blocker；同时避免继续堆叠 summary wrapper。

## 技术方案

### Task A - Algorithm Bridge

Owner：`robot-algorithm-engineer`

职责：

- 在 `onboard/scripts/field_route_evidence_manifest.py` 增加可选输入 `--cloud-terminal-result-json`。
- 读取 schema `trashbot.cloud_command_terminal_result.v1`，转换成既有 `trashbot.delivery_result_evidence.v1`。
- source 固定为 `cloud_command_terminal_result`，source_schema 固定保留云端终态 schema。
- `terminal_result_type in {delivery_terminal, dropoff_terminal}` 且 `result_code/task_terminal_state` 表达完成时，可设置 `delivery_result_claimed=true`；但 `delivery_success` 仍必须为 false。
- `task_record_ref` / `evidence_ref` 只能作为 safe refs 或安全摘要，不得输出路径、URL、token、raw/base64。
- 输入缺失时仍沿用现有 `--delivery-result-json` 缺失 blocked 行为；两种输入同时提供时优先 `--delivery-result-json`，并在文档中说明。

允许改动范围：

- `/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py`
- `/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py`
- `/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md`
- `/Users/m1/apps/rober/sprints/2026.07.10_02-06_o5_o6_cloud_terminal_result_delivery_bridge/artifacts/algorithm_worker_report.md`

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

### Task B - O6 Readback Contract

Owner：`robot-software-engineer`

职责：

- 在 O6 tests 中增加 fixture：field evidence / artifact bundle 携带 Algorithm 输出的 `delivery_result_evidence`，其中 `source_schema=trashbot.cloud_command_terminal_result.v1`。
- 确认 archive detail、consumer detail 和 `include=delivery_result_evidence` 均保留该来源，并继续固定四个危险 false 字段。
- 如现有代码已满足，只补测试和接口文档；如不满足，在 `remote_cloud_relay.py` 做最小 additive 修复。

允许改动范围：

- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`
- `/Users/m1/apps/rober/sprints/2026.07.10_02-06_o5_o6_cloud_terminal_result_delivery_bridge/artifacts/o6_worker_report.md`

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

## 最终验收

```bash
git diff --check
rg -n "cloud_terminal_result|cloud_command_terminal_result|software_proof_cloud_terminal_result_delivery_bridge_only|trashbot.cloud_command_terminal_result.v1|delivery_result_evidence" sprints/2026.07.10_02-06_o5_o6_cloud_terminal_result_delivery_bridge docs/navigation/field_route_evidence_manifest.md docs/interfaces/o6_cloud_archive_api.md OKR.md docs/process/okr_progress_log.md
```

## 风险和边界

- 本轮不证明真实 production cloud、真实公网 HTTPS/TLS、4G/SIM、production DB/queue 或 OSS/CDN live traffic。
- 本轮不证明真实 live Nav2 route execution、真实 delivery record、真实 operator confirmation 媒体、真实 robot motion 或真实 delivery success。
- 如果 cloud terminal result 内含路径、URL、token、raw/base64 或 dangerous true，必须 fail-closed。
