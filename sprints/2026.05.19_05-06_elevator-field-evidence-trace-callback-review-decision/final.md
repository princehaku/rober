# Sprint 2026.05.19_05-06 Elevator Field Evidence Trace Callback Review Decision - Final

## sprint_type: epic

Final time: 2026-05-19 05:23 Asia/Shanghai.

## 1. 用户价值和产品北极星

本轮把 PR #4 route/elevator 现场材料链路从“callback intake ready”推进到“review decision 可判定”。现场 owner 后续能看到哪些材料缺失、哪些材料被拒、是否需要重新回执，或者是否能进入下一段 owner handoff。

北极星仍是面向普通手机用户的可解释送垃圾机器人；本轮不是实机送达，不是电梯 field pass，也不是 O5 云端生产证明。

## 2. OKR 映射

| Objective | 收口判断 |
| --- | --- |
| Objective 1 | 保持约 81%。本轮未新增 WAVE ROVER/UART/HIL、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery` 或 PR #5 真实 2D LiDAR / ToF 材料。 |
| Objective 2 | 保守保持约 99%。新增 `elevator_field_evidence_trace_callback_review_decision`，推进电梯 assisted delivery 现场材料复核决策；仍不是真实 field pass。 |
| Objective 3 | 保守保持约 99%。把 Nav2/fixed-route runtime、route completion signal、field task record 等缺口继续作为 review decision hard requirements；仍缺真实路线运行。 |
| Objective 4 | 保守保持约 99%。mobile/web 只读展示 review decision、decision reasons、missing/rejected materials 和 owner handoff；仍缺真实 phone/browser 现场验收。 |
| Objective 5 | 保持约 68%。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。 |

## 3. KR 拆解或更新

- Objective 2 KR5/KR6/KR7：本轮新增 same safe `evidence_ref` callback review decision，可承接真实门状态、目标楼层确认、人工协助、dropoff/cancel、delivery result 等材料的复核状态，但当前全部仍是待回填、待复核或 metadata ready。
- Objective 3 KR3/KR4/KR5：route runtime、route completion signal、field task record 继续作为 required materials，防止 review ready 被误当成路线通过。
- Objective 4 KR6/KR7：手机端只读展示 review decision、missing/rejected materials 和 owner handoff，不暴露 raw JSON/ROS topic，也不启用控制动作。

## 4. 本轮核心抓手

核心抓手完成：`elevator_field_evidence_trace_callback_review_decision`。

- Autonomy：PC review-decision gate + focused tests + interface docs。
- Robot：diagnostics safe alias + focused tests + interface docs。
- Full-Stack：mobile/web 只读 panel + fixtures + focused tests + product flow docs。
- Product：closeout、OKR 当前快照、进展日志和风险边界更新。

## 5. 需要做什么

下一步若继续 PR #4 route/elevator 现场链路，应进入 owner handoff 或真实材料回填：

- 现场 owner 回填真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、field task record、dropoff/cancel completion、delivery result。
- Autonomy/Robot 基于同一 safe `evidence_ref` 做后续 handoff 或材料 backfill intake，不得把缺失材料写成通过。
- Full-Stack 继续只读展示结果，除非真实 phone/browser 和 production control gates 另行通过。

## 6. 优先级和验收口径

下一轮优先级：

1. Objective 5 数字最低但外部材料仍缺；只有拿到真实 external proof 才应继续 O5 completion。
2. Objective 1 次低但真实 WAVE ROVER/UART/HIL 与 PR #5 2D LiDAR / ToF 材料仍缺；无真实硬件时不要继续消费同一 blocker。
3. 若 O5/O1 真实材料不可用，继续 Objective 2/O3 的 PR #4 route/elevator 真实材料回填或 owner handoff。
4. 可并行补 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。

验收口径：所有本轮输出继续标记 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：后续 owner handoff / route runtime material 判定。
- Robot Platform Engineer：field task record、diagnostics summary 和同一 `evidence_ref` 复账。
- User Touchpoint Full-Stack Engineer：真实手机/browser 验收链和只读展示继续对齐。
- Hardware Infra Engineer：PR #5 2D LiDAR / ToF 与 WAVE ROVER/UART/HIL 真实材料。
- Product Manager / OKR Owner：OKR rerank、阶段验收和 blocker 重复消费控制。

## 8. 风险、阻塞和需要补齐的证据链

- 本轮不证明真实电梯、真实 Nav2/fixed-route、真实 task record/completion signal、dropoff/cancel completion、delivery success、WAVE ROVER/UART/HIL、真实 phone/browser、PR #5 真实 2D LiDAR/ToF 材料或 O5 external proof。
- 当前仍缺真实路线采集、真实 route completion signal、真实现场 task record、真实门状态、真实楼层确认、人工协助现场记录、真实送达、失败恢复实测、真实 dropoff/cancel completion 和真实 delivery result。
- `ready_for_elevator_field_owner_handoff_not_proven` 只能表示 metadata review decision 进入 owner handoff；`not_proven` 必须保留。

## 9. 需要创建或更新的 sprint 文档

已创建/更新：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`
- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

主会话复跑：

- `python3 -m py_compile pc-tools/evidence/elevator_field_evidence_trace_callback_review_decision.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py mobile/web/test_mobile_web_entrypoint.py`：通过。
- `python3 -m unittest tests/test_elevator_field_evidence_trace_callback_review_decision.py`：`Ran 7 tests in 0.043s OK`。
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 196 tests in 0.475s OK`。
- `python3 mobile/web/test_mobile_web_entrypoint.py`：`Ran 108 tests in 0.688s OK`。
- `node --check mobile/web/app.js`：通过。
- required `rg` 与 scoped `git diff --check`：通过。

## 最终结论

本 sprint 可收口为 O2/O3/O4 的 Docker/local `software_proof`：callback review decision、Robot diagnostics alias、mobile/web 只读展示和文档链路已形成。OKR 百分比不因本地 metadata proof 上调；O5 仍约 68%，O1 仍约 81%，O2/O3/O4 保守保持约 99%。
