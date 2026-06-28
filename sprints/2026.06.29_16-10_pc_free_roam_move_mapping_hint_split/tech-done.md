# PC 自由移动建议与建图缺口拆分

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 中拆分上车端 `free_roam_autonomy_next_action` 的普通文案。
- 当 next_action 同时包含“可先自由移动”和“建图验收还差”时，PC 首页改为分别显示自由移动建议与建图缺口，避免把相机/雷达/地图记录缺口误读成发车前预检。
- 自由移动下一步按钮只消费移动相关建议；只有出现 `建图验收...` 段时才拆分，普通自动扫图建议里的后续监看文案保持完整。
- 在 `pc-tools/workstation/test/App.test.ts` 更新断言，确保“上车建议：已勾安全确认，可先自由移动”和“建图缺口：画面首帧”分开展示。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "allows free-roam keyboard while camera is not ready|reuses one plain safety confirmation|allows recording on stale radar proof"` 通过：2 tests passed。
- `npm --prefix pc-tools/workstation test` 通过：2 files passed, 368 tests passed。
- `npm --prefix pc-tools/workstation run build` 通过；仅保留 Vite chunk size 既有警告。
- 只读查询 `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 通过，现场为 `free_roam.status=start_ready`、`free_roam_autonomy_start_ready=true`、`free_roam.mapping_ready=false`，next_action 同时包含“可先自由移动”和“建图验收还差”。

## 剩余风险

- 本轮没有现场安全确认，因此没有启动自由移动、键盘手控、底盘手控、雷达或 Nav2。
- 自由移动真实闭环仍需现场勾选安全确认后启动，并验证停止兜底和运动发布。
- 建图验收仍缺相机首帧、雷达新鲜、地图记录和新鲜地图画面；本轮只是把这些缺口从移动前置文案里拆出来。
