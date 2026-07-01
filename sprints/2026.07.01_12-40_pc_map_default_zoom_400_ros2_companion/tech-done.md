# PC 地图默认 400% 与 ROS2 配套说明

sprint_type: micro

## 实际改动

- 将 PC 普通首屏和 `/map` 直达地图的默认细节视图从 `300%` 提升到 `400%`，保留 `100%` 适配全图和 `2400%` 细节放大。
- 同步 `live_closure_summary` 地图显示合同，让 summary、DOM 和测试夹具都暴露当前默认缩放 `400%`。
- 保留普通用户简易 PC 工作站为主入口；ROS2 配套继续作为工程观察：本地 RViz2 使用 `ros2 launch ros2_trashbot_bringup rviz.launch.py`，远程浏览器观察使用 Foxglove bridge。
- 更新 `docs/product/pc_tools_workstation.md`，明确 RViz2/Foxglove 只读观察用途，不启动 ROS2/RViz2/Foxglove、Nav2、建图 runtime 或任何运动命令。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，结果 `1 passed | 230 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite build 成功；仍提示既有 chunk 大小 warning。
- 通过：`npm test`，结果 `3 passed` test files，`417 passed` tests。
- 通过：`git diff --check`。

## 剩余风险

- 这轮只改 PC 显示和只读合同；未执行真实 RViz2 桌面 HIL，也未触发任何小车运动。
- 工作区仍有两个历史 artifact 脏文件，本轮不纳入提交。
