# 2026-06-23 05:35 restore first-jog blocker priority

sprint_type: micro

## 实际改动

- 调整普通首屏 `本轮进度 -> 验收卡点` 的优先级：当送达草稿覆盖 latest operator report、first-jog 只缺基础安全确认时，先提示 `恢复试动确认`，不再被当前 `L/R=0/0` 排障文案抢走。
- 补充前端回归测试，覆盖送达草稿覆盖 basic safety、当前只读轮速 `0/0` 时，验收卡点必须显示恢复试动确认。
- 更新 `docs/product/pc_tools_workstation.md`，明确该提示不自动恢复材料、不调用 first-jog/manual、delivery complete、keyboard pulse、stop 或 `/cmd_vel`。

## 只读上位机取证

- 已通过 SSH `root@192.168.1.11 -p 37878` 只读访问上位机，未执行运动或确认类接口。
- `/api/base/feedback-samples/latest` 显示 T1001 可读，但 latest wheel L/R 仍为 `0/0`，`wheel_feedback_lr_nonzero_proven=false`。
- `/api/operator/report` 当前为 `delivery_material_draft_not_operator_confirmed`，`operator_present=false`、`physical_clearance_confirmed=false`、`emergency_stop_ready=false`，且 `wheel_feedback_lr_nonzero_proven=false`、`physical_motion_lidar_delta_proven=false`。
- 这些证据说明当前真实卡点仍是恢复/重做 first-jog 材料和低速试动读非零 L/R，不能宣称 wheel raw L/R、delivery success 或键盘手控闭环完成。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test`，`Test Files 2 passed (2)`，`Tests 134 passed (134)`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`，Vite client build 和 server TypeScript build 均完成。
- 已通过：`git diff --check`。
- 测试期间两个历史 DOM smoke JSON 只改动 `checked_at`，已还原为原始时间戳，未纳入本轮 diff。

## 剩余风险

- 本轮只改善 PC 普通首屏卡点引导，并做只读上位机取证；没有执行真实 first-jog/manual、Nav2 route、delivery complete 或键盘连续手控。
