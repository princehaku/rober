# 2026.07.03 04:40 PC 大地图与 ROS2 观察口径同步

sprint_type: micro

## 实际改动

- 同步 PC 工作站地图显示验收测试：当前有效大地图口径为 `width: min(3200px, 100%)`、首页 `4fr/300px` 驾驶台、large 地图最小 `960px`、最高缩放 `800%`。
- 更新 `docs/product/pc_tools_workstation.md` 的当前合同，明确普通用户优先用 PC 大地图和 `/map`，ROS2 配套为工程观察：本地 RViz2、远程 Foxglove bridge + Foxglove Web。
- 清理文档中仍冒充当前口径的 `3200%/6400%` 缩放说明，避免后续迭代按旧实验尺寸把地图做回超宽滚动画布。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "direct map|地图|ROS2|RViz|Foxglove|plain-map"`（1 file / 4 tests passed / 233 skipped）
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`（1 file / 237 tests passed）
- 通过：`cd pc-tools/workstation && npm run build`（Vite 仅提示 chunk size warning）
- 通过：`git diff --check`
- 通过：重启 PC Node 到 `0.0.0.0:7001`，新 PID 为 `19805`；`GET /` 和 `GET /map` 均返回构建后的前端入口。
- 通过：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 读回 `map_display_primary_url=/map`、`map_display_default_zoom_percent=300%`、`map_display_max_zoom_percent=800%`、`map_display_engineering_tools_action_label=工程观察：RViz2 / Foxglove`、RViz2 launch、Foxglove bridge launch 和 `ws://192.168.1.11:8765`。

## 剩余风险

- 本轮没有启动真实 RViz2/Foxglove bridge，也没有做真实浏览器截图或 ROS2 HIL；只是把 PC 页面当前大地图合同、测试和文档同步到一致状态。
- 仓库里既有两个 2026.06.11 artifact 脏文件，本轮未修改也不纳入提交。
