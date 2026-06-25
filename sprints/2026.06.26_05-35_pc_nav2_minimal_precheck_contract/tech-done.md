# 2026-06-26 05:35 PC Nav2 最小预检合同对齐

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 高级诊断中的 Nav2 目标预检门禁标签从 `goal operator material gate` 改为 `goal minimal safety gate`，避免误导为仍需 operator report 材料包。
- `pc-tools/workstation/test/App.test.ts`
  - 将默认 Nav2 goal preflight fixture 从旧 `operator_report_preflight_required` 改为 `preflight_passed / ready_for_navigation_goal_not_executed`。
  - fixture 中 `operator_report_preflight` 明确为 `not_required_for_nav2_minimal_safety_precheck`，不再伪造读取 `/api/operator/report`。
  - 更新高级诊断回归，验证预检通过、显示最小安全门禁、不出现旧 `operator_report_preflight_required`，且仍不调用 `/api/nav2/start`、`NavigateToPose`、`/cmd_vel` 或 `/api/base/manual`。
- `docs/product/pc_tools_workstation.md`
  - 同步当前 Nav2 目标预检合同：只要求 `confirm_navigation_preflight=true` 与固定只读定位/路径 readback，不再读取或要求 `/api/operator/report`。
  - 标注 2026-06-11/06-21 历史 smoke 中的 operator report 缺口已被后续最小预检口径取代。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "Robot Control V1|plain trip"`，8 passed / 181 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，2 files / 189 passed。
- 通过：`git diff --check`。
- 确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 PC node 监听 `*:7001`，未改 Clash/系统代理。

## 剩余风险

- 本轮只对齐 PC Nav2 preflight 合同、mock fixture 和高级诊断文案；没有在真实小车上执行 Nav2 路线或做 HIL。
