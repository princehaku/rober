# Algorithm Worker Report

## 实际改动

- 在 [`/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py`](/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py) 增加 `route_bag_payload_replay` 生成器，挂到 manifest 顶层和 `field_motion_evidence_packet.route_bag_payload_replay`。
- 新增 `trashbot.route_bag_payload_replay.v1` / `software_proof_route_bag_payload_replay_only` 契约，保留 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 新增对 DB3 `messages.data` 的只读 payload 统计：`payload_sample_count`、`payload_size_min_bytes`、`payload_size_max_bytes`、`payload_size_avg_bytes`、`payload_sha256_prefix_samples`；其中 `payload_sha256_prefix_samples` 已按 O6/O7 合同收敛为 `string[]` 短 hex 前缀，不再回显 per-sample topic/timestamp/payload_size 结构。
- 新增 fail-closed 分支，覆盖缺 DB3、DB3 不可读、SQLite schema 不符、空 topic/message、payload 为空、unsafe topic、危险 true、路径/root/token/raw/base64/credential URL 等场景。
- 在 [`/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py`](/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py) 扩展 DB3 fixture，补充 payload replay ready / missing / unreadable / empty / unsafe 的单元测试。
- 在 [`/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md`](/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md) 补充 `route_bag_payload_replay` 接口说明和 fail-closed 约束。

## 验证结果

- `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py`
- `python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
- `rg -n "route_bag_payload_replay|software_proof_route_bag_payload_replay_only|safe_to_control|delivery_success" onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md`
- `git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md`
- payload replay smoke 通过，输出摘要包含 `status=ready_not_route_execution_proof`、`proof_scope=software_proof_route_bag_payload_replay_only`、`payload_sample_count=8`、`payload_size_min_bytes=72`、`payload_size_max_bytes=921652`、`payload_size_avg_bytes=1371.093`、`payload_sha256_prefix_samples` 为短 hex `string[]`、`contains_abs_path=false`、`safe_to_control=false`、`delivery_success=false`。
- 本轮只修正 `payload_sha256_prefix_samples` 的合同形状，没有改动 O6/O7、OKR 或 tech-done。

## 剩余风险

- 当前 payload replay 只证明 rosbag2 DB3 的安全摘要可消费，不证明真实 live Nav2、真实底盘控制或 delivery success。
- `messages.data` 仍然只做只读统计和短 hash 前缀样本，后续若要接 O6/O7 消费链路，需要保持同样的 fail-closed contract。

## 本轮复核

- 复核时间：2026-07-09
- 复核结论：算法侧实现与测试已在工作区内通过，本轮未发现需要补写的生成器缺口。
- 复核命令：`python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
