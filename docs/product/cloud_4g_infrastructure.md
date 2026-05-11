# 4G Cloud Infrastructure Boundary

## 目标

O6 的真实产品目标是让手机通过云端 API 控制小车，小车通过 4G 主动 outbound polling 云端控制面。云端只承载轻量 JSON command/status/ack，不承载图片大对象，不暴露底层机器人控制入口，也不要求手机和小车处于同一 WiFi。

本轮 `2026.05.12_05-06_remote-cloud-service-docker-proof` 只完成 independent Docker/local HTTP relay proof：`remote_cloud_relay.py` 可在本机 Python 或 Docker 容器内独立运行，不依赖 ROS2 runtime 或 `operator_gateway` 进程。该 proof 不等于真实云、真实 4G、HTTPS/TLS、OSS/CDN、Nav2/fixed-route、WAVE ROVER 或 HIL。

## 云端基线规格

目标服务端基线：

- 规格：4C 8G，无 GPU。
- 入口：公网 HTTPS API，后续由网关或反向代理终止 TLS。
- 管理：SSH 仅允许运维来源地址访问，禁止作为产品流量入口。
- 产品流量：手机访问云端 API；机器人只主动访问云端 API。
- 数据面：大对象走 OSS/CDN，云中转节点不做图片和视频大流量中转。

本轮 proof 仅在本机 HTTP 中验证控制面语义，没有申请域名、没有配置 TLS 证书、没有开放公网入口，也没有做云主机防火墙实配。

## 网络方向

正式网络方向：

```text
phone web/app -> cloud HTTPS API
robot remote_bridge -> cloud HTTPS API outbound polling
cloud API -> file/db queue for commands/status/acks
robot snapshots -> OSS object storage
phone diagnostics -> CDN or cloud API references
```

安全边界：

- 不接受公网 inbound 直连小车。
- 不把底层速度控制、硬件参数或调试端口暴露给手机用户。
- 手机端只看到任务命令、机器人状态、ACK 和普通用户可读错误。
- ACK 只表示 robot bridge 已处理 command envelope，不表示真实送达完成。

## 防火墙和端口边界

目标云端防火墙策略：

- 对公网开放：HTTPS 443。
- 可选临时调试：HTTP 80 仅用于证书签发或跳转 HTTPS。
- 运维 SSH：限制来源地址；不与产品 API 共用凭证。
- 数据库、队列、对象存储凭证：不直接暴露公网。

本轮 Docker/local proof 不配置真实防火墙。`remote_cloud_relay.py` 默认建议监听 `127.0.0.1`，用于本机或容器内验证。

## 容量边界

4C 8G 无 GPU 的基线只承担控制面：

- command/status/ack 是小 JSON，适合短轮询或后续升级为 WebSocket/MQTT。
- 单机器人轮询间隔应由机器人侧参数控制，避免低价值高频空轮询。
- file-backed store 只用于单机 proof；生产环境需要数据库或队列来处理并发、一致性、备份和灾备。
- 图片、日志包、视频片段不得通过 relay service 主通道传输。

本轮没有做压测、跨实例一致性、多租户隔离或生产数据库迁移。

## OSS/CDN 目标

大对象目标链路：

- OSS bucket：`bytegallop`
- region：`oss-cn-hangzhou`
- 对象前缀：`rober/<robot_id>/<date>/<task_id>/`
- CDN base URL：`https://cdn.bytegallop.com/rober/`

凭证原则：

- 小车侧使用 STS 临时凭证或受限 AK。
- 主 AK/SK 不直放小车，不写入仓库，不进入 state file。
- CDN 只做公开只读视图入口；私有任务数据走云端 API 网关和 bearer auth。

本轮没有实现 OSS 上传、STS 签发、CDN 回源、图片生命周期回收或真实凭证 rotate。

## 凭证边界

服务端、CI 和上车机器人均通过环境变量或安全配置注入凭证：

- `TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN`：本轮 independent relay proof 的 bearer token。
- `.env` 不入仓库；`.env.example` 只能放占位符。
- 错误响应和 state file 不得包含 bearer token、Authorization header、credential-bearing URL、串口设备、baudrate、WAVE ROVER 参数、底层速度控制入口或 raw ROS topic 名。
- token rotate、账号分级、机器人 provisioning 和审计日志是后续真实云 sprint 的范围。

## 本轮 Docker Proof

本轮新增 independent relay service module：

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-token \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --host 127.0.0.1 \
  --port 8088 \
  --state-path /tmp/trashbot_remote_cloud_relay.json
```

已覆盖 API：

```text
POST /robots/{robot_id}/commands
GET  /robots/{robot_id}/commands/next?last_ack_id=<id>
POST /robots/{robot_id}/status
GET  /robots/{robot_id}/status
POST /robots/{robot_id}/commands/{command_id}/ack
GET  /robots/{robot_id}/commands/{command_id}/ack
```

proof 边界：

- bearer auth：缺 token 或错 token 返回 `auth_failed`。
- command：`id` 作为幂等键，支持 `collect`、`confirm_dropoff`、`cancel`，过期 command 不作为 next 返回。
- status：缺失返回 `status_missing`，过期返回 `status_stale`。
- ACK：终态只允许 `acked`、`failed`、`ignored`。
- persistence：commands/status/acks 写入本地 JSON state file，使用临时文件加 `os.replace` 做原子替换。
- phone-safe errors：覆盖 `auth_failed`、`bad_request`、`not_found`、`status_missing`、`status_stale`、`malformed_json`。

未完成项：

- 真实云部署、域名、公网入口、HTTPS/TLS、防火墙实配。
- 真实 4G/SIM、弱网/断网 carrier 测试。
- 生产数据库、队列、多实例一致性、备份和灾备。
- OSS/CDN 上传、STS、受限 AK、生命周期和 rotate。
- Nav2/fixed-route、WAVE ROVER、真实硬件运动、HIL 和用户实机验收。
