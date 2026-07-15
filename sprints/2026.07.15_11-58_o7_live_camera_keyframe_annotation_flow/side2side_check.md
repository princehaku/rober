# O7 真实相机关键帧标注流 Epic - Side2Side Check

## 状态与对照范围

- `sprint_type: epic`
- Product side-to-side：`accepted_software_contract_and_single_blocked_live_gate_no_keyframe`
- 对照：`pre_start.md`、`prd.md`、`tech-plan.md`、补全后的 `tech-done.md`、Algorithm 三个 JSON、
  Full-stack 四个 JSON + validation log、实际 git diff 与两位 Engineer 验证事实。

## 计划与实际对照

| 验收项 | 计划 | 实际 | Product 判定 |
| --- | --- | --- | --- |
| Algorithm 离线合同 | helper/test/doc、39 tests、注释 >20% | py_compile 0，39 tests OK，`20.7108%/21%` | 接受 |
| 唯一 inventory | 最多一次 daemon-off | invocation `1`，exit `2`，`inventory_ssh_or_payload_failed` | 接受 blocked gate |
| 单帧 capture | gate clean 后最多一次 | gate blocked，capture `0`，无 keyframe/PNG/hash | 拒绝 live keyframe |
| O6/O7 合同 | 既有主路径、fixture 不冒充 live | relay 202 tests；workstation 530 tests/build/lint；hostile PASS | 接受软件合同 |
| 真实 manifest 投影 | 同 task/source/count fail-closed | Algorithm/O6/O7 均同 task、`live_inventory_blocked`、`1/0` | 接受诚实投影 |
| annotation-ready | 仅 clean live 或显式 fixture | 真实 path `annotation_ready=false`；fixture 单独标识 | 拒绝真实 annotation |

## Artifact 与安全核对

- Algorithm 三个 JSON、Full-stack 四个 JSON 均通过 `python3 -m json.tool`。
- 结构断言确认 inventory/capture=`1/0`、`annotation_ready=false`、四 delta=false；
  `safe_to_control/robot_control_executed/route_execution_success/delivery_success/hil_pass=false`。
- O6 write/readback 与 O7 consumer 保留同一 task/source/count/blocker；未生成 `keyframe.png`，
  `media_basename/sha256` 为空，未用 fixture 或历史图片替代。
- raw pixels、binary/base64、绝对路径、远端 host、stderr/traceback 未进入 JSON/API/UI。
- inventory fallback 的 daemon `0/0` 不是远端 daemon clean 证明；publisher count `0` 也不是现场
  已确认无 publisher，只能说明远端 payload 未形成。

## 验证与失败修复核对

- Algorithm：首轮注释比例约 `5.69%` 与 artifact assertion `KeyError` 均已离线修复；最终
  39 tests OK、注释 `20.7108%/21%`，没有重跑 SSH。
- Full-stack：错误 test class、topic/path false positive、二次 sanitize、TS index、错误 mock helper、
  历史 DOM timestamp 六类偏差均已定位修复；relay 202、workstation 530、build/lint、JSON/rg/diff 通过。
- Product 本轮不重跑 SSH 或产品全量测试，只复核已留存 Engineer 日志并执行 JSON/结构/rg/diff/status 验收。

## Product Acceptance 与 Proof Boundary

- 接受：daemon-off/no-write/no-control 设计、唯一 blocked inventory、capture 未启动的安全决策、
  Algorithm 软件合同、O6/O7 blocked/fixture metadata 合同、hostile fail-closed 和文档同步。
- 拒绝：真实 keyframe、可见内容、privacy approval、真实 annotation submit/export、RTC/video、
  production cloud/DB/OSS、route execution、delivery/operator acceptance、HIL、safe-to-control。
- Product proof boundary：
  `software_contract_o6_o7_live_camera_keyframe_annotation_metadata_only_with_single_blocked_live_inventory_no_keyframe`。

## Mission / OKR / KR

- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `mission_objective_0_satisfied=false`、`okr_credit=false`
- O5 约 `85%`、O6/O7 各约 `93%`、O1 约 `94%`，主百分比全平；KR `不归档`，历史区无新增完成项。

## Anti-repeat 与下一轮

- 本 camera inventory、single-frame helper/capture gate、manifest、O6 section、O7 card、fixture/hostile
  matrix 已消费并退役；不得下一轮换壳重复。
- `inventory_ssh_or_payload_failed` 不得再包装为第三层 preflight/readback/diagnostic/status helper。
- 默认 next owner：`product-okr-owner` 切换到其他 Objective，选择能产生新 mission-grade artifact/action
  的 Engineer lane；禁止继续 O7 camera 支持面。
- 例外：只有 CEO 提供 fresh authorization 且现场已有 camera publisher 新条件，才另开新 sprint 由
  `robot-algorithm-engineer` 直接执行新授权 live gate；不能复用本 sprint invocation 或包装旧 blocker。
