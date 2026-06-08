# O6 Cloud Archive API Tech Done

## sprint_type

sprint_type: epic

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 增加 `trashbot.o6.cloud_archive.v1` local/mock file-backed archive API。
  - 增加 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 状态文件入口，未配置时回落到系统临时目录。
  - 支持 `POST /api/o6/archive/tasks`、`GET /api/o6/archive/tasks`、`GET /api/o6/archive/tasks/<task_id>`。
  - 支持 duplicate `task_id` idempotent upsert。
  - 固定输出 `source=local_mock_archive`、`real_cloud_db_connected=false`、`real_oss_connected=false`、`connects_cloud_production=false`、`robot_control_executed=false`。
  - 对坏 JSON、缺字段、倒序时间、数组过大、凭证/控制/串口/traceback 等 unsafe 内容 fail closed。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 增加 O6 空列表、upsert/list/detail、unsafe/oversized、坏 JSON、缺字段、倒序时间、missing detail fail-closed 覆盖。
  - 测试使用临时 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE`，避免污染开发机状态。
- `cloud-relay/README.md`
  - 补充 O6 local/mock archive API 启用方式、请求字段、upsert 和 not-proven 边界。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 新增 O6 archive API contract，记录 endpoint、request、response、fail-closed 和 O7 consumption 边界。
- `docs/product/pc_tools_workstation.md`
  - 补充 PC/O7 后续消费 O6-shaped 数据源的产品边界。

## 验证结果

运行时间：2026-06-09 01:15:08 CST。

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

结果：通过，无输出。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

结果：

```text
Ran 123 tests in 37.569s

OK
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md sprints/2026.06.09_01-02_o6-cloud-archive-api
```

结果：通过，无输出。

## 失败定位

- 首轮验收命令在补强前已通过：`py_compile` 通过、`unittest` 为 `Ran 121 tests in 36.524s OK`、`git diff --check` 通过。
- 自检发现 `trajectory_frames` / `events` 缺字段会被静默视为空数组，不符合本 sprint `tech-plan.md` 的 required request contract。
- 已修复为必填数组校验，并补充坏 JSON、缺字段、倒序时间和 missing detail 单测；最终复跑后 `Ran 123 tests in 37.569s OK`。

## 剩余风险

- 本轮只证明 local/mock file-backed O6-shaped archive API，不证明真实云 DB、真实 OSS、production cloud、TLS、公网、4G/SIM 或隧道接入。
- `evidence_refs[]` 只保留对象引用形状，不证明 OSS 对象实际存在或可访问。
- 本轮不实现真实标注提交、模型推理、RTC/视频、ASR/TTS、手控/寻路或机器人控制。
- 本轮未 SSH 上车、未读写串口、未触发 WAVE ROVER/HIL；硬件事实未进入真实集成验证阶段。
- 工作区仍存在禁止触碰的旧未跟踪目录 `sprints/2026.06.09_00-01_o6-local-cloud-archive-mvp/`，本轮未修改或删除。
