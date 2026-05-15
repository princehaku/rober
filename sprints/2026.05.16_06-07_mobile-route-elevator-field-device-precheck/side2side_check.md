# Sprint 2026.05.16_06-07 Mobile Route Elevator Field Device Precheck - Side2Side Check

sprint_type: epic

## 1. 对照结论

本轮 PRD 要求把 current `mobile/web` 入口、route/elevator handoff summary、真实设备/PWA observation checklist 和现场材料清单收敛成 `mobile_route_elevator_field_device_precheck`，并保持 phone-safe、whitelist-only、metadata-only、fail-closed。

对照 A/B/C 结果：要求已满足。mobile 首屏可见 precheck panel 并支持 whitelist copy/export；Robot diagnostics 有 metadata-only gate；pc-tools 有 helper/gate 校验 schema、boundary、same-evidence-ref、route/elevator required materials、device/PWA checklist 和 unsafe/success claim。Start / Confirm Dropoff / Cancel gating 未改变。

## 2. 用户价值核对

用户价值从“看见 handoff browser proof”推进到“真实设备/现场前可按手机导出检查清单”。现场操作者现在能围绕同一 `evidence_ref` 准备真实设备、PWA prompt/user choice、route/elevator materials、Nav2/fixed-route runtime log、dropoff/cancel completion 和 delivery result 的后续回填。

仍不把 precheck 当成业务完成：它只说明材料入口和边界已统一，不证明真实路线、电梯、手机、投放或 delivery success。

## 3. OKR 对照

- Objective 4：可保守上调到约 77%。理由是首屏 precheck/export 入口已落地，并由 Robot diagnostics 与 pc-tools 围栏支撑真实设备验收前流程。
- Objective 2：保持约 76%。本轮只列出 route/elevator field materials 和 same-evidence-ref 采集要求，没有真实电梯、真实 dropoff/cancel completion 或 delivery success。
- Objective 3：保持约 76%。本轮只形成 pre-field checklist，没有真实 Nav2/fixed-route runtime log、真实路线采集或 completion signal。
- Objective 5：保持约 66%。本轮 not real Objective 5 external proof；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
- Objective 1：保持约 73%。本轮未触碰 WAVE ROVER、UART、Orange Pi、真实串口、`T=1001` feedback 或 HIL。

## 4. 验收口径核对

通过项：

- `mobile_route_elevator_field_device_precheck` 首屏 panel 已实现。
- copy/export 是 whitelist-only。
- `delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 保持可见。
- Robot diagnostics metadata-only gate 已实现，precheck metadata 不进入 command、ACK、control、Nav2、HIL、dropoff/cancel completion 或 delivery success。
- pc-tools helper/gate 已实现并 fail-closed。
- `docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md`、`docs/navigation/fixed_route_workflow.md`、`pc-tools/README.md` 已由 A/B/C 同步更新。

未通过但符合边界的项：

- 未做真实手机 / 真实 iPhone/Android device behavior 验收。
- 未做 production app 或真实 PWA prompt/user choice 验收。
- 未做真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion 或真实 delivery success。
- 未做 WAVE ROVER、真实串口/UART 或 HIL。
- 未做 Objective 5 外部材料验证。

## 5. 收口判断

本 sprint 可按 `software_proof_docker_mobile_route_elevator_field_device_precheck_gate` 收口。下一步应使用该 precheck 去采集真实设备/PWA 或 route/elevator field materials，而不是继续堆本地 metadata。

