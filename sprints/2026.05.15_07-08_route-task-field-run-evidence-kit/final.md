# Sprint 2026.05.15_07-08 Route Task Field Run Evidence Kit - Final

sprint_type: epic

## 1. 用户价值和产品北极星

本轮把上一轮 field-run console 继续推进为现场证据包。现场同学可以按同一 `evidence_ref` 查看需要准备的材料目录、采集模板、重跑命令、缺失材料和 operator handoff，不再从多个 JSON/日志手动拼接下一次真实路线-任务联跑需要的证据。

北极星仍是：普通手机用户交付垃圾后，小车可验证地沿固定路线完成投递，而不是只靠 artifact 或 happy path 叙事声称完成。

## 2. OKR 映射与 KR 拆解

- Objective 2：推进 KR4/KR5。Evidence kit 把任务状态、dropoff/cancel 材料、失败/恢复原因、operator next steps 和 completion 缺口转成现场补证清单。
- Objective 3：推进 KR2/KR3/KR5。Evidence kit 把 route status/replay、execution pack、task record、completion signal、console summary 和未来现场回填材料统一到 same `evidence_ref`。
- Objective 5：本轮不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 外部材料。

## 3. 本轮核心抓手

核心抓手是 `software_proof_docker_route_task_field_run_evidence_kit_gate`：把 PC artifact、Robot diagnostics 和 mobile read-only panel 统一到“现场证据包准备完成但未证明实跑”的口径，并强制 `primary_actions_enabled=false`、`delivery_success=false`。

## 4. 实际交付

- Autonomy：新增 route/task field-run evidence kit CLI 与测试，输出 schema、boundary、material directory manifest、capture templates、commands、missing materials、operator handoff 和 readonly summaries。
- Robot：diagnostics metadata-only 消费 evidence kit / summary，支持 explicit ref 与环境变量来源，校验 schema/boundary，保持 fail-closed。
- Full-stack：`mobile/web` 新增只读“路线现场证据包” panel，不改变 Start/Confirm/Cancel gating。
- Product：完成 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` 收口。

## 5. 验收口径与责任 Engineer

- Autonomy Algorithm Engineer：PC 侧 artifact 与测试通过。
- Robot Platform Engineer：diagnostics metadata-only consumption 与测试通过。
- User Touchpoint Full-Stack Engineer：mobile read-only panel、fixture、entrypoint test 与 syntax check 通过。
- Product Manager / OKR Owner：OKR 快照、进度日志和 sprint closeout 与证据边界一致。

## 6. OKR 收口

- Objective 1：保持约 73%。本轮未改硬件、WAVE ROVER、UART、Orange Pi、launch 参数或 HIL 证据。
- Objective 2：约 66% -> 约 67%。理由是 evidence kit 已把现场任务材料、dropoff/cancel 缺口和 operator next steps 组织成下一次真实联跑可执行证据包。
- Objective 3：约 66% -> 约 67%。理由是 fixed-route / task material chain 从 field-run console 继续推进到 same `evidence_ref` 证据包、diagnostics summary 和 mobile read-only panel。
- Objective 4：保持约 73%。本轮只增加只读面板，不计真实手机/browser、production app 或 PWA prompt/user choice。
- Objective 5：保持约 66%。没有真实外部云/4G/OSS/CDN/DB/queue 材料，不能因本地 software proof 上调。

## 7. 风险、阻塞和证据缺口

- 仍缺真实 Nav2/fixed-route 运行、真实路线采集、WAVE ROVER、真实串口/UART、HIL、同一 `evidence_ref` 上车实机复账、真实 dropoff/cancel completion、真实送达和 delivery success。
- 仍缺真实手机设备/browser、production app、真实 PWA prompt/user choice。
- 仍缺 Objective 5 的真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration 和外部探针证据。
- 本轮 evidence kit 是 software proof，不是现场实跑、HIL 或真实送达。

## 8. 下一步

当前数值最低 Objective 是 Objective 5（约 66%），但只有拿到真实外部材料时才应继续提升 O5。若外部材料仍不可用，最高可行动作是沿 O2/O3 把本轮 evidence kit 用于真实 Nav2/fixed-route 或上车实机复账，补齐同一 `evidence_ref` 的现场材料。
