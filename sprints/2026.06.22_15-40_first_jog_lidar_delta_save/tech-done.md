# First-Jog LiDAR Delta Save

sprint_type: micro

## 实际改动

- 修正 PC workstation 后端 first-jog/manual 运动证据压缩白名单，保留 LiDAR delta 相关字段和 `scan_delta_ref`。
- 运动证据 gap 判定新增 remote motion key values 的 LiDAR delta 识别，避免上位机已证明时仍显示缺口。
- 普通首屏 `保存轮速记录` 在同轮 first-jog 已证明 LiDAR delta 时，会把雷达移动记录随 wheel raw L/R 一起保存到 operator report。
- 更新 `docs/product/pc_tools_workstation.md`，说明该入口仍只保存材料，不伪造未证明的 LiDAR delta 或 delivery success。

## 验证结果

- 通过：`npm test`，2 个 test files、118 个 tests 全部通过。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，完成 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只修 PC 代理与 UI 保存材料链路，不直接执行真实 first-jog。
- 真实键盘连续手控仍需要现场 first-jog 同时拿到 wheel raw L/R 非零、LiDAR delta，并完成 operator report gate。
