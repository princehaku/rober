# PC 地图默认 8000% 大图

sprint_type: micro

## 实际改动

- 将 PC 普通地图和 `/map` 直达大屏的默认缩放从 `4800%` 提升到 `8000%`，最高细节放大仍保持 `9600%`，`适配` 仍回到 `100%` 全图。
- 同步更新 `GET /api/robot-control/summary` / live closure summary / shared contract / DOM 测试里的 `map_display_default_zoom_percent=8000%`。
- 保持 ROS2 配套分层不变：普通用户优先用 PC 特大地图和 `/map`；RViz2/Foxglove 只作为工程观察，不作为发车入口。

## 验证结果

- 通过：`npm test -- test/App.test.ts`，237 个测试通过。
- 通过：`npm test -- test/robotControlSummary.test.ts test/catalog.test.ts`，193 个测试通过。
- 通过：`npm run build`；仅保留 Vite 大 chunk 提醒。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只调整 PC 显示默认缩放和说明合同，不包含真实浏览器截图验收；真实地图视觉大小仍建议现场打开 `http://<PC>:7001/map` 复看。
