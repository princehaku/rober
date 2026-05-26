# O7 Labeling Local Draft Editor

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 的 `Cloud Archive Tasks` / `Local labeling review panel` 附近新增 `Local draft annotation editor`。
- editor 只消费 `labeling_queue_inspector.sample_review_items`、`allowed_label_types` 和 `label_schema`，草稿只保存在浏览器内存中。
- 草稿字段包含当前 item、draft status、selected label type、confidence、note/metadata 摘要、validation status，以及固定 false 边界：`submit_enabled=false`、`autosave_available=false`、`real_annotation_api_connected=false`、`dataset_export_available=false`、`cloud_write_executed=false`。
- 本地校验覆盖 allowed label type 和 finite `0..1` confidence；失败状态显示 `blocked_label_type_not_allowed` 或 `blocked_invalid_confidence`。
- 草稿按 `task_id:item_id` 隔离，item cursor 切换不会把上一条 item 的草稿显示到当前 item；`Reset draft` 只重置当前 item 的内存草稿。
- 更新 `docs/interfaces/o7_cloud_archive_task_api.md`、`docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`，明确该 editor 不调用 API、不写后端、不 autosave、不导出训练集、不代表 annotation API 接通。

## 验证结果

- 通过：`cd pc-tools/workstation && npm run build`
  - 关键输出：`✓ 31 modules transformed.`、`✓ built in 2.15s`
- 通过：`cd pc-tools/workstation && npm run test`
  - 关键输出：`Test Files  2 passed (2)`、`Tests  38 passed (38)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - 关键输出：ESLint exit code 0，无错误输出
- 通过：`git diff --check -- pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts docs/interfaces/o7_cloud_archive_task_api.md docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_34-35_o7-labeling-local-draft-editor/tech-done.md`
  - 关键输出：exit code 0，无 whitespace error

## 剩余风险

- 当前能力仍是 PC-only software proof；没有真实 O6 annotation API、真实 review queue、真实云写入、真实 autosave 或真实 dataset export 证据。
- 真实图片/视频标注画布、云端提交审计和训练集导出仍未接入。
