# O6 Tunnel Online Status Sprint Final

## 结果回顾

本轮完成 O6-KR1 的 local/mock 隧道在线态链路软件形状：  
`POST /api/o6/tunnel/heartbeat`、`GET /api/o6/tunnel/robots`、`GET /api/o6/tunnel/robots/<robot_id>` 已接入，并在 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 的 `FileBackedO6CloudArchiveStore` 下新增 `tunnel_status` section。  

接口返回固定边界字段，始终宣告 non-production：`schema=trashbot.o6.tunnel_status.v1`、`source=local_mock_tunnel_status`、`proof_status=not_proven`、`safe_to_control=false`、`real_tunnel_connected=false`、`real_4g_connected=false`、`connects_cloud_production=false`、`robot_control_executed=false`。

## 需求收口（与 PRD 对齐）

- 端点覆盖：`heartbeat`、`robots`、`robots/<robot_id>` 均已可用，并支持 `status/provider/limit` 查询。
- 状态语义：`online/offline` 按 `now_ms <= last_seen_at_ms + ttl_seconds * 1000`。
- 输入与安全：非法 `provider`、bad JSON、超大 body、unsafe 内容与 `endpoint`/`metadata` 非法字段均 fail-closed。
  - 其中 tunnel heartbeat 现已明确拒绝普通文本 `token=leaked` 与 `traceback`，和文档口径一致。
- 存储策略：与既有 O6 archive store 同一环境变量 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE`，未新增独立路径。
- 前后端文档：接口边界已同步到 `docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md`、`cloud-relay/README.md`；Sprint 文档增加 `tech-done / side2side_check / final`。

## 验收证据

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`：通过
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 通过，关键输出：`Ran 136 tests in ... OK`
  - 新增 tunnel heartbeat 的 `token=leaked` / `traceback` fail-closed 断言后，测试总数保持 `136`。
- `rg -n ... /api/o6/tunnel/...`（设计关键字、接口关键字）在实现/测试/文档中命中齐套。
- `git diff --check -- ...`（涉及实现、测试、文档与本轮 sprint）无 whitespace/error 警告。

## 剩余风险与后续

- 仍是软件证据层，不代表真实隧道建连、真实 4G、真实公网 TLS、真实云 DB/queue、或机器人下发控制能力已接通。
- 已满足本 sprint 范围；下轮应补真实隧道部署材料、endpoint 真实性校验、跨实例时钟漂移与探测/抖动补偿策略。
