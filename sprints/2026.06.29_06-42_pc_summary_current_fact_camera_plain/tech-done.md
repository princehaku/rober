# Summary 当前事实相机普通话口径

- sprint_type: micro
- 时间：2026-06-29 06:42 CST
- Owner：User Touchpoint Full-Stack Engineer（主会话执行；本轮按用户要求不调用 subagent）

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `currentFactCameraPart()`，仅在 `current_fact_plain` 顶层总事实里把相机片段从工程口径转换成普通用户口径。
  - `画面未可见` 在总事实中显示为 `画面未显示`，`不当作画面可见` 显示为 `不当作已经看到画面`。
  - 底层 `readback_summary.camera.camera_wysiwyg_status_plain` 保持兼容原文，继续服务精细诊断。
- `pc-tools/workstation/test/catalog.test.ts`
  - 锁定 summary API 顶层总事实不再出现 `画面未可见`，同时确认底层 camera readback 仍保持原合同。
- `pc-tools/workstation/test/App.test.ts`
  - 同步默认 fixture 的 `current_fact_plain`，避免后续前端直接消费该字段时带回旧口径。
- `docs/product/pc_tools_workstation.md`
  - 记录 `current_fact_plain` 相机片段普通话口径和只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`
  - 结果：1 个测试文件通过，38 个用例通过，122 个同文件用例按过滤跳过。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`
  - 结果：1 个测试文件通过，1 个用例通过，214 个同文件用例按过滤跳过。
- 通过：`npm --prefix pc-tools/workstation run build`
  - 结果：TypeScript 与 Vite build 通过；保留既有 Vite chunk size warning。
- 通过：`npm --prefix pc-tools/workstation test`
  - 结果：2 个测试文件通过，375 个用例通过。
- 通过：重启 PC API 到 `0.0.0.0:7001`，实际监听 PID `1124`。
  - 只读 `GET /api/robot-control/summary` 结果：`current_fact_plain` 以 `画面未显示：不是页面独占...` 开头；底层 `readback_summary.camera.camera_wysiwyg_status_plain` 仍为 `画面未可见：不是页面独占...`；`viewer_count=0`、`upstream_connected=false`、`has_recent_frame=false`。

## 剩余风险

- 本轮只改 PC summary 顶层文案，不触发真实相机 reader、不调用 manual/stop/Nav2/free-roam/delivery。
- live 相机源仍可能保持 UVC 首帧失败；本轮只确保总事实明确说明不是页面独占、画面未显示。
