# Sprint 2026.05.13_14-15 OSS/CDN Live Probe Gate - Side2Side Check

## 用户价值和产品北极星

北极星：普通手机用户和部署同学不需要理解 OSS、CDN、preflight、ACK 或 ROS2，也能知道诊断对象链接是否已经具备可被公网/CDN 读取的证据，以及当前为什么仍不能按 production ready 放行。

本轮价值：把“OSS/CDN live traffic 尚未证明”从口头风险推进为可执行、可审计、可被 preflight 和 robot compatibility fence 消费的 live probe gate；在当前 Docker-only 主机上保持 blocked-by-design，避免把本地 artifact shape 写成真实 CDN 可达。

## OKR 映射

- Objective 5 KR3：OSS 写入策略从 manifest shape 推进到 live probe artifact 入口。
- Objective 5 KR4：CDN base URL 的只读视图入口新增 live probe readiness/preflight 解释。
- Objective 5 KR6：OSS/CDN 不可达时的 graceful degradation 具备 phone-safe blocked summary 和 retry hint。

## KR 拆解或更新

- KR3：从“对象前缀和 manifest 可审计”推进到“live probe artifact 可生成并可被 preflight 消费”。
- KR4：从“CDN URL 形态正确”推进到“CDN live probe complete/blocked 状态可被系统解释”。
- KR6：从“不可达风险写在文档里”推进到“`production_ready=false`、`overall_status=blocked`、`live_probe_complete=false` 的 gate 化表达”。

## 本轮核心抓手

1. Full-stack 新增 `trashbot.oss_cdn_live_probe` schema v1、artifact writer、validator、preflight consumption、CLI/env 支持。
2. Robot metadata-only fence 证明 live probe readiness 不触发 backend action、不 POST ACK、不推进 cursor。
3. OKR 只保守上调 Objective 5，不扩大到真实 OSS/CDN live traffic 或 production ready。
4. closeout 统一证据边界为 `software_proof_docker_oss_cdn_live_probe_gate`。

## 需要做什么

本轮已完成：

- Task A：Full-stack 完成 OSS/CDN live probe artifact/preflight/CLI/env 能力和产品文档同步。
- Task B：Robot 完成 remote bridge/protocol metadata-only compatibility fence 和接口文档同步。
- Task C：Product 完成 sprint closeout、OKR 和 process log 收口。

后续需要另开 sprint：

- 使用真实 OSS/CDN 凭证和公网 CDN 回源环境执行 live probe。
- 引入真实云、4G/SIM 或 production DB/queue 外部证据。
- 真实手机设备/browser 对 phone-safe blocked/ready 文案做端到端验收。

## 优先级和验收口径

优先级：P0，Objective 5 启动时是当前最低完成度 Objective，且 OSS/CDN live traffic 是云中转产品化的关键缺口。

验收口径：

- `trashbot.oss_cdn_live_probe` artifact 能生成，并能被 production preflight 消费。
- 无真实 CDN/OSS 外部证据时保持 `production_ready=false`、`overall_status=blocked`、`live_probe_complete=false`。
- metadata-only live probe response 不触发机器人动作、不 POST ACK、不推进或持久化 cursor。
- 文档、OKR 和 sprint closeout 只声明 `software_proof_docker_oss_cdn_live_probe_gate`。

## 对应责任 Engineer

- `full-stack-software-engineer`：remote cloud relay artifact/preflight/CLI/env、cloud relay README、O5 产品文档。
- `robot-software-engineer`：remote bridge/protocol metadata-only fence、`docs/interfaces/ros_contracts.md`。
- `product-okr-owner`：OKR、process log、sprint closeout。

## 风险、阻塞和证据链

已补齐证据链：

- Full-stack relay unittest：`Ran 64 tests in 7.096s OK`。
- Full-stack relay `py_compile`：OK。
- Full-stack scoped diff check：OK。
- Robot remote bridge/protocol unittest：`Ran 88 tests in 44.322s OK`。
- Robot test files `py_compile`：exit 0。
- Robot scoped diff check：exit 0。

仍未补齐：

- 真实 OSS/CDN live traffic。
- 真实云。
- 真实 4G/SIM。
- production DB/queue。
- 真实手机设备/browser。
- Nav2/fixed-route。
- WAVE ROVER。
- HIL。
- 真实送达。

## 需要创建或更新的 sprint 文档

本轮需要并已创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

本轮需要并已更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`
