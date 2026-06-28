# PC Free Roam Latest Visible Summary

sprint_type: micro

## 实际改动

- 普通 PC 首屏 `刷新自由移动状态（只读）` 的结果摘要优先展示：
  - `free_move_start_status_plain`
  - `motion_runtime_status_plain`
  - `mapping_acceptance_status_plain`
- 用户点击只读刷新后，页面直接显示自由移动是否可启动、当前是否已经发布低速运动、建图是否可验收。
- 当 latest 返回 `free_move_start_ready=true` 但 `motion_ready=false` 时，页面可见摘要会明确 `motion_ready=false` 只表示尚未开始发布运动，不是启动阻塞。
- 同步更新 App 测试、PC tools README 和产品文档。

## 验证结果

- `npm --prefix pc-tools/workstation test -- App.test.ts -t "free-roam latest"`：命令成功退出，但 pattern 未命中用例，Vitest 输出 `1 skipped (1)`，不作为有效验证证据。
- `npm --prefix pc-tools/workstation test -- App.test.ts -t "refreshes free-roam autonomy latest"`：通过，`1 passed | 214 skipped (215)`。
- `npm --prefix pc-tools/workstation test`：通过，`2 passed (2)`、`375 passed (375)`。
- `npm --prefix pc-tools/workstation run build`：通过，Vite 输出 client build 成功；仅保留 chunk size warning。
- 只读检查本机 `0.0.0.0:7001` 的 `/api/robot-control/free-roam/autonomy/latest`：通过。返回 `proxy_status=latest_loaded`、`free_move_start_ready=true`、`motion_ready=false`、`mapping_readiness_ready=false`、`robot_control_executed=false`，并返回三段白话字段：
  - `free_move_start_status_plain=自由移动可启动；当前有停止请求，点击开始会先清除停止请求。`
  - `motion_runtime_status_plain=当前未在自由移动运行态；motion_ready=false 只表示尚未开始发布运动，不是启动阻塞。`
  - `mapping_acceptance_status_plain=建图验收未 ready；还差：画面首帧、雷达新鲜、地图记录、地图画面；这不阻止先低速自由移动。`

## 剩余风险

- 本轮只改普通页面只读展示，不启动 free-roam、不启动建图、不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。
- 真实低速自由移动仍需要现场安全确认后执行；当前建图验收仍依赖画面首帧、雷达新鲜、地图记录和地图画面。
