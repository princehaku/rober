# Integration Acceptance Report

## 1. 验收范围

- Sprint: `2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material`
- 验收目标：确认返工后的 `pc_live_nav2_execution_material` 在 Algorithm -> O6 -> O7 间不再发生 `goal_accepted / goal_result_status / result_status / nav2_terminal_status` 字段漂移。
- 验收方式：只读代码审查 + 轻量定向测试；未改产品代码。

## 2. 已审阅输入

- [`/Users/m1/apps/rober/AGENTS.md`](/Users/m1/apps/rober/AGENTS.md)
- [`/Users/m1/apps/rober/sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/tech-plan.md`](/Users/m1/apps/rober/sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/tech-plan.md)
- [`/Users/m1/apps/rober/sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/algorithm_worker_report.md`](/Users/m1/apps/rober/sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/algorithm_worker_report.md)
- [`/Users/m1/apps/rober/sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/o6_worker_report.md`](/Users/m1/apps/rober/sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/o6_worker_report.md)
- [`/Users/m1/apps/rober/sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/o7_worker_report.md`](/Users/m1/apps/rober/sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/o7_worker_report.md)
- [`/Users/m1/apps/rober/sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/pc_live_nav2_execution_material_source.json`](/Users/m1/apps/rober/sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/pc_live_nav2_execution_material_source.json)

## 3. 轻量命令与输出片段

### 3.1 Algorithm 定向单测

```bash
python3 -m unittest onboard.tests.test_field_route_evidence_manifest.FieldRouteEvidenceManifestTest.test_pc_live_nav2_execution_material_ready_consumes_safe_short_summary
```

输出片段：

```text
.
----------------------------------------------------------------------
Ran 1 test in 0.008s

OK
{"gate_pass": true, "output": ".../manifest.json", "schema": "trashbot.field_evidence_manifest.v1", "status": "field_evidence_manifest_ready_not_delivery_proof"}
```

### 3.2 O6 定向单测

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay.RemoteCloudRelayHttpTest.test_o6_pc_live_nav2_execution_material_in_field_and_bundle_readback
```

输出片段：

```text
.
----------------------------------------------------------------------
Ran 1 test in 0.789s

OK
```

### 3.3 O7 定向测试

```bash
cd pc-tools/workstation && npm run test -- -t "keeps pc live Nav2 execution material ready"
```

输出片段：

```text
Test Files  1 passed | 2 skipped (3)
Tests  1 passed | 489 skipped (490)
```

### 3.4 只读源码核对命令

```bash
rg -n "goal_result_status|result_status|nav2_terminal_status|terminal_status|goal_accepted|nav2_goal_accepted|pc_live_nav2_execution_material" ...
sed -n '6978,7140p' onboard/scripts/field_route_evidence_manifest.py
sed -n '18370,18495p' onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
sed -n '6228,6322p' pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts
```

结果：关键 fallback 顺序、alias 双写和对应测试断言均存在，见下文结论。

## 4. 验收结论

### 4.1 Algorithm producer

结论：**通过，但要区分 source material 与 producer output。**

- source fixture [`pc_live_nav2_execution_material_source.json`](/Users/m1/apps/rober/sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/pc_live_nav2_execution_material_source.json) 直接包含：
  - canonical: `goal_accepted`, `goal_result_status`
  - legacy input alias: `terminal_status`
- source fixture **不直接包含**：
  - `result_status`
  - `nav2_goal_accepted`
  - `nav2_terminal_status`
- 但 producer 代码 [`/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py`](/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py:6999) 明确把输入收敛成输出：
  - 读取：`goal_result_status`，fallback `terminal_status`
  - 输出：`goal_accepted` + `nav2_goal_accepted`
  - 输出：`goal_result_status` + `result_status` + `nav2_terminal_status`
- Algorithm 定向测试 [`/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py`](/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py:5040) 明确断言 producer output 同时具备：
  - `goal_accepted=true`
  - `nav2_goal_accepted=true`
  - `goal_result_status="goal_timeout_cancel_requested"`
  - `result_status="goal_timeout_cancel_requested"`
  - `nav2_terminal_status="goal_timeout_cancel_requested"`

判定：**Algorithm 最终 producer output 已满足 canonical + alias 双写，不再只靠 alias。**

### 4.2 O6 archive/readback

结论：**通过。**

- O6 代码 [`/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py:18377) 对布尔字段做 alias 兼容：
  - `goal_accepted` -> fallback `nav2_goal_accepted`
- O6 对结果状态的读取优先级为 [`remote_cloud_relay.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py:18400)：
  - `goal_result_status`
  - `result_status`
  - `nav2_terminal_status`
  - `terminal_status`
- O6 输出仍固定回写：
  - `goal_result_status`
  - `result_status`
- O6 定向测试 [`/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py:5430) 验证 field readback / bundle readback / consumer detail 都保持：
  - `goal_accepted=true`
  - `goal_result_status="goal_timeout_cancel_requested"`
  - `result_status="goal_timeout_cancel_requested"`
- legacy payload 兼容测试也存在于 [`test_remote_cloud_relay.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py:1533)，覆盖 `nav2_goal_accepted` 与 `nav2_terminal_status`。

判定：**O6 已按要求优先 canonical `goal_result_status`，并保留 `result_status` alias 输出。**

### 4.3 O7 adapter/consumer

结论：**通过。**

- O7 adapter [`/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`](/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts:6231) 对结果状态的消费顺序为：
  - `goal_result_status`
  - `result_status`
  - `nav2_terminal_status`
  - `terminal_status`
- O7 对 goal accepted 的消费顺序为 [`o7ConsumerReadAdapter.ts`](/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts:6240)：
  - `goal_accepted`
  - `nav2_goal_accepted`
- O7 回归测试 [`/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`](/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts:6323) 覆盖四类输入：
  - O6 canonical top-level payload
  - O6 legacy `result_status`
  - Algorithm legacy `field_motion_evidence_packet.nav2_terminal_status`
  - Algorithm canonical `field_motion_evidence_packet.goal_result_status`
- 定向测试通过，说明 O7 不会因 canonical / legacy 并存而把 ready material 误打回 blocked。

判定：**O7 已兼容 `goal_result_status -> result_status -> nav2_terminal_status -> terminal_status` 与 `goal_accepted -> nav2_goal_accepted`。**

## 5. 集成验收总判定

**验收通过。**

- Algorithm producer output 已从 raw source material 收敛出 canonical + alias 双写。
- O6 已按 `goal_result_status` 优先消费，并输出 `goal_result_status` + `result_status`。
- O7 已按既定 fallback 顺序消费，能同时兼容 O6 canonical、O6 legacy、Algorithm legacy。
- 本轮验收未发现 `pc_live_nav2_execution_material` 在 Algorithm -> O6 -> O7 之间继续漂移的证据。

## 6. 剩余风险

- 当前 source fixture 本身不是 producer final output；它只是 Algorithm 输入材料。alias `nav2_goal_accepted` / `nav2_terminal_status` 由 producer 构造输出，而不是直接保存在 source JSON 里。
- 本轮只做了定向轻量验证，没有重跑 O6/O7 全量测试套件；结论范围限定在 `pc_live_nav2_execution_material` 字段契约，不外推到其它 section。
- 证据边界仍是 `software_proof_pc_live_nav2_execution_material_only`，不代表真实 live route execution success、wheel L/R nonzero、delivery success 或 HIL。
