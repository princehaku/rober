# O6 Event Evidence Archive Tech Done

## sprint_type: epic

本轮按 `tech-plan.md` 实现 O6 Event Evidence Archive，主责 owner 为 `full-stack-software-engineer`。范围限定在 local/mock cloud archive API、测试、接口文档、PC 产品边界、cloud-relay README 和本 sprint 收口文档；未改硬件、WAVE ROVER、Orange Pi 串口、ROS launch、真实 SSH 上车配置或 PC/手机 UI 功能代码。

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `trashbot.o6.archive_events.v1` / `local_mock_event_archive`。
  - 新增 `trashbot.o6.archive_evidence.v1` / `local_mock_evidence_archive`。
  - 新增 `POST /api/o6/archive/events`、`GET /api/o6/archive/events`、`POST /api/o6/archive/evidence`、`GET /api/o6/archive/evidence`。
  - events 只允许附着已有 task，幂等键为 `task_id + event_id`。
  - evidence 只保存 `evidence_ref` basename 摘要，幂等键为 `task_id + evidence_id`，固定 `real_oss_upload_success=false`。
  - GET 支持 `robot_id/task_id/type/time/event_id/limit` 过滤，返回白名单字段和 summary。
  - fail-closed 覆盖 bad JSON、非对象、缺字段、数组过大、`unknown_task`、`unauthorized_task`、非法类型、越过 task 时间窗、unsafe content、真实能力声明、非法 query 和 raw content。
  - `GET /api/o6/archive/tasks/<task_id>` 兼容读回新增 `events[]` 与 `evidence_refs[]` 摘要。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 新增 event archive 成功写入/查询/过滤/task detail 读回测试。
  - 新增 event archive 幂等和混合批次测试。
  - 新增 evidence archive 成功写入/查询/过滤/task detail 读回测试。
  - 新增 evidence archive 幂等和混合批次测试。
  - 新增 event/evidence fail-closed 覆盖。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 补齐四个新 endpoint 的 request/response/filter/idempotency/fail-closed contract。
- `docs/product/pc_tools_workstation.md`
  - 补齐 PC/O7 消费新 event/evidence timeline 的产品边界和禁止解释。
- `cloud-relay/README.md`
  - 补齐 cloud-relay runtime 使用说明和 local/mock 证据边界。

## 验证结果

实现阶段指定命令已运行：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

结果：通过，无输出。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

结果：

```text
Ran 142 tests in 46.238s

OK
```

```bash
rg -n "trashbot\\.o6\\.archive_events\\.v1|trashbot\\.o6\\.archive_evidence\\.v1|POST /api/o6/archive/events|GET /api/o6/archive/events|POST /api/o6/archive/evidence|GET /api/o6/archive/evidence|local_mock_event_archive|local_mock_evidence_archive|real_oss_upload_success=false|archive_event_written|archive_evidence_written|unknown_task|unauthorized_task|fail-closed" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_05-06_o6-event-evidence-archive
```

结果：通过，命中新增 schema、route、source、固定 false 字段、fail-closed 和 sprint 设计/收口文档关键字。

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_05-06_o6-event-evidence-archive
```

结果：通过，无 whitespace error。

第一轮 unittest 曾失败于 `oss://...` evidence ref 被旧 `_safe_text()` 脱敏为 `[redacted]`，导致新增写入返回 `evidence_ref is required`。已定位为新 API 不应复用旧 path-only ref helper 处理对象引用；修复为新路径先安全校验 URL，再保存 path basename 摘要，随后完整 unittest 通过。

## 剩余风险

- 本轮仍是 local/mock file-backed proof，不证明真实 cloud DB、production queue、真实 OSS 上传、CDN 可读、4G、公网 HTTPS/TLS、真实机器人控制或现场采集成功。
- `evidence_ref` 只保存 basename 摘要，满足本轮“不保存原始内容”的安全边界；后续若 O7 需要完整 object key，需要另起 sprint 设计脱敏 object key contract。
- 未运行 Docker/Humble `colcon build`，因为本轮验收命令限定 Python 编译、unittest、rg 和 diff check；本轮不改 ROS launch 或硬件路径。
