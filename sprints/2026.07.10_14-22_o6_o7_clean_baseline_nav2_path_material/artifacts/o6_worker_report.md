# O6 Worker Report

## 改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`

## 实际实现

- 在 O6 archive/readback 中新增 additive section `clean_baseline_nav2_path_material`。
- 新增输入 schema `trashbot.clean_baseline_nav2_path_material.v1`、回读 schema `trashbot.o6.clean_baseline_nav2_path_material.v1`，proof scope 固定为 `software_proof_clean_baseline_nav2_path_material_only`。
- 新 section 已接入：
  - `field_evidence_manifest` ingest
  - `artifact_bundle` ingest
  - archive task detail 顶层 alias
  - consumer detail 顶层 alias
  - `field_evidence_consumer_ingest`
  - `artifact_bundle_consumer_ingest`
  - `include=clean_baseline_nav2_path_material`
- section-local fail-closed 已覆盖：bad schema、proof scope mismatch、task mismatch、危险 true、unsafe text/raw/base64、绝对路径、URL/token、traceback/response body。
- 回读字段只保留 tech-plan 约定的安全字段与固定 false flags，不回显原始路径或正文。

## 验证结果

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
# exit 0

python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
# Ran 175 tests in 72.238s
# OK

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material/artifacts/o6_worker_report.md
# exit 0
```

## 剩余风险

- 这里只证明 O6 local/mock archive/readback 能安全消费 clean-baseline no-motion path material，不证明真实 route execution、真实 delivery、真实 operator confirmation、真实 production cloud 或 HIL。
- 目前只覆盖 O6 backend；O7 consumer/UI 侧是否完整展示该 section，仍需对应 owner 收口验证。
