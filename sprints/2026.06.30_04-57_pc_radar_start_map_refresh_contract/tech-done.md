# PC 雷达启动后地图同轮刷新合同

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏雷达面板新增结构化合同：
    - `data-radar-start-refreshes-proof=true`
    - `data-radar-start-refreshes-map-preview=true`
    - `data-radar-restart-refreshes-map-preview=true`
    - 固定雷达 proof 和地图 preview endpoint。
  - 雷达刷新、启动、重启按钮同步暴露是否会刷新 proof 和地图 preview 的 `data-*` 字段。
  - 仅在雷达需要启动或重启时显示普通提示：启动或重启后会自动刷新雷达读数和地图画面，返回前不把旧点当当前地图标记。
- `pc-tools/workstation/test/App.test.ts`
  - 补齐雷达启动按钮、雷达面板和自动地图刷新合同断言。
  - 继续验证雷达启动不发送底盘 manual、Nav2、delivery 或 `/cmd_vel`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录“雷达开始后地图标记所见即所得”的前端合同和安全边界。

## 验证结果

- `npm test -- test/App.test.ts -t "shows plain radar start only when the readback says lidar is stopped"`
  - 结果：通过，`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `npm test -- test/App.test.ts -t "auto-refreshes radar proof after plain radar start reports ok"`
  - 结果：通过，`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `npm run build`
  - 结果：通过，Vite 产物包含 `dist/assets/index-KkJaNEb-.js`。
- `npm test -- --run`
  - 结果：通过，`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- `git diff --check`
  - 结果：通过，无空白错误。
- PC Node 重启与 HTTP smoke
  - `npm run api -- --host 0.0.0.0 --port 7001` 已重新监听，`lsof` 显示 `node` 监听 `TCP *:7001`。
  - `GET http://127.0.0.1:7001/` 返回新 bundle：`index-KkJaNEb-.js`。
  - JS bundle 已包含 `data-radar-start-refreshes-proof`、`data-radar-start-refreshes-map-preview`、`data-refreshes-map-preview-after-start`、`data-refreshes-map-preview-after-restart`、`data-refreshes-map-preview-after-proof` 和 `plain-radar-map-refresh-contract`。

## 剩余风险

- 本轮只补 PC Web 合同与测试，不自动点击雷达启动、不启动 ROS2 runtime、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实地图雷达点是否出现仍依赖上车 `/api/radar/start`、`/api/radar/scan-proof/refresh`、`/api/map/preview` 返回真实新扫描与 map-frame 坐标；PC 侧负责在启动/重启后自动刷新并防止旧点冒充当前点。
