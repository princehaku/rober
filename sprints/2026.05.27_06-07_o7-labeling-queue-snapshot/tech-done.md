# O7 Labeling Queue Snapshot Tech Done

## Sprint Type

sprint_type: micro

## 实际改动

- 在 `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py` 新增 `labeling_queue_snapshot` fail-closed cloud contract，固定 `source=software_proof`、`snapshot_status=blocked_not_proven`、`safe_to_control=false`、`primary_actions_enabled=false`、`submit_enabled=false`、`rollback_enabled=false`、`real_annotation_api_connected=false`、`dataset_export_available=false`。
- 在 `pc-tools/workstation/src/shared/contracts.ts` 和 `pc-tools/workstation/src/server/o7OperatorConsole.ts` 新增 O7-KR4 标注队列类型与静态响应，覆盖 review queue、selected item、label schema、allowed label types、draft labels、submit/rollback audit、dataset export gaps 和 next required evidence。
- 在 `pc-tools/workstation/src/components/O7OperatorConsolePanel.vue` 增加只读 Labeling queue snapshot 面板；没有新增按钮、键盘绑定、提交、回滚、导出或本地写文件路径。
- 在 `pc-tools/workstation/test/App.test.ts` 和 `pc-tools/workstation/test/catalog.test.ts` 增加 O7-KR4 fail-closed 断言，确认真实 annotation API、submit、rollback 和 dataset export 均未开启。
- 同步更新 `docs/interfaces/o7_realtime_operator_console.md` 与 `docs/product/pc_tools_workstation.md`，明确该 snapshot 只为后续 O6 annotation API / training dataset export 留槽位。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过，Vite 输出 `✓ built in 1.86s`。
- `cd pc-tools/workstation && npm run test`：通过，`Test Files  2 passed (2)`，`Tests  16 passed (16)`。
- `cd pc-tools/workstation && npm run lint`：通过，无 ESLint 输出。
- `python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`：通过，无输出。
- `git diff --check -- cloud-relay pc-tools docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_06-07_o7-labeling-queue-snapshot`：通过，无输出。

## 剩余风险

- 本轮仍是 software proof contract，不连接真实 O6 annotation API，不提供真实标注队列、真实截图/帧、真实提交、真实回滚或真实训练集导出。
- 后续需要 O6 提供 annotation review queue query、label schema、selected item media evidence ref、submit/rollback audit log 和 dataset export manifest 后，才能把占位字段替换为真实只读数据。
- 本轮按 CEO 指定不修改 `OKR.md`，不提升 O7 百分比。
