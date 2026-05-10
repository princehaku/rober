# Sprint 2026.05.11 06-07 HIL + Route E2E Hardening-2 - Tech Plan

## 状态

- 阶段：tech-plan started
- 时间：2026-05-11
- Owner：`full-stack-software-engineer`
- 本轮目标：统一 O1/O2/O3 的 operator status/diagnostics 证据透传规则，并把失败可恢复建议落地到 operator 页面。

## 任务分工

- 主责：`full-stack-software-engineer`
- 允许改动文件：
  - `sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/pre_start.md`
  - `sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/prd.md`
  - `sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/tech-plan.md`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- 协作点：若发现 task_record 的持久化契约与 `evidence_ref` 含义不一致，需要和 `robot-software-engineer` 同步。

## 统一透传规则（Implementation）

1. 统一字段抽取
   - 在 `operator_gateway_diagnostics.py` 添加 traceability 抽取 helper。
   - 统一优先级顺序：
     - `task_record`（任务记录）
     - `latest_status`（状态快照）
     - `last_task`（历史任务）
   - 兼容旧字段 `state_transitions` 映射到 `state_transition_history`。

2. status/diagnostics 一致透传
   - `failure_code`
   - `evidence_ref`
   - `source`
   - `state_transition_history`
   - `human_intervention_required`

3. 去重与回退策略
   - 统一从抽取结果填充 `failure`、`diagnostics`、`status_payload` 与 `last_task`。
   - 对缺省字段做回退：优先 `last_task`，其次 `task_record_path` / `result_path`。

4. 手机端可执行建议
   - 在 `operator_gateway_http.py` 中新增 `diagRecoveryHint` 生成逻辑：
     - 基于 `failure_code` 与 `evidence_ref` 输出固定模板建议
     - 失败分支映射为具体动作（重试、恢复到上一路径、回到起点、确认场景清理）
   - 移除空泛“人工接管”文案。

## 字段一致性承诺（当前轮）

- `source`：统一由 `normalize_evidence_source` 归一化。
- `evidence_ref`：只在故障上下文中透传，不重复拼接。
- `failure_code`：单一来源传播到 status 与 diagnostics。
- `state_transition_history`：保留原始链路历史，优先 `task_record` 的 `state_transitions`。
- `human_intervention_required`：保留并在 UI 显示为可执行提示。

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

## 风险与残留

- O1/O2/O3 的上下游任务状态源（`task_record` 字段语义）若后续有结构变更，本轮透传规则需补充兼容。
- 本轮不改 `src/ros2_trashbot_interfaces` 与状态机策略，若后续新增失败码，需要更新 `buildRecoveryHints` 映射。
- 仅改网关/页面透传链路，不改硬件层与 vendor 协议。
