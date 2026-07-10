# O6/O7 Annotation Submit Export Tech Plan

## Sprint 类型

- sprint_type: epic
- automation_id: rober-okr
- target_objectives: O6, O7
- evidence_boundary: software_proof_local_mock_annotation_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的活跃 Objective 是 **O6：云端核心后端**，当前约 33%。
2. 本 sprint 针对 O6，同时协同 O7。O6 负责 annotation submit + dataset export 的 local/mock archive 能力，O7 负责 PC consumer 主路径触发和展示。
3. O7 当前约 34%，不是最低 Objective，但本轮 O7 工作直接消费 O6 新能力，属于 O6/O7 交界项；该选择避免重复硬件、camera、wheel raw blocker，也避免继续产出 wrapper-only/surface-only。

## 技术方案概览

本轮采用“后端先定义稳定 local/mock 合同，PC 通过 adapter 消费”的方式：

1. O6 复用现有 file-backed archive store，接收 annotation submit 并按 task 持久化。
2. O6 新增 task-level annotation dataset export，返回安全 manifest/summary，不输出原始大对象。
3. O7 PC 后端新增 consumer read submit/export adapter，只允许本机 HTTP 回环 O6 base URL。
4. O7 UI 在 consumer-detail labeling primary path 展示 submit/export 触发与结果。
5. 所有真实控制、真实生产云、真实 annotation API、真实 dataset export 和 delivery success 字段保持 false。

## 任务分工

### robot-software-engineer

负责 O6 backend/local mock API/store/tests/docs。

交付内容：

- 扩展 `remote_cloud_relay.py` 的 O6 labeling submit 合同，保持现有 `POST /api/o6/archive/labels` 兼容。
- 新增 task-level annotation export 合同，建议路径为 `GET /api/o6/archive/labels/<task_id>/export?format=jsonl`。
- 在 `FileBackedO6CloudArchiveStore` 中持久化 submit receipt/export metadata，或从 labels store 可复现派生 export result。
- 扩展 O6 consumer labeling detail，确保 PC 能读取 submit/export 结果。
- 更新 Python unittest，覆盖 submit/export 正常和 fail-closed 分支。
- 更新 O6 接口文档。

### full-stack-software-engineer

负责 PC O7 adapter/UI/tests/docs。

交付内容：

- 扩展 `pc-tools/workstation` shared contracts，新增 local/mock annotation submit receipt 与 dataset export result 类型。
- 在 O7 consumer read adapter 中新增 submit/export adapter 函数和 Express route 绑定。
- 在 `workstationApi.ts` 增加固定 client 方法，浏览器只调用 PC 后端，不直连 O6。
- 在 `O7FixturePreviewPanel.vue` 的 consumer-detail labeling primary path 中展示 submit/export 操作和结果。
- 更新 `catalog.test.ts` 与 `App.test.ts`。
- 更新 PC 产品/接口文档和 README。

### product-okr-owner

负责收口 OKR、side2side、final。

交付内容：

- implementation 完成后核对 `tech-done.md`、测试证据和风险边界。
- 创建/更新 `side2side_check.md`，逐项对照 PRD 验收口径。
- 创建/更新 `final.md`，判断 O6/O7 是否保守上调，是否归档 KR，以及剩余风险。
- 如证据成立，再更新 `OKR.md` 和 `docs/process/okr_progress_log.md`；本 planning 任务不改这些文件。

## 文件范围和冲突规避

### robot-software-engineer 可改范围

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- 必要时只读参考 `docs/navigation/field_route_evidence_manifest.md` 和 `docs/navigation/o7_field_evidence_consumer_ingest.md`；如确需修改，必须在 `tech-done.md` 说明原因。

### full-stack-software-engineer 可改范围

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

### product-okr-owner 可改范围

- `sprints/2026.07.09_06-53_o6_o7_annotation_submit_export/tech-done.md`
- `sprints/2026.07.09_06-53_o6_o7_annotation_submit_export/side2side_check.md`
- `sprints/2026.07.09_06-53_o6_o7_annotation_submit_export/final.md`
- 收口阶段如证据成立，允许改 `OKR.md` 和 `docs/process/okr_progress_log.md`。

### 共享接口和兼容规则

- 不设置两个 engineer 同时修改同一产品代码文件。
- O6 合同主责为 `robot-software-engineer`；PC 只能消费 tech-plan 中约定的 O6 local/mock API，不重写 O6 Python。
- `docs/interfaces/o6_cloud_archive_api.md` 由 `robot-software-engineer` 修改；`docs/interfaces/o7_realtime_operator_console.md` 和 `docs/product/pc_tools_workstation.md` 由 `full-stack-software-engineer` 修改。
- 现有 `POST /api/o6/archive/labels`、`GET /api/o6/archive/labels`、`GET /api/o6/archive/labels/<task_id>`、O6 consumer read、O7 `route_replay_mvp` 和 `labeling_mvp` 字段必须保持向后兼容；新增字段必须 optional。
- 如果 implementation 发现建议路径 `GET /api/o6/archive/labels/<task_id>/export?format=jsonl` 与现有 router 冲突，`robot-software-engineer` 可以选择等价路径，但必须同步更新 O6 docs，并确保 `full-stack-software-engineer` 的 adapter 只消费最终文档化路径。

## 接口边界

### O6 Annotation Submit

优先复用：

- `POST /api/o6/archive/labels`

请求继续支持：

- `robot_id`
- `task_id`
- `labels[]`

新增或强化响应摘要：

- `schema=trashbot.o6.archive_labeling.v1`
- `source=local_mock_labeling`
- `write_status=created|updated`
- `duplicate=true|false`
- `local_mock_annotation_submit_written=true`
- `submit_receipt.status=local_mock_annotation_written`
- `submit_receipt.receipt_id`
- `submit_receipt.task_id`
- `submit_receipt.label_count`
- `submit_receipt.safe_to_control=false`
- `submit_receipt.delivery_success=false`
- `submit_receipt.primary_actions_enabled=false`
- `submit_receipt.robot_control_executed=false`

fail-closed：

- task 不存在、robot mismatch、labels 空数组、labels 超限、字段超长、unsafe `evidence_ref`、payload 含凭证/串口/`/cmd_vel`/traceback。
- 任意危险字段声明为 true。
- 返回 4xx，不写入 store。

### O6 Dataset Export

建议新增：

- `GET /api/o6/archive/labels/<task_id>/export?format=jsonl`

响应建议：

- `schema=trashbot.o6.annotation_dataset_export.v1`
- `source=local_mock_labeling_export`
- `export_status=local_mock_export_ready|blocked_not_proven`
- `task_id`
- `robot_id`
- `format=jsonl`
- `label_count`
- `item_count`
- `export_manifest`
- `sample_rows[]` 限量安全摘要
- `local_mock_dataset_export_written=true` 或 `local_mock_dataset_export_ready=true`
- `dataset_export_available=false`
- `real_dataset_export_connected=false`
- `real_annotation_api_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`

export 不得包含：

- 绝对路径
- credential URL
- bearer token / password / secret
- 原始图片、视频、音频、rosbag 内容
- base64
- 串口路径、波特率、`/cmd_vel`

### O7 PC Adapter

建议新增 PC 后端 route：

- `POST /api/o7/consumer-read/tasks/<task_id>/annotations/submit`
- `GET /api/o7/consumer-read/tasks/<task_id>/annotations/export`

PC route 只接受：

- `baseUrl` 为 `http://127.0.0.1`、`http://localhost` 或 `http://[::1]`。
- `task_id` 为安全 ID。
- submit body 只包含当前 draft label 所需小型白名单字段。

PC route 必须拒绝：

- 非 HTTP、非回环、credentials、query/hash 注入。
- 空 task id、schema mismatch、O6 返回非 object、O6 返回危险 true 字段。
- browser 直接携带 bearer/token/password/secret。

PC 输出建议：

- `schema=trashbot.pc_tools_workstation.o7_annotation_submit_result.v1`
- `schema=trashbot.pc_tools_workstation.o7_annotation_dataset_export_result.v1`
- `adapter_status=local_mock_annotation_written|local_mock_export_ready|fail_closed`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `real_annotation_api_connected=false`
- `real_dataset_export_connected=false`
- `connects_cloud_production=false`

## 危险字段 Fail-Closed 规则

Implementation 必须递归扫描 O6 入参、O6 出参和 PC adapter 出参。以下字段任一为 true 都必须 fail-closed，或在固定 false 字段中被强制 false：

- `safe_to_control`
- `delivery_success`
- `primary_actions_enabled`
- `robot_control_executed`
- `connects_cloud_production`
- `real_cloud_db_connected`
- `real_oss_connected`
- `real_annotation_api_connected`
- `real_dataset_export_connected`
- `cloud_write_executed`
- `command_dispatch_enabled`
- `manual_control_enabled`
- `navigate_goal_enabled`
- `keyboard_control_enabled`
- `playback_available`
- `safe_to_play`
- `sends_to_robot`

兼容旧合同：

- `submit_enabled=false` 保持真实 submit API 未连接的语义。
- `dataset_export_available=false` 保持真实 dataset export 未连接的语义。
- local/mock 成功只能通过明确 local/mock 字段表达，不得复用真实能力字段。

## 代码质量要求

- 技术注释必须使用中文，且新增/修改代码注释比例超过 20%。
- 复杂校验逻辑需要解释为什么 fail-closed，而不是只描述代码做了什么。
- 不引入生产凭证、绝对本机路径、真实外网 URL 或硬件参数假设。
- 本轮是 local/mock 开发，不涉及 WAVE ROVER、UART、波特率、引脚、电压或机械尺寸；implementation 不应修改硬件配置。

## 验收命令

implementation 子 agent 必须运行并在 `tech-done.md` 记录结果：

### Robot/O6

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

### PC/O7

```bash
cd pc-tools/workstation && npm run test -- catalog.test.ts
```

```bash
cd pc-tools/workstation && npm run test -- App.test.ts
```

```bash
cd pc-tools/workstation && npm run build
```

```bash
cd pc-tools/workstation && npm run lint
```

### Workspace / Diff

```bash
bash onboard/scripts/docker_humble_build.sh
```

```bash
git diff --check
```

planning 阶段只验证三份计划文档存在且包含必要关键词，不运行上述 implementation 验收命令。

## 验收输出要求

implementation 子 agent 必须返回：

1. 实际改动的文件列表。
2. 验证命令输出结果，包含关键日志片段。
3. 失败定位和修复记录，如有。
4. 剩余风险，特别是生产云、真实机器人数据、真实媒体、真实控制和 delivery success 的缺口。

Product 收口必须返回：

1. 用户价值和产品北极星。
2. OKR 映射和方向判断。
3. KR 拆解、更新或历史归档。
4. 本轮核心抓手。
5. 后续需要做什么。
6. 优先级和验收口径。
7. 对应责任 Engineer。
8. 风险、阻塞和证据链缺口。
9. 已完成 KR 历史记录位置、证据来源和剩余风险。
10. 已创建或更新的 sprint 文档。

## 剩余风险

- 本轮即使完成也只证明 `software_proof_local_mock_annotation_only`，不证明真实生产云、真实 DB/queue、OSS/CDN、TLS/4G 或真实机器人数据。
- 真实 keyframe/media 可访问性仍可能未证明；若 export 只包含 ref 字符串，不能宣称媒体已可访问。
- 真实 annotation API、真实 dataset export、rollback、autosave、审计日志和训练 split policy 仍可能缺失。
- 真实机器人运动、WAVE ROVER wheel raw 非零、RTC/video、ASR/TTS、电梯状态链和完整路线长期验收仍不在本轮范围内。
