# Sprint 2026.05.13_06-07 Cloud External Probe Bundle Gate - Pre Start

## Sprint 类型

- sprint_type: epic
- 本轮目标：推进 Objective 5 云中转 + OSS/CDN 数据通路产品化，在 Docker-only 条件下新增 `software_proof_docker_cloud_external_probe_bundle_gate`。
- 本轮不修改 `OKR.md`，工程实现和 closeout 后再由 Product Owner 汇总更新 OKR 进展。

## 开工证据

- `OKR.md` 4.1 更新时间为 2026-05-13 05:11 Asia/Shanghai：Objective 5 当前约 57%，低于 Objective 4 约 58%；O1/O2/O3 虽约 75%/77%/77%，但当前主机没有真实 WAVE ROVER、真实串口、HIL、Nav2/fixed-route 或真实送达证据。
- `sprints/2026.05.13_05-06_mobile-task-start-confirmation-gate/final.md` 只完成 Objective 4 的 `software_proof_docker_mobile_task_start_confirmation_gate`，并明确 Objective 5 不调整。
- `sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/final.md` 已完成 `software_proof_docker_cloud_deployment_readiness_gate`，但剩余缺口仍是真实云、真实 HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性和 production disaster recovery。
- `cloud-relay/README.md` 当前路线图把 TLS / 反向代理、生产 DB、多实例一致性、灾备、真实 4G、真实公网、真实 OSS/CDN、监控和告警列为后续工作；现有 `/healthz`、`/readyz`、`/preflightz` 和 deployment readiness artifact 仍是 Docker/local software proof。

## 用户价值和产品北极星

用户价值：未来把云中转服务部署到真实公网 URL 前，团队需要一份可复用、phone-safe、preflight-safe 的外部探测 bundle，能用同一口径判断 `/healthz`、`/readyz`、`/preflightz` 对手机入口是否安全、对部署前检查是否可读、对生产风险是否诚实暴露。

产品北极星：普通手机用户不需要理解公网、TLS、队列、OSS/CDN 或 ROS2；产品和工程团队必须先把外部探测结果收敛为可审计 artifact，避免把本地 Docker 证明包装成真实云可用。

## OKR 映射

- Objective 5 KR1：云中转服务端最小契约增加外部探测口径，围绕 HTTP health/readiness/preflight 的 phone-safe JSON 摘要建立可复用证据。
- Objective 5 KR2：部署基线继续围绕公网入口、HTTPS/TLS、防火墙和运维边界暴露缺口，但本轮只证明 local probe contract。
- Objective 5 KR5：凭证与敏感信息继续不得泄漏到 artifact、phone-safe summary、preflight summary 或日志。
- Objective 5 KR6：外部探测摘要必须区分网络/部署问题与机器人问题，失败时给出 graceful degradation 与 retry hint。
- Objective 2 guardrail：robot bridge 侧必须证明 `cloud_external_probe` / deployment metadata-only response 不触发 robot action、不 POST ACK、不推进 cursor。

## 本轮核心抓手

新增 `software_proof_docker_cloud_external_probe_bundle_gate`：

- Full-stack 方向：在 cloud relay 侧定义 external probe artifact/CLI/preflight 消费/Docker smoke fence，面向未来真实公网 URL，但本轮只运行本地 Docker/local URL。
- Robot 方向：在 `remote_bridge` / protocol compatibility fence 中确认 external probe 和 deployment metadata 只作为 metadata，不进入 command action、不生成 ACK、不推进 cursor。
- Product 方向：本文件、`prd.md`、`tech-plan.md` 先明确范围、证据边界、并行 owner、验收命令和 closeout 口径。

## Owner 与并行策略

- full-stack-software-engineer：负责 `cloud-relay/`、`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`、`onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`、`.env.example`、相关产品文档。
- robot-software-engineer：负责 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`、`remote_bridge_protocol.py`、`test_remote_bridge.py`、`test_remote_bridge_protocol.py`、`docs/interfaces/ros_contracts.md` 或相关 robot contract 文档。
- 并行方式：两个 owner 文件范围不重叠，工程实现阶段必须并行启动两个 worker；Product Owner 不写工程代码。

## 风险、阻塞和证据边界

- 当前没有真实云主机、真实 HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、真实手机设备、HIL、Nav2/fixed-route、WAVE ROVER 或 real delivery。
- 本轮 artifact 必须保持 `production_ready=false`，不得把本地 Docker/local probe 推断为生产可用。
- `/preflightz` 可以返回 blocked；blocked 是正确证据，不是工程失败，前提是缺口和 retry hint 清晰、敏感信息已脱敏。
- ACK 语义仍是 accepted/processing evidence，不能解释为 delivery success。

## 需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程实现后必须继续创建或更新：`tech-done.md`、`side2side_check.md`、`final.md`。
- closeout 时再更新：`OKR.md` 4.1 和 `docs/process/okr_progress_log.md`，并同步相关 `docs/` 产品/接口文档。
