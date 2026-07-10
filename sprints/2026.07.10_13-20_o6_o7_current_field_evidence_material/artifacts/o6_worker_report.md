# O6 Worker Report

## sprint_type: micro

### 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `current_field_evidence_material` additive section 的 O6/O7 读回链路。
  - 新增源 schema `trashbot.current_field_evidence_material.v1` 到 O6 schema `trashbot.o6.current_field_evidence_material.v1` 的收敛逻辑。
  - 固定 proof scope 为 `software_proof_current_field_evidence_material_only`。
  - 在 `field_evidence`、`artifact_bundle`、archive detail、consumer detail、explicit include 中保留安全摘要。
  - 对缺失、schema/proof scope 不支持、task mismatch、危险 true、URL/token/绝对路径/traceback/raw/response body 等情况做 section-local fail-closed，且不回显敏感原文。
  - 维持固定 false flags，避免把本地 mock 读回误读成真实控制或送达。

- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 增加 current field evidence material 的正向读回和负向 fail-closed 覆盖。
  - 覆盖 field_evidence / artifact_bundle / consumer include 三条读回路径。
  - 覆盖 schema/proof scope/task mismatch/unsafe 文本/危险 true 的阻断行为。

- `docs/interfaces/o6_cloud_archive_api.md`
  - 补充 `current_field_evidence_material` 的接口说明、可读回路径、字段对齐和 fail-closed 规则。

### 已运行或未运行的验证

- 已运行 `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 结果：通过，未输出错误。

- 已运行 `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - 结果：失败，2 个断言失败。
  - 失败 1：`test_o6_current_field_evidence_material_in_field_and_bundle_readback`
    - 断言期望 `status == current_field_evidence_material_ready_not_route_execution_proof`
    - 实际返回 `blocked_not_proven`
  - 失败 2：`test_o6_current_field_evidence_material_missing_or_unsafe_returns_blocked_summary`
    - 断言期望 `blocked_reasons` 含 `current_field_evidence_material_not_available`
    - 实际返回 `current_field_evidence_material_unsafe`

- 已运行 `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/artifacts/o6_worker_report.md`
  - 结果：通过，未输出错误。

### 最后卡点

- 当前卡点是 `current_field_evidence_material` 的状态语义与 Algorithm/O7 预期不一致。
- 代码和测试都在尝试把它作为 `current_field_evidence_material_ready_not_route_execution_proof` 回读，但实际汇总路径仍会把这类输入压成 `blocked_not_proven`，并且危险判定落到了 `current_field_evidence_material_unsafe`。
- 这说明 section 的 status、blocked_reasons 以及上层 consumer 期待还没有完全对齐，现阶段不能宣称该 section 的 ready 状态已稳定。

### 剩余风险

- 目前仅能确认软件侧 fail-closed 路径存在，不能证明该 section 的 ready 状态与 Algorithm/O7 的字段契约完全一致。
- 由于 unittest 已失败，本轮不应把这次改动当成完成交付。
- 需要后续在不扩大敏感回显的前提下，对 `current_field_evidence_material` 的 unsafe 判定和 ready status 规则再做一次对齐。
