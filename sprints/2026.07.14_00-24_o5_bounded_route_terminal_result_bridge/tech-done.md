# Tech Done - O5 Bounded Route Terminal Result Bridge

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/`
- Implementation owner: `robot-software-engineer`
- Proof boundary: `software_proof_o5_bounded_route_terminal_result_bridge_only`
- Source artifact: `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json`
- Output artifact: `artifacts/o5_bounded_route_terminal_result_bridge_summary.json`

## 实际改动

- 新增 `onboard/scripts/o5_bounded_route_terminal_result_bridge.py`：
  - 读取并校验 O3 `trashbot.o3.bounded_route_mock_execution.v1` summary。
  - 启动本地 in-process relay，不改 `remote_cloud_relay.py`，不绕过 HTTP API 写 store。
  - 依次调用 `POST /api/commands/collect`、`POST /robots/{robot_id}/commands/{command_id}/terminal-result`、`GET /api/commands/{command_id}/result?robot_id=...`。
  - 写出 `trashbot.o5.bounded_route_terminal_result_bridge.v1` summary，固定所有 delivery、route、control、HIL、production false 字段。
- 新增 `onboard/tests/test_o5_bounded_route_terminal_result_bridge.py`：
  - 覆盖 happy path、CLI 写文件、source schema 漂移、dangerous true field、缺少 no-motion source guard 的 fail-closed 行为。
- 更新 `docs/product/cloud_4g_infrastructure.md` 和 `docs/product/remote_4g_mvp.md`：
  - 记录 O5 bounded route terminal-result bridge 的 schema、proof boundary、HTTP 主路径和不证明范围。
- 生成 `sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json`。

## Artifact 关键结果

- `schema=trashbot.o5.bounded_route_terminal_result_bridge.v1`
- `proof_boundary=software_proof_o5_bounded_route_terminal_result_bridge_only`
- `source_schema=trashbot.o3.bounded_route_mock_execution.v1`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `command_id=o5-bounded-route-terminal-result-bridge-task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `result_code=mock_route_execution_completed_not_live_delivery`
- `terminal_result_state=terminal_result_recorded`
- `reconciliation_state=terminal_result_recorded`
- `relay_capabilities=[cloud_phone_command_api, cloud_command_terminal_result, cloud_command_result_reconciliation]`
- 固定 false：`delivery_success`、`route_execution_success`、`safe_to_control`、`hil_pass`、`robot_control_executed`、`connects_cloud_production`、`uses_base_uart`、`publishes_cmd_vel`、`calls_base_manual`。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o5_bounded_route_terminal_result_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

结果：通过，exit 0。

```bash
python3 -m unittest onboard.tests.test_o5_bounded_route_terminal_result_bridge
```

结果：`Ran 6 tests in 1.599s`，`OK`。

```bash
python3 onboard/scripts/o5_bounded_route_terminal_result_bridge.py \
  --source-summary sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json \
  --output sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json
```

结果：通过，输出 artifact `generated_at_utc=2026-07-13T16:38:30Z`，`terminal_result_state=terminal_result_recorded`，`reconciliation_state=terminal_result_recorded`。

```bash
python3 -m json.tool sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json >/dev/null
```

结果：通过，exit 0。

```bash
python3 - <<'PY'
...
PY
```

结果：`bounded_route_terminal_result_bridge_acceptance_ok`。

```bash
rg -n "bounded_route_terminal_result_bridge|software_proof_o5_bounded_route_terminal_result_bridge_only|mock_route_execution_completed_not_live_delivery|terminal_result_recorded|cloud_command_result_reconciliation" onboard/scripts/o5_bounded_route_terminal_result_bridge.py onboard/tests/test_o5_bounded_route_terminal_result_bridge.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge
```

结果：通过，脚本、测试、文档、计划和 output artifact 均包含验收锚点。

```bash
git diff --check -- onboard/scripts/o5_bounded_route_terminal_result_bridge.py onboard/tests/test_o5_bounded_route_terminal_result_bridge.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge
```

结果：通过，exit 0。

## 失败定位

无。首轮 `py_compile`、targeted unittest、CLI artifact generation、JSON 校验、结构断言、anchor rg 和 scoped diff check 均通过。

## 剩余风险与边界

- 本轮只证明 local/mock O5 bounded route terminal-result bridge 软件链路。
- 不证明真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser、真实 route execution、delivery/operator acceptance、HIL 或 safe-to-control。
- 未触发真实机器人控制、Nav2 action、底层手动控制 API 或 UART。
- O5 百分比是否调整应由 Product closeout 判定；按当前证据边界，本轮建议保持 support-only / flat scoring。

## 协同需求

- 需要 `product-okr-owner` 做 side-by-side acceptance / final closeout，并决定 OKR 记录是否保持 flat。
- 当前不需要 Hardware、Autonomy 或 Full-Stack 协同；只有进入真实 HIL、Nav2 route execution、生产公网或手机/browser 实证时再分别拉对应 owner。
