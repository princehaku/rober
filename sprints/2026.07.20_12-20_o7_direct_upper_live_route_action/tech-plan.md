# O7 Direct Upper Live Route Action - Tech Plan

## Sprint metadata

- `sprint_type: epic`
- 唯一主责 owner：`full-stack-software-engineer`
- 执行模型：单 owner 串行；read-only pre-gate -> exactly-one execute -> at-most-one stop -> read-only latest/feedback -> regression -> tech-done
- Proof 目标：`direct_upper_current_live_route_action_artifact`，最终等级由真实结果决定

## OKR 最低优先级核对

`OKR.md` 4.1 的当前快照为 O5 约 `85%`、O6/O7 各约 `93%`、O1 约 `94%`，所以最低 Objective 是 O5。

本 sprint 不针对最低 O5。理由：O5 provider/runtime blocker 已连续消费 `2/2`，Product 已明确禁止第三轮 wrapper、diagnostic、preflight 或 tunnel 包装；CEO 本轮 fresh 授权的是 operator 看护下的 current live route action。方向因此调整为主推 O7/O6 的真实用户动作/route evidence，并以 current stop/base feedback supporting O1。这是 blocker 红线与 fresh gate change 驱动的切换，不是为提高百分比而换方向。

## 1. Owner 与串行边界

只派一个 `full-stack-software-engineer`，由其完成远端 curl、artifact、回归验证、失败修复循环和 `tech-done.md`。本轮不派 Algorithm/Hardware，避免重复此前 business execution stall；他们只在事实出现后的 Product acceptance 阶段提供只读判读。

## 2. 严格文件范围

### 2.1 默认允许创建/修改

```text
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/tech-done.md
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/action_identity.json
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/direct_upper_request.json
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/stop_request.json
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/pre_gate_health_compat.raw
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/pre_gate_api_health.raw
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/pre_gate_status.raw
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/pre_gate_nav2_latest.raw
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/pre_gate_decision.json
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/direct_execute_response.raw
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/direct_stop_response.raw
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/post_nav2_latest.raw
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/post_base_feedback_latest.raw
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/live_sequence_invocation_manifest.json
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/json_assertion_result.txt
sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/workstation_regression.txt
```

`.raw` 文件必须保存 curl 原始 body；对应 HTTP status、SSH/curl exit、JSON parse status、SHA256 和 invocation count 统一写入 manifest。禁止用 fixture/synthetic body 覆盖原始失败。

### 2.2 默认禁止

- 不修改 `pre_start.md`、`prd.md`、`tech-plan.md`、`OKR.md`、progress log 或 sprint 外产品文档；由 Product acceptance 后处理。
- 不修改 `pc-tools/workstation/src/**`、`pc-tools/workstation/test/**`、`onboard/**`、hardware/vendor、launch、ROS2 或 runtime 配置。
- 不在上位机仓库或 `/tmp` 留持久文件；remote curl 只通过 stdin/stdout，artifact 落在本 sprint 本地目录。

### 2.3 明确合同 bug 的唯一例外

若 run-only 验证发现可复现且与既有 workstation action receipt 合同直接相关的 bug，Engineer 必须先保存失败 artifact，并停止所有 live POST；随后报告 Product 重新开窄修复范围。没有 Product 重新派单前，本 sprint 不得修改 product code。上位机/ROS2/hardware bug 不属于 Full-stack owner 范围，只记录根因和证据，不越权修复。

## 3. 固定 artifacts 输入

先用 `apply_patch` 创建 `action_identity.json`、`direct_upper_request.json`、`stop_request.json`；不得用 shell write trick。内容分别为：

```json
{
  "task_id": "task_o3_28_pose_fixed_route_consumer_20260713_0402",
  "run_id": "run_o7_direct_upper_live_route_20260720_02",
  "route_intent_id": "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path",
  "authorization_ref": "ceo_20260720_1220_bounded_motion_operator_watch_route_clear_v2",
  "action_id": "action_o7_direct_upper_nav_20260720_02"
}
```

```json
{
  "confirm_navigation_execution": true,
  "goal_frame_id": "map",
  "goal_x": 0.8,
  "goal_y": 0.25,
  "goal_yaw": 0.0,
  "base_command_mode": "ros",
  "managed_runtime_opt_in": true,
  "result_timeout_s": 8,
  "server_timeout_s": 12,
  "route_preview_point_count": 28,
  "route_preview_source_point_count": 28,
  "route_preview_frame_id": "map",
  "route_start_x": 0.07615115310756959,
  "route_start_y": 0.2500000037252903,
  "route_goal_x": 0.8,
  "route_goal_y": 0.2500000037252903
}
```

```json
{}
```

## 4. Read-only pre-gate

固定 SSH transport：

```bash
ssh -p 37878 root@192.168.1.11
```

Engineer 必须逐项执行 remote curl，并将 stdout 保存到上述 `.raw`，同时把 SSH/curl exit 与 HTTP status 写入 manifest：

```bash
curl --silent --show-error --max-time 5 http://127.0.0.1:8787/health
curl --silent --show-error --max-time 5 http://127.0.0.1:8787/api/health
curl --silent --show-error --max-time 12 http://127.0.0.1:8787/api/status
curl --silent --show-error --max-time 12 http://127.0.0.1:8787/api/nav2/goal/execution/latest
```

这些 curl 必须在 SSH 远端执行，而不是在开发主机直接访问 127.0.0.1。`/health` 是 CEO 指定的 compatibility read；仓库 canonical health 是 `/api/health`。兼容路径 404 可以被 canonical `/api/health` 的 clean JSON 替代，但两者事实都必须保留，不能修改上位机补 alias。

### 4.1 Pre-gate JSON 断言

`pre_gate_decision.json` 至少包含：

- `ssh_transport=direct_upper_remote_curl`
- `upper_loopback_base=http://127.0.0.1:8787`
- `authorization_ref` 与 `operator_watch=true/route_clear=true/physical_position_bounded=true`
- 四个 read 的 invocation count/HTTP/parse 状态；
- `canonical_health_json=true`；
- status/latest 的 schema/status/time lineage 摘要；
- `existing_motion_active=false` 或无法确认时 fail closed；
- `explicit_unsafe_blocker_present=false`；
- `pre_gate_pass=true|false` 与具体 reasons；
- `motion_post_invocation_count_before_gate=0`。

只有 JSON parse、runtime attribution、现场条件、no-existing-motion 与无明确 unsafe blocker 全部 clean 才 `pre_gate_pass=true`。任何 unknown 都 fail closed；health/SSH 只证明 transport，不是业务结果。

## 5. Exactly-one direct upper execute

只有 `pre_gate_pass=true` 才运行下列 remote curl 一次：

```bash
curl --silent --show-error --max-time 120 \
  --request POST \
  --header 'Content-Type: application/json' \
  --data-binary @- \
  http://127.0.0.1:8787/api/nav2/goal/execute
```

本地 `direct_upper_request.json` 通过 SSH stdin 传给 remote curl，原始 stdout 写入 `direct_execute_response.raw`。必须满足：

- `confirm_navigation_execution=true`；
- execute invocation count=`1`；
- endpoint 完全等于 `/api/nav2/goal/execute`；
- `exactly-one=true`、`no.retry=true`；
- 不得因 timeout、HTTP error、JSON parse error、goal reject、cancel、result failed 或 unknown 再执行；
- 不得换 `base_command_mode`、goal、timeout、route count 或 identity；
- manual/free-roam/keyboard/direct `/cmd_vel`/`/initialpose`/UART/delivery invocation=`0`。

若 pre-gate fail，execute invocation=`0`，直接进入 artifact/tech-done 收口。

## 6. At-most-one stop 与只读 post readback

一旦 execute invocation 已发生，不论返回成功、失败、超时或 unknown，最多一次执行：

```bash
curl --silent --show-error --max-time 20 \
  --request POST \
  --header 'Content-Type: application/json' \
  --data-binary @- \
  http://127.0.0.1:8787/api/base/stop
```

输入为 `stop_request.json`。stop invocation count 必须 `<=1`、`no.retry=true`；stop transport failure 不允许第二次 stop。随后只读：

```bash
curl --silent --show-error --max-time 12 http://127.0.0.1:8787/api/nav2/goal/execution/latest
curl --silent --show-error --max-time 12 http://127.0.0.1:8787/api/base/feedback-samples/latest
```

分别保存 `post_nav2_latest.raw` 与 `post_base_feedback_latest.raw`。不得再发送运动 POST。

## 7. Invocation manifest 与 JSON 断言

`live_sequence_invocation_manifest.json` 必须至少记录：

- identity 五字段、request/identity SHA256；
- 按时间排序的 endpoint/method/invocation/SSH exit/curl exit/HTTP status/body SHA256/JSON parse status；
- `pre_gate_pass`、`execute_invocation_count`、`stop_invocation_count`；
- `exactly_one_execute_observed`、`no_retry_observed`；
- 所有禁止动作 invocation count=`0`；
- response/latest 的 schema、status、goal accepted/result received/result status、robot control、route proof、HIL、wheel L/R、stop 与 delivery 摘要；
- `mock_fallback_invocation_count=0`；
- `remote_temp_file_residual_count=0`；
- proof/delta candidate 与 conservative reason。

运行结构断言并把 stdout 保存为 `json_assertion_result.txt`：

```bash
python3 - <<'PY'
import json
from pathlib import Path

p = Path('sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack')
identity = json.loads((p / 'action_identity.json').read_text())
request = json.loads((p / 'direct_upper_request.json').read_text())
decision = json.loads((p / 'pre_gate_decision.json').read_text())
manifest = json.loads((p / 'live_sequence_invocation_manifest.json').read_text())

assert identity == {
    'task_id': 'task_o3_28_pose_fixed_route_consumer_20260713_0402',
    'run_id': 'run_o7_direct_upper_live_route_20260720_02',
    'route_intent_id': 'route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path',
    'authorization_ref': 'ceo_20260720_1220_bounded_motion_operator_watch_route_clear_v2',
    'action_id': 'action_o7_direct_upper_nav_20260720_02',
}
assert request['confirm_navigation_execution'] is True
assert request['goal_frame_id'] == 'map'
assert request['goal_x'] == 0.8 and request['goal_y'] == 0.25 and request['goal_yaw'] == 0.0
assert request['base_command_mode'] == 'ros'
assert request['route_preview_point_count'] == 28
assert request['route_preview_source_point_count'] == 28
assert decision['motion_post_invocation_count_before_gate'] == 0
assert manifest['execute_invocation_count'] in (0, 1)
assert manifest['stop_invocation_count'] in (0, 1)
assert manifest['no_retry_observed'] is True
assert manifest['mock_fallback_invocation_count'] == 0
assert manifest['manual_invocation_count'] == 0
assert manifest['free_roam_invocation_count'] == 0
assert manifest['direct_cmd_vel_invocation_count'] == 0
assert manifest['initialpose_invocation_count'] == 0
assert manifest['uart_invocation_count'] == 0
assert manifest['delivery_invocation_count'] == 0
if decision['pre_gate_pass']:
    assert manifest['execute_invocation_count'] == 1
    assert manifest['exactly_one_execute_observed'] is True
else:
    assert manifest['execute_invocation_count'] == 0
    assert manifest['stop_invocation_count'] == 0
assert manifest['delivery_success'] is False
print('o7_direct_upper_live_route_action_structure_ok')
PY
```

对所有声明为 JSON 的 artifact 运行 `python3 -m json.tool`。`.raw` 若不可解析，保留原始事实并让 manifest 的 `json_parse_status` fail closed；不得伪造 JSON 通过。

## 8. Workstation contract regression

run-only 结束后运行并把完整摘要/exit 记录到 `workstation_regression.txt`：

```bash
cd pc-tools/workstation
npm run test -- test/catalog.test.ts -t "Nav2 goal execution"
npm run test
npm run build
npm run lint
```

回归失败时先读错误、定位是否为既有环境/fixture drift 还是明确合同 bug。不得用修改产品代码来掩盖 live failure；需要代码修复时先停止并请求 Product 重开窄范围。修复获批后才执行“最小修复 -> targeted -> full test -> build -> lint”的失败修复循环，直到通过或留下明确 blocker。

## 9. Proof / delta 判定

- 只有 SSH/health/status/latest：`current_run_artifact_delta` 可按新 current artifact 判 true，但 `external_artifact_delta=false|仅只读`、`user_action_delta=false`、`live_control_delta=false`，无 OKR credit。
- execute 未进入 upper handler或无法由 response/latest 归因：`user_action_delta=false`。
- direct upper handler 可归因地接收一次动作：`user_action_delta=true` 候选；HTTP 200 本身不等于 route success。
- current response/latest 明确 `robot_control_executed=true`：`live_control_delta=true` 候选；必须与新 run/action 时间窗一致。
- `goal_accepted=true`、`result_received=true`、`result_status=succeeded` 且 `nav2_goal_execution_proven=true`：`route_execution_success=true` 候选。
- `hil_pass=true` 还必须由 current wheel L/R feedback 支持；否则保持 false。
- stop response 只证明 stop endpoint 被调用；底盘已停必须由 stop result/feedback 支持。
- `delivery_success=false` 固定；本轮不调用 delivery/operator acceptance。
- 最终 OKR credit、百分比和 KR 归档仅由 Product `side2side_check.md` / `final.md` 裁决。

## 10. 验收命令

Implementation owner 必须运行并回传完整结果：

```bash
test -s sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/tech-done.md
test -s sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/action_identity.json
test -s sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/direct_upper_request.json
test -s sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/pre_gate_decision.json
test -s sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/live_sequence_invocation_manifest.json
python3 -m json.tool sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/action_identity.json >/dev/null
python3 -m json.tool sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/direct_upper_request.json >/dev/null
python3 -m json.tool sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/pre_gate_decision.json >/dev/null
python3 -m json.tool sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/artifacts/full-stack/live_sequence_invocation_manifest.json >/dev/null
rg -n "task_o3_28_pose_fixed_route_consumer_20260713_0402|run_o7_direct_upper_live_route_20260720_02|route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path|action_o7_direct_upper_nav_20260720_02|ceo_20260720_1220_bounded_motion_operator_watch_route_clear_v2|confirm_navigation_execution|exactly|no.retry|/api/nav2/goal/execute|/api/base/stop" \
  sprints/2026.07.20_12-20_o7_direct_upper_live_route_action
cd pc-tools/workstation && npm run test -- test/catalog.test.ts -t "Nav2 goal execution"
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
git diff --check -- \
  sprints/2026.07.20_12-20_o7_direct_upper_live_route_action \
  pc-tools/workstation/src/shared/contracts.ts \
  pc-tools/workstation/src/server/index.ts \
  pc-tools/workstation/test/catalog.test.ts
```

另外必须运行第 7 节 Python JSON 断言，并输出 `o7_direct_upper_live_route_action_structure_ok`。

## 11. Tech-done 输出要求

`tech-done.md` 必须包含：

1. 实际改动文件列表；
2. 每条 remote read/action/stop/readback 的 invocation count、exit、HTTP、JSON parse 与 artifact 路径；
3. workstation targeted/full/build/lint 与 JSON 断言结果；
4. 首轮失败、根因、修复与复验循环；
5. proof/delta 建议与不证明项；
6. 剩余风险，尤其是 stop 是否被 feedback 支持、latest 是否为本 action、wheel/HIL 与 delivery 缺口；
7. 明确 `no.retry=true`，禁止以第二次 execute/stop 补证据。
