# 2026-07-14 03:29 O7 Mission Bundle Terminal Material Export

## Sprint Type

- `sprint_type: epic`
- 主责 owner：`full-stack-software-engineer`
- 目标 Objective：O7 用户触点与 O6 evidence bundle 消费一致性

## 上轮状态

- `sprints/2026.07.14_01-24_o6_o7_bounded_route_terminal_result_intake/final.md` 已接受 O6/O7 selected-task bounded route terminal-result material local/mock intake/readback。
- O5 仍是当前 `OKR.md` 完成度最低 Objective，约 `85%`，但缺口仍是真实公网 HTTPS/TLS success-class、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 和真实 phone/browser 证据。
- 本轮不继续做 O5 本地包装或 CDN/TLS wrapper，避免重复消费 `blocked_http_status_not_success_class` / 无 production evidence 的同一根因。

## 本轮目标

- 让 O7 mission evidence bundle export 在读取 selected O6 detail 时，把已经纳入 detail include 的 `bounded_route_execution_gate_material` 与 `bounded_route_terminal_result_material` 纳入 section summary 与 material count。
- 保持 proof boundary 为 `software_proof_o7_o6_mission_evidence_bundle_export_only`，并继续固定 `safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`robot_control_executed=false`。
- 同步 workstation 接口/产品文档，避免 UI/文档把 terminal result receipt 错解为真实路线执行、送达或 HIL。

## 风险边界

- 本轮只处理 O7 本机 loopback selected-task export 聚合，不连接 production cloud、不触发机器人运动、不访问真实 UART/WAVE ROVER、不生成真实 dataset export。
- 本轮 OKR 百分比预期保持 flat；它是避免最新 material 被 bundle export 漏计的合同修正，不是 O5/O7 真实生产或现场证据。
