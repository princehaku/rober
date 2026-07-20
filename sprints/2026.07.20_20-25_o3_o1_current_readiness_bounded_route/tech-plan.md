# O3/O1 Current Readiness + Bounded Route - Tech Plan

## Plan metadata

- `sprint_type: epic`
- 状态：`implementation_ready_with_phase_gates`
- 唯一 live-control / 集成 owner：`robot-software-engineer`
- 专业 owner：`robot-algorithm-engineer`、`robot-hardware-engineer`、`full-stack-software-engineer`
- SSH：`root@192.168.1.11:37878`
- route target：`map (0.8, 0.25, yaw=0)`
- authorization：仅本轮一次 current readiness window + 条件通过后的 exactly-one route attempt

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前最低 Objective 是 O5，约 `85%`；O6/O7 各约 `93%`；O1 约 `94%`。
2. 本 sprint 不针对 O5。O5 provider/runtime 同根因已消费 `2/2`，第三次 tunnel/provider/wrapper/readback 被红线禁止。
3. 本 sprint 合法切换到 O3 current readiness supporting，并以 `READINESS_GO` 为硬门尝试一次 O1/O6/O7 bounded-route/current-HIL/user-action evidence。
4. planning、软件测试和 NO-GO 均不自动计分；只有 current route/HIL/user-action artifact 可由 Product 评估主百分比，KR 默认 `不归档`。

## 运行时连续性与串行策略

禁止多个 owner 并行操作真实上位机。Robot Software 是唯一 live-control owner，按 Phase A→B 执行 remote GET/POST、保存 raw artifact、无条件 stop/cleanup；Algorithm、Hardware、Full-stack 只在上一阶段冻结后进行本地/只读专业验收或范围内修复。

Phase A 必须复用当前已修复的 Upper API/O10 80s/final-reserve 合同，并让 current lifecycle 在 proof 与条件 route 之间连续。O11 不得自启第二套 runtime，O10 `managed_runtime_opt_in=false`，`initialpose_opt_in=false`。Phase A NO-GO 时立即 stop；GO 时先做 pre-stop，再发唯一 goal。

## Phase 0 - 冻结 inputs 与部署一致性

Robot Software 先用 `apply_patch` 在 sprint artifacts 下创建 identity/request JSON，不用 shell write trick。随后只读验证：

```bash
git status --short
ssh -p 37878 root@192.168.1.11 'curl -fsS http://127.0.0.1:8787/api/health && curl -fsS http://127.0.0.1:8787/api/status && curl -fsS http://127.0.0.1:8787/api/nav2/status'
```

若 remote helper/API SHA 与本地目标文件不一致，允许部署本 sprint 已通过测试的相关脚本；部署前后必须记录 SHA256。不得直接编辑远端文件。若无需代码改动，不得制造 churn。

## Phase A - Current strict-no-motion readiness

唯一 live-control owner 按顺序执行，每个 response 都保存为本 sprint `artifacts/robot-software/*.raw`，HTTP/SSH/curl/parse/SHA 写入 `phase_a_invocation_manifest.json`：

```bash
ssh -p 37878 root@192.168.1.11 "curl -fsS -X POST http://127.0.0.1:8787/api/nav2/start -H 'Content-Type: application/json' --data-binary @-" <<'JSON'
{"strict_no_motion":true,"base_enabled":false,"lidar_enabled":false,"reuse_existing_scan":true,"timeout_s":20}
JSON
ssh -p 37878 root@192.168.1.11 "curl -fsS -X POST http://127.0.0.1:8787/api/nav2/proof/refresh -H 'Content-Type: application/json' --data-binary @-" <<'JSON'
{"timeout_s":30,"managed_runtime_opt_in":false,"managed_timeout_s":30,"managed_map_yaml":"","initialpose_opt_in":false,"path_generation_opt_in":true,"path_generation_timeout_s":30,"path_goal_frame_id":"map","path_goal_x":0.8,"path_goal_y":0.25,"path_goal_yaw":0.0}
JSON
ssh -p 37878 root@192.168.1.11 'curl -fsS http://127.0.0.1:8787/api/nav2/proof/latest && curl -fsS http://127.0.0.1:8787/api/nav2/status && curl -fsS http://127.0.0.1:8787/api/status'
```

`readiness_assertion.json` 必须包含：

- `schema_version=trashbot.o3_o1.current_readiness_bounded_route.v1`
- `READINESS_GO=true|false` 与 exact blockers
- current final artifact、natural completion、`artifact_kind=final`、`last_phase=final`、`current_command=null`
- map/amcl/planner/controller active
- current fresh persisted pose、AMCL pose、dynamic `map->odom` freshness/unique attribution、`map->base_link`
- `initialpose_publish_attempts=0`
- path requested/attempted/succeeded/generated 与 point count
- current obstacle clear、existing motion false、operator/route/physical-limit authorization refs
- base/LiDAR new-open=`0/0`
- start/proof/latest invocation=`1/1/1`，goal/manual/cmd_vel/UART=`0/0/0/0`

任一 missing/unknown/stale/conflict/timeout/non-final/cleanup risk 都置 NO-GO。NO-GO 时立即一次 owned `POST /api/nav2/stop`，记录 stopped/residual；route/pre-stop/goal count 全部为 0，然后进入 tech-done。

## Phase B - Pre-stop + exactly-one bounded route + post-stop

仅 `READINESS_GO=true` 才继续。先执行一次 pre-stop：

```bash
ssh -p 37878 root@192.168.1.11 "curl -fsS -X POST http://127.0.0.1:8787/api/base/stop -H 'Content-Type: application/json' --data-binary '{}'"
```

pre-stop semantic/feedback 不 clean 则 goal count=`0`，owned Nav2 stop 后收口。clean 时，固定 request：

```json
{
  "confirm_navigation_execution": true,
  "goal_frame_id": "map",
  "goal_x": 0.8,
  "goal_y": 0.25,
  "goal_yaw": 0.0,
  "base_command_mode": "ros",
  "managed_runtime_opt_in": false,
  "result_timeout_s": 20,
  "server_timeout_s": 12,
  "task_id": "task_o3_28_pose_fixed_route_consumer_20260713_0402",
  "run_id": "run_o3_o1_current_readiness_route_20260720_2025_01",
  "route_intent_id": "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path",
  "authorization_ref": "ceo_20260720_2025_operator_watch_route_clear_physical_limit_v1",
  "action_id": "action_o3_o1_bounded_nav_20260720_2025_01"
}
```

通过 remote loopback 仅一次 `POST /api/nav2/goal/execute`。无论 success/fail/timeout/unknown，禁止 retry；随后最多一次 `POST /api/base/stop`，再只读 `/api/nav2/goal/execution/latest`、`/api/base/feedback-samples/latest`、`/api/status`，最后一次 owned `POST /api/nav2/stop` 清理 lifecycle。base stop 与 Nav2 lifecycle stop 是不同 endpoint，manifest 必须分别计数。

`phase_b_invocation_manifest.json` 必须固定：execute=`0|1`、pre_base_stop=`0|1`、post_base_stop=`0|1`、nav2_owned_stop=`1`；manual/free-roam/direct cmd_vel/initialpose/UART/delivery=`0`；no-retry=true；remote residual=`0`；所有 raw body、HTTP、parse、SHA 和 timestamps 齐备。

## Owner 分工与文件范围

### Robot Software - live integration / repair / tech-done

允许：

- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/field_route_evidence_preflight.md`
- 本 sprint `artifacts/robot-software/**`
- 本 sprint `tech-done.md`

任务：先运行本地回归；只在 current execution 发现明确 API/start/stop/execute integration bug 时做最小修复、测试、部署、复验。执行 Phase 0/A/B，保存 raw/manifest，汇总所有 owner 证据到 `tech-done.md`。不得修改 Algorithm/Hardware/Full-stack 文件。

验收：

```bash
python3 -m py_compile onboard/scripts/upper_robot_api.py
python3 -m unittest onboard/tests/test_upper_robot_api.py
python3 -m json.tool sprints/2026.07.20_20-25_o3_o1_current_readiness_bounded_route/artifacts/robot-software/readiness_assertion.json >/dev/null
python3 -m json.tool sprints/2026.07.20_20-25_o3_o1_current_readiness_bounded_route/artifacts/robot-software/phase_a_invocation_manifest.json >/dev/null
git diff --check -- onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py docs/navigation/field_route_evidence_preflight.md sprints/2026.07.20_20-25_o3_o1_current_readiness_bounded_route
```

Phase B 发生时再校验 `phase_b_invocation_manifest.json` 与所有 route/stop/readback raw；NO-GO 时必须明确不存在 Phase B action artifact。

### Algorithm - readiness 专业验收/必要修复

允许：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/fixed_route_workflow.md`
- 本 sprint `artifacts/algorithm/**`

任务：在 Robot Software 冻结 Phase A raw 后只读验证 freshness、attribution、persisted pose、planner/controller/path、80s/final reserve；必要时只修自己的 helper/test/doc，交回 Robot Software 决定是否允许一个新的授权窗口。不得自行 SSH、start/stop/proof/goal；不得在同一授权窗口重跑 Phase A。

验收：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py
python3 -m json.tool sprints/2026.07.20_20-25_o3_o1_current_readiness_bounded_route/artifacts/algorithm/readiness_review.json >/dev/null
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/fixed_route_workflow.md sprints/2026.07.20_20-25_o3_o1_current_readiness_bounded_route
```

### Hardware - same-window stop/T1001 验收

允许：

- 只读 vendor sources
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_bounded_route_hil_evidence.py`
- `docs/hardware/wave_rover_bounded_route_hil_evidence.md`
- 本 sprint `artifacts/hardware/**`

任务：只在 Phase B execute=`1` 且 artifacts 冻结后验证；不发送任何 live 命令。按 `json_cmd.h` 的 `FEEDBACK_BASE_INFO=1001` 和 vendor frame `L/R/r/p/y/v` 校验同窗 pre/post stop、motion/post-stop 与 lineage。T1001 存在不等于 L/R 非零或 HIL pass。

验收：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py
python3 -m unittest onboard.src.ros2_trashbot_hardware.test.test_wave_rover_bounded_route_hil_evidence
python3 -m json.tool sprints/2026.07.20_20-25_o3_o1_current_readiness_bounded_route/artifacts/hardware/wave_rover_hil_evidence.json >/dev/null
git diff --check -- onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_bounded_route_hil_evidence.py docs/hardware/wave_rover_bounded_route_hil_evidence.md sprints/2026.07.20_20-25_o3_o1_current_readiness_bounded_route
```

### Full-stack - frozen receipt consumption

允许：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/product/pc_tools_workstation.md`
- 本 sprint `artifacts/full-stack/**`

任务：只在 Phase A/B frozen 后验证现有 receipt/consumer-read 对 identity、NO-GO/terminal、stop、feedback、operator outcome 的表达；不得调用机器人、不得新建 endpoint/wrapper/mock success。只有明确合同 bug 才最小修复。

验收：

```bash
cd pc-tools/workstation && npm run test -- test/catalog.test.ts -t "Nav2 goal execution"
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
python3 -m json.tool sprints/2026.07.20_20-25_o3_o1_current_readiness_bounded_route/artifacts/full-stack/action_receipt_review.json >/dev/null
git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md sprints/2026.07.20_20-25_o3_o1_current_readiness_bounded_route
```

## Dispatch 与修复顺序

1. 先派 Robot Software 单线执行本地回归 + Phase 0/A；它是唯一 live owner。
2. Phase A frozen 后派 Algorithm 只读/本地验证。若 NO-GO 且 artifact honest，直接收口；若发现代码 bug，不消耗同一窗口补跑，修复后要求新的 CEO/current gate 才能再 live。
3. `READINESS_GO=true` 且 Algorithm 接受时，Robot Software 继续 Phase B；不得把另一个 owner 变成第二 live-control owner。
4. Phase B frozen 后 Hardware 与 Full-stack 文件范围互斥，可并行专业验收；二者均不得 live/control。
5. Robot Software 汇总 `tech-done.md`；Product 只读验收创建 `side2side_check.md`、`final.md` 并按实际证据更新 OKR/progress。

## Proof boundary 与 Product credit

- NO-GO：只接受 current artifact/诊断 delta，route/user-action/HIL/delivery/safe false。
- execute handler 可归因：user-action candidate；HTTP 200 不足。
- current terminal succeeded + latest/action lineage：route success candidate。
- route success + same-window pre/post stop + valid T1001 motion/post-stop + operator result：HIL/operator acceptance candidate。
- `delivery_success=false` 固定；`safe_to_control` 保守保持 false，除非另有独立 Product/HIL gate。

所有代码注释必须为中文且比例严格 `>20%`。任何验证失败先定位、在 owner 范围修复、重跑 targeted/full；不得把第一轮失败直接交差。任何额外 live window、第二 goal、第二 base stop retry、`/initialpose`、manual、direct `/cmd_vel`、UART 直控或 unattended motion 都禁止。
