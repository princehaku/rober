# 2026.06.29 03:40 PC Nav2 success requires wheel proof

sprint_type: micro

## 实际改动

- PC Nav2 latest 只读代理新增 `goal_execution_key_values.execution_proof_gap`。当 `goal_succeeded` 但执行窗口 wheel L/R 非零未证明时，返回 `wheel_lr_nonzero_not_proven`。
- PC 普通首屏收紧 Nav2 完整路线判断：`goal_succeeded + feedback_sample_count` 不再等于已到达，必须同时有 `nav2_goal_execution_proven=true` 和 wheel L/R 非零证明。
- 地图目标 marker 从旧的“已到达”降级为“到达未证明”，行程卡显示“路线返回成功，真车未证明”，避免旧 action success 被误读成完整路线执行。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md`，记录本轮只读边界：不执行 Nav2 goal、不发送 manual/free-roam/delivery/stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "draws the latest Nav2 goal on the real map when goal coordinates are available"`，1 passed。
- 通过：`npm test -- --run test/App.test.ts -t "uses Robot Control summary latest Nav2 execution readback on the plain map when latest key values are empty"`，1 passed。
- 通过：`npm test -- --run test/App.test.ts -t "keeps trip latest pending unproven across trip card and map"`，1 passed。
- 通过：`npm test -- --run test/catalog.test.ts -t "latest execution proxy"`，4 passed。
- 通过：`npm test -- --run`，2 files passed，360 tests passed。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只修 PC 对 Nav2 latest/summary 证据的解释，不代表现场 Nav2 lifecycle、路径生成服务、相机首帧、雷达 lifecycle 或真实路线 HIL 已恢复。
