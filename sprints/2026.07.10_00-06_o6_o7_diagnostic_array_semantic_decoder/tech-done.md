# O6/O7 DiagnosticArray Semantic Decoder Tech Done

## Sprint 类型

sprint_type: epic

收口时间：2026-07-10 00:32 CST。

## 实际改动

本 sprint 已完成 Algorithm -> O6 -> O7 的 DiagnosticArray semantic decoder 软件证据链。Product/OKR 收口基于三个 worker report，不直接改产品代码、测试代码或硬件配置。

Algorithm owner 实际改动：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/artifacts/algorithm_worker_report.md`

O6 owner 实际改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/artifacts/o6_worker_report.md`

O7 owner 实际改动：

- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/artifacts/o7_worker_report.md`

Product/OKR owner 实际改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/tech-done.md`
- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/side2side_check.md`
- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/final.md`
- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/artifacts/product_worker_report.md`

## 验证结果

Algorithm worker 验证：

```text
$ python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
exit code: 0

$ python3 -m unittest onboard.tests.test_field_route_evidence_manifest
Ran 48 tests in 0.236s
OK
```

O6 worker 验证：

```text
$ python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
Ran 163 tests in 60.706s
OK
```

O7 worker 验证：

```text
$ cd pc-tools/workstation && npm run test && npm run build && npm run lint
Test Files  3 passed (3)
Tests  482 passed (482)
build passed
lint passed
```

Product/OKR 收口验证：

```text
$ test -f sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/artifacts/algorithm_worker_report.md
exit code: 0

$ test -f sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/artifacts/o6_worker_report.md
exit code: 0

$ test -f sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/artifacts/o7_worker_report.md
exit code: 0
```

最终 `rg` 和 `git diff --check` 输出见 `artifacts/product_worker_report.md`。

## 偏差

- O7 worker 未修改生产 adapter/contract/Vue 逻辑；现有 full semantic decode matrix 通用归一逻辑已能读取 DiagnosticArray row，本轮只补 fixture/test/docs/report。
- 本轮没有新增真实生产云、真实路线执行、真实机器人运动或真实送达材料，因此 OKR 只从约 76% 保守上调到约 78%，不归档 KR。

## 证据边界

本轮证据边界是 local/offline software proof。它证明 `diagnostic_msgs/msg/DiagnosticArray` 可由 fixture DB3 / O6 readback / O7 fixture UI 链路从 unsupported topic type 转为 decoded coverage，并继续保持 `safe_to_control=false`、`delivery_success=false`。

本轮不证明：

- 真实 production cloud、真实 4G/TLS、production DB/queue 或 OSS/CDN live traffic。
- 真实 live Nav2 route execution、真实 robot motion 或完整路线长期验收。
- 真实 delivery record、真实 operator confirmation 或真实 delivery success。
- raw ROS message payload 已全量语义回放。
- 真实 annotation API/export、真实 dataset export 或真实手机/browser 现场验收。

## 剩余风险和下一步

- DiagnosticArray decoder 只输出安全摘要，不保留 diagnostic message/key/value 原文；现场故障深挖仍需要受控私有日志或原始 rosbag。
- 如果真实 route bag 缺 `/diagnostics` 或 O6 未传入该 matrix row，O7 仍会按 fail-closed 展示缺口。
- 下一轮不建议继续只补 decoder；优先补真实或准现场 live Nav2 result、delivery record/operator confirmation、production cloud。若继续 decoder，必须选择 full semantic decode matrix 中仍有实际 gap 的安全 topic type。
