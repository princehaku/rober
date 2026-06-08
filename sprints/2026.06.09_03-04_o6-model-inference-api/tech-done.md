# O6 Model Inference API Tech Done

## sprint_type

sprint_type: epic

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `POST /api/o6/archive/inference`。
  - 新增 `trashbot.o6.model_inference.v1` 成功响应合同。
  - 复用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 与 `FileBackedO6CloudArchiveStore`，只允许对已有 archive task 写入 local/mock inference events。
  - 支持 `elevator_door_state` 与 `floor_recognition`，事件类型固定为 `model_inference.elevator_door_state` / `model_inference.floor_recognition`。
  - 结果可通过 `GET /api/o6/archive/tasks/<task_id>` 的 `events[]` 读回。
  - 幂等键为 `task_id + inference_id + input_id + result_type`，全新结果返回 `201/write_status=created/duplicate=false`，任一旧键命中返回 `200/write_status=updated/duplicate=true`。
  - 成功响应固定 `source=local_mock_inference`、`proof_status=not_proven`、`real_gpu_model_connected=false`、`real_external_model_api_connected=false`、`real_model_inference_success=false`。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 覆盖 inference 成功写入和 detail 读回。
  - 覆盖幂等更新、混合批次、unknown_task、unauthorized_task。
  - 覆盖 bad JSON、非对象 JSON、缺字段、数组过大、未知 output、unsafe content、真实能力声明、时间窗外输入 fail-closed。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 补充 `POST /api/o6/archive/inference` request/response/event/duplicate/fail-closed contract。
- `docs/product/pc_tools_workstation.md`
  - 补充 PC/O7 对 O6 inference event 的只读消费边界。
- `cloud-relay/README.md`
  - 补充 O6 local/mock inference API、store 复用和真实能力 false 边界。

## 验证结果

运行时间：2026-06-09 03:15:29 CST。

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

结果：通过，无输出。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

结果：

```text
Ran 131 tests in 41.166s

OK
```

最终收口补充运行：

```bash
rg -n "trashbot.o6.model_inference.v1|POST /api/o6/archive/inference|local_mock_inference|model_inference.elevator_door_state|model_inference.floor_recognition|real_gpu_model_connected=false|real_external_model_api_connected=false|real_model_inference_success=false|unknown_task|unauthorized_task|not_proven|fail-closed" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_03-04_o6-model-inference-api
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_03-04_o6-model-inference-api
```

结果：

- `rg`：通过，命中 `trashbot.o6.model_inference.v1`、`POST /api/o6/archive/inference`、`local_mock_inference`、`model_inference.elevator_door_state`、`model_inference.floor_recognition`、`unknown_task`、`unauthorized_task`、`not_proven`、`fail-closed` 以及真实能力 false 字段。
- `git diff --check`：通过，无输出。

## 偏差与失败定位

- 首轮 `py_compile` 通过。
- 首轮 unittest 通过，无失败定位。
- 实现选择保守要求 input 包含 `input_id/input_type/evidence_ref/captured_at_ms`，因为缺少证据引用或采集时间会破坏事件可追溯性和 task 时间窗校验。
- 最终范围自检确认没有修改硬件配置、ROS2 launch、WAVE ROVER/串口代码、PC UI、手机 UI 或未授权旧 sprint `sprints/2026.06.09_00-01_o6-local-cloud-archive-mvp/`。

## 剩余风险

- 本轮只证明 local/mock model inference contract，不证明真实 GPU、真实外部模型 API、真实生产云、真实 OSS、真实电梯门状态、真实楼层识别或机器人控制。
- `archive_event_written=true` 只表示 file-backed local/mock store 写入成功。
- PC/手机后续消费必须继续展示 `not_proven` 与真实能力 false 字段，不能把 `result_value=unknown` 或事件存在解释成真实识别成功。
