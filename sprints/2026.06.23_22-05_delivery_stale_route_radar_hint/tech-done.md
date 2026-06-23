# 2026.06.23 22:05 Delivery Stale Route Radar Hint

sprint_type: micro

## 实际改动

- PC 普通首屏在雷达未运行且已读到旧/未通过/不完整 Nav2 行程证据时，统一提示 `先启动雷达，再重新执行本轮行程`。
- `确认送达` 禁用态从只提示 `先启动雷达` 收紧为 `确认送达（先雷达再行程）`，避免把旧路线误当成本轮 delivery success 前置材料。
- 同步更新高级目标收口、`本轮进度`、行程卡片和送达卡片的同类文案，并补充单测覆盖不触发 radar start、Nav2 execute、delivery complete、manual 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md` 记录普通用户首屏的新引导口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "keeps stale Nav2 rerun explicit"`，1 个目标用例通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个 test files、145 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只做 PC 前端文案与 gate 显示修正；真实上位机当前仍需要 operator 显式启动雷达、重新执行本轮 Nav2 行程、补齐送达现场确认后，delivery success 才能闭环。
