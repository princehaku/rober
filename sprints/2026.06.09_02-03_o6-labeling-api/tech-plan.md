# O6 Labeling API Tech Plan

## 计划状态

本文件完成后，进入实现设计阶段。`full-stack-software-engineer` 按文档把接口契约、边界与测试落到 `remote_cloud_relay.py`，本轮仍只做设计与验收口径。设计通过后再进入本地 mock 实现。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 中最低 Objective 仍是 `O6`，进度 `0%`。
2. 本 sprint 直接对准 `O6-KR4（数据打标/标注 API）`。
3. 继续理由：`KR4` 是 O7 标注闭环的前置契约；与 `KR2/3/6` 的 local/mock 存档链路天然衔接。先冻结本地接口后，后续再接真实云标注服务、训练导出、模型反馈。

## 技术目标

在现有 `remote_cloud_relay.py` O6 local/mock 架构上新增 `archive labeling` API：

- `POST /api/o6/archive/labels`
- `GET /api/o6/archive/labels`
- `GET /api/o6/archive/labels/<task_id>`

本方案不连接真实 cloud DB/OSS，不执行训练导出，不调用任何机器人控制路径。

## 执行 owner

- 主责：`full-stack-software-engineer`
- 模式：单 owner 单线闭环。
- 不并行原因：本轮范围集中在同一 HTTP handler、同一状态文件模型与 O6/O7 文档边界。

## 允许 Engineer 改动范围

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/pc_tools_workstation.md`
- `cloud-relay/README.md`
- `sprints/2026.06.09_02-03_o6-labeling-api/tech-done.md`

允许并需要更新：

- `sprints/2026.06.09_02-03_o6-labeling-api/side2side_check.md`（后续验收）
- `sprints/2026.06.09_02-03_o6-labeling-api/final.md`（收口）

## 接口影响

### Request（POST）

`POST /api/o6/archive/labels`

```json
{
  "robot_id": "trashbot-001",
  "task_id": "task-2026-06-09-a",
  "labels": [
    {
      "item_id": "trajectory-0001",
      "item_type": "trajectory_frame",
      "label_type": "elevator_door_state",
      "value": "open",
      "confidence": 0.97,
      "annotator_id": "labeler-A",
      "evidence_ref": "labels/evidence-0001.json",
      "notes": "door fully open in this frame"
    }
  ]
}
```

- `labels` 最大长度建议限制为 64。
- 单条 `notes`/`evidence_ref`/`annotator_id` 长度上限建议 512。
- `label_type` 建议白名单：`elevator_door_state`、`elevator_floor`、`obstacle_class`、`trajectory_gate`。

### Response（POST/List/Detail）

- 成功写入/更新：HTTP `201`（首次）或 `200`（更新）
- 失败请求：HTTP `400`
- 失败越权/未知：HTTP `403` 或 `404`

所有成功响应固定包含：

- `schema=trashbot.o6.archive_labeling.v1`
- `schema_version=1`
- `source=local_mock_labeling`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `submit_enabled=false`
- `rollback_enabled=false`
- `dataset_export_available=false`
- `real_annotation_api_connected=false`
- `real_dataset_export_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `not_proven` 必须显式包含：`real_annotation_submit_success`、`real_annotation_review_api`、`real_dataset_export`、`real_o7_labeling_production`

`GET /api/o6/archive/labels` 需返回安全摘要字段，例如：

- `task_summary[]`（含 `task_id/robot_id/task_status/pending_item_count/labeled_item_count/latest_label_updated_at_ms`）
- `label_summary.task_count`
- `label_summary.pending_task_count`
- `label_summary.labeled_task_count`
- `blocked_reasons`

`GET /api/o6/archive/labels/<task_id>` 需返回该任务级别：

- `task_id/robot_id`
- `itemized_labels[]`
- `task_status`（`pending|partial|labeled|blocked`）
- `label_summary`

### O7 影响

- `o7_labeling_queue_snapshot.submit_enabled` 仍固定 `false`，`real_annotation_api_connected=false`。
- `dataset_export_available` 在 O7 快照中应继续 `false`。
- `safe_summary` 与 `blocked_reasons` 变更需在 `docs/product/pc_tools_workstation.md` 同步说明。

## 实现要求

1. 状态管理与 `task` 关联
   - 标注结果必须附着在已有 O6 archive task 上，不可凭空创建 task。
   - 推荐复用 O6 store 的 `task_id + robot_id` 主键，用同一 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 文件。
   - 对于不存在的 `task_id` 直接 fail-closed。
   - 对 `task_id` 在该文件中的 `robot_id` 不一致时 fail-closed（越权）。

2. Idempotent upsert
   - `task_id + item_id + label_type` 作为 label 幂等键。
   - 已存在则更新返回 `write_status=updated` 与 `duplicate=true`。
   - 首次写入返回 `write_status=created` 与 `duplicate=false`。

3. Fail-closed 覆盖
   - 坏 JSON、非对象 body、空 body。
   - 缺字段、字段类型错误。
   - 数组过大、长度越界。
   - unsafe content：`Authorization`、`Bearer`、`token`、`/cmd_vel`、串口路径、`baudrate`、`traceback`、凭证 URL。
   - 未匹配 robot/task 时不自动创建、不回显输入样例，返回明确 code。

4. 安全摘要查询
   - `/api/o6/archive/labels` 默认返回不含完整 payload 的 `task summary`，不能原样回显原始 label 明细。
   - 支持 `status=pending|labeled|all`，`limit` 上限 100。
   - 任何时候都保持固定字段边界 false。

5. 文档同步
   - `docs/interfaces/o6_cloud_archive_api.md` 增加 labeling API 的请求/响应/fail-closed/schema/not-proven。
   - `docs/product/pc_tools_workstation.md` 增加 O7 标注入口消费说明。
   - `cloud-relay/README.md` 更新启动与 mock store 边界说明（含本轮不能称为 production）。

6. 注释规范（如涉及实现新增）
   - 技术注释使用中文，解释“为什么”而非仅“做什么”。

## 验收命令（设计阶段）

```bash
test -f sprints/2026.06.09_02-03_o6-labeling-api/pre_start.md && test -f sprints/2026.06.09_02-03_o6-labeling-api/prd.md && test -f sprints/2026.06.09_02-03_o6-labeling-api/tech-plan.md
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O6|KR4|annotation|label|POST /api/o6/archive/labels|GET /api/o6/archive/labels|TRASHBOT_O6_CLOUD_ARCHIVE_STATE|real_annotation_api_connected=false|dataset_export_available=false|python3 -m unittest" sprints/2026.06.09_02-03_o6-labeling-api
```

```bash
git diff --check -- sprints/2026.06.09_02-03_o6-labeling-api
```

## 验收命令（Engineer 实现阶段）

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
rg -n "trashbot.o6.archive_labeling.v1|POST /api/o6/archive/labels|GET /api/o6/archive/labels|real_annotation_api_connected=false|dataset_export_available=false|local_mock_labeling|unknown_task|unauthorized_task|idempotent" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_02-03_o6-labeling-api
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_02-03_o6-labeling-api
```

## 给 `full-stack-software-engineer` 的 prompt 边界

- 范围：仅执行本 sprint 的设计验收通过后落地实现。
- 文件范围按上方“允许 Engineer 改动范围”。
- 结果要求必须返回：实际改动文件、验证输出、失败定位、剩余风险。
- 禁止点：
  - 不得把 `local_mock_labeling` 或 `not_proven` 写成 production。
- 不得发送/返回机器人控制相关成功状态。
- 未通过本文件命令及测试前不允许 commit/push。

## full-stack 工程师提交前提

- 必须先更新以下文档后，主节点才允许进入 commit/push：
  - `sprints/2026.06.09_02-03_o6-labeling-api/tech-done.md`
  - `sprints/2026.06.09_02-03_o6-labeling-api/side2side_check.md`
  - `sprints/2026.06.09_02-03_o6-labeling-api/final.md`

## 收口与提交规则

- 本轮实现完成后先补 `tech-done.md`。
- 成功验收后再进入 `side2side_check.md` 与 `final.md`。
- commit message 建议：

```text
Add O6 local/mock annotation API contract and mock labeling contract proof
```

并保留证据边界：`local/mock`；不可声称生产云、真实 OSS、真实训练导出、真实 robot 控制。

## 剩余风险

- 本轮不产生真实训练集导出与模型反馈，后续仍需 O7 标注流程/评审流接入。
- 与 O7 前端真实路由联调前，`submit_enabled` 与 `rollback` 仍应保持 fail-closed。
- 标注 schema 先支持 JSON mock 能力，复杂标注关系（多标注并发冲突、版本历史、审计签名）在后续迭代实现。
