# Sprint 2026.05.12_06-07 Remote Cloud Entry Docker Deploy - Tech Plan

## 状态

- 阶段：tech-plan
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据边界：目标为 `software_proof_docker_deploy`

## 用户价值和产品北极星

技术计划服务于一个产品目标：把 O6 remote cloud relay 从 local Python proof 推进到 Docker deploy proof，让后续真实云入口具备可部署、可检查、可鉴权、可恢复和可对接 robot client 的基础。北极星仍是普通手机用户不懂 ROS2/硬件也能通过云端入口使用小车；本轮只补云控制面入口，不碰正式手机 UI 和 HIL。

## OKR 映射

| Objective/KR | 技术抓手 |
| --- | --- |
| O6 KR1 | 容器化 `trashbot.remote.v1` commands/status/ack relay，保持 outbound polling contract。 |
| O6 KR2 | Docker deploy proof 和文档化云入口边界，支撑未来 4C 8G 公网 HTTPS 迁移。 |
| O6 KR5 | env/`.env.example` 和脱敏检查，确保凭证不入仓库、不进响应或 state file。 |
| O6 KR6 | health/readiness 与 phone-safe failure，支撑网络/服务/鉴权/状态问题区分。 |
| O5 支撑 | readiness/status 为 future phone UI 提供用户可读状态，不声明正式 UI 完成。 |

## 技术方案

### Task A - Docker deploy proof

- Owner：`full-stack-software-engineer`
- 目标：
  - 为 `remote_cloud_relay.py` 增加 Docker 启动入口或 compose 服务定义。
  - 增加 `.env.example` 或等价 env 占位，覆盖 bearer token、state path、host/port、future OSS/CDN/TLS 占位。
  - 明确默认安全监听边界，开发 proof 可本机访问但不默认冒充公网。
- 允许改动范围：
  - `Dockerfile`、`docker/`、`docker-compose*.yml`、`scripts/` 中与 remote cloud relay 启动直接相关的文件。
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - `docs/product/cloud_4g_infrastructure.md`
  - `docs/product/remote_4g_mvp.md`
  - `sprints/2026.05.12_06-07_remote-cloud-entry-docker-deploy/tech-done.md`
  - 必要的 targeted tests/smoke 文件。
- 接口影响：
  - 不改变既有 `trashbot.remote.v1` command/status/ack 路径语义。
  - 不暴露 `/cmd_vel`、ROS topic、串口、baudrate 或 WAVE ROVER 参数。

### Task B - Health/readiness and phone-safe smoke

- Owner：`full-stack-software-engineer`
- 目标：
  - 增加 `/healthz`、`/readyz` 或等价 readiness check。
  - readiness 覆盖服务存活、contract/version、bearer auth configured、state store writable。
  - 错误输出保持 phone-safe，不泄露 credential、硬件参数或 raw traceback。
- 允许改动范围：
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - remote cloud relay 相关 targeted tests。
  - `docs/product/cloud_4g_infrastructure.md`
  - 当前 sprint `tech-done.md`
- 接口影响：
  - 可新增 health/readiness endpoint。
  - 不改变现有 commands/status/ack response shape，除非是向后兼容的可选字段。

### Task C - Robot client compatibility fence

- Owner：`robot-software-engineer`
- 目标：
  - 在容器服务或等价 deploy entry 上验证 `RemoteCloudClient.post_status -> get_next_command -> post_ack`。
  - 保持 auth failed、malformed response、cloud unreachable 的保守语义：不执行不可信 command、不推进 cursor、不伪造 terminal ACK。
- 允许改动范围：
  - `src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 如确有必要，`src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
  - 当前 sprint `tech-done.md`
- 接口影响：
  - 不改 ACK 语义。ACK 仍只代表 command envelope 处理，不代表真实送达结果。

## 执行顺序和 team 分工

1. `full-stack-software-engineer` 先完成 Docker deploy proof 与 readiness。
2. `robot-software-engineer` 在容器入口可用后做 robot client compatibility fence。
3. 如两个任务文件范围互不重叠，可并行；若共享 `remote_cloud_relay.py` 或同一 smoke 脚本，则以 `full-stack-software-engineer` 为主责集成，`robot-software-engineer` 只补 compatibility 事实。
4. `product-okr-owner` 只做验收、边界核对和 sprint 收口，不替 Engineer 写产品代码。

## 验收命令

执行同学必须按“测试只围栏”原则运行 targeted checks，不做宽泛回归矩阵。

### Task A / Task B targeted validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  docs/product/cloud_4g_infrastructure.md \
  docs/product/remote_4g_mvp.md \
  sprints/2026.05.12_06-07_remote-cloud-entry-docker-deploy/tech-done.md
```

### Docker deploy smoke

具体命令由 Engineer 根据实际文件名写入 `tech-done.md`，但必须覆盖：

```text
1. build image or compose build
2. start relay container with env placeholders
3. call health/readiness
4. post status
5. enqueue command
6. robot-style get next command
7. post ack
8. read ack/status back
9. stop container and preserve relevant logs
```

### Task C robot compatibility validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
```

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  sprints/2026.05.12_06-07_remote-cloud-entry-docker-deploy/tech-done.md
```

### Product preflight document validation

```bash
git diff --check -- \
  sprints/2026.05.12_06-07_remote-cloud-entry-docker-deploy/pre_start.md \
  sprints/2026.05.12_06-07_remote-cloud-entry-docker-deploy/prd.md \
  sprints/2026.05.12_06-07_remote-cloud-entry-docker-deploy/tech-plan.md
```

## 验收标准

- Docker deploy proof 可以在本机 Docker 环境复现。
- health/readiness 或等价 smoke 能明确返回服务状态和失败原因。
- command/status/ack contract 在容器入口上通过。
- robot client compatibility 不退化。
- docs/product 已同步 Docker proof 与真实云缺口。
- `tech-done.md` 写清实际改动、命令输出、失败定位和剩余风险。
- 不把本轮结果写成真实云、真实 4G、OSS/CDN、HIL、Nav2/fixed-route 或正式手机 UI 完成。

## 风险和回滚边界

- 若 Docker Desktop、镜像构建或端口占用失败，Engineer 必须记录阻塞，不得只用 host Python smoke 冒充 Docker deploy proof。
- 若 health/readiness 新增接口影响旧 API，必须优先保守回滚接口变更，保留旧 command/status/ack contract。
- 若 env/compose 引入真实密钥或机器本地路径，必须立即移除并重跑 scoped diff/security check。
- 若 tests 变宽或耗时过高，应收缩到 remote cloud relay 和 remote bridge compatibility 围栏。
