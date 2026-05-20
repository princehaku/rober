# Sprint 2026.05.20_12-13 Field Evidence Rerun Material Dispatch - Side2Side Check

## 1. 验收口径对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| PC gate 输出现场证据复跑材料派发包 | 通过 | `trashbot.field_evidence_rerun_material_dispatch.v1` 和 summary schema 已实现，覆盖 required material groups、owner work orders、rerun commands、callback packet requirements 和 same safe `evidence_ref`。 |
| Robot diagnostics 只读消费 | 通过 | `robot_diagnostics_field_evidence_rerun_material_dispatch_summary` 已支持 explicit ref、top-level、nested、status diagnostics 和 diagnostics nested summary；fail-closed default。 |
| mobile/web 普通用户只读展示 | 通过 | “现场证据复跑材料派发”panel 只展示 safe summary，不 fetch raw artifact，主操作 gating 不变。 |
| 固定安全状态保留 | 通过 | `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 保留在 PC / Robot / mobile / closeout 文档口径中。 |
| OKR 不虚增 | 通过 | Objective 5 仍约 68%，Objective 1 仍约 81%；O2/O3/O4 仅记录 software-proof dispatch package，不写真实 field pass。 |
| PR #5 thread 状态不误关 | 通过 | `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending；本 sprint 不解决真实 2D LiDAR / ToF 材料。 |

## 2. 用户价值核对

本轮把“现场 owner 还缺哪些真实材料”从分散的 handoff/review 状态，收束为一个可执行派发包：谁负责、缺什么、如何 rerun、补完后怎样提交 callback packet。对普通手机用户和支持同学的价值是：mobile/web 只显示安全下一步，不把本地 metadata、ACK、review handoff 或 fixture 当成真实送达。

## 3. Forbidden Claims 核对

本轮没有声明：

- 真实 route/elevator field pass。
- 真实 dropoff/cancel completion 或 delivery success。
- HIL、真实 WAVE ROVER/UART、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`。
- Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。
- 真实手机/browser、production app、真实 PWA prompt/userChoice。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved。

## 4. 仍需补齐的证据链

- 现场 owner 需要按派发包提交同一 safe `evidence_ref` 的真实 route completion signal、field task record、Nav2/fixed-route runtime log、电梯门/楼层/人工协助 summaries、dropoff/cancel completion、delivery result 和真实手机/browser evidence。
- Hardware owner 仍需 PR #5 `PRRT_kwDOSWB9286CJ3tX` 对应真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- Cloud/O5 owner 仍需真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 external proof。
