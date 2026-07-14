# O3 Managed Runtime Scan Attempt Recovery Tech Plan

## 方案

本轮不继续扩展 `/scan` QoS 合同，而是围绕“为什么最新 true-board artifact 没有稳定进入 `/scan` attempt 层”做受控恢复。策略是先把板端 managed runtime / ROS2 source / lifecycle readiness 恢复到可重复进入 `/scan` attempt 的状态；如果恢复成功，再沿用现有 BEST_EFFORT / RELIABLE attempt 合同读取 sample/timeout/classification；如果恢复失败，则把 root cause 收敛到比上一轮更前置的 runtime blocker。

## 用户价值和产品北极星

本轮直接服务于“固定路线能否开始生成 current-run path 证据”。没有 `/scan` attempt 级 artifact，就没有可靠的 `/amcl_pose`、`map_to_odom` 和 `path_generated` 事实，因此也无法推进用户真正关心的路线稳定送达。

## OKR 映射和方向判断

- O1：`继续`。本轮是 current same-run path generation success 的前置恢复工作。
- O5：`暂停 support-only lane`。原因是最近连续 fail-closed 后仍缺真实 external production evidence，继续投入不会新增 mission artifact delta。
- O6/O7：`继续但不直接推进`。只有本轮拿到新的 current-run route/runtime material，后续才有资格消费。

## 文件范围

Planning 阶段主节点已创建：

- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/pre_start.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/prd.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/tech-plan.md`

Implementation 阶段允许 `robot-algorithm-engineer` 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/tech-done.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/artifacts/*`

禁止修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- O5 relay / cloud production readiness 代码
- O6 archive / readback schema
- O7 workstation UI
- WAVE ROVER、串口、引脚、电压、波特率、机械或 `docs/vendor/` 文档
- 其他 sprint 目录

## 对应责任 Engineer

- Implementation owner: `robot-algorithm-engineer`
- Product closeout: `product-okr-owner`

这是单 owner 任务，按 AGENTS 规则由 Algorithm 单线闭环实现、测试、修复和 `tech-done.md` 留档。

## 实施步骤

1. 复盘上一轮 final / tech-done / live artifacts，确认 latest canonical 失败边界是 `partial_runtime_in_progress`，而不是 `/scan` attempt timeout。
2. 检查 helper 在 managed runtime、ROS2 source、CLI/runtime readiness、lifecycle wait 上的进入条件和 fail-closed 输出。
3. 最小修改 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 与目标单测，让 artifact 能稳定表达：
   - 是否进入 `/scan` attempt 层；
   - 若未进入，是哪个 runtime blocker 最先失败；
   - 若已进入，继续沿用现有 BEST_EFFORT / RELIABLE attempt 字段。
4. 更新导航文档，说明“先看 runtime recovery，再看 `/scan` attempts”的读取顺序。
5. 运行本地 `py_compile`、targeted unittest、local fail-closed artifact。
6. true-board 可达时下发 helper，运行 managed runtime no-motion probe，拉回 latest artifact。
7. 若 latest artifact 进入 `/scan` attempt 层，记录 BEST_EFFORT / RELIABLE attempt 结果；若未进入，记录更前置 root cause。
8. 更新 `tech-done.md`，明确本轮属于：
   - `scan_attempt_recovered`，或
   - `runtime_still_blocked_before_scan_attempt`

## 验收命令

Implementation owner 必须运行并记录：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --output sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/artifacts/local_o10_managed_runtime_scan_attempt_recovery.raw.json
```

本地 Mac 没有 ROS 时允许 exit `2`，但必须 fail-closed 并落盘 artifact。

真实板可达时必须运行：

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' \
  > sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/artifacts/live_o10_managed_runtime_scan_attempt_recovery.raw.json
```

```bash
rg -n "managed runtime|ROS2 source|/scan|best_effort|reliable|partial_runtime_in_progress|safe_to_control|robot_control_executed|delivery_success|hil_pass" \
  sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py
```

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery
```

Product planning 阶段只读验收命令：

```bash
test -s sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/pre_start.md
test -s sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/prd.md
test -s sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|robot-algorithm-engineer|managed runtime|/scan" sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery
```

## 优先级和验收口径

P0：

- latest true-board artifact 是否重新进入 `/scan` attempt 层；
- 若未进入，是否把 root cause 收敛到更前置 runtime blocker；
- 顶层 safety / control / delivery / HIL false 字段是否保持不变。

P1：

- 文档是否同步说明本轮 proof boundary；
- `tech-done.md` 是否能指导下一条现场执行命令。

## 风险、阻塞和需要补齐的证据链

- 风险：即使 managed runtime 恢复，`/scan` 也可能仍无 sample，后续还要继续区分 QoS、publisher behavior 或 localization prerequisites。
- 阻塞：如果 true-board 不可达，只能得到 local fail-closed，不足以形成 live runtime recovery proof。
- 证据链：需要 latest live artifact、命令输出摘要和对 root cause 的明确归因；历史偶发成功不能覆盖 same-run latest fail-closed 事实。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：O5，约 `~85%`。
- 本 sprint 是否针对该最低 Objective：否。
- 理由：O5 当前连续卡在 `okr_credit_allowed=false` 与缺真实 external production evidence 的同一 blocker，本轮再做 packet、probe、checklist 或 wrapper 只会重复 support-only 消费。根据 CEO 指定，本轮切到可推进的 O3 live no-motion lane，优先恢复 managed runtime / `/scan` attempt 现场证据，以支撑 O1/O6/O7 的 current same-run path/live route material 缺口。

## 输出要求

子 agent 必须返回：

1. 实际改动的文件列表；
2. 验证命令输出结果；
3. latest live/local artifact 关键字段，尤其是 `status`、`evidence_type`、`/scan.probe.boundary`、BEST_EFFORT / RELIABLE attempt 是否出现、`path_generated` 和顶层 false safety fields；
4. 失败定位；
5. 剩余风险；
6. 下一条现场执行命令。
