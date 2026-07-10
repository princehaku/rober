# Algorithm Worker Report

run_time: 2026-07-09 15:17:20 CST

## 自主能力目标和本轮抓手

本轮目标是把 O11 `o11_nav2_goal_execution_proof.py` 产出的 NavigateToPose proof JSON 转成 O6/O7 可白名单回读的 additive `nav2_goal_execution_evidence`。抓手是只读 `--nav2-goal-proof-json`，不启动 Nav2、不发布 `/cmd_vel`，并把摘要写入 manifest 顶层与 `field_motion_evidence_packet.nav2_goal_execution_evidence`。

## 改动文件和接口影响

- `onboard/scripts/field_route_evidence_manifest.py`
  - 新增 `--nav2-goal-proof-json`。
  - 新增 `trashbot.nav2_goal_execution_evidence.v1` 摘要和 `software_proof_nav2_goal_execution_evidence_only` 证据边界。
  - 摘要只提取 O11 proof 白名单字段；`task_id` 沿用 field packet lineage，不让 proof 覆盖。
  - proof 缺失、schema mismatch、dangerous true、unsafe path/root/token/raw/base64 字段或文本时输出 `blocked_not_proven`。
  - `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false` 保持不变。
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 覆盖 ready fixture、schema mismatch、dangerous true + unsafe text fail-closed。
- `docs/navigation/field_route_evidence_manifest.md`
  - 记录新参数、白名单字段、schema/proof_scope 和不证明真实送达的边界。
- `sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/artifacts/algorithm_worker_report.md`
  - 本报告。

未改动 `onboard/scripts/o11_nav2_goal_execution_proof.py` 与 `onboard/tests/test_o11_nav2_goal_execution_proof.py`。

## 实现内容

- `nav2_goal_execution_evidence.status` 使用 `ready_not_delivery_proof | blocked_not_proven`。
- O11 原始 `status` 写入 `source_status`，避免和摘要自身状态冲突。
- 白名单字段包括 goal/result、goal_request、base_feedback_summary、base_command_summary。
- unsafe 检测只输出 blocked reason 与计数，不回显原始路径、root、token、raw payload 或 base64 内容。
- 如果 O11 proof 原文包含 `robot_control_executed=true`，摘要仍固定 `robot_control_executed=false`，只在 `next_required_evidence` 保留 delivery record 需求。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py onboard/scripts/o11_nav2_goal_execution_proof.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest onboard.tests.test_o11_nav2_goal_execution_proof
```

结果：

```text
Ran 29 tests in 0.059s
OK
```

```bash
rg -n "nav2_goal_execution_evidence|NAV2_GOAL_EXECUTION_EVIDENCE|software_proof_nav2_goal_execution_evidence_only" onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md
```

关键结果：

```text
onboard/scripts/field_route_evidence_manifest.py:32:NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA = "trashbot.nav2_goal_execution_evidence.v1"
onboard/scripts/field_route_evidence_manifest.py:33:NAV2_GOAL_EXECUTION_EVIDENCE_PROOF_SCOPE = "software_proof_nav2_goal_execution_evidence_only"
onboard/scripts/field_route_evidence_manifest.py:773:def build_nav2_goal_execution_evidence(args: argparse.Namespace, packet: dict[str, Any]) -> dict[str, Any]:
onboard/tests/test_field_route_evidence_manifest.py:649:        self.assertEqual(evidence["schema"], manifest.NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA)
docs/navigation/field_route_evidence_manifest.md:24:- `--nav2-goal-proof-json <o11_nav2_goal_execution_proof.json>`...
```

```bash
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/scripts/o11_nav2_goal_execution_proof.py onboard/tests/test_field_route_evidence_manifest.py onboard/tests/test_o11_nav2_goal_execution_proof.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/artifacts/algorithm_worker_report.md
```

结果：通过，无输出。

## 数据、样本或调试输出变化

- manifest 顶层新增 `nav2_goal_execution_evidence`。
- `field_motion_evidence_packet` 内新增同名嵌套摘要。
- 新测试 fixture 证明：
  - ready O11 proof 可输出 `ready_not_delivery_proof`。
  - proof 内 `task_id` 不覆盖 packet lineage。
  - schema mismatch 输出 `blocked_not_proven`，不破坏 artifact gate。
  - dangerous true 与 unsafe path/raw/base64 输入不会把原值写进输出。

## 剩余风险和下一步

- 本轮只完成 Algorithm 侧 manifest 摘要，不包含 O6 ingest/readback 与 O7 UI 消费改动。
- 证据边界是 `software_proof_nav2_goal_execution_evidence_only`，不证明真实 production cloud、真实 live Nav2 run、真实 delivery success、真实 OSS/CDN 或真实手机/PC 验收。
- 真实 O11 proof 若携带日志路径等运维字段，会按安全规则 fail-closed；后续可由 O11 或采集侧提供安全裁剪版 proof JSON，再进入同一参数。
