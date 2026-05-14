# Sprint 2026.05.15_07-08 Route Task Field Run Evidence Kit - Pre Start

sprint_type: epic

## 1. 启动背景

当前 `OKR.md` 4.1 快照更新时间为 2026-05-15 05:20 Asia/Shanghai，Objective 2、Objective 3、Objective 5 均约 66%，并列最低。最近 `2026.05.15_06-07_route-task-field-run-console` 已完成 `software_proof_docker_route_task_field_run_console_gate`，把 execution pack、route status、task record 和 completion signal 收敛成 field-run 准备台。

本机仍只有 Docker，没有真实 WAVE ROVER、串口、HIL、Nav2/fixed-route 现场运行、真实手机或公网/4G/OSS/CDN/DB/queue 外部材料。Objective 5 的下一步必须依赖真实外部材料，继续堆本地 metadata 不会提高可信完成度。因此本轮转向并列最低且仍可推进的 Objective 2 / Objective 3。

## 2. 本轮目标

把上一轮 field-run console 继续推进为可交给现场同学执行和回填的证据包：生成目录 manifest、采集模板、命令清单、same `evidence_ref` 约束、缺失材料状态和 phone-safe/diagnostics 只读摘要。边界仍是 Docker/local software proof，不声明真实送达、真实路线运行、HIL 或 dropoff/cancel completion。

## 3. Owner

- Product Manager / OKR Owner：维护 PRD、计划、验收和 OKR 收口。
- Autonomy Algorithm Engineer：PC 侧 evidence kit CLI、测试和 `docs/navigation/`。
- Robot Platform Engineer：diagnostics metadata-only consumption 和 `docs/interfaces/`。
- User Touchpoint Full-Stack Engineer：`mobile/web` 只读 evidence kit panel 和 `docs/product/`。

## 4. 验收边界

- 只允许证明 `software_proof_docker_route_task_field_run_evidence_kit_gate`。
- 不允许把 artifact pass、ACK、summary、mobile panel 或 diagnostics 写成 `delivery_success=true`。
- 不允许声明真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、串口/UART、HIL、真实 dropoff/cancel completion、真实手机/browser 或 O5 external proof。

## 5. 重复 blocker 核对

最近两轮 O5 blocker 均指向真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 和 worker/migration 缺失。本轮不消费 O5 blocker；只推进 O2/O3 的现场证据包软件准备层。
