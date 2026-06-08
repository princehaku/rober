# O6 Tunnel Online Status Tech Plan

## 计划状态

本文件完成后，设计阶段可转交 `full-stack-software-engineer` 做实现。  
当前只做文档化和验收口径，不写产品代码。

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前完成度最低的是 `O6：云端核心后端——数据存档、模型推理与打标平台`。
2. 本 sprint 直接落地 `O6-KR1（上位机隧道/心跳接入与在线状态）`。
3. 继续原因：前 3 轮已完成 local/mock 的 `archive`、`labeling`、`inference`，缺口集中在隧道在线态可观测链路；提前完成会减少后续 O7 与运营层误读。

## 技术目标

定义 `local/mock` 心跳状态 API，在既有 O6 风格下提供统一的在线/离线快照：  
`POST /api/o6/tunnel/heartbeat`、`GET /api/o6/tunnel/robots`、`GET /api/o6/tunnel/robots/<robot_id>`。

固定响应头语义：
- `schema=trashbot.o6.tunnel_status.v1`
- `source=local_mock_tunnel_status`
- `real_tunnel_connected=false`
- `real_4g_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `proof_status=not_proven`

## 执行 owner

- 主责：`full-stack-software-engineer`，单 owner 单线闭环；
- 不并行原因：接口、存储、测试与文档同步都集中在同一状态 API 形状下。

## 文件范围（建议）

工程实现建议改动范围（本 sprint 设计仅产出此目录文件）：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `sprints/2026.06.09_04-05_o6-tunnel-online-status/tech-done.md`
- `sprints/2026.06.09_04-05_o6-tunnel-online-status/side2side_check.md`
- `sprints/2026.06.09_04-05_o6-tunnel-online-status/final.md`
- `docs/interfaces/o6_cloud_archive_api.md`（建议补充 `tunnel` 摘要字段）
- `docs/product/pc_tools_workstation.md`（建议补充 `robots tunnel status` 只读说明）
- `cloud-relay/README.md`（建议补充 local/mock tunnel status boundary）

不得触碰的范围：硬件协议、ROS2 mainline、WAVE ROVER、串口、4G 硬件驱动、前端应用源码。

## 接口实现约束（供工程实现）

### A. 心跳上报：`POST /api/o6/tunnel/heartbeat`

请求示例：

```json
{
  "robot_id": "trashbot-001",
  "tunnel_provider": "frp",
  "endpoint": "<redacted-endpoint-or-host>",
  "observed_at": 1750000123000,
  "ttl_seconds": 300,
  "metadata": {
    "ip_family": "ipv4",
    "network_type": "cellular",
    "region": "cn-hangzhou"
  }
}
```

要求：
- `tunnel_provider` 仅允许枚举；
- `endpoint` 存储/返回时必须脱敏（如不保存 token、端口参数）；
- `ttl_seconds` 必须在可预测范围；
- `metadata` 仅允许安全白名单字段，长度与深度受限；
- 失败返回 `400/422` + fail-closed 消息，不执行控制。

### B. `GET /api/o6/tunnel/robots`

返回示例（字段示意）：

```json
{
  "schema": "trashbot.o6.tunnel_status.v1",
  "schema_version": 1,
  "source": "local_mock_tunnel_status",
  "updated_at_ms": 1750000123000,
  "query": {"limit": 50, "status": "all"},
  "real_tunnel_connected": false,
  "robots": [
    {
      "robot_id": "trashbot-001",
      "status": "online",
      "last_seen_at_ms": 1750000123000,
      "ttl_seconds": 300,
      "observed_at_ms": 1750000123000,
      "endpoint": "<redacted-endpoint>",
      "tunnel_provider": "frp"
    }
  ]
}
```

要求：
- 按 `last_seen_at_ms` 倒序；
- 只返回白名单字段；
- 支持 `status`/`limit`/`provider` 过滤（本 sprint 推荐）。

### C. `GET /api/o6/tunnel/robots/<robot_id>`

返回示例（字段示意）：

```json
{
  "schema": "trashbot.o6.tunnel_status.v1",
  "schema_version": 1,
  "source": "local_mock_tunnel_status",
  "robot_id": "trashbot-001",
  "status": "online",
  "last_seen_at_ms": 1750000123000,
  "ttl_seconds": 300,
  "observed_at_ms": 1750000123000,
  "not_found": false,
  "real_tunnel_connected": false,
  "robot_control_executed": false
}
```

要求：
- 若查询不到，返回 `404` + fail-closed，不回显输入或敏感值；
- 失败不返回 raw endpoint token。

## 数据存储与既有 O6 兼容

- 推荐复用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 路径体系：  
  - 同一类文件路径风格（可配置、测试可重定向、默认回落）；
  - 与 O6 现有测试风格一致（最小 fixture/临时文件隔离）；
  - 共享 store 结构中新增 `tunnel_status` section，避免另起一套路径和并发语义。
- 写入与读取必须为可幂等读模型，重复上报不产生重复实体；
- `endpoint` 只保留 sanitized 信息。

## 安全与 Fail-Closed 要求

- 禁止记录/回显：
  - `Authorization`/`Bearer`
  - `token`/`password`/`secret`/`private_key`
  - credential URL
  - `/cmd_vel`
- 不执行任何下发命令/控制动作；
- 超大 body 与非 JSON body 直接拒绝；
- 对越权/未知 robot 返回明确失败态，不创建“离线占位”记录。

## 验收命令（设计阶段）

```bash
test -f sprints/2026.06.09_04-05_o6-tunnel-online-status/pre_start.md && test -f sprints/2026.06.09_04-05_o6-tunnel-online-status/prd.md && test -f sprints/2026.06.09_04-05_o6-tunnel-online-status/tech-plan.md
```

```bash
rg -n "trashbot\\.o6\\.tunnel_status\\.v1|local_mock_tunnel_status|real_tunnel_connected|real_4g_connected|connects_cloud_production|robot_control_executed|/api/o6/tunnel/heartbeat|/api/o6/tunnel/robots|ttl_seconds|online|offline|TRASHBOT_O6_CLOUD_ARCHIVE_STATE|fail-closed|sprint_type: epic" sprints/2026.06.09_04-05_o6-tunnel-online-status
```

```bash
git diff --check -- sprints/2026.06.09_04-05_o6-tunnel-online-status/pre_start.md sprints/2026.06.09_04-05_o6-tunnel-online-status/prd.md sprints/2026.06.09_04-05_o6-tunnel-online-status/tech-plan.md
```

## 交付门槛

- 设计文档通过内部评审；
- 设计命令通过 `test` + `rg` + `git diff --check`；
- 工程实现阶段再补 `tech-done.md / side2side_check.md / final.md`；
- commit 前由主节点确认本 sprint 的设计与工程实现均无真实能力误导字段。

## 风险边界（本轮）

- 本轮只证明 local/mock 软件形状，不覆盖真实隧道 reconnect/retry、证书链、真实 endpoint 泄露防护策略（只做最小脱敏方案）；
- 4G/公网到位时，需增加 `connects_cloud_production` 与重试链路证据，不在本轮范围；
- O7 前端/手机页如需历史趋势图/告警策略，需要后续 KR 或独立 sprint 补齐。
