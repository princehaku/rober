# Sprint 2026.05.19_23-24 Real Material Followup Escalation Status - Side2Side Check

## 1. Sprint 类型

- sprint_type: epic
- 检查时间：2026-05-19 23:23 Asia/Shanghai。
- 检查对象：`real_material_followup_escalation_status` PC artifact、Robot safe alias、mobile/web 只读 panel、接口文档、产品文档、OKR closeout。

## 2. 用户价值对照

| PRD 用户价值 | 本轮交付 | 验收结论 |
| --- | --- | --- |
| 现场 owner 能看到 owner、due_status、blocked_reason、next_required_evidence、escalation_level、rerun command/status summary。 | PC summary 覆盖四类 material group；mobile/web 只读 panel 展示相同 safe fields。 | 通过，仍是 `software_proof` / `not_proven`。 |
| Product 能判断 O5、O1 / PR #5、PR #4 route/elevator、O4 real phone 哪些仍缺真实材料。 | summary `review_refs` 明确 Objective 5、Objective 1、Objective 4、PR #4、PR #5 `PRRT_kwDOSWB9286CJ3tX` blocker。 | 通过，不提高 OKR 百分比。 |
| Robot 和 mobile 只能展示 sanitized summary，不读取 raw materials 或授权控制。 | Robot safe alias fail closed；mobile panel 只读且不改变 Start Delivery / Confirm Dropoff / Cancel gating。 | 通过。 |
| Reviewer 能看到 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 blocked。 | PC gate、docs、OKR 和 final 均保留 `blocked_pending_real_materials`。 | 通过。 |

## 3. OKR 映射对照

| Objective | PRD 期望 | 本轮验收 |
| --- | --- | --- |
| Objective 5 | 只追踪 external proof 缺口，不把 Docker-only status 当真实 external proof。 | 保持约 68%，仍缺公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。 |
| Objective 1 | 只追踪 PR #5 / hardware real material 缺口，不关闭 `PRRT_kwDOSWB9286CJ3tX`。 | 保持约 81%，仍缺 WAVE ROVER/UART/HIL、2D LiDAR / ToF source/procurement/installation/wiring/power/calibration/HIL-entry。 |
| Objective 2 / Objective 3 | 只追踪 PR #4 route/elevator real field material 缺口。 | 均保持约 99%，仍缺真实 Nav2/fixed-route runtime、route completion signal、field task record、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel material 和 delivery_result。 |
| Objective 4 | 只追踪 real phone material 缺口，不把 mobile panel 当真实手机 proof。 | 保持约 99%，仍缺真实 iPhone/Android、production app、PWA prompt/user choice 和 true phone/browser acceptance。 |

## 4. 验证对照

本轮 Product closeout 复跑所有集成验收命令：

- `python3 -m unittest tests/test_real_material_followup_escalation_status.py`：`Ran 6 tests ... OK`
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 217 tests ... OK`
- `python3 mobile/web/test_mobile_web_entrypoint.py`：`Ran 141 tests ... OK`
- `node --check mobile/web/app.js`：通过
- `python3 -m py_compile pc-tools/evidence/real_material_followup_escalation_status.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：通过
- Artifact regeneration：通过
- Required `rg`：通过
- Scoped `git diff --check`：通过

## 5. Side-by-side 结论

- 需求侧：PRD 的四组 material group、owner/due/blocker/next evidence/escalation/rerun 状态已全部落地。
- 工程侧：PC gate、Robot diagnostics 和 mobile/web 三层对齐同一 `software_proof_docker_real_material_followup_escalation_status_gate`。
- 产品侧：本轮只把真实材料缺口转成可追责 follow-up queue，不把它写成真实材料已到位、真实现场通过、HIL、手机通过或 delivery success。
- 阻塞侧：下一步仍需要 field owners 提供真实材料，然后重跑 `real_material_evidence_intake` / review chain。
