# O6 Model Inference API Tech Plan

## 计划状态

本文件完成后只表示设计阶段就绪，不表示已经开始写产品代码。下一步由 `full-stack-software-engineer` 单线闭环实现、测试、修复并补齐 `tech-done.md`、`side2side_check.md`、`final.md`。

本轮设计只证明 `local/mock` model inference contract：电梯门开/关、楼层识别等推理结果可以按合同写入 O6 archive task 的事件存档。它不证明真实 GPU、外部模型、生产云、真实 OSS、真实 PC/手机消费、机器人控制、真实电梯识别或真实送达。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 中最低 Objective 是 `O6：云端核心后端`，进度 `0%`。
2. 本 sprint 直接针对最低 Objective 的 `O6-KR5（模型推理接口）`。
3. 继续理由：最近两轮已经完成 O6 archive task 与 labeling local/mock 软件证据，本轮补齐模型推理 contract，能把电梯门状态和楼层证据写入同一 archive event 数据源，继续为 O7 PC/手机消费铺底。

## 技术目标

新增 O6 local/mock 模型推理 API 设计：

- `POST /api/o6/archive/inference`
- 推理结果写入既有 archive task 的 `events[]` 或等价事件存档。
- `GET /api/o6/archive/tasks/<task_id>` 能读回推理事件。

首批推理结果：

- `elevator_door_state`：值域建议 `open | closed | opening | closing | unknown`。
- `floor_recognition`：值域建议使用字符串楼层证据，如 `B1`、`1F`、`12F`、`unknown`。

所有结果都必须附带 `confidence`、`evidence_ref` 或 `input_id` 摘要，以及 `not_proven` 边界。

## 任务分工

- Product / OKR Owner：完成本 sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`，冻结范围、验收口径和风险边界。
- 实现 owner：`full-stack-software-engineer`。
- 执行方式：单 owner 单线闭环。
- 不并行原因：实现范围集中在同一 HTTP handler、同一 local/mock archive store、同一接口文档/PC 文档/README 边界；拆成多个工程 owner 会增加共享文件冲突。

## 允许改动文件范围

### 本设计阶段允许改动

- `sprints/2026.06.09_03-04_o6-model-inference-api/pre_start.md`
- `sprints/2026.06.09_03-04_o6-model-inference-api/prd.md`
- `sprints/2026.06.09_03-04_o6-model-inference-api/tech-plan.md`

### Engineer 实现阶段允许改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/pc_tools_workstation.md`
- `cloud-relay/README.md`
- `sprints/2026.06.09_03-04_o6-model-inference-api/tech-done.md`
- `sprints/2026.06.09_03-04_o6-model-inference-api/side2side_check.md`
- `sprints/2026.06.09_03-04_o6-model-inference-api/final.md`

不得改动硬件配置、ROS2 launch 参数、WAVE ROVER/串口相关代码、PC UI、手机 UI 或其他 sprint 目录。

## 接口影响

### Request

`POST /api/o6/archive/inference`

```json
{
  "robot_id": "trashbot-001",
  "task_id": "task-2026-06-09-a",
  "inference_id": "infer-0001",
  "model_family": "elevator_scene_stub",
  "requested_outputs": ["elevator_door_state", "floor_recognition"],
  "inputs": [
    {
      "input_id": "frame-0001",
      "input_type": "image_ref",
      "evidence_ref": "rober/trashbot-001/2026-06-09/task-2026-06-09-a/frame-0001.jpg",
      "captured_at_ms": 1780930000000,
      "metadata": {
        "camera": "front",
        "scene": "elevator"
      }
    }
  ]
}
```

约束：

- `task_id` 必须已存在于 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 对应 store。
- `robot_id` 必须与既有 archive task 一致。
- `requested_outputs[]` 最大建议 8，首批只允许 `elevator_door_state` 与 `floor_recognition`。
- `inputs[]` 最大建议 16。
- `metadata` 只能作为小型 JSON object 安全摘要，不能塞原始图像、凭证或完整模型返回体。

### Response

成功响应建议：

```json
{
  "schema": "trashbot.o6.model_inference.v1",
  "schema_version": 1,
  "source": "local_mock_inference",
  "proof_status": "not_proven",
  "safe_to_control": false,
  "delivery_success": false,
  "primary_actions_enabled": false,
  "pc_only": true,
  "connects_cloud_production": false,
  "robot_control_executed": false,
  "real_gpu_model_connected": false,
  "real_external_model_api_connected": false,
  "real_model_inference_success": false,
  "real_floor_recognition_proven": false,
  "real_elevator_door_state_proven": false,
  "archive_event_written": true,
  "write_status": "created",
  "duplicate": false,
  "task_id": "task-2026-06-09-a",
  "inference_id": "infer-0001",
  "results": []
}
```

### Archive event contract

推理结果必须进入目标 task 的事件存档，建议每条结果生成一条事件：

```json
{
  "event_id": "infer-0001:frame-0001:elevator_door_state",
  "event_type": "model_inference.elevator_door_state",
  "occurred_at_ms": 1780930000000,
  "source": "local_mock_inference",
  "inference_id": "infer-0001",
  "input_id": "frame-0001",
  "model_family": "elevator_scene_stub",
  "result_type": "elevator_door_state",
  "result_value": "unknown",
  "confidence": 0.0,
  "evidence_ref": "rober/trashbot-001/2026-06-09/task-2026-06-09-a/frame-0001.jpg",
  "not_proven": [
    "real_gpu_model",
    "real_external_model_api",
    "real_elevator_door_state"
  ]
}
```

`floor_recognition` 使用同样 event 形状，`event_type=model_inference.floor_recognition`，`result_value` 只能作为候选楼层证据，不得被解释成真实到站证明。

### 幂等语义

- 幂等键：`task_id + inference_id + input_id + result_type`。
- 全新结果：`201`，`write_status=created`，`duplicate=false`。
- 已存在结果：`200`，`write_status=updated`，`duplicate=true`。
- 混合批次含任一旧键时，按 `updated` 语义返回，并在摘要里列出 created/updated counts。

### Fail-closed

以下场景必须 fail-closed：

- 坏 JSON、非对象 body、空 body。
- 缺少 `robot_id`、`task_id`、`inference_id`、`model_family`、`requested_outputs[]`、`inputs[]`。
- `requested_outputs[]` 或 `inputs[]` 不是数组、为空或超过上限。
- `requested_outputs[]` 含未知类型。
- `task_id` 不存在：`unknown_task`。
- `robot_id` 与 task 不一致：`unauthorized_task`。
- `captured_at_ms` 类型错误，或明显不在 task 起止时间窗口内。
- unsafe content：`Authorization`、`Bearer`、`token`、`/cmd_vel`、串口路径、`baudrate`、`traceback`、带凭证 URL。
- 请求或 local/mock 结果含真实能力声明：`success=true`、`production_ready=true`、`gpu_connected=true`、`external_model_connected=true`、`floor_recognition_proven=true`、`elevator_door_state_proven=true`、`robot_control_executed=true`。

失败响应不得回显危险内容，不得创建 task，不得写孤儿 inference record，不得触发机器人控制。

## 文档同步要求

Engineer 实现时必须同步更新：

- `docs/interfaces/o6_cloud_archive_api.md`
  - 增加 `POST /api/o6/archive/inference` request/response/event/fail-closed/not_proven contract。
- `docs/product/pc_tools_workstation.md`
  - 增加 PC/O7 后续消费 O6 inference event 的只读边界，明确不能解释成真实电梯识别或真实楼层到达。
- `cloud-relay/README.md`
  - 增加 O6 local/mock inference API 启用方式、store 复用和不证明真实模型/生产云的边界。

## 注释与工程质量要求

- 新增技术注释必须使用中文，并解释为什么保留 local/mock、not_proven 和 fail-closed 边界。
- 注释比例必须超过 20%，尤其是输入校验、幂等更新和事件写入逻辑。
- 不得把 `local_mock_inference`、`not_proven` 或 false 边界字段改成生产成功语义。

## 验收命令

### 设计阶段

```bash
test -f sprints/2026.06.09_03-04_o6-model-inference-api/pre_start.md
```

```bash
test -f sprints/2026.06.09_03-04_o6-model-inference-api/prd.md
```

```bash
test -f sprints/2026.06.09_03-04_o6-model-inference-api/tech-plan.md
```

```bash
rg -n "sprint_type: epic|O6|KR5|模型推理|full-stack-software-engineer|验收命令|OKR 最低优先级核对|local/mock|not_proven|fail-closed" sprints/2026.06.09_03-04_o6-model-inference-api
```

```bash
git diff --check -- sprints/2026.06.09_03-04_o6-model-inference-api
```

### Engineer 实现阶段

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
rg -n "trashbot.o6.model_inference.v1|POST /api/o6/archive/inference|local_mock_inference|model_inference.elevator_door_state|model_inference.floor_recognition|real_gpu_model_connected=false|real_external_model_api_connected=false|real_model_inference_success=false|unknown_task|unauthorized_task|not_proven|fail-closed" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_03-04_o6-model-inference-api
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_03-04_o6-model-inference-api
```

## 给 full-stack-software-engineer 的实现边界

下一步派发给 `full-stack-software-engineer` 时，prompt 必须包含完整角色说明、本轮任务、文件范围、验收命令和输出要求。

实现必须返回：

1. 实际改动的文件列表。
2. 验证命令输出结果。
3. 失败定位（如有）。
4. 剩余风险。

## 收口与提交规则

- 设计阶段不提交产品代码。
- 实现完成后先补 `tech-done.md`，再做 `side2side_check.md` 和 `final.md`。
- 未通过实现阶段验收命令前，不允许 commit/push。
- commit message 建议：

```text
Add O6 local/mock model inference API contract proof
```

提交说明必须保留证据边界：`local/mock` model inference contract software proof，不证明真实 GPU、外部模型、生产云、真实 OSS、4G、隧道、机器人控制、真实电梯识别或真实送达。

## 风险边界

- 本 sprint 只设计并后续证明 local/mock inference contract，不证明真实模型能力。
- 当前不接生产 DB/queue/OSS/CDN，因此 archive event 只是本地 file-backed proof。
- 真实楼层识别、真实电梯门状态、真实 PC/手机消费和真实机器人控制必须后续独立验收。
- 任何消费端必须保留 `not_proven`、`safe_to_control=false`、`robot_control_executed=false`，不得把推理结果当成自动驾驶闭环完成。
