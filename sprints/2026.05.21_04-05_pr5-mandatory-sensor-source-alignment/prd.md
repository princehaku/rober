# PR5 Mandatory Sensor Source Alignment PRD

## 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给低成本 ROS2 小车后，小车能沿固定路线完成送达、电梯 assisted delivery、投放或人工取走，并且每一次结果都有可回放证据。本 sprint 的用户价值不是证明传感器已经采购、安装或 HIL 通过，而是让 PR #5 unresolved thread `PRRT_kwDOSWB9286CJ3tX` 中的 mandatory sensor assumptions 有本地 vendor-source 可追溯边界，避免继续用产品目标口径替代硬件事实。

面向用户的真实收益是：未来手机端、Robot diagnostics、Nav2/fixed-route 和硬件文档看到同一组传感器前提时，都能区分“产品目标需要 2D LiDAR / ToF / 单目相机”和“当前 repo 只有 vendor source boundary，真实材料仍 pending”。这能降低后续验收和售后诊断误读。

## OKR 映射

- Objective 5：当前最低，约 68%。本 sprint 不直接推进 O5，因为 Docker-only host 没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 true phone/browser external proof；近期已经做过多轮本地 metadata/fail-closed guard。
- Objective 1：约 81%，是本轮最低可行动作。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`，且 review 要求 mandatory sensor assumptions 引用本地 vendor source。本 sprint 只能推进 source-alignment software proof，不提高 HIL 或真实硬件完成度。
- Objective 2/3/4：受益于边界同步。Autonomy 和 mobile 可以展示或引用同一传感器前提边界，但不得写成真实 route/elevator field pass、真实手机/browser proof、dropoff/cancel completion 或 delivery success。

## KR 拆解或更新

- KR-A：Hardware PC gate 生成 `pr5_mandatory_sensor_source_alignment` artifact/summary，逐项核对 `docs/vendor/VENDOR_INDEX.md` 和本地 WAVE ROVER / Orange Pi vendor refs 是否支撑 source-boundary wording。
- KR-B：Product hardware boundary 写清 mandatory sensor assumptions：单目相机、2D LiDAR、ToF 安全环分别是产品目标、source boundary、还是 material pending；不得把 pending 写成 vendor-proven installed hardware。
- KR-C：Robot diagnostics 暴露 `robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary` safe alias，只读消费 sanitized summary，并保留 `not_proven` / `hardware_material_pending`。
- KR-D：mobile/web 展示只读“PR #5 传感器来源对齐”panel，给现场 owner 和支持人员看 source boundary、missing materials、next required evidence，不触发任何主操作。
- KR-E：Autonomy 文档同步 fixed-route / Nav2 的感知前提：2D LiDAR 和 ToF 是路线/安全目标材料，真实 Nav2/SLAM/near-field safety pass 仍需后续 evidence，不能由 PR #5 source alignment 替代。

## 本轮核心抓手

核心抓手是把“mandatory sensor assumptions”从口号变成可验证、可审查、可下游消费的 source-alignment contract。它必须回答：

- 哪些本地 vendor 文件是事实入口。
- 哪些 sensor assumptions 只是产品目标或 material pending。
- 哪些真实材料仍需要 field owner 或 hardware owner 回填。
- 哪些下游 UI / diagnostics / Nav2 文案必须保持 fail-closed。
- 哪些证据可以支持 GitHub reviewer 继续人工 review，但不能自动关闭 thread 或提升 OKR 百分比。

## 需要做什么

1. Hardware Infra Engineer 创建 PC gate 和 focused unittest，更新产品硬件边界与接口文档。
2. Robot Platform Engineer 增加 diagnostics safe alias 和 focused diagnostics unittest。
3. User Touchpoint Full-Stack Engineer 增加 read-only mobile panel、fixture 和 phone-safe copy。
4. Autonomy Algorithm Engineer 更新 fixed-route/Nav2 workflow 与 evidence contract 中的传感器前提边界。
5. Product Manager / OKR Owner 在实现后只做保守验收收口：更新 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`，不得虚增真实 proof。

## 优先级和验收口径

Priority P0:

- `PRRT_kwDOSWB9286CJ3tX` 必须在 artifact、summary、docs 和 mobile copy 中出现，且状态仍是 unresolved / material pending，直到 reviewer 实际 resolve。
- 所有 surfaces 必须引用 `docs/vendor/VENDOR_INDEX.md` 作为 source entrypoint；涉及 WAVE ROVER / UART / JSON / Orange Pi 的事实必须要求 implementation worker 读取 vendor index 指向的本地资料。
- Safe summary 必须保留 `software_proof_docker_pr5_mandatory_sensor_source_alignment_gate`、`hardware_material_pending`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 任何真实采购、安装、接线、电源、标定、HIL、Nav2/SLAM field pass、near-field safety pass、phone/browser proof、O5 external proof 或 delivery success claim 必须 fail closed。

验收口径：

- 四个 owner 的围栏命令通过。
- Required `rg` 能命中 `pr5_mandatory_sensor_source_alignment`、`PRRT_kwDOSWB9286CJ3tX`、`docs/vendor/VENDOR_INDEX.md`、`hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `git diff --check` 只覆盖本轮 touched files；不得被无关 workspace churn 阻塞。
- Product closeout 不提升 Objective 5，也不提升 Objective 1，除非实现阶段出现真实外部 / 硬件 / reviewer resolution evidence。

## 对应责任 Engineer

- Hardware Infra Engineer：PC gate、source rules、product hardware boundary、interface doc、focused unit test。
- Robot Platform Engineer：operator diagnostics safe alias、runtime contract doc、focused diagnostics test。
- User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture、mobile user flow doc、focused mobile test。
- Autonomy Algorithm Engineer：fixed-route/Nav2 sensing assumption docs and evidence contract boundary.
- Product Manager / OKR Owner：planning docs now; later closeout docs, conservative OKR/progress-log updates, and evidence boundary review.

## 风险、阻塞和需要补齐的证据链

- O5 blocker：缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser external proof。
- O1 blocker：缺真实 2D LiDAR / ToF SKU/source/receipt/procurement、安装、接线、电源、标定、HIL-entry、WAVE ROVER/UART/HIL、reviewer resolution。
- PR #5 blocker：`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved；本 sprint 最多让 mandatory sensor source alignment ready for manual review，不得写成 resolved。
- PR #6 boundary：README/docs-only，不是 runtime/hardware/HIL/phone/browser/O5 external proof。
- Field proof boundary：最新 O2/O3/O4 handoff 仍缺真实 task record、Nav2/fixed-route runtime log、route completion signal、elevator door/floor/human-assistance evidence、dropoff/cancel completion、delivery result 和 true phone/browser material。

## 非声明边界

This sprint must not claim real 2D LiDAR / ToF procurement, install, wiring, power validation, calibration, HIL entry, WAVE ROVER/UART/HIL, Nav2/SLAM field pass, near-field safety pass, real route/elevator field pass, real phone/browser validation, real PWA prompt/userChoice, O5 external proof, public HTTPS/TLS proof, 4G/SIM proof, OSS/CDN live traffic proof, production DB/queue or worker/cutover proof, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved, dropoff completion, cancel completion, delivery result, or delivery success.

## 需要创建或更新的 sprint 文档

- Created in planning: `pre_start.md`, `prd.md`, `tech-plan.md`.
- To be created after implementation: `tech-done.md`, `side2side_check.md`, `final.md`.
