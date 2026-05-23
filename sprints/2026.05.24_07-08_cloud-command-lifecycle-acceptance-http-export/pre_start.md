# Cloud Command Lifecycle Acceptance HTTP Export Pre Start

Run time: 2026-05-24 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 背景证据

- 当前 `OKR.md` 4.1 显示 Objective 5：云中转 + OSS/CDN 数据通路产品化约 68%，是当前最低 Objective。
- 最近 sprint `sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/final.md` 已完成 `cloud_command_lifecycle_replay_acceptance_packet_cli_export`，但它仍只是不启动 HTTP server 的 support/field-owner metadata。
- GitHub PR #5 live review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；PR #7 open 但无 review threads。
- 本机只有 Docker；本轮不得把 Docker/local support API 证明写成真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、true phone/browser proof、HIL、Nav2/fixed-route runtime pass 或 delivery success。

## 用户价值和产品北极星

用户价值：支持同学和 field owner 不需要启动 relay 服务外的手工 CLI，也能通过 independent cloud relay 的只读 HTTP API 拉取同一份安全验收包，用于 review / support handoff / field-owner follow-up。

产品北极星：普通手机用户的云端控制链路必须可支持、可解释、可复盘，同时任何未证明的机器人控制、ACK、cursor、materials、GitHub 或 delivery 成功都保持 fail-closed。

## 本轮目标

方向：`cloud_command_lifecycle_replay_acceptance_packet_http_export`

把 CLI export 同一份安全验收包接到 independent cloud relay 的只读 HTTP API，例如：

```text
GET /api/support/cloud-command-lifecycle-replay-acceptance-packet-export
```

目标 evidence boundary：

```text
software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate
```

## 范围边界

允许做：

- 新增只读 HTTP GET route，返回与 CLI export 同源、同语义、同 false-state flags 的安全验收包。
- 返回 phone-safe / support-safe JSON，保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 复用上一轮 CLI export 的安全字段、safe copy、owner handoff、next required evidence 和 boundary markers。
- 用 fenced tests 验证 route 存在、payload markers、unsafe token redaction 和 no side effects。

明确禁止：

- replay/resubmit command。
- post ACK。
- mutate cursor/state。
- 上传材料。
- GitHub action。
- Nav2、机器人控制、HIL、route/elevator field pass 或 delivery success。
- 把结果写成 not true phone/browser proof 之外的真实手机/browser 证明。
- 因本轮软件证明给 `OKR.md` 做 percentage lift；本轮默认 no OKR percentage lift。

## Owner 分工

- `full-stack-software-engineer`：主责实现 independent cloud relay 只读 HTTP GET route、HTTP-focused fenced tests、接口文档同步。
- `robot-software-engineer`：只读核对 Robot diagnostics / acceptance packet safe alias 是否仍满足 HTTP export 消费边界；如无需改动，返回 no-change 证据。
- `product-okr-owner`：维护本 sprint 留档、验收口径、OKR 最低优先级核对、最终 closeout；实现完成后确认是否仍 no OKR percentage lift。

## 需要创建或更新的 sprint 文档

本轮是 Epic sprint，必须完整走：

- `sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/pre_start.md`
- `sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/prd.md`
- `sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/tech-plan.md`
- `sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/tech-done.md`
- `sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/side2side_check.md`
- `sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/final.md`

## 启动风险

- O5 仍缺真实外部证据，本轮只能推进 Docker/local HTTP support API 形态。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / hardware_material_pending，不能借 O5 HTTP export 关闭 O1 hardware material 缺口。
- 如果 HTTP route 复用了现有 relay state，必须证明 GET 不改变 ACK cursor、command queue、state file 或 material status。
- 如果实现需要 bearer auth，可做；不要求 bearer auth也可以，但 route 必须只读、phone-safe、fail-closed。
