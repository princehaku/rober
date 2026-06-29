# PC 建图 readiness 仪表 micro sprint

- sprint_type: micro
- 时间：2026-06-30 07:43 CST
- owner：User Touchpoint Full-Stack Engineer（主会话直接执行；本轮按用户要求不调用 subagent）

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通首屏自由移动 / 建图卡新增 `plain-mapping-readiness-gauge`。
  - 仪表合并展示自由移动、安全确认、相机首帧、雷达刷新、地图记录、地图画面刷新状态。
  - DOM 合同新增 `data-can-free-move-now`、`data-camera-ready-for-mapping`、`data-radar-ready-for-mapping`、`data-map-runtime-started`、`data-map-preview-fresh`、`data-mapping-start-ready`、`data-mapping-evidence-ready`、`data-mapping-missing-reasons`、固定自由移动/建图/地图预览入口和 `data-sends-motion-when-clicked=false`。
  - 普通文案从“传感器 ready 后建图”调整为“传感器就绪后建图”。
- `pc-tools/workstation/src/styles.css`
  - 新增建图仪表状态样式，区分“待安全确认 / 可先移动 / 可启动建图 / 可验收建图”。
- `pc-tools/workstation/test/App.test.ts`
  - 补默认首屏、传感器就绪只缺地图记录、摄像头首帧失败但可先移动三类回归断言。
- `pc-tools/README.md`
  - 同步 PC 工作站入口说明和新 DOM 合同。
- `docs/product/pc_tools_workstation.md`
  - 同步产品边界，明确该仪表只展示和验收，不新增运动入口。

## 验证结果

- 已通过：`npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
- 已通过：`npm test -- test/App.test.ts -t "points mapping-ready users to start the map recording when only mapping runtime is missing"`
- 已通过：`npm test -- test/App.test.ts -t "allows low-speed free-roam recording while marking mapping degraded when camera has no first frame"`
- 已通过：`npm test -- --run`（389 passed）
- 已通过：`npm run build`（产物 `index-C6Q5dZMQ.js` / `index-Cmol8DJx.css`）
- 已通过：`git diff --check`

## 剩余风险

- 本轮是 PC Web 展示、DOM 合同和单测验证，没有执行真实小车 HIL。
- 真实自由移动、建图记录、相机首帧、雷达 fresh 和地图画面刷新仍需要在 192.168.1.11 上车环境现场验收。
