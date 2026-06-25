# PC 自动扫图锁定态人工扫图回退

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“自动扫图准备”在 `free_roam_autonomy=locked` 时明确提示自动扫图未开放。
  - locked 状态下直接给出当前可用人工扫图流程：`开始记录 -> 启用键盘 -> 按住方向键/WASD -> 停止 -> 保存地图`。
  - 保持自动扫图按钮禁用，PC 端仍只展示 readiness，不生成自动运动命令。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定默认首屏必须展示人工扫图回退文案。
  - 追加断言默认渲染不会调用 `/api/robot-control/base/manual`。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-25 起 locked 自动扫图的普通首屏能力边界和接口副作用边界。

## 验证结果

- `npm test -- -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，1 passed / 164 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 165 tests passed。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
- 7001 只读 summary：
  - `source_base_url=http://192.168.1.11:8787`
  - `safe_to_control=false`
  - `keyboard_control_mode=bounded_repeating_manual_pulse`
  - `free_roam_autonomy=locked`
- PC Node 端口：
  - `node` 正在 `TCP *:7001` 监听。
- SSH 只读探测：
  - `ssh root@192.168.1.11 -p 37878` 可连接。
  - 上位机 `0.0.0.0:8787` 正在监听。

## 剩余风险

- 本轮没有执行真实底盘运动、Nav2 行程、地图记录或自动扫图；真实扫图覆盖仍需现场 operator 勾选安全确认后人工按住键盘验证。
- 自动扫图继续保持 locked；要开放自动模式仍需要上车端 watchdog、雷达避障 gate 和 HIL 证据。
- 7001 服务保持在当前本机端口，不涉及 Clash 配置。
