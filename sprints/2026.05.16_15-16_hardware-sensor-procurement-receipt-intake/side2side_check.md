# Sprint 2026.05.16_15-16 Hardware Sensor Procurement Receipt Intake - Side2Side Check

sprint_type: epic

## 1. PRD / Tech Plan 对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| PC gate 新增 receipt intake artifact / summary | 通过 | Task A 新增 `trashbot.hardware_sensor_procurement_receipt_intake.v1`、`trashbot.hardware_sensor_procurement_receipt_intake_summary.v1` 和 `software_proof_docker_hardware_sensor_procurement_receipt_intake_gate`。 |
| 能接收 receipt/source/vendor/SKU/cost/install/wiring/power/calibration/HIL-entry redacted materials | 通过 | Task A 输出 accepted / missing / rejected materials、next_required_evidence 和 owner_handoff。 |
| 缺材料或 unsafe claim fail closed | 通过 | Task A 覆盖 unsupported schema/boundary、缺关键材料、success/control/HIL/O5 claims、credential/token/URL/path/checksum/raw JSON 泄漏。 |
| Robot diagnostics metadata-only consumer | 通过 | Task B 新增 constants、default summary、source contract、sanitizer / summary function 和 explicit / env / inline / diagnostics / alias consumption。 |
| Mobile 首屏只读 panel | 通过 | Task C 在 execution pack 后新增“传感器采购收货回填” panel，展示 receipt intake 状态、材料状态、next evidence、owner handoff、safe evidence ref、boundary 和 not_proven。 |
| 主操作 fail closed | 通过 | Task B / C 均声明不触发 collect / dropoff / cancel、ACK、cursor、Nav2、HIL；Start / Confirm Dropoff / Cancel gating 未改变。 |
| 文档同步 | 通过 | Task A 更新 `docs/product/production_hardware_boundary.md`，Task B 更新 `docs/interfaces/ros_contracts.md`，Task C 更新 `docs/product/mobile_user_flow.md`，Task D 更新 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`。 |

## 2. OKR 最低优先级核对回顾

- 当前 live OKR 中 Objective 5 仍是数值最低，约 66%。
- 本 sprint 不针对 Objective 5 的原因仍成立：当前开发主机只有 Docker，本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
- 本轮选择 Objective 4 是因为 PR #5 和最近三轮硬件材料链都指向低成本量产硬件边界：2D LiDAR / ToF 必须从 product target 推进到可接收真实 receipt、source、install、wiring、power、calibration 和 HIL-entry 材料的入口。
- 因此 Objective 4 可按 software proof 保守上调；Objective 1 / 2 / 3 / 5 均不因本轮上调。

## 3. 用户价值验收

- 用户价值：采购或现场同学未来拿到真实传感器材料后，可以通过统一 receipt intake 入口回填，而不是靠聊天解释材料是否能进入安装、标定或 HIL。
- 产品北极星对齐：本轮继续把低成本量产硬件边界做成可诊断、可回填、可在手机端解释的只读链路，服务普通用户最终可验收的送垃圾任务。
- 当前限制：本轮只是材料接收与校验入口；没有真实 receipt 或真实硬件材料，因此不能声明采购完成、安装完成、标定完成或 HIL-entry 通过。

## 4. 证据边界核对

本轮只证明：

- `software_proof_docker_hardware_sensor_procurement_receipt_intake_gate`
- PC gate / Robot diagnostics / mobile web 对 receipt intake summary 的 fail-closed 软件链路
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮不证明：

- 真实采购、真实收货、真实安装、真实接线、真实电源、真实标定、真实 HIL entry
- 真实 route/elevator field pass、真实 Nav2/fixed-route、真实手机/browser
- dropoff/cancel completion、delivery success
- Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration

## 5. 结论

本轮满足 PRD / Tech Plan 的 Product Closeout 口径，可以作为 Objective 4 低成本量产硬件边界的 +1pp software proof。下一步若要继续提升 Objective 4 或打通 Objective 1 / 2 / 3，必须补真实 2D LiDAR / ToF receipt/source/SKU、安装、接线、电源、标定和 HIL-entry materials；若要提升 Objective 5，必须补真实外部云/4G/OSS/CDN/DB/queue 证据。
