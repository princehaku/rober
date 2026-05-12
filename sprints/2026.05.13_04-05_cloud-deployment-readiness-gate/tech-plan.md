# Sprint 2026.05.13_04-05 Cloud Deployment Readiness Gate - Tech Plan

## Sprint Type

- sprint_type: epic
- Execution model: two parallel engineering workers after this plan is complete, then product closeout.
- Evidence boundary target: `software_proof_docker_cloud_deployment_readiness_gate`
- Product rule: 本计划不更新 OKR 数字；最终 `final.md` 根据 worker 证据再保守评估。

## OKR 最低优先级核对

当前 `OKR.md` 4.1 按数字排序的最低 Objective 是：

- Objective 5：云中转 + OSS/CDN 数据通路产品化，当前约 55%。

相邻 Objective：

- Objective 4：手机用户体验与低成本量产边界，当前约 56%。
- Objective 1/2/3 当前约 75%/77%/77%，但本机没有真实硬件，真实 WAVE ROVER、串口、HIL、Nav2/fixed-route 和送达闭环仍不可在本轮直接证明。

本 sprint 正针对最低 Objective 5。选择理由基于 live 证据：

- 03-04 已将 Objective 4 从约 54% 推进到约 56%，Objective 5 保持约 55%。
- 02-03 已完成 `cloud-relay/` self-contained runtime，但 final 明确建议继续真实云前置链路：生产环境配置审计、部署凭证占位校验、TLS/域名/healthcheck runbook 或云端队列替身到真实服务切换计划。
- 当前主机仍只有 Docker，没有真实云、真实 4G/SIM 或真实硬件；因此本轮只能做 deployment readiness gate，不能做真实云验收。

## 技术方案

### 1. Full-stack worker: cloud deployment readiness gate

目标：在 `cloud-relay/` 和对应产品文档中实现/文档化 deployment readiness artifact、preflight、CLI/Docker smoke 和 env 占位。

允许改动文件范围：

- `cloud-relay/`
- `.env.example`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- Worker 自行新增的最小 cloud-relay 测试或 smoke helper，路径应在 `cloud-relay/` 或既有 cloud relay 测试目录内
- 本 sprint 文档中的 worker 结果段（实现后由收口补入 `tech-done.md`）

实现要求：

- 复用现有 `ros2_trashbot_cloud_relay.remote_cloud_relay` 和 `remote_cloud_relay.py` proof ladder，不复制第二套 `trashbot.remote.v1` 语义。
- 新增或扩展 deployment readiness artifact，schema 命名建议使用 `trashbot.cloud_deployment_readiness`，schema_version 从 `1` 开始。
- Artifact / preflight 输出必须包含 `evidence_boundary=software_proof_docker_cloud_deployment_readiness_gate`、`production_ready=false`、`overall_status=blocked` 或等价 blocked/warning、`not_proven`、`safe_summary`、`retry_hint`。
- 检查项至少覆盖：public base URL/TLS/public ingress、healthcheck endpoint、bearer secret 占位、state backend、production DB/queue gap、OSS/CDN gap、4G/SIM gap、deployment runbook or smoke command presence。
- `.env.example` 只能新增 placeholder，不得写入真实 token、OSS AK/SK、root password、DB URL、queue URL 或 credential-bearing URL。
- Docker smoke 或 CLI smoke 必须断言本地占位配置不会得到 `production_ready=true`。
- Phone-safe / preflight 输出不得泄漏 bearer token、Authorization header、OSS secret、AK/SK、root password、DB URL、queue URL、credential-bearing URL、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic、`/cmd_vel` 或 traceback。
- 更新 `cloud-relay/README.md`、`docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`，明确运行方式、证据边界和非证明项。
- 代码技术注释使用中文，并解释为什么要保持 blocked-by-design 与脱敏边界。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest <targeted-cloud-relay-tests>
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
```

```bash
# 若 Docker 不可用，必须改用等价 CLI smoke，并在输出中说明 Docker block：
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

```bash
git diff --check -- <full-stack-touched-files>
```

输出必须包含：

1. 实际改动文件列表。
2. 上述验收命令输出摘要。
3. 若 Docker smoke 失败，给出根因定位；只有环境不可用时才允许用 CLI smoke 替代。
4. 剩余风险，尤其是真实云/HTTPS/TLS/4G/DB/queue/OSS-CDN/HIL 未证明项。

### 2. Robot worker: deployment metadata compatibility fence

目标：在 remote bridge compatibility fence 中验证 deployment-readiness metadata-only response 不触发 robot action、不 ACK、不推进/持久化 cursor、不改变 `trashbot.remote.v1` envelope。

允许改动文件范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`（仅当需要补 protocol fence）
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`（仅当测试暴露兼容缺口）
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`（仅当测试暴露兼容缺口）
- `docs/product/remote_4g_mvp.md`（仅当需要补 robot-side contract 文档）
- 本 sprint 文档中的 worker 结果段（实现后由收口补入 `tech-done.md`）

实现要求：

- 首选只加 compatibility fence；若现有生产代码已满足，不要为了形式修改 runtime。
- 构造 deployment-readiness metadata-only cloud response，例如包含 `deployment_readiness`、`cloud_deployment_readiness`、`preflight`、`production_ready=false`、`evidence_boundary=software_proof_docker_cloud_deployment_readiness_gate`，但不包含可执行 command。
- 断言：
  - `FakeOperatorBackend.calls == []`。
  - `cloud.ack_posts == []`。
  - `worker.last_ack_id` 保持原值。
  - `cursor_state_path` 不被创建或不被改写。
  - 返回/状态中不出现 `delivery_success`、`/cmd_vel`、raw credential 字段。
  - 既有 `trashbot.remote.v1` command/status/ack envelope 测试仍通过。
- 如需修改生产代码，必须保持 unknown metadata fail-closed，且不得影响正常 collect/dropoff/cancel command。
- 代码技术注释使用中文，并解释 deployment metadata 为什么只能作为诊断元数据。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
```

```bash
git diff --check -- <robot-touched-files>
```

输出必须包含：

1. 实际改动文件列表。
2. 上述验收命令输出摘要。
3. 若无需生产代码修改，明确说明测试围栏证明了什么。
4. 剩余风险，尤其是真实云/4G/HIL/真实送达未证明项。

### 3. Product owner: closeout after implementation

目标：实现完成后收口 Objective 5 进度、证据边界和 sprint 链路。

允许改动文件范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/tech-done.md`
- `sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/side2side_check.md`
- `sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/final.md`

收口要求：

- 汇总 full-stack 与 robot worker 的实际改动和验证输出。
- `OKR.md` 只按实际 software proof 保守更新，不得写成真实云、真实 HTTPS/TLS、真实 4G/SIM、真实 OSS/CDN、生产 DB/queue、HIL 或真实送达。
- `docs/process/okr_progress_log.md` 写清本轮证据边界、非证明项、下一步真实外部证据缺口。
- `side2side_check.md` 必须核对 PRD 验收口径、证据边界、非证明项、worker 输出和 docs 同步。
- `final.md` 必须记录是否 commit/push、未完成事项和下一步建议。

Product 收口验证命令：

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/tech-done.md sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/side2side_check.md sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/final.md
```

## 并行启动要求

本 sprint 是 2 owner 工程 Epic，文件范围互不重叠，必须并行启动两个 worker：

- `full-stack-software-engineer` 负责 `cloud-relay/`、`.env.example` 和云产品文档。
- `robot-software-engineer` 负责 remote bridge compatibility fence。

`product-okr-owner` 不在实现阶段改产品代码或测试代码；只在 worker 完成后收口 OKR、progress log 和 sprint closeout 文档。

## 接口影响

- 不改变 `trashbot.remote.v1` commands/status/ack envelope。
- 不改变 ROS2 action/service/topic contract。
- 不新增硬件、UART、WAVE ROVER、Orange Pi、机械或电气假设。
- 新增 readiness artifact / metadata 只能作为云部署诊断元数据，不得进入 robot action decision。

## 风险边界

- 本轮成功也只能支持 `software_proof_docker_cloud_deployment_readiness_gate`。
- 不证明真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN 实流量、生产 DB/queue、多实例一致性、生产灾备、正式手机 app、真实手机设备/浏览器、Nav2/fixed-route、WAVE ROVER、HIL 或 delivery success。
- 如果 preflight 输出泄漏 secret、Docker smoke 把 placeholder 配置判成 ready、或 robot fence 发现 metadata 触发 action/ACK/cursor，必须阻断收口并要求对应 worker 修复。

## Product 计划任务只读检查

本 Product 计划任务只运行 sprint 文档 diff check：

```bash
git diff --check -- sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/pre_start.md sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/prd.md sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/tech-plan.md
```
