# Sprint 2026.05.15_03-04 Route Task Field Run Execution Pack - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

现场人员现在已经能看到 route/task field-run review console，但还缺一份“照着跑就能采到下一轮材料”的执行包。本轮 PRD 要求把复核结论转成执行 manifest、材料模板、命令清单、重跑清单和 phone-safe summary，让现场联跑从“读懂问题”进入“按同一 `evidence_ref` 采集材料”。

产品北极星仍是低成本 ROS2 垃圾投递机器人完成可验证的送达闭环。本轮不是送达闭环完成，而是为 Objective 2 / Objective 3 的真实 route/task field run 补齐执行准备层。

## 2. OKR 映射

- Objective 2：推进 KR5“每次任务产出可复盘记录”。本轮要求执行包明确 task record、robot-side task evidence、dropoff/cancel completion、失败原因和 delivery success 的材料边界。
- Objective 3：推进 KR2/KR3/KR5“固定路线流程、dry-run/实跑边界、PC 调试与复核展示”。本轮要求执行包列出 route status、Nav2/fixed-route runtime log、真实路线采集和同一 `evidence_ref` 复账要求。
- Objective 5：本轮不推进。O5 仍需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration 材料；Docker/local execution pack 不能替代。

## 3. KR 拆解或更新

本轮不修改 `OKR.md`，只为实现阶段定义可验收 KR 子项：

1. KR2/O2-O3 执行包 manifest：输出 schema `trashbot.route_task_field_run_execution_pack.v1`，boundary `software_proof_docker_route_task_field_run_execution_pack_gate`。
2. KR2/O3 材料模板：列出 route status、Nav2/fixed-route runtime log、真实路线采集说明、PC review console 和 execution bundle 输入要求。
3. KR5/O2 任务材料模板：列出 task record、robot-side task evidence、dropoff/cancel completion、失败恢复、delivery success 的 required/not_proven 字段。
4. KR5/O2-O3 同一 `evidence_ref` 要求：manifest 必须让同一 run 的所有材料共享同一 `evidence_ref`，缺失或不一致时输出 blocked/not_proven。
5. KR5/O2-O3 命令清单：输出 first-run commands、rerun commands、commands_to_rerun 和 operator_next_steps，支持现场人员重跑。
6. KR4/O4 支援面：输出 phone-safe summary，仅用于 diagnostics/mobile 只读展示，不改变 Start/Confirm/Cancel gating。

## 4. 本轮核心抓手

交付 `software_proof_docker_route_task_field_run_execution_pack_gate`，把 review console 的 operator next steps 转成现场执行包：

- manifest：统一 execution pack 顶层状态、schema、evidence boundary、source review ref、same evidence ref requirement。
- materials templates：明确每类材料的文件名建议、必须字段、缺失时的 blocked reason。
- command list：给出生成/复核/重跑所需命令，避免现场人员从 sprint 文档里拼命令。
- phone-safe summary：只保留 safe evidence ref、材料状态、命令摘要、not_proven 和 support copy。
- not_proven：固定包含真实 Nav2/fixed-route、真实路线采集、HIL、dropoff/cancel completion、delivery success、Objective 5 external proof。

## 5. 需要做什么

1. 新增 PC/evidence CLI，读取上一轮 review console，生成 execution pack manifest。
2. 新增 sample/material template drill，证明 manifest 能在 Docker/local 环境输出 ready/blocked 两类状态。
3. diagnostics metadata-only 消费 execution pack summary，并保持动作、ACK、cursor、HIL、delivery success 隔离。
4. mobile/web 增加只读“路线任务现场执行包” summary，不读取 raw artifact、不暴露路径/凭证/ROS/hardware 细节。
5. 更新 `docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 和 sprint closeout 文档。

## 6. 优先级和验收口径

P0：

- manifest、materials templates、commands、rerun commands 和 phone-safe summary 均可从 CLI 输出。
- 同一 `evidence_ref` 是强约束；不一致或缺失时不能输出 ready。
- `not_proven` 和 `delivery_success=false` 必须出现在 artifact、diagnostics、mobile 和 closeout 中。
- diagnostics/mobile 均 metadata-only/read-only，不触发 Start/Confirm/Cancel、collect/dropoff/cancel、ACK、cursor 或 HIL。

P1：

- 文档把现场执行顺序、材料模板和重跑清单写清楚。
- mobile 文案中文优先，避免 raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、路径、checksum、traceback、凭证或 Objective 5 external proof 泄漏。

验收口径：

- 通过 targeted py_compile、targeted unittest/sample drill、required `rg` 和 scoped `git diff --check`。
- 不跑真实硬件、不宣称 HIL、不宣称 delivery success。

## 7. 对应责任 Engineer

- `autonomy-engineer`：execution pack CLI、sample drill、PC/tool 文档和 navigation 文档。
- `robot-software-engineer`：diagnostics metadata-only summary、接口文档和隔离测试。
- `full-stack-software-engineer`：mobile/web 只读面板、fixture、entrypoint 测试和产品文档。
- `product-okr-owner`：收口文档、OKR 口径和证据边界。
- `hardware-engineer`：本轮不主责；若后续执行阶段触及 WAVE ROVER、UART、串口、波特率、引脚、电压或机械安装，必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向资料。

## 8. 风险、阻塞和证据链

- 当前主机没有真实硬件，只有 Docker/local 软件环境；本轮只能形成 software proof。
- execution pack ready 只表示现场执行材料准备充分，不等于真实 Nav2/fixed-route 实跑。
- phone-safe summary 只用于支持人员和用户触点理解下一步，不是控制授权。
- Objective 5 不因本轮上调，除非后续拿到真实外部云/4G/OSS/CDN/DB/queue 材料。
- 真实 delivery success 必须来自真实路线任务完成、dropoff/cancel completion 和同一 `evidence_ref` 上车复账，不能由 manifest、review decision、diagnostics summary 或 mobile panel 推导。

## 9. 需要创建或更新的 sprint 文档

本阶段创建：

- `sprints/2026.05.15_03-04_route-task-field-run-execution-pack/pre_start.md`
- `sprints/2026.05.15_03-04_route-task-field-run-execution-pack/prd.md`
- `sprints/2026.05.15_03-04_route-task-field-run-execution-pack/tech-plan.md`

实现后必须继续创建或更新：

- `sprints/2026.05.15_03-04_route-task-field-run-execution-pack/tech-done.md`
- `sprints/2026.05.15_03-04_route-task-field-run-execution-pack/side2side_check.md`
- `sprints/2026.05.15_03-04_route-task-field-run-execution-pack/final.md`
