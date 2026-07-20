# O3/O1 Live Deadline Fix Validation + Bounded Route - Tech Done

## Sprint metadata

- `sprint_type: epic`
- owner：`robot-software-engineer`
- 状态：`phase-a-no-go-sealed`
- `PHASE0_GATE=PASS`
- `PHASE_A_CONSUMED=yes`
- `READINESS_GO=false`
- Phase B：`not_executed`
- proof boundary：`live_absolute_deadline_natural_final_but_phase_a_no_go_start_transport_corrupted_owned_cleanup_only`
- target commit：`85ba7308785aa3c4033180a097e3d388358a97de`
- authorization：`ceo_20260720_2124_operator_watch_route_clear_physical_limit_v2`
- run：`run_o3_o1_current_readiness_route_20260720_2124_01`

## 实际改动

本轮没有修改产品代码或测试代码，`onboard/scripts/upper_robot_api.py`、
`onboard/scripts/o10_amcl_nav2_runtime_proof.py` 与两份测试文件保持 target commit 内容，属于
`no-code-churn`。实际变更为：

- 在 `artifacts/robot-software/` 冻结 identity、Phase A/B request、Phase 0 deployment manifest，
  保存 Phase 0 pre/post raw 与 transport、Phase A start/latest/status/stop/cleanup raw 与 transport，
  并生成 `phase_a_invocation_manifest.json` 与 `readiness_assertion.json`。
- 更新 `docs/navigation/field_route_evidence_preflight.md`，新增 exactly-once live JSON 防复发合同：
  从已验证的 `frozen_requests.json` 用 `jq -c` 提取单个 object，经 stdin 原样 pipe 到远端
  `curl --data-binary @-`，禁止多层 shell inline JSON。
- 创建本 `tech-done.md`，如实记录 Phase 0/A、NO-GO、cleanup、证据缺口和 handoff。

所有仓库文件均通过 `apply_patch` 创建或更新；远端只部署经过本地 target SHA 验证的脚本临时文件，
远端 py_compile/SHA 通过后以同文件系统 rename 原子替换，没有交互式编辑远端文件。

## Phase 0 部署硬门

本地硬门全部通过：

| 验收 | 结果 |
|---|---|
| HEAD 等于 target commit | exit `0` |
| target Upper SHA | `8c0f6eebb786e1cd6b1cb5d17485e59972140bf76a94e7669773ef438228b4c3` |
| target O10 SHA | `d9f92d708bdac6feec35798e4acfcd50b58349a3de3315a24a605cf5c82307eb` |
| `py_compile` | exit `0` |
| parent absolute-deadline targeted | `Ran 1 test`，`OK` |
| Upper full | `Ran 119 tests`，`OK (skipped=1)` |
| O10 full | `Ran 170 tests`，`OK` |
| combined | `Ran 289 tests`，`OK (skipped=1)` |

远端 preflight 发现 `/root/rober` 没有可用 Git metadata，因此 manifest 明确记录
`remote_git_commit_unavailable_or_not_authoritative`；实际部署权威使用两份 target content SHA、remote
py_compile、service 与 health：

| 文件 | pre SHA | temp/post SHA |
|---|---|---|
| `upper_robot_api.py` | `df7a71c662a074c6e9eecb1523f7daf7ce78a33507193e3779192fc61a71461a` | `8c0f6eebb786e1cd6b1cb5d17485e59972140bf76a94e7669773ef438228b4c3` |
| `o10_amcl_nav2_runtime_proof.py` | `2ecdbb977ae1a211e4f6af3555d7f623f12f1bf2a161d10cf9443c3538af3fa2` | `d9f92d708bdac6feec35798e4acfcd50b58349a3de3315a24a605cf5c82307eb` |

两份 remote temp/post `py_compile` exit `0`，两份 SHA 断言 exit `0`。service restart exit `0`，旧
MainPID=`689027`，新 MainPID=`693117`，`ActiveState=active`、`SubState=running`，active since
`2026-07-20 21:48:44 CST`。post health 在 `2026-07-20 21:49:00.761 CST` 返回 HTTP `200`、
`status=ready`；status/nav2 status HTTP `200` 且 JSON parse clean，初始 Nav2 lifecycle stopped、PID
null、`robot_control_executed=false`。因此 `PHASE0_GATE=PASS`。

restart 总等待约 79 秒，表现为 systemd 等待旧服务停止；它最终自然 exit `0`，不是 SHA、compile、
service active 或 health 硬门失败。

## Phase A exactly-once 结果

### 调用计数与失败定位

| endpoint | 方法 | count | exit / HTTP / parse | 语义 |
|---|---:|---:|---|---|
| `/api/nav2/start` | POST | `1` | `0 / 200 / true` | `blocked_strict_no_motion_contract` |
| `/api/nav2/proof/refresh` | POST | `1` | `0 / 200 / unknown` | `blocked_with_root_cause`，自然 final |
| `/api/nav2/proof/latest` | GET | `1` | `0 / 200 / true` | `not_proven` |
| `/api/nav2/status` after proof | GET | `1` | `0 / 200 / true` | lifecycle stopped |
| `/api/status` after proof | GET | `1` | `0 / 200 / true` | unified current readback |
| `/api/nav2/stop` | POST | `1` | `0 / 200 / true` | `stopped_owned_process_group` |
| `/api/nav2/status` after stop | GET | `1` | `0 / 200 / true` | lifecycle stopped、PID null |

`/api/nav2/start` 的 endpoint 已被调用一次，授权窗口因此已消费。响应 raw 显示 Upper API 收到的 body
不是 JSON object：`failure_reason=invalid_nav2_start_json`，JSON decoder 在 line 1 column 2 失败；
remote start command `executed=false`、`invocation_count=0`，没有启动 lifecycle，base UART/LiDAR serial
open=`0/0`，motion=false。根因是 client 把内联 JSON 嵌在多层本地/SSH shell 引号中，属性名双引号在
到达远端 curl 前被剥离。依 no-retry 合同没有第二次 start；文档已改为 frozen request + `jq -c` +
stdin 原样传输模式，只做离线结构验收，没有重发 live。

start semantic failure 已足以锁定 NO-GO。仍按冻结合同完成唯一 proof/latest/status 诊断，没有把 proof
当成 start retry。proof wrapper 在 `77717ms` 自然返回 HTTP `200`，helper returncode=`2` 表示诚实
blocked，不是 process timeout：

- `artifact_kind=final`
- `last_phase=final`
- `current_command=null`
- `partial_artifact_preserved=false`
- `deadline_source=parent_absolute_monotonic`
- `outer_process_timeout_s=80.0`
- `process_wait_timeout_s=79.99757383600809`
- parent/helper 共用 absolute monotonic deadline；startup budget consumption=`3.107847494073212s`
- helper final `generated_at_ms=1784555573480`，即 `2026-07-20 21:52:53.480 CST`

这是真实板对 absolute deadline fix 的 natural-final 验证，证明上一 sprint 的
`parent_helper_monotonic_clock_origin_mismatch` 已不再把 helper 截成 partial/fallback；它不等于
readiness GO。

### READINESS_GO fail-closed

`READINESS_GO=false`。除了 start transport corruption 与 lifecycle stopped，current final 还明确显示：

- map_server/amcl/planner_server/controller_server active=`false/false/false/false`；
- current AMCL pose 未观测，persisted pose 未 live consumed；
- dynamic `map->odom` 未观测、无 timestamp/freshness/unique AMCL attribution，`map->base_link=false`；
- `initialpose_publish_attempts=0`；
- path requested=`true`，attempted/succeeded/generated=`false/false/false`，point count=`0`，fixed goal
  request 未 materialize；
- current status 仍读到 `lidar_min_distance_m=0.03500000014901161` 且 latest scan proof stale，obstacle
  clear 未证明；
- existing motion=false、robot control=false、physical motion=false。

任一字段已足以 NO-GO；因此没有修复后重跑，没有进入 Phase B。

## NO-GO cleanup 与 Phase B 缺席

NO-GO 后只调用一次 owned `/api/nav2/stop`，HTTP `200`、JSON parse true、
`status=stopped_owned_process_group`。stop readback 与后续只读 status 都是 lifecycle stopped、PID null。
`/tmp/rober_nav2_lifecycle/nav2.pid`、`nav2_lifecycle.pid` 均 absent，helper PID `694056` absent，严格
owned runtime process scan 无匹配，`residual_count=0`。

Phase B artifact 明确 absent，counts 固定：

- pre-base-stop/goal/post-base-stop=`0/0/0`
- Phase B terminal/feedback/status GET=`0/0/0`
- Phase B owned Nav2 stop=`0`
- `/initialpose`、manual、free-roam、direct `/cmd_vel`、UART、`T=1`、`T=11`、`T=13`、`T=1001`、
  delivery=`0`
- `physical_motion=false`

因此 `route_execution_success=false`、`hil_pass=false`、`delivery_success=false`、
`safe_to_control=false`、`okr_credit=false`。

## 验证结果

最终验证：

```text
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0

python3 -m unittest onboard/tests/test_upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py
Ran 289 tests in 2.713s
OK (skipped=1)
exit 0

frozen start body: python3 -m json.tool + jq structural assertion + stdin JSON parse
frozen_start_stdin_json_structure_ok
exit 0

all required artifact JSON: python3 -m json.tool
exit 0

Phase A identity/count/no-retry/Phase B absent/cleanup/deadline structural assertion
final_structure_assertion=ok
exit 0
```

targeted `1`、Upper `119`、O10 `170`、combined `289` 的 Phase 0 明细见上节。最终 `rg`、Phase B absent
断言与 scoped `git diff --check` 见本 sprint 最终验收输出。产品/测试代码没有变化，因此新增代码中文
技术注释比例检查为 `not_applicable_no_code_churn`；新增文档使用中文解释 client transport 安全不变量。

## Artifact 完整性与剩余风险

- proof refresh HTTP 响应正常结束，curl exit `0`、HTTP `200`，wrapper 前缀字段与 elapsed/deadline 已
  记录，但统一终端在完整响应返回后按 token 上限截断，未能把 wrapper body 原样持久化；
  `phase_a_nav2_proof_refresh.transport.json` 因此固定 `response_raw_persisted=false`、
  `response_json_parse_ok=null`。没有补调用、拼造 raw 或把该缺口写成 clean。
- canonical `/api/nav2/proof/latest` 的完整 343156-byte raw 已通过 apply_patch 持久化并 parse clean，
  包含同一 current final artifact；该事实证明 deadline natural final，但不能消除 wrapper raw 缺失这一
  artifact 完整性风险。
- start request 实际坏 body 没有被 server 回显，只能从 JSON decoder error 证明 payload 损坏；
  `request_body_at_server_parse_bytes=null`，不得反推或伪造精确 body。
- current localization、TF、planner/controller、path 与 obstacle clear 仍不满足，未来 live 必须新授权，
  且先按新增 stdin 传输合同完成 client-side frozen body 结构断言。

## Handoff

需要 `robot-algorithm-engineer` 对冻结 Phase A 做只读 review：确认 live absolute deadline natural final、
start transport corruption、lifecycle/localization/TF/path exact blockers 与 NO-GO。Algorithm 不得 SSH、
不得 start/proof/stop/goal 或同窗 retry。本 sprint 已 sealed；即使离线发现修复项，也只能在新 fresh
authorization 下进入下一次 live。Phase B 没有 execute，故本轮不派 Hardware T=1001/HIL review，
Full-stack 也无需介入。

## Product / Algorithm closeout addendum

本 addendum 不改写 Robot Software 的原始执行事实。Algorithm 已对冻结 artifact 做只读 review，结论为
`ACCEPT_NO_GO`；Product 接受该结论并将最终统一 proof boundary 规范为
`current_live_deadline_validation_plus_start_transport_no_go_not_readiness_or_route`。

必须同时保留两条事实：

- `DEADLINE_LIVE_VALIDATED=true`：current board proof 在 `77717ms` 自然形成 final，absolute-deadline
  blocker 已经真实板验证关闭；
- `READINESS_GO=false`：唯一 start 在 remote handler 执行前被 client shell quoting 损坏，
  `invalid_nav2_start_json`、remote invocation=`0`，没有 route/HIL/user action/delivery。

新 blocker 固定为 `phase_a_start_json_transport_corrupted_before_remote_handler`，本轮只消费 `1/2`；它不是
deadline、ROS 或 hardware blocker。当前 delta ledger 为 `current_run_artifact_delta=true`，只对应 live deadline
validation 与 current safe NO-GO；external/live-control/user-action 均 false，route/HIL/delivery/safe/OKR credit
均 false。O5 保持约 `85%` 且 provider/runtime `2/2` 继续暂停，O6/O7 各约 `93%`、O1 约 `94%`
flat；O3 supporting only，KR `不归档`。

Product 本阶段没有重跑 Engineer 已留档的 targeted `1`、Upper `119`（skip1）、O10 `170`、combined
`289`（skip1）测试，也没有执行 SSH、live endpoint 或 control；Hardware/Full-stack 因 Phase B execute=`0`
未派。下一轮必须取得新的 fresh authorization，复核 remote target SHA/service health，冻结 request，并用
`jq -c` 从 `frozen_requests.json` 提取 body、经 stdin pipe 到远端 curl；只执行 exactly-one Phase A，GO
才进入 Phase B，NO-GO 即封存。当前授权不得复用，inline JSON 永久禁用。
