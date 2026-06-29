# PC 自由移动 / 建图主面板 DOM 合同

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-30 17:25 CST

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainFreeRoamDomEvidence`，把自由移动启动、最小安全确认、相机/雷达是否阻塞移动、建图启动 ready、建图启动缺口、建图验收 ready、建图验收缺口和固定代理入口整理成普通首屏主面板可直接读取的结构化证据。
  - `plain-free-roam-mapping` 主面板新增 `data-free-move-start-ready`、`data-free-move-safety-only`、`data-camera-blocks-free-motion`、`data-radar-blocks-free-motion`、`data-mapping-start-ready`、`data-mapping-start-missing-reasons`、`data-mapping-acceptance-ready`、`data-mapping-acceptance-missing-reasons` 和固定 endpoint 属性。
  - `plain-free-roam-start` 主按钮新增 `data-can-start-free-motion`、`data-sends-motion-when-clicked`、`data-requests-mapping-when-clicked`、`data-requires-safety-confirmation`、`data-minimal-precheck-safety-only` 和固定 endpoint 属性。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展默认首屏测试，证明未勾安全确认时主按钮不发车，但自由移动 ready 且相机/雷达不阻塞自由移动；建图启动缺口仍暴露为相机首帧和雷达 fresh。
  - 扩展建图 ready 测试，证明画面和雷达 ready、只差地图记录时，主按钮会先走 `/api/robot-control/map/start`，再走 `/api/robot-control/free-roam/autonomy/start`，并在 DOM 中声明会请求建图和自由移动。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 记录 2026-06-30 17:25 CST 的自由移动 / 建图主面板 DOM 合同。

## 验证结果

- 已通过:
  - `cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - `cd pc-tools/workstation && npm test -- test/App.test.ts -t "points mapping-ready users to start the map recording when only mapping runtime is missing"`
  - `cd pc-tools/workstation && npm test -- --run`
    - 结果: `Test Files 2 passed (2)`, `Tests 389 passed (389)`
  - `cd pc-tools/workstation && npm run build`
    - 结果: TypeScript 与 Vite build 通过，生成 `dist/assets/index-TkmUu_Af.js` 和 `dist/assets/index-BZI7zFw0.css`
  - `git diff --check`
    - 结果: 通过，无 whitespace error
  - 重启并验证 `0.0.0.0:7001`
    - 结果: `node` 监听 `TCP *:7001`
  - `curl -fsS http://127.0.0.1:7001/`
    - 结果: 返回 `Rober PC Tools Workstation`，资产为 `index-TkmUu_Af.js` / `index-BZI7zFw0.css`
  - `curl -fsS http://127.0.0.1:7001/assets/index-TkmUu_Af.js | rg ...`
    - 结果: 构建产物包含 `data-free-move-start-ready`、`data-mapping-start-ready`、`data-fixed-mapping-start-endpoint`、`data-fixed-free-roam-start-endpoint`、`data-requests-mapping-when-clicked`
  - `GET http://127.0.0.1:7001/api/robot-control/summary`
    - 结果: HTTP 200，`schema=trashbot.pc_tools_workstation.robot_control_summary.v1`，`free_roam_motion_start_ready=true`，`free_roam_mapping_start_ready=false`，`free_roam_mapping_start_missing_reasons=["lidar_fresh"]`

## 剩余风险

- 本轮只补 PC 普通首屏 DOM 合同和前端测试；没有对真实小车发运动命令，也没有证明真实底盘、相机、雷达、Nav2 或建图 runtime 的 HIL 结果。
- 旧 artifact 文件仍有历史未提交改动，本轮不会纳入提交范围。
