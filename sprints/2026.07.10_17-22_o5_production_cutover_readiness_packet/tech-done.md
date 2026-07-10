# O5 Production Cutover Readiness Packet Tech Done

- sprint_type: epic
- owner: robot-software-engineer
- proof_boundary: `software_proof_cloud_production_cutover_readiness_packet_only`
- OKR credit: `okr_credit_allowed=false`

## 实际改动

- 在 `remote_cloud_relay.py` 新增 `trashbot.cloud_production_cutover_readiness_packet.v1` 合同，聚合 cloud deployment readiness、cloud external probe、public ingress/TLS、DB/queue external probe、worker migration rehearsal、worker cutover drain、OSS/CDN live probe 和 external evidence intake 的现有 summary。
- 新增 `--write-cloud-production-cutover-readiness-packet-artifact <packet.json>` CLI 写出，以及 `--preflight --cloud-production-cutover-readiness-packet-artifact <packet.json>` 消费入口。
- Packet 只输出短状态、counts、safe basename、`sha256` 短前缀、blocked reasons、next required evidence、`next_live_command` 和 gate 字段；固定 `production_ready=false`、`okr_credit_allowed=false`、`support_only_reason=no_real_production_external_evidence`、`proof_scope_class=software_proof_support_only`。
- 对 unsafe URL/path/token/raw/base64/traceback、危险 true、task mismatch、缺关键字段 fail-closed，不回显 artifact 路径、URL、凭证、响应体、串口、ROS topic 或 `/cmd_vel`。
- 更新 `docs/product/cloud_4g_infrastructure.md` 和 `docs/interfaces/o6_cloud_archive_api.md`，明确该 packet 是 O5 preflight/CLI 只读合同，不是 O6 archive task section。

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`：通过，无输出。
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`：通过，`Ran 179 tests in 74.465s`，`OK`。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/cloud_4g_infrastructure.md docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet`：通过，无输出。

## 剩余风险

- 本轮没有真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker cutover、OSS/CDN live traffic 或真实手机/browser 材料，因此不提升 O5 OKR credit。
- Packet 只能证明 cutover readiness 合同、CLI 写出和 preflight readback 可用；不证明 production cloud connected、delivery success、robot safe-to-control 或生产切换完成。
- 下一轮若要提升 O5，需要提交真实外部材料：公网 HTTPS/TLS 外部探测、4G/SIM 链路、production DB/queue probe、worker cutover/drain 日志、OSS/CDN live traffic 和手机/browser 验收证据。
