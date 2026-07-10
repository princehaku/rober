# Algorithm Worker Report

## 自主能力目标和本轮抓手

- 目标：让 `field_route_evidence_manifest.py` 的 `--cloud-terminal-result-json` 在不破坏 direct `trashbot.cloud_command_terminal_result.v1` 合同的前提下，兼容 O5 relay `trashbot.cloud_command_result_reconciliation.v2` wrapper。
- 抓手：只允许 `result_state=terminal_result_recorded` 且 nested `terminal_result.schema=trashbot.cloud_command_terminal_result.v1` 的 reconciliation wrapper 下钻到既有 `delivery_result_evidence` 生成逻辑；pending / missing / task drift / unsafe refs / dangerous true 一律 fail-closed。

## 改动文件和接口影响

1. `onboard/scripts/field_route_evidence_manifest.py`
2. `onboard/tests/test_field_route_evidence_manifest.py`
3. `docs/navigation/field_route_evidence_manifest.md`
4. `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/artifacts/algorithm_worker_report.md`

接口影响：

- `--cloud-terminal-result-json` 新增兼容 `trashbot.cloud_command_result_reconciliation.v2`。
- 输出合同不变：继续产出 `trashbot.delivery_result_evidence.v1`，`source=cloud_command_terminal_result`，`source_schema=trashbot.cloud_command_terminal_result.v1`。
- `same_task_mission_evidence_gate` 继续只接受 `delivery_result_evidence.source_schema=trashbot.cloud_command_terminal_result.v1` 的安全摘要，不把 reconciliation wrapper 自身当作新的 mission schema。

## 实现内容

- 在 manifest 脚本中新增 reconciliation schema 常量与 wrapper gate。
- reconciliation 输入只有在以下条件同时满足时才会归一化成 direct terminal result：
  - `result_state=terminal_result_recorded`
  - `terminal_result` 为 object
  - `terminal_result.schema=trashbot.cloud_command_terminal_result.v1`
  - wrapper / nested `task_id` 与当前 manifest `task_id` 不漂移
- 归一化后继续复用既有 direct terminal result 安全摘要逻辑，保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 新增测试覆盖：
  - reconciliation recorded ready path
  - reconciliation pending path fail-closed
  - reconciliation task drift + unsafe refs fail-closed 且不回显 secret/path/base64
- 更新导航文档，明确 wrapper 兼容入口和 fail-closed 条件。

## 测试、dry-run 或上车验证结果

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/artifacts/algorithm_worker_report.md
```

结果：

- `py_compile`: exit 0
- `unittest`: exit 0, `Ran 58 tests in 0.304s`, `OK`
- scoped `git diff --check`: exit 0

## 数据、样本或调试输出变化

- 新增 reconciliation fixture：`write_cloud_terminal_reconciliation_json(...)`
- 新增 blocked reasons：
  - `cloud_terminal_result_reconciliation_result_state_not_recorded`
  - `cloud_terminal_result_reconciliation_terminal_result_missing`
  - `cloud_terminal_result_reconciliation_terminal_result_not_object`
  - `cloud_terminal_result_reconciliation_terminal_result_schema_mismatch`
  - `cloud_terminal_result_reconciliation_task_id_mismatch`
  - `cloud_terminal_result_reconciliation_nested_task_id_mismatch`

## 失败定位（如有）

- 本轮算法侧验收未出现新增失败；direct terminal result 既有测试继续通过。

## 剩余风险和下一步能力建设建议

- 当前验证边界仍是 local/mock software proof，只证明 reconciliation material 可被 manifest 安全消费，不证明真实 production cloud、真实 4G、真实 route execution 或真实 delivery success。
- Robot Software 并行 smoke 若直接读取 O6 consumer detail，需要继续确认其断言仍以 `delivery_result_evidence.source_schema=trashbot.cloud_command_terminal_result.v1` 为准，而不是 reconciliation wrapper schema。
- 下一步建议：用 relay in-process smoke 把 reconciliation GET 响应直接送入 manifest，再串 O6 archive/readback，确认 same-task gate 在跨进程路径上仍保持 ready-not-success-proof。
