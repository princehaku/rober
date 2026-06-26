# 2026-06-26 23:58 PC 轮速先只读刷新再试动

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：给普通首屏 `刷新当前轮速（只读）` 按钮加 ref，使 `本轮进度 -> 去轮速` 能直接聚焦到该只读按钮。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当当前 wheel raw L/R 尚未读到时，轮速目标下一步优先提示 `刷新当前轮速（只读）`；读到静态 `L/R=0/0` 后再提示低速试动读取非零。
- `pc-tools/workstation/test/App.test.ts`：新增回归，锁定 summary 无 L/R 时先只读 POST `/api/robot-control/base/feedback-samples`，不自动调用 first-jog、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录该 UI 口径。

## 验证结果

- 已通过：`npm test -- test/App.test.ts -t "wheel|轮速|L/R"`，12 tests passed。
- 已通过：`npm test -- test/App.test.ts`，119 tests passed。
- 已通过：`npm test`，215 tests passed。
- 已通过：`npm run build`；Vite 仍有既有 chunk size warning，但构建成功。
- 已通过：`npm run lint`。
- 已通过：`git diff --check`。
- live 预检：`POST http://127.0.0.1:7001/api/robot-control/base/feedback-samples?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 `samples_forwarded`、`t1001_observed_count=3`、`L/R=0/0`、`wheel_feedback_lr_nonzero_proven=false`、`sends_motion_commands=false`。
- 已通过：重启本机 `npm run api`，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node ... TCP *:7001 (LISTEN)`。
- 已通过：重启后 live 只读轮速接口仍返回 `samples_forwarded`、HTTP 200、`t1001_observed_count=3`、`L/R=0/0`、`nonzero=false`、`sends_motion_commands=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只优化“先看见当前 L/R”的 PC 引导，不等于 wheel raw L/R 非零已完成。
- 完整 Nav2 真车执行证明、delivery success、PC 键盘连续手控 live 证明、自动扫图真车 HIL 仍需继续推进。
