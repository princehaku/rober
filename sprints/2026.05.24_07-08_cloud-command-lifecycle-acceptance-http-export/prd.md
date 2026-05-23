# Cloud Command Lifecycle Acceptance HTTP Export PRD

Run time: 2026-05-24 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：support / field owner 可以通过一个稳定的 HTTP GET endpoint 获取 cloud command lifecycle replay acceptance packet，不需要 SSH、CLI 参数或人工翻 Docker smoke 日志。

产品北极星：云中转控制链路要让普通用户问题可解释、支持同学可复盘、现场 owner 可补证，同时控制动作保持安全关闭；support export 只能帮助 review，不能成为机器人运动或送达证明。

## 2. OKR 映射

主目标：Objective 5 云中转 + OSS/CDN 数据通路产品化。

映射 KR：

- KR1：commands/status/ack 控制面契约继续保持 HTTP/API 化，但本轮只新增 support GET export，不新增 command mutation。
- KR5：凭证和脱敏边界继续保持；payload 不得暴露 bearer token、Authorization、credential-bearing URL、DB/queue URL、本地 state path、ROS topic、hardware details 或 raw traceback。
- KR6：远程诊断 graceful degradation 增强；当 terminal result pending、ACK accepted/processing only、owner handoff 或 material pending 时，HTTP export 只给安全解释和 next required evidence。

相关目标影响：

- Objective 1：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，本轮不证明 2D LiDAR / ToF、WAVE ROVER、UART、HIL 或 vendor material。
- Objective 4：endpoint 可供 phone/support surface 后续消费，但本轮不是 true phone/browser proof。
- Objective 2 / Objective 3：本轮不改变 Nav2、route/elevator、task_orchestrator、field pass 或 delivery result。

## 3. KR 拆解或更新

本轮不更新 `OKR.md` 百分比，只定义本 sprint 的可验收 KR：

1. HTTP route KR：independent cloud relay 暴露 `GET /api/support/cloud-command-lifecycle-replay-acceptance-packet-export`，返回 `cloud_command_lifecycle_replay_acceptance_packet_http_export`。
2. 同源验收包 KR：HTTP export 必须复用 CLI export / acceptance packet 的安全语义，保留 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate` 和源 boundary。
3. Fail-closed KR：payload 必须显式包含 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、`accepted_processing_only_not_delivery_success` 或等价 ACK 语义。
4. No-side-effect KR：GET 请求不得 replay/resubmit command、post ACK、mutate cursor/state、上传材料、触发 GitHub action、控制 Nav2/机器人或写入 delivery success。
5. Fenced validation KR：只跑最小围栏验证，覆盖 route、payload markers、redaction、no state mutation 和 scoped diff；不做 broad regression。

## 4. 本轮核心抓手

把上一轮 CLI export 的安全验收包从“人工命令可导出”推进到“support HTTP API 可读取”。这比继续堆测试更接近 Objective 5 产品化，因为它让 independent cloud relay 的 support surface 具备可集成入口。

## 5. 需要做什么

`full-stack-software-engineer` 需要：

- 在 onboard relay implementation 中新增只读 GET endpoint；`cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py` 仅作为 thin wrapper，只有需要 wrapper docs marker 时才改。
- 让 endpoint 返回 phone-safe / support-safe JSON。
- 增加 targeted HTTP tests，证明 route 输出 required markers 且 GET 没有副作用。
- 同步更新 `docs/product/cloud_4g_infrastructure.md` 或相关接口说明，写清 HTTP export 是 Docker/local software proof。

`robot-software-engineer` 需要：

- 只读核对 Robot diagnostics acceptance packet safe alias 和 HTTP export 消费字段一致。
- 如发现 Robot safe alias 缺必要字段，再提出最小变更；否则返回 no-change proof。

`product-okr-owner` 需要：

- 在 sprint closeout 中核对 Objective 5 是否仍约 68%，默认 no OKR percentage lift。
- 确认 `not true phone/browser proof`、`not delivery success`、`not HIL`、`not PR #5 resolved` 在 closeout 中保持可见。

## 6. 优先级和验收口径

P0：

- HTTP GET route 可用且只读。
- payload 包含 `cloud_command_lifecycle_replay_acceptance_packet_http_export`。
- payload 包含 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate`。
- payload 保留 false-state flags 和 no OKR percentage lift 语义。

P1：

- route 对 missing / unsafe / stale source packet fail closed。
- route 不输出 raw token、Authorization header、local path、traceback、ROS topic、hardware details 或 command-control internals。
- focused tests 证明 GET 前后 cursor/state 不变。

P2：

- docs/product 同步写清 API route、证据边界和不是 true phone/browser proof。

## 7. 对应责任 Engineer

- 主责：`full-stack-software-engineer`
- 协同核对：`robot-software-engineer`
- 计划与验收：`product-okr-owner`

不需要 `hardware-engineer` 或 `autonomy-engineer` 改文件；PR #5 hardware material 和 route/elevator field pass 仍是外部证据缺口。

## 8. 风险、阻塞和需要补齐的证据链

- 缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic，所以本轮不是 O5 external proof。
- 缺真实 phone/browser run，所以本轮 not true phone/browser proof。
- 缺 verified terminal delivery/dropoff/cancel result，所以本轮 not delivery success。
- 缺 Nav2/fixed-route runtime、route/elevator field pass、WAVE ROVER/UART/HIL，所以不能影响 Objectives 1/2/3 的真实闭环。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，不能被 HTTP export 关闭。

## 9. 本轮不做

- 不加 POST/PUT/PATCH/DELETE。
- 不加 replay/resubmit。
- 不 post ACK。
- 不 mutate cursor/state。
- 不上传材料。
- 不触发 GitHub action。
- 不改 Nav2、机器人控制、HIL 或 delivery success。
- 不更新 `OKR.md` 百分比，除非后续真实外部证据出现。
