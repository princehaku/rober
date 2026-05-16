# Sprint 2026.05.17_01-02 Route Task Field Retest Operator Drill - PRD

sprint_type: epic

## 1. 用户问题

上一轮 `route_task_field_retest_material_pack` 已能校验现场材料目录，但现场人员拿到 summary 后仍需要人工串命令、人工确认下一步应该跑 result intake 还是 result reconciliation，并且容易把“材料目录可复账”误读成真实送达完成。

在本机只有 Docker、没有真实硬件的约束下，本轮要把“材料包已就绪但还没真实跑”的状态推进为一份 operator drill：明确同一 `evidence_ref` 下的下一条命令、预期输入输出、缺失材料、回调动作和 phone-safe 摘要。

## 2. 目标用户

- 现场支持同学：照着 drill 准备真实材料目录和回填结果，不需要理解 ROS2 topic、UART 或云端内部字段。
- Robot / Full-stack 消费面：只读展示 drill summary，继续 fail closed，避免误开主操作按钮。
- Product / OKR owner：能基于 PR #4 / PR #5 与最近 sprint 证据判断下一步是真实材料回填，而不是继续做 O5 本地包装。

## 3. 成功标准

- PC gate 输出 `trashbot.route_task_field_retest_operator_drill.v1` 与 `trashbot.route_task_field_retest_operator_drill_summary.v1`。
- 输出固定 `software_proof_docker_route_task_field_retest_operator_drill_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Drill 包含 material pack command、result intake command、result reconciliation command、required outputs、missing material prompts、operator callback checklist 和 rerun notes。
- 缺输入、坏 JSON、unsupported schema/boundary、证据号不一致、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER、success wording、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- Robot diagnostics 和 mobile/web 只展示 safe summary，不展示 raw artifact、raw paths、credentials、ROS topic、串口、硬件参数或完整 JSON。

## 4. 非目标

- 不采集真实 Nav2/fixed-route runtime log。
- 不运行真实电梯、真实 WAVE ROVER、真实 UART、HIL 或真实手机设备验收。
- 不提升 Objective 5；没有真实外部云/4G/OSS/CDN/DB/queue evidence 时 Objective 5 保持 blocked。
- 不新增大范围测试；只运行 tech-plan 中的围栏验证。

## 5. OKR 对齐

- Objective 2：把 PR #4 电梯 assisted delivery 的现场材料回填链路从“材料包摘要”推进到“操作演练和下一步命令”。
- Objective 3：把 route/task field retest 的 material pack -> intake -> reconciliation 执行顺序固化，降低真实 Nav2/fixed-route 材料回填时的命令断裂。
- Objective 4：手机端只读解释 operator drill 状态和下一步，不改变主操作授权。
- Objective 5：保持约 66%，不因本地 operator drill 提升。

## 6. 验收口径

本轮验收只看 Docker/local software proof：

- CLI / diagnostics / mobile copy 都必须包含 proof boundary。
- 所有主操作状态保持 `primary_actions_enabled=false`。
- 所有送达结果保持 `delivery_success=false`。
- 所有缺口必须写明真实材料仍待现场回填。
