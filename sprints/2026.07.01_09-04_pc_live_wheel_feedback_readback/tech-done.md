# 2026.07.01 09:04 PC 共享轮速验收读回

## sprint_type

micro

## 实际改动

- 在 PC 普通首屏动作清单顶部新增 `plain-live-wheel-feedback-readback`，把完整行程执行和键盘连续手控共同缺的同窗口 wheel L/R 非零证据前置显示。
- 新增 `plain-live-wheel-feedback-readback-refresh`，只读回 `/api/robot-control/base/feedback-samples` 和 `/api/robot-control/summary`。
- DOM 明确暴露受影响动作 ids、最新 wheel raw L/R、样本数、非零样本数、固定读回端点和 no-motion 边界。
- 该入口不重跑 Nav2、不启用手控/键盘、不启动自由移动/建图、不提交 delivery、不 stop、不发送 motion。
- 更新 PC 工作站产品边界文档，记录共享轮速验收条。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，结果 `1 passed | 230 skipped`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，生成 `dist/assets/index-BfGMLw1v.js` 与既有 CSS；仅保留 Vite 大 chunk 提示。
- 通过：`cd pc-tools/workstation && npm test`，结果 `3 passed`、`417 passed`。
- 通过：`git diff --check`。
- 通过：重启 PC API 后 `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `*:7001`，PID `2112`。
- 通过：`curl -I http://127.0.0.1:7001/map` 返回 `HTTP/1.1 200 OK`。
- 通过：构建产物 `dist/assets/index-BfGMLw1v.js` 包含 `plain-live-wheel-feedback-readback`、`轮速验收` 和 `读回轮速`。
- 通过：真实 no-motion `GET /api/robot-control/base/feedback-samples` 返回 `proxy_status=samples_forwarded`、`status=loaded`、`robot_control_executed=false`。
- 通过：随后 `GET /api/robot-control/summary` 返回 `wheel_lr_nonzero=false`、`wheel_rerun_feedback_sample_count=239`、`wheel_rerun_feedback_nonzero_sample_count=0`、`wheel_rerun_latest_raw_left=0`、`wheel_rerun_latest_raw_right=0`，符合当前尚未完成同窗口轮速闭环的事实。
- 通过：no-motion 刷新雷达贴图后，`GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_point_count=157`，summary 返回 `radar_map_points_visible=true`。

## 剩余风险

- 当前改动是 PC 只读 UI/DOM 合同；wheel L/R 非零仍需要现场勾安全确认后执行 Nav2 路线或按住键盘，并在同一运动窗口读回。
- 完整 Nav2 闭环仍缺同窗口 wheel L/R 非零和 delivery success；相机仍需现场修复 USB full-speed 链路后复测。
