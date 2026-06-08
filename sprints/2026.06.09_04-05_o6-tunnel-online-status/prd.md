# O6 Tunnel Online Status PRD

## 需求概述

本轮在 `O6` 链路中补齐 `KR1` 设计：上位机通过隧道/心跳对云端汇报在线状态，云端基于 `last_seen_at + ttl` 判断 `online/offline`，并通过列表与单体查询接口供 O7/运营端读取。

这是 **local/mock software proof** 阶段需求，不用于判断真实公网、真实 4G、真实 frp/WireGuard/ngrok 连通是否已建立，不用于执行机器人控制。

## 目标用户

- Full-Stack 工程：要有稳定可实现的 endpoint、状态语义、错误边界和存储形态，才能一次性把隧道心跳链路接通。
- PC/运营：要知道当前每台机器人是否最近在线，能按 `robot_id` 查询最近状态。
- Product/QA：要有统一 fail-closed 证据，不把 local/mock 状态误读为 production 成功。

## 用户价值

1. 让 O7/运营层有统一的“在线性价比”信号，而不是把 `heartbeat` 写成散落日志；
2. 让后续真实隧道切换时只替换 transport，不重写 API 契约；
3. 在真实 4G 和公网接入前，先把边界和输入约束固化，降低安全与控制面风险。

## 范围内功能（P0）

### 1) `POST /api/o6/tunnel/heartbeat`

#### 请求

- `robot_id`：string，必填，非空。
- `tunnel_provider`：string，必填，必须为 `frp | wireguard | ngrok | mock` 之一。
- `endpoint`：string，可选；只允许记录不含 token 的白名单内容。
- `observed_at`：number，可选；若缺省按 server time。
- `ttl_seconds`：number，可选；建议范围 `60 <= ttl_seconds <= 86400`，默认 `300`。
- `metadata`：object，可选白名单，仅允许小对象：
  - `ip_family`
  - `network_type`
  - `region`
  - `notes`（长度上限）

#### 响应

- 统一 schema：`trashbot.o6.tunnel_status.v1`
- `source`：`local_mock_tunnel_status`
- 返回 `last_seen_at_ms`、`ttl_seconds`、`status`（`online|offline` 计算后）；
- 必含 `real_tunnel_connected=false`、`real_4g_connected=false`、`connects_cloud_production=false`、`robot_control_executed=false`。

#### 验证规则（本接口）

- content-length 过滤防超大 body；
- body 必须是 JSON 对象；
- 禁止回显敏感 key/value：`Authorization`、`Bearer`、`token`、`password`、`secret`、`private_key`、`credential` URL、`/cmd_vel`；
- 不执行任何机器人控制命令。

### 2) `GET /api/o6/tunnel/robots`

- 返回最近 heartbeats 记录；
- 每条记录含：`robot_id`、`status`、`last_seen_at_ms`、`ttl_seconds`、`endpoint`（脱敏）与 `source`；
- 支持可选查询参数：
  - `limit`（1~100，默认 50）；
  - `status`（`online|offline|all`，默认 `all`）；
  - `provider`（可选过滤）。
- 排序：`last_seen_at_ms` 倒序。

### 3) `GET /api/o6/tunnel/robots/<robot_id>`

- 成功返回该机器人最近状态；
- 未命中返回 `404`，且为 fail-closed（不泄露输入、metadata 或敏感字段）。

### 状态计算语义

对单条记录：

- 设 `last_seen_at_ms` 为最后上报时间（或 `observed_at`/服务端接收时间）；
- 设 `ttl_seconds` 为当前记录 TTL；
- 当前时间 `now_ms` 满足 `now_ms <= last_seen_at_ms + ttl_seconds*1000` 判定为 `online`；
- 否则判定为 `offline`。
- `unknown robot` 永远是 `404`（本 sprint 不返回 `offline` 兜底）。

## 固定边界与安全字段

所有成功响应必须可见：

- `schema: trashbot.o6.tunnel_status.v1`
- `schema_version: 1`
- `source: local_mock_tunnel_status`
- `proof_status: not_proven`
- `real_tunnel_connected: false`
- `real_4g_connected: false`
- `connects_cloud_production: false`
- `robot_control_executed: false`
- `safe_to_control: false`（若已有字段体系）

`/api/o6/tunnel/robots/<robot_id>` 命中时返回 `status`，但不得返回 raw endpoint token，endpoint 字段必须脱敏/掩码。

## 范围外

- 不实现真实隧道建连、真实重连算法、DNS/IPv6 真实拨测。
- 不接入真实 4G、真实公网、真实 TLS 证书验证闭环。
- 不执行 robot 控制命令（含 `/cmd_vel`）；
- 不新增硬件相关串口、UART、WAVE ROVER、Orange Pi 驱动、Nav2 逻辑；
- 不新增模型/标签/任务存档主线。

## KR 拆解（本轮）

- `KR1-A`：定义/冻结 `POST /api/o6/tunnel/heartbeat` payload 与 fail-closed 校验。
- `KR1-B`：定义状态查询接口 `GET /api/o6/tunnel/robots` 与 `GET /api/o6/tunnel/robots/<robot_id>`。
- `KR1-C`：统一 `status = online/offline` 计算语义，并固定 `trashbot.o6.tunnel_status.v1` + `local_mock_tunnel_status`。
- `KR1-D`：定义 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 兼容的 file-backed 存储风格（路径、测试隔离、local/mock 约束）及 endpoint 仅脱敏策略。
- `KR1-E`：定义安全边界：不回显敏感字段、不保存凭据、不执行控制。

## 优先级与验收口径（设计交付）

P0 完成后，工程才可进入实现：

- `POST /api/o6/tunnel/heartbeat` 可成功写入并返回固定边界字段；
- `GET /api/o6/tunnel/robots` 可按最近状态返回集合；
- `GET /api/o6/tunnel/robots/<robot_id>` 可返回该车在线/离线；
- 未命中 robot 返回 404 并 fail-closed；
- 所有成功响应均包含 schema/source/not_proven + 真实能力 false 字段；
- endpoint 不回显凭据（仅脱敏或不可回显 token）。

P1 验收项：

- 文档（本 sprint 3 文件）完整、字段一致；
- 设计评审明确标记 `local/mock software proof` 与“未完成真实隧道/4G/控制”的边界；
- 实现前/实现后均不改动旧未跟踪目录 `sprints/2026.06.09_00-01_o6-local-cloud-archive-mvp/`。

## 责任 Owner

- `product-okr-owner`：产品设计、验收口径、风险边界定义；
- 主责实现：`full-stack-software-engineer`（单线闭环）；
- 确认咨询：无硬件并行咨询，本轮不要求算法/硬件并行。

## 风险与证据边界

- 本轮产出 `local/mock proof`，不能认定真实隧道已接通；
- 仅输出最小状态快照，不替代机器控制、任务投递、回滚或 delivery 成功判断；
- endpoint、token、secret 只允许出现脱敏值；
- 真实部署的 SSH、frp/WireGuard/ngrok 客户端/服务端与云端凭据，在后续实现/验证 sprint 的部署章节处理（不在本文件字段中硬编码）。
