# PC 自动扫图 runtime 状态

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 从 `free_roam_autonomy_latest` 或 `/api/status.free_roam_autonomy` 读取 runtime artifact 的 `decision.state/reason/stop_required`。
  - 在 `safe_command_boundary.free_roam_autonomy_runtime` 中输出只读状态摘要；无 artifact 时稳定返回 `not_loaded`。
  - 自动扫图按钮仍保持 locked，不改变 `safe_to_control=false`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“自动扫图准备”新增 `自动扫图状态` 行，把 runtime state 翻译为门禁锁定、低速直行判断、避障换向、原地找新覆盖、停止中或已完成。
  - 文案明确 artifact-only / cmd_vel 发布边界，不把 runtime state 外推成 PC 自动发车能力。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 Robot Control summary 合同，新增 `free_roam_autonomy_runtime`。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 覆盖首屏 runtime 文案和 server 从 latest artifact 提取 state/reason 的行为。
- `docs/product/pc_tools_workstation.md`、`docs/navigation/free_roam_autonomy.md`
  - 同步 PC 用户口径和 free-roam 技术口径。

## 验证结果

- 已通过：`npm test -- --testNamePattern "free-roam autonomy runtime|renders Robot Control V1"`，`2 passed / 167 skipped`。
- 通过：`npm run lint`。
- 通过：`npm test`，`169 passed`。
- 通过：`npm run build`。
- 通过：`curl -s http://127.0.0.1:7001/api/robot-control/summary`，确认默认 `source_base_url=http://192.168.1.11:8787`、`safe_to_control=false`、`free_roam_autonomy=locked`、`free_roam_autonomy_runtime.status=not_loaded`、`cmd_vel_publish_enabled=false`。
- 待本轮收口继续执行：`git diff --check`。

## 剩余风险

- 本轮没有触发真实自动扫图、Nav2 execute、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- `free_roam_autonomy_runtime` 只证明 PC 能显示上车端最近一次状态机 artifact；真车自由跑动建图仍需要 stop fallback、雷达避障、地图覆盖增长和低速 HIL 后才能解锁运动发布。
