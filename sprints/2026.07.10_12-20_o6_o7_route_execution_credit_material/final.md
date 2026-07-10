# O6/O7 Route Execution Credit Material Final

## 本轮目标

在缺真实 production cloud、真实 WAVE ROVER HIL 和现场 route run 的环境下，选择仍可推进且不重复消费 blocker 的 O6/O7 路径：把 `same_task_route_execution_material_packet` 从安全摘要推进为可判定 OKR credit candidate 的同一 `task_id` 材料合同。

## 完成情况

已完成。Algorithm、O6、O7 三侧均已支持并验证以下字段：

- `live_or_field_command_evidence_present`
- `delivery_or_operator_material_consumed`
- `route_execution_credit_candidate`
- `credit_support_only_reason`
- `credit_required_evidence`

这些字段让 O6/O7 能区分“只是 support-only/readback wrapper”和“同 task 已具备 live/field command + delivery/operator 材料的 credit candidate”。它不会把任何 software proof 升级为真实 delivery success，也不会放开控制权限。

## 验证证据

- Algorithm：`python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py` 通过；`python3 -m unittest onboard.tests.test_field_route_evidence_manifest` 输出 `Ran 67 tests in 0.499s OK`。
- O6：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 通过；`python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` 输出 `Ran 171 tests in 68.289s OK`。
- O7：`cd pc-tools/workstation && npm run test && npm run build && npm run lint` 通过，关键结果 `Tests 486 passed (486)`，build 仅保留既有 chunk-size warning，lint 通过。
- 主节点验收：关键字段 `rg` 贯通 Algorithm、O6、O7、docs 和 sprint；`git diff --check` 通过。

## OKR 调整

- O6：约 87% -> 约 88%。理由：O6 archive/readback 已保留并 fail-closed credit-aware route execution material 字段，能把同一 `task_id` 的 live/field command 与 delivery/operator 材料转成可审计 credit candidate。
- O7：约 87% -> 约 88%。理由：O7 consumer/UI 已消费、展示并回归保护这些字段，能向 operator 展示 support-only 与 credit candidate 的差异。
- O5：维持约 85%。仍缺真实 production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic 和真实手机/browser 验收。
- O1：维持约 86%。仍缺真实 WAVE ROVER nonzero L/R、轮向、operator report、真实 robot motion 和 HIL acceptance。

本轮不归档任何 KR。

## 剩余风险

- 证据边界为 `software_proof_o6_o7_route_execution_credit_material_only`。
- 不证明真实 production cloud、production DB/queue、多实例一致性、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN、真实 annotation API/export 或 hardware safety/HIL。
- `route_execution_credit_candidate=true` 仍只是材料合同结果，不是控制或送达成功信号。

## 下一轮建议

1. 若有真实云/DB/queue/live endpoint 材料，优先回到 O5，用真实 production readback 或外部 probe 推进。
2. 若有上车日志和 HIL 材料，优先回到 O1，消费同一 run 的 `feedback_T1001.log`、motion command、operator report 和 HIL acceptance。
3. 若继续 O6/O7，必须输入真实或准现场 live route execution、delivery record、operator confirmation 或 production cloud readback，避免再做只读 wrapper。
