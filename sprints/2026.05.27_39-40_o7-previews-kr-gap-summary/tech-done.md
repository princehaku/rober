# O7 Previews KR Gap Summary

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 的 `O7 previews acceptance guard` 内新增 `O7 real capability gap summary`，按 O7-KR1~KR6 从已加载 acceptance guard `surfaces` 派生 matched surface count、surface ids、blocked/not_proven 摘要，并固定展示 `ready_for_real_operation=false`。
- 同一区块展示 `remaining_real_capability_gaps` 和关键 false 字段：`safe_to_control=false`、`sends_commands=false`、`connects_cloud_production=false`、`robot_control_executed=false`。未加载 guard 时保持 `not_loaded`，不推断 ready。
- 更新 `pc-tools/workstation/test/App.test.ts`，覆盖 KR1~KR6 gap summary、surface id、remaining real capability gaps、关键 false 字段，并断言派生 summary 不新增 acceptance guard 之外的 API 调用。
- 更新 `docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`，说明该 summary 只读消费 existing acceptance guard，不新增 API/probe/fixture/命令，不提升 O7 完成度。

## 验证结果

- 通过：`cd pc-tools/workstation && npm run build`。关键结果：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成，Vite 输出 `✓ built in 2.17s`。
- 通过：`cd pc-tools/workstation && npm run test`。关键结果：`Test Files  2 passed (2)`，`Tests  38 passed (38)`。
- 通过：`cd pc-tools/workstation && npm run lint`。关键结果：`eslint .` 无报错退出。
- 通过：`git diff --check -- pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_39-40_o7-previews-kr-gap-summary/tech-done.md`。关键结果：无 whitespace error 输出。

## 剩余风险

- 当前改动仍是 PC software proof 视图，只能帮助 operator 看清 O7-KR1~KR6 缺真实证据；不证明真实 RTC/视频、ROS2 `/tf`、云归档、标注 API、ASR/TTS、safe command、robot ACK、硬件 HIL 或 O7 完成。
