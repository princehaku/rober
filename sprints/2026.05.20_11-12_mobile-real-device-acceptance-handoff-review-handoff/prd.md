# Sprint 2026.05.20_11-12 Mobile Real Device Acceptance Handoff Review Handoff - PRD

## 1. 产品目标

本轮目标是把 `mobile_real_device_field_trial_acceptance_execution_handoff_review_decision` 的复核结果，转成下一步现场 owner 可执行的 handoff package，并让 Robot diagnostics 与 mobile/web 只读展示“现场验收交接复核交接”。

该 package 只回答一个产品问题：复核以后，谁接下一步、为什么接、还缺什么、怎么重跑、哪些材料已接受或被拒。

## 2. 用户价值和产品北极星

用户价值：

- 现场 owner 可以从手机或 diagnostics 看到 current decision、handoff owner、handoff reason 和 rerun guidance。
- 售后或复核人员可以区分 accepted / missing / rejected / blocked，避免把缺证据的交接误解成真实验收通过。
- 普通用户看到的是 fail-closed 的状态说明，而不是 raw ROS topic、raw JSON、硬件路径、凭证、日志全文或控制授权。

产品北极星：

- 手机端继续作为普通用户唯一入口。
- 所有 evidence state 都必须 phone-safe、只读、可复跑、可解释。
- 没有真实现场材料时，必须保持 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 3. OKR 映射

主 Objective：Objective 4 手机用户体验与低成本量产边界。

辅助约束：

- Objective 5 当前约 68%，仍最低，但本轮不针对 O5；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser，不能继续堆 O5 metadata depth。
- Objective 1 当前约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；没有真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry，也没有 WAVE ROVER/UART/HIL，因此不能计为 O1 进展。
- Objective 2 / Objective 3 约 99%，但真实 route/elevator field pass、Nav2/fixed-route runtime、dropoff/cancel completion、delivery result 仍缺；本轮不声称现场通过。
- Objective 4 当前约 99%，本轮只补现场验收交接复核后的 handoff 可见性；不声称真实手机/browser 或 OKR 百分比提升。

## 4. KR 拆解

KR-A：Robot diagnostics 输出 safe summary。

- schema / state 必须包含 `mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff`。
- safe summary 必须携带 current decision、handoff owner、handoff reason、accepted / missing / rejected / blocked summaries、next required evidence、rerun guidance、safe `evidence_ref` 和 evidence boundary。
- 必须保留 `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate`。

KR-B：mobile/web 只读展示 handoff package。

- 首屏或现有现场验收链路中展示“现场验收交接复核交接”。
- 只消费 phone-safe summary，不请求 raw artifact，不发 ACK/cursor，不触发 Start / Confirm Dropoff / Cancel。
- `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 时三类主操作继续禁用。

KR-C：文档与验收口径同步。

- `docs/interfaces/ros_contracts.md` 写清 Robot diagnostics summary contract。
- `docs/product/mobile_user_flow.md` 写清 mobile/web 只读 handoff panel 的用户价值、字段白名单、禁止项和证据边界。
- Product closeout 后续更新 sprint `tech-done.md`、`side2side_check.md`、`final.md`，并仅在证据支持时更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。

## 5. 本轮核心抓手

核心抓手是“handoff review decision -> handoff package”，不是新增真实验收、不是打开控制、不是做云外部 proof。

最小可用展示：

- current decision: 例如 `ready_for_field_owner_handoff_not_proven` 或 blocked/missing/rejected 组合。
- handoff owner: 现场 owner 或下一责任角色。
- handoff reason: 为什么进入 handoff，而不是结束验收。
- accepted / missing / rejected / blocked summaries: 复核结果摘要。
- next required evidence: 下一步必须补齐的真实材料。
- rerun guidance: 重跑命令或现场采集步骤的 phone-safe 摘要。
- same safe `evidence_ref`: 与上一轮 handoff review decision 链路保持同一 safe reference。
- evidence boundary: `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate`。

## 6. 优先级和验收口径

P0 必须满足：

- Robot diagnostics 与 mobile/web 使用同一个 handoff review handoff 语义。
- `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 在 diagnostics、fixture、UI 和文档中一致。
- Start Delivery、Confirm Dropoff、Cancel 不得因本轮 panel 或 summary 变为可用。
- 禁止 raw ROS topic、`/cmd_vel`、serial/UART details、baudrate、WAVE ROVER parameters、credentials、DB/queue URL、OSS AK/SK、local paths、tracebacks、checksums、complete artifacts、raw field materials。

P1 应满足：

- accepted / missing / rejected / blocked 四类摘要在 mobile/web 上可读。
- rerun guidance 与 next required evidence 明确区分，避免把“建议重跑”写成“已经通过”。
- 文档明确本轮不是真实手机/browser、O5 external proof、O1 hardware/HIL、route/elevator field pass、dropoff/cancel completion 或 delivery success。

## 7. 对应责任 Engineer

Robot Platform Engineer：

- Owner 文件范围：
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/interfaces/ros_contracts.md`
- 责任：生产 Robot diagnostics safe summary、测试 fail-closed 字段、同步接口文档。

User Touchpoint Full-Stack Engineer：

- Owner 文件范围：
  - `mobile/web/app.js`
  - `mobile/web/styles.css`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `mobile/fixtures/mobile_web_status.fixture.json`
  - `mobile/web/fixtures/status.json`
  - `docs/product/mobile_user_flow.md`
- 责任：展示只读 handoff panel、更新 fixtures、验证三类主操作继续禁用、同步产品流程文档。

Product closeout：

- Owner 文件范围：
  - `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/tech-done.md`
  - `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/side2side_check.md`
  - `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/final.md`
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
- 责任：只在 worker 实现和验证完成后收口；不得把 software proof 写成真实 proof。

## 8. 风险、阻塞和需要补齐的证据链

- `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，必须继续写成 hardware_material_pending。
- 真实手机/browser、production app、真实 PWA prompt/userChoice 仍缺。
- O5 external proof 仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- O1 hardware/HIL 仍缺：WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry。
- O2/O3 field proof 仍缺：真实 Nav2/fixed-route runtime log、route completion signal、field task record、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result。

## 9. 需要创建或更新的 sprint 文档

本 planning 阶段创建 `pre_start.md`、`prd.md`、`tech-plan.md`。

后续实现完成后必须更新 `tech-done.md`、`side2side_check.md`、`final.md`；若有证据变化，再保守更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
