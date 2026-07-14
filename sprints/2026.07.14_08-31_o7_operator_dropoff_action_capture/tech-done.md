# O7 operator dropoff action capture tech done

- sprint_type: epic
- owner: full-stack-software-engineer
- status: accepted_local_mock_software_proof
- proof_boundary: `software_proof_o6_o7_operator_dropoff_action_capture_only`
- bounded_result: selected-task operator action request construction、O6 local archive event write/readback receipt、O7 UI receipt 展示、fail-closed validation

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - O6 archive event whitelist 新增 `operator.dropoff_acceptance`。
  - O6 local/mock archive guard 新增拒绝 `real_operator_action_proven=true`、`route_execution_success=true`、`hil_pass=true` 等真实能力 claim。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 新增 O6 `operator.dropoff_acceptance` 正向写入、readback、list/detail 和真实能力 true claim 拒绝测试。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 O7 request/receipt contract：`trashbot.pc_tools_workstation.o7_operator_dropoff_action_capture_result.v1`。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - 新增 selected-task operator dropoff capture adapter。
  - 仅允许本机 loopback `baseUrl`，固定转发 O6 `POST /api/o6/archive/events`，固定写入 `event_type=operator.dropoff_acceptance`。
  - 对 task mismatch、unknown fields、caller 覆盖 `event_type`、unsafe refs、credential/raw/base64-like 内容、控制/导航/UART 字符串和真实能力 true claim fail-closed。
  - 成功 receipt 固定 `real_operator_action_proven=false`、`delivery_success=false`、`route_execution_success=false`、`safe_to_control=false`、`hil_pass=false`、`robot_control_executed=false`、`connects_cloud_production=false`。
- `pc-tools/workstation/src/server/index.ts`
  - 新增 `POST /api/o7/consumer-read/tasks/:taskId/operator/dropoff-acceptance/request?baseUrl=<local-loopback-url>`。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 workstation client API：`postO7OperatorDropoffActionCapture`。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 在 selected-task consumer detail 面板中新增 operator dropoff capture 表单、按钮、receipt 展示、fixed false fields 和 not_proven 展示。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 adapter create/update receipt、unsafe input fail-closed、bad O6 receipt fail-closed、HTTP endpoint 透出。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 UI 点击、请求路径、receipt schema、`operator.dropoff_acceptance`、proof boundary 和固定 false 展示。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 记录 O6 `operator.dropoff_acceptance` 事件、安全白名单和 fail-closed 边界。
- `docs/interfaces/o7_realtime_operator_console.md`
  - 记录 O7 endpoint、O6 转发、receipt schema、proof boundary 和不证明项。
- `docs/product/pc_tools_workstation.md`
  - 记录 PC workstation 用户旅程新增 operator dropoff action capture，明确 local/mock 证明边界。

## 用户旅程和触点收益

- operator console 现在可以在已选 O7 consumer task 上构造一次 dropoff acceptance action request。
- 用户能看到该 request 是否被写入 O6 local archive，并在同一 UI 中看到 receipt、O6 write status、event identity、operator action id、evidence refs、fixed false fields 和 not_proven。
- 失败时返回 `capture_status=fail_closed`、`blocked_reasons` 和恢复线索，不把 unsafe/action/control 输入伪装成成功。

## 接口影响

- O6 local archive event whitelist 增加 `operator.dropoff_acceptance`。
- O7 新增 endpoint：
  - `POST /api/o7/consumer-read/tasks/:taskId/operator/dropoff-acceptance/request?baseUrl=<local-loopback-url>`
- O7 receipt schema：
  - `trashbot.pc_tools_workstation.o7_operator_dropoff_action_capture_result.v1`
- proof boundary：
  - `software_proof_o6_o7_operator_dropoff_action_capture_only`

## 验证结果

```text
$ python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
# passed with no output
```

```text
$ python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
Ran 200 tests in 88.807s
OK
```

```text
$ cd pc-tools/workstation && npm run test
Test Files  3 passed (3)
Tests  519 passed (519)
Duration  46.20s
```

```text
$ cd pc-tools/workstation && npm run build
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ 34 modules transformed.
✓ built in 2.06s
warning: Some chunks are larger than 500 kB after minification.
```

```text
$ cd pc-tools/workstation && npm run lint
eslint .
# passed with no lint errors
```

```text
$ rg -n "operator/dropoff-acceptance/request|operator.dropoff_acceptance|o7_operator_dropoff_action_capture_result|software_proof_o6_o7_operator_dropoff_action_capture_only|real_operator_action_proven=false|delivery_success=false|route_execution_success=false|safe_to_control=false|hil_pass=false|robot_control_executed=false|connects_cloud_production=false" ...
# passed: matched required contract anchors across code, tests, docs, and sprint files.
# first matches included tech-done proof_boundary, O6 operator.dropoff_acceptance whitelist,
# O7 endpoint, O7 receipt schema, and all fixed false strings.
```

```text
$ git diff --check -- <allowed files and sprint directory>
# passed with no output
```

## 失败定位与修复

- 本轮最终验收命令均通过；没有留下需要二次修复的失败项。
- `npm run build` 保留已有 Vite 大 chunk warning，不影响本轮合同和测试结果。

## Proof boundary 和不证明项

- 本轮只证明：selected-task operator action request construction、O6 local archive event write/readback receipt、O7 UI receipt 展示、fail-closed validation。
- 固定 false：`real_operator_action_proven=false`、`delivery_success=false`、`route_execution_success=false`、`safe_to_control=false`、`hil_pass=false`、`robot_control_executed=false`、`connects_cloud_production=false`。
- 不证明：real operator action、delivery success、route execution、HIL、safe-to-control、production cloud、robot control、`/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART。

## 剩余风险

- 该 sprint 是 local/mock software proof only，未连接真实 operator/browser session、真实云端、真实 route execution、HIL 或机器人控制链路。
- O5 仍需要 same-window live route/HIL/operator evidence 或 success-class production/cloud evidence；本轮不提升 O5 完成度。
