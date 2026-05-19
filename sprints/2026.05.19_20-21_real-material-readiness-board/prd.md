# Sprint 2026.05.19_20-21 Real Material Readiness Board - PRD

## 1. 产品问题

当前 OKR 最低项 Objective 5 和下一低项 Objective 1 都需要真实材料才能推进，但本机没有真实硬件，只有 Docker。PR #4 route/elevator 与 O4 mobile 也已经连续多轮把真实材料缺口包装成 software-proof handoff。继续单点 wrapper 会让团队看起来在推进，但不会帮助现场 owner 交付真实材料。

本轮产品问题是：缺一个统一、只读、fail-closed 的 `real_material_readiness_board`，把 O5 external、O1 / PR #5 hardware、PR #4 route/elevator、O4 real phone 四类真实材料缺口合并展示，并明确 next_required_evidence、owner、blocker 和不能触发控制的安全边界。

## 2. 用户价值和产品北极星

产品北极星：让普通手机用户、现场 owner 和工程团队都能从一个入口判断“现在不能继续的原因是什么，下一份真实材料应该由谁提供”。

用户价值：

- 对现场 owner：减少跨 sprint 文档查找，直接看到四类材料的 missing / blocked / ready_for_review 状态。
- 对手机用户：只看到可理解的中文状态和下一步，不看到 raw JSON、ROS topic 或内部 test 名称。
- 对工程团队：Robot diagnostics 与 mobile/web 使用同一 summary，避免 O5/O1/PR #4/O4 各自发散。
- 对 Product closeout：保持 OKR 证据边界，避免把 `software_proof` 当作真实材料。

## 3. OKR 映射

- Objective 5：当前约 68%，最低。board 展示 external material readiness，但不制造真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover 或 external proof。
- Objective 1：当前约 81%。board 展示 WAVE ROVER/UART/HIL 与 PR #5 `PRRT_kwDOSWB9286CJ3tX` 所需真实 2D LiDAR / ToF 材料 readiness，但不关闭 review thread，不提高 O1。
- Objective 2 / Objective 3：当前约 99%。board 展示 PR #4 route/elevator / Nav2/fixed-route / task-record / delivery-result 所需真实现场材料 readiness，但不声明 route/elevator field pass。
- Objective 4：当前约 99%。board 展示真实 iPhone/Android / production app / PWA prompt/userChoice / true browser acceptance 所需材料 readiness，但不新增第四个单用途 mobile wrapper。

## 4. KR 拆解

KR-A：定义统一 readiness schema。

- 每类材料必须包含 `status`、`owner`、`next_required_evidence`、`blocking_reason`、`source_refs`、`evidence_ref`、`proof_boundary`。
- 顶层 summary 必须包含 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

KR-B：Robot diagnostics 可只读消费 board summary。

- Robot diagnostics 只展示 readiness 和 next actions。
- 不允许 board 影响 Start Delivery、Confirm Dropoff、Cancel、底盘控制或 action result。

KR-C：mobile/web 首屏可读展示。

- mobile/web 增加只读 “真实材料就绪看板”。
- 四类材料以中文状态展示，缺口和下一步必须面向普通用户/现场 owner 可理解。
- 不暴露 raw JSON 或 ROS topic。

KR-D：PC/evidence gate 可生成本地 software-proof artifact。

- PC gate 聚合已有 repo-local evidence、sample fixtures 与 review state。
- 输出只用于 routing，不作为真实 proof。

## 5. 范围

本轮必须做：

- `real_material_readiness_board` PC-side gate 或等价 evidence builder。
- Robot diagnostics summary alias / schema docs。
- mobile/web read-only board 和 fixtures。
- product/interface docs 同步更新。
- sprint closeout 文档和保守 OKR closeout。

本轮不做：

- 不更新 `OKR.md` 直到工程 worker 完成并返回证据。
- 不关闭 PR #5 `PRRT_kwDOSWB9286CJ3tX`。
- 不实现任何真实底盘、WAVE ROVER、UART、HIL、Nav2、route/elevator 控制。
- 不做 O5 真实公网、4G/SIM、OSS/CDN、production DB/queue、worker/cutover。
- 不把 mobile/web panel 写成真实手机/browser acceptance。

## 6. 优先级和验收口径

P0：

- board 聚合四类材料缺口，且每类至少有明确 owner、blocking_reason、next_required_evidence。
- 顶层 fail-closed flags 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- `PR #4`、`PR #5`、`PRRT_kwDOSWB9286CJ3tX` 必须在 board copy 或 evidence refs 中出现。

P1：

- Robot diagnostics 和 mobile/web 使用同一个 summary contract。
- mobile/web copy 中文优先，面向现场 owner，不把内部命令作为主文案。

P2：

- docs/product 与 docs/interfaces 同步解释 board 只是 routing surface，不是 proof surface。

验收口径：

- Focused unittest / `py_compile` / `node --check` / required `rg` / scoped `git diff --check` 通过。
- 不新增大范围测试，只使用围栏验证。
- closeout 中明确不会提高 OKR 百分比，除非工程实际拿到真实材料；本轮预期不会拿到。

## 7. 责任 Engineer

- Hardware Infra Engineer：硬件材料 bucket 与 PR #5 unresolved thread 映射。
- Autonomy Algorithm Engineer：PR #4 route/elevator 与 Nav2/fixed-route material bucket 映射。
- Robot Platform Engineer：diagnostics summary 和 read-only safety contract。
- User Touchpoint Full-Stack Engineer：mobile/web board 与 fixture。
- Product Manager / OKR Owner：PRD、tech-plan、closeout、OKR 边界。

## 8. 风险、阻塞和证据链

风险：

- 如果 board 文案不够严格，团队可能误读为材料已经齐备。
- 如果四类材料状态不统一，mobile/web 与 Robot diagnostics 会再次分裂成多个 wrapper。
- 如果没有引用 PR #5 unresolved thread 和 PR #4 route/elevator blocker，下一轮仍可能重复消费已 blocked 的路径。

阻塞：

- 本机没有真实硬件，只有 Docker。
- 无真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue。
- 无真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry。
- 无真实 route/elevator field pass 或真实手机/browser acceptance。

需要补齐的真实证据链：

- O5 external proof packet。
- O1 WAVE ROVER/UART/HIL packet 或 PR #5 sensor material packet。
- PR #4 route/elevator same safe `evidence_ref` field packet。
- O4 real phone/browser acceptance packet。
