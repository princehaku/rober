# Board Offline Evidence Intake Tech Done

## sprint_type: epic

## 实际改动

- `onboard/scripts/field_route_evidence_manifest.py`
  - 复用现有 `--mode local` 作为离线 evidence packet intake 主入口。
  - 新增 `--input <dir>`，作为 `--artifact-root <dir>` 的等价 alias，保证 sprint P0 验收命令可原样运行。
  - 新增本地 packet 内已有 manifest 的只读校验：识别 `field_evidence_manifest.json`、`trashbot_field_evidence_manifest.json`、`trashbot.field_evidence_manifest.v1.json`、`manifest.json` 及 `route_data/` 下同名候选。
  - 对已有 manifest 的 schema mismatch、坏 JSON、非 object root、`delivery_success=true`、`safe_to_control=true`、`primary_actions_enabled=true` 做 fail-closed；即使 artifact 完整，也输出 `gate_pass=false`、`status=blocked_existing_manifest_reuse`。
  - 保持生成 manifest 顶层 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`；`gate_pass=true` 只表示 artifact gate 完整，不表示真实送达或真实控制。
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 新增 `--input` alias 测试。
  - 新增 existing manifest schema mismatch fail-closed 测试。
  - 新增 existing manifest unsafe claim fail-closed 测试。
- `docs/navigation/field_route_evidence_manifest.md`
  - 记录 `--input` 离线导入入口、preflight 缺省语义、已有 manifest 候选名、安全字段和 fail-closed 规则。

## 验证结果

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py onboard/scripts/field_route_evidence_preflight.py
```

结果：通过，无输出。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

结果：通过，`Ran 8 tests in 0.051s`，`OK`。

```bash
python3 onboard/scripts/field_route_evidence_manifest.py --help
```

结果：通过，help 中包含 `--input INPUT_DIR`，说明为 `Alias for --artifact-root when importing a local offline evidence packet.`。

```bash
python3 onboard/scripts/field_route_evidence_manifest.py --mode local --input /tmp/trashbot_field_evidence_fixture --output /tmp/trashbot_field_evidence_manifest.json
```

结果：通过，输出摘要：

```json
{"gate_pass": true, "output": "/tmp/trashbot_field_evidence_manifest.json", "schema": "trashbot.field_evidence_manifest.v1", "status": "field_evidence_manifest_ready_not_delivery_proof"}
```

生成 manifest 关键字段：

- `artifact_status=gated`
- `blocked_reason=missing_preflight_json`
- `not_proven=true`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `artifact_health.present_count=5`

```bash
rg -n "trashbot.field_evidence_manifest.v1|delivery_success|safe_to_control|primary_actions_enabled|not_proven|artifact_status|gate_pass" onboard pc-tools sprints/2026.06.09_21-03_board-offline-evidence-intake
```

结果：通过，退出码 0；命中既有 onboard / pc-tools / sprint 文档中的 manifest schema、`not_proven` 和 fail-closed 安全字段。

```bash
git diff --check
```

结果：通过，无输出。

## 偏差与说明

- 未新增 `field_route_evidence_offline_intake.py`。原因：现有 `field_route_evidence_manifest.py --mode local` 已具备 artifact 扫描、manifest gate 和 fail-closed 主体，只缺少 `--input` alias 与已有 manifest 安全校验；复用现有入口能避免 live/offline 双路径分叉。
- 本轮没有触碰 `pc-tools/**`。机器人侧输出字段仍是既有 `trashbot.field_evidence_manifest.v1`，并新增 `input_manifest` 摘要供消费者只读解释；不改变 PC 端必须消费的安全字段。
- 本轮不依赖真实 SSH。`root@192.168.1.11 -p 37878` 仍是 P1 风险，不作为 P0 验收阻塞。

## 剩余风险

- `/tmp/trashbot_field_evidence_fixture` 是本地 fixture，只证明 offline intake 软件路径，不证明真实 SLAM、真实 route capture、真实 Nav2 replay 或真实 delivery。
- 真实现场人工导出包仍需现场人员提供，且必须包含非空 `map.yaml`、`route.csv`、keyframes、`route_bag/` 或 rosbag、`fixed_route_replay.jsonl`。
- 真实 SSH `192.168.1.11:37878` 最近仍不可达；后续若网络恢复，应把真实 run 目录直接喂给同一 `--input` / `--artifact-root` 路径。
