# 2026.06.30 06:05 PC 地图放大与最小预检合同

sprint_type: micro

## 实际改动

- PC 普通首屏地图默认缩放从 `125%` 提升到 `150%`，缩放档位扩展到 `300%`，并把大图/全屏地图高度继续提高，解决 PC 上地图仍显得偏小的问题。
- 地图卡新增 `data-default-map-zoom-percent=150%`，ROS2 配套提示保留 RViz2 调试入口，并补充 Foxglove 作为浏览器远程观察工具；普通用户仍留在简易 PC 工作站大地图，不进入复杂 ROS 面板。
- PC 手控/首次点动/停止代理响应补齐最小预检合同字段，明确低速运动只要求现场安全确认，operator report、相机和雷达材料不再作为普通手控前置。
- 同步更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`，记录地图、ROS2 配套工具和最小预检最新口径。

## 验证结果

- `npm test -- test/App.test.ts -t "allows confirmed low-speed motion when operator visual material is incomplete and still allows stop"`：通过，`1 passed | 218 skipped`。
- `npm test -- test/App.test.ts -t "enables non-stop motion only after complete operator material and still uses the fixed workstation proxy"`：通过，`1 passed | 218 skipped`。
- `npm test -- --run`：通过，`2 passed` test files，`389 passed` tests。
- `npm run build`：通过，Vite 仅保留既有 chunk size warning。
- `git diff --check`：通过，无 whitespace error。
- 7001 smoke：`node` 进程 `90265` 监听 `*:7001`；`curl -fsS http://127.0.0.1:7001/` 返回当前 `index-BZdwxS-k.js` / `index-Dp17eOUy.css`；dist bundle 可检出 `default-map-zoom-percent`、`Foxglove`、`minimal_precheck_safety_only`、`manual minimal precheck`、`operator_report_required`、`camera_or_radar_required`。

## 剩余风险

- 本轮只修改 PC Web 只读显示、代理响应合同和文档，不发送真实运动命令，不等于真实 HIL 已完成。
- RViz2/Foxglove 作为 ROS2 配套观察工具写入提示和文档，本轮不自动安装、启动或配置 Foxglove Bridge。
