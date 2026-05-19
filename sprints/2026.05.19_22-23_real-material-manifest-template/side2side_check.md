# Sprint 2026.05.19_22-23 Real Material Manifest Template - Side2Side Check

## 1. 验收对照结论

本轮 Product 验收通过，但只通过 `software_proof_docker_real_material_manifest_template_gate`。它证明 repo 内 manifest template / Robot diagnostics / mobile read-only 展示链路可以 fail closed 地表达“需要哪些真实材料”，不证明任何真实材料已经到位。

## 2. PRD / Tech Plan 对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 覆盖 Objective 5 external material template | 通过 | `real_material_manifest_template` / `template_groups` 覆盖 O5 external，保留 `not_proven`。 |
| 覆盖 Objective 1 / PR #5 hardware material template | 通过 | Template 包含 O1 / PR #5 hardware material group，并保留 `PRRT_kwDOSWB9286CJ3tX` unresolved / `blocked_pending_real_materials`。 |
| 覆盖 PR #4 route/elevator material template | 通过 | Template 包含 Nav2/fixed-route、route completion、field task record、elevator door state、target floor confirmation、human assistance record、dropoff/cancel material 和 delivery_result。 |
| 覆盖 Objective 4 real phone material template | 通过 | mobile/web 只读展示真实手机 / production app / PWA prompt / phone-browser acceptance 的材料需求，不改变主操作 gating。 |
| Robot 只读 diagnostics safe alias | 通过 | `real_material_manifest_template` safe alias 兼容 `manifest_template` / `template_groups` / `required_item_templates`，保持 fail closed。 |
| Evidence boundary | 通过 | 全链路保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。 |

## 3. 用户价值核对

- 现场 owner 现在可以从 template groups 看到每类真实材料应提交什么。
- Product 可以把 O5 external、O1 / PR #5 hardware、PR #4 route/elevator、O4 real phone 的材料缺口统一路由到后续 intake / review decision。
- Engineer / Reviewer 可以用同一 safe evidence ref 和 fail-closed fields 判断下一步是否能进入真实材料 review。
- 普通手机用户体验没有被误开控制入口；mobile/web 仍只读展示，不提供新的 Start/Confirm/Cancel 权限。

## 4. 不能验收为完成的事项

- 不能验收为真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。
- 不能验收为真实 WAVE ROVER/UART/HIL、真实反馈包、真实 `/odom`、`/imu/data`、`/battery` 或 PR #5 真实 2D LiDAR / ToF material。
- 不能验收为 PR #4 route/elevator field pass、真实 Nav2/fixed-route、真实电梯、真实 dropoff/cancel completion 或 delivery success。
- 不能验收为真实手机设备、production app、PWA prompt/user choice 或 true phone/browser acceptance。

## 5. Product 判断

本轮是有效的 closeout：它把上一轮 `real_material_evidence_intake` 的“材料缺口可记录”推进到“现场 owner 有统一模板可回填”。OKR 百分比不提升，仍保持 O5 约 68%、O1 约 81%、O2/O3/O4 约 99%。
