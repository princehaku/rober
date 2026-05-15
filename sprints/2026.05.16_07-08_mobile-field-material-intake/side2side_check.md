# Sprint 2026.05.16_07-08 Mobile Field Material Intake - Side2Side Check

sprint_type: epic

## 1. 验收对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 手机首屏可见 `mobile_field_material_intake` | 通过 | Task A 更新 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、fixture 和 mobile entrypoint test；`mobile/test_mobile_web_entrypoint.py` Ran 49 tests OK。 |
| whitelist-only copy/export | 通过 | Task A copy/export 仅输出 safe entry/evidence_ref、真实设备/PWA checklist、route/elevator field materials、same-evidence-ref status、`not_proven` 和 `delivery_success=false`。 |
| Start / Confirm Dropoff / Cancel gating 未改 | 通过 | Task A 明确保持原 gating；Task B 不把 intake metadata 接入 command、ACK、control、cursor、persistence、terminal ACK、Nav2、HIL、dropoff/cancel 或 delivery success。 |
| Robot diagnostics metadata-only consumer | 通过 | Task B 新增 `mobile_field_material_intake` / `_summary` consumer，并对 bad JSON/missing/unsupported/unsafe/success claim fail closed；diagnostics unittest Ran 87 tests OK。 |
| pc-tools fail-closed intake/gate | 通过 | Task C 新增 `pc-tools/evidence/mobile_field_material_intake.py` 和 tests，覆盖同一 safe `evidence_ref` 下的真实设备/PWA observation、route/elevator materials、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel material status；unittest Ran 5 tests OK。 |
| 文档同步 | 通过 | 已同步 `docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md`、`docs/navigation/fixed_route_workflow.md`、`pc-tools/README.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。 |

## 2. OKR 最低优先级核对

当前 `OKR.md` 4.1 数值最低仍是 Objective 5，约 66%。本 sprint 不针对 Objective 5；理由仍成立：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration 或其他真实外部 O5 材料，继续做本地 O5 metadata 会重复消费 blocker。

本轮主目标是 Objective 4。`mobile_field_material_intake` 把 06-07 precheck 推进为手机端真实材料 intake 入口，并由 Robot diagnostics 与 pc-tools gate 做 metadata-only / fail-closed 支撑。Objective 2/3 仅获得 same-evidence-ref 现场材料摄取支撑，不足以上调。

## 3. 证据边界复核

本轮边界固定为 `software_proof_docker_mobile_field_material_intake_gate`。

不证明：

- 真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- 真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion 或 delivery success。
- WAVE ROVER、真实 UART/串口、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery`。
- Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration。

## 4. 结论

验收通过。Objective 4 可保守从约 77% 上调到约 78%；Objective 1、2、3、5 不上调。下一步应使用本轮 intake/gate 去采集真实手机/PWA 或 route/elevator 现场材料，而不是继续追加本地 O5 metadata。
