# Algorithm Worker Report

## 自主能力目标和本轮抓手

- 目标：为同一 `task_id` 的 Nav2 goal、delivery result、route execution readiness、pose progress 增加 `trashbot.route_delivery_closure_packet.v1` 软件闭合包。
- 抓手：复用现有 additive 的 fail-closed 语义，只输出 summary-only 字段，并把结果同时写入 manifest 顶层与 `field_motion_evidence_packet.route_delivery_closure_packet`。

## 改动文件和接口影响

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/artifacts/algorithm_worker_report.md`

接口影响：

- 新增 additive schema：`trashbot.route_delivery_closure_packet.v1`
- 新增 proof scope：`software_proof_route_delivery_closure_packet_only`
- 新增 ready 状态：`route_delivery_closure_ready_not_success_proof`
- 固定 false：`safe_to_control`、`delivery_success`、`primary_actions_enabled`、`robot_control_executed`、`route_execution_success`

## 实现内容

1. 在 `field_route_evidence_manifest.py` 新增 closure packet 常量、blocked summary 与 builder。
2. 将 closure packet 挂到 manifest 顶层和 `field_motion_evidence_packet.route_delivery_closure_packet`。
3. 收紧规则：缺关键输入、schema mismatch、dangerous true、unsafe text、unsafe 计数、task mismatch 均 blocked。
4. blocked 摘要对 `route_execution_source` 做安全裁剪，避免路径泄漏。
5. 新增 ready / blocked 两条单测，并同步更新导航合同文档。

## 测试、dry-run 或上车验证结果

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

关键结果：

- `python3 -m py_compile ...` 通过，无输出。
- `python3 -m unittest onboard.tests.test_field_route_evidence_manifest` 通过：

```text
Ran 50 tests in 0.252s
OK
```

## 数据、样本或调试输出变化

- `route_delivery_closure_packet` 现在会在 ready 场景输出：
  - `status=route_delivery_closure_ready_not_success_proof`
  - `closure_ready=true`
  - linked status / readiness / claim flags
- blocked 场景会输出：
  - `blocked_reasons`
  - `next_required_evidence`
  - 所有安全相关布尔固定为 `false`

## 失败定位（如有）

- 首轮失败：`closure_ready` 没把 task mismatch / unsafe text 纳入完整闭合条件。
- 修复：blocked 路径统一返回 `closure_ready=false`，并补 `same_task_route_delivery_closure_inputs`。
- 次轮失败：blocked 摘要透传了不安全 `route_execution_source`。
- 修复：对 linked source 做安全文本裁剪，命中 unsafe marker 时返回 `None`。

## 剩余风险

- 该 packet 仍然只是 `software_proof_route_delivery_closure_packet_only`，不证明真实 live Nav2 route execution、真实 delivery success、真实 operator confirmation 现场有效性或 production cloud。
- 当前 unsafe text 规则基于保守字符串扫描；若后续新增字段类型，需要继续同步白名单与 fail-closed 覆盖。
