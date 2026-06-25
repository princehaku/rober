# PC Camera Online Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“实时画面”在 camera readback 显示服务/设备在线、但本页 WebRTC 画面还没打开时，仍显示 `未打开`，提示从“还没有打开实时画面。”改为 `相机在线，点打开画面。`。
- `pc-tools/workstation/test/App.test.ts`：新增回归测试，确认 camera ready 只改变普通提示，不显示 `画面可见`，不泄露 `preview_status`、`/dev/video1`，也不自动调用 camera offer 或 first-frame probe。
- `docs/product/pc_tools_workstation.md`：同步记录相机在线但画面未打开的普通首屏展示边界。

## 验证结果

- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test`：通过，157 tests。
- `cd pc-tools/workstation && npm run build`：通过。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `camera.status=ready`、`devices_status=loaded`、`preview_status=idle_not_started`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 剩余风险

- 本轮只改 PC 首屏状态解释，没有打开 WebRTC、没有执行 camera first-frame probe、没有产生新画面样张。
- 真实“画面可见”仍必须由用户点击 `打开画面` 后，本地 video/canvas 采样达到亮度和非黑阈值才能显示。
