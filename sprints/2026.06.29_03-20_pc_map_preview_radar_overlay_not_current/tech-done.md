# 2026.06.29 03:20 PC map preview radar overlay not_current

sprint_type: micro

## 实际改动

- `RobotControlMapPreviewRadarOverlay.overlay_status` 新增 `not_current`，用于表达地图预览随图读取到旧雷达点但不能作为当前点绘制。
- `/api/robot-control/map/preview` 的 `radar_overlay` 同轮读取 free-roam latest、radar status 和 scan proof：当 runtime `/scan` stale 或 radar lifecycle stopped 时，返回 `not_current`，清空可绘制点数组和点数，只保留 source count/frame id 供诊断。
- 更新 catalog 合同测试，覆盖 stopped/stale 旧雷达点不贴图，同时确认正常 loaded/partial overlay 路径不回归。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md`，记录只读边界：不启动雷达、不刷新 proof、不发送 manual/Nav2/free-roam/delivery/stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- --run test/catalog.test.ts -t "map preview radar overlay"`，2 passed。
- 通过：`npm test -- --run test/App.test.ts -t "draws map preview radar overlay when summary scan points are missing"`，1 passed。
- 通过：`npm test -- --run test/App.test.ts -t "shows partial map preview radar overlay as local scan until robot map pose exists"`，1 passed。
- 通过：`npm test -- --run test/catalog.test.ts -t "workstation map lifecycle proxies use fixed endpoints and whitelist short request body fields"`，1 passed。
- 通过：`npm test -- --run`，2 files / 360 tests passed。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 输出 chunk size warning，构建成功。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只修 PC map preview radar overlay 的只读实时性门禁，不代表现场雷达 lifecycle、相机首帧、Nav2 planner/controller 或真车 HIL 已恢复。
