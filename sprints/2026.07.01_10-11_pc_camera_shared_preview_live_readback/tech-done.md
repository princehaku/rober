# PC 当前卡点相机共享预览读回

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：
  - `plain-live-camera-recovery-readback` 增加共享预览状态 DOM：viewer 数、upstream active、exclusive claim、single upstream、auto joins、固定 MJPEG endpoint 和 status endpoint。
  - 可见文案直接显示“共享预览：单上游多人共享，当前 N 个页面观看；上游已/未连接；页面独占=false”。
- `pc-tools/workstation/test/App.test.ts`：补充当前卡点相机恢复条的共享预览 DOM 和文案断言。
- `docs/product/pc_tools_workstation.md`：记录当前卡点相机共享预览读回合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 file passed，1 test passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，7 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 仍提示既有 bundle size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，417 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，PID `40423`；`HEAD http://127.0.0.1:7001/map` 返回 `200`。
- 通过：只读 live summary `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `live_wysiwyg_camera_recovery_status=not_exclusive_needs_source_check`、`live_wysiwyg_camera_shared_preview_client_count=0`、`live_wysiwyg_camera_shared_preview_upstream_active=false`、`live_wysiwyg_camera_shared_preview_exclusive_camera_claim=false`，下一步仍是换高速 USB 口/线或带供电 Hub 后复测。

## 剩余风险

- 本轮只补 PC 当前卡点读回，不打开独占相机、不重置 USB、不改变 MJPEG relay、不启动建图或任何运动命令。
- live 当前相机仍未出帧；需要现场把摄像头接到高速 USB 口/线或带供电 Hub 后复测。
