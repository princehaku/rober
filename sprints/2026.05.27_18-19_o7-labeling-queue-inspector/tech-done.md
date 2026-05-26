# O7 Labeling Queue Inspector

sprint_type: micro

## 实际改动

- 在 `trashbot.o7.cloud_archive_tasks.v1` 响应中新增 `labeling_queue_inspector`，从 selected task 的本地 archive fixture 读取 `review_items[]`、`labels[]`、`label_schema`、`allowed_label_types[]`、`draft_labels[]` 和 `dataset_export`，生成 KR4 只读标注队列检查视图。
- `review_items[]` 形状支持每个 item 的 `current_labels[]` / `labels[]`；只有 `labels[]` 的旧 archive 也会派生最小 review item 和 draft label 摘要。
- blocked / unsafe / success / control / real API claim 输入统一 fail-closed：样本为空，`submit_enabled=false`、`rollback_enabled=false`、`dataset_export_available=false`、`real_annotation_api_connected=false`。
- `O7 Previews > Cloud Archive Tasks` 增加标注队列检查展示：status、review item count、sample review items 表格、label schema、allowed label types、draft labels、dataset export gaps 和标注 false fields。
- 同步更新 `docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_cloud_archive_task_api.md`、`docs/interfaces/o7_realtime_operator_console.md`。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。关键输出：`vite v7.3.3 building client environment for production...`、`✓ built in 2.04s`。
- `cd pc-tools/workstation && npm run test`：通过。关键输出：`Test Files  2 passed (2)`、`Tests  32 passed (32)`。
- `cd pc-tools/workstation && npm run lint`：通过，无 ESLint 报错。
- `git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md docs/interfaces/o7_cloud_archive_task_api.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_18-19_o7-labeling-queue-inspector`：通过，无 whitespace error 输出。

## 剩余风险

- 本轮仍是 PC-only 本地 fixture software proof，不连接 O6 真实云归档、不连接真实 annotation API、不提交或回滚标注、不导出训练集。
- 尚未证明真实路线帧、关键帧截图、标注任务、训练集导出格式或云端存档的一致性；后续需要 O6/O7 真实 API 契约和样本数据接入。
- O7-KR4 体验从“label count / preview summary”推进到“可检查标注队列形状”，但还不是可写数据标注界面。
