# O3 Scan Probe QoS Repair Tech Plan

## 方案

在 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 中把 `/scan` probe 从单次 `ros2 topic echo --once /scan` 升级为结构化多尝试诊断。优先使用适配 `sensor_msgs/msg/LaserScan` 的 sensor-data QoS 或等价稳定读法；必要时保留 CLI fallback。artifact 需要记录每次尝试的 command、timeout、timed_out、observed、elapsed_ms、stdout/stderr 摘要和 endpoint/publisher 摘要。

`build_localization_signal_freshness` 和 root cause 选择应消费新的 `/scan` 尝试摘要：成功时输出 `/scan.observed=true` 与 freshness；失败时输出可操作原因，例如 QoS attempt timeout、publisher missing、message stale、ROS CLI unavailable 或 managed runtime window expired。

## 文件范围

允许 `robot-algorithm-engineer` 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/tech-done.md`
- `sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/artifacts/*`

禁止修改：

- O5 relay、O6 archive、O7 workstation、WAVE ROVER hardware driver、vendor docs、OKR.md。

## 接口影响

O10 helper JSON 只允许 additive / backward-compatible 变化。建议新增或扩展：

- `proof.localization_signal_freshness["/scan"].probe.attempts[]`
- `proof.localization_signal_freshness["/scan"].probe.best_attempt`
- `proof.localization_signal_freshness["/scan"].publishers`
- `proof.localization_signal_freshness["/scan"].qos_probe_boundary`

所有 safety fields 必须保持保守 false，除非真实验收证据另有证明；本轮预期不会改变这些字段。

## 验收命令

子 agent 必须运行并记录结果：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --output sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/artifacts/local_o10_scan_qos_repair.raw.json
```

本地 Mac 没有 ROS 时允许 exit 2，但必须 fail-closed 且落盘 artifact。

真实板可达时必须运行：

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' \
  > sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/artifacts/live_o10_scan_qos_repair.raw.json
```

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_13-41_o3_scan_probe_qos_repair
```

## OKR 最低优先级核对

当前 `OKR.md` 4.1 中最低主 Objective 是 O5，约 `~85%`。本 sprint 不直接针对 O5，理由是最近 O5 external evidence / field execution pivot 已明确 fail-closed：没有真实 production external evidence 或新 field execution material，继续 O5 readiness、wrapper、probe、checklist 只能保持 `okr_credit_allowed=false`，不能产生主 OKR 增量。

本轮转向 O3 no-motion scan probe repair，是为了打通 O1 current same-run path generation 与 O6/O7 live material 消费链的前置现场 blocker。若本轮仍不能产生 `/scan` 可读或更强 live artifact，下一轮不得继续重复消费同一 scan/amcl timeout blocker，必须切换 Objective 或升级材料/现场条件缺口。

## 风险

- 真实板 SSH 或 ROS runtime 可能不可达；此时只能留下 local fail-closed artifact，不能声明 live proof。
- `/scan` 可读后仍可能卡在 AMCL 参数、TF source、map quality 或 planner lifecycle；本轮只解决第一个现场 blocker。
- 若当前工作区已有未提交改动，子 agent 必须在现有改动基础上增量修改，不得回滚或覆盖他人变更。
