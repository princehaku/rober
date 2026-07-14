# Tech Plan - O5 Command Lifecycle CLI Export Refresh

- sprint_type: epic
- Sprint: `sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/`
- Implementation owner: `robot-software-engineer`
- Product owner: `product-okr-owner`
- Proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低 Objective：Objective 5，约 `85%`。
2. 本 sprint 针对该最低 Objective：是。
3. 本轮不直接追求百分比提升，因为 success-class production/cloud evidence、真实 phone/browser、4G/SIM、production DB/queue、worker cutover 与 OSS/CDN live traffic 不在当前环境中可用；本轮只刷新一个不重复最近 support wrapper 的 O5 command lifecycle CLI export artifact。

## 实施范围

允许改动：

- `sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/tech-done.md`
- `sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/artifacts/o5_command_lifecycle_cli_export.json`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`

只读参考：

- `AGENTS.md`
- `OKR.md`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck/final.md`

## 实施步骤

1. 使用现有 `remote_cloud_relay.py --write-cloud-command-lifecycle-replay-acceptance-packet-cli-export` 生成 sprint artifact。
2. 更新最小产品文档，标记 2026-07-14 fresh CLI export refresh 边界和不可计分口径。
3. 创建 `tech-done.md`，记录实际改动、验证结果、失败定位和剩余风险。
4. 所有 wording 必须保持 support-only，不得写成 delivery/operator acceptance、route execution、production cloud 或 safe-to-control。

## 验收命令

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay -k cloud_command_lifecycle_replay_acceptance_packet_http_export
python3 onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py --write-cloud-command-lifecycle-replay-acceptance-packet-cli-export sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/artifacts/o5_command_lifecycle_cli_export.json
python3 -m json.tool sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/artifacts/o5_command_lifecycle_cli_export.json >/dev/null
python3 - <<'PY'
import json
from pathlib import Path
p = Path("sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/artifacts/o5_command_lifecycle_cli_export.json")
data = json.loads(p.read_text())
assert data["schema"] == "trashbot.cloud_command_lifecycle_replay_acceptance_packet_cli_export.v1"
assert data["evidence_boundary"] == "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate"
assert data["artifact_status"] == "export_ready_for_field_owner_review_not_proven"
for key in ("delivery_success", "primary_actions_enabled", "safe_to_control"):
    assert data[key] is False
source = data["source_packet"]
for key in ("ack_post_allowed", "cursor_updates_allowed", "persistence_updates_allowed", "command_replay_allowed", "command_resubmit_allowed", "material_upload_allowed", "review_action_allowed", "github_action_allowed", "robot_command_side_effects_allowed", "nav2_triggered", "hil_pass"):
    assert source[key] is False
encoded = json.dumps(data, ensure_ascii=False).lower()
for forbidden in ("authorization", "bearer", "token", "raw_command", "command_payload", "checksum", "local_path", "serial", "uart", "wave_rover", "ros_topic", "cmd_vel", "traceback"):
    assert forbidden not in encoded
print("o5_command_lifecycle_cli_export_acceptance_ok")
PY
rg -n 'cloud_command_lifecycle_replay_acceptance_packet_cli_export|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate|export_ready_for_field_owner_review_not_proven|accepted_processing_only_not_delivery_success|terminal_result_pending|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|不归档|O5.*85' docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh
git diff --check -- docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh
```

## 风险

- 本轮不连接真实公网、生产 DB/queue、OSS/CDN、4G/SIM 或真实手机/browser。
- 本轮不读取或修改 relay command/status/ACK state，不触发 robot control。
- OKR closeout 必须保持 O5 flat，且写明下一步只接受 success-class production/cloud evidence 或 explicit same-window live route/HIL/delivery/operator evidence。
