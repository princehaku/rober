# 2026.06.27 16:47 PC 自由移动近障碍首屏事实条

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainFreeRoamObstacleCautionText()`，从 `free_roam_autonomy_gates[]` 的 `obstacle_clear` 非 ready 状态提取最近障碍证据和下一步动作。
  - 普通首屏 `当前事实` 的自由移动行在可启动、已解锁或停止记录状态下追加近障碍提示，例如 `当前雷达近障碍：最近障碍 0.04m，原地换向避让，不继续直行`。
  - 该提示只改变 operator 看到的事实和动作预期，不改变 `free_roam_autonomy_start_ready`、不触发任何运动入口。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 `obstacle_clear=not_proven` 时的首屏自由移动提示。
  - 覆盖 live 形状：`readback_summary.lidar` 缺失或旧 proof、不含地图点数组，但 free-roam runtime `/scan` 新鲜且最近障碍为 `0.04m`。
  - 保持 no-motion 断言：不自动请求 `/api/robot-control/base/manual`、`/cmd_vel`、Nav2 路线执行或 delivery。
- `docs/product/pc_free_roam_mapping_design.md`
- `docs/product/pc_tools_workstation.md`
  - 同步记录：近障碍提示不等于自由移动硬门禁，建图验收仍按 mapping gates 单独收口。

## 验证结果

- `npm test -- --run test/App.test.ts -t "free-roam|radar"`：通过，44 passed。
- `npm test -- --run`：通过，2 files / 298 tests passed。
- `npm run build`：通过，生成新前端 bundle `/assets/index-JZylO_GD.js`。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 7001 live 只读 HTTP 验证：
  - `GET /` 返回新 bundle `/assets/index-JZylO_GD.js`。
  - `GET /api/robot-control/summary` 现场形状为 `camera=source_first_frame_failed`、`lidar=latest_proof_incomplete_while_lifecycle_running`、`lidar_fresh=ready/free-roam runtime /scan 新鲜`、`obstacle_clear=not_proven/最近障碍 0.04m`、`free_roam_autonomy_runtime.cmd_vel_publish_enabled=false`。

## 剩余风险

- 本轮未发起 manual、keyboard、free-roam start/stop、Nav2、delivery、stop 或 `/cmd_vel`，因此不声称真实小车已移动、自动驾驶已恢复或 delivery success 已完成。
- 内置 browser 实例在验证阶段返回 closed，未完成真实浏览器 DOM 读取；已用组件 DOM 测试、HTTP 新 bundle 和 live summary 形状覆盖该展示分支。
- 摄像头仍是 `source_first_frame_failed`，这次只改首屏近障碍事实提示，不修摄像头无首帧。
