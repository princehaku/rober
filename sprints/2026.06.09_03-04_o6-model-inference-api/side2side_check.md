# O6 Model Inference API Side-by-Side Check

## 验收口径对照

| tech-plan / PRD 口径 | 实现结果 | 状态 |
| --- | --- | --- |
| 新增 `POST /api/o6/archive/inference` | 已在 relay HTTP handler 中新增 POST route | 通过 |
| 复用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` / `FileBackedO6CloudArchiveStore` | `build_server()` 仍创建同一 archive store，inference 通过 `archive_store.upsert_inference()` 写入 | 通过 |
| 只允许对已有 archive task 写入 | unknown task 返回 `unknown_task`，不会创建 task | 通过 |
| robot mismatch 返回 `unauthorized_task` | `task.robot_id != request.robot_id` 返回 403 | 通过 |
| 支持 `elevator_door_state` 与 `floor_recognition` | requested output 白名单只包含两项 | 通过 |
| 事件写入 `events[]` 并可从 task detail 读回 | `GET /api/o6/archive/tasks/<task_id>` 返回 `model_inference.elevator_door_state` / `model_inference.floor_recognition` 事件 | 通过 |
| 成功响应固定 `trashbot.o6.model_inference.v1` / `local_mock_inference` / `not_proven` | 响应和测试均覆盖固定字段 | 通过 |
| 真实能力 false 字段 | `real_gpu_model_connected=false`、`real_external_model_api_connected=false`、`real_model_inference_success=false`、`robot_control_executed=false` 固定保留 | 通过 |
| 幂等键 `task_id + inference_id + input_id + result_type` | 重复提交更新既有事件，混合批次返回 updated | 通过 |
| fail-closed | bad JSON、非对象、缺字段、数组过大、未知 output、unsafe content、真实能力声明、时间窗外输入均返回 4xx | 通过 |
| 文档同步 | `docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md`、`cloud-relay/README.md` 已更新 | 通过 |

## 用户旅程变化

- PC/O7 后续可以从同一个 O6 archive task detail 中看到推理事件，不需要 UI 自造电梯门状态或楼层证据。
- 手机/PC 后续消费方能读取 `proof_status=not_proven` 和真实能力 false 字段，避免把 mock 推理误导成真实模型或真实控制依据。
- 工程 QA 可以用本地 file-backed store 复现写入、重复提交、查询和 fail-closed 行为。

## 尚未覆盖

- 未接真实模型服务、真实 GPU、真实外部模型 API。
- 未接真实生产云 DB/queue、真实 OSS/CDN、真实 4G/SIM。
- 未做 PC UI 或手机 UI 改造。
- 未做真实机器人、电梯、底盘控制、HIL 或现场验证。
