# O3/O1 Live Deadline Fix Validation + Bounded Route - Tech Plan

## Plan metadata

- `sprint_type: epic`
- 状态：`implementation_ready_with_serial_live_gates`
- 唯一 live owner / 集成 owner：`robot-software-engineer`
- Phase A frozen review：`robot-algorithm-engineer`
- Phase B frozen review：`robot-hardware-engineer`
- Full-stack：默认 `not_dispatched`
- SSH：`root@192.168.1.11:37878`
- target HEAD：`85ba7308785aa3c4033180a097e3d388358a97de`
- route target：`map (0.8, 0.25, yaw=0)`
- authorization：`ceo_20260720_2124_operator_watch_route_clear_physical_limit_v2`
- run：`run_o3_o1_current_readiness_route_20260720_2124_01`
- task：`task_o3_28_pose_fixed_route_consumer_20260713_0402`
- route intent：`route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- action：`action_o3_o1_bounded_nav_20260720_2124_01`

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前最低 Objective 是 O5，约 `85%`；O6/O7 各约 `93%`，O1 约 `94%`。
2. 本 sprint 不针对 O5。O5 provider/runtime 同根因 blocker 已消费 `2/2`，继续暂停；禁止第三次 tunnel/provider/preflight/wrapper/readback。
3. 本 sprint 合法切换到 O3 current readiness supporting，利用 CEO 21:24 fresh authorization 验证已发布 deadline fix；仅在 `READINESS_GO=true` 后推进一次 O1/O6/O7 current route/HIL/user-action evidence。
4. O1/O6/O7 初始全部 flat，KR 默认 `不归档`。部署、软件测试、Phase A NO-GO 与单独 path success 都不自动计分。

## 串行状态机与 handoff

```text
Phase 0 HEAD/SHA/health hard gate
  -> FAIL: repair Phase 0 while Phase A count=0
  -> PASS: robot-software-engineer executes Phase A exactly once
      -> freeze raw + manifest + assertion
      -> robot-algorithm-engineer read-only review
          -> NO-GO/disagree: one owned cleanup, seal, no retry
          -> READINESS_GO=true: same robot-software-engineer continues
              -> pre-base-stop exactly once
                  -> FAIL: owned cleanup, goal=0, seal, no retry
                  -> PASS: NavigateToPose exactly once
                      -> post-base-stop at most once
                      -> terminal/feedback/status read-only
                      -> owned cleanup exactly once
                      -> freeze Phase B
                      -> robot-hardware-engineer read-only T=1001/HIL review
```

Phase A start 一旦调用，本 fresh authorization window 即被消费。Algorithm 与 Hardware 不得 SSH 或 live；它们的 review 不得与 live owner 并行。Full-stack 只有 route terminal frozen 且既有 receipt contract 出现真实 bug 时才条件派发。

## Phase 0 - 冻结 inputs、离线回归、部署 HEAD

### 0.1 先冻结 artifact contract

Robot Software 用 `apply_patch` 创建以下文件，不用 shell write trick：

- `artifacts/robot-software/frozen_identity.json`
- `artifacts/robot-software/frozen_requests.json`
- `artifacts/robot-software/phase0_deployment_manifest.json`

identity 必须包含本文件 metadata 的五个 id、`target_commit`、source host、fixed goal、operator watch、route clear、physical limit、bounded motion authorized、`no_retry=true`。Requests 必须固定 Phase A/B body 和 forbidden invocation=`0`。

### 0.2 可复制的本地目标与回归命令

```bash
cd /Users/m1/apps/rober
TARGET_COMMIT=85ba7308785aa3c4033180a097e3d388358a97de
test "$(git rev-parse HEAD)" = "$TARGET_COMMIT"
test "$(git show "$TARGET_COMMIT":onboard/scripts/upper_robot_api.py | shasum -a 256 | awk '{print $1}')" = "8c0f6eebb786e1cd6b1cb5d17485e59972140bf76a94e7669773ef438228b4c3"
test "$(git show "$TARGET_COMMIT":onboard/scripts/o10_amcl_nav2_runtime_proof.py | shasum -a 256 | awk '{print $1}')" = "d9f92d708bdac6feec35798e4acfcd50b58349a3de3315a24a605cf5c82307eb"
git diff --quiet "$TARGET_COMMIT" -- onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_runtime_proof_parent_absolute_deadline_starts_before_popen
python3 -m unittest onboard/tests/test_upper_robot_api.py
python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py
python3 -m unittest onboard/tests/test_upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py
```

任一失败必须先定位并在对应 owner 范围最小修复、重跑 targeted/full。若代码偏离 target commit，则本轮部署目标不再成立，Phase A invocation=`0`，先由 Product 确认新 target；不得静默部署未冻结代码。

### 0.3 可复制的 remote preflight/deploy/restart/health 命令

先只读取证，保存 `phase0_remote_pre.raw.txt`：

```bash
ssh -p 37878 root@192.168.1.11 'set -eu; cd /root/rober; (git rev-parse HEAD || true); sha256sum onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py; systemctl is-active trashbot-upper-robot-api.service; curl -fsS http://127.0.0.1:8787/api/health; curl -fsS http://127.0.0.1:8787/api/status; curl -fsS http://127.0.0.1:8787/api/nav2/status'
```

从已验证的本地 target HEAD 部署两份脚本到临时路径，远端编译与 SHA 通过后再原子替换；不得直接交互式编辑远端：

```bash
scp -P 37878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py.codex-85ba7308785aa3c4.py
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py.codex-85ba7308785aa3c4.py
ssh -p 37878 root@192.168.1.11 'set -eu; cd /root/rober; python3 -m py_compile onboard/scripts/upper_robot_api.py.codex-85ba7308785aa3c4.py onboard/scripts/o10_amcl_nav2_runtime_proof.py.codex-85ba7308785aa3c4.py; test "$(sha256sum onboard/scripts/upper_robot_api.py.codex-85ba7308785aa3c4.py | awk '\''{print $1}'\'')" = "8c0f6eebb786e1cd6b1cb5d17485e59972140bf76a94e7669773ef438228b4c3"; test "$(sha256sum onboard/scripts/o10_amcl_nav2_runtime_proof.py.codex-85ba7308785aa3c4.py | awk '\''{print $1}'\'')" = "d9f92d708bdac6feec35798e4acfcd50b58349a3de3315a24a605cf5c82307eb"; install -m 0644 onboard/scripts/upper_robot_api.py.codex-85ba7308785aa3c4.py onboard/scripts/upper_robot_api.py; install -m 0755 onboard/scripts/o10_amcl_nav2_runtime_proof.py.codex-85ba7308785aa3c4.py onboard/scripts/o10_amcl_nav2_runtime_proof.py; rm -f onboard/scripts/upper_robot_api.py.codex-85ba7308785aa3c4.py onboard/scripts/o10_amcl_nav2_runtime_proof.py.codex-85ba7308785aa3c4.py; python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py; systemctl restart trashbot-upper-robot-api.service'
```

服务重启允许只读 health poll 等待 listener ready，但不得进入 Phase A 试探。最终硬门命令：

```bash
ssh -p 37878 root@192.168.1.11 'set -eu; cd /root/rober; test "$(sha256sum onboard/scripts/upper_robot_api.py | awk '\''{print $1}'\'')" = "8c0f6eebb786e1cd6b1cb5d17485e59972140bf76a94e7669773ef438228b4c3"; test "$(sha256sum onboard/scripts/o10_amcl_nav2_runtime_proof.py | awk '\''{print $1}'\'')" = "d9f92d708bdac6feec35798e4acfcd50b58349a3de3315a24a605cf5c82307eb"; systemctl is-active --quiet trashbot-upper-robot-api.service; curl -fsS http://127.0.0.1:8787/api/health; curl -fsS http://127.0.0.1:8787/api/status; curl -fsS http://127.0.0.1:8787/api/nav2/status'
```

`phase0_deployment_manifest.json` 必须记录 remote Git SHA（可用时）、目标 commit、两脚本 pre/temp/post SHA、remote py_compile、service PID/restart/health、初始 lifecycle/existing motion 与每条命令 exit。Phase A 前硬门为两份 post SHA 精确匹配、remote compile/service/health clean；远端 Git SHA 若可作为部署版本来源也必须等于 target。任一不满足时 Phase A count=`0`。

## Phase A - exactly-once current strict-no-motion

以下 block 只能由唯一 live owner 执行一次，不能整块重贴。每个 response raw 与 transport metadata 都写入 `artifacts/robot-software/`，最终由 `phase_a_invocation_manifest.json` 汇总 SHA256、timestamp、exit、HTTP、parse、semantic 与 count。

```bash
ssh -p 37878 root@192.168.1.11 "curl -fsS --max-time 30 -X POST http://127.0.0.1:8787/api/nav2/start -H 'Content-Type: application/json' --data-binary @-" <<'JSON'
{"strict_no_motion":true,"base_enabled":false,"lidar_enabled":false,"reuse_existing_scan":true,"timeout_s":20}
JSON
ssh -p 37878 root@192.168.1.11 "curl -fsS --max-time 95 -X POST http://127.0.0.1:8787/api/nav2/proof/refresh -H 'Content-Type: application/json' --data-binary @-" <<'JSON'
{"timeout_s":30,"managed_runtime_opt_in":false,"managed_timeout_s":30,"managed_map_yaml":"","initialpose_opt_in":false,"path_generation_opt_in":true,"path_generation_timeout_s":30,"path_goal_frame_id":"map","path_goal_x":0.8,"path_goal_y":0.25,"path_goal_yaw":0.0}
JSON
ssh -p 37878 root@192.168.1.11 'curl -fsS http://127.0.0.1:8787/api/nav2/proof/latest; curl -fsS http://127.0.0.1:8787/api/nav2/status; curl -fsS http://127.0.0.1:8787/api/status'
```

`readiness_assertion.json` 必须明确：

- `READINESS_GO=true|false` 与 exact blockers；
- target commit 与 remote SHA hard gate；
- current natural final、absolute deadline source/shared deadline/remaining wait、`artifact_kind=final`、`last_phase=final`、`current_command=null`；
- current AMCL pose、persisted pose audit、dynamic `map->odom` freshness/unique attribution、`map->base_link`；
- map/amcl/planner/controller active；
- path requested/attempted/succeeded/generated、point count、goal `(0.8,0.25,0)`；
- obstacle clear、existing motion false、fresh authorization；
- `initialpose_publish_attempts=0`、base/LiDAR new-open=`0/0`；
- start/proof/latest=`1/1/1`，goal/manual/cmd_vel/UART=`0`。

任一 missing/unknown/stale/conflict/timeout/partial/fallback/non-final 均为 NO-GO。NO-GO 只执行一次：

```bash
ssh -p 37878 root@192.168.1.11 "curl -fsS -X POST http://127.0.0.1:8787/api/nav2/stop -H 'Content-Type: application/json' --data-binary '{}'"
```

随后只读确认 lifecycle stopped、PID/process-group/owned residual=`0`，封存 Phase A；pre-base-stop/goal/post-base-stop=`0/0/0`，不得同窗修复后重跑。

## Phase A frozen -> Algorithm handoff

Algorithm 允许读取 frozen artifacts；允许范围：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/fixed_route_workflow.md`
- 本 sprint `artifacts/algorithm/**`

它不得 SSH/live/retry。输出 `artifacts/algorithm/readiness_review.json`，明确同意/拒绝 `READINESS_GO`、deadline validation、exact blockers 和 no-retry。可复制验收命令：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py
python3 -m json.tool sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/artifacts/algorithm/readiness_review.json >/dev/null
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/fixed_route_workflow.md sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route
```

若 review 发现 helper bug，Algorithm 在范围内最小修复、运行 targeted/full、更新 navigation doc；本授权窗口保持 sealed，不部署、不重跑，下一 live 必须新授权。

## Phase B - conditional pre-stop + exactly-one route + post-stop

仅 `READINESS_GO=true` 且 Algorithm frozen review 接受时，由同一个 Robot Software owner 继续。先恰好一次 pre-stop：

```bash
ssh -p 37878 root@192.168.1.11 "curl -fsS -X POST http://127.0.0.1:8787/api/base/stop -H 'Content-Type: application/json' --data-binary '{}'"
```

pre-stop HTTP/semantic/feedback/readback 任一不 clean：goal=`0`、post-base-stop=`0`，执行一次 owned `/api/nav2/stop` 后封存 `phase_b_invocation_manifest.json`，不得重试。

只有 pre-stop clean 才 exactly once 执行：

```bash
ssh -p 37878 root@192.168.1.11 "curl -fsS --max-time 35 -X POST http://127.0.0.1:8787/api/nav2/goal/execute -H 'Content-Type: application/json' --data-binary @-" <<'JSON'
{"confirm_navigation_execution":true,"goal_frame_id":"map","goal_x":0.8,"goal_y":0.25,"goal_yaw":0.0,"base_command_mode":"ros","managed_runtime_opt_in":false,"result_timeout_s":20,"server_timeout_s":12,"task_id":"task_o3_28_pose_fixed_route_consumer_20260713_0402","run_id":"run_o3_o1_current_readiness_route_20260720_2124_01","route_intent_id":"route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path","authorization_ref":"ceo_20260720_2124_operator_watch_route_clear_physical_limit_v2","action_id":"action_o3_o1_bounded_nav_20260720_2124_01"}
JSON
```

不论 success/fail/timeout/unknown，禁止第二次 execute。随后最多一次 post-stop，再只读 terminal/feedback/status，最后一次 owned cleanup：

```bash
ssh -p 37878 root@192.168.1.11 "curl -fsS -X POST http://127.0.0.1:8787/api/base/stop -H 'Content-Type: application/json' --data-binary '{}'"
ssh -p 37878 root@192.168.1.11 'curl -fsS http://127.0.0.1:8787/api/nav2/goal/execution/latest; curl -fsS http://127.0.0.1:8787/api/base/feedback-samples/latest; curl -fsS http://127.0.0.1:8787/api/status'
ssh -p 37878 root@192.168.1.11 "curl -fsS -X POST http://127.0.0.1:8787/api/nav2/stop -H 'Content-Type: application/json' --data-binary '{}'"
```

`phase_b_invocation_manifest.json` 固定记录 execute=`0|1`、pre_base_stop=`1`、post_base_stop=`0|1`、nav2_owned_stop=`1`、no-retry=true、terminal class、remote residual=`0`；manual/free-roam/direct cmd_vel/initialpose/UART direct/delivery=`0`。base stop 与 Nav2 lifecycle stop 分开计数。

## Phase B frozen -> Hardware handoff

仅 execute=`1` 且 Phase B 全部 frozen 后派 Hardware。先读：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`

允许范围：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_bounded_route_hil_evidence.py`
- `docs/hardware/wave_rover_bounded_route_hil_evidence.md`
- 本 sprint `artifacts/hardware/**`

只读校验 vendor `FEEDBACK_BASE_INFO=1001`、`L/R/r/p/y/v`、pre/motion/post-stop 同窗 lineage；不得发任何 live/stop/UART 命令。可复制验收：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py
python3 -m unittest onboard.src.ros2_trashbot_hardware.test.test_wave_rover_bounded_route_hil_evidence
python3 -m json.tool sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/artifacts/hardware/wave_rover_hil_evidence.json >/dev/null
git diff --check -- onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_bounded_route_hil_evidence.py docs/hardware/wave_rover_bounded_route_hil_evidence.md sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route
```

`T=1001` 存在不等于 L/R 非零、轮向正确、HIL pass 或 safe-to-control；必须由同窗结构证据逐项判定。

## Robot Software 文件范围与验收

允许：

- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/field_route_evidence_preflight.md`
- 本 sprint `artifacts/robot-software/**`
- 本 sprint `tech-done.md`

部署 O10 target 文件是 live integration 动作，不授权 Robot Software 修改 Algorithm 文件。若 Phase A 暴露 Upper API integration bug，只能在上述范围修复、补中文注释、同步 docs、跑 targeted/full；同窗不重跑。

最终可复制验收：

```bash
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard/tests/test_upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py
python3 -m json.tool sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/artifacts/robot-software/frozen_identity.json >/dev/null
python3 -m json.tool sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/artifacts/robot-software/frozen_requests.json >/dev/null
python3 -m json.tool sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/artifacts/robot-software/phase0_deployment_manifest.json >/dev/null
python3 -m json.tool sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/artifacts/robot-software/phase_a_invocation_manifest.json >/dev/null
python3 -m json.tool sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/artifacts/robot-software/readiness_assertion.json >/dev/null
rg -n '85ba7308785aa3c4033180a097e3d388358a97de|ceo_20260720_2124_operator_watch_route_clear_physical_limit_v2|run_o3_o1_current_readiness_route_20260720_2124_01|READINESS_GO|no.retry|remote.*sha|0.8|0.25' sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/artifacts/robot-software
git diff --check -- onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py docs/navigation/field_route_evidence_preflight.md sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route
```

Phase B 发生时追加 `python3 -m json.tool .../phase_b_invocation_manifest.json`；Phase A NO-GO 时必须断言该文件 absent 且 Phase A manifest 中 Phase B counts 全为 `0`。所有新增/修改代码的技术注释必须为中文；按 strict added-nonblank-line 口径分别审计 owner 文件，中文技术注释或中文 docstring 行 / 新增非空代码行必须严格 `>20%`。

## Full-stack 条件例外范围

默认不派。只有 frozen route terminal 触发既有 receipt contract 真实 bug 时允许：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/product/pc_tools_workstation.md`
- 本 sprint `artifacts/full-stack/**`

只做最小修复与 workstation test/build/lint；不得 SSH/control、新 endpoint、wrapper 或 mock success。

## 失败修复、NO-GO 与 cleanup 规则

- Phase 0 fail：只允许在 Phase A invocation=`0` 时修部署/health 并复验硬门；不能跳过 SHA。
- Phase A fail/NO-GO：一次 owned cleanup，冻结 exact blocker；可离线修 code/test/doc，但不得同窗 retry。
- pre-stop fail：execute=`0`、post-stop=`0`、一次 owned cleanup，冻结；不得第二次 pre-stop。
- execute fail/timeout/unknown：execute 已消费，禁止 retry；最多一次 post-stop，然后 read-only + owned cleanup。
- cleanup residual 非零：安全事件优先，只允许停止 owner 已创建的 PID/process group；不得用新 start/proof/goal 补救，最终如实 blocked。
- 任一 owner 首轮测试失败必须定位、修复、重跑 targeted/full；不得把第一轮失败直接交差。

## Proof boundary 与 Product credit

- Phase 0：`deployment_verified_only`，Mission credit=`false`。
- Phase A NO-GO：`current_readiness_diagnostic_only`，route/user-action/HIL/delivery/safe=`false`。
- GO + pre-stop + execute accepted：`mission_attempt` / user-action candidate，不等于 route success。
- same-lineage terminal success：route success candidate。
- route success + same-window pre/post stop + valid T=1001 motion/post-stop + operator outcome：HIL/operator candidate。
- `delivery_success=false` 固定；`safe_to_control=false` 默认。Product final 才能判断 OKR，不能由 Engineer manifest 自行抬分或归档 KR。

## 本轮 planning 验收命令

```bash
rg -n 'sprint_type: epic|ceo_20260720_2124_operator_watch_route_clear_physical_limit_v2|run_o3_o1_current_readiness_route_20260720_2124_01|85ba7308785aa3c4033180a097e3d388358a97de|READINESS_GO|exactly|NO-GO|T=1001|OKR 最低优先级核对|robot-software-engineer|robot-algorithm-engineer|robot-hardware-engineer|root@192.168.1.11:37878|0.8|0.25' sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/{pre_start.md,prd.md,tech-plan.md}
test ! -e sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/tech-done.md && test ! -e sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/side2side_check.md && test ! -e sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/final.md
git diff --check -- sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route
git status --short -- sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route
```
