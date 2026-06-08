# O6 Cloud Archive API Final

## 收口状态

状态：software proof complete，等待主节点最终验收后 commit/push。

本轮完成 O6 MVP local/mock file-backed archive API 工程闭环：

- 三个 endpoint 可用：`POST /api/o6/archive/tasks`、`GET /api/o6/archive/tasks`、`GET /api/o6/archive/tasks/<task_id>`。
- 本地状态文件入口明确：`TRASHBOT_O6_CLOUD_ARCHIVE_STATE`。
- duplicate `task_id` 使用 idempotent upsert。
- 响应 schema 固定为 `trashbot.o6.cloud_archive.v1`，source 固定为 `local_mock_archive`。
- 真实云和控制边界固定 fail closed：`real_cloud_db_connected=false`、`real_oss_connected=false`、`connects_cloud_production=false`、`robot_control_executed=false`。

## 验证摘要

- `python3 -m py_compile ...`：通过，无输出。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest ...`：通过，`Ran 123 tests in 37.569s`，`OK`。
- `git diff --check -- ...`：通过，无输出。

## OKR 进度建议

本 sprint 可作为 O6 从 0% 起步的第一份软件证据，建议 Product owner 在后续 OKR 收口中把 O6 从 0% 提升到小幅软件侧进展。建议不要大幅提升，因为本轮仍未覆盖 O6-KR1 真实隧道、O6-KR4 标注 API、O6-KR5 模型推理、真实 DB、真实 OSS 或 production cloud。

## 提交建议

主节点最终验收通过后可以 commit/push。提交说明建议明确：

```text
Add O6 local mock cloud archive API software proof
```

提交说明必须保留证据边界：local/mock file-backed O6 archive API software proof，不证明真实 cloud DB、OSS、production cloud、4G、隧道或机器人控制。

## 剩余风险

- 未连接真实云数据库或队列。
- 未连接真实 OSS，`evidence_refs[]` 只是引用形状。
- 未证明公网 HTTPS/TLS、4G/SIM、隧道接入或 production deploy。
- 未实现真实标注提交、模型推理、RTC/视频、ASR/TTS、手控/寻路。
- 未 SSH 上车、未操作硬件、未跑 HIL；因此不能声明 WAVE ROVER、串口、Nav2 或真实送达通过。
- 旧未跟踪目录 `sprints/2026.06.09_00-01_o6-local-cloud-archive-mvp/` 仍存在且本轮未触碰。
