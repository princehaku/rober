# O6/O7 Annotation Submit Export Tech Done

## Sprint 类型

- sprint_type: epic
- closeout_owner: product-okr-owner
- implementation_owners: robot-software-engineer, full-stack-software-engineer
- evidence_boundary: software_proof_local_mock_annotation_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 实际改动

### O6 Backend / Local Mock

来源：`artifacts/o6_engineer_report.md`，run time `2026-07-09 07:12:22 CST`。

- 扩展 `POST /api/o6/archive/labels`，在保持旧合同兼容的基础上返回 local/mock submit proof：
  - `local_mock_annotation_submit_written=true`
  - `submit_receipt.status=local_mock_annotation_written`
  - `submit_receipt.receipt_id`
  - `submit_receipt.task_id`
  - `submit_receipt.label_count`
- 新增 task-level export API：`GET /api/o6/archive/labels/<task_id>/export?format=jsonl`。
- export 只从既有 task labels 派生安全 `export_manifest` 和限量 `sample_rows[]`，不读取原始文件、不连接 OSS/DB、不输出绝对路径、不输出 base64、不暴露凭证、不触碰 `/cmd_vel`。
- labels detail 与 O6 consumer `labeling` section 增加 submit/export 摘要，供 O7 按 task detail 主路径读取。
- 增加危险 true 字段、unsafe label refs、非法 format/query、missing task、robot mismatch、empty labels、oversized labels 和 no-label export 的 fail-closed 覆盖。

O6 实际改动文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.09_06-53_o6_o7_annotation_submit_export/artifacts/o6_engineer_report.md`

### O7 PC Adapter / UI

来源：`artifacts/o7_engineer_report.md`，更新时间 `2026-07-09 07:25:04 CST`。

- 新增 PC result schema：
  - `trashbot.pc_tools_workstation.o7_annotation_submit_result.v1`
  - `trashbot.pc_tools_workstation.o7_annotation_dataset_export_result.v1`
- 新增 O7 adapter：
  - `buildO7ConsumerAnnotationSubmit()` 调 O6 `POST /api/o6/archive/labels`
  - `buildO7ConsumerAnnotationExport()` 调 O6 `GET /api/o6/archive/labels/<task_id>/export?format=jsonl`
- 新增 PC 后端 route：
  - `POST /api/o7/consumer-read/tasks/<task_id>/annotations/submit`
  - `GET /api/o7/consumer-read/tasks/<task_id>/annotations/export`
- 浏览器只调用 PC 后端 route，不直连 O6；PC adapter 只允许本机 HTTP 回环 base URL，并拒绝 credentials、query/hash、非 HTTP、非回环、空 task id、schema mismatch、危险 true 字段、未知 submit body 字段和 token/password/secret/credential/bearer 文本。
- `O7FixturePreviewPanel.vue` consumer-detail labeling primary path 增加 local/mock 提交标注和导出数据集操作，展示 receipt/export manifest/sample rows/blocker/false 字段；缺 detail 或 labeling MVP blocker 时禁用。
- 文案保持 local/mock、not_proven，不暗示真实控制、真实生产云或真实 annotation API。
- 同步更新 PC README、PC 产品文档和 O7 接口文档。

O7 实际改动文件：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_realtime_operator_console.md`
- `sprints/2026.07.09_06-53_o6_o7_annotation_submit_export/artifacts/o7_engineer_report.md`

## 验证结果

本 Product 收口不重跑 O6/O7 全量实现测试，按本轮任务要求引用 engineer report 中已完成的实现验证，并运行 closeout 轻量验证。

### O6 验证

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

结果：通过，无输出。

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

关键输出：

```text
Ran 149 tests in 50.772s

OK
```

### O7 验证

```bash
cd pc-tools/workstation && npm run test -- catalog.test.ts
```

关键输出：`Test Files  1 passed (1)`；`Tests  204 passed (204)`；`Duration  43.10s`。

```bash
cd pc-tools/workstation && npm run test -- App.test.ts
```

关键输出：`Test Files  1 passed (1)`；`Tests  247 passed (247)`；`Duration  30.55s`。

```bash
cd pc-tools/workstation && npm run build
```

结果：通过；关键输出包含 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`、`✓ built in 1.77s`。Vite 仍提示既有 chunk 大于 500 kB，不阻塞本轮。

```bash
cd pc-tools/workstation && npm run lint
```

结果：通过；关键输出：`eslint .`。

## 失败定位

- O6：最终验证没有遗留失败；工程报告仅记录初始 targeted `py_compile` 在测试更新前也通过。
- O7：第一轮 `App.test.ts` 失败，原因是新增英文按钮文案触发既有只读安全断言；已改为中文按钮文案并复验通过。
- O7：第一轮复跑 `catalog.test.ts` 失败，原因是恢复越界 `server/catalog.ts` 改动后 `index.ts` 仍从 `catalog.ts` 引入新 builder；已改为从 `o7ConsumerReadAdapter.ts` 直接引入并复验通过。

## 偏差和边界

- 本轮没有运行 `bash onboard/scripts/docker_humble_build.sh`，因为 Product 收口任务明确只跑文件存在、关键字段 `rg` 和 `git diff --check` 的轻量验证；O6/O7 全量实现验证引用 engineer report。
- 本轮没有硬件、串口、ROS2 runtime、真实云、真实媒体或真实机器人控制操作。
- `safe_to_control: false`、`delivery_success: false`、`primary_actions_enabled: false`、`robot_control_executed: false` 保持不变。

## Product Closeout 轻量验证

```bash
test -f sprints/2026.07.09_06-53_o6_o7_annotation_submit_export/tech-done.md
test -f sprints/2026.07.09_06-53_o6_o7_annotation_submit_export/side2side_check.md
test -f sprints/2026.07.09_06-53_o6_o7_annotation_submit_export/final.md
```

结果：三个文件均存在，命令退出码 0，无输出。

```bash
rg -n "software_proof_local_mock_annotation_only|149 tests|204 passed|247 passed|O6|O7|safe_to_control: false|delivery_success: false" sprints/2026.07.09_06-53_o6_o7_annotation_submit_export OKR.md docs/process/okr_progress_log.md
```

结果：命中 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 和 engineer reports 中的证据字段，包括 `software_proof_local_mock_annotation_only`、`149 tests`、`204 passed`、`247 passed`、`safe_to_control: false`、`delivery_success: false`。

```bash
git diff --check
```

结果：通过，退出码 0，无输出。

## 剩余风险

- 只证明 `software_proof_local_mock_annotation_only`。
- 不证明真实 annotation API、真实 dataset export、production cloud、真实媒体、真实机器人控制或 delivery success。
- 不证明 production DB/queue、OSS/CDN、TLS/4G、真实隧道、真实机器人数据、真实 keyframe/media 可访问性、真实 rollback/autosave/audit log 或训练 split policy。
- O6 export rows 只是从 labels 派生的安全摘要，不是生产训练文件。
- O7 只证明 PC adapter/UI 可消费 O6 local/mock API，不证明真实云端或长期运营链路。
