# O6/O7 Annotation Submit Export PRD

## Sprint 类型

- sprint_type: epic
- automation_id: rober-okr
- evidence_boundary: software_proof_local_mock_annotation_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 用户价值和产品北极星

本轮产品目标是把 O6/O7 的标注链路从“能看见 draft 和 blocked receipt”推进到“能在本地/mock 后端提交标注，并导出任务级 dataset 摘要”。运营/开发者可以围绕同一 `task_id` 完成最小数据闭环：查看路线/关键帧材料、提交标注、看到持久化 receipt、导出训练数据清单。

北极星仍是普通用户可验证地完成垃圾投递。本 sprint 只提升任务复盘和数据训练能力，不证明真实投递、真实机器人控制或真实生产云。

## 问题陈述

当前 O6/O7 已有以下能力：

- O6 能 ingest field evidence manifest，并生成 task、trajectory、events、evidence refs。
- O6 consumer read 能让 PC 读取 task detail、field evidence、labeling、inference、tunnel。
- O7 consumer detail 能展示 `route_replay_mvp` 与 `labeling_mvp`，并固定 `submit_receipt.status=submit_blocked_fail_closed`。

当前缺口是：

- PC 端没有通过主路径触发 annotation submit。
- O6 local/mock archive 没有把 submit receipt 和 dataset export 作为同一任务的可验证闭环暴露给 O7。
- O7 不能展示 export result，因此 KR4 仍停留在只读 preview。

## 目标和非目标

### Goals

1. O6 local/mock archive 接收并持久化 annotation submit。
2. O6 提供 task 级 annotation dataset export，至少支持安全 JSON/JSONL 摘要。
3. O7 PC consumer detail 主路径可以触发 local/mock annotation submit，并展示 O6 返回的 submit receipt。
4. O7 PC consumer detail 主路径可以触发或读取 task-level dataset export，并展示 export result。
5. 所有危险字段继续 fail-closed，不把 local/mock write/export 解释为真实 annotation API、真实云写入、真实训练集生产或 delivery success。

### Non-Goals

- 不连接生产 DB/queue、OSS/CDN、TLS/4G、真实公网云。
- 不读取真实大对象内容，不上传图片/视频/rosbag，不回显 base64。
- 不下发机器人控制、不启动 ROS2 runtime、不打开串口、不发送 `/cmd_vel`。
- 不修 camera、wheel raw、WAVE ROVER、真实路线、电梯、ASR/TTS blocker。
- 不把 O6 KR4/O7 KR4 直接标完成。

## OKR 映射和方向判断

- O6 KR4：云端提供数据打标/标注 API。本轮目标是 local/mock annotation submit + readback/export，属于软件侧推进。
- O6 KR6：REST API 供 PC/手机消费。本轮需要让 consumer detail 或相关 detail/export API 暴露 submit/export 结果。
- O7 KR4：数据标注/打标界面。本轮需要从展示 draft 推进到 local/mock submit/export 操作闭环。
- 方向判断：继续。本轮针对最低活跃 O6，同时协同 O7；不重复最近两轮 wrapper-only/surface-only 产物。

## 用户故事

1. 作为运营/开发者，我在 PC O7 consumer detail 中选择一个已有 `task_id`，能看到当前 review item、media/evidence ref、label schema 和 draft labels。
2. 作为运营/开发者，我点击本地/mock submit 后，PC 通过固定 O7 adapter 调用 O6 local/mock archive，O6 持久化 annotation，并返回 receipt。
3. 作为运营/开发者，我点击或读取 dataset export 后，能看到 task 级 export manifest、label count、item count、format、safe refs 和 blocked/not_proven 说明。
4. 作为产品验收方，我能从测试和文档确认所有真实控制、真实云、真实生产导出和送达成功字段都保持 false。

## 功能需求

### O6 Backend / Local Mock

- 复用或扩展现有 `POST /api/o6/archive/labels` 作为 local/mock annotation submit 入口，保持旧 `labels[]` 合同兼容。
- 对同一 `task_id + item_id + label_type` 继续幂等 upsert，首次写入返回 created，重复写入返回 updated。
- 响应新增 submit receipt 摘要，表达 local/mock 写入已发生，但不得把 `submit_enabled`、`real_annotation_api_connected`、`cloud_write_executed` 改为 true。
- 新增 task-level export 入口，建议为 `GET /api/o6/archive/labels/<task_id>/export?format=jsonl`，返回安全 export manifest 和限量 rows/sample refs。
- export 必须基于 store 中已存在的 task 与 labels；缺 task、robot mismatch、无 labels、非法 format、危险 query 或 unsafe payload 均 fail-closed。
- O6 consumer detail 的 `labeling` section 或 O6 labels detail 必须能被 PC adapter 稳定读取 submit/export 结果。

### O7 PC Consumer Detail

- 在 consumer detail labeling primary path 增加 local/mock submit 操作，提交当前 draft label 或测试 fixture draft，走 PC 后端 adapter，不从浏览器直连 O6。
- 增加 local/mock dataset export 操作或读取展示，显示 O6 export result。
- `O7FixturePreviewPanel.vue` 的旧 archive fixture labeling panel 继续只作为 debug fallback，不能覆盖 consumer detail 主路径。
- UI 文案和状态必须避免“生产云”“真实 API”“可控制”“送达成功”等暗示。
- PC 后端只允许本机 HTTP 回环 base URL，继续拒绝 credentials、query/hash 注入、非 HTTP、非回环、schema drift 和危险 true 字段。

## 验收口径

本轮 implementation 完成时，至少满足：

- O6 unittest 覆盖合法 submit、幂等 update、task-level export、无 labels blocked、危险字段 true fail-closed、unsafe refs fail-closed。
- PC catalog tests 覆盖 O7 adapter submit/export 成功路径和 fail-closed 路径。
- PC App tests 覆盖 UI 触发 submit/export、receipt/export result 展示、缺 detail/blocked 时禁用或显示 blocker。
- Build、lint、git diff check 通过。
- `tech-done.md` 写清实际改动、验证结果、失败定位和剩余风险。
- implementation 更新相关 `docs/` 文档，确保 O6/O7 接口和产品边界不滞后。

## 危险字段和 Fail-Closed 规则

以下字段在本轮任何响应、adapter 输出和 UI 判断中都不得因为 local/mock submit/export 变为 true：

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

`submit_enabled` 与 `dataset_export_available` 如果在现有合同中代表真实能力，也必须继续保持 false。允许新增明确 local/mock 语义字段，例如 `local_mock_annotation_submit_written`、`local_mock_dataset_export_written`、`dataset_export.status=local_mock_export_ready`。

## 责任 Engineer

- `robot-software-engineer`：O6 backend/local mock API/store/tests/docs。
- `full-stack-software-engineer`：PC O7 adapter/UI/tests/docs。
- `product-okr-owner`：收口 OKR、`side2side_check.md`、`final.md`，并判断是否需要保守调整 O6/O7 进度。

## 已完成 KR 历史归档

本 planning 阶段不归档任何 KR。上一轮证据只证明 local/mock consumer detail route/labeling MVP；本轮只有在 submit/export 软件证据完整后，才能在 `final.md` 判断是否更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。

## 需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 待 implementation 更新：`tech-done.md`。
- 待 Product 收口更新：`side2side_check.md`、`final.md`。
