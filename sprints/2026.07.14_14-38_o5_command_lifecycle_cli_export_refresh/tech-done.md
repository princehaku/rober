# Tech Done - O5 Command Lifecycle CLI Export Refresh

- sprint_type: epic
- Sprint: `sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/`
- Implementation owner: `robot-software-engineer`
- Completion time: 2026-07-14 14:43 CST
- Corrected revalidation time: 2026-07-14 14:48 CST
- Proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`
- Acceptance status: `artifact_refreshed_corrected_validation_passed_support_only`

## 实际改动

- 生成 `sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/artifacts/o5_command_lifecycle_cli_export.json`。
- 更新 `docs/product/remote_4g_mvp.md`，补充本轮 O5 CLI export refresh 的 support-only 产品边界。
- 更新 `docs/product/cloud_4g_infrastructure.md`，补充本轮 CLI artifact、schema、false flags 和 OKR flat 口径。
- 未修改 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 或 `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`。

## 实现内容

现有 CLI 成功写出 fresh artifact：

- schema: `trashbot.cloud_command_lifecycle_replay_acceptance_packet_cli_export.v1`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_cli_export`
- evidence boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`
- artifact status: `export_ready_for_field_owner_review_not_proven`
- ACK/result wording: `accepted_processing_only_not_delivery_success` / `terminal_result_pending`
- fixed false fields: `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`

本轮只证明 support/field-owner review 用 phone-safe JSON 仍可由 relay CLI 生成。O5 仍约 `85%`，本轮 `不归档`，不声明 production cloud、delivery success、route execution、HIL、safe-to-control、真实 phone/browser 或机器人控制。

## 验证结果

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
exit 0
```

```text
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay -k cloud_command_lifecycle_replay_acceptance_packet_http_export
..
Ran 2 tests in 1.060s
OK
exit 0
```

```text
python3 onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py --write-cloud-command-lifecycle-replay-acceptance-packet-cli-export sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/artifacts/o5_command_lifecycle_cli_export.json
exit 0
generated_at=2026-07-14T06:48:00Z
artifact_status=export_ready_for_field_owner_review_not_proven
delivery_success=false
primary_actions_enabled=false
safe_to_control=false
```

```text
python3 -m json.tool sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/artifacts/o5_command_lifecycle_cli_export.json >/dev/null
exit 0
```

```text
python3 - <<'PY' ... corrected artifact assertion
o5_command_lifecycle_cli_export_acceptance_ok
exit 0
```

```text
rg -n 'cloud_command_lifecycle_replay_acceptance_packet_cli_export|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate|export_ready_for_field_owner_review_not_proven|accepted_processing_only_not_delivery_success|terminal_result_pending|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|不归档|O5.*85' docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh
exit 0
required anchors found in product docs, sprint docs, and artifact
```

```text
git diff --check -- docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh
exit 0
```

## 失败定位

无。Product owner 已修正验收脚本后，完整验证通过。为遵守本轮窄修范围，未修改产品代码或测试。

## 剩余风险

- 本轮没有连接真实公网、production DB/queue、OSS/CDN、4G/SIM 或真实 phone/browser。
- 本轮没有触发 `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART 或任何 robot control。
- 本轮不证明 route execution、delivery/operator acceptance、HIL、safe-to-control 或 production cloud。
- 本轮无需 Product、Hardware、Autonomy 或 Full-Stack 继续协同；下一步只有在出现 success-class production/cloud evidence 或 explicit same-window live route/HIL/delivery/operator evidence 后才应提升 OKR 口径。
