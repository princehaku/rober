# PC Nav2 Controller Plain Readback

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏自动驾驶当前态在 `controller_server_active=false` 时，下一步改为先恢复控制服务，再准备图上行程并按地图画面确认。
  - 地图 `行程读数` 同时显示规划服务和控制服务状态，避免把 controller inactive 淹没在路线/定位缺口里。
  - 旧 Nav2 action succeeded 但 wheel raw L/R 未闭环时，自动驾驶诊断会在普通首屏显示 `Nav2 controller 未 active，重跑前先恢复`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新地图读数断言，覆盖控制服务 `已运行 / 未读取` 文案。
  - 增加 ROS/T=13 非零命令但 wheel raw L/R=0/0 且 controller inactive 的普通首屏断言。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏和地图行程读数新增 controller 状态展示。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 controller blocker 在前端 WYSIWYG 的消费方式。

## 验证结果

- `npm test -- test/App.test.ts -t "plain map|ROS T13 command evidence" --maxWorkers=1 --no-fileParallelism`
  - 通过：1 个测试文件，4 个相关用例通过。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示 bundle 超过 500 kB，这是既有体积 warning。
- `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 通过：2 个测试文件，316 个用例通过。
- `git diff --check`
  - 通过，无空白错误。

## 剩余风险

- 本轮只修正 PC 端只读呈现，不自动恢复 Nav2 controller，也不触发真实 Nav2 execute 或底盘运动。
- live 当前仍需上车端恢复 controller、生成图上路线、读到 robot map pose，并在现场安全确认后重跑 Nav2，才能复验同窗口 wheel raw L/R 非零。
- 摄像头当前无首帧仍是 UVC/输入/供电层面问题；共享预览不是浏览器独占，但本轮没有做硬件侧相机修复。
