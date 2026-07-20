# O7 Full-stack live route 用户动作回执 - Tech Plan

## OKR 最低优先级核对

1. `OKR.md` 当前最低 Objective 是 O5，约 `85%`；其次为 O6/O7，各约 `93%`；O1 约 `94%`。
2. 本 sprint 不针对最低 O5，主推 O7、联动 O6/O1。
3. O5 production/provider runtime blocker 已消费 `2/2`；Algorithm 与 Hardware business owner 又分别在业务文件/命令前
   多次 runtime stall。CEO 本轮要求切换不同 Objective 或未消费业务 owner/证据类别，因此选择未消费的
   `full-stack-software-engineer` 与 live 用户动作 receipt，不重派旧 owner，不创建 wrapper。

## 技术方案

### Phase A - 核心 execute receipt contract

在既有 `POST /api/robot-control/nav2/goal/execute` 内增加 identity sanitizer 和
`user_action_receipt`，不改变 endpoint、fixed remote path、goal clamp、base URL allowlist、minimal preflight 或危险字段
扫描。Receipt 在 normalize reject、preflight reject、remote non-2xx、timeout/exception 与 forwarded 路径统一生成。

请求 identity 固定为：

```text
task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402
run_id=run_o7_full_stack_live_route_user_action_20260720_01
route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path
authorization_ref=ceo_20260720_bounded_motion_operator_watch_route_clear_v1
action_id=action_o7_live_nav_20260720_01
```

Receipt 只抄安全摘要，不保存 credential、SSH target、绝对远端路径或 raw upstream dump。`user_action_delta` 由 Product
依据 live invocation/receipt 判断，不由软件在 mock 测试中硬编码为 OKR credit。

### Phase B - 离线验证与 hostile matrix

使用既有 fake upstream 测试：forwarded、preflight reject、remote 500、timeout、危险 true field、超长/控制字符 identity。
确认 exactly one remote POST、identity 稳定、unsafe 仍 fail closed、不会调用 `/api/base/manual`，也不会新增 endpoint。
Mock fallback 只存在于测试，不能写入 live artifacts。

### Phase C - exactly one live/fail-closed action

启动本地 workstation API，先读真实 upper computer summary；随后用 fixed identity、28/28 route metadata、
`map (0.8,0.25,0)`、`base_command_mode=ros` 调用 execute 一次。无论返回、超时或断连，均保存 action receipt，并按
`stop rule` 最多调用一次 workstation base stop。之后只读 latest、base feedback 与 summary，不发第二个 goal。

若 pre-action 当前事实或 operator 判断不安全，仍不得改目标或换入口；可以不向远端 forward，并以本地 fail-closed
用户动作 receipt 收口。若请求已经发出但结果不确定，必须 stop 并把 terminal status 标成 unknown，不得补跑。

### Phase D - 工程与 Product 收口

Full-stack 更新 `tech-done.md`，记录代码、测试、live invocation、receipt、stop、cleanup、失败与风险。Product 依据
artifact 决定：

- 有有效 current-run action receipt：可记录 `user_action_delta=true`，但仍按 terminal/readback 判断 OKR credit；
- 仅 contract/mock：所有 mission delta false，百分比 flat；
- route success 只接受 upstream terminal/readback 明确证据；HIL 与 delivery 不由 receipt 推导。

之后才允许创建 `side2side_check.md`、`final.md`，以及按实际 delta 更新 `OKR.md` 与
`docs/process/okr_progress_log.md`。

## Owner 与文件范围

唯一 implementation/verification owner：`full-stack-software-engineer`。允许文件范围严格限定为：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.20_11-20_o7_full_stack_live_route_user_action_receipt/artifacts/full-stack/**`
- `sprints/2026.07.20_11-20_o7_full_stack_live_route_user_action_receipt/tech-done.md`

禁止修改 `OKR.md`、progress log、上车 API、ROS2、Algorithm/Hardware 文件、旧 sprint、package dependencies 或 lockfile。
所有新增技术注释必须使用中文，修改范围内有意义中文注释比例必须严格 `>20%`。

## 接口边界

- Workstation endpoint 保持 `/api/robot-control/nav2/goal/execute`；remote endpoint 固定
  `/api/nav2/goal/execute`，不得接受任意 remote path。
- 新 identity 是审计 metadata，不得影响 goal、mode、timeout、preflight 或动作成功判定。
- Receipt 的 `request_forwarded=true` 只表示 fixed proxy 已调用 upstream，不等于 goal accepted/succeeded。
- `robot_control_executed`、terminal/result、route feedback 只消费 upstream 明确字段；缺失即 not proven。
- `safe_to_control` 与 `delivery_success` 不得因本轮 receipt 变 true；`hil_pass` 仅可原样保留 upstream 明确事实，并由
  Product 复核，不得由 Full-stack 推导。

## stop rule 与 Proof boundary

- Execute invocation count=`1`，remote goal invocation count `<=1`，mock fallback invocation count=`0`。
- execute 返回/失败/timeout/unknown/operator stop 后，base stop invocation count `<=1`；stop 也失败时保留原始失败，不重试。
- 清理本地 workstation PID；禁止第二 goal、换模式补跑、manual/free-roam/direct `/cmd_vel`/`/initialpose`/UART。
- Planning Proof boundary：`planning_only_o7_full_stack_live_route_user_action_receipt`。
- Live fail-closed Proof boundary：`live_upper_computer_o7_route_user_action_receipt_attempt_only`。
- 成功 receipt 仍不自动证明 `route_execution_success=true`、`hil_pass=true`、`safe_to_control=true` 或
  `delivery_success=true`。

## 验收命令

以下命令由 `full-stack-software-engineer` 执行并把 exit code/关键输出写入 `tech-done.md`。

### A. Contract 与全量 workstation 验收

```bash
cd /Users/m1/apps/rober/pc-tools/workstation
npm run test -- test/catalog.test.ts -t "Nav2 goal execution"
npm run test
npm run build
npm run lint
cd /Users/m1/apps/rober
git diff --check -- \
  pc-tools/workstation/src/shared/contracts.ts \
  pc-tools/workstation/src/server/index.ts \
  pc-tools/workstation/test/catalog.test.ts \
  docs/product/pc_tools_workstation.md \
  sprints/2026.07.20_11-20_o7_full_stack_live_route_user_action_receipt
```

### B. Exactly one live/fail-closed 用户动作

工程 owner 必须把 request body 冻结为以下内容，先保存到本 sprint
`artifacts/full-stack/live_action_request.json`，再启动本地 workstation API：

```json
{
  "task_id": "task_o3_28_pose_fixed_route_consumer_20260713_0402",
  "run_id": "run_o7_full_stack_live_route_user_action_20260720_01",
  "route_intent_id": "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path",
  "authorization_ref": "ceo_20260720_bounded_motion_operator_watch_route_clear_v1",
  "action_id": "action_o7_live_nav_20260720_01",
  "goal_x": 0.8,
  "goal_y": 0.25,
  "goal_yaw": 0,
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

```bash
cd /Users/m1/apps/rober/pc-tools/workstation
HOST=127.0.0.1 PORT=7072 npm run api
```

另一个 shell 只运行以下一次性序列；任一步失败都不得再次 POST execute：

```bash
cd /Users/m1/apps/rober
ART=sprints/2026.07.20_11-20_o7_full_stack_live_route_user_action_receipt/artifacts/full-stack
curl -sS --max-time 30 \
  'http://127.0.0.1:7072/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787' \
  -o "$ART/pre_action_summary.json"
curl -sS --max-time 115 \
  -H 'Content-Type: application/json' \
  --data-binary "@$ART/live_action_request.json" \
  'http://127.0.0.1:7072/api/robot-control/nav2/goal/execute?baseUrl=http%3A%2F%2F192.168.1.11%3A8787' \
  -o "$ART/live_action_receipt.json"
curl -sS --max-time 30 -X POST \
  'http://127.0.0.1:7072/api/robot-control/base/stop?baseUrl=http%3A%2F%2F192.168.1.11%3A8787' \
  -o "$ART/post_action_stop_receipt.json"
curl -sS --max-time 30 \
  'http://127.0.0.1:7072/api/robot-control/nav2/goal/execution/latest?baseUrl=http%3A%2F%2F192.168.1.11%3A8787' \
  -o "$ART/post_action_latest.json"
curl -sS --max-time 30 \
  'http://127.0.0.1:7072/api/robot-control/base/feedback-samples/latest?baseUrl=http%3A%2F%2F192.168.1.11%3A8787' \
  -o "$ART/post_action_base_feedback.json"
curl -sS --max-time 30 \
  'http://127.0.0.1:7072/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787' \
  -o "$ART/post_action_summary.json"
```

### C. Artifact 结构断言

```bash
python3 -m json.tool sprints/2026.07.20_11-20_o7_full_stack_live_route_user_action_receipt/artifacts/full-stack/live_action_receipt.json >/dev/null
python3 -m json.tool sprints/2026.07.20_11-20_o7_full_stack_live_route_user_action_receipt/artifacts/full-stack/post_action_stop_receipt.json >/dev/null
python3 - <<'PY'
import json
from pathlib import Path
p = Path('sprints/2026.07.20_11-20_o7_full_stack_live_route_user_action_receipt/artifacts/full-stack')
r = json.loads((p / 'live_action_receipt.json').read_text())
receipt = r['user_action_receipt']
assert receipt['task_id'] == 'task_o3_28_pose_fixed_route_consumer_20260713_0402'
assert receipt['run_id'] == 'run_o7_full_stack_live_route_user_action_20260720_01'
assert receipt['route_intent_id'] == 'route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path'
assert receipt['authorization_ref'] == 'ceo_20260720_bounded_motion_operator_watch_route_clear_v1'
assert receipt['action_id'] == 'action_o7_live_nav_20260720_01'
assert r['proxy_status'] in {'execution_forwarded', 'execution_rejected', 'execution_failed'}
assert receipt['proof_boundary'] == 'live_upper_computer_o7_route_user_action_receipt_attempt_only'
print('o7_live_route_user_action_receipt_acceptance_ok')
PY
rg -n "task_id|run_id|route_intent_id|authorization_ref|action_id|user_action_receipt|execution_forwarded|stop|Proof boundary" \
  sprints/2026.07.20_11-20_o7_full_stack_live_route_user_action_receipt/artifacts/full-stack \
  sprints/2026.07.20_11-20_o7_full_stack_live_route_user_action_receipt/tech-done.md
git status --short
```

## Live 优先与 mock fallback

Live action 是本 sprint 唯一业务抓手。Mock/fake upstream 仅用于 Phase B contract tests；若 8787 不可达、请求被拒、
timeout 或 stop 失败，Engineer 必须以真实 fail-closed receipt 收口并停止，不得生成 mock live receipt、不得重跑、不得
上调 OKR。若 contract 尚未实现或测试失败，则不进入 live Phase，先修复再复验；这不消耗 live invocation count。

## 剩余风险

- Current upper computer runtime、地图、定位、controller、WAVE ROVER feedback 可能不满足 route success；本 sprint 允许
  fail-closed，但只允许一个 action。
- Receipt metadata 是 O7 用户触点证据，不替代 Algorithm terminal 判读或 Hardware HIL；Product 必须保守分层。
- 若 Full-stack worker 也在业务文件/命令前 runtime stall，则本 lane 立即冻结，不再创建 fallback/canary/wrapper，返回
  exact runtime blocker 和下一条 runtime-owner reopen signal。
