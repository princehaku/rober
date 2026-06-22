# Plain Wheel Evidence Save

sprint_type: micro

## 实际改动

- PC 普通首屏在 first-jog 返回 `wheel_feedback_lr_nonzero_proven=true` 后显示 `保存轮速证据`，保存后显示普通话术“轮速证据已保存；后续手控材料可复用”。
- 保存动作只提交固定 `POST /api/robot-control/operator/report`，带上 first-jog wheel raw L/R、during-motion T1001 帧数和 PC 侧短 ref；不再次发送运动命令，不补 LiDAR delta、real route map 或 delivery success。
- 补充 Vue 测试，覆盖保存轮速证据时 operator report claim 的安全边界，并确认未调用 `/api/robot-control/base/manual`。
- 更新 `docs/product/pc_tools_workstation.md`，记录普通首屏轮速证据保存入口和 proof 边界。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`112 passed (112)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`，无 whitespace error。

## 剩余风险

- 本轮只验证 PC 端 UI、代理请求体和 fail-closed 边界；未发送真实底盘运动，也不证明 LiDAR 位移、完整路线地图或 delivery success。
- 真正 wheel raw L/R 非零仍依赖现场 first-jog 响应已经由上位机 during-motion T1001 readback 证明。
