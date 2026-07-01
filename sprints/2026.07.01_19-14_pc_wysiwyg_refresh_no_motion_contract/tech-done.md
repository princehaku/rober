# PC 所见刷新只读边界合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-live-closure-wysiwyg-refresh` 补齐 `data-submits-delivery=false` 和 `data-stops-motion=false`。
  - `plain-wysiwyg-evidence-refresh` 补齐地图预览、雷达状态、相机 MJPEG 状态固定 endpoint 与 refresh 声明。
  - `plain-wysiwyg-evidence-refresh` 补齐不启动雷达 lifecycle、建图 runtime、Nav2、manual、keyboard、free-roam，不提交 delivery、不 stop、不发送运动的 DOM 合同。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展普通首屏 WYSIWYG 刷新按钮断言，证明按钮只刷新画面/雷达/地图读回，不触发 motion、delivery 或 stop。
- `docs/product/pc_tools_workstation.md`
  - 同步“画面/地图/雷达点所见即所得”刷新按钮的只读边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "Robot Control V1|WYSIWYG|wysiwyg|当前所见|live closure"`，1 file passed，4 tests passed。
- 通过：`git diff --check`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 大 chunk warning 为既有提示，构建成功。
- 通过：`cd pc-tools/workstation && npm test -- --run`，3 files passed，421 tests passed。
- 通过：7001 工作站返回新 bundle `index-DtjgPYSC.js`，其中包含 `plain-live-closure-wysiwyg-refresh`、`plain-wysiwyg-evidence-refresh`、`data-submits-delivery` 和 `data-stops-motion`。
- 通过：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 WYSIWYG 刷新序列 `/api/robot-control/radar/scan-proof/refresh`、`/api/robot-control/camera/first-frame/probe`、`/api/robot-control/map/preview`、`/api/robot-control/radar/status`、`/api/robot-control/camera/mjpeg/status`，且 `live_wysiwyg_refresh_sends_motion=false`、`live_wysiwyg_refresh_starts_nav2=false`、`live_wysiwyg_refresh_starts_radar_lifecycle=false`。

## 剩余风险

- 本轮只加固 PC DOM 合同和测试，不启动真实雷达 lifecycle，不执行 Nav2/manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 当前真实 summary 仍显示画面未出帧、雷达点未贴图；需要现场继续复测相机硬件、启动/刷新雷达并刷新地图预览。
