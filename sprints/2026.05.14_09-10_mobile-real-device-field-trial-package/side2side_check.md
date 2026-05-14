# Sprint 2026.05.14_09-10 Mobile Real Device Field Trial Package - Side-by-Side Check

## 对照结论

- sprint_type: epic
- 对照目标：为真实 iPhone/Android 或 production app 现场试跑新增 phone-safe `mobile_real_device_field_trial_package*`，并保持 Robot metadata-only 控制边界。
- 结论：Task A/B 均满足本轮验收口径；本轮可按 `software_proof_docker_mobile_real_device_field_trial_package_gate` 收口。

## 用户价值和产品北极星

- 用户价值：现场人员可以用“真实设备现场试跑包”统一记录 runtime metadata、人工 observation fields、`safe_to_control=false`、ACK 非 delivery success 和 `not_proven`，减少材料遗漏或误读。
- 产品北极星：手机仍是普通用户唯一入口；本轮只证明 Docker/local `mobile/web` 能生成 field trial package，并证明 Robot metadata-only fence 不把该 package 当作控制或送达证据。

## OKR 映射

- Objective 4：Task A 的 field trial package UI/logic/tests/docs 与 Task B 的 Robot metadata-only fence 支持 O4 从约 85% 保守上调到约 86%。
- Objective 5：仍是最低 Objective（约 68%），但本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 外部材料，因此保持不变。
- Objective 1/2/3：没有硬件、HIL、Nav2/fixed-route、task_orchestrator 或真实 delivery 新证据，因此保持不变。

## 验收对照

| 验收项 | 证据 | 结论 |
| --- | --- | --- |
| Field trial package 首屏可见并可复制 | Task A 新增 `mobile_real_device_field_trial_package*` 与“真实设备现场试跑包”panel；`mobile.test_mobile_web_entrypoint` `Ran 29 tests ... OK` | 通过 |
| Copy package phone-safe 且保持控制关闭 | Task A `rg` 覆盖 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven`、`software_proof_docker_mobile_real_device_field_trial_package_gate` | 通过 |
| 主操作 fail closed，ACK 不是 delivery success | Task A tests/docs 证明 field trial package 不启用 Start/Confirm/Cancel，ACK/package copy 只是 accepted/processing/support metadata | 通过 |
| Robot metadata-only fence 不触发控制语义 | Task B `Ran 157 tests in 80.820s OK`，证明 metadata 不触发 collect/dropoff/cancel、ACK POST、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success | 通过 |
| Product closeout 保守更新 OKR | `OKR.md` 和 `docs/process/okr_progress_log.md` 写明 O4 约 86%、O5 约 68%，Objective 1/2/3 不调整 | 通过 |

## 风险和证据边界

- 本轮是 Docker/local mobile software proof + Robot metadata-only fence，不是真实 iPhone/Android、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实 delivery。
- 真实设备现场试跑包只是 field trial handoff/support metadata；ACK、HTTP accepted、receipt、field trial package、browser proof、handoff session 和 install prompt evidence 都不是 delivery success。
