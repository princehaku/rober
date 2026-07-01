# PC 地图默认全图适配

sprint_type: micro

## 实际改动

- 将普通 PC 首屏和 `/map` 直达地图大屏的默认缩放从 `600%` 调整为 `100%` 全图适配，避免真实地图进入页面后默认只显示局部空白区域。
- 修正真实地图 overlay frame 的 `min-height` 覆盖，避免 261x113 这类窄地图被强行拉伸到 1120px 高，保证默认视图按原始比例显示。
- 保留 `细节放大` 到 `2400%`、`+/-` 逐级缩放和 `适配` 回到 `100%`，地图、路线、小车位置和雷达点仍在同一张 WYSIWYG 画布上缩放。
- 同步更新 `live_closure_summary` 地图显示合同、TypeScript contract、App/summary 测试和 PC workstation 文档；RViz2/Foxglove 仍只作为工程观察配套，不作为普通用户主界面。

## 验证结果

- `npm test -- --run test/App.test.ts -t "map"`：通过，67 passed / 164 skipped。
- `npm test -- --run test/robotControlSummary.test.ts`：通过，8 passed。
- `npm run lint`：通过。
- `npm run build`：通过，Vite build 完成，保留 chunk size warning。
- `npm test`：通过，3 files / 420 tests。
- `git diff --check`：通过。
- 重启 PC Node 到 `0.0.0.0:7001` 后浏览器实测通过：`plain-map-panel` 显示 `data-map-zoom-percent=100%`、`data-map-zoom-scale=1`；真实图片自然尺寸 `261x113`，页面 frame 为 `1224x530`，比例约 `2.31`，与原图一致；首屏能看到地图结构、路线框和雷达点。

## 剩余风险

- 本轮只改变 PC 地图默认显示缩放，不执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实路线执行、wheel raw L/R 非零、delivery success、键盘连续手控和建图启动仍按当前 goal 继续推进。
