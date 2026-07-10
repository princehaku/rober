# O5 Production Cutover Readiness Packet Side-to-side Check

## sprint_type

sprint_type: epic

## 用户价值和产品北极星

产品北极星仍是让普通手机用户可以安全、可验证地把垃圾交给小车并完成送达。O5 的用户价值不是多一个本地 probe，而是让上线生产云前的缺口能被同一个 readiness packet 明确表达：公网入口、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实手机/browser 证据分别处于什么状态，下一条 live 命令应该跑什么。

本轮实现的价值是把这些 production cutover readiness 信息聚合成 `trashbot.cloud_production_cutover_readiness_packet.v1`，并通过 CLI 写出和 preflight 消费验证可读、可脱敏、可 fail-closed。它不是 production success，也不是 delivery success。

## OKR 映射和方向判断

- Objective：O5 云中转控制面产品化。
- 方向判断：继续 O5，但本轮不加 OKR credit。
- 结论：`okr_credit_allowed=false`，O5 保持约 85%，不归档 KR。
- 原因：本轮只消费既有 software-proof/readiness summary，没有接入真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 或真实手机/browser 证据。

## Side-to-side 对照

| 验收项 | 计划口径 | 实际结果 | Product 判定 |
| --- | --- | --- | --- |
| readiness packet 合同 | 建立 O5 production cutover readiness packet/readback | 已新增 `trashbot.cloud_production_cutover_readiness_packet.v1` | 通过 |
| CLI 写出 | 支持写出 readiness artifact | 已新增 `--write-cloud-production-cutover-readiness-packet-artifact` | 通过 |
| preflight 消费 | 支持后续 preflight 读取 packet artifact | 已新增 `--cloud-production-cutover-readiness-packet-artifact` | 通过 |
| OKR gate | 无真实外部材料时必须 `okr_credit_allowed=false` | 固定 `okr_credit_allowed=false`、`support_only_reason=no_real_production_external_evidence` | 通过 |
| next command | 输出下一条可执行生产/现场命令方向 | packet 输出 `next_live_command` | 通过 |
| false safety flags | 不得打开 delivery/control/production success | 固定 `production_ready=false`、不宣称 delivery/control success | 通过 |
| 脱敏与 fail-closed | 不回显 URL、token、DB/queue endpoint、路径、raw body、traceback | worker report 记录 unsafe URL/path/token/raw/base64/traceback、dangerous true、task mismatch、缺关键字段 fail-closed | 通过 |

## 验证证据

- Robot Software：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 通过。
- Robot Software：`python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` 输出 `Ran 179 tests in 74.465s` 和 `OK`。
- Robot Software：scoped `git diff --check` 通过。

## Proof Boundary

本轮 proof boundary 是 `software_proof_cloud_production_cutover_readiness_packet_only`。

本轮只证明 O5 cloud production cutover readiness packet 的软件合同、CLI 写出、preflight 消费、support-only gate 和脱敏/fail-closed 规则可用。

明确不证明：

- 真实公网 HTTPS/TLS。
- 真实 4G/SIM。
- production DB/queue。
- production worker/cutover。
- OSS/CDN live traffic。
- 真实手机/browser。
- 真实 production cutover。
- 真实 delivery success。

## 下一轮建议

O5 只有接入真实 external production evidence（HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser）才可考虑 OKR 增量。若这些材料仍不可得，下一轮应转 O1 current same-run HIL，或转 O6/O7 live route/delivery/operator/production readback，避免继续用 support-only packet 包装 OKR 进度。
