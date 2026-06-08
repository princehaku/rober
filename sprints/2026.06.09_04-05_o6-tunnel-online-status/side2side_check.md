# O6 Tunnel Online Status Side-by-side Check

## 对照目标

核对《设计-开发-文档》是否保持同口径，并确认无真实能力误导。

## 对照结果

- 需求项 `POST /api/o6/tunnel/heartbeat` 与实现
  - 设计：必填 `robot_id`、`tunnel_provider`；可选 `endpoint`、`observed_at`、`ttl_seconds`、`metadata`。
  - 实现：`_o6_tunnel_status_validate_payload` 与 `upsert_tunnel_status` 已覆盖；`tunnel_provider` 限制 `frp|wireguard|ngrok|mock`，`ttl_seconds` 限制 `60~86400`。
  - 结果：已对齐。

- 在线/离线语义
  - 设计：`now_ms <= last_seen_at_ms + ttl_seconds * 1000`。
  - 实现：`_o6_tunnel_status_has_online` 与 `list/get` 查询共享同一语义。
  - 结果：已对齐。

- 固定成功字段边界
  - 设计：`schema`/`schema_version`/`source`/`proof_status` 与 all false boundary。
  - 实现：`_o6_tunnel_status_fixed_payload` 固定 `trashbot.o6.tunnel_status.v1`、`schema_version=1`、`source=local_mock_tunnel_status`、`proof_status=not_proven`、`safe_to_control=false`、`real_tunnel_connected=false`、`real_4g_connected=false`、`connects_cloud_production=false`、`robot_control_executed=false`。
  - 结果：已对齐。

- 存储与读取一致性
  - 设计：复用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 同一 store。
  - 实现：`FileBackedO6CloudArchiveStore` 新增 `tunnel_status` 节点，`_load/_persist_locked` 同步读写。
  - 结果：已对齐。

- 安全与 fail-closed
  - 设计：不回显 credential、no `/cmd_vel`、超大 body fail-closed、未知 robot 404、失败不下发控制。
  - 实现：`has_unsafe_payload` 与 `parse_json_body_with_limit` 覆盖拒绝路径；`/api/o6/tunnel/robots/<robot_id>` 未命中返回 `404`；无远程命令分支；已补 `metadata.notes: "token=leaked"`、endpoint `traceback`、metadata `traceback observed` 的 fail-closed 断言。
  - 结果：已对齐。

## 用户端一致性

- `docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md`、`cloud-relay/README.md` 已同步列出 O6 隧道 API、边界字段、脱敏与 fail-closed 说明。
- 结果：一致。

## 未决项

- 无阻塞缺口；剩余为下一阶段真实隧道/4G/公网与控制链路打通前置条件，不在本 sprint 范围。
