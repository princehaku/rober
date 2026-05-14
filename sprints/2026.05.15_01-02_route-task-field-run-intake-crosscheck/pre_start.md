# Sprint 2026.05.15_01-02 Route Task Field Run Intake Crosscheck - Pre Start

sprint_type: epic

## 1. 开工判定

- 本轮目标：创建 `route_task_field_run_intake` / crosscheck 软件能力，把上一轮 `software_proof_docker_route_task_field_run_readiness_gate` 从“准备材料清单”推进到“接收并校验同一 `evidence_ref` 下的现场材料”。
- 目标证据边界：`software_proof_docker_route_task_field_run_intake_crosscheck_gate`。
- 本轮不实现工程代码；本文件、`prd.md`、`tech-plan.md` 只定义下一轮 Engineer 执行范围、验收口径和风险边界。
- 计划完成后进入实现阶段时，必须由子 agent 执行代码、测试、修复和 `tech-done.md` 更新；主节点不得直接写产品代码、测试代码或硬件配置。

## 2. 当前 OKR 与切换理由

- `OKR.md` 4.1 当前最低 Objective 是 Objective 5：约 68%。
- 本机条件仍是 Docker/local 软件环境；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- 因此本轮不继续堆 Objective 5 本地 metadata。继续写本地 O5 包只会增加 blocked-by-design 材料，不能提升真实 external proof。
- Objective 1 约 75%，但本机没有真实 WAVE ROVER、串口/UART、`T=1001` feedback 或 HIL。不能把 Docker/local readiness、py_compile、CLI 或 synthetic artifact 当成 `hil_pass`。
- 可执行抓手转向 Objective 2 / Objective 3：把 route/task field run 的材料 intake、同一 `evidence_ref` crosscheck、缺失/不一致/未证明分类和 phone-safe 复盘链路补齐为软件能力。

## 3. 上轮证据摘要

- 最新 sprint：`sprints/2026.05.15_00-01_route-task-field-run-readiness/`。
- 已完成证据：`software_proof_docker_route_task_field_run_readiness_gate`。
- 已有输出能力：`route_task_field_run_readiness.py` 汇总 PC route debug console、operator review、execution bundle，输出 `required_field_run_materials`、`commands_to_run`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- diagnostics 已能 metadata-only 消费 readiness summary，不触发 collect/dropoff/cancel、ACK、cursor、Nav2、HIL 或 delivery success。
- mobile/web 已有只读“路线任务现场联跑准备”面板，只消费 phone-safe summary，不读取 raw artifact，不改变 Start/Confirm/Cancel gating。

## 4. 用户价值和产品北极星

- 用户价值：现场人员不需要猜“还缺什么材料”或手动对比多份 JSON；系统能用同一 `evidence_ref` 接收 route status、task record、runtime log、robot-side task evidence 和 mobile summary，并明确输出 missing、mismatch、not_proven 和 commands_to_rerun。
- 产品北极星：让不会 ROS2、串口和云基础设施的用户，能通过手机/诊断摘要理解一次路线-任务现场联跑是否具备复盘价值，以及下一步该补跑哪条命令。
- 本轮不追求“证明已送达”；追求“现场材料能被可靠 intake、交叉核对、保守复盘”。

## 5. 本轮核心抓手

1. 新增 field-run material intake/crosscheck artifact：接收同一 `evidence_ref` 下的材料引用和摘要。
2. 分类输出 `missing_materials`、`mismatch_reasons`、`not_proven`、`commands_to_rerun`。
3. diagnostics 只读消费 intake summary，继续 metadata-only，不触发机器人动作。
4. mobile/web 只读消费 support-safe mobile summary，让普通用户看到“缺什么、哪里不一致、还不能证明什么”。
5. 同步 docs 下接口/产品/导航文档，避免文档滞后于工程契约。

## 6. 需要做什么

- Autonomy owner：在 `pc-tools/evidence/` 增加 `route_task_field_run_intake` CLI / tests，定义 schema、输入材料、crosscheck 规则和 conservative status。
- Robot owner：在 operator diagnostics 中只读消费 intake artifact / summary，新增 metadata-only tests，确保不会触发 collect/dropoff/cancel、ACK、cursor、Nav2 或 HIL。
- Full-stack owner：在 mobile/web 增加只读 field-run intake/crosscheck panel，仅展示 phone-safe summary 和 commands_to_rerun，不改变 Start/Confirm/Cancel gating。
- Product/OKR owner：实现收口后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`；本 planning 阶段不修改 `OKR.md`。

## 7. Owner 与优先级

- P0 `autonomy-engineer`：field-run intake/crosscheck CLI、artifact schema、同一 `evidence_ref` 校验、单元测试、导航文档。
- P0 `robot-software-engineer`：diagnostics metadata-only summary、robot-side fence tests、接口文档。
- P1 `full-stack-software-engineer`：mobile/web 只读 summary panel、fixture/test、产品文档。
- P1 `product-okr-owner`：收口证据、OKR 进度与边界语言。

## 8. 风险、阻塞和证据边界

- 本轮只能产生 Docker/local software proof：`software_proof_docker_route_task_field_run_intake_crosscheck_gate`。
- 本轮不证明真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、串口/UART、HIL、dropoff/cancel completion、delivery success 或 Objective 5 external proof。
- 如果输入材料缺失，输出必须是 `missing` / `not_proven`，不得自动推断成功。
- 如果 `evidence_ref` 不一致，输出必须是 `mismatch`，并给出 commands_to_rerun，而不是合并成成功材料。
- mobile 和 diagnostics 只能消费白名单摘要；不得暴露 raw artifact、完整本地路径、ROS topic、`/cmd_vel`、串口/UART、baudrate、WAVE ROVER 参数、凭证、DB/queue URL、OSS AK/SK、traceback 或 checksum。

## 9. 需要创建或更新的 sprint 文档

- 本 planning 阶段创建：
  - `sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/pre_start.md`
  - `sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/prd.md`
  - `sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/tech-plan.md`
- 实现完成后必须补齐：
  - `sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/tech-done.md`
  - `sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/side2side_check.md`
  - `sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/final.md`
