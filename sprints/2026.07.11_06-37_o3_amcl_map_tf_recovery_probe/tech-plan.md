# O3 AMCL Map TF Recovery Probe Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的主 Objective 是 O5，约 `~85%`。
2. 本 sprint 不直接推进 O5。
3. 转向理由：最近 `2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot` 已确认当前环境缺真实 production external evidence，`2026.07.11_04-36` 和 `2026.07.11_05-55` 已按红线切到 O3 现场验证 lane；继续 O5 readiness/probe/checklist 会重复消费 `no_real_production_external_evidence` blocker，并且 `okr_credit_allowed=false`。本轮继续 O3 是为了拿到新的现场 path/material 前置证据，后续才可恢复 O6/O7 消费链或真实 route proof。

## Owner 与分工

- `robot-algorithm-engineer` 单线闭环：实现必要诊断、运行本地测试、运行真实板 no-motion smoke、更新 `tech-done.md`。
- 主节点：只做派单、验收、`side2side_check.md` / `final.md` 汇总。

## 文件范围

允许修改：

- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/tech-done.md`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/**`

不得修改：

- O5/O6/O7 relay、archive、PC workstation 或 cloud production readiness packet 文件。
- WAVE ROVER 硬件协议、launch 默认运动入口、`/cmd_vel` 或 `/api/base/manual` 相关控制逻辑。
- 其他 sprint 目录。

## 接口边界

- 允许新增或扩展 preflight 输出字段，但必须保持原有 `schema=trashbot.board_field_evidence_preflight.v1`。
- 新字段必须是安全摘要，不得泄漏私钥、token、完整本地路径、raw curl body、完整 ROS stdout 或 traceback。
- 所有危险字段必须固定 false：`safe_to_control`、`delivery_success`、`primary_actions_enabled`、`robot_control_executed`、`route_execution_success`、`hil_pass`。
- 真实板命令必须是只读 topic/TF/lifecycle/file-probe 或 no-motion proof readback，不允许发运动命令。

## 验收命令

子 agent 必须运行并汇报结果：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py
```

```bash
python3 -m unittest onboard.tests.test_field_route_evidence_preflight
```

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.raw.json
```

若真实上位机可达，运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 8 --output sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.raw.json
```

最后运行：

```bash
git diff --check -- onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_preflight.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe
```

## 风险与回滚

- 若真实板不可达，本轮只能保留 local dry-run 和不可达原因，不得宣称现场 root cause。
- 若真实板仍 blocked，本轮可作为 root-cause evidence，但不提升主 OKR 百分比。
- 若发现需要启动或重启 Nav2 lifecycle，子 agent 必须先确认命令不会发送运动，并在 artifact 中保留 no-motion 安全字段。
