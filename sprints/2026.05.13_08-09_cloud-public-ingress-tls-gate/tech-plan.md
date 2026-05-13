# Sprint 2026.05.13_08-09 Cloud Public Ingress TLS Gate - Tech Plan

## 目标

建立 `software_proof_docker_cloud_public_ingress_tls_gate`：新增或验证 phone-safe 的公网入口/TLS/反向代理配置 artifact，使 deployment readiness / preflight 能区分"有配置包但未实证"和"完全缺配置"，同时保持 `production_ready=false`、`overall_status=blocked`。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低且可推进 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 59%。
2. 本 sprint 直接针对 Objective 5。选择理由是 `sprints/2026.05.13_07-08_mobile-operation-log-gate/final.md` 已将 Objective 4 上调到约 60%，并建议若 O5 低于 O4，则切回云链路。
3. Objective 5 的主要缺口仍是：真实云、真实 HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性、production disaster recovery、real phone app/device、HIL、Nav2/fixed-route、WAVE ROVER 或 real delivery。
4. 不选择 Objective 1：O1 约 75%，主要缺真实 WAVE ROVER `hil_pass`、真实串口日志、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 实机样本；当前本机无真实硬件。
5. 不选择 Objective 2：O2 约 77%，主要缺真实 Nav2/fixed-route 运行、同一 `evidence_ref` 任务复盘、真实送达和失败恢复实测；当前 Docker-only 无法证明真实任务闭环。
6. 不选择 Objective 3：O3 约 77%，主要缺真实路线采集、Nav2 waypoint/fixed-route 实跑、关键帧实景证据与上车复账。
7. 不选择 Objective 4：O4 约 60%，刚完成 `software_proof_docker_mobile_operation_log_gate`；当前低于它的是 O5。
8. Docker-only 边界：本 sprint 只能声明 Docker/local software proof。不得声明真实 HTTPS/TLS、公网入口、真实云、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性、production disaster recovery、真实手机设备/browser、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 技术方案

### Full-stack cloud readiness 方案

- 在 cloud relay runtime 增加 public ingress/TLS gate artifact 生成或现有 deployment readiness 子结构。
- artifact 字段只描述配置状态和证据边界，例如 `schema`、`schema_version`、`evidence_boundary`、`production_ready`、`overall_status`、`ingress_config_present`、`tls_config_present`、`reverse_proxy_config_present`、`external_probe_proven=false`、`not_proven`、`safe_summary`、`retry_hint`。
- preflight / deployment readiness 消费该 artifact 后区分两类状态：
  - `missing_public_ingress_tls_config`：完全缺配置。
  - `public_ingress_tls_config_present_not_externally_proven`：配置包存在，但没有真实外部 HTTPS/TLS、公网入口、DNS、反向代理、防火墙实证。
- Docker/local smoke 或 CLI drill 必须证明两种路径都保持 `production_ready=false`、`overall_status=blocked`。
- 输出不得包含真实 URL、credential-bearing URL、Authorization header、bearer token、证书私钥、root password、OSS AK/SK、DB/queue URL、本地 state path、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。
- 文档同步 `cloud-relay/README.md`、`docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`，明确该 gate 只补 deployment readiness，不证明真实公网/TLS。

### Robot compatibility 方案

- 在 remote bridge / protocol 测试中增加 public ingress/TLS readiness metadata-only response。
- 验证 metadata-only response 不触发 backend action。
- 验证不 POST ACK。
- 验证不推进或持久化 cursor。
- 验证 protocol normalization 剥离 command envelope 外 public ingress/TLS metadata。
- 文档中明确该 metadata 属于 deployment readiness / phone-safe support summary，不属于 `trashbot.remote.v1` action 语义。

## 并行 owner 拆分

### Task A：full-stack-software-engineer

文件范围：

- `cloud-relay/`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`

实现要求：

- 增加 `software_proof_docker_cloud_public_ingress_tls_gate` artifact 或 deployment readiness 子 gate。
- 覆盖配置缺失和配置存在但未实证两种路径。
- 保持 `production_ready=false`、`overall_status=blocked`。
- 不引入真实云部署、真实证书签发、真实域名解析或外部公网 probe。
- 更新 cloud-relay README 和产品文档，写清 TLS / 反向代理下一步的证据边界。
- 保持中文技术注释比例要求，复杂逻辑注释解释为什么 fail closed。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
git diff --check -- cloud-relay onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md
```

预期结果：

- targeted unittest 输出 `OK`。
- `py_compile` 无输出。
- Docker smoke 或 CLI drill 输出 artifact evidence boundary：`software_proof_docker_cloud_public_ingress_tls_gate`。
- 配置缺失与配置存在但未实证都保持 blocked，不出现 `production_ready=true`。

### Task B：robot-software-engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 增加 cloud public ingress/TLS metadata-only compatibility fence。
- 覆盖不触发 action、不 POST ACK、不推进 cursor、不持久化 cursor。
- 覆盖 protocol normalization 剥离 command envelope 外 metadata。
- 更新接口文档，明确 public ingress/TLS readiness metadata 不改变 command/status/ack envelope。
- 保持 ACK 只是 accepted/processing evidence，不是 delivery success。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

预期结果：

- targeted unittest 输出 `OK`。
- `py_compile` 无输出。
- scoped `git diff --check` 无输出。
- metadata-only fence 证明 public ingress/TLS readiness 不产生 robot side effect。

### Task C：product-okr-owner closeout

文件范围：

- `sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/tech-done.md`
- `sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/side2side_check.md`
- `sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

收口要求：

- 汇总 Task A 和 Task B 实际改动与验证输出。
- 检查所有引用文档路径真实存在。
- 保守更新 Objective 5 进度；Objective 1/2/3/4 除非有新证据不调整。
- 明确 evidence boundary：`software_proof_docker_cloud_public_ingress_tls_gate`。
- 明确不声明真实 HTTPS/TLS、公网入口、真实云、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性、production disaster recovery、真实手机设备/browser、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

验收命令：

```bash
test -f docs/product/cloud_4g_infrastructure.md && test -f docs/product/remote_4g_mvp.md && test -f docs/interfaces/ros_contracts.md && test -f docs/process/okr_progress_log.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate
```

## 接口影响

- 可新增 deployment readiness / public ingress TLS artifact schema 或现有 readiness artifact 的向后兼容子字段。
- 不改变 `trashbot.remote.v1` command/status/ack envelope。
- 不改变 `/cmd_vel`、ROS2 topic、hardware launch 参数或 robot action 语义。
- phone-safe summary 可以新增脱敏字段，但字段值不得包含 raw URL、credential-bearing URL、token、证书私钥、本地路径、ROS topic、串口或 WAVE ROVER 参数。

## 安全与隐私边界

public ingress/TLS artifact、preflight 输出和 phone-safe summary 不得包含：

- bearer token、Authorization header、OSS AK/SK、root password。
- TLS private key、证书私钥路径、credential-bearing URL。
- DB URL、queue URL、production secret、raw state path。
- raw base URL 或完整 external probe URL。
- local filesystem path、traceback、checksum、完整 artifact。
- raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数。
- 可被误读为真实 HTTPS/TLS、公网入口、真实云/4G、OSS/CDN live traffic、production ready、HIL 或真实送达的文案。

## 验证计划

后续执行阶段必须至少运行围栏验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
git diff --check -- cloud-relay onboard/src/ros2_trashbot_behavior docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/interfaces/ros_contracts.md
```

本 planning 阶段验收命令：

```bash
test -f sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/pre_start.md && test -f sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/prd.md && test -f sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/tech-plan.md
```

## 风险与回滚

- 如果 full-stack gate 只能证明配置包存在，Product closeout 不得把它写成真实 TLS 或公网入口；必须保持 `production_ready=false`、`overall_status=blocked`。
- 如果 Docker smoke 因配置存在误报 ready，Task A 必须先修 fail-closed 逻辑，再谈 OKR 进度。
- 如果 robot fence 发现 metadata 进入 action path，Task B 必须收紧 normalization 或 test expectation，不能用文档解释绕过。
- 如果 validation 只能证明 local CLI / Docker path，Objective 5 只能按软件证明小幅推进，真实云/4G/OSS/CDN/DB/queue 仍留作后续。
- 回滚方式是移除 public ingress/TLS gate 增量和对应 docs 增量；不得回滚无关 sprint 或其他 worker 改动。
