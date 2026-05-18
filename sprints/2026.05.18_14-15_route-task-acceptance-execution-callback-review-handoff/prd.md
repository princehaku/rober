# Sprint 2026.05.18_14-15 Route Task Acceptance Execution Callback Review Handoff - PRD

## 1. 产品问题

上一轮 `route_task_field_retest_acceptance_execution_callback_review_decision` 已能把 callback intake 的 received/missing/rejected 状态转成 review decision，但现场 owner 仍需要一份更接近执行交接的 package：下一步到底是进入受控现场复跑、补齐 owner 材料、同一 `evidence_ref` 重跑，还是因 unsafe review handoff 阻断。

如果没有 handoff layer，review decision 容易停留在工程复核结果，不能形成面向现场执行和售后支持的下一步材料清单。

## 2. 用户价值和产品北极星

用户价值:

- 现场 owner 可以在 PC gate / Robot diagnostics / 手机只读面板中看到统一 handoff 结论。
- 支持同学可以快速判断缺哪类材料、谁负责补、是否必须同一 `evidence_ref` 重跑。
- 普通手机用户不会看到 raw ROS topic、硬件细节、凭证、traceback 或成功误导文案。

产品北极星:

- 让 `rober` 的 route/elevator trash delivery 从“软件准备”逐步变成“可复核、可交接、可回填真实现场证据”的闭环。
- 本轮只推进 field retest acceptance execution callback review handoff，不宣称真实送达成功。

## 3. OKR 映射

| Objective | 本轮映射 | 进度判断 |
| --- | --- | --- |
| Objective 1：硬件协议可信底盘 | 只保留 blocker 边界；不新增 WAVE ROVER/UART/HIL 证明。 | 保持约 81%。 |
| Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环 | 主受益 Objective。把 PR #4 route/elevator callback review decision 转成 handoff package，服务受控现场复跑材料准备。 | 保守保持约 99%，除非后续 closeout 有真实材料。 |
| Objective 3：可验证导航与固定路线 | 次受益 Objective。handoff 继续要求 Nav2/fixed-route runtime log、route completion signal、task record 等真实材料。 | 保守保持约 99%，不证明真实路线运行。 |
| Objective 4：手机用户体验与低成本量产边界 | 手机新增只读“现场复核交接” panel，帮助支持同学理解下一步，但不改变主操作 gating。 | 保守保持约 99%，不证明真实手机/browser。 |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 数字最低但 stop rule 成立；本轮不推进 O5 external proof。 | 保持约 68%。 |

## 4. KR 拆解或更新

- Objective 2 / KR6, KR7: handoff package 必须保留电梯门状态、目标楼层确认、人工协助、接管原因、同一 `evidence_ref` 与可回放材料要求。
- Objective 3 / KR2, KR3, KR4, KR5: handoff 必须继续要求 Nav2/fixed-route runtime log、route completion signal、task record、关键证据引用和失败原因，不能把 summary 当真实运行。
- Objective 4 / KR1, KR5, KR6, KR7: 手机只读 panel 必须中文优先、phone-safe、fail-closed，不暴露 raw ROS/hardware details，不改变 Start/Confirm/Cancel gating。
- Objective 5 / KR1-KR6: 不更新；没有真实 external proof 时不能上调或声称云链路产品化完成。

## 5. 本轮核心抓手

核心抓手是 `route_task_field_retest_acceptance_execution_callback_review_handoff`：

- 输入: 上一轮 `route_task_field_retest_acceptance_execution_callback_review_decision` artifact/summary。
- 输出: handoff artifact/summary，供 PC、Robot diagnostics、mobile/web 同步只读消费。
- 状态建议:
  - `ready_for_acceptance_execution_callback_review_handoff`
  - `needs_owner_follow_up`
  - `needs_acceptance_execution_callback_rerun`
  - `evidence_ref_mismatch_rerun`
  - `blocked_unsafe_review_handoff`

## 6. 范围边界

必须做:

- 读取 review decision artifact/summary，生成 handoff artifact/summary。
- Robot diagnostics 增加 `robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary` safe alias。
- mobile/web 增加只读“现场复核交接” panel，消费主 summary 或 Robot safe alias。
- Product closeout 更新 sprint 收口文档、`OKR.md`、`docs/process/okr_progress_log.md` 和必要 docs。

明确不做:

- 不打开真实串口、UART、WAVE ROVER 或 HIL。
- 不触发 Start Delivery、Confirm Dropoff、Cancel 或任何 robot command。
- 不新增真实 route/elevator field pass 结论。
- 不把 review decision、handoff、ACK、diagnostics/mobile summary 写成 task completion、dropoff/cancel completion、delivery result 或 delivery success。
- 不推进 O5 external proof。

## 7. 优先级和验收口径

P0:

- PC gate fail-closed 读取 review decision，并输出 handoff status、safe `evidence_ref`、owner handoff、next required evidence、safe rerun hints、boundary flags。
- 所有 summary 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- mobile panel 只读展示，不改变 Start/Confirm/Cancel gating。

P1:

- diagnostics safe alias 与主 summary 字段一致，禁止泄漏 raw artifacts、absolute paths、checksums、credentials、tracebacks、ROS topic、`/cmd_vel`、serial/UART、baudrate 或 hardware raw details。
- docs/product 或接口说明同步更新，保持手机/diagnostics contract 可追溯。

验收口径:

- 只运行围栏验证：`py_compile`、focused unittest、`node --check`、mobile focused unittest、required `rg`、scoped `git diff --check`。
- 不跑 broad tests。
- 验收成功只代表 repo-local Docker/software proof 可复核，不代表真实现场或外部生产通过。

## 8. 责任 Engineer

- Task A Autonomy: `autonomy-engineer`
- Task B Robot: `robot-software-engineer`
- Task C Full-stack: `full-stack-software-engineer`
- Task D Product closeout: `product-okr-owner`

## 9. 风险、阻塞和证据链缺口

- O5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser external proof。
- O1 仍缺真实 WAVE ROVER/UART/HIL packet、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery` 和 operator HIL report；同一 blocker 已被多轮 O1 sprint 消费。
- PR #5 仍缺 2D LiDAR/ToF vendor source、SKU、receipt、采购、安装、接线、电源、标定和 HIL-entry。
- PR #4 仍缺真实 route/elevator field materials：真实门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 和 delivery result。

## 10. 需要创建或更新的 sprint 文档

- 当前计划阶段: `pre_start.md`, `prd.md`, `tech-plan.md`
- 执行完成后: `tech-done.md`, `side2side_check.md`, `final.md`
