# PC 普通首屏当前画面记录

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `移动/导航` 新增 `用当前画面记录`。
  - 点击后只调用固定 `camera/first-frame/probe` 获取当前样张 ref，再提交固定 operator report。
  - camera 样张材料会写入 `visible_content_proven=true` 和 `camera_artifacts_ref=<sample>`；手填视频编号仍走原 `记录画面`，不伪造相机可见。
  - 画面探针执行中，首屏移动状态显示 `正在读取当前画面；不会发车。`
- `pc-tools/workstation/test/App.test.ts`
  - 增加普通首屏当前画面记录测试，断言只调用 camera probe 和 operator report，不调用 first-jog/manual/Nav2/delivery/`/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录当前画面记录入口和安全边界。

## 验证结果

- 通过：`npm test -- -t "current camera frame|plain video reference"`（2 passed，170 skipped）
- 通过：`npm run lint`
- 通过：`npm test`（172 passed）
- 通过：`npm run build`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`（`node` 监听 `*:7001`，未使用 Clash 端口）

## 剩余风险

- 本轮是 PC/mock 层材料记录增量，没有触发真实 first-jog、manual、Nav2 execute、delivery complete、stop 或 `/cmd_vel`。
- 真实相机样张质量仍取决于上位机 `camera/first-frame/probe` 和现场光照；若 probe 没有 sample ref，按钮不会提交空材料。
