# PC Free Roam Latest Runtime Plain Status

sprint_type: micro

## 实际改动

- `GET /api/robot-control/free-roam/autonomy/latest` 顶层新增：
  - `free_move_start_status_plain`
  - `motion_runtime_status_plain`
  - `mapping_acceptance_status_plain`
- 这三个字段把自由移动 start gate、当前运动运行态、建图验收态拆开说明。
- 当 live 形态出现 `free_move_start_ready=true` 但 `motion_ready=false` 时，接口会明确 `motion_ready=false` 只表示尚未开始发布运动，不是启动阻塞。
- 同步更新前端 fallback、App fixture、catalog 合同测试、PC tools README 和产品文档。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "free-roam autonomy latest"`，结果 `Test Files 1 passed (1)`，`Tests 2 passed | 158 skipped (160)`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `Test Files 2 passed (2)`，`Tests 375 passed (375)`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 TypeScript、Vite 和 server TypeScript build 全部通过；Vite 仅保留既有 chunk size warning。
- 通过：本机 PC API 已重启到 `0.0.0.0:7001`，监听进程为 `node` PID `20198`。
- 通过：只读检查 `GET http://127.0.0.1:7001/api/robot-control/free-roam/autonomy/latest` 返回 `proxy_status=latest_loaded`、`free_move_start_ready=true`、`motion_start_ready=true`、`motion_ready=false`、`robot_control_executed=false`。
- 通过：同一 live 响应返回 `motion_runtime_status_plain=当前未在自由移动运行态；motion_ready=false 只表示尚未开始发布运动，不是启动阻塞。`，并返回 `mapping_acceptance_status_plain=建图验收未 ready；还差：画面首帧、雷达新鲜、地图记录、地图画面；这不阻止先低速自由移动。`

## 剩余风险

- 本轮只补 free-roam latest 只读解释字段，不启动 free-roam、不启动建图、不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。
- 当前 live 仍需要现场安全确认后才能实际启动低速自由移动；建图验收还依赖画面首帧、雷达新鲜、地图记录和地图画面。
