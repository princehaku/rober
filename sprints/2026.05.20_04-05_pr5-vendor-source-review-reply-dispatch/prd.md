# Sprint 2026.05.20_04-05 PR5 Vendor Source Review Reply Dispatch - PRD

## 1. 用户价值和产品北极星

普通用户最终需要的是一台低成本、可量产、可售后诊断的送垃圾机器人，而不是一套把硬件愿望误写成已验证事实的文档。PR #5 unresolved thread `PRRT_kwDOSWB9286CJ3tX` 现在的产品风险很具体：reviewer 要求为 mandatory sensor assumptions 引用 vendor sources；如果团队只能拿出内部解释而不能给出安全、可发布、可复核的 reply，后续硬件基线仍会停留在“看起来合理但不能验收”的状态。

本轮用户价值是把 03-04 的 `pr5_vendor_source_review_packet` 转成可发布到 GitHub review thread 的 reply-dispatch 能力。它让 CEO、Engineer 和 reviewer 看到同一条事实线：local `docs/vendor/` 能证明哪些 source boundary，2D LiDAR / ToF 哪些材料仍 `hardware_material_pending` / `not_proven`，以及为什么当前不能关闭真实材料 blocker。

产品北极星不变：普通手机用户能安全交付垃圾。任何会影响量产、导航、安全环或售后诊断的硬件假设，都必须有可追溯 source 和真实材料；没有材料时必须 fail closed。

## 2. OKR 映射

- Objective 5：当前约 68%，是 `OKR.md` 4.1 数字最低 Objective。本轮不推进 Objective 5，因为没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料；继续做 O5 local command/status/ACK metadata 会重复消费 blocker。
- Objective 1：当前约 81%。本轮直接服务 PR #5 `PRRT_kwDOSWB9286CJ3tX` 的 vendor/source review 风险，但只做 reply-dispatch `software_proof`，不证明真实 WAVE ROVER/UART/HIL，也不证明 2D LiDAR / ToF 真实材料，因此不提高 Objective 1。
- Objective 4：当前约 99%。mobile/web 可只读展示 reply-dispatch 状态和 safe copy，但不证明真实手机/browser、production app、真实 PWA prompt/user choice 或控制闭环，因此不提高 Objective 4。

## 3. KR 拆解或更新

- O1 KR：把 PR #5 mandatory sensor assumptions 的 reply 输出拆成 source boundary、missing materials、next evidence 和 non-claim 四段；2D LiDAR / ToF 必须保留 `hardware_material_pending` / `not_proven`，直到真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 到位。
- O4 KR：手机端只读展示 reply-dispatch 状态，文案必须明确 “ACK / summary / reply-ready 不等于送达、HIL、真实手机验收或硬件材料到位”。
- O5 KR：本轮只在 `OKR 最低优先级核对` 中保留 stop rule，不做 O5 completion 更新。
- Product closeout KR：实现完成后只记录 `software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate`，不得把 GitHub reply 文案写成真实材料 closure。

## 4. 本轮核心抓手

`pr5_vendor_source_review_reply_dispatch`：

1. 读取或复用 03-04 `pr5_vendor_source_review_packet` summary。
2. 生成安全 Markdown reply / summary：
   - 指向 thread `PRRT_kwDOSWB9286CJ3tX`。
   - 引用 local vendor/source boundary：`docs/vendor/VENDOR_INDEX.md` 及其指向的 WAVE ROVER / Orange Pi / UART JSON / firmware/vendor app references。
   - 明确 local vendor tree 不证明 project 2D LiDAR / ToF 真实 source/materials。
   - 标记 `source=software_proof`、`hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
3. Robot diagnostics 只读暴露 reply-dispatch summary。
4. Mobile/web 只读展示 reply-dispatch 状态和中文 safe copy。
5. Product closeout 不提高 Objective 5 / Objective 1 / Objective 4。

## 5. 需要做什么

- Hardware：实现 reply-dispatch artifact generator，把 vendor/source packet 转成 safe Markdown reply 和 machine-readable summary；如果缺 03-04 packet 或出现 success/HIL/delivery/control claim，必须 fail closed。
- Robot：新增 diagnostics safe alias，只消费 sanitized reply-dispatch summary，不读取 raw GitHub token、raw artifact body、串口、ROS graph 或控制面。
- Full-Stack：新增 mobile/web 只读 panel 或接入现有 PR #5 硬件材料区域，展示 thread、reply status、source boundary、missing materials、next required evidence 和 safe copy。
- Product：实现后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`；如需要发布到 GitHub thread，必须以人工确认或独立执行为准，本轮软件只生成安全 reply，不默认发帖。

## 6. 优先级和验收口径

优先级：P1。

理由：

- 它直接对应当前唯一 unresolved PR #5 review thread `PRRT_kwDOSWB9286CJ3tX`。
- 它在 Docker-only host 上可推进，不需要真实硬件，也不重复 O5 external-material blocker。
- 它把上轮 packet 从 “内部可复核” 推进为 “可对 reviewer 安全解释”，是 release/review 闭环前的最小软件抓手。

验收口径：

- 生成的 Markdown reply 只能包含 safe source-boundary 和 missing-materials 信息，不包含 token、credential、raw local path、serial/UART output、ROS topic payload 或控制语义。
- Reply 必须包含 `software_proof`、`not_proven`、`hardware_material_pending`、`delivery_success=false`、`primary_actions_enabled=false`。
- Reply 必须明确 2D LiDAR / ToF 仍缺真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- Robot/mobile 只读消费，不启用 Start Delivery / Confirm Dropoff / Cancel，不产生 ACK/cursor/command side effect。
- Product closeout 明确 Objective 5、Objective 1、Objective 4 均不提高。
- 验证只做围栏：focused unittest、`py_compile`、`node --check`、targeted `rg`、scoped `git diff --check`。

## 7. 对应责任 Engineer

- `hardware-engineer`：reply-dispatch generator、artifact schema、Markdown safety scanner、source-boundary semantics。
- `robot-software-engineer`：Robot diagnostics safe alias、metadata-only interface docs、fail-closed tests。
- `full-stack-software-engineer`：mobile/web read-only panel、fixture、中文 safe copy 和 no-control assertions。
- `product-okr-owner`：GitHub reply wording boundary、OKR closeout、sprint 六文档后半段、progress log。

## 8. 风险、阻塞和需要补齐的证据链

- 真实材料风险：2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 仍缺；本轮不能关闭。
- GitHub 操作风险：reply-dispatch 软件可生成 Markdown，但是否发布到 unresolved thread 需要明确执行者和权限；不能把生成 reply 写成 GitHub 已回复。
- O5 风险：Objective 5 仍约 68%，没有真实 external proof；本轮只记录 stop rule，不补 O5。
- O1 风险：Objective 1 不因 source-boundary reply 而提高；仍缺真实 WAVE ROVER/UART/HIL。
- O4 风险：mobile/web 只读展示不等于真实手机/browser 验收。

证据链必须保持：

`pr5_vendor_source_review_packet` -> `pr5_vendor_source_review_reply_dispatch` -> Robot diagnostics read-only summary -> mobile/web safe copy -> Product closeout。

## 9. 需要创建或更新的 sprint 文档

本计划阶段只创建：

- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/pre_start.md`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/prd.md`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/tech-plan.md`

实现完成后必须继续补齐：

- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/tech-done.md`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/side2side_check.md`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/final.md`

Product closeout 若涉及 OKR/progress 状态变化，只允许写明不提高 Objective 5、Objective 1、Objective 4，并保留 `software_proof` 边界。
