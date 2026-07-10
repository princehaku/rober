# Algorithm Worker Report

## 实际改动文件

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`

## 实现内容

- 在 `build_same_task_route_execution_material_packet` 新增 credit-aware 字段：
  - `live_or_field_command_evidence_present`
  - `delivery_or_operator_material_consumed`
  - `route_execution_credit_candidate`
  - `credit_support_only_reason`
  - `credit_required_evidence`
- 复用既有 same-task mission gate 的 live/support-only 口径，避免 route execution packet 与 mission gate 对同一材料给出冲突解释。
- 保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`hil_pass=false`、`route_execution_success=false` 固定不变。

## 接口影响

- `trashbot.same_task_route_execution_material_packet.v1` 新增 5 个向后兼容字段。
- 旧字段与原有 blocked/ready 语义保持不变；新字段只补充 credit 判定，不放宽任何成功或控制相关开关。

## 验证结果

```bash
$ python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
# exit 0

$ python3 -m unittest onboard.tests.test_field_route_evidence_manifest
...................................................................
----------------------------------------------------------------------
Ran 67 tests in 0.499s

OK

$ git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material
# exit 0
```

补充单测覆盖：

- route execution packet ready 但缺 live/field evidence 时，`route_execution_credit_candidate=false`
- live motion + delivery/operator 材料都存在时，`route_execution_credit_candidate=true`
- 缺 delivery claim/operator confirmation 时，标记 `delivery_or_operator_material_missing`
- task drift / dangerous true / unsafe text 时继续 fail-closed

## 失败定位

- 无。

## 剩余风险

- 本轮仍是 local/mock/software proof，不证明真实 live Nav2、真实 robot motion、真实 delivery success、真实 production cloud 或 HIL。
- `route_execution_credit_candidate=true` 只表示 same-task route execution material 已具备 credit candidate 形态，不表示可以解锁控制或宣称送达成功。
