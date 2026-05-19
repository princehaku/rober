# Sprint 2026.05.19_22-23 Real Material Manifest Template - PRD

## 1. 用户价值和产品北极星

产品北极星：把 `rober` 做成普通手机用户可用、现场 owner 可验收、Engineer 可复盘的低成本 ROS2 自主垃圾投递机器人。

本轮 PRD 的用户价值不是再增加一个本地 wrapper，而是把 `real_material_evidence_intake` 前置成现场 owner 可以执行的 `manifest template` / submission pack：

- 现场 owner 能按同一 safe `evidence_ref` 提交真实材料，不需要理解每个 Objective 的内部 gate。
- Product 能判断材料是否对应 Objective 5 external、Objective 1 / PR #5 hardware、PR #4 route/elevator 或 Objective 4 real phone。
- Engineer 能把 submission pack 接入 PC gate、Robot diagnostics 和 mobile/web，而不会把材料模板误写成真实 proof。
- Reviewer 能看到 `PRRT_kwDOSWB9286CJ3tX` 仍是 `blocked_pending_real_materials`，直到真实 2D LiDAR / ToF 或 HIL-entry 材料到位。

## 2. OKR 映射

### Objective 5：云中转 + OSS/CDN 数据通路产品化

- 当前约 68%，数字最低。
- 本轮映射：定义 O5 external material manifest template，要求公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 等材料在同一 safe `evidence_ref` 下提交。
- 不提升条件：没有真实外部材料时，仍保持 `software_proof` / `not_proven`。

### Objective 1：硬件协议可信底盘

- 当前约 81%。
- 本轮映射：定义 O1 / PR #5 hardware manifest template，覆盖 WAVE ROVER/UART/HIL packet、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、operator HIL report，以及 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 必须保持 unresolved / `blocked_pending_real_materials`，直到真实材料到位并通过后续 review。

### Objective 2 / Objective 3：送达任务、电梯 assisted delivery、导航与固定路线

- 当前均约 99%，但仍缺真实 route/elevator field materials。
- 本轮映射：定义 PR #4 route/elevator manifest template，覆盖 Nav2/fixed-route runtime log、route completion signal、field task record、elevator door state、target floor confirmation、human assistance record、dropoff/cancel material 和 delivery_result。
- 不提升条件：没有真实电梯、真实路线、真实 task record 或真实 delivery_result 时，不写成 route/elevator field pass。

### Objective 4：手机用户体验与量产边界

- 当前约 99%，但仍缺真实手机和 production app 验收。
- 本轮映射：定义 O4 real phone manifest template，覆盖真实 iPhone/Android behavior、production app、PWA prompt/user choice 和 true phone/browser acceptance。
- 不提升条件：Docker/local browser 或 mobile/web panel 仍只是 `software_proof`。

## 3. KR 拆解或更新

本轮不直接更新 OKR 百分比；只定义后续可验收 KR 输入：

- KR-M1：统一 material group 枚举：`o5_external`、`o1_pr5_hardware`、`pr4_route_elevator`、`o4_real_phone`。
- KR-M2：每组 manifest template 都必须要求同一 safe `evidence_ref`，并标注 `same_evidence_ref_required=true`。
- KR-M3：每组必须区分 required / optional / rejected material，禁止提交凭证、绝对路径、raw ROS topic、raw serial/UART control、完整私密日志或 success/control 字段。
- KR-M4：submission pack 必须输出 owner handoff、next required evidence、review routing 和 fail-closed boundary。
- KR-M5：所有输出必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 4. 本轮核心抓手

核心抓手是 field-owner 可填写的 `manifest template`，而不是又一个本地 metadata wrapper。

最小产品形态：

- 一个 repo 内模板或样例包，让现场 owner 清楚每个 material group 应提交哪些文件、字段和观察记录。
- 一个 schema/contract，让 Engineer 能把模板接入 `real_material_evidence_intake` 后续 gate。
- 一个 phone-safe / diagnostics-safe summary 方向，让 Robot/mobile 只读展示材料包状态。
- 一个 Product closeout 口径，让 OKR 只在真实材料到位并经 review 后才提升。

## 5. 需要做什么

后续实现 sprint 必须完成：

1. 新增 manifest template / submission pack artifact，覆盖四类 material group。
2. 给出 sample submission，但 sample 必须显式 `not_proven`，不能伪造真实 evidence。
3. 把 template 字段与上一轮 `real_material_evidence_intake` 的 accepted/missing/rejected 语义对齐。
4. 让 Robot diagnostics 和 mobile/web 只能消费 sanitized summary，不读取 raw manifest 或敏感材料。
5. 更新 `docs/interfaces/` 和 `docs/product/mobile_user_flow.md` 等相关文档，保证 docs 反映最新状态。

## 6. 优先级和验收口径

P0：

- 模板必须覆盖 Objective 5、Objective 1 / PR #5、PR #4 route/elevator、Objective 4 四组材料。
- 必须出现 `Objective 5`、`Objective 1`、`PR #5`、`PRRT_kwDOSWB9286CJ3tX`、`real_material_evidence_intake`、`manifest template`。
- 必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

P1：

- 模板字段能直接驱动后续 PC gate、Robot diagnostics 和 mobile/web 只读展示。
- 每个 owner 的文件范围、验证命令和失败定位清楚，符合 team 并行推进。

P2：

- 提供现场 owner 中文填写说明，但不能把说明文档当成真实材料。

验收口径：

- 三份规划文档存在。
- required `rg` 能命中 sprint 类型、OKR、PR、evidence boundary 和 fail-closed 关键词。
- scoped `git diff --check` 对本 sprint 目录通过。

## 7. 对应责任 Engineer

- Product Manager / OKR Owner：本轮负责 PRD、KR、验收口径和后续 owner 分工。
- Hardware Infra Engineer：主责 O1 / PR #5 hardware template；执行前必须读取 `docs/vendor/VENDOR_INDEX.md`，不得猜测 WAVE ROVER、UART、引脚、电压、反馈协议或机械细节。
- Autonomy Algorithm Engineer：主责 PR #4 route/elevator、Nav2/fixed-route、task record、route completion 和 delivery_result template。
- User Touchpoint Full-Stack Engineer：主责 field-owner submission pack 在 mobile/web 或 phone-safe copy 中的展示/导出体验，不能改变主操作 gating。
- Robot Platform Engineer：主责 Robot diagnostics sanitized summary，不能读取 raw materials 或产生控制授权。

## 8. 风险、阻塞和需要补齐的证据链

- O5：缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover。
- O1 / PR #5：缺真实 WAVE ROVER/UART/HIL packet、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report、2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- PR #4 route/elevator：缺真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、field task record、dropoff/cancel material、delivery_result。
- O4：缺真实 iPhone/Android device behavior、production app、PWA prompt/user choice 和 true phone/browser acceptance。
- 误用风险：如果任何实现输出 pass/success/control authorization，本轮验收失败，必须退回 `not_proven`。

## 9. 需要创建或更新的 sprint 文档

- 已创建规划目标：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 后续实现必须更新：`tech-done.md`、`side2side_check.md`、`final.md`。
- 后续 closeout 必须按实际交付更新 `OKR.md`、`docs/process/okr_progress_log.md` 和相关 `docs/`，但不得在没有真实材料前提高 OKR 百分比。
