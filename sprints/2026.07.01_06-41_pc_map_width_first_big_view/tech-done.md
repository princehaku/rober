# PC 大地图宽屏铺满

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`：真实地图底图从“高度撑满”改为“宽度优先撑满、保持原始比例、纵向滚动查看”，解决宽屏 PC 上正方形/窄地图只占中间小块的问题。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：在地图面板和地图显示证明条增加 `data-real-map-fit-mode=width-first-preserve-aspect-scroll-y`，把显示合同暴露给 DOM 验收。
- `pc-tools/workstation/test/App.test.ts`：锁定地图宽度优先铺满合同，并确认该改动仍只影响显示，不改变缩放、WYSIWYG overlay 或运动边界。
- `docs/product/pc_tools_workstation.md`：同步说明 PC 普通地图仍是主路径，ROS2 配套为 RViz2/Foxglove 工程观察，不作为普通用户发车前置。

## 验证结果

- `npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 passed / 229 skipped。
- `npm test -- --run test/App.test.ts -t "direct map"`：通过，3 passed / 227 skipped。
- `npm test -- --run test/robotControlSummary.test.ts`：通过，6 passed。
- `npm run build`：通过，Vite 输出 `dist/assets/index-BCGZQzjE.css` 与 `dist/assets/index-Dnj0kaV8.js`；仍有既有 chunk size warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听子进程 PID `29733`；`GET http://127.0.0.1:7001/api/health` 通过，`GET http://127.0.0.1:7001/map` 返回当前构建资源。
- 已从 `http://127.0.0.1:7001/assets/index-BCGZQzjE.css` 确认新 CSS 规则包含 `.plain-map-layer.has-real-map .plain-map-overlay-frame`、`height:auto`、`min-width:100%`。

## 剩余风险

- 本轮只做 PC CSS/DOM 显示修正，没有启动 RViz2/Foxglove，也没有发送 Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。
- live summary 可读到小车上位机，但现场仍有相机首帧失败/部分 Robot API 状态 blocked；这是现有传感器/状态缺口，不影响本轮地图宽度优先显示合同。
- 真实浏览器视觉效果仍建议在现场 PC 刷新 `http://<pc-ip>:7001/map` 后肉眼确认；如果用户希望“默认细节更大”而不是“底图宽度铺满”，下一轮可把默认缩放从 100% 调整为 150%。
