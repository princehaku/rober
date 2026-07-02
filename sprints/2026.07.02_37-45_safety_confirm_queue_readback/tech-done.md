# Safety Confirm Queue Readback

## sprint_type

micro

## 实际改动

- 在 PC workstation summary 的 `current_safety_confirm_queue_*` 中新增队列读回标签、读回按钮文案和 `readback_refreshes_*` 标志。
- 在普通用户 PC 首页 `plain-current-safety-confirm-queue` 上新增 `plain-current-safety-confirm-queue-readback` 按钮。
- 该按钮按队列动作顺序只读刷新 Nav2 行程、键盘轮速、自由移动等验收读回：map preview、Nav2 latest、wheel feedback、delivery latest、summary 和 free-roam latest。
- 固定该按钮不发送运动、不启动 Nav2/manual/keyboard/free-roam/建图/delivery/stop。
- 更新 summary 与 App 单测，固定读回端点、读回标签和 no-motion 边界。
- 更新 `docs/product/pc_tools_workstation.md`，同步说明队列读回按钮用途和边界。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，10 tests passed。
- 通过：`npm test -- test/App.test.ts`，237 tests passed。
- 通过：`npm run build`，TypeScript 与 Vite build 均完成；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 `0.0.0.0:7001`，新 PID `90224`。
- 通过：只读读取 `/api/robot-control/summary`，现场返回 `current_safety_confirm_queue_status=ready_for_safety_confirm`、`current_safety_confirm_queue_readback_button_label=只读复验队列`、`current_safety_confirm_queue_readback_sequence_labels=[刷新地图画面,读取最近行程,复验轮速采样,读取送达确认,刷新总览,读取自由移动状态]`、`current_safety_confirm_queue_readback_endpoints=[/api/robot-control/map/preview,/api/robot-control/nav2/goal/execution/latest,/api/robot-control/base/feedback-samples,/api/robot-control/delivery/latest,/api/robot-control/summary,/api/robot-control/free-roam/autonomy/latest]`、所有 `current_safety_confirm_queue_readback_refreshes_*` 为 `true`、`current_safety_confirm_queue_sends_motion_when_clicked=false`、`current_safety_confirm_queue_readback_sends_motion=false`、`current_radar_map_wysiwyg_pack_status=loaded`。

## 剩余风险

- 本轮不发送真实运动命令；队列读回按钮用于现场执行动作后的只读复验。
- 建图仍受相机首帧阻塞；自由移动仍可在安全确认后先做。
