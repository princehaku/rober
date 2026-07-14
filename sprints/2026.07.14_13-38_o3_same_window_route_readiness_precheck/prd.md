# PRD - O3 Same-Window Route Readiness Precheck

## 背景

O3/O1 已经形成一条严格 no-motion 路线材料链：28-pose same-task replay packet、controlled route execution gate record、bounded route command plan、bounded route mock execution。最近 O7 voice 和 O5/O6/O7 wrapper 也已连续收口为 support-only，不能再被包装成 OKR 增量。

当前缺口不是再生成一个 readback/export/action receipt，而是把已有 route material 汇总成下一次 live route/HIL 之前的 same-window readiness precheck。该 precheck 必须让后续 owner 一眼看到：哪些现场材料还缺，哪些字段必须保持 false，什么时候才可以进入真正受控 route execution evidence。

## 用户价值和产品北极星

普通用户最终要的是小车安全送达垃圾，而不是一组离线合同。这个 precheck 不直接给用户展示，也不证明送达；它服务于产品北极星的下一步现场执行：把“已有固定路线材料”与“还不能发车”的原因对齐，减少下一轮真实路线验证时的安全歧义和证据缺口。

## OKR 映射和方向判断

- O5 仍约 `85%` 且最低，但 success-class production/cloud evidence 当前不可得；本轮不再重复 O5 wrapper。
- O1 约 `94%`，主要缺口仍是 current live HIL、safe-to-control、Nav2 route execution success、delivery/operator acceptance。
- O6/O7 约 `93%`，最近 voice/offline/action/write/readback wrapper 已消费，本轮不继续 O7 voice。
- 方向判断：`调整` 到 O3/O1 route execution 前置证据收敛。KR 不归档，主百分比不调整。

## 需求

1. 后续实现新增 Algorithm 层 CLI 或 builder，例如 `onboard/scripts/o3_same_window_route_readiness_precheck.py`。
2. 输入必须只读已接受 artifacts：
   - 07:07 controlled route execution gate record。
   - 08:09 bounded route command plan。
   - 23:23 bounded route mock execution summary/progress。
   - 可选只读 10:12 stop/HIL mock gate，用于说明 stop/HIL 仍是 mock-only blocker。
3. 输出 schema 固定为 `trashbot.o3.same_window_route_readiness_precheck.v1`。
4. 输出 proof boundary 固定为 `software_proof_o3_o1_same_window_route_readiness_precheck_only`。
5. 输出 status 固定为 `blocked_missing_same_window_live_evidence`，除非后续真实材料输入合同明确改变；本 sprint 不允许声明 ready for live control。
6. 输出必须保留同一 identity：`packet_id`、`task_id`、`route_intent_id`、`route_csv_row_count=28`、`segment_count=27`。
7. 输出必须列出 missing evidence：
   - `explicit_operator_approval`
   - `current_live_stop_hil`
   - `same_window_scan_readiness`
   - `same_window_amcl_pose_readiness`
   - `same_window_map_to_odom_tf_readiness`
   - `nav2_controller_result`
   - `delivery_or_operator_acceptance`
8. 固定 false fields 必须包含：
   - `route_execution_success=false`
   - `delivery_success=false`
   - `hil_pass=false`
   - `safe_to_control=false`
   - `robot_control_executed=false`
   - `publishes_cmd_vel=false`
   - `calls_base_manual=false`
   - `uses_base_uart=false`
9. 输出必须显式包含 no-motion guards：no /cmd_vel、no /api/base/manual、no NavigateToPose、no WAVE ROVER UART。
10. 文档必须说明该 precheck 是 readiness blocker 收敛，不是 route execution、delivery、HIL、production cloud 或 safe-to-control 证明。

## 非目标

- 不发 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不发 NavigateToPose。
- 不触碰 WAVE ROVER UART。
- 不打开真实硬件、串口、底盘控制、Nav2 controller 或 BT navigator。
- 不连接 production cloud、DB/queue、OSS/CDN 或 4G。
- 不更新 O7 voice/offline smoke、O6/O7 readback/export/action receipt 或 O5 terminal-result wrapper。

## 本轮核心抓手

核心抓手是把已接受的 bounded route material 变成“same-window live route 还缺什么”的机器可验收 artifact。它应该帮助下一轮明确进入 live route/HIL 前的验收门槛，而不是继续把 mock execution、bounded plan 或 voice/offline wrapper 当成新进度。

## 优先级和验收口径

优先级：P0，作为下一轮 route execution evidence 的前置门。

Product 只接受：

- artifact identity 与已有 route chain 完全一致；
- 所有 control/success/HIL fields 固定 false；
- missing evidence 足够具体，能直接指导下一轮 live capture；
- no-motion guards 原文可检索；
- 验证命令通过并写入 `tech-done.md`。

Product 必须拒绝：

- 任何 route execution success、delivery success、HIL pass、safe-to-control 或 robot control claim；
- 任何真实控制调用；
- 任何把 precheck 命名成 live route proof、delivery proof 或 production proof 的输出。

## 历史记录和剩余风险

已完成 KR 不移动到历史区；本轮计划不归档 KR。历史证据来源保持在 07:07、08:09、23:23 sprint closeout 和 `OKR.md` 4.1 相关记录中。剩余风险是：如果后续仍没有 operator approval、current live HIL、same-window `/scan`/localization/TF readiness 和 Nav2/controller result，本链路仍只能停留在 `software_proof`。

## 需要创建或更新的 sprint 文档

本计划阶段只创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 implementation 完成后，由 owner 更新 `tech-done.md`；Product acceptance 才能更新 `side2side_check.md`、`final.md`、`OKR.md` 和进度日志。
