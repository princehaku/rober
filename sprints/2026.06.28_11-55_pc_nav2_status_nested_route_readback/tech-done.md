# 2026.06.28 11:55 PC Nav2 status nested route readback

sprint_type: micro

## 实际改动

- PC `Robot Control summary` 的 Nav2 路线摘要同时读取直接 `/api/nav2/proof/latest` 和嵌套 `/api/nav2/status.proof_latest`，补齐 `latest_path_generation_succeeded`、`latest_path_point_count`、`latest_path_preview_*` 等 key-value 白名单。
- `path_preview_points` 现在可从 status 嵌套 proof 抽取；当直接 proof latest 没有路线但 status 嵌套 proof 有 18 点路线时，PC 会把 `nav2_goal_ready` 判为 ready，并继续保留旧执行窗口 wheel raw L/R=0/0 的待复验提示。
- 新增 Vitest 覆盖 live 常见形态：直接 proof latest 0 点，status.proof_latest 含 planner/controller active、路线点和路径预览，最近一次 Nav2 action 成功但 wheel raw L/R 未非零。
- 同步更新 PC 和 fixed-route 文档，明确本轮是只读路线读数修复，不发车、不替代 wheel raw L/R、完整路线执行或 delivery success。

## 验证结果

- `cd pc-tools/workstation && npm run test -- catalog.test.ts` 通过：151 tests。
- `cd pc-tools/workstation && npm run test` 通过：2 files / 361 tests。
- `cd pc-tools/workstation && npm run build` 通过；Vite 仍提示单 chunk 大于 500 kB，这是既有前端体积 warning，不影响本轮功能。
- 真实上位机只读复核：`/api/camera/health` 显示 `uvc_no_frame_not_exclusive` 且 `source_usage.owner_count=0`，说明看不到画面不是浏览器独占；`/api/nav2/goal/execution/latest` 仍是旧 PWM action 成功但 wheel raw L/R=0/0；当前 `/api/nav2/status` 已被较新的 `blocked_with_root_cause` artifact 覆盖，所以本轮没有现场发车或重新生成路线。

## 剩余风险

- 本轮没有执行真实 Nav2 goal、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；自动驾驶完整路线、wheel raw L/R 非零和 delivery success 仍待现场安全确认后复验。
- 摄像头仍无首帧，根因更像 UVC 源头无帧而非页面独占；这会继续影响实时预览和建图验收，但不应阻止低速底盘试动。
- 当前 live Nav2 artifact 已回到 `blocked_with_root_cause`，PC 修复能正确消费嵌套路线材料，但仍需要上位机重新恢复服务、生成路线并执行同窗口 wheel raw L/R 复验。
