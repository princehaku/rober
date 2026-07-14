# O3 Signal Freshness TF Source Tech Plan

## 技术方案

本轮由 `robot-algorithm-engineer` 单线闭环，继续使用 real-board no-motion managed runtime，但不把目标设为立即 path success。实现重点是把单条 signal probe 的事实结构化，作为下一轮修 `/scan`、AMCL 或 dynamic TF 的依据。

建议实现：

1. 在 `o10_amcl_nav2_runtime_proof.py` 中新增或扩展 `localization_signal_freshness` / `tf_source_freshness` 摘要。
2. 对 `/scan`、`/amcl_pose`、`/odom`、`/tf`、`/tf_static` 记录同窗 probe 的耗时、return code、observed、topic type、publisher/subscriber、可解析 timestamp、freshness age 和 fail reason。
3. 对 TF inventory 进一步标注 dynamic/static source，尤其是：
   - `map->odom` 是否由 `/tf` dynamic edge 观测；
   - `odom->base_link` 是否 dynamic；
   - `base_link->laser_frame` 是否 static；
   - 仅有 static edge 时不得误判 localization closed。
4. root cause 输出优先从 signal freshness / source inventory 生成；若信息不足，明确 `freshness_unknown` 或 `probe_timeout`。
5. 更新测试覆盖至少两个场景：
   - `/scan` topic 存在但 once probe timeout，应输出 elapsed/timeout/stale 或 unknown，而不是泛化成功；
   - dynamic `odom->base_link` 与 static `base_link->laser_frame` 能被区分，`map->odom` 缺失仍 fail-closed。
6. 更新导航文档，写清本轮 artifact 字段与 no-motion proof boundary。

## 文件范围

允许改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/tech-done.md`
- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/*`

只读参考：

- `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/**`
- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/src/ros2_trashbot_nav/config/nav2_params.yaml`

禁止改动：

- WAVE ROVER / UART / hardware driver 参数；
- O5/O6/O7 archive/readback/UI wrapper；
- unrelated docs、mobile、cloud relay 或 workstation 文件。

## 接口影响

- 不改变 public API 的安全语义。
- 可以新增 helper artifact 字段；新增字段必须向后兼容。
- `safe_to_control`、`robot_control_executed`、`delivery_success`、`hil_pass` 必须保持 false。

## 验收命令

Algorithm owner 必须至少运行：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

本地 no-motion dry-run：

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --output sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/local_o10_signal_freshness.raw.json
```

若真实板 SSH 可达，必须先同步 helper 再运行 direct helper：

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

```bash
ssh -p 37878 root@192.168.1.11 'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' > sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/live_o10_signal_freshness.raw.json
```

最后运行 scoped diff 检查：

```bash
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_12-41_o3_signal_freshness_tf_source
```

## OKR 最低优先级核对

- 当前 `OKR.md` 完成度最低的 Objective：Objective 5，约 `85%`。
- 本 sprint 是否针对该最低 Objective：否。
- 理由：O5 已连续收敛为缺真实 external production evidence / field execution material，继续 O5 support-only/readback 工作会重复消费 blocker 且 `okr_credit_allowed=false`。本轮转向当前环境可执行的 O3 real-board no-motion signal freshness 证据，服务 O1 same-run path generation 和 O6/O7 后续 material consumption。
- final.md 收口时必须复核：O5 blocker 是否仍成立；本轮是否产出新的 signal freshness / TF source root cause、`map_to_odom=true` 或 path/material。

## 风险边界

- 如果只新增字段但没有真实板 artifact，本轮只能算 local software proof，不调整 OKR。
- 如果真实板仍 fail-closed，但 root cause 比上一轮更细，可以记录为 O3 supporting evidence，不上调主 OKR。
- 本轮无运动执行，不证明 safe-to-control、route execution、HIL pass 或 delivery success。
