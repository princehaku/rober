# O5/O6 Cloud Terminal Result Delivery Bridge Tech Done

## Sprint 类型

sprint_type: epic

## 用户价值和产品北极星

普通用户和运营支持最终需要从云端命令终态追到同一 `task_id` 的送达结果证据。本轮把 O5 `trashbot.cloud_command_terminal_result.v1` 纳入 O6/O7 已有 `delivery_result_evidence` 读模型，让 terminal result 不再停留在控制面孤岛，但仍不把它解释成真实送达成功。

## 实际改动

Algorithm worker：

- `onboard/scripts/field_route_evidence_manifest.py` 新增 `--cloud-terminal-result-json`，在未提供 `--delivery-result-json` 时把 O5 terminal result 转为 `trashbot.delivery_result_evidence.v1`。
- `onboard/tests/test_field_route_evidence_manifest.py` 新增 ready、schema mismatch、dangerous true/unsafe refs fail-closed 覆盖。
- `docs/navigation/field_route_evidence_manifest.md` 更新输入优先级、安全字段、示例命令和证据边界。

O6 worker：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` 新增 cloud terminal source schema readback 回归测试。
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 返工接受 Algorithm 输出的 `ready_not_delivery_proof`，并对外规范化为 `delivery_result_evidence_ready_not_delivery_proof`。
- `docs/interfaces/o6_cloud_archive_api.md` 更新 O6 readback 合同，明确 `source_schema=trashbot.cloud_command_terminal_result.v1` 必须保留。

Product closeout：

- `OKR.md` 更新 O5/O6/O7 保守进度、证据边界和下一步方向。
- `docs/process/okr_progress_log.md` 新增本 sprint 进度日志。
- 本 sprint 新增 `tech-done.md`、`side2side_check.md`、`final.md` 和 `artifacts/product_worker_report.md`。

## 验证结果

Algorithm worker 验证：

```text
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
通过，无输出。

python3 -m unittest onboard.tests.test_field_route_evidence_manifest
Ran 53 tests in 0.272s
OK
```

O6 worker 初次验证和返工后验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
通过，无输出。

python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
Ran 165 tests in 62.817s
OK
```

Product 收口验收：

```text
rg -n "cloud_terminal_result|cloud_command_terminal_result|trashbot.cloud_command_terminal_result.v1|software_proof_cloud_terminal_result_delivery_bridge_only|O5|O6|O7|delivery_success=false" ...
退出码 0，命中 1108 行。关键锚点包括 OKR.md 的 O5/O6/O7 进度、docs/process/okr_progress_log.md 的本 sprint 收口、docs/navigation/field_route_evidence_manifest.md 的 --cloud-terminal-result-json 合同、docs/interfaces/o6_cloud_archive_api.md 的 O6 状态规范化合同，以及本 sprint 收口文档。

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_02-06_o5_o6_cloud_terminal_result_delivery_bridge docs/navigation/field_route_evidence_manifest.md docs/interfaces/o6_cloud_archive_api.md onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
退出码 0，无输出。
```

## 偏差和返工

O6 worker 首轮发现 Algorithm 实际输出 `delivery_result_evidence.status=ready_not_delivery_proof`，而 O6 原先只接受 canonical 长状态，导致真实 Algorithm 输出会被降级为 `blocked_not_proven`。返工后 O6 接受该短状态，但对外仍规范化输出 `delivery_result_evidence_ready_not_delivery_proof`，避免 O7 多口径解析。

## OKR 调整

- O5：约 80% -> 81%。理由是 robot-facing terminal result 现在可作为同一 `task_id` 的 delivery result evidence 来源；但没有真实 production cloud / 4G / TLS / DB / queue 证据，所以只小幅上调。
- O6：约 80% -> 82%。理由是 O6 archive/readback 已保留 `source=cloud_command_terminal_result` 和 `source_schema=trashbot.cloud_command_terminal_result.v1`，并完成状态规范化返工与 165 个单测。
- O7：约 80% -> 81%。理由是 O7 可沿既有只读 delivery result evidence 路径识别该来源；但本轮没有新增 O7 UI、真实媒体、真实 operator confirmation 或 production cloud 证据。

## 剩余风险

- 证据边界是 `software_proof_cloud_terminal_result_delivery_bridge_only`。
- 不证明真实 production cloud、真实 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic。
- 不证明真实 live Nav2 route execution、真实 delivery record、真实 operator confirmation、真实 robot motion、真实 delivery success 或完整路线长期验收。
- 下一轮不要继续堆 wrapper/decoder；优先用该桥接合同接真实或准现场 same-task terminal result + live route execution / production cloud evidence。
