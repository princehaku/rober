# PC Free Roam Mapping Handoff Proof Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏自由移动 / 建图卡新增 `plain-free-roam-handoff-proof`。
  - 该验收条把“安全确认后可先低速自由移动”“画面和雷达 ready 后主按钮会先启动建图记录再低速移动”“地图记录和地图画面用于建图收口”串成一行。
  - DOM 暴露 `data-handoff-stage`、`data-can-free-move-now`、`data-camera-ready-for-mapping`、`data-radar-ready-for-mapping`、`data-mapping-start-ready`、`data-map-runtime-started`、`data-map-preview-fresh` 和固定 free-roam/map/camera/radar endpoint。
- `pc-tools/workstation/src/styles.css`
  - 为 handoff 验收条补齐待连接、待安全确认、可先移动、可边动边建图、建图可收口状态样式。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定默认待安全确认、已勾安全确认但传感器未齐、画面和雷达 ready 后主按钮请求建图记录三种状态。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明该行只做 PC Web 显示和只读合同，不自动勾安全确认、不自动启动自由移动或建图、不发送任何运动接口。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 个目标测试通过。
- `npm test -- test/App.test.ts -t "allows free-roam recording when camera source is selected but not yet frame-proven"`：通过，1 个目标测试通过。
- `npm test -- test/App.test.ts -t "points mapping-ready users to start the map recording when only mapping runtime is missing"`：通过，1 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、391 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-AMh4g_kJ.js` 与 `dist/assets/index-0NTdt-97.css`。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听进程为 `node` PID `25171`，页面入口引用 `index-AMh4g_kJ.js` 与 `index-0NTdt-97.css`。
- live bundle 检查：JS 命中 `plain-free-roam-handoff-proof=2`、`自由移动到建图=7`、`data-handoff-stage=2`、`data-primary-action-requests-mapping=6`、`先启动建图记录=3`；CSS 命中 `plain-free-roam-handoff-proof=6`、`可边动边建图=2`、`待安全确认=9`。

## 剩余风险

- 本轮只补 PC Web 显示和只读 DOM 合同，不自动勾安全确认、不自动启动自由移动或建图、不发送运动命令。
- 未做真实上位机 HIL 验证；自由移动、建图记录和地图刷新仍需现场按安全确认后人工验收。
