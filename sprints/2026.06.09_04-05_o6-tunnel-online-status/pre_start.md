# O6 Tunnel Online Status Epic Pre-Start

## sprint_type

sprint_type: epic

## 背景

按 Automation 1 小时 OKR 约束，新的 iteration 从 `2026-06-09` 启动：

- 上位机可通过 `ssh root@192.168.1.11 -p 37878` 访问；
- 先完成设计，不做功能代码；
- 设计不足不允许进入编码；
- 编码不完美不允许提交；
- 本轮结束后由主节点执行统一 `git commit/push`。

上位机真实隧道/公网部署属于后续验证事项；本轮先做 `local/mock` 软件形状，保证 O7 与上位机状态感知有统一入口，不把 mock 写成生产状态。

## 用户价值与产品北极星

**北极星**：让云端状态层可持续观测。  
这轮把 `O6-KR1` 聚焦为“上位机隧道心跳 + 云端在线/离线可观测”，先让生产链路有统一、可复现、可回放的状态数据形状。  
价值是“是否有真实 4G/公网”之前，先确认软件形状、边界与风险可回归，避免前后端、PC、手机和运维文档再各说各话。

## OKR 映射和方向判断

- 当前最低 Objective：`O6：云端核心后端——数据存档、模型推理与打标平台`（`OKR.md` 4.1 中当前最低，约 0%）。
- 本轮方向判断：**继续（continue）O6**，推进 `O6-KR1`。
- 判断依据：
  - 以已有 `sprints/2026.06.09_01-02_o6-cloud-archive-api`、`sprints/2026.06.09_02-03_o6-labeling-api`、`sprints/2026.06.09_03-04_o6-model-inference-api` 为前置，O6 已形成 `tasks/labels/inference` 的 local/mock 数据主线；
  - 本轮缺口是“隧道接入后的在线/离线感知语义”；
  - 先把 `heartbeat -> last_seen_at + ttl -> online/offline` 语义定稿，是后续隧道真实接入前的最低风险设计层。

## KR 拆解、历史归档与风险区分

### 本轮推进 KR

- `O6-KR1`：Orange Pi 上位机通过隧道/心跳接入云端，云端可感知在线/离线状态。

### 已完成 KR（历史归档）

- `O6-KR2/3/KR6` local/mock 软件证据：
  - `sprints/2026.06.09_01-02_o6-cloud-archive-api/final.md`
  - `sprints/2026.06.09_01-02_o6-cloud-archive-api/tech-done.md`
  - 证据：`POST/GET /api/o6/archive/tasks`、`TRASHBOT_O6_CLOUD_ARCHIVE_STATE`、`local_mock_archive`、`real_cloud_db_connected=false`。
- `O6-KR4` local/mock 软件证据：
  - `sprints/2026.06.09_02-03_o6-labeling-api/final.md`
  - 证据：`POST/GET /api/o6/archive/labels`、`local_mock_labeling`、`proof_status=not_proven`。
- `O6-KR5` local/mock 软件证据：
  - `sprints/2026.06.09_03-04_o6-model-inference-api/final.md`
  - 证据：`POST /api/o6/archive/inference`、`model_inference` event、`local_mock_inference`、`real_model_inference_success=false`。

### 现存风险（不在本轮）

- 真实公网隧道（frp/WireGuard/ngrok）、真实 4G、真实 TLS、真实 cloud 生产 DB/queue、真实 OSS、真实 robot 控制均未接通。
- 本轮只产出 local/mock 形状，不产生真实隧道心跳凭据或生产可用性 claim。

## 本轮核心抓手（功能点完整清单）

1. `POST /api/o6/tunnel/heartbeat`  
   - 上报 `robot_id`（必填）、`tunnel_provider`（`frp|wireguard|ngrok|mock`）；
   - `endpoint` 可选，需脱敏后存储/展示；
   - `observed_at` 可选，缺省时以 server 时间；
   - `ttl_seconds` 可选，需校验范围；
   - `metadata` 可选白名单（非敏感字段）。
2. `GET /api/o6/tunnel/robots`  
   - 列出最近状态；
   - 默认按 `last_seen_at_ms` 倒序；
   - 可选支持 `limit`、`status=online|offline|all`（建议设计）。
3. `GET /api/o6/tunnel/robots/<robot_id>`  
   - 读单机 `online/offline`；
   - 不存在时 `404` fail-closed。
4. 在线/离线语义  
   - `online` 当 `now_ms <= last_seen_at_ms + ttl_seconds*1000`；
   - 否则为 `offline`。
5. 固定响应 Schema 与边界字段  
   - `schema="trashbot.o6.tunnel_status.v1"`；
   - `source="local_mock_tunnel_status"`；
   - 必含 `real_tunnel_connected=false`、`real_4g_connected=false`、`connects_cloud_production=false`、`robot_control_executed=false`。
6. 安全红线  
   - 不回显 `Authorization/bearer/token/password/secret/private_key/credential URL`；
   - 不暴露 `/cmd_vel`；
   - 不保存/不回显 endpoint token；
   - body 过滤：限制 `Content-Length`；
   - 不执行任何远程命令和机器人控制动作。
7. 与既有 O6 状态存储兼容  
   - 尽量沿用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 或其测试风格（文件路径与隔离模式）；
   - local/mock store 命名与测试方式应与既有 O6 一致，便于全链路复用 fixture。

## 风险边界与文档同步

- 上位机 SSH（`ssh root@192.168.1.11 -p 37878`）仅写在部署/验证说明，不写死到接口文档、源代码 fixture 或数据库字段；避免将凭据与 endpoint 暴露在非部署上下文。
- 本轮仅更新 sprint 文档，不包含实现文件，也不要求硬件接线、ROS2 主控、WAVE ROVER/UART、串口、模型、手机端代码。
- `sprints/2026.06.09_00-01_o6-local-cloud-archive-mvp/` 仅供历史回溯，不触碰。

## 文件范围

本次可改动（限定）：

- `sprints/2026.06.09_04-05_o6-tunnel-online-status/pre_start.md`
- `sprints/2026.06.09_04-05_o6-tunnel-online-status/prd.md`
- `sprints/2026.06.09_04-05_o6-tunnel-online-status/tech-plan.md`

## 目标验收结果（本轮设计）

主验证命令（后续由实现前/实现后复用）：

```bash
test -f sprints/2026.06.09_04-05_o6-tunnel-online-status/pre_start.md && test -f sprints/2026.06.09_04-05_o6-tunnel-online-status/prd.md && test -f sprints/2026.06.09_04-05_o6-tunnel-online-status/tech-plan.md
```

```bash
rg -n "sprint_type: epic|O6-KR1|/api/o6/tunnel/heartbeat|/api/o6/tunnel/robots|trashbot\\.o6\\.tunnel_status\\.v1|local_mock_tunnel_status|real_tunnel_connected|real_4g_connected|connects_cloud_production|robot_control_executed|now_ms|last_seen_at_ms|offline|online" sprints/2026.06.09_04-05_o6-tunnel-online-status
```
