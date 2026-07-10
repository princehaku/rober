# Algorithm Worker Report

## 实际改动

- `onboard/scripts/field_route_evidence_manifest.py`
  - 增加可选 `--current-field-evidence-json` 输入。
  - 生成新增 additive packet `trashbot.current_field_evidence_material.v1`，`proof_scope=software_proof_current_field_evidence_material_only`。
  - 将同一摘要同时写入 manifest 顶层与 `field_motion_evidence_packet.current_field_evidence_material`。
  - 固定输出安全字段，关闭控制/成功类布尔值，fail-closed 处理危险 true 和不安全文本。
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 补充正向 fixture。
  - 增加 ready 路径用例，覆盖 camera / radar / map / Nav2 no-motion path / manual gate 摘要消费。
  - 增加 hostile 用例，验证危险 true 与不安全文本时 fail-closed。
- `docs/navigation/field_route_evidence_manifest.md`
  - 补充新输入、packet 语义、顶层与嵌套写入位置、固定 false 字段和安全边界说明。

## 验证结果

- `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py`
  - 通过。
- `python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
  - 通过。
- `git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/artifacts/algorithm_worker_report.md`
  - 通过。

## 失败定位

- 过程中出现过一次 hostile 测试断言不匹配，原因是污染字段落点不对，随后已修正到 `safe_command_boundary.locked_reason`，恢复通过。

## 剩余风险

- 该 packet 只证明 current field evidence summary 被安全消费，不证明真实 route execution、HIL、控制成功或云端生产连通。
- 仍依赖输入 JSON 形状与本次 fixture 一致；若上位机真实 summary 结构变化，需要补充解析兼容或新的测试样本。
