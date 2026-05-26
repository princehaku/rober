# sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`：在 O7 `Cloud Archive Tasks` / safe command review panel 附近新增 `Local safe command draft editor`，只基于当前 `safe_command_inspector` fixture 摘要维护浏览器内存草稿；支持 `manual_turn` / `navigate_goal`、manual direction、target `x/y/yaw`、idempotency draft/ref 输入和本地校验。
- `pc-tools/workstation/test/App.test.ts`：补充本地 safe command 草稿交互测试，覆盖 invalid direction、缺 idempotency、invalid navigate goal、reset、archive path 切换清理草稿，并断言交互不增加 `fetch` 次数。
- `docs/interfaces/o7_cloud_archive_task_api.md`、`docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步记录 editor 的输入、状态、校验规则和能力边界，明确不调用 API、不写云端、不发送命令、不绑定键盘、不下发寻路。

## 验证结果

- 通过：`cd pc-tools/workstation && npm run build`
  - 关键日志：`✓ 31 modules transformed.`、`✓ built in 2.11s`
- 通过：`cd pc-tools/workstation && npm run test`
  - 关键日志：`Test Files  2 passed (2)`、`Tests  38 passed (38)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - 关键日志：`eslint .` 退出码 0，无错误输出
- 通过：`git diff --check -- pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts docs/interfaces/o7_cloud_archive_task_api.md docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_36-37_o7-local-safe-command-draft-editor/tech-done.md`
  - 关键日志：退出码 0，无 whitespace 错误输出

## 剩余风险

- 当前仍是 PC-only software proof；未接真实 command API、robot ACK、键盘控制、自动寻路下发或硬件 HIL。
