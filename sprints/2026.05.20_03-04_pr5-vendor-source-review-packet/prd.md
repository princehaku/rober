# Sprint 2026.05.20_03-04 PR5 Vendor Source Review Packet - PRD

## 1. 用户价值和产品北极星

普通用户最终需要的是一台低成本、可量产、可售后诊断的送垃圾机器人，而不是一个靠隐含硬件假设堆起来的 demo。PR #5 的 unresolved review 指向同一个产品风险：如果 2D LiDAR / ToF baseline 没有本地 vendor/source 证据，后续采购、安装、Nav2/安全环和售后诊断都会建立在不可追溯假设上。

本轮用户价值不是“买到传感器”，而是让硬件基线的证据状态可复核：Engineer、CEO 和 reviewer 能一眼看到哪些硬件事实来自 `docs/vendor/`，哪些只是 product target，哪些材料还缺。这样后续拿到真实材料时可以直接回填、复核和关闭 `PRRT_kwDOSWB9286CJ3tX`，不会把 happy path 或文档愿望误写成硬件完成。

产品北极星对齐：让普通手机用户最终能安全交付垃圾。硬件 baseline 必须可信、低成本、可解释；没有 source 的硬件假设必须 fail closed。

## 2. OKR 映射

- Objective 1：硬件协议可信底盘。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，当前缺口是 2D LiDAR / ToF mandatory assumptions 缺本地 vendor source 可追溯材料。本轮只推进 reviewability，不提高 O1。
- Objective 4：手机用户体验与低成本量产边界。硬件 baseline 的 source 状态需要以普通用户/售后可理解的方式呈现，但手机端只能只读展示，不开放控制。
- Objective 5：仍是最低约 68%，但本轮不推进 O5，因为没有真实外部材料；继续 O5 local ACK/status metadata 会重复消费 blocker。

## 3. KR 拆解 / 更新

- O1 KR 补充抓手：硬件 baseline source packet 必须引用 `docs/vendor/VENDOR_INDEX.md`，并把 2D LiDAR / ToF 标成 `hardware_material_pending` / `not_proven`，直到真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 到位。
- O4 KR3 / KR9 支撑：量产硬件约束和传感器扩展点必须可配置、可追溯、可售后解释，不能把 product target 写成已验证硬件。
- 本轮不更新 `OKR.md` 百分比；实现完成后由 Product closeout 只记录 `software_proof` 证据边界。

## 4. 本轮核心抓手

`pr5_vendor_source_review_packet`：

1. 读取 `docs/vendor/VENDOR_INDEX.md` 和 `docs/product/production_hardware_boundary.md`。
2. 输出 artifact / summary，包含：
   - `thread_id=PRRT_kwDOSWB9286CJ3tX`
   - `source=software_proof`
   - `proof_boundary=software_proof_docker_pr5_vendor_source_review_packet_gate`
   - `vendor_source_boundary`
   - `hardware_material_pending`
   - `missing_materials`
   - `next_required_evidence`
   - `not_proven`
   - `delivery_success=false`
   - `primary_actions_enabled=false`
3. Robot diagnostics 只读暴露摘要，不读取硬件、串口、ROS graph 或 raw artifact。
4. Mobile/web 只读展示 “PR #5 vendor/source review packet”，主操作继续 disabled。

## 5. 需要做什么

- Hardware：实现 PC gate 和 focused tests，确保缺 `docs/vendor/VENDOR_INDEX.md`、缺 source-boundary semantics、出现 success/HIL/delivery wording 时 fail closed。
- Robot：新增 diagnostics safe alias，消费 summary 并强制 metadata-only / read-only / fail-closed。
- Full-Stack：新增 mobile/web 只读 panel 或接入现有材料状态区域，展示 thread、source boundary、missing materials、next evidence 和 safe copy。
- Product：收口 sprint 六文档后半段、`OKR.md` 和 `docs/process/okr_progress_log.md`，保持不提高 O1/O5，必要时给 GitHub thread 留一条 review-ready 摘要。

## 6. 优先级和验收口径

优先级：P1。原因是它直接对应唯一 unresolved PR #5 thread，且可在 Docker-only 环境推进，不重复 O5 外部材料 blocker。

验收口径：

- Packet 能从当前 repo 文档生成，不需要真实硬件或外部服务。
- Packet 明确引用 `docs/vendor/VENDOR_INDEX.md` 作为 source boundary，同时明确 local vendor tree 不证明 2D LiDAR / ToF 实物。
- Robot/mobile 只读消费，不启用 Start Delivery / Confirm Dropoff / Cancel，不产生 ACK/cursor/command side effect。
- 所有输出必须包含 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 验证只做围栏：focused unittest、`py_compile`、`node --check`、targeted `rg`、scoped `git diff --check`。

## 7. 对应责任 Engineer

- `hardware-engineer`：PC gate / artifact / hardware source semantics。
- `robot-software-engineer`：Robot diagnostics safe alias / interface docs。
- `full-stack-software-engineer`：mobile/web read-only panel / fixture / product doc sync。
- `product-okr-owner`：OKR closeout、review wording、sprint docs。

## 8. 风险、阻塞和证据链

- 未解决风险：真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 仍缺。
- GitHub review risk：`PRRT_kwDOSWB9286CJ3tX` 可能继续 unresolved；本轮只让 review packet 可执行，不自动关闭 thread。
- 证据链必须保持：`software_proof_docker_pr5_vendor_source_review_packet_gate` -> Robot diagnostics summary -> mobile/web safe copy -> Product closeout。
- 不得宣称真实 hardware materials、HIL、route/elevator field pass、真实手机/browser、O5 external proof 或 delivery success。

## 9. 需要创建或更新的 sprint 文档

本轮已创建 fresh Epic planning docs：

- `sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/pre_start.md`
- `sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/prd.md`
- `sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/tech-plan.md`

实现完成后必须继续补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
