# Sprint 2026.05.16_19-20 Route Task Terminal Review Decision - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动新的 Epic sprint：`route_task_terminal_review_decision`。目标不是继续堆 O5 本地 metadata，也不是第三轮消费 PR #5 的硬件基线 / source / precheck blocker，而是把上一轮 `route_task_terminal_completion_rehearsal` software-proof 摘要转成 operator review decision、owner handoff、next-required-evidence 和 field retest request guidance。

产品北极星：让普通手机用户和现场支持能围绕一次送垃圾任务看到“为什么还不能证明送达、下一次现场复测要补什么、由谁补”的可执行材料，而不是只看到一组本地 gate 通过。

## 2. 证据输入

- `OKR.md` 4.1：Objective 5 约 66%，是当前数值最低 Objective；但本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration。继续 O5 只能重复本地 metadata，不能形成 Objective 5 external proof。
- `OKR.md` 4.1：Objective 1 约 75%，是下一低 Objective；但最近两轮 `2026.05.16_17-18_hardware-baseline-source-alignment` 和 `2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck` 已连续消费 PR #5 的硬件基线 / source / precheck blocker。本机无真实 WAVE ROVER、真实串口、2D LiDAR / ToF receipt/install/calibration 或 HIL，不应第三轮继续堆同类 hardware gate。
- PR #5 review 已指出三个具体风险：默认硬件集与强制传感器基线矛盾；OKR 最低目标叙述漂移；强制传感器假设缺 `docs/vendor` 来源。前两轮硬件 sprint 已把这些问题转换为 software-proof gate，但真实硬件材料仍缺。
- `sprints/2026.05.16_16-17_route-task-terminal-completion-rehearsal/final.md`：Objective 2 / Objective 3 仍缺真实 Nav2/fixed-route runtime log、task record、route completion signal、门状态、楼层确认、人工协助记录、dropoff/cancel completion 或 delivery result；但已有 `route_task_terminal_completion_rehearsal` software-proof 终态复账 contract。

## 3. 本轮转向理由

本轮转向 Objective 2 / Objective 3，原因是它们虽不是数值最低，但在 Docker-only 环境中有可行动的下一步：把 terminal completion rehearsal 的摘要变成 review decision 和 field retest guidance。该能力能直接服务下一次真实 route/elevator field session，让工程同学知道下一次必须补哪些同一 `evidence_ref` 材料。

本轮边界固定为 `software_proof` only、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。它不证明真实 Nav2/fixed-route、真实电梯、真实 dropoff/cancel completion、真实 delivery success、WAVE ROVER/UART/HIL、真实手机/browser 或 Objective 5 external proof。

## 4. Owner 和职责

- Product Manager / OKR Owner：维护本轮 sprint planning 文档、OKR 映射、验收口径和 closeout 口径。
- Robot Platform Engineer：后续实现 Robot diagnostics / task record metadata-only 消费，保持 fail-closed。
- Autonomy Algorithm Engineer：后续实现 PC evidence gate，把 terminal rehearsal summary 转成 review decision artifact / summary。
- User Touchpoint Full-Stack Engineer：后续实现 mobile/web 只读 review decision panel 和 field retest guidance。
- Hardware Infra Engineer：本轮默认不进入实现；若工程实现触及 WAVE ROVER、ESP32、Orange Pi、UART、电气、传感器 SKU、接线或 HIL，必须先回到 `docs/vendor/VENDOR_INDEX.md` 做事实确认。

## 5. 风险和阻塞

- Objective 5 阻塞：缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- Objective 1 阻塞：缺真实 WAVE ROVER/UART/HIL、真实传感器材料和上车 logs；同一 PR #5 硬件 blocker 已连续消费两轮。
- Objective 2 / Objective 3 风险：本轮只能把 software-proof 摘要转换为 review decision，不能替代真实现场材料。
- Product 风险：如果文案弱化 `not_proven`、`delivery_success=false` 或 `primary_actions_enabled=false`，会把 review decision 误读成送达完成。

## 6. 本轮文档链

- 已创建：`pre_start.md`
- 本轮继续写入：`prd.md`
- 本轮继续写入：`tech-plan.md`
- 实现完成后必须补齐：`tech-done.md`、`side2side_check.md`、`final.md`
