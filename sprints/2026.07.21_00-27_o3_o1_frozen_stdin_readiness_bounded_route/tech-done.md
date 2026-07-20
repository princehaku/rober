# O3/O1 Frozen Stdin Readiness + Bounded Route - Tech Done

## Sprint metadata

- `sprint_type: epic`
- owner：`robot-software-engineer`
- 状态：`phase-a-natural-final-no-go-clean-sealed`
- target commit：`af08e6545819758b1b3e6127903d55d5664fa93a`
- authorization：`ceo_20260721_0025_operator_watch_route_clear_physical_limit_v4`
- run：`run_o3_o1_frozen_stdin_readiness_route_20260721_0025_01`
- action：`action_o3_o1_bounded_nav_20260721_0025_01`
- `PHASE0_GATE=PASS`
- `AUTHORIZATION_CONSUMED=yes`
- Phase A start/proof/latest/owned-stop：`1/1/1/1`
- Phase B pre-base-stop/goal/post-base-stop：`0/0/0`
- `READINESS_GO=false`
- `physical_motion=false`
- final state：`NO_GO_CLEAN`
- proof boundary：`current_live_frozen_stdin_transport_validated_natural_final_readiness_no_go_owned_cleanup_no_route`

## 实际改动

本轮优先使用安全 shell stdin pipeline 完成现场验证，没有修改产品代码或测试代码：

- `onboard/scripts/upper_robot_api.py`：无改动；live target SHA 为
  `8c0f6eebb786e1cd6b1cb5d17485e59972140bf76a94e7669773ef438228b4c3`。
- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`：无改动；live target SHA 为
  `d9f92d708bdac6feec35798e4acfcd50b58349a3de3315a24a605cf5c82307eb`。
- 两份直接测试文件：无改动。
- `artifacts/robot-software/frozen_identity.json`、`frozen_requests.json`：冻结 fresh authorization、
  run/action/task/route lineage、target host/commit、fixed goal、operator/route/physical-limit、no-retry、
  endpoint counts 与 forbidden counts。
- `artifacts/robot-software/*.compact.json`：从 frozen request 对应 body 形成的单行 canonical transport
  material；所有 body 都与 `jq -c` 实时提取结果 SHA/byte/line/cmp 一致。
- `artifacts/robot-software/phase0/**`：保存 remote Git provenance、两脚本 SHA、py_compile、service、
  health/status/Nav2 status、初始 PID file 与精确 owner process inventory raw。
- `artifacts/robot-software/phase_a/**`：保存 start/proof/latest/owned-stop 和 cleanup 的 raw response、
  HTTP、curl exit、stderr；raw 均先落远端并下载，再解析。
- `phase_a_invocation_manifest.json`、`readiness_decision.json`、`attempt_counts.json`、`cleanup.json`：
  固化 transport、endpoint/SSH/curl/HTTP、bytes/hash/parse/semantic、handler、open/motion、deadline、
  natural final、readiness、exact counts 与 cleanup 结论。
- `docs/navigation/field_route_evidence_preflight.md`：把示例 key 修正为实际 `.phase_a_start`，并新增
  本轮 live stdin transport/natural-final/NO-GO/cleanup 边界。
- 本 `tech-done.md`：记录真实执行、验证、风险和条件协同。

新增代码中文技术注释比例：`not_applicable_no_product_or_test_code_change`。本轮只有 JSON artifact 与中文
文档变更，不制造产品代码 churn。

## Vendor 资料来源与硬件边界

本轮开工前重新核对：

- `docs/vendor/VENDOR_INDEX.md`：WAVE ROVER 以 UART newline-delimited JSON 通信，硬件参数不得凭记忆猜测；
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`：`FEEDBACK_BASE_INFO=1001`，底盘速度
  命令为 `T=1`，ROS 速度命令为 `T=13`；
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`：`T=1/T=13/T=130/T=131` 的 firmware
  handler 映射；
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`：`T=1001` 的 `L/R/r/p/y/v`
  feedback 字段；
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`：UTF-8 JSON + newline 串口 framing 与 `T=1`
  left/right speed reference。

Phase A strict start 的 effective contract 明确 `base_enabled=false`、`lidar_enabled=false`，new-open=`0/0`；
owned Nav2 stop 明确 `sends_base_stop_command=false`、`uses_base_uart=false`。Phase B 没有解锁，所以本轮没有
发送 `T=1/T=11/T=13`，没有采集 current `T=1001`，也没有 HIL 结论。

## 离线验证

按计划顺序执行，全部通过：

```text
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0

python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_runtime_proof_parent_absolute_deadline_starts_before_popen
Ran 1 test in 0.002s
OK

python3 -m unittest onboard/tests/test_upper_robot_api.py
Ran 119 tests in 0.264s
OK (skipped=1)

python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py
Ran 170 tests in 2.468s
OK

python3 -m unittest onboard/tests/test_upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py
Ran 289 tests in 2.670s
OK (skipped=1)
```

没有离线失败，也没有需要产品代码修复的回归。上一轮 transport blocker 的修复入口不是新代码，而是本轮
冻结 request + `jq -c` + stdin pipe 的安全执行方式。

## Frozen request 验证

`frozen_identity.json`、`frozen_requests.json` 与每个 compact body 均通过 `python3 -m json.tool`；identity、
fixed goal、authorization/run/action/task/route、host/commit、`no_retry=true`、9 个 endpoint expected count
和全部 forbidden count=`0` 通过 `jq -e`。

关键 body 结果：

| body | SHA-256 | bytes | lines | `jq -c` source cmp |
|---|---|---:|---:|---|
| `phase_a_start` | `a6f2e1ee...d9bc` | `111` | `1` | pass |
| `phase_a_proof` | `eaa666cc...e9b` | `265` | `1` | pass |
| `phase_a_owned_stop` | `ca3d163b...356` | `3` | `1` | pass |
| `phase_b_goal`（未发送） | `fe13b812...7869` | `564` | `1` | pass |

Phase B pre/post stop 与 owned cleanup 的 `{}` body 同样为 `ca3d...2356`、`3` bytes、`1` line、cmp pass。
所有实际 Phase A POST 都是本地 `jq -c` 输出经 stdin 到远端 `curl --data-binary @-`；没有 inline JSON、
heredoc body 或远端变量拼 JSON。

## Phase 0 部署与安全硬门

Phase 0 没有调用 start/proof/goal/control，authorization 尚未消费。结果：

- remote Git metadata 不可用，仅记为 provenance，不作为部署身份；
- remote Upper/O10 pre SHA 已分别精确等于本地已验证 SHA，因此 `deploy=false`、`restart=false`；
- remote `py_compile` exit `0`；
- `trashbot-upper-robot-api.service` active/running，PID=`1221`；
- `/api/health`、`/api/status`、`/api/nav2/status` 均 curl exit `0`、HTTP `200`、JSON parse clean；
- health `status=ready`；initial lifecycle `running=false`、`state=stopped`、PID null；
- owned PID files=`0`、精确 Python owner residual process=`0`、`robot_control_executed=false`。

因此 `PHASE0_GATE=PASS`，才进入唯一 Phase A。

## Phase A exactly-once 真实执行

### Start transport

`phase_a_start` stdin pipe 发出时 fresh authorization 立即消费。唯一结果：

- local pipeline/SSH/curl exit=`0/0/0`，HTTP `200`，raw=`43080` bytes，SHA
  `cf63421e...2bc6`，JSON parse clean；
- remote handler invocation=`1`，lifecycle command executed/ok=`true/true`；
- `status=started_strict_no_motion`、`semantic_success=true`；
- effective contract `base_enabled=false`、`lidar_enabled=false`，owned PID=`5344`；
- base UART/LiDAR new-open=`0/0`，`physical_motion=false`。

这真实板关闭了上一轮 `phase_a_start_json_transport_corrupted_before_remote_handler`；HTTP `200` 并非单独
成功依据，结论依赖 parse、request consumed、handler、semantic 与 lifecycle readback 全部成立。

### Proof natural final 与 canonical latest

唯一 `/api/nav2/proof/refresh`：

- local pipeline/SSH/curl exit=`0/0/0`，HTTP `200`，raw=`394807` bytes，SHA
  `a3317371...2e3f`，JSON parse clean；
- helper executed=true、returncode=`2`、status=`blocked_with_root_cause`；这是语义 NO-GO，不是 transport
  或 process timeout；
- elapsed=`79587ms`、`deadline_source=parent_absolute_monotonic`、outer budget=`80s`、remaining wait
  `79.99781858999995s`；
- natural artifact 为 `artifact_kind=final`、`last_phase=final`、`current_command=null`、
  `partial_artifact_preserved=false`，finalization reason=`budget_reserve_reached_before_noncritical_command`；
- base/LiDAR new-open=`0/0`、`physical_motion=false`。

随后唯一 GET `/api/nav2/proof/latest` curl/HTTP=`0/200`，raw=`376509` bytes、parse clean。Proof response 与
canonical latest 的 `latest_result` 经 canonical JSON 计算后 SHA 均为
`7dacf37534d81dfcdba4c37641b045b6aa2f5ffc526ca055e37210a9ab474c32`，且
`generated_at_ms=1784566573168` 相同，因此 `same_current=true`、`natural_final=true`。

### READINESS_GO 决策

`READINESS_GO=false`，因为必须全绿的子门仍存在以下 false/missing/conflict：

- map lifecycle active，但 canonical map proof 不 clean、`/map_once_not_observed`；
- AMCL active，末段 `amcl_pose_observed=true`，但 current pose timestamp/freshness 未通过，persisted pose
  `audited=false`、`persisted_pose_live_consumed=false`；
- planner/controller active=`false/false`；
- dynamic `map->odom`、unique AMCL attribution、`map->base_link` 均 false，TF blocked reason
  `/tf_topic_missing`；
- path requested=true，但 attempted/succeeded/generated=`false/false/false`、point count=`0`，fixed goal 未
  materialize；
- current obstacle-clear 未证明，status 只含 stale scan proof，历史 readback
  `lidar_min_distance_m=0.03500000014901161` 不能作为 current clear gate。

任一项已足以 NO-GO。本轮没有补调用、修复后重跑或使用旧 nested success。

### Owned stop 与 cleanup

唯一 `/api/nav2/stop` stdin POST：local pipeline/SSH/curl=`0/0/0`，HTTP `200`，raw=`37723` bytes、parse
clean，`status=stopped_owned_process_group`、semantic success=true。随后只读 cleanup readback：

- lifecycle `running=false`、`state=stopped`、PID null；
- start PID `5344` 不存在；owned PID files=`0`；精确 owner residual process=`0`；
- `/api/status` 与 `/api/nav2/status` HTTP `200`、parse clean、`robot_control_executed=false`；
- cleanup scope 仅 `o11_owned_pid_process_group_only`，没有 broad kill；
- `final_state=NO_GO_CLEAN`。

## Phase B、运动、T=1001 与成功边界

由于 `READINESS_GO=false`，Phase B 未解锁：

- pre-base-stop/goal/post-base-stop=`0/0/0`；
- terminal/feedback/status Phase B readback=`0/0/0`；
- Phase B owned cleanup=`0`（Phase A owned stop 已为 `1`）；
- goal retry=`0`，所有 retry=`0`；
- `/initialpose`、manual、free-roam、direct `/cmd_vel`、direct UART、delivery=`0`；
- current-run `T=1001` sample=`0`，不得借历史反馈；
- `physical_motion=false`、`robot_control_executed=false`；
- `route_execution_success=false`、`hil_pass=false`、`delivery_success=false`、`safe_to_control=false`。

本轮只证明：frozen stdin transport 已真实板通过、strict start 进入 handler、proof 能自然生成 current final、
readiness 诚实 NO-GO 且 owned cleanup clean。它不证明 route execution、user action、HIL、delivery、
safe-to-control 或 Mission Objective 0 完成。

## 最终结构验证

最终至少执行：

- 全部 frozen/manifest/decision/count/cleanup/raw JSON `python3 -m json.tool`；
- request identity/count、body SHA/byte/line/cmp、Phase A exact counts、Phase B zero counts；
- `READINESS_GO` fail-closed 结构、same-current/natural-final hash/timestamp；
- cleanup lifecycle stopped/PID null/residual `0`；
- required contract `rg`；
- scoped `git diff --check`。

实际结果：全部 JSON parse、identity/count/body hash/byte/line/cmp、Phase 0、Phase A exact counts、
Phase B zero counts、same-current/natural-final、readiness false gates、cleanup clean、required `rg`、
`side2side_check.md`/`final.md` absent 与 scoped `git diff --check` 均通过，最终输出
`final_structural_validation=pass`。没有重开 live window或重发任何 endpoint。

## 失败定位、剩余风险与协同

失败定位：离线/transport/Phase 0/start/cleanup 均无失败；唯一 NO-GO 是 current readiness semantic 不满足，
主要 blocker 是 current map/scan、pose freshness/persisted pose、dynamic TF、planner/controller、path 和
obstacle-clear 未全绿。依 no-retry 合同，本授权窗口已经封存，不能同窗修复重跑。

剩余风险：

- current pose 顶层 observed 与 persisted audit 的 pre-publish sample/freshness 存在冲突，必须由 Algorithm
  对 frozen current final 只读判定，不能由后续历史 readback洗白；
- map/scan 与 TF 仍不足，planner/controller/path 未激活；
- obstacle clear 没有 current clean evidence；
- 没有 Phase B，故底盘 stop feedback、current `T=1001`、wheel direction、HIL/operator、route terminal
  与 delivery 全未覆盖；
- 本 fresh authorization 已消费，任何新的 live start/proof/goal 都需要下一次 fresh authorization。

协同触发：

- `robot-algorithm-engineer`：已触发条件，因为 same-current natural final 已形成；只允许 frozen artifact
  read-only review，不得 SSH/live/retry/control；
- `rober-hardware-engineer`：不触发，因为 Phase B execute=`0`、current `T=1001`=`0`；
- `full-stack-software-engineer`：不触发，本轮无触点合同问题；
- `product-okr-owner`：Engineer 留档完成后触发 Product acceptance/closeout；百分比与 KR 由 Product 保守
  判定，本文件不修改 `OKR.md`、progress log、`side2side_check.md` 或 `final.md`。
