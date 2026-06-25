# 2026.06.26 02:52 PC 当前画面探针失败 WYSIWYG

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `cameraProbePlainFailureHint()`，普通首屏会消费本次 `camera/first-frame/probe` 的失败结果。
  - `cameraSourcePlainFailureHint()` 同时读取 summary 归因和本次 probe 归因；当 probe timeout、open/read 失败或本机 fallback 时，实时画面框和 `画面状态` 显示 `相机没有出画面，检查摄像头/视频线。`。
  - 成功 probe 不会把未打开的 WebRTC 画面伪装成实时画面，只修正失败的可见反馈。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `shows current camera probe failure on the plain first screen without submitting material`，覆盖 `用当前画面记录` 遇到首帧 timeout 时，普通画面框/状态显示失败，且不提交 operator report、不调用 first-jog/manual/Nav2/delivery 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录当前画面探针失败贴回普通首屏画面框的产品口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "shows current camera probe failure on the plain first screen"`
  - 结果：通过，`1 passed | 181 skipped (182)`。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过，`eslint .` 无报错。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `cd pc-tools/workstation && npm test`
  - 结果：通过，`2 passed (2)`，`182 passed (182)`。
- `git diff --check`
  - 结果：通过，无空白错误。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：`node` 正在监听 `TCP *:7001 (LISTEN)`。

## 验证副作用处理

- 全量 Vitest 会刷新旧 DOM smoke artifact 的 `checked_at` 字段；本轮已将
  `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`
  和
  `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`
  恢复到原始时间戳，避免旧证据被误记为本轮产物。

## 剩余风险

- 本轮只做 PC mock/DOM 验证，没有连接真实摄像头跑实体 first-frame probe。
- 该改动只让失败可见，不修复真实摄像头、视频线、驱动或上位机 camera service 问题。
