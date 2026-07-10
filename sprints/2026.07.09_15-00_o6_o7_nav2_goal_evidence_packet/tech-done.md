# O6/O7 Nav2 Goal Evidence Packet Tech Done

## sprint_type: epic

Product 收口时间：2026-07-09 15:29 CST。

## 用户价值和产品北极星

本轮把 Nav2 goal execution proof 从孤立 JSON 推进为同一 `task_id` 下可归档、可回读、可展示的证据摘要。用户价值是让“机器人是否有一条可解释的 Nav2 目标执行记录、结果摘要是什么、下一步还缺什么证据”进入 O6/O7 主链路，而不是停留在单机脚本日志。

产品北极星不变：普通手机用户把垃圾交给机器人后，机器人要可验证地完成投递。本轮只证明 Nav2 goal execution evidence 的软件证据链，不证明真实送达。

## 实际改动汇总

### Algorithm / `robot-algorithm-engineer`

- 在 `onboard/scripts/field_route_evidence_manifest.py` 新增 `--nav2-goal-proof-json`。
- 新增 `trashbot.nav2_goal_execution_evidence.v1` 摘要和 `software_proof_nav2_goal_execution_evidence_only` 证据边界。
- 将 `nav2_goal_execution_evidence` 写入 manifest 顶层和 `field_motion_evidence_packet.nav2_goal_execution_evidence`。
- 保持 `task_id` 沿用 field packet lineage，不允许 O11 proof 覆盖。
- 对 schema mismatch、dangerous true、unsafe path/root/token/raw/base64 等输入 fail-closed，输出 `blocked_not_proven`。

### O6 / `robot-software-engineer`

- 在 O6 archive ingest/readback 中新增 `nav2_goal_execution_evidence` sanitizer/readback helper。
- 支持 field evidence manifest、artifact bundle、archive task detail、consumer detail、`include=field_evidence` 和 `include=nav2_goal_execution_evidence` 回读。
- 只暴露白名单字段；危险 true、unsafe path/root/token/raw/base64、schema/proof-scope mismatch 均 fail-closed。
- 保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

### O7 / `full-stack-software-engineer`

- O7 consumer detail 新增只读 `Nav2 goal execution evidence` 摘要展示。
- 展示 schema/status/proof_scope、goal requested/sent/accepted/result received、result status/code、base command/feedback 摘要、blocked reasons、next required evidence 和 false safety fields。
- `DEFAULT_DETAIL_INCLUDE` 新增 `nav2_goal_execution_evidence`。
- Adapter 白名单读取 top-level、field evidence、field motion packet、artifact bundle、readiness wrapper 等来源，schema/proof-scope mismatch 与 unsafe text 均 fail-closed。

## 三路验证结果

Algorithm 验证：

```text
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py onboard/scripts/o11_nav2_goal_execution_proof.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest onboard.tests.test_o11_nav2_goal_execution_proof
Ran 29 tests in 0.059s
OK
```

O6 验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
Ran 156 tests in 53.382s
OK
```

O7 验证：

```text
cd pc-tools/workstation && npm run test
Test Files  3 passed (3)
Tests       477 passed (477)
```

```text
cd pc-tools/workstation && npm run build
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
34 modules transformed.
built in 1.73s
```

```text
cd pc-tools/workstation && npm run lint
eslint .
exit code 0
```

## 失败修复

- Algorithm：报告未记录实现后验证失败。
- O6：报告未记录实现后验证失败。
- O7：首次 `npm run build` 失败于 `src/server/o7ConsumerReadAdapter.ts` 的 TS2783，原因是 `connects_cloud_production` / `robot_control_executed` 显式字段被 `fixedFalseFields()` 重复覆盖；删除重复显式字段后 build 通过。

## OKR 映射和方向判断

- O6：本轮推进 KR2 / KR6 的软件侧证据链，archive/read model 已能回读 Nav2 goal/result evidence。
- O7：本轮推进 KR3 / KR4 的软件侧消费链路，PC 工作站能展示同一 `task_id` 的只读 Nav2 goal evidence readiness。
- 方向判断：继续推进 O6/O7，但下一轮不应继续堆叠只读 wrapper；应优先补真实或更接近现场的 `route_bag`、live Nav2 pose progress、真实媒体访问或 delivery record。
- KR 归档判断：不归档任何 KR。

## 安全旗标

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

## 剩余风险

- 本轮证据边界是 `software_proof_nav2_goal_execution_evidence_only`。
- 不证明真实 production cloud、真实 OSS/CDN、真实 route bag、真实 live Nav2 run、真实底盘运动、真实 delivery success、真实 annotation API/export、真实手机/PC 现场验收。
- O11 proof 若携带原始路径、root、token、raw 或 base64 内容会按安全规则 fail-closed；后续若需要接真实日志，应先产出安全裁剪版 proof。
