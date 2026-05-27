# O7 Previews Acceptance Expanded Surfaces

sprint_type: micro

## 实际改动

- 扩展 `GET /api/o7/previews/acceptance` 的 covered surfaces，新增 `realtime_map_pose_preview`、`elevator_state_timeline_preview`、`route_replay_trajectory_minimap`、`local_draft_annotation_editor`、`local_tts_draft_editor`、`local_safe_command_draft_editor`。
- 同步扩展 `O7PreviewsAcceptanceSurfaceId` 类型，避免新增 surface 只存在于服务端运行时数据。
- 更新 O7 Previews 页面测试 mock 和断言，检查新增 surface id 与页面 copy，而不是只检查 surface 数量。
- 更新 `catalog.test.ts` 中 O7 Previews acceptance guard 的静态合同断言，补齐新增 6 个 surface，并继续检查关键 `evidence_boundary`、`blocked_reasons` 和 `not_proven` 语义。
- 更新 PC workstation 产品文档和 `pc-tools/README.md`，明确 acceptance guard 不读取 fixture、不触发 probe、不发送命令、不连接生产云、不提升 O7 完成度。

## 验证结果

- 第一次验证：
  - 通过：`cd pc-tools/workstation && npm run build`
    - 关键输出：`✓ 31 modules transformed.`、`✓ built in 2.20s`
  - 失败：`cd pc-tools/workstation && npm run test`
    - 关键输出：`test/catalog.test.ts > O7 previews acceptance guard summarizes PC-only preview readiness boundaries`
    - 失败原因：`catalog.test.ts` 仍精确断言旧 7 个 `covered_surface_ids`，实际响应已经包含本轮新增 6 个 surface。
  - 通过：`cd pc-tools/workstation && npm run lint`
  - 通过：`git diff --check -- pc-tools/workstation/src/server/o7PreviewsAcceptance.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_38-39_o7-previews-acceptance-expanded-surfaces/tech-done.md`
- 追加修复后验证：
  - 通过：`cd pc-tools/workstation && npm run build`
    - 关键输出：`✓ 31 modules transformed.`、`✓ built in 2.17s`
  - 通过：`cd pc-tools/workstation && npm run test`
    - 关键输出：`Test Files  2 passed (2)`、`Tests  38 passed (38)`
  - 通过：`cd pc-tools/workstation && npm run lint`
  - 通过：`git diff --check -- pc-tools/workstation/src/server/o7PreviewsAcceptance.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_38-39_o7-previews-acceptance-expanded-surfaces/tech-done.md`

## 剩余风险

- 本轮只扩展 O7 Previews acceptance guard 的治理覆盖面，不接真实 RTC/视频、ROS2 `/tf`、云 archive、annotation/voice/command API、robot ACK 或硬件 HIL。
- O7 完成度不因本轮变化提升，仍是 software proof / `blocked_not_proven`。
- 验证范围是 PC workstation build/test/lint 和指定文件 diff whitespace check；未进行真实浏览器人工验收、真实云端、真实机器人或硬件验证。
