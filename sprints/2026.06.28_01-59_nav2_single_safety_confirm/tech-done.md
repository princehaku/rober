# Nav2 单一安全确认

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 删除高级 Nav2 的独立 `confirmNavigationPreflight` 与 `confirmNavigationExecution` 前端状态。
  - 高级目标预检固定发送 `confirm_navigation_preflight=true`，保持只读预检兼容字段，但 UI 不再要求额外勾选。
  - 高级目标执行改为读取全页面统一 `plainUnifiedSafetyConfirmed/plainManualSafetyConfirmed`。
  - 高级 Nav2 表单只显示一个“现场安全确认（全页面一次生效）”复选框，和普通首屏共用同一状态。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增静态合同测试，防止高级 Nav2 再引入两个独立确认复选框。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 Nav2 高级入口也收敛到单一安全确认；后端确认字段仍保留兜底。

## 验证结果

- `npm test -- --testNamePattern "advanced Nav2 confirmation|fixed POST proxies|Nav2|nav2" --maxWorkers=1 --no-fileParallelism`
  - 通过：47 passed, 284 skipped。
- `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 通过：331 passed。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；仍有既有 Vite chunk size warning。
- `git diff --check`
  - 通过。
- `HOST=0.0.0.0 PORT=7001 npm run api:public`
  - 已重新启动，`node` 监听 `*:7001`。
- `curl -sS --max-time 5 http://127.0.0.1:7001/api/robot-control/summary`
  - 只读复验通过：summary 正常返回。
  - 当前现场仍显示 `keyboard_control_start_ready=true`、`free_roam_motion_start_ready=true`、`nav2_goal_ready=false`。
  - 当前 connection 仍为 `degraded`，原因是 camera health/devices timeout；这不是本轮确认 UI 变更造成。

## 剩余风险

- 本轮只改 PC 前端确认口径，不发送真实 Nav2 goal、manual/free-roam、stop 或 `/cmd_vel`。
- 后端仍要求 `confirm_navigation_execution=true`，直接绕过前端且未带确认的请求仍会被拒绝。
- 完整 Nav2 路线执行、wheel raw L/R 非零和 delivery success 仍需要现场安全确认后的真实运行证据。
