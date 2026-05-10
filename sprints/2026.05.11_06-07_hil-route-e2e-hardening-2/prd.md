# Sprint 2026.05.11 06-07 HIL + Route E2E Hardening-2 - PRD

## 用户价值与北极星

让手机端“看到同一套证据就知道下一步做什么”，在 O1/O2/O3 任何失败分支下，展示统一的 `failure_code/evidence_ref/source/state_transition_history/human_intervention_required`，并给出可执行恢复建议，减少用户猜测和误操作。

## 本轮目标

1. operator gateway status/diagnostics 统一采集与透传规则，避免 O1/O2/O3 的证据字段漏传、重复拼接。
2. 失败链路中将 `evidence` 与 `failure_code` 映射为用户可执行的恢复建议（而非空洞提示）。
3. 仅更新现有三份 sprint 文件与行为网关代码，不新增测试文件。

## 用户旅程收益

- 用户触发任务→运行中可持续查看 `source/evidence_ref/human_intervention_required`。
- 任务失败时看到清晰 `failure_code` 与来源证据，不再只看到“异常停止/需人工接管”。
- 依据建议直接执行“重试/清场/回点位/恢复路线”等动作，闭环率更高。

## OKR 映射（本轮聚焦）

- KR1：同一失败事件在 `status` 与 `diagnostics` 中的 `failure_code/evidence_ref/source/state_transition_history/human_intervention_required` 保持一致。
- KR2：普通用户在 operator 页面可读到可执行恢复建议，并可追踪来源（evidence + 失败分支）。
- KR3：完成一次性规则定义并沉淀进本轮 `tech-plan` 方便下轮接手。

## 范围

### 做什么

1. 修改 `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
2. 修改 `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
3. 修改 `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
4. 同步更新本轮 `pre_start.md`、`prd.md`、`tech-plan.md`

### 不做什么

- 不改硬件协议、vendor 资料、WAVE ROVER/ESP32/Orange Pi 接口。
- 不新增测试文件，不扩展到 detector / vision 分支。
- 不改 behavior 状态机关键策略，不改调度算法。

## 验收标准（用户可见结果）

1. 失败时 status 与 diagnostics 均返回以下字段且来源一致：
   - `source`
   - `evidence_ref`
   - `failure_code`
   - `state_transition_history`
   - `human_intervention_required`
2. `diagRecoveryHint` 在 operator 页面展示建议文字，且建议与 evidence 失败分支可对应（如缺图像点、导航中断、路由跳转中断）。
3. 手机端不再重复拼接 `evidence` 字段；字段以透传主数据为准。
4. 未新增测试文件；仅在既有测试命令上验证。

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

## 预计用户提示优先级

- P0：`failure_code` 有值但用户页没看到/不一致。
- P1：`failure_code` 显示但无具体建议，不能执行下一步。
- P2：多路数据源重复拼接，导致建议文本误导。
