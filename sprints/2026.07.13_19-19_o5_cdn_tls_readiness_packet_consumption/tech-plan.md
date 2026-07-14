# Tech Plan - O5 CDN/TLS Readiness Packet Consumption

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低完成度 Objective 是 O5，约 `85%`。
2. 本 sprint 针对最低 Objective：是，直接针对 O5 production/cloud evidence readiness。
3. 非重复理由：13:13 已经真实 probe 并 blocked 在 `blocked_http_status_not_success_class`；本轮不重跑同一 probe，而是让 O5 production cutover readiness packet 消费该 sanitized external evidence artifact。

## Owner Routing

主责 owner：`robot-software-engineer`。

理由：改动位于 cloud relay / preflight / readiness packet 合同和 Python unit tests，不涉及 WAVE ROVER、ESP32、UART、电压、引脚、机械尺寸或真实运动控制。

## File Scope

允许改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/interfaces/o5_cdn_tls_external_evidence_probe.md`
- `sprints/2026.07.13_19-19_o5_cdn_tls_readiness_packet_consumption/tech-done.md`

禁止改：

- 硬件/vendor 文件。
- WAVE ROVER/UART 配置。
- ROS2 launch、`/cmd_vel`、`/api/base/manual`、NavigateToPose。
- O7 workstation bundle export 文件。
- 历史 sprint 文件，除非只读取 13:13 artifact 作为测试 fixture 事实。

## Implementation Notes

- 新增常量：schema、env var、evidence boundary/proof boundary。
- 新增 `cdn_tls_external_evidence_summary(artifact_path)` 或等价 helper。
- 将 source tuple 加入 `_cloud_production_cutover_readiness_sources()`。
- CLI args/preflight env path 要与现有 pattern 一致。
- Summary 对 `accepted_claim=none` 或 `http_status_class=4xx` 应返回 `ok=false` 或让 readiness section `blocked_not_proven`，但要保留安全 counts/blocked reason。
- 如果未来 `accepted_claim=o5_cdn_tls_external_evidence_delta` 且 HTTP class 为 2xx/3xx，也只能让 section software proof ready；packet 仍必须 `production_ready=false`、`okr_credit_allowed=false`。

## Acceptance Commands

子 agent 必须运行并记录结果：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
python3 -m json.tool sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/artifacts/cdn_tls_external_evidence_summary.json >/dev/null
rg -n "cdn_tls_external_evidence|TRASHBOT_REMOTE_CLOUD_CDN_TLS_EXTERNAL_EVIDENCE_ARTIFACT|blocked_http_status_not_success_class|software_proof_o5_cdn_tls_external_evidence_readiness_packet_consumption_only|safe_to_control=false|delivery_success=false" onboard/src/ros2_trashbot_behavior docs sprints/2026.07.13_19-19_o5_cdn_tls_readiness_packet_consumption/tech-done.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/cloud_4g_infrastructure.md docs/interfaces/o5_cdn_tls_external_evidence_probe.md sprints/2026.07.13_19-19_o5_cdn_tls_readiness_packet_consumption
```

## Risks

- Consuming the 4xx artifact must not be mistaken for production readiness.
- Full URL/path/token/body/header/traceback/local path redaction remains mandatory.
- This sprint should not change OKR percentages by itself; Product closeout decides after evidence review.
