# Wheel Restore Hint

sprint_type: micro

## 实际改动

- PC 普通首屏“轮速记录”状态按 first-jog readiness 分流。
- 当 `first_jog_readiness_summary.status=blocked_missing_basic_safety` 且已有可见画面材料时，提示改为“先点恢复试动确认，再试动读取轮速”。
- 当已有画面但还不能 first-jog 时，兜底提示改为“现场画面已在，先完成试动前确认”。
- 更新 Vue 测试，覆盖送达草稿覆盖 latest operator report 时，轮速记录面板提示恢复试动确认。
- 本轮不触发真实 first-jog、不提交送达确认、不修改底盘协议。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`114 passed (114)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`，无 whitespace error。

## 只读现场证据

- SSH 上位机可达。
- `/api/base/status` 可读到 `/dev/ttyS5`、115200、T=1001，但本次只读 L/R 仍为 `0/0`。
- `/api/nav2/goal/execution/latest` artifact loaded，最近结果为 `goal_succeeded`，`delivery_success=false`。
- `/api/delivery/latest` 为 `blocked_missing_delivery_material`，缺 `confirm_delivery_completion`、operator observed motion/stop 和 delivery success claim。
- `/api/operator/report` latest 是 `delivery_material_draft_not_operator_confirmed`，wheel/LiDAR/delivery 均未证明。

## 剩余风险

- wheel raw L/R 非零仍未真实证明，需要现场安全确认后执行 first-jog 并保存 during-motion L/R 非零记录。
- delivery success 仍需要现场最终确认并通过上位机 delivery gate。
