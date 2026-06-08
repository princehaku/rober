# sprint_type: epic

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 O6 隧道在线态接口实现：
    - `POST /api/o6/tunnel/heartbeat`
    - `GET /api/o6/tunnel/robots`
    - `GET /api/o6/tunnel/robots/<robot_id>`
  - 采用同一 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 路径复用 `FileBackedO6CloudArchiveStore`，新增 `tunnel_status` section，保持与 archive 的文件形状兼容。
  - `heartbeat` 入参支持 `robot_id`、`tunnel_provider`、`endpoint`、`observed_at`、`ttl_seconds`、`metadata`，其中 `endpoint` 脱敏后入库和回显。
  - `observed_at` 支持整数毫秒和 ISO8601（支持字符串空值回退服务端时钟），`status` 按 `now_ms <= last_seen_at_ms + ttl_seconds*1000` 计算。
  - `/api/o6/tunnel/robots` 支持 `status=online|offline|all`、`provider`、`limit` 过滤，默认按 `last_seen_at_ms` 倒序。
  - `/api/o6/tunnel/robots/<robot_id>` 未命中返回 `404` fail-closed。
  - 成功响应固定 `trashbot.o6.tunnel_status.v1`、`schema_version=1`、`source=local_mock_tunnel_status`、`proof_status=not_proven`、`safe_to_control=false`、`real_tunnel_connected=false`、`real_4g_connected=false`、`connects_cloud_production=false`、`robot_control_executed=false`。
  - `tunnel` 相关响应使用 `_send_tunnel_status_json`，避免通用脱敏逻辑误改 `endpoint` `://` 字段展示。
  - 写入 `payload` 和查询响应做 `body` 大小限制与 fail-closed 验证，拒绝 unsafe content（含 `Authorization/Bearer/token/password/secret/private_key/credential URL/ /cmd_vel / serial/baudrate/traceback`）。

- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 增加 tunnel API 的单测闭环：
    - `POST` 不支持的 provider、unsafe endpoint/metadata、超大 body / 非对象 JSON 的 fail-closed。
    - 额外补上 `metadata.notes: "token=leaked"`、endpoint `traceback`、metadata `traceback observed` 的 fail-closed 断言，和文档/README 中的 unsafe content 口径对齐。
    - 心跳入库成功后回读 endpoint 脱敏、`status/last_seen_at_ms/ttl_seconds` 一致性。
    - `GET /api/o6/tunnel/robots` 的 `status/provider/limit` 过滤与排序。
    - `GET /api/o6/tunnel/robots/<robot_id>` 成功与 `404` 分支。
    - `FileBackedO6CloudArchiveStore` 在 fixture 里同时恢复 `tasks` 与 `tunnel_status`。

- `docs/interfaces/o6_cloud_archive_api.md`
  - 增补 O6 tunnel online status contract：请求字段、响应固定字段、列表/单体查询语义、status 语义与 fail-closed 规则、unsafe 说明同步到接口文档。

- `docs/product/pc_tools_workstation.md`
  - 增补 PC 工具链 O6 Tunnel Online Status API 在 `PC-Tools` 边界展示中的说明：只读链路、状态语义、固定 false fields 与不承诺真实 4G/隧道/控制能力。

- `cloud-relay/README.md`
  - 增补本轮新增 O6 tunnel API 说明：同 Store 复用、请求/过滤参数、固定边界字段、脱敏与 fail-closed 边界、`real/4G/control` 不承诺声明。

## 验证结果

- 设计与验收文件完整性（已在代码实现后保留）
  - `test -f sprints/2026.06.09_04-05_o6-tunnel-online-status/pre_start.md && test -f sprints/2026.06.09_04-05_o6-tunnel-online-status/prd.md && test -f sprints/2026.06.09_04-05_o6-tunnel-online-status/tech-plan.md`
  - `test` 返回码通过（无输出错误）。

- 命令检查
  - `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
    - 通过
  - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
    - 通过
    - 关键片段：`Ran 136 tests` / `OK`
    - 追加验证了 tunnel heartbeat 对普通文本 `token=leaked` 与 `traceback` 的 fail-closed。
  - `rg -n "trashbot\.o6\.tunnel_status\.v1|local_mock_tunnel_status|real_tunnel_connected|real_4g_connected|connects_cloud_production|robot_control_executed|/api/o6/tunnel/heartbeat|/api/o6/tunnel/robots|ttl_seconds|online|offline|TRASHBOT_O6_CLOUD_ARCHIVE_STATE|fail-closed" onboard/src/ros2_trashbot_behavior/...`
    - 可见新功能关键字覆盖到 `remote_cloud_relay.py`、测试、接口文档与本轮 sprint 文档。
  - `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_04-05_o6-tunnel-online-status`
    - 未发现空白/缩进类问题。

## 剩余风险

- 本轮仍是 local/mock software proof：不代表真实公网隧道、4G、TLS、云端生产 DB/queue、机器人控制链路已接通。
- endpoint 脱敏采用最小化规则，仍建议与后续真实隧道部署统一 credential/url 脱敏策略。
- `status` 判断使用本地 `last_seen_at_ms + ttl`，未覆盖跨实例时钟漂移、历史重放和网络抖动补偿策略。
