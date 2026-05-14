# Sprint 2026.05.15_01-02 Route Task Field Run Intake Crosscheck - Side To Side Check

sprint_type: epic

## 1. PRD 验收对照

| PRD 项 | 验收结果 | 证据 |
| --- | --- | --- |
| 接收 route status、task record、runtime log、robot-side task evidence、support-safe mobile summary 五类材料 | 通过 | Task A CLI 支持五输入 JSON，五份临时材料同 `evidence_ref` `--once-json` drill 输出 `overall_status=ready_for_review`。 |
| 同一 `evidence_ref` crosscheck | 通过 | Task A 输出 `missing_materials=[]`、`mismatch_reasons=[]`；测试覆盖 missing/mismatch 场景。 |
| 输出 `missing_materials`、`mismatch_reasons`、`commands_to_rerun`、`not_proven` | 通过 | Task A artifact、Task B diagnostics summary、Task C mobile panel 均消费或展示对应字段。 |
| schema/boundary 统一 | 通过 | `trashbot.route_task_field_run_intake_crosscheck.v1` 和 `software_proof_docker_route_task_field_run_intake_crosscheck_gate` 已在 pc-tools、diagnostics、mobile、docs 中对齐。 |
| diagnostics metadata-only | 通过 | Task B tests `Ran 57 tests OK`，证明 summary 不触发 collect/dropoff/cancel、ACK POST、cursor advance/persistence、terminal ACK、Nav2、HIL 或 delivery success。 |
| mobile 只读展示，不改变 Start/Confirm/Cancel gating | 通过 | Task C tests `Ran 8 tests in 0.022s OK`；集成修复后 nested diagnostics summary 消费已复验。 |
| docs 同步更新 | 通过 | `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 均已由对应 Engineer 更新。 |

## 2. 用户价值核对

本轮把“下一次真实路线-任务联跑应该收什么材料”推进为“收到材料后如何按同一 `evidence_ref` 复账”。现场人员和支持人员可以从 CLI artifact、diagnostics metadata-only summary、mobile read-only panel 三个入口看到：

- 哪些材料缺失。
- 哪些材料的 `evidence_ref` 不一致。
- 需要补跑哪些命令。
- 哪些结论仍是 `not_proven`。
- 当前不是 delivery success，也不是 HIL。

这符合 PRD 的产品北极星：普通用户和售后人员不用读 raw ROS2 日志、串口输出或云基础设施细节，也能理解一次 route-task field run 是否具备复盘价值。

## 3. OKR 映射核对

- Objective 2：通过 task record、robot-side task evidence、mobile summary 的同一 `evidence_ref` intake/crosscheck，推进“每次任务产出可复盘记录”的软件链路。
- Objective 3：通过 route status、runtime log、fixed-route/PC 材料的同一 `evidence_ref` intake/crosscheck，推进固定路线现场复盘入口。
- Objective 5：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration，不调整。
- Objective 1：没有真实 WAVE ROVER、串口/UART、`T=1001` feedback 或 HIL，不调整。
- Objective 4：mobile panel 是 O2/O3 field-run review 的只读触点，不计入真实手机设备或 production app 验收。

## 4. 证据边界核对

本轮 `ready_for_review` 只表示材料形状和软件复账链路可进入人工复核。它不证明：

- 真实 Nav2/fixed-route。
- 真实路线采集。
- WAVE ROVER。
- 真实串口/UART。
- HIL。
- 同一 `evidence_ref` 上车复账。
- dropoff/cancel completion。
- delivery success。
- Objective 5 external proof。
- 公网 HTTPS/TLS。
- 4G/SIM。
- OSS/CDN live traffic。
- production DB/queue。
- worker/migration。

## 5. 结论

本 sprint 达到 PRD 的软件交付验收口径，可收口为 `software_proof_docker_route_task_field_run_intake_crosscheck_gate`。Objective 2 和 Objective 3 可以各从约 83% 保守上调到约 84%；Objective 1、Objective 4、Objective 5 不调整。
