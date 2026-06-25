# PC 自动扫图准备状态 Micro Sprint

## sprint_type

micro

## 实际改动

- 在 `safe_command_boundary` 中新增 `free_roam_autonomy`、`free_roam_autonomy_label` 和 `free_roam_autonomy_policy` 合同，后端 summary 固定返回 `locked`。
- 在 PC 普通首屏“扫地式建图”卡片新增“自动扫图准备”只读区，展示 watchdog、LiDAR 避障、停止兜底、地图刷新和 HIL artifact 等缺口。
- “自动扫图（未开放）”按钮保持禁用且没有绑定点击动作，不触发移动、Nav2、`/cmd_vel` 或 `/api/base/manual`。
- 更新产品文档和 PC/server 测试，锁定当前自动扫图能力边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`，2 个测试文件、154 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 和 `vite build` 通过。
- 通过：`git diff --check`。
- 通过：7001 本地服务只读 DOM smoke，`http://127.0.0.1:7001/` 显示“自动扫图准备”，按钮为“自动扫图（未开放）”且 disabled；页面不再暴露 `lidar_obstacle_gate` 或 `onboard_watchdog` 内部 token。
- 通过：7001 HTTP summary 只读检查，`free_roam_autonomy=locked`、`safe_to_control=false`、`robot_control_executed=false`。

## 剩余风险

- 当前只是 PC readiness 展示，不是自动探索实现；真正自动扫图仍缺上车端 watchdog、LiDAR 障碍 gate、覆盖策略、stop fallback 和 HIL 证据。
