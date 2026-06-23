# 2026.06.23 22:45 Keyboard Wheel Readback Hint

sprint_type: micro

## 实际改动

- PC 普通首屏键盘 gate 被 wheel raw L/R 非零材料挡住时，会在键盘区下一步里复述当前 `L/R=0/0`、T1001 帧数和短电压。
- `复查手控条件（先补轮速，不发车）` 后，键盘区继续复用当前 fresh `base/status` 读数，指向 `已检查轮速卡点`。
- 该改动只调整普通文案和测试，不改变键盘 gate、不启用键盘、不发送 keyboard pulse/manual/stop，也不调用 Nav2、delivery complete 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md` 记录键盘区 wheel readback 提示口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "keyboard arm button at wheel proof"`，1 个目标测试通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个 test files、145 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`git diff --check`。

## 剩余风险

- 真实上位机当前只读反馈仍为 `L/R=0/0`，雷达 lifecycle 未运行，Nav2 latest 是旧证据，delivery success=false；本轮只是让 PC 键盘手控入口更清楚地指出当前 wheel 卡点，未完成真实连续手控验收。
