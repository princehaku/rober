# PC 键盘轮速目标使用普通文案

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏键盘区的 `键盘轮速目标` 行把当前反馈从 `wheel raw L/R=...` 改为“当前轮速 L/R=...”，减少工程术语暴露。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏底盘试动摘要同步改成“轮速 L/R”，高级诊断仍保留 `wheel raw L/R` 排障口径。
- `pc-tools/workstation/test/App.test.ts`：更新键盘连续控制和底盘试动摘要回归测试，锁定启用前、启用后和底盘试动普通文案都不暴露 `wheel raw L/R=`；原测试继续确认按键触发 bounded manual pulse、stop 兜底且不发布 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录普通首屏键盘目标文案和只读边界。

## 验证结果

- `npm --prefix pc-tools/workstation test -- App.test.ts -t "keeps keyboard wheel readback unproven when manual pulse returns only zero L/R"`：通过，`1 passed | 214 skipped`。
- `npm --prefix pc-tools/workstation test`：通过，`2 passed (2)`、`375 passed (375)`。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 仍提示现有单 chunk 大于 500 kB。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 Node 正在 `*:7001` 监听。
- `GET http://127.0.0.1:7001/api/robot-control/summary`：只读通过；`current_fact_plain` 当前说明摄像头不是页面独占，而是 UVC 设备没有输出视频帧；同时说明相机、雷达不挡底盘试动或键盘手控，自动驾驶当前卡在执行窗口轮速 L/R=`0/0` 未非零。

## 剩余风险

- 本轮只改普通首屏可见文案，不改变底盘试动、键盘手控、Nav2 执行、delivery 或 `/cmd_vel` 行为。
- 真实键盘连续手控、轮速非零、完整 Nav2 路线执行和送达成功仍需要现场显式安全确认后操作验证；本轮只做只读 summary 核验。
- 现场摄像头问题从只读 summary 看不是页面独占，剩余风险在 UVC 设备无视频帧、USB 输入或供电，需要后续硬件/上车排障。
