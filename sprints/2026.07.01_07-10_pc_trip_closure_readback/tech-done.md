# PC 行程闭环只读验收块

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏行程卡新增 `plain-trip-closure-readback`。
  - 该块直接复用 live motion runbook 的 `run_nav2_route`，把完整行程闭环拆成三项中文事实：到点已读到/未读到、同窗口轮速 L/R 已非零/未证明、送达确认已完成/未完成。
  - 新增 `读回闭环` 按钮，但按钮只调用既有只读读回链路：Nav2 latest、base feedback samples、summary、delivery latest；不执行 Nav2、不发送手控/键盘/自由移动/建图/送达/停止命令。
- `pc-tools/workstation/src/styles.css`
  - 为行程卡闭环块补充紧凑四列布局和未就绪/待收口/已闭环状态色，保持普通 PC 界面简易直读。
- `pc-tools/workstation/test/App.test.ts`
  - 补充普通首屏 DOM 契约：三项闭环事实、只读 endpoint、按钮不发车、不会启动 Nav2/manual/keyboard/free-roam/map runtime/delivery/stop。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 `plain-trip-closure-readback` 的用户语义和只读边界。

## 验证结果

- `npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，1 passed。
- `npm test -- --run test/App.test.ts`：通过，230 passed。
- `npm run lint`：通过。
- `npm run build`：通过，包含 `tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json`；Vite 仍提示既有 bundle 超 500 kB。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`，PID `4781`。
- 只读 summary 读回：
  - `schema=trashbot.pc_tools_workstation.robot_control_summary.v1`
  - `console_status=loaded_fail_closed_summary`
  - `source_base_url=http://192.168.1.11:8787`
  - `health=ready`
  - `status=source_first_frame_failed`
  - `delivery_success=false`
  - `safe_to_control=false`

## 剩余风险

- 本轮没有发送任何运动/控制 POST，也没有做真实 Nav2 行程、同窗口 wheel L/R 非零或送达确认；完整行程硬件闭环仍需 CEO 现场安全确认后再执行。
- 上车 status 仍显示 `source_first_frame_failed`，说明摄像头当前首帧问题未在本 micro sprint 内解决。
- Vite bundle size warning 是既有体积提示，本轮未处理代码拆包。
