# 2026-06-26 01:30 PC 键盘停止后地图保留方向

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏扫地式建图在键盘/屏幕方向键松开并完成 stop 收口后，地图流程 marker 保留上次方向和轮速结论。
  - 保存前刷新完成时显示 `已停可保存：前进，轮速非零`；尚需刷新时显示 `已停待刷新：前进，轮速待非零`。
  - marker 的可访问说明同步包含上次方向、停止原因和 L/R 读数。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 free-roam 键盘流程测试，覆盖 stop 后地图 marker 文案和 aria。
  - 继续验证松开后不会调用 Nav2 execute 或 delivery complete。
- `docs/product/pc_tools_workstation.md`
  - 记录键盘停止后地图 marker 的 WYSIWYG 口径和安全边界。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步扫地式建图向导设计。

## 验证结果

- 通过：`npm test -- -t "keeps free-roam keyboard locked until map recording starts"`
  - `Test Files 1 passed | 1 skipped (2)`
  - `Tests 1 passed | 178 skipped (179)`
- 通过：`npm run lint`
- 通过：`npm run build`
  - `vite v7.3.3 building client environment for production`
  - `dist/assets/index-D0bglJSM.js 475.18 kB`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 179 passed (179)`
- 通过：`git diff --check`
  - 无输出，未发现空白或 diff 格式问题。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node ... TCP *:7001 (LISTEN)`

## 剩余风险

- 本轮只覆盖 PC 前端状态呈现和 mock 组件测试，不触发真实建图、manual、keyboard pulse、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实现场仍需在 `0.0.0.0:7001` 页面按住并松开方向键，复核地图 marker 与实际底盘反馈是否一致。
