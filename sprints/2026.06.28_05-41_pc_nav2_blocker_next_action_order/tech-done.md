# PC Nav2 Blocker Next Action Order

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 基于 `readback_summary.nav2.current_blocker_reasons` 生成普通首屏下一步顺序。
  - 当 Nav2 proof 当前缺 `/scan`、`/amcl_pose`、`map->odom TF` 或 localization readiness 时，首屏按“雷达 -> 重新定位 -> 准备图上路线 -> 地图画面确认”提示。
  - 如果 planner/controller/Nav2 stack 同时未运行，当前事实会先提示启动/恢复自动驾驶服务（不发车），再串接雷达/定位/路线顺序。
  - 行程状态、行程最小确认提示和本轮进度的行程下一步同步使用同一顺序。
- `pc-tools/workstation/test/App.test.ts`
  - 加强 Nav2 blocker 首屏测试，锁定 `当前事实`、行程状态、最小确认提示和本轮进度都包含雷达/定位/路线顺序。
- `docs/product/pc_tools_workstation.md`
  - 同步 Nav2 blocker 下一步排序规则和安全边界。

## 只读现场证据

- 只读 SSH 上位机查询显示当前 Nav2 proof blocker 仍包含：
  - `/scan_once_not_observed`
  - `/amcl_pose_once_not_observed`
  - `map_to_odom_not_observed`
  - `map_to_base_link_blocked_by_missing_map_to_odom`
  - `localization_not_ready_for_path_generation`
- `GET /api/radar/status` 显示 `continuous_scan_status=latest_proof_present_but_lifecycle_not_running`、`latest_scan_proof_fresh=false`。
- 本轮没有发送真实 radar start、localize reset、Nav2 start、Nav2 execute、manual、keyboard、delivery、free-roam、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "shows current Nav2 blocker reasons in first-screen facts"`
- 通过：`npm test`
  - `2 passed`，`343 passed`
- 通过：`npm run lint`
- 通过：`npm run build`
  - TypeScript 与 Vite build 通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`

## 剩余风险

- 本轮只修正 PC 首屏下一步引导，不等于真实 Nav2 已可执行。
- 真实小车仍需现场按安全流程处理雷达 lifecycle/current scan、AMCL pose、map->odom TF 和 localization readiness。
