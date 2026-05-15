# Sprint 2026.05.16_01-02 Elevator Evidence Driven Mainline - Pre Start

sprint_type: epic

## 1. 启动依据

- `OKR.md` 4.1 当前最低 Objective 是 Objective 5，约 66%；但 `OKR.md` 第 6 节明确要求：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料时，不继续叠本地 O5 metadata gate。
- 本机环境仍是 Docker-only，没有真实硬件、真实串口、真实电梯、真实手机设备或真实外部云材料；本轮不得声明 HIL、真实送达或 O5 external proof。
- 最近 PR 证据：
  - GitHub PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 于 2026-05-14 合并，主题是把跨楼层/电梯 assisted delivery 变成 required MVP capability，并固化 sensing/hardware baseline 与 evidence requirements。
  - GitHub PR #4 `Add elevator-assisted delivery capability to agents, registry and OKR` 于 2026-05-14 合并，明确把 elevator state 和 evidence chain 写入 agent/OKR；测试只覆盖配置/文档，没有 runtime integration test。
- 最近 sprint 证据：`2026.05.15_13-14_elevator-field-rehearsal-execution-pack` 已把现场复核材料整理成 execution pack，但 final.md 仍列出真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime、同一 `evidence_ref` task record/completion signal 等缺口。

## 2. 本轮目标

把电梯 assisted delivery 从“固定 dry-run 阶段 + execution pack 材料”推进到“行为主链路可消费同一 `evidence_ref` 的 rehearsal evidence artifact”。

本轮只形成 `software_proof_docker_elevator_evidence_driven_mainline_gate`：

- Autonomy 提供/校验电梯 rehearsal evidence artifact shape。
- Robot `task_orchestrator` 在 dry-run 模式下只读该 artifact，驱动电梯阶段、失败原因、manual takeover、speaker prompt 和 task record。
- Full-stack `mobile/web` 只读展示 evidence-driven elevator assist summary，不启用 Start/Confirm/Cancel，也不把 ACK 或 artifact 当 delivery success。

## 3. Owner

- 主责：Robot Platform Engineer，负责行为主链路和 task record。
- 并行：Autonomy Algorithm Engineer，负责 evidence artifact CLI/schema/docs。
- 并行：User Touchpoint Full-Stack Engineer，负责手机只读展示和 copy fence。
- Product Manager / OKR Owner 在工程任务返回后做 closeout、OKR 与进度记录。

## 4. 主要风险

- 没有真实硬件和真实电梯，本轮只能证明 Docker/local software proof。
- Robot 与 Autonomy 共享新 artifact contract，必须按 `tech-plan.md` 固定字段实现，避免并行漂移。
- 任何 success phrasing、`delivery_success=true`、`primary_actions_enabled=true`、raw ROS topic、serial/UART、WAVE ROVER、credential 或本地 raw path 都必须 fail closed 或被 phone-safe copy 过滤。

