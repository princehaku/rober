# PC map engineering observer label

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/App.vue`：顶部普通入口从 `地图大屏` 改为 `地图大屏 /map`，让现场看到地图太小时的直接入口。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：地图卡里的 ROS2 配套按钮从 `ROS2观察` 改为 `工程观察`，避免普通用户误以为要先进入 ROS2 工具才能看地图。
- `pc-tools/workstation/src/styles.css`：同步注释口径，明确首页只显示工程观察开关，展开后才是 RViz2/Foxglove 只读入口。
- `pc-tools/workstation/test/App.test.ts`：更新普通入口和地图卡按钮的断言，继续验证 `/map` 不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime，也不发运动命令。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`：同步产品口径。普通用户解决地图太小优先用 PC 首页大地图或 `/map`；ROS2 配套为 RViz2 与 Foxglove 工程观察，不替代普通 PC UI。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "map display|direct map|ROS2|Foxglove"`，1 file passed，4 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`，1 file passed，239 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积 warning，本轮没有新增 build error。

## 剩余风险

- 本轮只收敛 PC 地图入口和 ROS2 配套可见文案，没有启动或部署 RViz2/Foxglove，也没有执行真实浏览器截图验收。
- 相机实时首帧、wheel raw L/R 非零、完整 Nav2 真实移动和 delivery success 不属于本轮改动，仍按当前现场硬件/闭环风险继续推进。
