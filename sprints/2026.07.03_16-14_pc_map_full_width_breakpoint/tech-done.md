# PC 地图全宽断点

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/styles.css`：新增 `1600px` 以下的普通首页地图优先断点。常见 PC 宽度下地图先占整行全宽，`900px-1600px` 时共享图传和 WASD 放在第二行并排，`900px` 以下纵向排列。该改动只影响显示布局，不触发 ROS2/RViz2/Foxglove/Nav2/建图 runtime，也不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`：同步当前“地图太小”的 UI 口径，以及 ROS2 配套分层：普通用户优先 PC 大地图和 `/map`；工程观察用 RViz2 或 Foxglove bridge。

## 验证结果

- 修改前 Chrome headless DOM 探针：1440x900 首页地图画布约 `1018x756`，右侧图传/手控栏固定 `360px`。
- `npm test -- --run App.test.ts -t "map|地图|RViz2|Foxglove"`：通过，1 个 test file，70 passed。
- `npm run lint`：通过。
- `npm run build`：通过；仍只有既有 Vite chunk size warning。
- `npm test`：通过，3 个 test files，439 passed。
- 7001 重启后 `GET /api/health`：`workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 修改后 Chrome headless DOM 探针：1440x900 首页第一个可见面板为 `plain-map-panel`，地图面板 `1418x888`，实际地图画布 `1388x810`；`/map` 直达页地图面板 `1440x876`，非地图卡片隐藏。

## 剩余风险

- 这轮只处理 PC 地图显示面积和 ROS2 配套说明，不证明相机首帧、wheel raw L/R 非零、真实 Nav2 HIL 或 delivery success。
