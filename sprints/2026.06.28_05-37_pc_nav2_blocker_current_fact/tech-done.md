# PC Nav2 Blocker Current Fact

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `readback_summary.nav2` 新增 `current_blocker_reasons` 和 `current_blocker_labels`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 从 `/api/nav2/proof/latest` 的 `proof.blockers[]` 提取当前 Nav2 blocker reason/detail。
  - 将 `/scan_once_not_observed`、`/amcl_pose_once_not_observed`、`map_to_odom_not_observed`、`localization_not_ready_for_path_generation` 等原因压成普通用户能读懂的中文 labels。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的自动驾驶行新增“读回根因”，避免只显示泛化的“图上行程未准备”。
- `pc-tools/workstation/test/App.test.ts`
  - 新增首屏事实测试，锁定 Nav2 blocker labels 可见，并确认不触发 Nav2 execute、manual、delivery 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步 Nav2 blocker summary 字段、真实只读诊断形态和安全边界。

## 只读现场证据

- `ssh -p 37878 root@192.168.1.11` 成功连接上位机。
- 只读查询 `http://127.0.0.1:8787/api/nav2/proof/latest` 显示当前 blocker：
  - `/scan_once_not_observed`
  - `/amcl_pose_once_not_observed`
  - `map_to_odom_not_observed`
  - `map_to_base_link_blocked_by_missing_map_to_odom`
  - `localization_not_ready_for_path_generation`
- 本轮没有发送真实 Nav2 execute、manual、keyboard、delivery、free-roam、base stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "shows current Nav2 blocker reasons in first-screen facts"`
  - 目标测试 1 passed。
- 通过：`npm run build`
  - TypeScript 与 Vite build 通过；仅保留既有 Vite chunk size warning。
- 通过：`npm test`
  - `2 passed`，`343 passed`
- 通过：`npm run lint`
- 通过：`git diff --check`

## 剩余风险

- 本轮把真实 Nav2 root cause 显示到 PC 首屏，但没有启动 Nav2 服务或执行真实路线。
- 当前真实现场仍需要继续处理 `/scan`、`/amcl_pose`、`map->odom TF` 和 localization readiness，才能证明完整 Nav2 路线执行。
