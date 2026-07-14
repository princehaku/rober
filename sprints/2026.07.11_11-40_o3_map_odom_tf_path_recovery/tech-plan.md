# O3 Map Odom TF Path Recovery Tech Plan

## 技术方案

本轮继续使用 real-board no-motion managed runtime。Robot Software 直接修 O10 helper / preflight 的 AMCL TF 主链路：

1. 在 `o10_amcl_nav2_runtime_proof.py` 中加强 AMCL broadcast 条件采集：
   - AMCL params：`tf_broadcast`、`global_frame_id`、`odom_frame_id`、`base_frame_id`；
   - AMCL graph：publishers/subscribers；
   - `/tf` / `/tf_static` source inventory；
   - `/amcl_pose` 是否在 `map` frame；
   - `/scan` 与 `/map` 是否在 managed runtime 窗口内被观察到；
   - managed static TF 进程与 `odom->base_link`、`base_link->laser_frame` 状态。
2. 针对 `map_to_odom=false` 输出更具体 root cause，并避免在已经有足够定位 blocker 时继续跑拖死 HTTP 的慢 probe。
3. 修正外层 `field_route_evidence_preflight.py` 或 `upper_robot_api.py` 的 refresh 等待预算，使 preflight 能自然拿到 helper final body。预算调整必须有上限且仍 fail-closed。
4. 若 AMCL/TF 条件满足后 `map->odom` 出现，开启 path proof 并复验 `path_generated`。

## 文件范围

允许改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/tech-done.md`
- `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/artifacts/*`

只读参考：

- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/**`
- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
- `onboard/src/ros2_trashbot_nav/config/nav2_params.yaml`
- `onboard/scripts/o11_nav2_lifecycle.sh`

禁止改动：

- WAVE ROVER / UART / hardware driver 参数；
- O5/O6/O7 archive/readback/UI wrapper；
- unrelated docs or tests。

## 接口影响

- 不改变 public API schema 的 safety 语义。
- 可以新增 root-cause/detail 字段；新增字段必须向后兼容。
- `safe_to_control`、`robot_control_executed`、`delivery_success`、`hil_pass` 必须保持 false。

## 验收命令

Robot Software 必须至少运行：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper onboard.tests.test_field_route_evidence_preflight onboard.tests.test_upper_robot_api
```

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/artifacts/local_preflight.raw.json
```

若真实板 SSH 可达，必须运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 12 --output sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/artifacts/live_map_odom_tf_path.raw.json
```

若 preflight 仍无法回读 helper final body，必须补跑 direct helper 或记录 SSH 不可达原因：

```bash
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

最后运行 scoped diff 检查：

```bash
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_upper_robot_api.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery
```

## OKR 最低优先级核对

- 当前 `OKR.md` 完成度最低的 Objective：Objective 5，约 `85%`。
- 本 sprint 是否针对该 Objective：否。
- 理由：O5 近两轮已收敛为 `no_real_production_external_evidence` / `okr_credit_allowed=false`，继续做 readiness、probe 或 support-only packet 不允许提升主 OKR；本轮转向可在当前 real-board/no-motion 环境推进的 O3/O1 localization/path 前置链。
- final.md 收口时需复核：O5 blocker 是否仍成立；本轮是否拿到 `map->odom`、path 或更具体 AMCL blocker。

## 风险边界

- 即使 `map->odom=true`，本轮仍不证明底盘运动、route execution、safe-to-control、HIL pass 或 delivery success。
- 如果 SSH 不可达，最多只能收口为 local/mock proof，必须保持 OKR 百分比不变。
- 如果只提高 refresh timeout 但没有更具体 AMCL/root-cause 事实，不得计为 mission progress。
