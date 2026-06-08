# O6 Model Inference API Final

## 收口结论

本轮 O6-KR5 local/mock 模型推理接口已完成软件侧 contract proof。

已交付：

- `POST /api/o6/archive/inference`
- `trashbot.o6.model_inference.v1`
- `local_mock_inference`
- `model_inference.elevator_door_state`
- `model_inference.floor_recognition`
- `unknown_task`
- `unauthorized_task`
- `not_proven`
- `fail-closed`

推理结果已写入既有 archive task 的 `events[]`，并可由 `GET /api/o6/archive/tasks/<task_id>` 读回。所有成功响应固定 `real_gpu_model_connected=false`、`real_external_model_api_connected=false`、`real_model_inference_success=false`，不声明真实模型、生产云或机器人控制成功。

## 验证证据

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

通过，无输出。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

通过：

```text
Ran 131 tests in 41.166s

OK
```

```bash
rg -n "trashbot.o6.model_inference.v1|POST /api/o6/archive/inference|local_mock_inference|model_inference.elevator_door_state|model_inference.floor_recognition|real_gpu_model_connected=false|real_external_model_api_connected=false|real_model_inference_success=false|unknown_task|unauthorized_task|not_proven|fail-closed" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_03-04_o6-model-inference-api
```

通过，命中新增 schema、route、source、event type、fail-closed、unknown/unauthorized 和真实能力 false 字段。

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_03-04_o6-model-inference-api
```

通过，无输出。

## OKR 回顾

- 当前最低 Objective 仍是 O6。
- 本轮直接推进 `O6-KR5：模型推理接口（电梯门开/关、楼层识别）可在云端调用，推理结果写入事件存档，不要求 GPU 上线即可用` 的 local/mock 软件证据。
- 因仍未连接真实 GPU、外部模型 API、生产云、OSS、PC/手机真实消费和现场机器人数据，本轮不更新 OKR 百分比。

## 剩余风险

- 真实模型推理服务未接入。
- 真实生产云 DB/queue 未接入。
- 真实 OSS evidence object 未验证。
- PC/手机 UI 尚未消费 inference events。
- 真实电梯门状态、真实楼层识别、机器人控制和现场送达均未证明。

## 最终自检

- 未改硬件配置、ROS2 launch、WAVE ROVER/串口代码、PC UI、手机 UI 或其他 sprint 目录。
- 未触碰未授权旧 sprint `sprints/2026.06.09_00-01_o6-local-cloud-archive-mvp/`。
- 范围自检时间：2026-06-09 03:17:30 CST。
- 实现 worker 未直接 commit/push；主节点验收后按用户要求统一 commit/push。
