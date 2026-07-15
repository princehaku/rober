# O7 真实相机关键帧标注流 Epic - Final

## Sprint Metadata

- `sprint_type: epic`
- Product status：`accepted_software_contract_and_single_blocked_live_gate_no_keyframe_no_mission_credit`
- Blocker：`inventory_ssh_or_payload_failed`
- Proof boundary：`software_contract_o6_o7_live_camera_keyframe_annotation_metadata_only_with_single_blocked_live_inventory_no_keyframe`

## Product Acceptance 结论

本轮接受两个 Engineer 已完成的安全软件合同，以及 Algorithm 唯一一次 daemon-off inventory 在未形成
可解析远端 payload 后 fail closed、capture 保持 `0` 的决策。Full-stack 沿既有 O6 artifact-bundle / task
detail / O7 consumer-detail 路径保留同一 blocked manifest 的 task/source/count，并用 fixture/hostile matrix
证明合同，不曾把 fixture 升级为 live。

本轮拒绝真实 keyframe：没有 PNG、hash、topic/stamp、width/height/encoding 或已确认 publisher；
`annotation_ready=false`。同时拒绝可见内容、隐私批准、真实 annotation submit/export、RTC/video、生产云、
DB/OSS、路线执行、送达/operator acceptance、HIL 与 safe-to-control。

## 实际改动与验证

- Algorithm：helper、39-test suite、vision doc、三个 blocked JSON、`tech-done.md`；py_compile exit `0`，
  `Ran 39 tests ... OK`，中文注释 `20.7108%/21%`。
- 唯一 live gate：inventory invocation `1`、exit `2`、blocker=`inventory_ssh_or_payload_failed`；
  capture invocation `0`、无 retry、无 keyframe。
- Full-stack：既有 O6/O7 主路径、contracts/UI/tests 与三份 docs；relay `202` tests OK，workstation
  `530` tests OK，build/lint PASS，新增注释 `20.4748%/20.4372%`。
- 七个 JSON、同源结构断言、forbidden binary/path/URL scan、required `rg` 与 scoped diff check PASS。
- 首轮失败及修复已完整记录在 `tech-done.md`；没有用第二次 SSH/live 调用修复离线问题。

## Mission / OKR / KR 决策

- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`
- `safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、
  `delivery_success=false`、`hil_pass=false`
- O5 保持约 `85%`，O6/O7 各保持约 `93%`，O1 保持约 `94%`；KR `不归档`，无完成 KR 进入历史区。

## 失败定位与剩余风险

- 精确 blocker 只能定到 `inventory_ssh_or_payload_failed`；因安全设计未持久化远端 stderr/host/traceback，
  不能进一步声称 SSH、ROS source、topic CLI、dependency 或 JSON decode 中哪一步失败。
- fallback daemon `0/0` 不证明远端 daemon clean；publisher count `0` 不证明现场没有 publisher。
- fixture 只证明 software contract；没有真实图像内容、隐私/标注行动或 production media lineage。
- Vite build 保留既有 `chunk >500 kB` warning，不影响本轮通过，但仍是长期前端打包风险。

## Anti-repeat 与下一步

本 camera inventory、single-frame helper/capture gate、manifest、O6 section、O7 card 和 fixture/hostile matrix
全部视为已消费并退役。下一轮不得把 `inventory_ssh_or_payload_failed` 再包装成 preflight、readback、
diagnostic、status、browser、export 或 mock wrapper，也不得重跑本 sprint inventory/capture。

默认由 `product-okr-owner` 切换 Objective，选择能直接产生新 mission-grade artifact/action 的 Engineer lane。
只有 CEO 给出 fresh authorization 且现场出现已确认 camera publisher 新条件，才允许另立新 sprint，交给
`robot-algorithm-engineer` 直接执行新的 live gate；该例外不复用本轮调用额度，也不能只做诊断包装。
