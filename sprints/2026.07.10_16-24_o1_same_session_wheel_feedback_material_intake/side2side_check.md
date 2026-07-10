# O1 Same-session WAVE ROVER Wheel Feedback Material Intake Side-to-side Check

## sprint_type

sprint_type: epic

## 验收结论

Product closeout 通过。Hardware owner 本轮没有新增控制动作，也没有把历史材料冒充 current live HIL pass；实现产物确实消费了历史真实上位机 artifact，并把 O1 same-session wheel feedback material 收敛为可复验、脱敏、fail-closed 的软件证据。

## 用户价值和产品北极星

产品北极星仍是“普通用户把垃圾交给小车后，小车能安全、可验证地送到目标点”。O1 的用户价值是让底盘 wheel feedback 材料进入可信证据链：团队现在能区分“历史 same-session wheel feedback material 已被安全接入”和“当前 live HIL pass / safe-to-control 仍未证明”。

## Side-to-side 核对

| 计划口径 | 实际证据 | Product 判断 |
| --- | --- | --- |
| 消费历史真实上位机 artifact，而不是新增 wrapper | 输入为 `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json` | 通过，本轮有真实历史 material delta |
| 输出清晰合同 | 新增 `trashbot.wave_rover_same_session_wheel_feedback_material.v1` | 通过 |
| ready status 保守命名 | positive 输出 `same_session_wheel_feedback_material_ready_not_delivery_proof` | 通过，不声称 delivery proof |
| 提取 same-session nonzero pair | `latest_nonzero_pair.left_speed=61.0`、`latest_nonzero_pair.right_speed=61.0`、`phase=motion_window` | 通过 |
| 安全字段不可被输入抬高 | 固定 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` | 通过 |
| 脱敏输出 | 主节点只读验收看到 positive CLI 输出没有 `/dev/tty`、baudrate、endpoint 或 raw frames | 通过 |
| fail-closed | dangerous temp artifact exit 4，`safe_to_control=true` 被压回 blocked / false | 通过 |

## OKR 映射和方向判断

- 映射 Objective：O1 硬件协议可信底盘。
- 方向判断：继续 O1，但只计保守增量。
- 进度判断：O1 可从约 86% 保守上调到约 87%，因为本轮消费了历史真实上位机 same-session wheel feedback material，不是同层 wrapper、review 或 checklist。
- O5 保持约 85%，O6/O7 保持约 91%。
- 本轮不归档 KR；KR3/KR4 仍需要 current live HIL、轮速方向、IMU/battery 标定和硬件准入证据才能进入完成归档。

## 风险和剩余证据

- 本轮不是 current live HIL pass。
- 本轮不是 hardware safe-to-control。
- 本轮不证明 delivery success、Nav2 route execution、operator acceptance 或 production cloud。
- O1 下一步需要当前同 run `feedback_T1001.log`、motion command record、operator / external motion observation、HIL acceptance record。

## Product 验收命令

Product closeout 后运行文件存在性、关键证据 `rg` 和 scoped `git diff --check`。最终命令输出记录在 `artifacts/product_worker_report.md` 和 `final.md`。
