# sprint_type: micro

## 实际改动

- 在 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 新增 O6 local/mock cloud archive API：
  - `POST /api/o6/archive/tasks`
  - `GET /api/o6/archive/tasks`
  - `GET /api/o6/archive/tasks/<task_id>`
- 新增 file-backed 本地 mock store，路径由 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 注入，未设置时回落到系统临时目录默认文件。
- 给 `POST /api/o6/archive/tasks` 加了路由局部 body 大小限制，读取 JSON 前先检查 `Content-Length`，超过 `O6_CLOUD_ARCHIVE_MAX_BODY_BYTES = 256 * 1024` 时直接 fail closed 400，不影响其他路由的 JSON 解析行为。
- 固定返回 `trashbot.o6.cloud_archive.v1`，并明确 `source=local_mock_archive`、`real_cloud_db_connected=false`、`real_oss_connected=false`、`connects_cloud_production=false`、`robot_control_executed=false`。
- `task_id` 采用 idempotent upsert，不走 `409 conflict`。
- 对坏 JSON、缺字段、超大数组和 unsafe content 采取 fail closed；响应只输出白名单字段，不回显 raw secrets、`Authorization`、`Bearer`、`/cmd_vel`、串口路径或 credentials URL。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`，补了 O6 API 的空态、upsert/list/detail、unsafe/oversized payload 和超大 raw request body 验证，并修正了旧测试里手工构造 handler 的签名。
- 更新 `cloud-relay/README.md`、`docs/product/pc_tools_workstation.md`，并新增 `docs/interfaces/o6_cloud_archive_api.md`，把 O6 作为 O7 后续可消费的 O6-shaped 数据源讲清楚。

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 通过
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 通过
  - 结果：`Ran 121 tests in 36.047s`
  - 结论：`OK`
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md sprints/2026.06.09_00-01_o6-local-cloud-archive-mvp/tech-done.md`
  - 通过

## 剩余风险

- 这条 O6 链路仍然是本地 mock / file-backed store，不代表真实云数据库、真实 OSS、真实生产网络或真实机器人控制已经接通。
- 当前只覆盖了最小 O6 archive 任务形状；后续如果要把 route replay / labeling / voice / safe command 真正串起来，还需要各自的 O7 consumer 再对齐更完整的任务视图和前端页面。
- 默认临时目录路径与环境变量路径切换已支持，但暂未做跨进程/多实例并发压力验证。
