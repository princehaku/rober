# Sprint 2026.05.15_09-10 Route Task Field Run Material Validation - Pre Start

sprint_type: epic

## 1. 启动依据

当前 `OKR.md` 4.1 显示 Objective 5 约 66%，仍是数值最低 Objective；但 `OKR.md` 第 6 节明确要求：只有拿到真实外部材料（公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration）时才继续推进 O5 completion。本机没有真实硬件，只有 Docker，也没有这些外部材料，因此本轮不重复消费 O5 blocker。

最新 sprint `2026.05.15_08-09_route-task-field-run-material-bundle` 的 `final.md` 第 4 节给出下一步：若仍没有 O5 外部材料，最高价值动作是拿 material bundle 去补 Objective 2 / Objective 3 的真实材料，包括真实 Nav2/fixed-route、真实路线采集、同一 `evidence_ref` 上车复账、dropoff/cancel completion 或 delivery success。受当前环境限制，本轮先把现场材料包推进为可校验的 material validation gate，为下一次真实 route/task field run 回填做准备。

## 2. 近期证据与反复问题

- PDD / sprint 主题：`07-08_route-task-field-run-evidence-kit` 把现场证据包组织起来；`08-09_route-task-field-run-material-bundle` 把证据包转成材料目录和模板。
- 评审与 closeout 反复指出：不能把 artifact pass、mobile panel、diagnostics summary 或 ACK 写成真实 Nav2/fixed-route、真实 dropoff/cancel completion、HIL 或 delivery success。
- 反复环境 blocker：本机 Docker-only，没有 WAVE ROVER、真实串口、真实手机、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic 或 production DB/queue 证据。

## 3. 本轮目标

建立 `software_proof_docker_route_task_field_run_material_validation_gate`：

- Autonomy：新增 PC 侧 material validation CLI，读取 material bundle 与现场材料目录，校验模板是否被真实材料替换、同一 `evidence_ref` 是否保持一致、dropoff/cancel/delivery 字段是否继续 fail-closed。
- Robot：diagnostics metadata-only 消费 validation artifact / summary，支持 explicit ref 与环境变量，schema/boundary 不匹配时 fail closed。
- Full-stack：`mobile/web` 新增只读“路线材料校验” panel，展示 validation status、缺失/占位材料、operator next steps 与 `not_proven`，不改变 Start / Confirm / Cancel gating。
- Product：收口 sprint 文档、`OKR.md` 与 `docs/process/okr_progress_log.md`，保守记录 O2/O3 software proof 进展。

## 4. Owner 与边界

- Autonomy Algorithm Engineer：`pc-tools/evidence/`、`pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`。
- Robot Platform Engineer：`onboard/src/ros2_trashbot_behavior/` diagnostics 与 `docs/interfaces/ros_contracts.md`。
- User Touchpoint Full-Stack Engineer：`mobile/web/`、`mobile/fixtures/`、`mobile/test_mobile_web_entrypoint.py`、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：`OKR.md`、`docs/process/okr_progress_log.md`、本 sprint closeout docs。

## 5. 风险

本轮仍不证明真实 route/task field run、真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、真实 dropoff/cancel completion、delivery success、真实手机/browser 或 O5 外部云证据。所有输出必须保持 Docker/local software proof 边界。
