# 2026-06-28 18:45 PC 当前事实雷达贴图 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的雷达行新增地图贴图口径。
  - 地图预览随图雷达点已贴到地图坐标时显示“地图预览雷达点 N 个已贴到地图”。
  - 只有雷达局部轮廓时显示“雷达局部轮廓 N 个，未贴到地图”。
  - 点数-only、距离-only 和旧雷达点不会被升级成地图坐标点；该改动只消费只读 summary/map preview。
- `pc-tools/workstation/test/App.test.ts`
  - 加强地图预览雷达 overlay 测试，锁定当前事实与地图 marker/caption 的所见即所得一致性。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏当前事实雷达贴图口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "map preview radar overlay"`
  - 结果：1 个测试文件通过，2 个目标测试通过，195 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，345 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮未做真实雷达、真实地图或真车 HIL；验证范围限定在 PC 普通首屏只读展示和回归测试。
- 未发送任何 radar start/refresh、manual、keyboard、Nav2、delivery、free-roam、stop 或 `/cmd_vel` 请求。
